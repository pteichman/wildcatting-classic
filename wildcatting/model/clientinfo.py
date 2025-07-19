from .serialize import Serializable

class ClientInfo(Serializable):
    def __init__(self, clientHandle, gameId):
        self._clientHandle = clientHandle
        self._gameId = gameId
        self._players = []
        self._handles = {}
        self._symbols = {}

    def getGameId(self):
        return self._gameId

    def setGameId(self, gameId):
        assert isinstance(gameId, str)
        self._gameId = gameId

    def getClientHandle(self):
        return self._clientHandle

    def setClientHandle(self, clientHandle):
        assert isinstance(gameId, str)
        return self._clientHandle

    def addPlayerInfo(self, username, handle, symbol):
        self._players.append(username)
        self._handles[username] = handle
        self._symbols[username] = symbol

    def hasPlayer(self, username):
        return username in self._players

    def getPlayerHandle(self, username):
        return self._handles[username]

    def getPlayerSymbol(self, username):
        return self._symbols[username]
