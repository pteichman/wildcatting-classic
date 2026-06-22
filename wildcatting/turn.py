class Turn:
    def __init__(self):
        self._week = 0
        self._drilledSite = None
        self._surveyedSite = None

    def get_week(self):
        return self._week

    def set_week(self, week):
        self._week = week

    def set_player(self, player):
        self._player = player

    def get_player(self):
        return self._player

    def get_drilled_site(self):
        return self._drilledSite

    def set_drilled_site(self, drilledSite):
        self._drilledSite = drilledSite

    def get_surveyed_site(self):
        return self._surveyedSite

    def set_surveyed_site(self, surveyedSite):
        self._surveyedSite = surveyedSite
