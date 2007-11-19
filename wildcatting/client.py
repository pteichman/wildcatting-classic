import curses

from views import PlayerField
from views import FieldView
from views import putch
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
        self._border_win.box()
        self._border_win.refresh()
                    

    def wildcatting(self, stdscr):
        self._stdscr = stdscr
        
        (h,w) = stdscr.getmaxyx()
        border_h = h - 4
        border_w = w - 6
        field_w = border_w - 2
        field_h = border_h - 2
        self._oilfield = OilField(field_w, field_h)
        self._playerfield = PlayerField(field_w, field_h)
        self._border_win = stdscr.derwin(border_h, border_w, 2, 3)
        self._field_win = stdscr.derwin(field_h, field_w, 3, 4)
        self._field_win.keypad(1)
        self.border()

        view = FieldView(self._field_win, self._playerfield)

        x = 0 ; y = 0
        
        self._field_win.addch(y, x, " ", curses.A_REVERSE | curses.A_BLINK)
        self._field_win.refresh()
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        while True:
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
                self._field_win.move(y, x)
                self._field_win.refresh()

            if survey:
                self.survey(x, y)

            putch(self._field_win, y, x, " ", curses.A_REVERSE | curses.A_BLINK)
            view.display()

    def run(self):
        curses.wrapper(self.wildcatting)
