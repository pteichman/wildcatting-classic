import unittest

from wildcatting.exceptions import WildcattingException
from wildcatting.game import Game, OilFiller, TaxFiller
from wildcatting.model import OilField, Player
from wildcatting.theme import DefaultTheme


class TestOilFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        filler = OilFiller(DefaultTheme())
        filler.fill(field)

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)

                self.assertNotEqual(site, None)
                self.assertTrue(site.probability >= 0)
                self.assertTrue(site.probability <= 100)


class TestTaxFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        OilFiller(DefaultTheme()).fill(field)
        TaxFiller(DefaultTheme()).fill(field)

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)

                self.assertNotEqual(site, None)
                self.assertTrue(site.tax >= 0)


class TestGame(unittest.TestCase):
    def testAddPlayer(self):
        game = Game(10, 10)

        player = Player("alice", "A")
        game.add_player("test_client", player)

        self.assertTrue(player in game.get_players())

    def testTwoPlayers(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.add_player("test_client", player1)
        self.assertTrue(player1 in game.get_players())

        player2 = Player("bob", "B")
        game.add_player("test_client", player2)
        self.assertTrue(player2 in game.get_players())

        self.assertTrue(player1 in game.get_players())

    def testTwoPlayerOrder(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")
        game.add_player("test_client", player1)
        game.add_player("test_client", player2)

        players = game.get_players()
        self.assertTrue(len(players) == 2)

        self.assertEqual(player1, players[0])
        self.assertEqual(player2, players[1])

    def testRejoin(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")

        game.add_player("test_client", player1)
        self.assertTrue(player1 in game.get_players())

        self.assertRaises(WildcattingException, game.add_player, "test_client", player1)

    def testStartGame(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.add_player("test_client", player1)

        self.assertEqual(False, game.started)
        game.start()
        self.assertEqual(True, game.started)

    def testFinishGame(self):
        game = Game(10, 10, turnCount=1)

        player1 = Player("alice", "A")
        game.add_player("test_client", player1)

        self.assertEqual(False, game.started)
        game.start()
        self.assertEqual(True, game.started)

        self.assertEqual(False, game.finished)
        game.end_turn(player1)
        self.assertEqual(True, game.finished)

    def testWeekIncrement(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")

        game.add_player("test_client", player1)
        self.assertTrue(player1 in game.get_players())
        game.add_player("test_client", player2)
        self.assertTrue(player2 in game.get_players())

        game.start()
        self.assertTrue(game.started)

        # Week 1
        self.assertEqual(1, game.week.week_num)
        game.end_turn(player1)
        self.assertEqual(1, game.week.week_num)
        game.end_turn(player2)

        # Week 2
        self.assertEqual(2, game.week.week_num)
        game.end_turn(player1)
        self.assertEqual(2, game.week.week_num)
        game.end_turn(player2)

        # Week 3
        self.assertEqual(3, game.week.week_num)
        game.end_turn(player1)
        self.assertEqual(3, game.week.week_num)
        game.end_turn(player2)


if __name__ == "__main__":
    unittest.main()
