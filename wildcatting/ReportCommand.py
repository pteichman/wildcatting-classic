import curses
import logging

import wildcatting.report
import wildcatting.util

from .cmdparse import Command


class ReportCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "report", summary="Test a Wildcatting report")

    def run(self, options, args):
        wildcatting.util.startLogger("report.log")
        curses.wrapper(wildcatting.report.main)
