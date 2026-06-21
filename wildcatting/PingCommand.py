import logging
import sys
from xmlrpc.client import ServerProxy

from .cmdparse import Command


class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "ping", summary="Ping a Wildcatting server")

        self.add_option("-p", "--port", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--host", type="string",
                        default="localhost", help="server hostname")

    def run(self, options, args):
        url = f"http://{options.host}:{options.port}/"
        s = ServerProxy(url, allow_none=True)

        try:
            server_version = s.version()
        except Exception:
            print(f"Server at {url} is not up.")
            sys.exit(1)

        print(f"{server_version} server at {url} is up.")
        sys.exit(0)
