import curses
import logging
import time
from argparse import Namespace

from wildcatting.client import Wildcatting
from wildcatting.cmdparse import Command
from wildcatting.game import Game
from wildcatting.view import (
    FadeInOilFieldCursesAnimator,
    OilFieldCursesView,
    OilFieldDrillCostView,
    OilFieldProbabilityView,
    OilFieldTextView,
)


class ScreensaverCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(
            self, "screensaver", summary="avoid character burn-in on your terminals"
        )

        self.add_argument("--no-border", action="store_true", help="disable border")
        self.add_argument(
            "--ascii",
            action="store_true",
            help="enable advanced ascii display (recommended)",
        )
        self.add_argument("--ansi", action="store_true", help="enable ansi display")
        self.add_argument("--fade-in", action="store_true", help="fade in mode")
        self.add_argument(
            "--probability",
            action="store_true",
            default=True,
            help="probabilty landscapes",
        )
        self.add_argument(
            "--drill-cost", action="store_true", help="drill cost landscapes"
        )

        self.y_border = 2
        self.x_border = 3

    def ascii_screensaver(self) -> None:
        while True:
            game = Game(80, 23)
            field = game.oil_field
            OilFieldTextView(field).ascii()
            time.sleep(0.25)

    def ansi_screensaver(self) -> None:
        try:
            while True:
                game = Game(80, 23)
                field = game.oil_field
                OilFieldTextView(field).ansi()
                time.sleep(0.25)
        except Exception:
            print(chr(27) + "[0m")

    def border_win(
        self, parent: curses.window, no_border: bool
    ) -> tuple[int, curses.window]:
        if no_border:
            win = parent
            border = 0
        else:
            h, w = parent.getmaxyx()
            win = parent.derwin(
                h - self.y_border * 2,
                w - self.x_border * 2,
                self.y_border,
                self.x_border,
            )
            win.box()
            border = 1
        win.refresh()

        return border, win

    def player_screensaver(
        self, stdscr: curses.window, options: Namespace, args: list[str]
    ) -> None:
        border, border_win = self.border_win(stdscr, options.no_border)
        border_win_h, border_win_w = border_win.getmaxyx()
        height = border_win_h - border * 2
        width = border_win_w - border * 2
        win = border_win.derwin(height, width, border, border)
        win_h, win_w = win.getmaxyx()

        while True:
            game = Game(win_w, win_h)
            field = game.oil_field

            w = Wildcatting()
            w.player_field = field
            view: OilFieldCursesView
            if options.drill_cost:
                view = OilFieldDrillCostView(win, w, 1, 25)
            else:
                view = OilFieldProbabilityView(win, w)

            win.clear()
            animator = FadeInOilFieldCursesAnimator(field)
            while not animator.is_done():
                animator.animate()
                view.display()

    def view_screensaver(
        self, stdscr: curses.window, options: Namespace, args: list[str]
    ) -> None:
        border, border_win = self.border_win(stdscr, options.no_border)
        border_win_h, border_win_w = border_win.getmaxyx()
        height = border_win_h - border * 2
        width = border_win_w - border * 2
        win = border_win.derwin(height, width, border, border)
        win_h, win_w = win.getmaxyx()

        while True:
            game = Game(win_w, win_h)
            field = game.oil_field

            w = Wildcatting()
            w.player_field = field
            view: OilFieldCursesView
            if options.drill_cost:
                view = OilFieldDrillCostView(win, w, 1, 25)
            else:
                view = OilFieldProbabilityView(win, w)

            for row in range(field.height):
                for col in range(field.width):
                    site = field.get_site(row, col)
                    site.surveyed = True

            view.display()
            time.sleep(0.25)

    def run(self, options: Namespace, args: list[str]) -> None:
        if options.ascii:
            self.ascii_screensaver()
        elif options.ansi:
            self.ansi_screensaver()
        elif options.fade_in:
            curses.wrapper(self.player_screensaver, options, args)
        else:
            curses.wrapper(self.view_screensaver, options, args)
