import version
import inspect

from SimpleXMLRPCServer import SimpleXMLRPCServer

class TieredXMLRPCServer(SimpleXMLRPCServer):
    def register_subinstance(self, tier, instance):
        for (name, method) in inspect.getmembers(instance, inspect.ismethod):
            if not name.startswith("_"):
                self.register_function(method, "%s.%s" % (tier, name))

class admin:
    def ping(self):
        return True

class server:
    def echo(self, s):
        return s

    def ping(self):
        return True

    def version(self):
        return version.VERSION_STRING
