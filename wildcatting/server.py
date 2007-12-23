import logging

import version
import inspect
import base64
import re
import random

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpclib

from wildcatting.exceptions import WildcattingException
from wildcatting.game import Game
import wildcatting.model

from theme import DefaultTheme

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

class SettingService:
    def __init__(self, theme):
        self._setting = theme.generateSetting()

    def getSetting(self):
        return self._setting.serialize()

class GameService:
    HANDLE_SEP = "::"
    
    def __init__(self, theme=None):
        if theme is None:
            theme = DefaultTheme()
        
        self._theme = theme
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

        self._games[gameId] = Game(width, height, self._theme)
        return gameId

    def join(self, gameId, username, symbol):
        assert isinstance(gameId, str)
        assert isinstance(username, str)
        
        game = self._getGame(gameId)
        player = wildcatting.model.Player(username, symbol)

        secret = game.addPlayer(player)

        return self._encodeGameHandle(gameId, player, secret)

    def survey(self, handle, row, col):
        game, player = self._readHandle(handle)
        turn = game.getTurn()

        if turn.getPlayer() != player:
            raise WildcattingException("Not player's turn")

        if turn.getSurveyedSite():
            raise WildcattingException("Already surveyed this turn")
        
        field = game.getOilField()

        site = field.getSite(row, col)
        if site.isSurveyed():
            raise WildcattingException("Site is already surveyed")

        site.setSurveyed(True)
        turn.setSurveyedSite(site)
        
        return site.serialize()

    def erect(self, handle, row, col):
        game, player = self._readHandle(handle)
        turn = game.getTurn()

        if turn.getPlayer() != player:
            raise WildcattingException("Not player's turn")

        if turn.getDrilledSite():
            raise WildcattingException("Already drilled this turn")
        
        field = game.getOilField()

        site = field.getSite(row, col)
        well = wildcatting.model.Well()
        well.setPlayer(player)
        well.setWeek(game.getTurn().getWeek())
        site.setWell(well)
        turn.setDrilledSite(site)
        
        return True

    def getGameId(self, handle):
        gameId, playerName, secret = self._decodeGameHandle(handle)
        return gameId

    def start(self, handle):
        game, player = self._readHandle(handle)

        if player != game.getMaster():
            raise WildcattingException("Player is not game master")
        game.start()

    def isStarted(self, handle):
        game, player = self._readHandle(handle)
        return game.isStarted()

    def listPlayers(self, handle):
        game, player = self._readHandle(handle)

        players = game.getPlayers()
        ret = [player.getUsername() for player in players]
        return ret
        
    def drill(self, handle, row, col):
        game, player = self._readHandle(handle)
        turn = game.getTurn()

        if turn.getPlayer() != player:
            raise WildcattingException("Not player's turn")
        
        drilledSite = turn.getDrilledSite()
        if drilledSite and not (drilledSite.getRow() == row and drilledSite.getCol() == col):
            raise WildcattingException("Already drilled somewhere else this turn")
        
        field = game.getOilField()
        site = field.getSite(row, col)
        well = site.getWell()
        return well.drill(site)

    def endTurn(self, handle):
        game, player = self._readHandle(handle)
        turn = game.getTurn()

        if turn.getPlayer() != player:
            raise WildcattingException("Not player's turn")

        game.endTurn(player)

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
                    playerSite.setWell(site.getWell())
                    playerSite.setTax(site.getTax())

        return playerField.serialize()
        
class StandaloneServer:
    def __init__(self, theme):
        import inspect

        base = BaseService()
        funcs = inspect.getmembers(base, inspect.ismethod)
        for name, method in funcs:
            setattr(self, name, method)

        self.admin = AdminService()
        self.game = GameService(theme)
        self.setting = SettingService(theme)
