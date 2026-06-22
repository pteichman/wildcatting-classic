import logging
import socket
from optparse import Values

import wildcatting.server
import wildcatting.theme
import wildcatting.util
import wildcatting.version
from wildcatting.cmdparse import Command


class ServerCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "server", summary="Run the Wildcatting server")
        self.add_option(
            "-n",
            "--host",
            action="store",
            type="str",
            default="",
            help="server hostname",
        )
        self.add_option(
            "-p",
            "--port",
            action="store",
            type="int",
            default="7777",
            help="server port",
        )

    def run(self, options: Values, args: list[str]) -> None:
        wildcatting.util.startLogger("server.log")

        host = options.host

        s = wildcatting.server.TieredXMLRPCServer((host, options.port))

        theme = wildcatting.theme.DefaultTheme()

        s.register_instance(wildcatting.server.BaseService())
        s.register_subinstance("admin", wildcatting.server.AdminService())
        s.register_subinstance("game", wildcatting.server.GameService(theme))
        s.register_subinstance("setting", wildcatting.server.SettingService(theme))
        s.register_introspection_functions()

        if len(host) == 0:
            # use hostname for display purposes, even if we're bound
            # to all interfaces
            host = socket.gethostname()

        url = f"http://{host}:{options.port}/"

        self.log.info("Wildcatting server start")
        print(f"{wildcatting.version.VERSION_STRING} server listening at {url}")
        try:
            s.serve_forever()
        finally:
            self.log.info("Wildcatting server shutdown")
