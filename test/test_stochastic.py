import random
import unittest

from wildcatting.game import Game
from wildcatting.model import Player, Well
from wildcatting.server import GameService
from wildcatting.theme import DefaultTheme


class TestSeededDeterminism(unittest.TestCase):
    def test_same_seed_same_field(self) -> None:
        random.seed(42)
        field1 = Game(10, 10).oil_field.serialize()

        random.seed(42)
        field2 = Game(10, 10).oil_field.serialize()

        self.assertEqual(field1, field2)

    def test_different_seeds_differ(self) -> None:
        random.seed(1)
        field1 = Game(10, 10).oil_field.serialize()

        random.seed(2)
        field2 = Game(10, 10).oil_field.serialize()

        self.assertNotEqual(field1, field2)


class TestFieldPropertyRanges(unittest.TestCase):
    def test_all_sites_within_theme_bounds(self) -> None:
        theme = DefaultTheme()
        field = Game(20, 20, theme=theme).oil_field

        min_drill = theme.get_min_drill_cost()
        max_drill = theme.get_max_drill_cost()
        min_tax = theme.get_min_tax()
        max_tax = theme.get_max_tax()

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                self.assertGreaterEqual(site.probability, 0)
                self.assertLessEqual(site.probability, 100)
                self.assertGreaterEqual(site.drill_cost, min_drill)
                self.assertLessEqual(site.drill_cost, max_drill)
                self.assertGreaterEqual(site.tax, min_tax)
                self.assertLessEqual(site.tax, max_tax)

    def test_oil_prices_always_positive(self) -> None:
        prices = DefaultTheme().get_oil_prices()
        for _ in range(100):
            self.assertGreater(next(prices), 0.0)


class TestCompleteGameFlow(unittest.TestCase):
    def test_idle_two_player_game_completes(self) -> None:
        turn_count = 5
        game = Game(10, 10, turn_count=turn_count)
        p1 = Player("alice", "A")
        p2 = Player("bob", "B")
        game.add_player("c1", p1)
        game.add_player("c2", p2)
        game.start()

        while not game.finished:
            game.end_turn(p1)
            if not game.finished:
                game.end_turn(p2)

        self.assertTrue(game.finished)

    def test_idle_players_pnl_stays_zero(self) -> None:
        turn_count = 5
        game = Game(10, 10, turn_count=turn_count)
        p1 = Player("alice", "A")
        p2 = Player("bob", "B")
        game.add_player("c1", p1)
        game.add_player("c2", p2)
        game.start()

        while not game.finished:
            self.assertEqual(p1.profit_and_loss, 0)
            self.assertEqual(p2.profit_and_loss, 0)
            game.end_turn(p1)
            if not game.finished:
                game.end_turn(p2)

        self.assertEqual(p1.profit_and_loss, 0)
        self.assertEqual(p2.profit_and_loss, 0)


class TestOilDiscovery(unittest.TestCase):
    def test_drilling_finds_oil_at_correct_depth(self) -> None:
        random.seed(42)
        theme = DefaultTheme()
        game = Game(10, 10, theme=theme)
        field = game.oil_field

        oil_site = None
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                if site.reservoir is not None:
                    oil_site = site
                    break
            if oil_site is not None:
                break

        self.assertIsNotNone(
            oil_site, "seed 42 must produce at least one oil site on 10x10"
        )
        assert oil_site is not None

        player = Player("alice", "A")
        well = Well(week=1, player=player)
        oil_site.well = well

        assert oil_site.reservoir is not None
        oil_depth = oil_site.reservoir.oil_depth
        assert oil_depth is not None

        for _ in range(oil_depth - 1):
            found, _ = well.drill(oil_site, theme.get_drill_increment())
            self.assertFalse(found)
            self.assertIsNone(oil_site.oil_depth)

        found, _ = well.drill(oil_site, theme.get_drill_increment())
        self.assertTrue(found)
        oil_site.oil_depth = well.drill_depth
        self.assertEqual(oil_site.oil_depth, oil_depth)
        self.assertEqual(well.drill_depth, oil_depth)


class TestMultiplayerTurnOrder(unittest.TestCase):
    def test_three_player_survey_order_across_two_weeks(self) -> None:
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 5)
        h1 = service.join(client_handle, "alice", "A")
        h2 = service.join(client_handle, "bob", "B")
        h3 = service.join(client_handle, "carol", "C")
        service.start(h1)

        for week in range(2):
            self.assertEqual(service.get_players_turn(client_handle), "alice")
            service.survey(h1, week, 0)

            self.assertEqual(service.get_players_turn(client_handle), "bob")
            service.survey(h2, week, 1)

            self.assertEqual(service.get_players_turn(client_handle), "carol")
            service.survey(h3, week, 2)

            self.assertIsNone(service.get_players_turn(client_handle))

            service.end_turn(h1)
            service.end_turn(h2)
            service.end_turn(h3)


if __name__ == "__main__":
    unittest.main()
