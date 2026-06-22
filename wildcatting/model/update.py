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

    def get_week(self):
        return self._week

    def set_week(self, week):
        self._week = week

    def get_oil_price(self):
        return self._oilPrice

    def set_oil_price(self, oilPrice):
        self._oilPrice = oilPrice

    def get_players_turn(self):
        return self._playersTurn

    def set_players_turn(self, playersTurn):
        self._playersTurn = playersTurn

    def get_pending_players(self):
        return self._pendingPlayers

    def set_pending_players(self, pendingPlayers):
        self._pendingPlayers = pendingPlayers

    def get_game_finished(self):
        return self._gameFinished

    def set_game_finished(self, gameFinished):
        self._gameFinished = gameFinished

    def get_sites(self):
        return self._sites

    def set_sites(self, sites):
        self._sites = sites
