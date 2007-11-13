import curses
import random

from oilfield import Site

class SurveyorsReport:

    def __init__(self, win, site):
        self._win = win
        self._site = site

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)

    def display(self):
        (h, w) = self._win.getmaxyx()
 
        coord_str = "X=%s  Y=%s" % (self._site.x, self._site.y)
        prob_str = str(self._site.prob) + "%"
        cost_str = "$" + str(self._site.cost).rjust(4)
        tax_str = "$" + str(self._site.tax).rjust(4)

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

def main(stdscr):
        (h,w) = stdscr.getmaxyx()
        win = stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)
        
        site = Site(32, 15, 25)
        site.cost = 12
        site.tax = 615
        report = SurveyorsReport(win, site)
        report.display()
        while True:
            pass
    
if __name__ == "__main__":
    curses.wrapper(main)
