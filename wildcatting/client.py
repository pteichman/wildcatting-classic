import curses

from views import PlayerField
from views import FieldView
from oilfield import OilField

class client:

    def survey(self, win, x, y):
        site = self._oilfield.getSite(x, y)
        self._playerfield.setSite(x, y, site)

    def wildcatting(self, stdscr):
        (h,w) = stdscr.getmaxyx()
        stdscr.addstr(1, 3, "Let's go wildcatting!\n", curses.A_REVERSE)
        field_h = h - 4
        field_w = w - 6
        self._oilfield = OilField(field_w, field_h)
        self._playerfield = PlayerField(field_w, field_h)

        win = stdscr.derwin(field_h, field_w, 2, 3)
        win.box()
        win.refresh()

        view = FieldView(win, self._playerfield)

        x = 1 ; y = 1
        
        curses.curs_set(0)
        win.addch(y, x, " ", curses.A_REVERSE)
        win.refresh()
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        while True:
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
                self.survey(stdscr, mx-3, my-2)
                stdscr.addstr(1, w-6, str(self._playerfield.getSite(mx-3, my-2).prob) + "% ")
            elif c == ord(' '): 
                self.survey(stdscr, x, y)
                stdscr.addstr(1, w-6, str(self._playerfield.getSite(x, y).prob) + "% ")
            if dx != 0 or dy != 0:
                win.addch(y, x, " ", curses.color_pair(0))
                x += dx ; y += dy
                win.addstr(y, x, " ")

            win.addch(y, x, " ", curses.A_REVERSE)
            view.display()

    def run(self):
        curses.wrapper(self.wildcatting)
