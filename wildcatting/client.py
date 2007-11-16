import curses

from views import PlayerField
from views import FieldView
from oilfield import OilField
from report import SurveyorsReport

class client:

    def survey(self, x, y):
        site = self._oilfield.getSite(x, y)
        report = SurveyorsReport(self._stdscr, site)
        report.display()
        yes = report.input()
        if yes:
            site.rig = "B"
        self._playerfield.setSite(x, y, site)
        self._stdscr.clear()
        self.border()

    def border(self):
        (h,w) = self._stdscr.getmaxyx()
        self._stdscr.addstr(1, 3, "Let's go wildcatting!\n", curses.A_REVERSE)
        self._field_win.box()
        self._field_win.refresh()
                    

    def wildcatting(self, stdscr):
        self._stdscr = stdscr
        
        (h,w) = stdscr.getmaxyx()
        field_h = h - 4
        field_w = w - 6
        self._oilfield = OilField(field_w, field_h)
        self._playerfield = PlayerField(field_w, field_h)

        self._field_win = stdscr.derwin(field_h, field_w, 2, 3)
        self._field_win.keypad(1)
        self.border()

        view = FieldView(self._field_win, self._playerfield)

        x = 1 ; y = 1
        
        self._field_win.addch(y, x, " ", curses.A_REVERSE)
        self._field_win.refresh()
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        while True:
            curses.curs_set(0)
            dx = 0 ; dy = 0
            c = stdscr.getch()
            if c == curses.KEY_UP: dy = -1
            elif c == curses.KEY_DOWN: dy = 1
            elif c == curses.KEY_LEFT: dx = -1
            elif c == curses.KEY_RIGHT: dx = 1
            elif c == curses.KEY_MOUSE:
                mid, mx, my, mz, bstate = curses.getmouse()
                dx = mx - x - 3
                dy = my - y - 2
                self.survey(mx-3, my-2)
            elif c == ord(' '): 
                self.survey(x, y)

            if dx != 0 or dy != 0:
                self._field_win.addch(y, x, " ", curses.color_pair(0))
                x += dx ; y += dy
                self._field_win.addstr(y, x, " ")
                self._field_win.move(y, x)
                self._field_win.refresh()

            self._field_win.addch(y, x, " ", curses.A_REVERSE)
            view.display()

    def run(self):
        curses.wrapper(self.wildcatting)
