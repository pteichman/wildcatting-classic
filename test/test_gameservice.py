import pytest

from wildcatting.exceptions import WildcattingException
from wildcatting.model import Site, Well
from wildcatting.server import GameService
from wildcatting.theme import DefaultTheme


class TestGameService:
    def testGameStart(self) -> None:
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        gameId = service.new(10, 10, 13)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)

        assert service.is_started(handle1) is False
        service.start(handle1)
        assert service.is_started(handle1) is True

    def testShortGame(self) -> None:
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

        assert service.is_started(handle1) is False
        assert service.is_started(handle2) is False

        # make sure player 2 isn't the game master
        with pytest.raises(WildcattingException):
            service.start(handle2)

        # start the game
        service.start(handle1)

        # make sure both players see the game started
        assert service.is_started(handle1) is True
        assert service.is_started(handle2) is True

        # make sure it's week 1
        game, player = service._read_handle(handle1)
        assert game.week.week_num == 1

        # it's player 1's turn - make sure player 2 can't survey
        with pytest.raises(WildcattingException):
            service.survey(handle2, 0, 0)

        # survey as player 1
        Site.deserialize(service.survey(handle1, 0, 0))

        # make sure player 1 can't survey twice in one turn
        with pytest.raises(WildcattingException):
            service.survey(handle1, 0, 0)

        # end player 1's turn
        service.end_turn(handle1)

        # make sure player 1 can't survey anymore
        with pytest.raises(WildcattingException):
            service.survey(handle1, 0, 0)

        # make sure it's still week 1
        game, player = service._read_handle(handle1)
        assert game.week.week_num == 1

        # survey as player 2
        Site.deserialize(service.survey(handle2, 0, 1))

        # end player 2's turn
        service.end_turn(handle2)

        # make sure player 2 can't survey anymore
        with pytest.raises(WildcattingException):
            service.survey(handle2, 0, 0)

        # make sure week is 2
        game, player = service._read_handle(handle1)
        assert game.week.week_num == 2

        # make sure both players see the game ended
        assert service.is_finished(handle1) is True
        assert service.is_finished(handle2) is True

    def testDrilling(self) -> None:
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)
        assert service.is_started(handle1) is False

        # start the game
        service.start(handle1)
        assert service.is_started(handle1) is True

        x, y = 0, 0

        # survey
        site = Site.deserialize(service.survey(handle1, x, y))
        site = Site.deserialize(service.erect(handle1, x, y))

        well = site.well
        assert well is not None
        while well.output is None and well.drill_depth < 10:
            well = Well.deserialize(service.drill(handle1, x, y))

    def testSneakyErecting(self) -> None:
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)
        assert service.is_started(handle1) is False

        # start the game
        service.start(handle1)

        assert service.is_started(handle1) is True

        # survey
        Site.deserialize(service.survey(handle1, 0, 0))

        # make sure we can't erect elsewhere
        with pytest.raises(WildcattingException):
            service.survey(handle1, 0, 1)

    def testSneakyDrilling(self) -> None:
        # start a game, survey once by each player
        service = GameService(DefaultTheme())

        name1 = "alice"
        well1 = name1[0].upper()

        # create the game, join it
        gameId = service.new(10, 10, 1)
        handle1 = service.join(gameId, name1, well1)

        game, player1 = service._read_handle(handle1)
        assert service.is_started(handle1) is False

        # start the game
        service.start(handle1)

        assert service.is_started(handle1) is True

        x, y = 0, 0

        # survey
        Site.deserialize(service.survey(handle1, x, y))
        Site.deserialize(service.erect(handle1, x, y))

        Well.deserialize(service.drill(handle1, x, y))
        with pytest.raises(WildcattingException):
            service.drill(handle1, x, y + 1)

    def testSimultaneousGame(self) -> None:
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

        assert service.is_started(handle1) is False
        assert service.is_started(handle2) is False

        service.start(handle1)

        assert service.get_players_turn(handle1) == name1
        assert service.get_players_turn(handle2) == name1
        Site.deserialize(service.survey(handle1, 0, 0))

        assert service.get_players_turn(handle1) == name2
        assert service.get_players_turn(handle2) == name2
        Site.deserialize(service.survey(handle2, 0, 1))

        service.end_turn(handle1)
        service.end_turn(handle2)

    def testGameWithoutSurvey(self) -> None:
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
        game, _ = service._read_handle(handle3)

        service.start(handle1)

        assert service.get_players_turn(handle1) == name1
        assert service.get_players_turn(handle2) == name1
        assert service.get_players_turn(handle3) == name1
        Site.deserialize(service.survey(handle1, 0, 0))

        service.end_turn(handle1)

        assert service.get_players_turn(handle1) == name2
        assert service.get_players_turn(handle2) == name2
        assert service.get_players_turn(handle3) == name2

        service.end_turn(handle2)

        assert service.get_players_turn(handle1) == name3
        assert service.get_players_turn(handle2) == name3
        assert service.get_players_turn(handle3) == name3

        service.end_turn(handle3)

        assert service.get_players_turn(handle1) == name1
        assert service.get_players_turn(handle2) == name1
        assert service.get_players_turn(handle3) == name1


class TestMultiplayerTurnOrder:
    def test_three_player_survey_order_across_two_weeks(self) -> None:
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 5)
        h1 = service.join(client_handle, "alice", "A")
        h2 = service.join(client_handle, "bob", "B")
        h3 = service.join(client_handle, "carol", "C")
        service.start(h1)

        for week in range(2):
            assert service.get_players_turn(client_handle) == "alice"
            service.survey(h1, week, 0)

            assert service.get_players_turn(client_handle) == "bob"
            service.survey(h2, week, 1)

            assert service.get_players_turn(client_handle) == "carol"
            service.survey(h3, week, 2)

            assert service.get_players_turn(client_handle) is None

            service.end_turn(h1)
            service.end_turn(h2)
            service.end_turn(h3)


class TestGameServiceSell:
    def _started_game(self) -> tuple[GameService, str, str]:
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 13)
        handle = service.join(client_handle, "alice", "A")
        service.start(handle)
        return service, client_handle, handle

    def test_sell_raises_if_no_well(self) -> None:
        service, client_handle, handle = self._started_game()
        service.survey(handle, 0, 0)
        with pytest.raises(WildcattingException):
            service.sell(handle, 0, 0)

    def test_sell_raises_if_already_sold(self) -> None:
        service, client_handle, handle = self._started_game()
        service.survey(handle, 0, 0)
        service.erect(handle, 0, 0)
        service.sell(handle, 0, 0)
        with pytest.raises(WildcattingException):
            service.sell(handle, 0, 0)

    def test_sell_raises_if_wrong_player(self) -> None:
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 13)
        handle1 = service.join(client_handle, "alice", "A")
        handle2 = service.join(client_handle, "bob", "B")
        service.start(handle1)

        # alice surveys and erects at (0, 0)
        service.survey(handle1, 0, 0)
        service.erect(handle1, 0, 0)

        # bob tries to sell alice's well
        with pytest.raises(WildcattingException):
            service.sell(handle2, 0, 0)

    def test_sell_returns_positive_price(self) -> None:
        service, client_handle, handle = self._started_game()
        service.survey(handle, 0, 0)
        service.erect(handle, 0, 0)
        price = service.sell(handle, 0, 0)
        assert price > 0
