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

    log = logging.getLogger("Wildcatting")
    
    def __init__(self, theme):
        self._games = {}
        self._nextGameId = 0
        self._theme = theme

    def _getGame(self, gameId):
        assert isinstance(gameId, str)

        game = self._games.get(gameId)
        if game is None:
            raise WildcattingException("Unknown game id: " + gameId)
        
        return game

    def _readHandle(self, handle):
        assert isinstance(handle, str)

        self.log.debug("Reading handle: %s", handle)
        (gameId, playerName, secret) = self._decodeGameHandle(handle)

        game = self._getGame(gameId)
        player = game.getPlayer(playerName, secret)

        return (game, player)

    def _readClientHandle(self, handle):
        assert isinstance(handle, str)
        
        (gameId, clientId) = self._decodeClientHandle(handle)
        self.log.info("gameId: %s, clientId: %s", gameId, clientId)

        game = self._getGame(gameId)

        return (game, clientId)

    def _ensureSurveyTurn(self, game, player):
        if game.isFinished():
            raise WildcattingException("Game is over")

        week = game.getWeek()
        
        if not week.isSurveyTurn(player):
            raise WildcattingException("Not player's turn")

        return week.getPlayerTurn(player)

    def _ensureTurn(self, game, player):
        if game.isFinished():
            raise WildcattingException("Game is over")

        week = game.getWeek()
        
        if week.isTurnFinished(player):
            raise WildcattingException("Player's turn is finished")

        return week.getPlayerTurn(player)

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

    def _encodeClientHandle(self, gameId, clientId):
        assert isinstance(gameId, str)
        assert isinstance(clientId, str)
        
        handle = GameService.HANDLE_SEP.join((gameId, clientId))
        return base64.b64encode(handle)

    def _decodeClientHandle(self, clientHandle):
        assert isinstance(clientHandle, str)

        self.log.debug("Decoding %s", clientHandle)
        clientHandle = base64.b64decode(clientHandle)
        self.log.debug("Got %s", clientHandle)
        
        assert re.match("\d+::.+", clientHandle) is not None

        return clientHandle.split(GameService.HANDLE_SEP, 2)

    def newClientHandle(self, gameId):
        game = self._games[gameId]
        clientId = game._newClientId()
        self.log.info("New client handle requested for game %s: %s",
                      gameId, clientId)
        return self._encodeClientHandle(gameId, clientId)

    def new(self, width, height, turnCount):
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert isinstance(turnCount, int)
        
        gameId = str(self._nextGameId)
        self._nextGameId = self._nextGameId + 1

        self._games[gameId] = Game(width, height, turnCount, self._theme)

        return self.newClientHandle(gameId)

    def join(self, clientHandle, username, symbol):
        assert isinstance(clientHandle, str)
        assert isinstance(username, str)

        gameId, clientId = self._decodeClientHandle(clientHandle)
        game = self._games[gameId]

        player = wildcatting.model.Player(username, symbol)
        secret = game.addPlayer(clientId, player)

        handle = self._encodeGameHandle(gameId, player, secret)

        self.log.debug("%s joined game %s (%s)", player.getUsername(), gameId, handle)

        return handle

    def getClientInfo(self, clientHandle):
        assert isinstance(clientHandle, str)

        gameId, clientId = self._decodeClientHandle(clientHandle)
        game = self._games[gameId]

        clientInfo = wildcatting.model.ClientInfo(clientHandle, gameId)

        for player in game.getClientPlayers(clientId):
            handle = self._encodeGameHandle(gameId, player, player.getSecret())
            clientInfo.addPlayerInfo(player.getUsername(), handle,
                                     player.getSymbol())

        return clientInfo.serialize()

    def survey(self, handle, row, col):
        game, player = self._readHandle(handle)
        turn = self._ensureSurveyTurn(game, player)

        if turn.getSurveyedSite():
            raise WildcattingException("Already surveyed this turn")
        
        field = game.getOilField()

        site = field.getSite(row, col)
        if site.isSurveyed():
            raise WildcattingException("Site is already surveyed")

        site.setSurveyed(True)
        turn.setSurveyedSite(site)

        game.markSiteUpdated(player, site)
        game.getWeek().endSurvey(player)
        
        return site.serialize()

    def erect(self, handle, row, col):
        game, player = self._readHandle(handle)
        turn = self._ensureTurn(game, player)

        if turn.getDrilledSite():
            raise WildcattingException("Already drilled this turn")
        
        field = game.getOilField()

        site = field.getSite(row, col)
        well = wildcatting.model.Well()
        well.setPlayer(player)
        well.setWeek(game.getWeek().getWeekNum())
        site.setWell(well)
        game.drill(row, col)
        turn.setDrilledSite(site)
        game.markSiteUpdated(player, site)
        
        return self._makePlayerSite(site).serialize()

    def getGameId(self, handle):
        gameId, playerName, secret = self._decodeGameHandle(handle)
        return gameId

    def getWeek(self, handle):
        game, player = self._readHandle(handle)

        return game.getTurn().getWeek()

    def start(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)

        master = game.getMaster()
        if master not in game.getClientPlayers(clientId):
            raise WildcattingException("Client is not game master")
        game.start()

    def isStarted(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)
        return game.isStarted()

    def isFinished(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)
        return game.isFinished()

    def listPlayers(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)

        players = game.getPlayers()
        ret = [player.getUsername() for player in players]
        return ret
        
    def drill(self, handle, row, col):
        game, player = self._readHandle(handle)
        turn = self._ensureTurn(game, player)
        
        drilledSite = turn.getDrilledSite()
        if drilledSite and not (drilledSite.getRow() == row and drilledSite.getCol() == col):
            raise WildcattingException("Already drilled somewhere else this turn")

        game.drill(row, col)
        game.markSiteUpdated(player, drilledSite)
        well = game.getOilField().getSite(row,col).getWell()
        return well.serialize()

    def sell(self, handle, row, col):
        game, player = self._readHandle(handle)

        field = game.getOilField()
        site = field.getSite(row, col)
        well = site.getWell()

        if well is None:
            raise WildcattingException("There is no well at this location")

        if well.isSold():
            raise WildcattingException("Well has already been sold")

        if well.getPlayer().getUsername() != player.getUsername():
            raise WildcattingException("Player does not own well")

        return well.sell()

    def endTurn(self, clientHandle, handle):
        game, player = self._readHandle(handle)

        game.endTurn(player)
        
        return self.getUpdate(clientHandle), self.getWellUpdates(handle)

    def getPlayersTurn(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)

        player = game.getWeek().getSurveyPlayer()
        if player is not None:
            return player.getUsername()

    def getPendingPlayers(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)

        players = game.getWeek().getPendingPlayers()

        return [p.getUsername() for p in players]

    def getUpdate(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)

        week = game.getWeek().getWeekNum()
        oilPrice = game.getOilPrice()

        currentPlayer = game.getWeek().getSurveyPlayer()
        if currentPlayer is None:
            playersTurn = None
        else:
            playersTurn = currentPlayer.getUsername()

        pendingPlayers = self.getPendingPlayers(clientHandle)
        gameFinished = game.isFinished()
        sites = game.getUpdatedSites(clientId)

        update = wildcatting.model.Update(week, oilPrice, playersTurn, pendingPlayers, gameFinished, sites)
        return update.serialize()
        
    def getWellUpdates(self, handle):
        game, player = self._readHandle(handle)

        wellUpdates = []
        field = game.getOilField()        
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                well = field.getSite(row, col).getWell()
                if well is not None and well.getPlayer().getUsername() == player.getUsername():
                    wellDict = {"row": row, "col": col, "well": well.serialize()}
                    wellUpdates.append(wellDict)

        return wellUpdates

    def _updatePlayerSite(self, playerSite, site):
        playerSite.setDrillCost(site.getDrillCost())
        playerSite.setProbability(site.getProbability())
        playerSite.setWell(site.getWell())
        playerSite.setTax(site.getTax())
        playerSite.setSurveyed(site.isSurveyed())
        playerSite.setOilDepth(site.getOilDepth())
        
    def _makePlayerSite(self, site):
        playerSite = wildcatting.model.Site(site.getRow(), site.getCol())
        if site.isSurveyed():
            self._updatePlayerSite(playerSite, site)

        return playerSite

    def getPlayerSite(self, handle, row, col):
        game, player = self._readHandle(handle)
        field = game.getOilField()
        site = field.getSite(row, col)
        playerSite = self._makePlayerSite(site)

        return playerSite.serialize()

    def getOilPrice(self, handle):
        game, player = self._readHandle(handle)
        return game.getOilPrice()

    def _exposeOil(self, site):
        reservoir = site.getReservoir()
        if reservoir is not None:
            site.setOilDepth(reservoir.getOilDepth())

    def getPlayerField(self, clientHandle):
        game, player = self._readClientHandle(clientHandle)
        field = game.getOilField()

        width, height = field.getWidth(), field.getHeight()
        playerField = wildcatting.model.OilField(width, height)

        gameFinished = game.isFinished()

        for row in xrange(height):
            for col in xrange(width):
                site = field.getSite(row, col)
                playerSite = playerField.getSite(row, col)

                if gameFinished:
                    self._exposeOil(site)

                if site.isSurveyed() or gameFinished:
                    self._updatePlayerSite(playerSite, site)

        return playerField.serialize()

    def getWeeklySummary(self, clientHandle):
        game, clientId = self._readClientHandle(clientHandle)

        return wildcatting.model.WeeklySummary.serialize(game.getWeeklySummary())

class StandaloneServer:
    def __init__(self):
        import inspect

        base = BaseService()
        funcs = inspect.getmembers(base, inspect.ismethod)
        for name, method in funcs:
            setattr(self, name, method)

        theme = DefaultTheme()
        self.admin = AdminService()
        self.game = GameService(theme)
        self.setting = SettingService(theme)
