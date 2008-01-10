import logging
import curses
import os

from wildcatting.colors import Colors

class View:
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr):
        self._stdscr = stdscr

        # for mac terminal workarounds - lazy mac check
        self._mac = os.path.exists("/mach_kernel")

    def _eatAllKeyEvents(self, win):
        curses.cbreak()
        win.nodelay(1)
        while win.getch() != -1:
            pass
        win.nodelay(0)

    def getGreenFGBG(self):
        if self._mac:
            bkgd = Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN)
            text = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)
        else:
            bkgd = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)
            text = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)

        return text, bkgd

    def addCentered(self, win, row, text, color=None):
        (h, w) = win.getmaxyx()

        col = (w - len(text))/2
        if color is None:
            win.addstr(row, col, text)
        else:
            win.addstr(row, col, text, color)

    def addLeft(self, win, row, text, color=None, pad=0):
        (h, w) = win.getmaxyx()

        col = pad
        if color is None:
            win.addstr(row, col, text)
        else:
            win.addstr(row, col, text, color)

    def addRight(self, win, row, text, color=None, pad=0):
        (h, w) = win.getmaxyx()

        col = w - len(text) - 1 - pad
        if color is None:
            win.addstr(row, col, text)
        else:
            win.addstr(row, col, text, color)

    def setFGBG(self, win, fg, bg):
        (h, w) = win.getmaxyx()
        
        win.bkgdset(" ", fg)

        # work around a problem with the MacOS X Terminal - draw the
        # background explicitly by drawing BG on BG "." characters
        if self._mac:
            for row in xrange(h):
                win.addstr(row, 0, "." * (w-1), bg)
        else:
            self._win.clear()            

    def putch(self, win, y, x, ch, attr=None):
        # workaround so we can write things to the bottom corner
        # or otherwise with the same method call
        (h,w) = win.getmaxyx()
        if y == h-1 and x == w-1:
            f = win.insch
        else:
            f = win.addch

        if attr:
            f(y, x, ch, attr)
        else:
            f(y, x, ch)
