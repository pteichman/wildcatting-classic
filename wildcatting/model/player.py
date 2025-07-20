from .serialize import Serializable

class Player(Serializable):
    def __init__(self, username, symbol):
        assert isinstance(username, str)
        assert isinstance(symbol, str)
        assert len(symbol) == 1

        self._username = username
        self._symbol = symbol
        self._secret = None

        self._profitAndLoss = 0

    def getUsername(self):
        return self._username

    def getSymbol(self):
        return self._symbol

    def getSecret(self):
        return self._secret or ""

    def setSecret(self, secret):
        assert isinstance(secret, str)
        self._secret = secret

    def getProfitAndLoss(self):
        return self._profitAndLoss

    def income(self, income):
        self._profitAndLoss += income

    def expense(self, expense):
        self._profitAndLoss -= expense
