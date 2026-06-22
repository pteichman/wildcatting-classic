import pytest

from wildcatting.model import Player
from wildcatting.week import Week


class TestWeek:
    def testGetOilPrice(self) -> None:
        week = Week(1, [Player("alice", "A")], 5.00)
        assert week.price == pytest.approx(5.00)

    def testFirstSurveyTurn(self) -> None:
        players = []
        players.append(Player("alice", "A"))
        players.append(Player("bob", "B"))

        week = Week(1, players, 5.00)

        assert players[0] == week.survey_player

    def testTurnProgression(self) -> None:
        players = []
        players.append(Player("alice", "A"))
        players.append(Player("bob", "B"))

        week = Week(1, players, 5.00)
        assert players[0] == week.survey_player
        assert week.is_survey_turn(players[0])
        assert not week.is_survey_turn(players[1])

        for player in players:
            assert not week.is_turn_finished(player)

        week.end_survey(players[0])
        assert players[1] == week.survey_player
        assert week.is_survey_turn(players[1])
        assert not week.is_survey_turn(players[0])

        week.end_survey(players[1])
        assert week.survey_player is None

        for player in players:
            assert not week.is_turn_finished(player)

        assert players[0] in week.pending_players
        week.end_turn(players[0])
        assert players[0] not in week.pending_players

        assert players[1] in week.pending_players
        week.end_turn(players[1])
        assert players[1] not in week.pending_players

        for player in players:
            assert week.is_turn_finished(player)

        assert week.finished
