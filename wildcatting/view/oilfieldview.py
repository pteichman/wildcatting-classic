import abc
import curses
import random
from typing import Any

import wildcatting.game
import wildcatting.model
from wildcatting.colors import Colors

from .view import View


class OilFieldTextView(View):
    def __init__(self, model: wildcatting.model.OilField) -> None:
        self._model = model

    def bracket(self, site: wildcatting.model.Site) -> int:
        p = site.probability
        if p > 95:
            b = 0
        elif p > 85:
            b = 1
        elif p > 70:
            b = 2
        elif p > 55:
            b = 3
        elif p > 35:
            b = 4
        else:
            b = 5
        return b

    def to_ascii(self, site: wildcatting.model.Site) -> str:
        b = self.bracket(site)
        return ".x%*&#"[b]

    def ascii(self) -> None:
        model = self._model
        for row in range(model.height):
            line = ""
            for col in range(model.width):
                line += self.to_ascii(model.get_site(row, col))
            print(line)

    def to_ansi(self, site: wildcatting.model.Site) -> str:
        b = self.bracket(site) % 9
        ansi = chr(27) + "[" + str(32 + b) + "m" + "O"
        return ansi

    def ansi(self) -> None:
        model = self._model
        for row in range(model.height):
            line = ""
            for col in range(model.width):
                line += self.to_ansi(model.get_site(row, col))
            print(line)


class ColorChooser(abc.ABC):
    def __init__(self) -> None:
        # increasing order of hotness
        self._colors = [
            Colors.get(curses.COLOR_WHITE, curses.COLOR_BLUE),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_CYAN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_GREEN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_YELLOW),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_MAGENTA),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_RED),
        ]

    @abc.abstractmethod
    def _choose_color(self, site: wildcatting.model.Site, colors: list[int]) -> int: ...

    def get_colors(self) -> list[int]:
        return self._colors[:]

    def site_color(self, site: wildcatting.model.Site | None) -> int:
        if site is None:
            return Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)

        return self._choose_color(site, self._colors)

    def blank_color(self, site: wildcatting.model.Site | None) -> int:
        if site is None:
            return Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)

        return self._choose_color(site, self._colors)


class ProbabilityColorChooser(ColorChooser):
    def _choose_color(self, site: wildcatting.model.Site, colors: list[int]) -> int:
        p = site.probability
        if p == 100:
            return colors[-1]

        return colors[int(p / 100.0 * len(colors))]


class DrillCostColorChooser(ColorChooser):
    def __init__(self, minDrillCost: int, maxDrillCost: int) -> None:
        ColorChooser.__init__(self)

        self._minDrillCost = minDrillCost
        self._maxDrillCost = maxDrillCost

    def _choose_color(self, site: wildcatting.model.Site, colors: list[int]) -> int:
        drillCost = site.drill_cost * 1.0
        costRange = self._maxDrillCost - self._minDrillCost
        idx = int(drillCost / costRange * (len(colors) - 1))

        return colors[idx]


class DepthColorChooser(ColorChooser):
    def _choose_color(self, site: wildcatting.model.Site, colors: list[int]) -> int:
        oilDepth = site.oil_depth
        if oilDepth is None:
            color = Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)
        else:
            depthRange = 9
            idx = int(oilDepth * 1.0 / depthRange * (len(colors) - 1))
            color = colors[idx]

        return color


class FadeInOilFieldCursesAnimator:
    def __init__(self, field: wildcatting.model.OilField) -> None:
        self._field = field

        self._coords: list[tuple[int, int]] = [
            (row, col) for row in range(field.height) for col in range(field.width)
        ]

    def is_done(self) -> bool:
        return len(self._coords) == 0

    def animate(self) -> None:
        row, col = random.choice(self._coords)
        self._coords.remove((row, col))

        site = self._field.get_site(row, col)
        site.surveyed = True


class OilFieldCursesView(View, abc.ABC):
    def __init__(self, win: Any, wildcatting_: Any) -> None:
        View.__init__(self, win)
        self._win = win
        self._wildcatting = wildcatting_

        self._colorChooser = self._make_color_chooser()

    @abc.abstractmethod
    def _make_color_chooser(self) -> ColorChooser: ...

    @abc.abstractmethod
    def get_key_label(self) -> str: ...

    def display(self) -> None:
        field = self._wildcatting.player_field
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                if site.surveyed:
                    self.display_site(site)

        self._win.refresh()

    def display_site(self, site: wildcatting.model.Site) -> None:
        well = site.well
        if well is None:
            # work around an MacOS X terminal problem with
            # displaying blank characters - it doesn't draw
            # the background if the well is " "
            if self._mac:
                symbol = "."
            else:
                symbol = " "
            color = self._colorChooser.blank_color(site)
        else:
            symbol = well.player.symbol
            color = self._colorChooser.site_color(site)

        self.putch(self._win, site.row, site.col, ord(symbol), color)

    def animate_game_end(self) -> None:
        animator = FadeInOilFieldCursesAnimator(self._wildcatting.player_field)
        while not animator.is_done():
            animator.animate()
            self.display()


class OilFieldProbabilityView(OilFieldCursesView):
    def _make_color_chooser(self) -> ColorChooser:
        return ProbabilityColorChooser()

    def get_key_label(self) -> str:
        return "PROBABILITY"


class OilFieldDrillCostView(OilFieldCursesView):
    def __init__(
        self, win: Any, wildcatting_: Any, minDrillCost: int, maxDrillCost: int
    ) -> None:
        self._minDrillCost = minDrillCost
        self._maxDrillCost = maxDrillCost

        OilFieldCursesView.__init__(self, win, wildcatting_)

    def get_key_label(self) -> str:
        return "DRILL COST"

    def _make_color_chooser(self) -> ColorChooser:
        return DrillCostColorChooser(self._minDrillCost, self._maxDrillCost)


class OilFieldDepthView(OilFieldCursesView):
    def _make_color_chooser(self) -> ColorChooser:
        return DepthColorChooser()

    def get_key_label(self) -> str:
        return "OIL DEPTH"

    def display_site(self, site: wildcatting.model.Site) -> None:
        well = site.well
        if well is None:
            # show a "." for surveyed sites
            symbol = "."
            color = self._colorChooser.blank_color(site)
        else:
            symbol = well.player.symbol
            color = self._colorChooser.site_color(site)

        self.putch(self._win, site.row, site.col, ord(symbol), color)
