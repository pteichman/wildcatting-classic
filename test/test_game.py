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

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assert_(site.getProbability() >= 0)
                self.assert_(site.getProbability() <= 100)

class TestTaxFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        OilFiller(DefaultTheme()).fill(field)
        TaxFiller(DefaultTheme()).fill(field)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assert_(site.getTax() >= 0)

class TestGame(unittest.TestCase):
    def testAddPlayer(self):
        game = Game(10, 10)

        player = Player("alice", "A")
        game.addPlayer(player)

        self.assert_(player in game.getPlayers())

    def testTwoPlayers(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.addPlayer(player1)
        self.assert_(player1 in game.getPlayers())

        player2 = Player("bob", "B")
        game.addPlayer(player2)
        self.assert_(player2 in game.getPlayers())

        self.assert_(player1 in game.getPlayers())

    def testTwoPlayerOrder(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")
        game.addPlayer(player1)
        game.addPlayer(player2)

        players = game.getPlayers()
        self.assert_(len(players) == 2)

        self.assertEquals(player1, players[0])
        self.assertEquals(player2, players[1])

    def testRejoin(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")

        secret1 = game.addPlayer(player1)
        self.assert_(player1 in game.getPlayers())

        self.assertRaises(WildcattingException, game.addPlayer, player1)

    def testStartGame(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.addPlayer(player1)

        self.assertEquals(False, game.isStarted())
        game.start()
        self.assertEquals(True, game.isStarted())

    def testFinishGame(self):
        game = Game(10, 10, turnCount=1)

        player1 = Player("alice", "A")
        game.addPlayer(player1)

        self.assertEquals(False, game.isStarted())
        game.start()
        self.assertEquals(True, game.isStarted())

        self.assertEquals(False, game.isFinished())
        game.endTurn(player1)
        self.assertEquals(True, game.isFinished())

    def testWeekIncrement(self):
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")

        secret1 = game.addPlayer(player1)
        self.assert_(player1 in game.getPlayers())
        secret2 = game.addPlayer(player2)
        self.assert_(player2 in game.getPlayers())

        game.start()
        self.assertTrue(game.isStarted())

        # Week 1
        self.assertEquals(1, game._turn.getWeek())
        game.endTurn(player1)
        self.assertEquals(1, game._turn.getWeek())
        game.endTurn(player2)

        # Week 2
        self.assertEquals(2, game._turn.getWeek())
        game.endTurn(player1)
        self.assertEquals(2, game._turn.getWeek())
        game.endTurn(player2)

        # Week 3
        self.assertEquals(3, game._turn.getWeek())
        game.endTurn(player1)
        self.assertEquals(3, game._turn.getWeek())
        game.endTurn(player2)

if __name__ == "__main__":
    unittest.main()
