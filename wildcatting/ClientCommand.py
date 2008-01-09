import logging
import socket
import sys
import os

import version

from client import Client
from cmdparse import Command
from util import startLogger

from xmlrpclib import ServerProxy

class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "client", summary="Run the Wildcatting client")

        user = os.environ.get("USER")
        if user is None:
            user = "none"
        well = user[0].upper()

        self.add_option("", "--no-network", action="store_true") 
        self.add_option("-p", "--port", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--host", type="string",
                        default="localhost", help="server hostname")
        self.add_option("-u", "--username", type="string",
                        default=user, help="username")
        self.add_option("-w", "--well", type="string",
                        default=well, help="well")
        self.add_option("-g", "--game", type="string",
                        default=None, help="game id")
        self.add_option("-r", "--handle", type="string",
                        default=None, help="game handle")

    def run(self, options, args):
        startLogger("client.log")
        
        url = "http://%s:%d/" % (options.host, options.port)
        if options.no_network:
            from theme import DefaultTheme
            from server import StandaloneServer
            s = StandaloneServer()
        else:
            s = ServerProxy(url, allow_none=True)

        try:
            server_version = s.version()
        except socket.error, e:
            print "Socket error contacting %s" % url
            print e.args[1]
            sys.exit(0)

        if server_version != version.VERSION_STRING:
            import textwrap
            print textwrap.fill("ERROR: Server at %s requires a %s client" % (url, server_version), os.getenv("COLUMNS", 80) - 5)
            sys.exit(1)

        c = Client(options.game, options.handle, options.username, options.well)

        self.log.info("Wildcatting client start")
        try:
            c.run(s)
        finally:
            self.log.info("Wildcatting client shutdown")
