from serialize import Serializable

class Player(Serializable):
    def __init__(self, username, symbol):
        assert isinstance(username, str)
        assert isinstance(symbol, str)
        assert len(symbol) == 1

        self._username = username
        self._symbol = symbol

    def getUsername(self):
        return self._username

    def getSymbol(self):
        return self._symbol
