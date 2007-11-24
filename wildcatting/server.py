import version
import inspect

from SimpleXMLRPCServer import SimpleXMLRPCServer

from wildcatting.game import Game
import wildcatting.model

class TieredXMLRPCServer(SimpleXMLRPCServer):
    def register_subinstance(self, tier, instance):
        for (name, method) in inspect.getmembers(instance, inspect.ismethod):
            if not name.startswith("_"):
                self.register_function(method, "%s.%s" % (tier, name))

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
        self._nextid = 0

    def _getGame(self, id):
        return self._games[id]

    def new(self, width, height):
        id = self._nextid
        self._nextid = self._nextid + 1

        self._games[id] = Game(width, height)
        return id

    def survey(self, id, row, col):
        game = self._getGame(id)
        field = game.getOilField()

        site = field.getSite(row, col)
        site.setSurveyed(True)
        return site.serialize()


    def drill(self, id, rig):
        game = self._getGame(id)
        field = game.getOilField()

        site = field.getSite(row, col)
        site.setRig(rig)
        return True

    def getPlayerField(self, id):
        game = self._getGame(id)
        field = game.getOilField()

        width, height = field.getWidth(), field.getHeight()
        playerField = wildcatting.model.OilField(width, height)

        for row in xrange(height):
            for col in xrange(width):
                site = field.getSite(row, col)
                playerSite = playerField.getSite(row, col)

                surveyed = site.getSurveyed()
                playerSite.setSurveyed(surveyed)

                if surveyed:
                    playerSite.setDrillCost(site.getDrillCost())
                    playerSite.setProbability(site.getProbability())
                    playerSite.setRig(site.getRig())
                    playerSite.setTax(site.getTax())

        return playerField.serialize()
