import logging

import wildcatting.turn
from wildcatting.model import Player
from wildcatting.turn import Turn


class Week:
    log = logging.getLogger("Wildcatting")

    def __init__(self, week_num: int, players: list[Player], price: float) -> None:
        self.week_num = week_num

        # copy the players array, so joins and exits don't affect this week
        self._players = players[:]
        self._survey_player_index: int = 0
        self._surveys_done: bool = False

        self.price = price
        self.pending_players: list[Player] = self._players[:]
        self._turns: dict[Player, Turn] = {}

        for player in self._players:
            self._turns[player] = wildcatting.turn.Turn(week=week_num, player=player)

    @property
    def survey_player(self) -> Player | None:
        if self._surveys_done:
            return None

        return self._players[self._survey_player_index]

    def get_player_turn(self, player: Player) -> Turn:
        return self._turns[player]

    def is_survey_turn(self, player: Player) -> bool:
        return self.survey_player == player

    def end_survey(self, player: Player) -> None:
        assert self.is_survey_turn(player)

        self._survey_player_index = self._survey_player_index + 1

        if self._survey_player_index > len(self._players) - 1:
            self._surveys_done = True

    def end_turn(self, player: Player) -> None:
        assert player in self.pending_players

        if self.is_survey_turn(player):
            self.end_survey(player)

        self.pending_players.remove(player)

    def is_turn_finished(self, player: Player) -> bool:
        player_index = self._players.index(player)

        surveyed = player_index < self._survey_player_index
        return bool(surveyed and player not in self.pending_players)

    @property
    def finished(self) -> bool:
        return len(self.pending_players) == 0
