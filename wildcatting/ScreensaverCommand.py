import logging
import time
import random
import curses

from wildcatting.cmdparse import Command
from wildcatting.oilfield import OilField
from wildcatting.views import OilFieldTextView, OilFieldCursesView
from wildcatting.views import PlayerField

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
            field = OilField(80, 23)
            OilFieldTextView(field.getModel()).ascii()
            time.sleep(.25)

    def ansiScreensaver(self):
        try:
            while True:
                field = OilField(80, 23)
                OilFieldTextView(field.getModel()).ansi()
                time.sleep(.25)
        except:
            print chr(27) + '[0m'

    def cursesScreensaver(self, stdscr, options, args):
        if options.no_border:
            win = stdscr
            border = 0
        else:
            screen_h, screen_w = stdscr.getmaxyx()
            win = stdscr.derwin(screen_h-self.y_border*2,
                                screen_w-self.x_border*2,
                                self.y_border, self.x_border)
    
            win.box()
            border = 1

        win_h, win_w = win.getmaxyx()
        win = win.derwin(win_h-border*2, win_w-border*2, border, border)
        ScreenSaver(win).run()

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
        win = border_win.derwin(border_win_h-border*2, border_win_w-border*2, border, border)
        win_h, win_w = win.getmaxyx()

        while True:
            field = OilField(win_w-1, win_h)
            playerField = PlayerField(win_w-1, win_h)
            view = OilFieldView(win, playerField)
            coords = []
            for i in xrange(0, win_w-1):
                for j in xrange(0, win_h):
                    coords += [(i, j)]

            while len(coords) > 0:
                choice = random.randint(0,len(coords)-1)
                x, y = coords[choice]
                del coords[choice]
                site = field.getSite(x, y)
                playerField.setSite(x, y, site)
                view.display()

    def viewScreensaver(self, stdscr, options, args):
        border, border_win = self.borderWin(stdscr, options.no_border)
        border_win_h, border_win_w = border_win.getmaxyx()
        height = border_win_h - border * 2
        width = border_win_w - border * 2
        win = border_win.derwin(height, width, border, border)
        win_h, win_w = win.getmaxyx()
        while True:
            field = OilField(win_w, win_h)
            view = OilFieldCursesView(win, field)
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

