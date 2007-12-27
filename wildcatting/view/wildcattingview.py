import curses
import random
import logging
import textwrap

from wildcatting.colors import Colors
import wildcatting.view
import wildcatting.game
import wildcatting.model


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
        self._oilView = oilView = wildcatting.view.OilFieldCursesView(self._field_win)

        self._fh, self._fw = self._field_win.getmaxyx()
        self._colorChooser = wildcatting.view.ColorChooser()
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
        actions = {}
        
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.halfdelay(50)

        self._oilView.display()
        wildcatting.view.putch(self._field_win, self._y, self._x, " ", curses.A_REVERSE)
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
        elif c == ord('w'):
            actions["weeklyReport"] = True

        if dx != 0 or dy != 0:
            if (self._x + dx) > self._fw - 1 or (self._y + dy) > self._fh - 1 or \
                (self._x + dx) < 0 or (self._y + dy) < 0:
                return actions

            wildcatting.view.putch(self._field_win, self._y, self._x, " ", curses.color_pair(0))
            self._x += dx ; self._y += dy
            wildcatting.view.putch(self._field_win, self._y, self._x, " ")
                

        if survey:
            actions["survey"] = (self._y, self._x)
            
        return actions
