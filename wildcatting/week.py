import logging

import wildcatting.turn
from wildcatting.model import Player
from wildcatting.turn import Turn


class Week:
    log = logging.getLogger("Wildcatting")

    def __init__(self, weekNum: int, players: list[Player], price: float) -> None:
        self.week_num = weekNum

        # copy the players array, so joins and exits don't affect this week
        self._players = players[:]
        self._surveyPlayerIndex: int = 0
        self._surveysDone: bool = False

        self.price = price
        self.pending_players: list[Player] = self._players[:]
        self._turns: dict[Player, Turn] = {}

        for player in self._players:
            self._turns[player] = wildcatting.turn.Turn(week=weekNum, player=player)

    @property
    def survey_player(self) -> Player | None:
        if self._surveysDone:
            return None

        return self._players[self._surveyPlayerIndex]

    def get_player_turn(self, player: Player) -> Turn:
        assert isinstance(player, Player)

        return self._turns[player]

    def is_survey_turn(self, player: Player) -> bool:
        assert isinstance(player, Player)

        return self.survey_player == player

    def end_survey(self, player: Player) -> None:
        assert isinstance(player, Player)
        assert self.is_survey_turn(player)

        self._surveyPlayerIndex = self._surveyPlayerIndex + 1

        if self._surveyPlayerIndex > len(self._players) - 1:
            self._surveysDone = True

    def end_turn(self, player: Player) -> None:
        assert isinstance(player, Player)
        assert player in self.pending_players

        if self.is_survey_turn(player):
            self.end_survey(player)

        self.pending_players.remove(player)

    def is_turn_finished(self, player: Player) -> bool:
        assert isinstance(player, Player)
        playerIndex = self._players.index(player)

        if playerIndex < self._surveyPlayerIndex and player not in self.pending_players:
            return True

        return False

    @property
    def finished(self) -> bool:
        return len(self.pending_players) == 0
