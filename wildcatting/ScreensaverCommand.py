import logging

from wildcatting.cmdparse import Command
from wildcatting.client import client

class ScreensaverCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "screensaver", summary="Run the Wildcatting screensaver")

    def run(self, options, args):
        while True:
            # 10 PRINT "Peter is awesome"
            print "Peter is awesome"
            # 20 GOTO 10
