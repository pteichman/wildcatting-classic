from .serialize import Serializable


class ClientInfo(Serializable):
    def __init__(self, clientHandle: str, gameId: str) -> None:
        self._clientHandle = clientHandle
        self._gameId = gameId
        self._players: list[str] = []
        self._handles: dict[str, str] = {}
        self._symbols: dict[str, str] = {}

    @property
    def game_id(self) -> str:
        return self._gameId

    @game_id.setter
    def game_id(self, gameId: str) -> None:
        self._gameId = gameId

    @property
    def client_handle(self) -> str:
        return self._clientHandle

    @client_handle.setter
    def client_handle(self, clientHandle: str) -> None:
        self._clientHandle = clientHandle

    def add_player_info(self, username: str, handle: str, symbol: str) -> None:
        self._players.append(username)
        self._handles[username] = handle
        self._symbols[username] = symbol

    def has_player(self, username: str) -> bool:
        return username in self._players

    def get_player_handle(self, username: str) -> str:
        return self._handles[username]

    def get_player_symbol(self, username: str) -> str:
        return self._symbols[username]
