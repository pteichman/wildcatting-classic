from .serialize import Serializable

class Update(Serializable):
    def __init__(self, week, oilPrice, playersTurn, pendingPlayers, gameFinished, sites):
        self._week = week
        self._oilPrice = oilPrice
        self._playersTurn = playersTurn
        self._pendingPlayers = pendingPlayers
        self._gameFinished = gameFinished
        self._sites = sites

    def getWeek(self):
        return self._week

    def setWeek(self, week):
        self._week = week

    def getOilPrice(self):
        return self._oilPrice

    def setOilPrice(self, oilPrice):
        self._oilPrice = oilPrice

    def getPlayersTurn(self):
        return self._playersTurn

    def setPlayersTurn(self, playersTurn):
        self._playersTurn = playersTurn

    def getPendingPlayers(self):
        return self._pendingPlayers

    def setPendingPlayers(self, pendingPlayers):
        self._pendingPlayers = pendingPlayers

    def getGameFinished(self):
        return self._gameFinished

    def setGameFinished(self, gameFinished):
        self._gameFinished = gameFinished

    def getSites(self):
        return self._sites

    def setSites(self, sites):
        self._sites = sites
