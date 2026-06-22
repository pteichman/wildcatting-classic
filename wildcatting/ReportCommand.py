import curses
import logging
from optparse import Values

import wildcatting.report
import wildcatting.util

from .cmdparse import Command


class ReportCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "report", summary="Test a Wildcatting report")

    def run(self, options: Values, args: list[str]) -> None:
        wildcatting.util.start_logger("report.log")
        curses.wrapper(wildcatting.report.main)
