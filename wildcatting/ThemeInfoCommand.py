import logging
import inspect
import textwrap

import wildcatting.theme
import wildcatting.table

from cmdparse import Command

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
            if name == "DefaultTheme":
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
            self.error("Unknown theme: %s" % themeName)

        theme = found()

        print "Name: %s" % themeName
        print "Location: %s" % theme.getLocation()
        print "Era: %s" % theme.getEra()
        print
        prices = theme.getOilPrices()
        print "Oil price generator: %s" % str(prices)

        print

        print "Drilling cost: %s .. %s per %d depth units" \
              % (self._formatPrice(theme, theme.getMinDrillCost()),
                 self._formatPrice(theme, theme.getMaxDrillCost()),
                 theme.getDrillIncrement())
        print "Taxes: %s .. %s" % (self._formatPrice(theme, theme.getMinTax()),
                                   self._formatPrice(theme, theme.getMaxTax()))
        print "Maximum oil output: %d barrels" % theme.getMaxOutput()
        print "At starting price, well profit is %s .. %s" % (self._formatPrice(theme, theme.getMinOutput()), self._formatPrice(theme, theme.getMaxOutput() * prices.getInitialPrice()))

        print
        print "Facts:"

        for fact in theme.getFacts():
            print textwrap.fill(fact.strip(), initial_indent="* ", subsequent_indent="  ")

    def printAllThemes(self):
        themes = self._getAllThemes()

        cols = ("Name", "Location", "Era", "Facts")

        rows = []
        for (name, theme) in themes:
            obj = theme()
            if theme == wildcatting.theme.DefaultTheme:
                name = "%s (default)" % name
            
            rows.append((name, obj.getLocation(), obj.getEra(), str(len(obj.getFacts()))))

        print wildcatting.table.format_table(cols, rows)
