import curses
import logging
import random
import textwrap
from dataclasses import dataclass

from wildcatting.colors import Colors

from .oilfieldview import (
    OilFieldDepthView,
    OilFieldDrillCostView,
    OilFieldProbabilityView,
    ProbabilityColorChooser,
)
from .view import View


@dataclass
class DrillInput:
    drill: bool = False
    stop: bool = False


def _drill_key(c: int) -> DrillInput:
    if c == ord("q") or c == ord("Q"):
        return DrillInput(stop=True)
    if c != -1:
        return DrillInput(drill=True)
    return DrillInput()


class DrillView(View):
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr, site, setting):
        self._stdscr = stdscr
        self._site = site
        self._setting = setting
        self._msg = None

    def set_message(self, msg):
        self._msg = msg

    def display(self):
        self._stdscr.clear()

        drillDepth = self._site.well.drill_depth * self._setting.drill_increment
        drillCost = self._site.drill_cost
        cost = drillDepth * drillCost

        height, width = self._stdscr.getmaxyx()
        row = (height - 5) // 2

        if self._msg is not None:
            self.addCentered(self._stdscr, row - 2, self._msg)

        self.addCentered(self._stdscr, row, "PRESS ANY KEY TO DRILL")
        self.addCentered(self._stdscr, row + 1, "PRESS Q TO STOP")
        self.addCentered(self._stdscr, row + 3, f"DEPTH: {drillDepth}")
        self.addCentered(self._stdscr, row + 4, f" COST: {cost}")
        self._stdscr.refresh()

    def input(self) -> DrillInput:
        return _drill_key(self._stdscr.getch())


@dataclass
class WildcattingInput:
    survey: tuple[int, int] | None = None
    check_for_updates: bool = False


def _wildcatting_key(
    c: int,
    x: int,
    y: int,
    fw: int,
    fh: int,
    mouse_pos: tuple[int, int] | None,
) -> tuple[int, int, WildcattingInput]:
    dx, dy, survey = 0, 0, False

    if c == -1:
        return x, y, WildcattingInput(check_for_updates=True)
    elif c == curses.KEY_UP:
        dy = -1
    elif c == curses.KEY_DOWN:
        dy = 1
    elif c == curses.KEY_LEFT:
        dx = -1
    elif c == curses.KEY_RIGHT:
        dx = 1
    elif c == curses.KEY_MOUSE and mouse_pos is not None:
        dx = mouse_pos[0] - x - 4
        dy = mouse_pos[1] - y - 2
        survey = True
    elif c == ord(" ") or c == ord("\n"):
        survey = True

    if dx != 0 or dy != 0:
        new_x, new_y = x + dx, y + dy
        if new_x < 0 or new_x >= fw or new_y < 0 or new_y >= fh:
            return x, y, WildcattingInput()
        x, y = new_x, new_y

    if survey:
        return x, y, WildcattingInput(survey=(y, x))
    return x, y, WildcattingInput()


class WildcattingView(View):
    log = logging.getLogger("Wildcatting")

    TOP_BORDER = 2
    SIDE_BORDER = 3
    TOP_PADDING = TOP_BORDER * 2 + 3
    SIDE_PADDING = SIDE_BORDER * 2 + 2

    def __init__(self, stdscr, wildcatting_, setting):
        View.__init__(self, stdscr)

        self._wildcatting = wildcatting_
        self._setting = setting

        (h, w) = stdscr.getmaxyx()
        bwh = h - (self.TOP_BORDER * 2)
        bww = w - (self.SIDE_BORDER * 2)

        field = wildcatting_.player_field
        rows, cols = field.height, field.width
        self._border_win = stdscr.derwin(bwh, bww, 1, 3)
        self._field_win = stdscr.derwin(rows, cols, 2, 4)
        bkgd = Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)
        self._field_win.bkgdset(" ", bkgd)
        probView = OilFieldProbabilityView(self._field_win, wildcatting_)
        drillCostView = OilFieldDrillCostView(
            self._field_win,
            wildcatting_,
            setting.min_drill_cost,
            setting.max_drill_cost,
        )
        depthView = OilFieldDepthView(self._field_win, wildcatting_)
        self._views = [probView, drillCostView, depthView]
        self._currentView = 0

        self._week = None
        self._fact = None

        self._fh, self._fw = self._field_win.getmaxyx()
        self._colorChooser = ProbabilityColorChooser()
        self._x, self._y = 0, 0

    def _draw_border(self):
        (h, w) = self._stdscr.getmaxyx()
        location = self._setting.location
        era = self._setting.era

        topstr = f"{location}, {era}."
        if self._wildcatting.game_finished:
            self._stdscr.addstr(0, 4, topstr, curses.A_BOLD)
        else:
            pricestr = self._setting.price_format % self._wildcatting.oil_price
            topstr = topstr + f"  Oil is {pricestr}"
            self._stdscr.addstr(0, 4, topstr, curses.A_BOLD)

            week = f"Week {self._wildcatting.week}"

            newWeek = False
            if week != self._week:
                newWeek = True

            self._week = week

            self._stdscr.addstr(
                0, w - self.SIDE_BORDER - len(week) - 1, week, curses.A_BOLD
            )

            if newWeek:
                self._fact = random.choice(self._setting.facts)
            wrapped = self._wrap_fact(self._fact, " " * 4, w - 8)
            self._stdscr.addstr(h - 3, 0, wrapped)

        self._border_win.box()

    def _wrap_fact(self, fact, indent, width):
        """Wrap a fact across three lines"""
        lines = textwrap.wrap(
            fact,
            width,
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=True,
        )

        # we only have space for three lines
        if len(lines) > 3:
            lines = lines[:3]

        return "\n".join(lines)

    def _draw_key_bar(self):
        border_h, border_w = self._border_win.getmaxyx()
        colors = list(self._colorChooser.get_colors())
        colors.reverse()
        keyStr = " " * (border_w - 2)
        blackOnWhite = Colors.get(curses.COLOR_BLACK, curses.COLOR_WHITE)
        self._border_win.addstr(border_h - 2, 1, keyStr, blackOnWhite)
        for i in range(len(colors)):
            color = colors[i]
            self._border_win.addstr(border_h - 2, 1 + i, " ", color)

        if self._mac:
            col = len(colors) + 1
            color = Colors.get(curses.COLOR_WHITE, curses.COLOR_WHITE)
            self._border_win.addstr(
                border_h - 2, col, "." * (border_w - col - 1), color
            )

        label = f" {self._get_current_view().get_key_label()}"
        self.addLeft(
            self._border_win, border_h - 2, label, blackOnWhite, pad=len(colors) + 1
        )

        turn = self._wildcatting.players_turn
        if turn is not None:
            coordStr = f"X={str(self._x).rjust(2)}   Y={str(self._y).rjust(2)}"
            self.addCentered(self._border_win, border_h - 2, coordStr, blackOnWhite)
            if not self._wildcatting.game_finished:
                self.addRight(
                    self._border_win, border_h - 2, f"{turn}'s turn", blackOnWhite
                )
        else:
            longestLabel = 0
            for view in self._views:
                if len(view.get_key_label()) > longestLabel:
                    longestLabel = len(view.get_key_label())

            players = self._wildcatting.pending_players
            label = " WAITING FOR {}".format(", ".join(players).upper())
            self.addLeft(
                self._border_win,
                border_h - 2,
                label,
                blackOnWhite,
                pad=len(colors) + 1 + longestLabel + 4,
            )

        self._border_win.refresh()

    def _get_current_view(self):
        return self._views[self._currentView]

    def _next_view(self):
        self._currentView = (self._currentView + 1) % len(self._views)

    def indicate_turn(self):
        border_h, border_w = self._border_win.getmaxyx()

        blackOnGreen = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)

        go = f"GO {self._wildcatting.players_turn.upper()}!"
        if self._mac:
            bkgd, text = self.get_green_fgbg()
            self.addCentered(self._border_win, border_h - 2, "." * (border_w - 2), text)
        else:
            go = go.center(border_w - 2)

        self.addCentered(self._border_win, border_h - 2, go, blackOnGreen)
        self._stdscr.move(self._y + 2, self._x + 4)
        self._border_win.refresh()
        self._field_win.refresh()

    def display(self):
        curses.curs_set(1)
        self._stdscr.clear()
        self._draw_border()
        self._get_current_view().display()

    def input(self, c=None, refresh=50) -> WildcattingInput:
        self._stdscr.move(self._y + 2, self._x + 4)
        self._field_win.refresh()
        curses.curs_set(0)
        self._draw_key_bar()

        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.halfdelay(refresh)
        curses.curs_set(1)

        if c is None:
            c = self._stdscr.getch()

        mouse_pos = None
        if c == curses.KEY_MOUSE:
            _mid, mx, my, _mz, _bstate = curses.getmouse()
            mouse_pos = (mx, my)
        elif c == ord("\t"):
            self._next_view()
            self._get_current_view().display()

        self._x, self._y, action = _wildcatting_key(
            c, self._x, self._y, self._fw, self._fh, mouse_pos
        )
        return action

    def animate_game_end(self):
        curses.curs_set(0)
        self._draw_key_bar()
        self._get_current_view().animate_game_end()
