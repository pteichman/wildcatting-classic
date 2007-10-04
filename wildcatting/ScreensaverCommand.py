import logging
import time

import curses

from wildcatting.cmdparse import Command
from wildcatting.oilfield import Field

class ScreensaverCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "screensaver", summary="Run the Wildcatting screensaver")

        self.y_border = 2
        self.x_border = 3

    def cursesScreensaver(self, stdscr):
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLUE)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_CYAN)
        
        screen_h, screen_w = stdscr.getmaxyx()
        win = stdscr.derwin(screen_h-self.y_border*2,
                            screen_w-self.x_border*2,
                            self.y_border, self.x_border)
    
        win.box()

        win_h, win_w = win.getmaxyx()
        win = win.derwin(win_h-2, win_w-2, 1, 1)

        while True:
            Field(win_w-1, win_h-1).curses(win)
            stdscr.refresh()
            time.sleep(.25)

    def run(self, options, args):
        curses.wrapper(self.cursesScreensaver)
