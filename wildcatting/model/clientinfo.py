from .serialize import Serializable


class ClientInfo(Serializable):
    def __init__(self, clientHandle, gameId):
        self._clientHandle = clientHandle
        self._gameId = gameId
        self._players = []
        self._handles = {}
        self._symbols = {}

    def get_game_id(self):
        return self._gameId

    def set_game_id(self, gameId):
        assert isinstance(gameId, str)
        self._gameId = gameId

    def get_client_handle(self):
        return self._clientHandle

    def set_client_handle(self, clientHandle):
        assert isinstance(clientHandle, str)
        return self._clientHandle

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
