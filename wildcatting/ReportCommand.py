import logging
import socket
import sys
import os
import curses
from .cmdparse import Command

import wildcatting.util
import wildcatting.report


from xmlrpc.client import ServerProxy

class ReportCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "report", summary="Test a Wildcatting report")

    def run(self, options, args):
        wildcatting.util.startLogger("report.log")
        curses.wrapper(wildcatting.report.main)
