import curses
import logging
import platform

from wildcatting.colors import Colors


class View:
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr):
        self._stdscr = stdscr
        self._mac = platform.system() == "Darwin"

    def getGreenFGBG(self):
        color = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)
        return color, color

    def addCentered(self, win, row, text, color=None):
        (h, w) = win.getmaxyx()

        col = (w - len(text)) // 2
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
        win.bkgdset(" ", fg)
        win.clear()

    def putch(self, win, y, x, ch, attr=None):
        # workaround so we can write things to the bottom corner
        # or otherwise with the same method call
        (h, w) = win.getmaxyx()
        if y == h - 1 and x == w - 1:
            f = win.insch
        else:
            f = win.addch

        if attr:
            f(y, x, ch, attr)
        else:
            f(y, x, ch)
