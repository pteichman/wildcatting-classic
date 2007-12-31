import unittest
import base64

from wildcatting.exceptions import WildcattingException
from wildcatting.server import GameService

from wildcatting.model import Site

class TestGameService(unittest.TestCase):
    def testGameStart(self):
        service = GameService()

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
        service = GameService()

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

        # survey as player 2
        site2 = Site.deserialize(service.survey(handle2, 0, 1))

        # end player 2's turn
        service.endTurn(handle2)

        # make sure player 2 can't survey anymore
        self.assertRaises(WildcattingException, service.survey, handle2, 0, 0)

        # make sure both players see the game ended
        self.assertEquals(True, service.isFinished(handle1))
        self.assertEquals(True, service.isFinished(handle2))

if __name__ == "__main__":
    unittest.main()
