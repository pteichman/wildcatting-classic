import curses

class client:
    def wildcatting(self, stdscr):
        (h,w) = stdscr.getmaxyx()
        win = stdscr.derwin(h-4, w-6, 2, 3)
    
        win.addstr(1, 1, "Let's go wildcatting!\n", curses.A_REVERSE)
        win.box()
        win.refresh()

        while True:
            pass

    def run(self):
        curses.wrapper(self.wildcatting)
