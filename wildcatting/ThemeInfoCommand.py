import inspect
import logging
import textwrap

import wildcatting.table
import wildcatting.theme

from .cmdparse import Command


class ThemeInfo(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        Command.__init__(self, "theme-info", summary="Get info about themes")

    def run(self, options, args):
        if len(args) == 0:
            self.printAllThemes()
        else:
            for theme in args:
                self.printTheme(theme)

    def _getAllThemes(self):
        themes = []
        for name, member in inspect.getmembers(wildcatting.theme,
                                               inspect.isclass):
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

    def _formatPrice(self, theme, price):
        return theme.getPriceFormat() % price

    def printTheme(self, themeName):
        themes = self._getAllThemes()

        found = None
        for name, theme in themes:
            if name == themeName:
                found = theme

        if found is None:
            self.error(f"Unknown theme: {themeName}")

        theme = found()

        print(f"Name: {themeName}")
        print(f"Location: {theme.getLocation()}")
        print(f"Era: {theme.getEra()}")
        print()
        prices = theme.getOilPrices()
        print(f"Oil price generator: {str(prices)}")

        print()

        print("Drilling cost: %s .. %s per %d depth units" \
              % (self._formatPrice(theme, theme.getMinDrillCost()),
                 self._formatPrice(theme, theme.getMaxDrillCost()),
                 theme.getDrillIncrement()))
        print(f"Taxes: {self._formatPrice(theme, theme.getMinTax())} .. {self._formatPrice(theme, theme.getMaxTax())}")
        print("Maximum oil output: %d barrels" % theme.getMaxOutput())
        print(f"At starting price, well profit is {self._formatPrice(theme, theme.getMinOutput())} .. {self._formatPrice(theme, theme.getMaxOutput() * prices.getInitialPrice())}")

        print()
        print("Facts:")

        for fact in theme.getFacts():
            print(textwrap.fill(fact.strip(), initial_indent="* ", subsequent_indent="  "))

    def printAllThemes(self):
        themes = self._getAllThemes()

        cols = ("Name", "Location", "Era", "Facts")

        rows = []
        for (name, theme) in themes:
            obj = theme()
            display_name = name
            if theme == wildcatting.theme.DefaultTheme:
                display_name = f"{name} (default)"

            rows.append((display_name, obj.getLocation(), obj.getEra(), str(len(obj.getFacts()))))

        print(wildcatting.table.format_table(cols, rows))
