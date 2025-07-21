import unittest

from wildcatting.exceptions import WildcattingException
from wildcatting.model import OilField, Player
from wildcatting.game import OilFiller, TaxFiller, Game
from wildcatting.theme import DefaultTheme

class TestOilFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        filler = OilFiller(DefaultTheme())
        filler.fill(field)

        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assertTrue(site.getProbability() >= 0)
                self.assertTrue(site.getProbability() <= 100)

class TestTaxFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        OilFiller(DefaultTheme()).fill(field)
        TaxFiller(DefaultTheme()).fill(field)

        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assertTrue(site.getTax() >= 0)

class TestGame(unittest.TestCase):
    def testAddPlayer(self):
        game = Game(10, 10)

        player = Player("alice", "A")
        game.addPlayer("test_client", player)

        self.assertTrue(player in game.getPlayers())

    def testTwoPlayers(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.addPlayer("test_client", player1)
        self.assertTrue(player1 in game.getPlayers())

        player2 = Player("bob", "B")
        game.addPlayer("test_client", player2)
        self.assertTrue(player2 in game.getPlayers())

        self.assertTrue(player1 in game.getPlayers())

    def testTwoPlayerOrder(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")
        game.addPlayer("test_client", player1)
        game.addPlayer("test_client", player2)

        players = game.getPlayers()
        self.assertTrue(len(players) == 2)

        self.assertEqual(player1, players[0])
        self.assertEqual(player2, players[1])

    def testRejoin(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")

        secret1 = game.addPlayer("test_client", player1)
        self.assertTrue(player1 in game.getPlayers())

        self.assertRaises(WildcattingException, game.addPlayer, "test_client", player1)

    def testStartGame(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.addPlayer("test_client", player1)

        self.assertEqual(False, game.isStarted())
        game.start()
        self.assertEqual(True, game.isStarted())

    def testFinishGame(self):
        game = Game(10, 10, turnCount=1)

        player1 = Player("alice", "A")
        game.addPlayer("test_client", player1)

        self.assertEqual(False, game.isStarted())
        game.start()
        self.assertEqual(True, game.isStarted())

        self.assertEqual(False, game.isFinished())
        game.endTurn(player1)
        self.assertEqual(True, game.isFinished())

    def testWeekIncrement(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")

        secret1 = game.addPlayer("test_client", player1)
        self.assertTrue(player1 in game.getPlayers())
        secret2 = game.addPlayer("test_client", player2)
        self.assertTrue(player2 in game.getPlayers())

        game.start()
        self.assertTrue(game.isStarted())

        # Week 1
        self.assertEqual(1, game.getWeek().getWeekNum())
        game.endTurn(player1)
        self.assertEqual(1, game.getWeek().getWeekNum())
        game.endTurn(player2)

        # Week 2
        self.assertEqual(2, game.getWeek().getWeekNum())
        game.endTurn(player1)
        self.assertEqual(2, game.getWeek().getWeekNum())
        game.endTurn(player2)

        # Week 3
        self.assertEqual(3, game.getWeek().getWeekNum())
        game.endTurn(player1)
        self.assertEqual(3, game.getWeek().getWeekNum())
        game.endTurn(player2)

if __name__ == "__main__":
    unittest.main()
