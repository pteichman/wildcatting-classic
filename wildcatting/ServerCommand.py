import logging
import socket

import wildcatting.version
import wildcatting.server
import wildcatting.util
import wildcatting.theme
from wildcatting.cmdparse import Command

class ServerCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "server", summary="Run the Wildcatting server")
        self.add_option("-n", "--host", action="store", type="str",
                        default="", help="server hostname")
        self.add_option("-p", "--port", action="store", type="int",
                        default="7777", help="server port")

    def run(self, options, args):
        wildcatting.util.startLogger("server.log")

        host = options.host

        s = wildcatting.server.TieredXMLRPCServer((host, options.port))

        s.register_instance(wildcatting.server.BaseService())
        s.register_subinstance("admin", wildcatting.server.AdminService())
        s.register_subinstance("game", wildcatting.server.GameService())
        s.register_subinstance("setting", wildcatting.server.SettingService())
        s.register_introspection_functions()

        if len(host) == 0:
            # use hostname for display purposes, even if we're bound
            # to all interfaces
            host = socket.gethostname()

        url = "http://%s:%d/" % (host, options.port)

        self.log.info("Wildcatting server start")
        print "%s server listening at %s" % (wildcatting.version.VERSION_STRING, url)
        try:
            s.serve_forever()
        finally:
            self.log.info("Wildcatting server shutdown")
