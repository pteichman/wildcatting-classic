from .serialize import Serializable


class ClientInfo(Serializable):
    def __init__(self, clientHandle, gameId):
        self._clientHandle = clientHandle
        self._gameId = gameId
        self._players = []
        self._handles = {}
        self._symbols = {}

    @property
    def game_id(self):
        return self._gameId

    @game_id.setter
    def game_id(self, gameId):
        assert isinstance(gameId, str)
        self._gameId = gameId

    @property
    def client_handle(self):
        return self._clientHandle

    @client_handle.setter
    def client_handle(self, clientHandle):
        assert isinstance(clientHandle, str)
        self._clientHandle = clientHandle

    def add_player_info(self, username, handle, symbol):
        self._players.append(username)
        self._handles[username] = handle
        self._symbols[username] = symbol

    def has_player(self, username):
        return username in self._players

    def get_player_handle(self, username):
        return self._handles[username]

    def get_player_symbol(self, username):
        return self._symbols[username]
