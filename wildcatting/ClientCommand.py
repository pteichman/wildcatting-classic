import logging
import socket
import sys

import wildcatting.util

from wildcatting.cmdparse import Command
from wildcatting.client import Client

from xmlrpclib import ServerProxy

class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "client", summary="Run the Wildcatting client")
        self.add_option("-p", "--port", action="store", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--hostname", action="store", type="string",
                        default="localhost", help="server hostname")

    def run(self, options, args):
        wildcatting.util.startLogger("client.log")
        
        url = "http://%s:%d/" % (options.hostname, options.port)
        server = ServerProxy(url)
        try:
            version = server.version()
        except socket.error, e:
            print "Socket error contacting %s" % url
            print e.args[1]
            sys.exit(0)

        Client().run(server)
