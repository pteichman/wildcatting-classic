import pytest

from wildcatting.exceptions import WildcattingException
from wildcatting.game import Game, OilFiller, TaxFiller
from wildcatting.model import OilField, Player
from wildcatting.theme import DefaultTheme


class TestOilFiller:
    def testFreshField(self) -> None:
        rows = cols = 10

        field = OilField(rows, cols)
        filler = OilFiller(DefaultTheme())
        filler.fill(field)

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)

                assert site is not None
                assert site.probability >= 0
                assert site.probability <= 100


class TestTaxFiller:
    def testFreshField(self) -> None:
        rows = cols = 10

        field = OilField(rows, cols)
        OilFiller(DefaultTheme()).fill(field)
        TaxFiller(DefaultTheme()).fill(field)

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)

                assert site is not None
                assert site.tax >= 0


class TestGame:
    def testAddPlayer(self) -> None:
        game = Game(10, 10)

        player = Player("alice", "A")
        game.add_player("test_client", player)

        assert player in game.get_players()

    def testTwoPlayers(self) -> None:
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.add_player("test_client", player1)
        assert player1 in game.get_players()

        player2 = Player("bob", "B")
        game.add_player("test_client", player2)
        assert player2 in game.get_players()

        assert player1 in game.get_players()

    def testTwoPlayerOrder(self) -> None:
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")
        game.add_player("test_client", player1)
        game.add_player("test_client", player2)

        players = game.get_players()
        assert len(players) == 2

        assert player1 == players[0]
        assert player2 == players[1]

    def testRejoin(self) -> None:
        game = Game(10, 10)

        player1 = Player("alice", "A")

        game.add_player("test_client", player1)
        assert player1 in game.get_players()

        with pytest.raises(WildcattingException):
            game.add_player("test_client", player1)

    def testStartGame(self) -> None:
        game = Game(10, 10)

        player1 = Player("alice", "A")
        game.add_player("test_client", player1)

        assert game.started is False
        game.start()
        assert game.started is True

    def testFinishGame(self) -> None:
        game = Game(10, 10, turn_count=1)

        player1 = Player("alice", "A")
        game.add_player("test_client", player1)

        assert game.started is False
        game.start()
        assert game.started is True

        assert game.finished is False
        game.end_turn(player1)
        assert game.finished is True

    def testWeekIncrement(self) -> None:
        game = Game(10, 10)

        player1 = Player("alice", "A")
        player2 = Player("bob", "B")

        game.add_player("test_client", player1)
        assert player1 in game.get_players()
        game.add_player("test_client", player2)
        assert player2 in game.get_players()

        game.start()
        assert game.started

        # Week 1
        assert game.week.week_num == 1
        game.end_turn(player1)
        assert game.week.week_num == 1
        game.end_turn(player2)

        # Week 2
        assert game.week.week_num == 2
        game.end_turn(player1)
        assert game.week.week_num == 2
        game.end_turn(player2)

        # Week 3
        assert game.week.week_num == 3
        game.end_turn(player1)
        assert game.week.week_num == 3
        game.end_turn(player2)
