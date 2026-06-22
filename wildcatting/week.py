import logging

import wildcatting.turn
from wildcatting.model import Player


class Week:
    log = logging.getLogger("Wildcatting")

    def __init__(self, weekNum, players, price):
        self._weekNum = weekNum

        # copy the players array, so joins and exits don't affect this week
        self._players = players[:]
        self._surveyPlayerIndex = 0
        self._surveysDone = False

        self._price = price
        self._pending = self._players[:]
        self._turns = {}

        for player in self._players:
            turn = wildcatting.turn.Turn()
            turn.player = player
            turn.week = weekNum
            self._turns[player] = turn

    @property
    def week_num(self):
        return self._weekNum

    @property
    def price(self):
        return self._price

    @property
    def survey_player(self):
        if self._surveysDone:
            return None

        return self._players[self._surveyPlayerIndex]

    def get_player_turn(self, player):
        assert isinstance(player, Player)

        return self._turns.get(player)

    def is_survey_turn(self, player):
        assert isinstance(player, Player)

        return self.survey_player == player

    def end_survey(self, player):
        assert isinstance(player, Player)
        assert self.is_survey_turn(player)

        self._surveyPlayerIndex = self._surveyPlayerIndex + 1

        if self._surveyPlayerIndex > len(self._players) - 1:
            self._surveysDone = True

    def end_turn(self, player):
        assert isinstance(player, Player)
        assert player in self._pending

        if self.is_survey_turn(player):
            self.end_survey(player)

        self._pending.remove(player)

    def is_turn_finished(self, player):
        assert isinstance(player, Player)
        playerIndex = self._players.index(player)

        if playerIndex < self._surveyPlayerIndex and player not in self._pending:
            return True

        return False

    @property
    def pending_players(self):
        return self._pending

    @property
    def finished(self):
        return len(self._pending) == 0
