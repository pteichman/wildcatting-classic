import curses
import random

from oilfield import OilField

class PlayerField:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._field = [None]*height
        for i in xrange(height):
            self._field[i] = [None]*width

    def setSite(self, x, y, site):
        self._field[y][x] = site

    def getSite(self, x, y):
        return self._field[y][x]

class OilFieldView:
    def __init__(self, win, field):
        self._win = win
        self._field = field

        # TODO put this somewhere sensible
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_CYAN)

    def siteColor(self, site):
        if site == None:
            return curses.color_pair(1)
        seq = range(2, 7)
        seq.reverse()
        p = site.getProbability()
        if p == 100:
            b = seq[-1]
        else:
            b = seq[int(p / 100. * len(seq))]
        return curses.color_pair(b)

    def display(self):
        model = self._field.getModel()

        for row in xrange(model.getHeight()):
            for col in xrange(model.getWidth()):
                site = model.getSite(row, col)
                putch(self._win, row, col,
                      ord(site.getRig()), self.siteColor(site))
        self._win.refresh()

def putch(win, y, x, ch, attr=None):
    (h,w) = win.getmaxyx()
    if y == h-1 and x == w-1:
        f = win.insch
    else:
        f = win.addch

    if attr:
        f(y, x, ch, attr)
    else:
        f(y, x, ch)



def main(stdscr):
        (h,w) = stdscr.getmaxyx()
        win = stdscr.derwin(h, w, 0, 0)
        field = OilField(w, h-1)
        playerField = PlayerField(w, h-1)
        view = FieldView(win, playerField)
        while True:
            x = random.choice(range(0,w-1))
            y = random.choice(range(0,h-2))
            site = field.getSite(x, y)
            playerField.setSite(x, y, site)
            view.display()

if __name__ == "__main__":
    curses.wrapper(main)
