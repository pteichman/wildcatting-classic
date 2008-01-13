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
        Command.__init__(self, "ping", summary="Ping a Wildcatting server")

        self.add_option("-p", "--port", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--host", type="string",
                        default="localhost", help="server hostname")

    def run(self, options, args):
        url = "http://%s:%d/" % (options.host, options.port)
        s = ServerProxy(url, allow_none=True)

        try:
            server_version = s.version()
        except:
            print "Server at %s is not up." % url
            sys.exit(1)

        print "Server at %s is up." % url
        sys.exit(0)
