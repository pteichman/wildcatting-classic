import inspect
import logging
import textwrap
from argparse import Namespace

import wildcatting.theme
from wildcatting.table import format_table
from wildcatting.theme.theme import Theme

from .cmdparse import Command


class ThemeInfo(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "theme-info", summary="Get info about themes")

    def run(self, options: Namespace, args: list[str]) -> None:
        if len(args) == 0:
            self.print_all_themes()
        else:
            for theme in args:
                self.print_theme(theme)

    def _get_all_themes(self) -> list[tuple[str, type[Theme]]]:
        themes: list[tuple[str, type[Theme]]] = []
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

    def _format_price(self, theme: Theme, price: float) -> str:
        return str(theme.get_price_format() % price)

    def print_theme(self, theme_name: str) -> None:
        themes = self._get_all_themes()

        found = None
        for name, theme in themes:
            if name == theme_name:
                found = theme

        if found is None:
            self.error(f"Unknown theme: {theme_name}")
            return

        theme_obj = found()

        print(f"Name: {theme_name}")
        print(f"Location: {theme_obj.get_location()}")
        print(f"Era: {theme_obj.get_era()}")
        print()
        prices = theme_obj.get_oil_prices()
        print(f"Oil price generator: {str(prices)}")

        print()

        min_drill = self._format_price(theme_obj, theme_obj.get_min_drill_cost())
        max_drill = self._format_price(theme_obj, theme_obj.get_max_drill_cost())
        drill_inc = theme_obj.get_drill_increment()
        print(f"Drilling cost: {min_drill} .. {max_drill} per {drill_inc} depth units")
        min_tax = self._format_price(theme_obj, theme_obj.get_min_tax())
        max_tax = self._format_price(theme_obj, theme_obj.get_max_tax())
        print(f"Taxes: {min_tax} .. {max_tax}")
        print(f"Maximum oil output: {theme_obj.get_max_output()} barrels")
        min_profit = self._format_price(theme_obj, theme_obj.get_min_output())
        max_profit = self._format_price(
            theme_obj, theme_obj.get_max_output() * prices.get_initial_price()
        )
        print(f"At starting price, well profit is {min_profit} .. {max_profit}")

        print()
        print("Facts:")

        for fact in theme_obj.facts:
            print(
                textwrap.fill(fact.strip(), initial_indent="* ", subsequent_indent="  ")
            )

    def print_all_themes(self) -> None:
        themes = self._get_all_themes()

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
                    obj.get_location(),
                    obj.get_era(),
                    str(len(obj.facts)),
                )
            )

        print(format_table(cols, rows))
