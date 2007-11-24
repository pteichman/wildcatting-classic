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
    
    def new(self, width, height):
        id = self._nextid
        self._nextid = self._nextid + 1
        
        self._games[id] = Game(width, height)

        return id

    def getOilField(self, id):
        field = self._games[id].getOilField()
        return field.serialize()
