import logging

import wildcatting.version
from wildcatting.cmdparse import Command
from wildcatting.server import server

from SimpleXMLRPCServer import SimpleXMLRPCServer

class ServerCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "server", summary="Run the Wildcatting server")
        self.add_option("-p", "--port", action="store", type="int",
                        default="7777", help="server port")

    def run(self, options, args):
        hostname = "localhost"
        s = SimpleXMLRPCServer((hostname, options.port))
        s.register_instance(server())

        url = "http://%s:%d/" % (hostname, options.port)

        print "%s server listening at %s" % (wildcatting.version.VERSION_STRING, url)
        s.serve_forever()
