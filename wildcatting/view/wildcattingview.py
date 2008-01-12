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

    def setMessage(self, msg):
        self._msg = msg

    def display(self):
        self._stdscr.clear()
        self._eatAllKeyEvents(self._stdscr)

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
    TOP_PADDING = TOP_BORDER * 2 + 3
    SIDE_PADDING = SIDE_BORDER * 2 + 2
    
    def __init__(self, stdscr, wildcatting_, setting):
        View.__init__(self, stdscr)

        self._wildcatting = wildcatting_
        self._setting = setting

        (h, w) = stdscr.getmaxyx()
        bwh = h - (self.TOP_BORDER * 2)
        bww = w - (self.SIDE_BORDER * 2)

        field = wildcatting_.getPlayerField()
        rows, cols = field.getHeight(), field.getWidth()
        self._border_win = stdscr.derwin(bwh, bww, 1, 3)
        self._field_win = stdscr.derwin(rows, cols, 2, 4)
        bkgd = Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)
        self._field_win.bkgdset(" ", bkgd)
        probView = wildcatting.view.OilFieldProbabilityView(self._field_win, wildcatting_)
        drillCostView = wildcatting.view.OilFieldDrillCostView(self._field_win, wildcatting_,
                                                                         setting.getMinDrillCost(),
                                                                         setting.getMaxDrillCost())
        depthView = wildcatting.view.OilFieldDepthView(self._field_win, wildcatting_)
        self._views = [probView, drillCostView, depthView]
        self._currentView = 0

        self._week = None
        self._fact = None

        self._fh, self._fw = self._field_win.getmaxyx()
        self._colorChooser = wildcatting.view.ColorChooser()
        self._x, self._y = 0, 0

    def _drawBorder(self):
        (h, w) = self._stdscr.getmaxyx()
        location = self._setting.getLocation()
        era = self._setting.getEra()

        topstr = "%s, %s." % (location, era)
        if self._wildcatting.isGameFinished():
            self._stdscr.addstr(0, 4, topstr, curses.A_BOLD)
        else:            
            pricestr = self._setting.getPriceFormat() % self._wildcatting.getOilPrice()
            topstr = topstr + "  Oil is %s" % pricestr
            self._stdscr.addstr(0, 4, topstr, curses.A_BOLD)

            week = "Week %d" % self._wildcatting.getWeek()

            newWeek = False
            if week != self._week:
                newWeek = True

            self._week = week

            self._stdscr.addstr(0, w - self.SIDE_BORDER - len(week) - 1, week, curses.A_BOLD)

            if newWeek:
                self._fact = random.choice(self._setting.getFacts())
            wrapped = self._wrap_fact(self._fact, " "*4, w-8)
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
        keyStr = " " * (border_w - 2)
        blackOnWhite = Colors.get(curses.COLOR_BLACK, curses.COLOR_WHITE)
        self._border_win.addstr(border_h - 2, 1, keyStr, blackOnWhite)
        for i in xrange(len(colors)):
            color = colors[i]
            self._border_win.addstr(border_h - 2, 1 + i, " ", color)

        if self._mac:
            col = len(colors) + 1
            color = Colors.get(curses.COLOR_WHITE, curses.COLOR_WHITE)
            self._border_win.addstr(border_h - 2, col, "." * (border_w - col - 1), color)

        label = " %s" % self._getCurrentView().getKeyLabel()
        self.addLeft(self._border_win, border_h - 2, label, blackOnWhite, pad=len(colors)+1)

        coordStr = "X=%s   Y=%s" % (str(self._x).rjust(2), str(self._y).rjust(2))
        self.addCentered(self._border_win, border_h - 2, coordStr, blackOnWhite)

        if not self._wildcatting.isGameFinished():
            self.addRight(self._border_win, border_h - 2, "%s's turn" % self._wildcatting.getPlayersTurn(), blackOnWhite)
            
        self._border_win.refresh()

    def _getCurrentView(self):
        return self._views[self._currentView]

    def _nextView(self):
        self._currentView = (self._currentView + 1) % len(self._views)

    def indicateTurn(self):
        border_h, border_w = self._border_win.getmaxyx()

        blackOnGreen = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)
        if self._mac:
            self.addCentered(self._border_win, border_h - 2, "." * (border_w - 2),
                             Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN))
            self.addCentered(self._border_win, border_h - 2, "GO %s!" % self._wildcatting.getPlayersTurn().upper(),
                             blackOnGreen)
        else:
            bar = ("GO %s!" % self._wildcatting.getPlayersTurn().upper()).center(border_w-2)
            self.addCentered(self._border_win, border_h - 2, bar, blackOnGreen)
        self._field_win.refresh()
        self._border_win.refresh()
        self._stdscr.move(self._y + 2, self._x + 4)
        self._field_win.refresh()

    def display(self):
        curses.curs_set(1)
        self._stdscr.clear()
        self._drawBorder()
        self._eatAllKeyEvents(self._stdscr)
        self._getCurrentView().display()

    def input(self, c=None):
        actions = {}

        self._stdscr.move(self._y + 2, self._x + 4)
        self._field_win.refresh()
        self._drawKeyBar()
            
        dx = 0 ; dy = 0
        survey = False

        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.halfdelay(50)

        if c is None:
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
        elif c == ord('\t'):
            self._nextView()
            self._getCurrentView().display()

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
        self._getCurrentView().animateGameEnd()
        
