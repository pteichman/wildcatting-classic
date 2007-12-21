class Turn:
    def __init__(self):
        self._week = 0
        self._drilledSite = None
        self._surveyedSite = None

    def getWeek(self):
        return self._week

    def setWeek(self, week):
        self._week = week

    def setPlayer(self, player):
        self._player = player

    def getPlayer(self):
        return self._player
        
    def getDrilledSite(self):
        return self._drilledSite

    def setDrilledSite(self, drilledSite):
        self._drilledSite = drilledSite

    def getSurveyedSite(self):
        return self._surveyedSite

    def setSurveyedSite(self, surveyedSite):
        self._surveyedSite = surveyedSite
