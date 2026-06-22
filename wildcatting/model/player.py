from .serialize import Serializable


class Player(Serializable):
    def __init__(self, username: str, symbol: str) -> None:
        assert isinstance(username, str)
        assert isinstance(symbol, str)
        assert len(symbol) == 1

        self.username = username
        self.symbol = symbol
        self._secret: str | None = None

        self.profit_and_loss: int = 0

    @property
    def secret(self) -> str:
        return self._secret or ""

    @secret.setter
    def secret(self, secret: str) -> None:
        assert isinstance(secret, str)
        self._secret = secret

    def income(self, income: int) -> None:
        self.profit_and_loss += income

    def expense(self, expense: int) -> None:
        self.profit_and_loss -= expense
