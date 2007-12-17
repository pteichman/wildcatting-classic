import unittest
import base64

from wildcatting.server import GameService

class TestGameService(unittest.TestCase):
    def testGameStart(self):
        service = GameService()

        gameId = service.new(10, 10)

        handle = service.join(gameId, "username", "U")
        print base64.b64decode(handle)

if __name__ == "__main__":
    unittest.main()
