import logging
import socket
import sys
import os

import wildcatting

from wildcatting.cmdparse import Command
from wildcatting.client import Client

from xmlrpclib import ServerProxy

class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "client", summary="Run the Wildcatting client")

        user = os.environ.get("USER")
        if user is None:
            user = "none"
        rig = user[0].upper()

        self.add_option("", "--no-network", action="store_true") 
        self.add_option("-p", "--port", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--hostname", type="string",
                        default="localhost", help="server hostname")
        self.add_option("-u", "--username", type="string",
                        default=user, help="username")
        self.add_option("-r", "--rig", type="string",
                        default=rig, help="rig")
        self.add_option("-g", "--game-id", type="string",
                        default=None, help="game id")

    def run(self, options, args):
        wildcatting.util.startLogger("client.log")
        
        url = "http://%s:%d/" % (options.hostname, options.port)
        if options.no_network:
            theme = wildcatting.theme.WestTexasTheme()
            server = wildcatting.server.StandaloneServer(theme)
        else:
            server = ServerProxy(url, allow_none=True)

        try:
            version = server.version()
        except socket.error, e:
            print "Socket error contacting %s" % url
            print e.args[1]
            sys.exit(0)

        client = Client(options.game_id, options.username, options.rig)

        self.log.info("Wildcatting client start")
        try:
            client.run(server)
        finally:
            self.log.info("Wildcatting client shutdown")
