import logging
import curses
import curses.textpad
import time

from view import View

from wildcatting.colors import Colors
import wildcatting.model

class PlayerCount(View):
    def __init__(self, stdscr):
        View.__init__(self, stdscr)

        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self, gameFinished=False):
        self._stdscr.clear()
        self._stdscr.refresh()

        fg, bg = self.getGreenFGBG()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "WILDCATTING")
        self.addCentered(self._win, 3, "HOW MANY PLAYERS? (1-4) ")

        self._win.refresh()

    def input(self):
        while True:
            c = self._stdscr.getch()

            try:
                num = int(chr(c))
                if 0 < num < 5:
                    return num
            except:
                pass

            self.addCentered(self._win, 13, "INVALID INPUT")
            self._win.refresh()
            time.sleep(1.0)
            self.display()

class PlayerNames(View):
    def __init__(self, stdscr, count):
        View.__init__(self, stdscr)

        self._count = count
        self._textpads = []

        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self, gameFinished=False):
        self._stdscr.clear()
        self._stdscr.refresh()
        (h,w) = self._win.getmaxyx()

        fg, bg = self.getGreenFGBG()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "PLAYERS")

        for i in xrange(1, self._count+1):
            row = i*2+1
            self.addLeft(self._win, row, "%d. " % i, pad=10)

            win = self._win.derwin(1, w-13*2, row, 13)

            textpad = curses.textpad.Textbox(win)
            self._textpads.append(textpad)
            
        self._win.refresh()

    def input(self):
        names = []
        for i in xrange(self._count):
            self._textpads[i].edit()
            name = self._textpads[i].gather().strip()

            # mac workaround.. we have hidden dots all over the screen
            name = name.strip(".")
            
            names.append(name)

        return names

if __name__ == "__main__":
    def main(stdscr):
        view = PlayerCount(stdscr)
        view.display()

        count = view.input()

        view = PlayerNames(stdscr, count)
        view.display()

        global names
        names = view.input()

    curses.wrapper(main)
    print names
