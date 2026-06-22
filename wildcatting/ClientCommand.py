import logging
import os
import sys
from argparse import Namespace
from xmlrpc.client import ServerProxy

from . import version
from .client import Client
from .cmdparse import Command
from .server import ServerProtocol, XmlRpcServer
from .util import start_logger


class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "client", summary="Run the Wildcatting client")

        user = os.environ.get("USER")
        if user is None:
            user = "none"
        symbol = user[0].upper()

        self.add_argument("--no-network", action="store_true")
        self.add_argument("-p", "--port", type=int, default=7777, help="server port")
        self.add_argument("-n", "--host", default="localhost", help="server hostname")
        self.add_argument("-u", "--username", default=user, help="username")
        self.add_argument("-m", "--hotseat", action="store_true", help="hotseat mode")
        self.add_argument("-s", "--symbol", default=symbol, help="well symbol")
        self.add_argument(
            "-w", "--weeks", type=int, default=13, help="length of game in weeks"
        )
        self.add_argument("-g", "--game", default=None, help="game id")
        self.add_argument("-r", "--handle", default=None, help="game handle")

    def run(self, options: Namespace, args: list[str]) -> None:
        start_logger("client.log")

        url = f"http://{options.host}:{options.port}/"
        if options.no_network:
            from .server import StandaloneServer

            s: ServerProtocol = StandaloneServer()
        else:
            s = XmlRpcServer(ServerProxy(url, allow_none=True))

        try:
            server_version = s.version()
        except OSError as e:
            print(f"Socket error contacting {url}")
            print(e.args[1])
            sys.exit(0)

        if server_version != version.VERSION_STRING:
            import textwrap

            cols = int(os.getenv("COLUMNS", 80)) - 5
            print(
                textwrap.fill(
                    f"ERROR: Server at {url} requires a {server_version} client", cols
                )
            )
            sys.exit(1)

        player = None if options.hotseat else (options.username, options.symbol)

        c = Client(options.weeks, options.game, options.handle, player)

        self.log.info("Wildcatting client start")
        try:
            c.run(s)
        finally:
            self.log.info("Wildcatting client shutdown")
