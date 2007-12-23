import unittest
import base64

from wildcatting.server import GameService

class TestGameService(unittest.TestCase):
    def testGameStart(self):
        service = GameService()

        username = "username"
        well = username[0].upper()

        gameId = service.new(10, 10)
        handle = service.join(gameId, username, well)

        game, player = service._readHandle(handle)
        self.assertEquals(username, player.getUsername())

if __name__ == "__main__":
    unittest.main()
