import logging
import time
import random
import curses

from wildcatting.cmdparse import Command
from wildcatting.views import OilFieldTextView, OilFieldCursesView
from wildcatting.game import Game

class ScreensaverCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "screensaver", summary="avoid character burn-in on your terminals")

        self.add_option("", "--no-border", action="store_true",
                        help="disable border")
        self.add_option("", "--ascii", action="store_true",
                        help="enable advanced ascii display (recommended)")
        self.add_option("", "--ansi", action="store_true",
                        help="enable ansi display")
        self.add_option("", "--fade-in", action="store_true",
                        help="fade in mode")

        self.y_border = 2
        self.x_border = 3

    def asciiScreensaver(self):
        while True:
            game = Game(80, 23)
            field = game.getOilField()
            OilFieldTextView(field).ascii()
            time.sleep(.25)

    def ansiScreensaver(self):
        try:
            while True:
                game = Game(80, 23)
                field = game.getOilField()
                OilFieldTextView(field).ansi()
                time.sleep(.25)
        except:
            print chr(27) + '[0m'

    def borderWin(self, parent, no_border):
        if no_border:
            win = parent
            border = 0
        else:
            h, w = parent.getmaxyx()
            win = parent.derwin(h - self.y_border * 2,
                                w - self.x_border * 2,
                                self.y_border, self.x_border)
            win.box()
            border = 1
        win.refresh()

        return border, win

    def playerScreensaver(self, stdscr, options, args):
        border, border_win = self.borderWin(stdscr, options.no_border)
        border_win_h, border_win_w = border_win.getmaxyx()
        height = border_win_h - border * 2
        width = border_win_w - border * 2
        win = border_win.derwin(height, width, border, border)
        win_h, win_w = win.getmaxyx()

        while True:
            game = Game(win_w, win_h)
            field = game.getOilField()

            view = OilFieldCursesView(win, field)

            coords = [(row, col) for row in xrange(field.getHeight())
                      for col in xrange(field.getWidth())]

            while len(coords) > 0:
                choice = random.randint(0, len(coords) - 1)
                row, col = coords[choice]
                del coords[choice]

                site = field.getSite(row, col)
                site.setSurveyed(True)
                view.display()
            time.sleep(0.25)

    def viewScreensaver(self, stdscr, options, args):
        border, border_win = self.borderWin(stdscr, options.no_border)
        border_win_h, border_win_w = border_win.getmaxyx()
        height = border_win_h - border * 2
        width = border_win_w - border * 2
        win = border_win.derwin(height, width, border, border)
        win_h, win_w = win.getmaxyx()

        while True:
            game = Game(win_w, win_h)
            field = game.getOilField()

            view = OilFieldCursesView(win, field)

            for row in xrange(field.getHeight()):
                for col in xrange(field.getWidth()):
                    site = field.getSite(row, col)
                    site.setSurveyed(True)

            view.display()
            time.sleep(0.25)

    def run(self, options, args):
        if options.ascii:
            self.asciiScreensaver()
        elif options.ansi:
            self.ansiScreensaver()
        elif options.fade_in:
            curses.wrapper(self.playerScreensaver, options, args)
        else:
            curses.wrapper(self.viewScreensaver, options, args)
