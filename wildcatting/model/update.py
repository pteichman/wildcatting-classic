from .serialize import Serializable


class Update(Serializable):
    def __init__(
        self, week, oilPrice, playersTurn, pendingPlayers, gameFinished, sites
    ):
        self._week = week
        self._oilPrice = oilPrice
        self._playersTurn = playersTurn
        self._pendingPlayers = pendingPlayers
        self._gameFinished = gameFinished
        self._sites = sites

    @property
    def week(self):
        return self._week

    @week.setter
    def week(self, week):
        self._week = week

    @property
    def oil_price(self):
        return self._oilPrice

    @oil_price.setter
    def oil_price(self, oilPrice):
        self._oilPrice = oilPrice

    @property
    def players_turn(self):
        return self._playersTurn

    @players_turn.setter
    def players_turn(self, playersTurn):
        self._playersTurn = playersTurn

    @property
    def pending_players(self):
        return self._pendingPlayers

    @pending_players.setter
    def pending_players(self, pendingPlayers):
        self._pendingPlayers = pendingPlayers

    @property
    def game_finished(self):
        return self._gameFinished

    @game_finished.setter
    def game_finished(self, gameFinished):
        self._gameFinished = gameFinished

    @property
    def sites(self):
        return self._sites

    @sites.setter
    def sites(self, sites):
        self._sites = sites
