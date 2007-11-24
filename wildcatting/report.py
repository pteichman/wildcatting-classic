import curses
import random

import wildcatting.model

class SurveyorsReport:

    def __init__(self, stdscr, site):
        self._stdscr = stdscr
        self._site = site
        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()
        
        (h, w) = self._win.getmaxyx()
        coord_str = "X=%s  Y=%s" % (self._site.getCol(), self._site.getRow())
        prob_str = str(self._site.getProbability()) + "%"
        cost_str = "$" + str(self._site.getCost()).rjust(4)
        tax_str = "$" + str(self._site.getTax()).rjust(4)

        self._win.bkgd(" ", curses.color_pair(1))
        self._win.addstr(1, 14, "SURVEYOR'S REPORT")
        self._win.addstr(4, 12, "LOCATION")
        self._win.addstr(4, 24, coord_str)
        self._win.addstr(6, 12, "PROBABILITY OF OIL")
        self._win.addstr(6, 31, prob_str)
        self._win.addstr(8, 12, "COST PER METER")
        self._win.addstr(8, 29, cost_str)
        self._win.addstr(10, 12, "TAXES PER WEEK")
        self._win.addstr(10, 29, tax_str)
        self._win.addstr(15, 13, "DRILL A WELL? (Y-N) ")

        self._win.refresh()

    def input(self):
        (h, w) = self._stdscr.getmaxyx()
        (wh, ww) = self._win.getmaxyx()
        done = False
        cur = 'n'
        self._win.keypad(1)
        self._win.move(15, 30)
        self._win.refresh()
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.curs_set(1)
        while not done:
            c = self._win.getch()
            if c == curses.KEY_UP or c == curses.KEY_LEFT:
                cur = 'y'
            elif c == curses.KEY_DOWN or c == curses.KEY_RIGHT:
                cur = 'n'
            elif c == ord('y'):
                cur = 'y'
                done = True
            elif c == ord('n'):
                cur = 'n'
                done = True
            elif (c == ord(' ')) or (c == 10):
                done = True
            elif c == curses.KEY_MOUSE:
                mid, mx, my, mz, bstate = curses.getmouse()
                x = mx - (w-ww)/2
                y = my - (h-wh)/2
                
                if y == 15 and x == 28:
                    cur = 'y'
                    done = True
                if y == 15 and x == 30:
                    cur = 'n'
                    done = True

            if cur == 'y':
                self._win.move(15, 28)
            else:
                self._win.move(15, 30)
                
            self._win.refresh()
            
        return cur == 'y'
            


def main(stdscr):
        (h,w) = stdscr.getmaxyx()
        win = stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)
        site = wildcatting.model.Site(32, 15, 25)
        report = SurveyorsReport(win, site)
        report.display()
        while True:
            pass
    
if __name__ == "__main__":
    curses.wrapper(main)
