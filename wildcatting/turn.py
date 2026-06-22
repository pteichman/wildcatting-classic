class Turn:
    def __init__(self):
        self._week = 0
        self._drilledSite = None
        self._surveyedSite = None

    @property
    def week(self):
        return self._week

    @week.setter
    def week(self, week):
        self._week = week

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, player):
        self._player = player

    @property
    def drilled_site(self):
        return self._drilledSite

    @drilled_site.setter
    def drilled_site(self, drilledSite):
        self._drilledSite = drilledSite

    @property
    def surveyed_site(self):
        return self._surveyedSite

    @surveyed_site.setter
    def surveyed_site(self, surveyedSite):
        self._surveyedSite = surveyedSite
