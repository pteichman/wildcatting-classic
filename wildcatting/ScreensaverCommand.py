import logging
import time

import curses

from wildcatting.cmdparse import Command
from wildcatting.oilfield import Field

class ScreensaverCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "screensaver", summary="Run the Wildcatting screensaver")

        self.add_option("", "--no-border", action="store_true",
                        help="disable border")
        self.add_option("", "--ascii", action="store_true",
                        help="enable advanced ascii display (recommended)")
        self.add_option("", "--ansi", action="store_true",
                        help="enable ansi display")

        self.y_border = 2
        self.x_border = 3

    def asciiScreensaver(self):
        while True:
            Field(80, 23).ascii()
            time.sleep(.25)

    def ansiScreensaver(self):
        try:
            while True:
                Field(80, 23).ansi()
                time.sleep(.25)
        except:
            print chr(27) + '[0m'

    def cursesScreensaver(self, stdscr, options, args):
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLUE)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_CYAN)

        if options.no_border:
            win = stdscr
            border = 0
        else:
            screen_h, screen_w = stdscr.getmaxyx()
            win = stdscr.derwin(screen_h-self.y_border*2,
                                screen_w-self.x_border*2,
                                self.y_border, self.x_border)
    
            win.box()
            border = 1

        win_h, win_w = win.getmaxyx()
        win = win.derwin(win_h-border*2, win_w-border*2, border, border)

        while True:
            Field(win_w-1, win_h-1).curses(win)
            stdscr.refresh()
            time.sleep(.25)

    def run(self, options, args):
        if options.ascii:
            self.asciiScreensaver()
        elif options.ansi:
            self.ansiScreensaver()
        else:
            curses.wrapper(self.cursesScreensaver, options, args)
