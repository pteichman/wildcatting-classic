import logging
import curses

from views import OilFieldCursesView
from views import putch
from report import SurveyorsReport
from game import Game

from wildcatting.model import OilField, Site

class Client:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, gameId, username, rig):
        self._gameId = gameId
        self._username = username
        self._rig = rig

    def _refreshPlayerField(self):
        self._stdscr.clear()
        self.border()
        self._playerField = OilField.deserialize(self._server.game.getPlayerField(self._handle))
        self._view.setField(self._playerField)
        self._view.display()

    def survey(self, x, y):
        oldsite = self._playerField.getSite(y, x)
        site = Site.deserialize(self._server.game.survey(self._handle, y, x))

        report = SurveyorsReport(self._stdscr, site, oldsite.isSurveyed())
        report.display()
        yes = report.input()
        if yes:
            self._server.game.drill(self._handle, y, x)

    def border(self):
        (h,w) = self._stdscr.getmaxyx()
        self._stdscr.addstr(1, 3, "Let's go wildcatting!\n", curses.A_REVERSE)
        self._border_win.box()

    def wildcatting(self, stdscr):
        self._stdscr = stdscr

        (h,w) = stdscr.getmaxyx()
        border_h = h - 4
        border_w = w - 6
        field_w = border_w - 2
        field_h = border_h - 2

        if self._gameId is None:
            self._gameId = self._server.game.new(field_w, field_h)
            self.log.info("Created a new game: ID is " + self._gameId)
        else:
            self.log.info("Reconnecting to game ID: " + self._gameId)

        self._handle = self._server.game.join(self._gameId, self._username, self._rig)

        self._border_win = stdscr.derwin(border_h, border_w, 2, 3)
        self._field_win = stdscr.derwin(field_h, field_w, 3, 4)

        self._view = view = OilFieldCursesView(self._field_win)

        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        self._refreshPlayerField()
        x = 0 ; y = 0
        while True:
            putch(self._field_win, y, x, " ", curses.A_REVERSE)
            self._field_win.refresh()
            self._view.display()
            
            curses.curs_set(0)
            dx = 0 ; dy = 0
            survey = False
            
            c = stdscr.getch()
            if c == curses.KEY_UP: dy = -1
            elif c == curses.KEY_DOWN: dy = 1
            elif c == curses.KEY_LEFT: dx = -1
            elif c == curses.KEY_RIGHT: dx = 1
            elif c == curses.KEY_MOUSE:
                mid, mx, my, mz, bstate = curses.getmouse()
                dx = mx - x - 4
                dy = my - y - 3
                survey = True
            elif c == ord(' '):
                survey = True

            if dx != 0 or dy != 0:
                if (x + dx) > field_w-1 or (y + dy) > field_h-1 or \
                    (x + dx) < 0 or (y + dy) < 0:
                    continue

                putch(self._field_win, y, x, " ", curses.color_pair(0))
                x += dx ; y += dy
                putch(self._field_win, y, x, " ")

            if survey:
                self.survey(x, y)
                self._refreshPlayerField()

    def run(self, server):
        self._server = server

        curses.wrapper(self.wildcatting)
