import logging

from wildcatting.cmdparse import Command
from wildcatting.client import client

class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "client", summary="Run the Wildcatting client")

    def run(self, options, args):
        c = client()
        c.run()
