import unittest

from wildcatting.exceptions import WildcattingException
from wildcatting.model import Site, Well
from wildcatting.server import GameService
from wildcatting.theme import DefaultTheme


class TestGameService(unittest.TestCase):
    def testGameStart(self):
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        gameId = service.new(10, 10, 13)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)

        self.assertEqual(False, service.is_started(handle1))
        service.start(handle1)
        self.assertEqual(True, service.is_started(handle1))

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

        game, player1 = service._read_handle(handle1)
        game, player2 = service._read_handle(handle2)

        self.assertEqual(False, service.is_started(handle1))
        self.assertEqual(False, service.is_started(handle2))

        # make sure player 2 isn't the game master
        self.assertRaises(WildcattingException, service.start, handle2)

        # start the game
        service.start(handle1)

        # make sure both players see the game started
        self.assertEqual(True, service.is_started(handle1))
        self.assertEqual(True, service.is_started(handle2))

        # make sure it's week 1
        game, player = service._read_handle(handle1)
        self.assertEqual(1, game.get_week().get_week_num())

        # it's player 1's turn - make sure player 2 can't survey
        self.assertRaises(WildcattingException, service.survey, handle2, 0, 0)

        # survey as player 1
        Site.deserialize(service.survey(handle1, 0, 0))

        # make sure player 1 can't survey twice in one turn
        self.assertRaises(WildcattingException, service.survey, handle1, 0, 0)

        # end player 1's turn
        service.end_turn(handle1)

        # make sure player 1 can't survey anymore
        self.assertRaises(WildcattingException, service.survey, handle1, 0, 0)

        # make sure it's still week 1
        game, player = service._read_handle(handle1)
        self.assertEqual(1, game.get_week().get_week_num())

        # survey as player 2
        Site.deserialize(service.survey(handle2, 0, 1))

        # end player 2's turn
        service.end_turn(handle2)

        # make sure player 2 can't survey anymore
        self.assertRaises(WildcattingException, service.survey, handle2, 0, 0)

        # make sure week is 2
        game, player = service._read_handle(handle1)
        self.assertEqual(2, game.get_week().get_week_num())

        # make sure both players see the game ended
        self.assertEqual(True, service.is_finished(handle1))
        self.assertEqual(True, service.is_finished(handle2))

    def testDrilling(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)
        self.assertEqual(False, service.is_started(handle1))

        # start the game
        service.start(handle1)
        self.assertEqual(True, service.is_started(handle1))

        x, y = 0, 0

        # survey
        site = Site.deserialize(service.survey(handle1, x, y))
        site = Site.deserialize(service.erect(handle1, x, y))

        well = site.get_well()
        while well.get_output() is None and well.get_drill_depth() < 10:
            well = Well.deserialize(service.drill(handle1, x, y))

    def testSneakyErecting(self):
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)
        self.assertEqual(False, service.is_started(handle1))

        # start the game
        service.start(handle1)

        self.assertEqual(True, service.is_started(handle1))

        # survey
        Site.deserialize(service.survey(handle1, 0, 0))

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

        game, player1 = service._read_handle(handle1)
        self.assertEqual(False, service.is_started(handle1))

        # start the game
        service.start(handle1)

        self.assertEqual(True, service.is_started(handle1))

        x, y = 0, 0

        # survey
        Site.deserialize(service.survey(handle1, x, y))
        Site.deserialize(service.erect(handle1, x, y))

        Well.deserialize(service.drill(handle1, x, y))
        self.assertRaises(WildcattingException, service.drill, handle1, x, y + 1)

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

        game, player1 = service._read_handle(handle1)
        game, player2 = service._read_handle(handle2)

        self.assertEqual(False, service.is_started(handle1))
        self.assertEqual(False, service.is_started(handle2))

        service.start(handle1)

        self.assertEqual(name1, service.get_players_turn(handle1))
        self.assertEqual(name1, service.get_players_turn(handle2))
        Site.deserialize(service.survey(handle1, 0, 0))

        self.assertEqual(name2, service.get_players_turn(handle1))
        self.assertEqual(name2, service.get_players_turn(handle2))
        Site.deserialize(service.survey(handle2, 0, 1))

        service.end_turn(handle1)
        service.end_turn(handle2)

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

        game, player1 = service._read_handle(handle1)
        game, player2 = service._read_handle(handle2)
        game, player3 = service._read_handle(handle3)

        service.start(handle1)

        self.assertEqual(name1, service.get_players_turn(handle1))
        self.assertEqual(name1, service.get_players_turn(handle2))
        self.assertEqual(name1, service.get_players_turn(handle3))
        Site.deserialize(service.survey(handle1, 0, 0))

        service.end_turn(handle1)

        self.assertEqual(name2, service.get_players_turn(handle1))
        self.assertEqual(name2, service.get_players_turn(handle2))
        self.assertEqual(name2, service.get_players_turn(handle3))

        service.end_turn(handle2)

        self.assertEqual(name3, service.get_players_turn(handle1))
        self.assertEqual(name3, service.get_players_turn(handle2))
        self.assertEqual(name3, service.get_players_turn(handle3))

        service.end_turn(handle3)

        self.assertEqual(name1, service.get_players_turn(handle1))
        self.assertEqual(name1, service.get_players_turn(handle2))
        self.assertEqual(name1, service.get_players_turn(handle3))


if __name__ == "__main__":
    unittest.main()
