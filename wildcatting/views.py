import curses
import random

from wildcatting.colors import Colors
import wildcatting.game
import wildcatting.model

class OilFieldTextView:
    def __init__(self, model):
        assert isinstance(model, wildcatting.model.OilField)
        self._model = model

    def bracket(self, site):
        p = site.getProbability()
        if p > 95:
            b = 0
        elif p > 85:
            b = 1
        elif p > 70:
            b = 2
        elif p > 55:
            b = 3
        elif p > 35:
            b = 4
        else:
            b = 5
        return b

    def toAscii(self, site):
        assert isinstance(site, wildcatting.model.Site)
        b = self.bracket(site)
        return ".x%*&#"[b]

    def ascii(self):
        model = self._model
        for row in xrange(model.getHeight()):
            line = ""
            for col in xrange(model.getWidth()):
                line += self.toAscii(model.getSite(row, col))
            print line

    def toAnsi(self, site):
        b = self.bracket(site) % 9
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi

    def ansi(self):
        model = self._model
        for row in xrange(model.getHeight()):
            line = ""
            for col in xrange(model.getWidth()):
                line += self.toAnsi(model.getSite(row, col))
            print line

class OilFieldCursesView:
    def __init__(self, win, field):
        self._win = win
        self.setField(field)

        # increasing order of hotness
        self._colors = [
            Colors.get(curses.COLOR_WHITE, curses.COLOR_BLUE),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_CYAN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_GREEN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_YELLOW),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_MAGENTA),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_RED),
            ]

    def setField(self, field):
        assert isinstance(field, wildcatting.model.OilField)
        self._field = field

    def siteColor(self, site):
        if site is None:
            return Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)

        assert isinstance(site, wildcatting.model.Site)

        p = site.getProbability()
        if p == 100:
            return self._colors[-1]

        return self._colors[int(p / 100. * len(self._colors))]

    def display(self):
        field = self._field

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                if site.isSurveyed():
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
    field = wildcatting.model.OilField(w, h)
    wildcatting.game.OilFiller().fill(field)

    view = OilFieldCursesView(win, field)
    while True:
        col = random.choice(range(0,w))
        row = random.choice(range(0,h))
        site = field.getSite(row, col)
        site.setSurveyed(True)
        site.setRig("B")
        view.display()

if __name__ == "__main__":
    curses.wrapper(main)
