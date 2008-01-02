import logging


class View:
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr):
        self._stdscr = stdscr

    def addCentered(self, win, row, text):
        (h, w) = win.getmaxyx()

        col = (w - len(text))/2
        win.addstr(row, col, text)

    def setFGBG(self, win, fg, bg):
        (h, w) = self._win.getmaxyx()
        
        # work around a problem with the MacOS X Terminal - draw the
        # background explicitly by drawing BG on BG "." characters
        win.bkgdset(" ", fg)
        for row in xrange(h):
            win.addstr(row, 0, " " * (w-1), bg)

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
