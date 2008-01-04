import curses
import random
import logging
import textwrap

from view import View

from wildcatting.colors import Colors
import wildcatting.game
import wildcatting.model


class DrillView(View):
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr, site, setting):
        self._stdscr = stdscr
        self._site = site
        self._setting = setting
        self._msg = None

    def updateSite(self, site):
        self._site = site

    def setMessage(self, msg):
        self._msg = msg

    def display(self):
        self._stdscr.clear()

        drillDepth = self._site.getWell().getDrillDepth() * self._setting.getDrillIncrement()
        drillCost = self._site.getDrillCost()
        cost = drillDepth * drillCost
        
        height, width = self._stdscr.getmaxyx()
        row = (height - 5) / 2

        if self._msg is not None:
            self.addCentered(self._stdscr, row-2, self._msg)

        self.addCentered(self._stdscr, row, "PRESS ANY KEY TO DRILL")
        self.addCentered(self._stdscr, row + 1, "PRESS Q TO STOP")
        self.addCentered(self._stdscr, row + 3, "DEPTH: %s" % drillDepth)
        self.addCentered(self._stdscr, row + 4, " COST: %s" % cost)
        self._stdscr.refresh()

    def input(self):
        actions = {}

        c = self._stdscr.getch()
        if c == -1:
            pass
        elif c == ord('q') or c == ord('Q'):
            actions["stop"] = True
        else:
            actions["drill"] = True

        return actions


class WildcattingView(View):
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
        bkgd = Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)
        self._field_win.bkgdset(" ", bkgd)
        self._oilView = oilView = wildcatting.view.OilFieldCursesView(self._field_win)

        self._fh, self._fw = self._field_win.getmaxyx()
        self._colorChooser = wildcatting.view.ColorChooser()
        self._x, self._y = 0, 0
        self._turn = 1
        self._price = 0

    def _drawBorder(self):
        (h, w) = self._stdscr.getmaxyx()
        location = self._setting.getLocation()
        era = self._setting.getEra()

        pricestr = self._setting.getPriceFormat() % self._price
        
        self._stdscr.addstr(0, 4, "%s, %s.  Oil is %s." % (location, era, pricestr), curses.A_BOLD)

        week = "Week %d" % self._turn

        self._stdscr.addstr(0, w - self.SIDE_BORDER - len(week) - 1, week, curses.A_BOLD)
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

    def updatePrice(self, price):
        self._price = price

    def updateTurn(self, turn):
        self._turn = turn

    def display(self):
        self._stdscr.clear()
        self._drawBorder()
        self._oilView.display()

    def input(self):
        actions = {}
        
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.halfdelay(50)

        self._stdscr.move(self._y + 2, self._x + 4)
        self._field_win.refresh()
        self._drawKeyBar()
            
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
        elif c == ord('w'):
            actions["weeklyReport"] = True

        if dx != 0 or dy != 0:
            if (self._x + dx) > self._fw - 1 or (self._y + dy) > self._fh - 1 or \
                (self._x + dx) < 0 or (self._y + dy) < 0:
                return actions

            self._x += dx ; self._y += dy

        if survey:
            actions["survey"] = (self._y, self._x)
            
        return actions

    def animateGameEnd(self):
        curses.curs_set(0)
        self._drawKeyBar()
        self._stdscr.refresh()
        self._oilView.animateGameEnd()
        
