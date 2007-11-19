import logging

from wildcatting.cmdparse import Command

from xmlrpclib import ServerProxy

class ConsoleCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "console", summary="Run the Wildcatting console")
        self.add_option("-p", "--port", action="store", type="int",
                        default="7777", help="server port")
        self.add_option("-n", "--hostname", action="store", type="string",
                        default="localhost", help="server hostname")

    def run(self, options, args):
        s = ServerProxy("http://localhost:%d" % options.port)
        print s.echo("Server is up.")
