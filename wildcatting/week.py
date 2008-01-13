import wildcatting.turn

class Week:
    def __init__(self, weekNum, players, price):
        self._weekNum = weekNum

        # copy the players array, so joins and exits don't affect this week
        self._players = players[:]
        self._surveyPlayerIndex = 0
        self._surveysDone = False

        self._price = price
        self._remaining = self._players[:]
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

    def getSurveyTurn(self):
        if self._surveysDone:
            return None

        return self._players[self._surveyPlayerIndex]

    def getPlayerTurn(self, player):
        return self._turns.get(player)

    def isSurveyTurn(self, player):
        return self.getSurveyTurn() == player

    def endSurvey(self, player):
        assert self.getSurveyTurn() == player

        self._surveyPlayerIndex = self._surveyPlayerIndex + 1

        if self._surveyPlayerIndex > len(self._players) - 1:
            self._surveysDone = True

    def endTurn(self, player):
        self._remaining.remove(player)

    def isTurnFinished(self, player):
        playerIndex = self._players.index(player)

        if playerIndex < self._surveyPlayerIndex \
               and player not in self._remaining:
            return True

        return False

    def isFinished(self):
        "Checking for finished week: len is %d" % len(self._remaining)
        return len(self._remaining) == 0
