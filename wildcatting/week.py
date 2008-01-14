import logging
from wildcatting.model import Player
import wildcatting.turn

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
            turn.setPlayer(player)
            turn.setWeek(weekNum)
            self._turns[player] = turn

    def getWeekNum(self):
        return self._weekNum

    def getPrice(self):
        return self._price

    def getSurveyPlayer(self):
        if self._surveysDone:
            return None

        return self._players[self._surveyPlayerIndex]

    def getPlayerTurn(self, player):
        assert isinstance(player, Player)

        return self._turns.get(player)

    def isSurveyTurn(self, player):
        assert isinstance(player, Player)

        return self.getSurveyPlayer() == player

    def endSurvey(self, player):
        assert isinstance(player, Player)
        assert self.isSurveyTurn(player)

        self._surveyPlayerIndex = self._surveyPlayerIndex + 1

        if self._surveyPlayerIndex > len(self._players) - 1:
            self._surveysDone = True

    def endTurn(self, player):
        assert isinstance(player, Player)
        assert player in self._pending

        if self.isSurveyTurn(player):
            self.endSurvey(player)

        self._pending.remove(player)

    def isTurnFinished(self, player):
        assert isinstance(player, Player)
        playerIndex = self._players.index(player)

        if playerIndex < self._surveyPlayerIndex \
               and player not in self._pending:
            return True

        return False

    def getPendingPlayers(self):
        return self._pending

    def isFinished(self):
        return len(self._pending) == 0
