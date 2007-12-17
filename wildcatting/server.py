import logging

import version
import inspect
import base64
import re

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpclib

from wildcatting.exceptions import WildcattingException
from wildcatting.game import Game
import wildcatting.model

class TieredXMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, *args, **kwargs):
        kwargs["allow_none"] = True
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)
    
    log = logging.getLogger("XMLRPCServer")

    def register_subinstance(self, tier, instance):
        for (name, method) in inspect.getmembers(instance, inspect.ismethod):
            if not name.startswith("_"):
                self.register_function(method, "%s.%s" % (tier, name))

    def _dispatch(self, *args, **kwargs):
        """Log all Exceptions raised by XML-RPC handlers"""
        try:
            response = SimpleXMLRPCServer._dispatch(self, *args, **kwargs)
        except:
            self.log.debug("XML-RPC Fault", exc_info=True)
            raise
        return response

class AdminService:
    def ping(self):
        return True

class BaseService:
    def echo(self, s):
        return s

    def ping(self):
        return True

    def version(self):
        return version.VERSION_STRING

class GameService:
    HANDLE_SEP = "::"
    
    def __init__(self):
        self._games = {}
        self._nextGameId = 0

    def _getGame(self, gameId):
        assert isinstance(gameId, str)

        game = self._games.get(gameId)
        if game is None:
            raise WildcattingException("Unknown game id: " + gameId)
        
        return game

    def _readHandle(self, handle):
        assert isinstance(handle, str)
        
        (gameId, playerName, secret) = self._decodeGameHandle(handle)

        game = self._getGame(gameId)
        player = game.getPlayer(playerName, secret)

        return (game, player)

    def _getSecret(self, playerId):
        assert isinstance(playerId, str)

        secret = self._secrets.get(playerId)
        if secret is None:
            raise WildcattingException("Unregistered player id: " + gameId)
        
        return secret

    def _encodeGameHandle(self, gameId, player, secret):
        assert isinstance(gameId, str)
        assert isinstance(player, wildcatting.model.Player)
        assert isinstance(secret, str)
        
        handle = GameService.HANDLE_SEP.join((gameId, player.getUsername(), secret))
        return base64.b64encode(handle)

    def _decodeGameHandle(self, gameHandle):
        assert isinstance(gameHandle, str)

        gameHandle = base64.b64decode(gameHandle)
        assert re.match("\d+::.+", gameHandle) is not None

        return gameHandle.split(GameService.HANDLE_SEP, 2)

    def new(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)
        
        gameId = str(self._nextGameId)
        self._nextGameId = self._nextGameId + 1

        self._games[gameId] = Game(width, height)
        return gameId

    def join(self, gameId, username, rig):
        assert isinstance(gameId, str)
        assert isinstance(username, str)
        
        game = self._getGame(gameId)
        player = wildcatting.model.Player(username, rig)

        secret = game.addPlayer(player)

        return self._encodeGameHandle(gameId, player, secret)

    def survey(self, handle, row, col):
        game, player = self._readHandle(handle)
        field = game.getOilField()

        site = field.getSite(row, col)
        if site.isSurveyed():
            raise WildcattingException("Site is already surveyed")

        site.setSurveyed(True)
        return site.serialize()

    def drill(self, handle, row, col):
        game, player = self._readHandle(handle)
        field = game.getOilField()

        site = field.getSite(row, col)
        site.setRig(player.getRig())
        return True

    def getPlayerField(self, handle):
        game, player = self._readHandle(handle)
        field = game.getOilField()

        width, height = field.getWidth(), field.getHeight()
        playerField = wildcatting.model.OilField(width, height)

        for row in xrange(height):
            for col in xrange(width):
                site = field.getSite(row, col)
                playerSite = playerField.getSite(row, col)

                surveyed = site.isSurveyed()
                playerSite.setSurveyed(surveyed)

                if surveyed:
                    playerSite.setDrillCost(site.getDrillCost())
                    playerSite.setProbability(site.getProbability())
                    playerSite.setRig(site.getRig())
                    playerSite.setTax(site.getTax())

        return playerField.serialize()
