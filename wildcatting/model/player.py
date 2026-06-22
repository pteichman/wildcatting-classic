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

    @property
    def username(self):
        return self._username

    @property
    def symbol(self):
        return self._symbol

    @property
    def secret(self):
        return self._secret or ""

    @secret.setter
    def secret(self, secret):
        assert isinstance(secret, str)
        self._secret = secret

    @property
    def profit_and_loss(self):
        return self._profitAndLoss

    def income(self, income):
        self._profitAndLoss += income

    def expense(self, expense):
        self._profitAndLoss -= expense
