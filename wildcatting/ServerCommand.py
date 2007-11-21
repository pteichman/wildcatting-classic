import logging

import wildcatting.version
import wildcatting.server
from wildcatting.cmdparse import Command

class ServerCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "server", summary="Run the Wildcatting server")
        self.add_option("-p", "--port", action="store", type="int",
                        default="7777", help="server port")

    def run(self, options, args):
        hostname = "localhost"
        s = wildcatting.server.TieredXMLRPCServer((hostname, options.port))

        s.register_instance(wildcatting.server.server())
        s.register_subinstance("admin", wildcatting.server.admin())
        s.register_introspection_functions()

        url = "http://%s:%d/" % (hostname, options.port)

        print "%s server listening at %s" % (wildcatting.version.VERSION_STRING, url)
        s.serve_forever()
