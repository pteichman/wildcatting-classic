import logging

import version
import inspect

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpclib

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
    def __init__(self):
        self._games = {}
        self._nextGameId = 0

    def _getGame(self, gameId):
        return self._games[gameId]

    def new(self, width, height):
        gameId = self._nextGameId
        self._nextGameId = self._nextGameId + 1

        self._games[gameId] = Game(width, height)
        return gameId

    def survey(self, gameId, row, col):
        game = self._getGame(gameId)
        field = game.getOilField()

        site = field.getSite(row, col)
        site.setSurveyed(True)
        return site.serialize()

    def drill(self, gameId, row, col, rig):
        game = self._getGame(gameId)
        field = game.getOilField()

        site = field.getSite(row, col)
        site.setRig(rig)
        return True

    def getPlayerField(self, gameId):
        game = self._getGame(gameId)
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
