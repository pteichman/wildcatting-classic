import sys
import logging

from wildcatting.cmdparse import Command, CommandParser

class EchoCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "echo", summary="echo a string from the server")

    def run(self, options, args):
        print options.server.echo(" ".join(args))

class HelpCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "help", summary="print help about commands")

    def run(self, options, args):
        options.parser.print_help()

class QuitCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "quit", summary="exit the wildcatting console")

    def run(self, options, args):
        sys.exit(0)