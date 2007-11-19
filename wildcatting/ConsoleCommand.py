import sys
import socket
import logging
import readline
import wildcatting.console

from optparse import OptionParser
from wildcatting.cmdparse import Command, CommandParser

from xmlrpclib import ServerProxy

class ConsoleParser(CommandParser):
    def format_help(self, *args, **kwargs):
        return self.format_command_help()

class ConsoleCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "console", summary="Run the Wildcatting console")
        self.add_option("-p", "--port", action="store", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--hostname", action="store", type="string",
                        default="localhost", help="server hostname")

    def run(self, options, args):
        url = "http://localhost:%d" % options.port
        s = ServerProxy(url)
        try:
            s.ping()
        except socket.error, e:
            print "Socket error contacting %s" % url
            print e.args[1]
            sys.exit(0)

        parser = ConsoleParser()
        parser.add_option("", "--server", action="store_const", default=s)
        parser.add_option("", "--parser", action="store_const", default=parser)
        parser.add_commands(wildcatting.console, "Console")

        while True:
            try:
                cmd = raw_input("wildcatting> ")
            except EOFError:
                print
                sys.exit(0)
            
            (command, opts, args) = parser.parse_args(cmd.split())

            if command is not None:
                if command == "help":
                    parser.print_help()
                else:
                    command.run(opts, args)
