import unittest
import base64

from wildcatting.exceptions import WildcattingException
from wildcatting.server import GameService

from wildcatting.model import Site, Well
from wildcatting.theme import DefaultTheme

class TestGameService(unittest.TestCase):
    def testGameStart(self):
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        gameId = service.new(10, 10, 13)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._readHandle(handle1)

        self.assertEquals(False, service.isStarted(handle1))
        service.start(handle1)
        self.assertEquals(True, service.isStarted(handle1))

    def testShortGame(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        name2 = "bob"
        well2 = name2[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)
        handle2 = service.join(gameId, name2, well2)

        game, player1 = service._readHandle(handle1)
        game, player2 = service._readHandle(handle2)

        self.assertEquals(False, service.isStarted(handle1))
        self.assertEquals(False, service.isStarted(handle2))

        # make sure player 2 isn't the game master
        self.assertRaises(WildcattingException, service.start, handle2)

        # start the game
        service.start(handle1)

        # make sure both players see the game started
        self.assertEquals(True, service.isStarted(handle1))
        self.assertEquals(True, service.isStarted(handle2))

        # make sure it's week 1
        game, player = service._readHandle(handle1)
        self.assertEquals(1, game.getWeek().getWeekNum())

        # it's player 1's turn - make sure player 2 can't survey
        self.assertRaises(WildcattingException, service.survey, handle2, 0, 0)

        # survey as player 1
        site1 = Site.deserialize(service.survey(handle1, 0, 0))

        # make sure player 1 can't survey twice in one turn
        self.assertRaises(WildcattingException, service.survey, handle1, 0, 0)

        # end player 1's turn
        service.endTurn(handle1)

        # make sure player 1 can't survey anymore
        self.assertRaises(WildcattingException, service.survey, handle1, 0, 0)

        # make sure it's still week 1
        game, player = service._readHandle(handle1)
        self.assertEquals(1, game.getWeek().getWeekNum())

        # survey as player 2
        site2 = Site.deserialize(service.survey(handle2, 0, 1))

        # end player 2's turn
        service.endTurn(handle2)

        # make sure player 2 can't survey anymore
        self.assertRaises(WildcattingException, service.survey, handle2, 0, 0)

        # make sure week is 2
        game, player = service._readHandle(handle1)
        self.assertEquals(2, game.getWeek().getWeekNum())

        # make sure both players see the game ended
        self.assertEquals(True, service.isFinished(handle1))
        self.assertEquals(True, service.isFinished(handle2))

    def testDrilling(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._readHandle(handle1)
        self.assertEquals(False, service.isStarted(handle1))

        # start the game
        service.start(handle1)
        self.assertEquals(True, service.isStarted(handle1))

        x, y = 0, 0

        # survey
        site = Site.deserialize(service.survey(handle1, x, y))
        site = Site.deserialize(service.erect(handle1, x, y))

        well = site.getWell()
        while well.getOutput() is None and well.getDrillDepth() < 10:
            well = Well.deserialize(service.drill(handle1, x, y))

    def testSneakyErecting(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._readHandle(handle1)
        self.assertEquals(False, service.isStarted(handle1))

        # start the game
        service.start(handle1)

        self.assertEquals(True, service.isStarted(handle1))

        # survey
        site1 = Site.deserialize(service.survey(handle1, 0, 0))

        # make sure we can't erect elsewhere
        self.assertRaises(WildcattingException, service.survey, handle1, 0, 1)

    def testSneakyDrilling(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._readHandle(handle1)
        self.assertEquals(False, service.isStarted(handle1))

        # start the game
        service.start(handle1)

        self.assertEquals(True, service.isStarted(handle1))

        x, y = 0, 0

        # survey
        site = Site.deserialize(service.survey(handle1, x, y))
        site = Site.deserialize(service.erect(handle1, x, y))

        well = Well.deserialize(service.drill(handle1, x, y))
        self.assertRaises(WildcattingException, service.drill, handle1, x, y+1)

    def testSimultaneousGame(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        name2 = "bob"
        well2 = name2[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)
        handle2 = service.join(gameId, name2, well2)

        game, player1 = service._readHandle(handle1)
        game, player2 = service._readHandle(handle2)

        self.assertEquals(False, service.isStarted(handle1))
        self.assertEquals(False, service.isStarted(handle2))

        service.start(handle1)

        self.assertEquals(name1, service.getPlayersTurn(handle1))
        self.assertEquals(name1, service.getPlayersTurn(handle2))
        site1 = Site.deserialize(service.survey(handle1, 0, 0))

        self.assertEquals(name2, service.getPlayersTurn(handle1))
        self.assertEquals(name2, service.getPlayersTurn(handle2))
        site2 = Site.deserialize(service.survey(handle2, 0, 1))

        service.endTurn(handle1)
        service.endTurn(handle2)

    def testGameWithoutSurvey(self):
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        name2 = "bob"
        well2 = name2[0].upper()

        name3 = "carol"
        well3 = name3[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)
        handle2 = service.join(gameId, name2, well2)
        handle3 = service.join(gameId, name3, well3)

        game, player1 = service._readHandle(handle1)
        game, player2 = service._readHandle(handle2)
        game, player3 = service._readHandle(handle3)

        service.start(handle1)

        self.assertEquals(name1, service.getPlayersTurn(handle1))
        self.assertEquals(name1, service.getPlayersTurn(handle2))
        self.assertEquals(name1, service.getPlayersTurn(handle3))
        site1 = Site.deserialize(service.survey(handle1, 0, 0))

        service.endTurn(handle1)

        self.assertEquals(name2, service.getPlayersTurn(handle1))
        self.assertEquals(name2, service.getPlayersTurn(handle2))
        self.assertEquals(name2, service.getPlayersTurn(handle3))

        service.endTurn(handle2)

        self.assertEquals(name3, service.getPlayersTurn(handle1))
        self.assertEquals(name3, service.getPlayersTurn(handle2))
        self.assertEquals(name3, service.getPlayersTurn(handle3))

        service.endTurn(handle3)

        self.assertEquals(name1, service.getPlayersTurn(handle1))
        self.assertEquals(name1, service.getPlayersTurn(handle2))
        self.assertEquals(name1, service.getPlayersTurn(handle3))


if __name__ == "__main__":
    unittest.main()
