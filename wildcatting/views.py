import curses
import random
import logging
import textwrap

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


class CursesColorChooser:
    def __init__(self):
        # increasing order of hotness
        self._colors = [
            Colors.get(curses.COLOR_WHITE, curses.COLOR_BLUE),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_CYAN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_GREEN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_YELLOW),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_MAGENTA),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_RED),
            ]

        self._blankColors = [
            Colors.get(curses.COLOR_BLUE, curses.COLOR_BLUE),
            Colors.get(curses.COLOR_CYAN, curses.COLOR_CYAN),
            Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN),
            Colors.get(curses.COLOR_YELLOW, curses.COLOR_YELLOW),
            Colors.get(curses.COLOR_MAGENTA, curses.COLOR_MAGENTA),
            Colors.get(curses.COLOR_RED, curses.COLOR_RED),
            ]

    def getColors(self):
        return self._colors[:]

    def siteColor(self, site):
        if site is None:
            return Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)

        assert isinstance(site, wildcatting.model.Site)

        return self._chooseColor(site, self._colors)

    def _chooseColor(self, site, colors):
        p = site.getProbability()
        if p == 100:
            return colors[-1]
        return colors[int(p / 100. * len(colors))]

    def blankColor(self, site):
        if site is None:
            return Colors.get(curses.COLOR_BLACK, curses.COLOR_BLACK)

        assert isinstance(site, wildcatting.model.Site)

        return self._chooseColor(site, self._blankColors)
    

class WildcattingView:
    log = logging.getLogger("Wildcatting")

    TOP_BORDER = 2
    SIDE_BORDER = 3
    
    def __init__(self, stdscr, rows, cols, setting):
        self._stdscr = stdscr
        self._setting = setting

        (h, w) = stdscr.getmaxyx()
        bwh = h - (self.TOP_BORDER * 2)
        bww = w - (self.SIDE_BORDER * 2)

        self._border_win = stdscr.derwin(bwh, bww, 1, 3)
        self._field_win = stdscr.derwin(rows, cols, 2, 4)
        self._oilView = oilView = OilFieldCursesView(self._field_win)

        self._fh, self._fw = self._field_win.getmaxyx()
        self._colorChooser = CursesColorChooser()
        self._x, self._y = 0, 0
        self._turn = 0

    def _drawBorder(self):
        (h, w) = self._stdscr.getmaxyx()
        location = self._setting.getLocation()
        era = self._setting.getEra()
        self._stdscr.addstr(0, 4, "%s, %s." %(location, era), curses.A_BOLD)
        self._stdscr.addstr(0, w - 10, "Week %s" % str(self._turn + 1), curses.A_BOLD)
        fact = random.choice(self._setting.getFacts())
        wrapped = self._wrap_fact(fact, " "*4, w-8)
        self._stdscr.addstr(h-3, 0, wrapped)
        self._border_win.box()

    def _wrap_fact(self, fact, indent, width):
        """Wrap a fact across three lines"""
        lines = textwrap.wrap(fact, width, initial_indent=indent,
                              subsequent_indent=indent, break_long_words=True)

        # we only have space for three lines
        if len(lines) > 3:
            lines = lines[:3]
        
        return "\n".join(lines)

    def _drawKeyBar(self):
        border_h, border_w = self._border_win.getmaxyx()
        colors = list(self._colorChooser.getColors())
        colors.reverse()
        keyStr = "." * (border_w - 2)
        bkgd = Colors.get(curses.COLOR_WHITE, curses.COLOR_WHITE)
        self._border_win.addstr(border_h - 2, 1, keyStr, bkgd)
        for i in xrange(len(colors)):
            color = colors[i]
            self._border_win.addstr(border_h - 2, 1 + i, " ", color)

        coordStr = "X=%s   Y=%s" % (str(self._x).rjust(2), str(self._y).rjust(2))
        foreground = Colors.get(curses.COLOR_BLACK, curses.COLOR_WHITE)
        self._border_win.addstr(border_h - 2, border_w / 2 - len(coordStr) / 2, coordStr, foreground)
        self._border_win.refresh()

    def updateField(self, field):
        self._oilView.setField(field)

    def updateTurn(self, turn):
        self._turn = turn

    def display(self):
        self._stdscr.clear()
        self._drawBorder()

    def input(self):
        actions = {"survey": None, "checkForUpdates": False}
        
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.halfdelay(50)
        if True:
            self._oilView.display()
            putch(self._field_win, self._y, self._x, " ", curses.A_REVERSE)
            self._field_win.refresh()
            
            self._drawKeyBar()
            
            curses.curs_set(0)
            dx = 0 ; dy = 0
            survey = False
            
            c = self._stdscr.getch()
            if c == -1:
                actions["checkForUpdates"] = True
            elif c == curses.KEY_UP: dy = -1
            elif c == curses.KEY_DOWN: dy = 1
            elif c == curses.KEY_LEFT: dx = -1
            elif c == curses.KEY_RIGHT: dx = 1
            elif c == curses.KEY_MOUSE:
                mid, mx, my, mz, bstate = curses.getmouse()
                dx = mx - self._x - 4
                dy = my - self._y - 2
                survey = True
            elif c == ord(' ') or c == ord('\n'):
                survey = True

            if dx != 0 or dy != 0:
                if (self._x + dx) > self._fw - 1 or (self._y + dy) > self._fh - 1 or \
                    (self._x + dx) < 0 or (self._y + dy) < 0:
                    return actions

                putch(self._field_win, self._y, self._x, " ", curses.color_pair(0))
                self._x += dx ; self._y += dy
                putch(self._field_win, self._y, self._x, " ")
                

        if survey:
            actions["survey"] = (self._y, self._x)
            
        return actions
    

class OilFieldCursesView:
    def __init__(self, win):
        self._win = win

    def setField(self, field):
        assert isinstance(field, wildcatting.model.OilField)
        self._field = field

    def display(self):
        field = self._field

        colorChooser = CursesColorChooser()
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                if site.isSurveyed():
                    well = site.getWell()
                    if well is None:
                        # work around an MacOS X terminal problem with
                        # displaying blank characters - it doesn't draw
                        # the background if the well is " "
                        symbol = "."
                        color = colorChooser.blankColor(site)
                    else:
                        symbol = well.getPlayer().getSymbol()
                        color = colorChooser.siteColor(site)

                    putch(self._win, row, col, ord(symbol), color)

        self._win.refresh()

# workaround so we can write things to the bottom corner
# or otherwise with the same method call
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
        site.setWell("B")
        view.display()

if __name__ == "__main__":
    curses.wrapper(main)
