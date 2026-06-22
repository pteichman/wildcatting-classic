import inspect
import logging
import textwrap
from optparse import Values
from typing import Any

import wildcatting.table
import wildcatting.theme

from .cmdparse import Command


class ThemeInfo(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "theme-info", summary="Get info about themes")

    def run(self, options: Values, args: list[str]) -> None:
        if len(args) == 0:
            self.printAllThemes()
        else:
            for theme in args:
                self.printTheme(theme)

    def _getAllThemes(self) -> list[tuple[str, Any]]:
        themes: list[tuple[str, Any]] = []
        for name, member in inspect.getmembers(wildcatting.theme, inspect.isclass):
            if name in ("Theme", "DefaultTheme"):
                continue

            bases = inspect.getmro(member)
            if len(bases) == 1:
                # class cannot be a subclass of Theme
                continue

            if wildcatting.theme.Theme in bases:
                themes.append((name, member))

        themes.sort()
        return themes

    def _formatPrice(self, theme: Any, price: Any) -> str:
        return str(theme.getPriceFormat() % price)

    def printTheme(self, themeName: str) -> None:
        themes = self._getAllThemes()

        found = None
        for name, theme in themes:
            if name == themeName:
                found = theme

        if found is None:
            self.error(f"Unknown theme: {themeName}")
            return

        theme = found()

        print(f"Name: {themeName}")
        print(f"Location: {theme.getLocation()}")
        print(f"Era: {theme.getEra()}")
        print()
        prices = theme.getOilPrices()
        print(f"Oil price generator: {str(prices)}")

        print()

        min_drill = self._formatPrice(theme, theme.getMinDrillCost())
        max_drill = self._formatPrice(theme, theme.getMaxDrillCost())
        drill_inc = theme.getDrillIncrement()
        print(f"Drilling cost: {min_drill} .. {max_drill} per {drill_inc} depth units")
        min_tax = self._formatPrice(theme, theme.getMinTax())
        max_tax = self._formatPrice(theme, theme.getMaxTax())
        print(f"Taxes: {min_tax} .. {max_tax}")
        print(f"Maximum oil output: {theme.getMaxOutput()} barrels")
        min_profit = self._formatPrice(theme, theme.getMinOutput())
        max_profit = self._formatPrice(
            theme, theme.getMaxOutput() * prices.getInitialPrice()
        )
        print(f"At starting price, well profit is {min_profit} .. {max_profit}")

        print()
        print("Facts:")

        for fact in theme.getFacts():
            print(
                textwrap.fill(fact.strip(), initial_indent="* ", subsequent_indent="  ")
            )

    def printAllThemes(self) -> None:
        themes = self._getAllThemes()

        cols = ("Name", "Location", "Era", "Facts")

        rows = []
        for name, theme in themes:
            obj = theme()
            display_name = name
            if theme == wildcatting.theme.DefaultTheme:
                display_name = f"{name} (default)"

            rows.append(
                (
                    display_name,
                    obj.getLocation(),
                    obj.getEra(),
                    str(len(obj.getFacts())),
                )
            )

        print(wildcatting.table.format_table(cols, rows))
