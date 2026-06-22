from .serialize import Serializable


class Player(Serializable):
    def __init__(self, username, symbol):
        assert isinstance(username, str)
        assert isinstance(symbol, str)
        assert len(symbol) == 1

        self.username = username
        self.symbol = symbol
        self._secret = None

        self.profit_and_loss = 0

    @property
    def secret(self):
        return self._secret or ""

    @secret.setter
    def secret(self, secret):
        assert isinstance(secret, str)
        self._secret = secret

    def income(self, income):
        self.profit_and_loss += income

    def expense(self, expense):
        self.profit_and_loss -= expense
