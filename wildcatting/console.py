import sys
import logging

import wildcatting.model
from wildcatting.cmdparse import Command, CommandParser

class EchoCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "echo", summary="echo a string from the server")

    def run(self, options, args):
        print options.server.echo(" ".join(args))

class FooCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "foo", summary="get a foo from the server")

    def run(self, options, args):
        f = wildcatting.model.Foo()
        dict = options.server.foo()
        print dict
        f.deserialize(dict)
        print "Value is", f.getValue()

class HelpCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "help", summary="print help about commands")

    def run(self, options, args):
        options.parser.print_help()

class ListMethodsCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "list-methods", summary="list server side methods")

    def run(self, options, args):
        print options.server.system.listMethods()

class QuitCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "quit", summary="exit the wildcatting console")

    def run(self, options, args):
        sys.exit(0)
