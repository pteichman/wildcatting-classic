import logging
import time

from wildcatting.cmdparse import Command
from wildcatting.oilfield import Field

class ScreensaverCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "screensaver", summary="Run the Wildcatting screensaver")

    def run(self, options, args):
        while True:
            Field(40,40).ansi()
            time.sleep(.25)
