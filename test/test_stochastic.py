import random
import unittest

from wildcatting.game import Game
from wildcatting.model import Player, Well
from wildcatting.server import GameService
from wildcatting.theme import DefaultTheme


class TestSeededDeterminism(unittest.TestCase):
    def test_same_seed_same_field(self):
        random.seed(42)
        field1 = Game(10, 10).getOilField().serialize()

        random.seed(42)
        field2 = Game(10, 10).getOilField().serialize()

        self.assertEqual(field1, field2)

    def test_different_seeds_differ(self):
        random.seed(1)
        field1 = Game(10, 10).getOilField().serialize()

        random.seed(2)
        field2 = Game(10, 10).getOilField().serialize()

        self.assertNotEqual(field1, field2)


class TestFieldPropertyRanges(unittest.TestCase):
    def test_all_sites_within_theme_bounds(self):
        theme = DefaultTheme()
        field = Game(20, 20, theme=theme).getOilField()

        min_drill = theme.getMinDrillCost()
        max_drill = theme.getMaxDrillCost()
        min_tax = theme.getMinTax()
        max_tax = theme.getMaxTax()

        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                self.assertGreaterEqual(site.getProbability(), 0)
                self.assertLessEqual(site.getProbability(), 100)
                self.assertGreaterEqual(site.getDrillCost(), min_drill)
                self.assertLessEqual(site.getDrillCost(), max_drill)
                self.assertGreaterEqual(site.getTax(), min_tax)
                self.assertLessEqual(site.getTax(), max_tax)

    def test_oil_prices_always_positive(self):
        prices = DefaultTheme().getOilPrices()
        for _ in range(100):
            self.assertGreater(next(prices), 0.0)


class TestCompleteGameFlow(unittest.TestCase):
    def test_idle_two_player_game_completes(self):
        turn_count = 5
        game = Game(10, 10, turnCount=turn_count)
        p1 = Player("alice", "A")
        p2 = Player("bob", "B")
        game.addPlayer("c1", p1)
        game.addPlayer("c2", p2)
        game.start()

        while not game.isFinished():
            game.endTurn(p1)
            if not game.isFinished():
                game.endTurn(p2)

        self.assertTrue(game.isFinished())

    def test_idle_players_pnl_stays_zero(self):
        turn_count = 5
        game = Game(10, 10, turnCount=turn_count)
        p1 = Player("alice", "A")
        p2 = Player("bob", "B")
        game.addPlayer("c1", p1)
        game.addPlayer("c2", p2)
        game.start()

        while not game.isFinished():
            self.assertEqual(p1.getProfitAndLoss(), 0)
            self.assertEqual(p2.getProfitAndLoss(), 0)
            game.endTurn(p1)
            if not game.isFinished():
                game.endTurn(p2)

        self.assertEqual(p1.getProfitAndLoss(), 0)
        self.assertEqual(p2.getProfitAndLoss(), 0)


class TestOilDiscovery(unittest.TestCase):
    def test_drilling_finds_oil_at_correct_depth(self):
        random.seed(42)
        theme = DefaultTheme()
        game = Game(10, 10, theme=theme)
        field = game.getOilField()

        oil_site = None
        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                if site.getReservoir() is not None:
                    oil_site = site
                    break
            if oil_site is not None:
                break

        self.assertIsNotNone(
            oil_site, "seed 42 must produce at least one oil site on 10x10"
        )

        player = Player("alice", "A")
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        oil_site.setWell(well)

        oil_depth = oil_site.getReservoir().getOilDepth()

        for _ in range(oil_depth - 1):
            self.assertFalse(well.drill(oil_site, theme.getDrillIncrement()))
            self.assertIsNone(oil_site.getOilDepth())

        self.assertTrue(well.drill(oil_site, theme.getDrillIncrement()))
        self.assertEqual(oil_site.getOilDepth(), oil_depth)
        self.assertEqual(well.getDrillDepth(), oil_depth)


class TestMultiplayerTurnOrder(unittest.TestCase):
    def test_three_player_survey_order_across_two_weeks(self):
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 5)
        h1 = service.join(client_handle, "alice", "A")
        h2 = service.join(client_handle, "bob", "B")
        h3 = service.join(client_handle, "carol", "C")
        service.start(h1)

        for week in range(2):
            self.assertEqual(service.getPlayersTurn(client_handle), "alice")
            service.survey(h1, week, 0)

            self.assertEqual(service.getPlayersTurn(client_handle), "bob")
            service.survey(h2, week, 1)

            self.assertEqual(service.getPlayersTurn(client_handle), "carol")
            service.survey(h3, week, 2)

            self.assertIsNone(service.getPlayersTurn(client_handle))

            service.endTurn(h1)
            service.endTurn(h2)
            service.endTurn(h3)


if __name__ == "__main__":
    unittest.main()
