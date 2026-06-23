import curses
import inspect
import logging
import os
import socket
import sys
import textwrap
import time
from argparse import Namespace
from xmlrpc.client import ServerProxy

import wildcatting.theme

from . import version
from .client import Client
from .cmdparse import Command
from .game import Game
from .server import (
    AdminService,
    BaseService,
    GameService,
    ServerProtocol,
    SettingService,
    StandaloneServer,
    TieredXMLRPCServer,
    XmlRpcServer,
)
from .state import Wildcatting
from .table import format_table
from .theme import DefaultTheme, Theme
from .util import start_logger
from .view.oilfieldview import FadeInOilFieldCursesAnimator, OilFieldTextView
from .view.wildcattingview import (
    OilFieldCursesView,
    OilFieldDrillCostView,
    OilFieldProbabilityView,
)


class ClientCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "client", summary="Run the Wildcatting client")

        user = os.environ.get("USER")
        if user is None:
            user = "none"
        symbol = user[0].upper()

        self.add_argument("--no-network", action="store_true")
        self.add_argument("-p", "--port", type=int, default=7777, help="server port")
        self.add_argument("-n", "--host", default="localhost", help="server hostname")
        self.add_argument("-u", "--username", default=user, help="username")
        self.add_argument("-m", "--hotseat", action="store_true", help="hotseat mode")
        self.add_argument("-s", "--symbol", default=symbol, help="well symbol")
        self.add_argument(
            "-w", "--weeks", type=int, default=13, help="length of game in weeks"
        )
        self.add_argument("-g", "--game", default=None, help="game id")
        self.add_argument("-r", "--handle", default=None, help="game handle")

    def run(self, options: Namespace, args: list[str]) -> None:
        start_logger("client.log")

        url = f"http://{options.host}:{options.port}/"
        if options.no_network:
            s: ServerProtocol = StandaloneServer()
        else:
            s = XmlRpcServer(ServerProxy(url, allow_none=True))

        try:
            server_version = s.version()
        except OSError as e:
            print(f"Socket error contacting {url}")
            print(e.args[1])
            sys.exit(0)

        if server_version != version.VERSION_STRING:
            cols = int(os.getenv("COLUMNS", 80)) - 5
            print(
                textwrap.fill(
                    f"ERROR: Server at {url} requires a {server_version} client", cols
                )
            )
            sys.exit(1)

        player = None if options.hotseat else (options.username, options.symbol)

        c = Client(options.weeks, options.game, options.handle, player)

        self.log.info("Wildcatting client start")
        try:
            c.run(s)
        finally:
            self.log.info("Wildcatting client shutdown")


class PingCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "ping", summary="Ping a Wildcatting server")

        self.add_argument("-p", "--port", type=int, default=7777, help="server port")
        self.add_argument("-n", "--host", default="localhost", help="server hostname")

    def run(self, options: Namespace, args: list[str]) -> None:
        url = f"http://{options.host}:{options.port}/"
        s = ServerProxy(url, allow_none=True)

        try:
            server_version = str(s.version())
        except Exception:
            print(f"Server at {url} is not up.")
            sys.exit(1)

        print(f"{server_version} server at {url} is up.")
        sys.exit(0)


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


class ServerCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "server", summary="Run the Wildcatting server")
        self.add_argument("-n", "--host", default="", help="server hostname")
        self.add_argument("-p", "--port", type=int, default=7777, help="server port")

    def run(self, options: Namespace, args: list[str]) -> None:
        start_logger("server.log")

        host = options.host

        s = TieredXMLRPCServer((host, options.port))

        theme = DefaultTheme()

        base = BaseService()
        s.register_function(base.echo)
        s.register_function(base.ping)
        s.register_function(base.version)

        admin = AdminService()
        s.register_function(admin.ping, "admin.ping")

        game = GameService(theme)
        s.register_function(game.drill, "game.drill")
        s.register_function(game.end_turn, "game.endTurn")
        s.register_function(game.erect, "game.erect")
        s.register_function(game.get_client_info, "game.getClientInfo")
        s.register_function(game.get_game_id, "game.getGameId")
        s.register_function(game.get_oil_price, "game.getOilPrice")
        s.register_function(game.get_pending_players, "game.getPendingPlayers")
        s.register_function(game.get_player_field, "game.getPlayerField")
        s.register_function(game.get_player_site, "game.getPlayerSite")
        s.register_function(game.get_players_turn, "game.getPlayersTurn")
        s.register_function(game.get_update, "game.getUpdate")
        s.register_function(game.get_week, "game.getWeek")
        s.register_function(game.get_weekly_summary, "game.getWeeklySummary")
        s.register_function(game.get_well_updates, "game.getWellUpdates")
        s.register_function(game.is_finished, "game.isFinished")
        s.register_function(game.is_started, "game.isStarted")
        s.register_function(game.join, "game.join")
        s.register_function(game.list_players, "game.listPlayers")
        s.register_function(game.new, "game.new")
        s.register_function(game.new_client_handle, "game.newClientHandle")
        s.register_function(game.sell, "game.sell")
        s.register_function(game.start, "game.start")
        s.register_function(game.survey, "game.survey")

        setting = SettingService(theme)
        s.register_function(setting.get_setting, "setting.getSetting")
        s.register_introspection_functions()

        if len(host) == 0:
            # use hostname for display purposes, even if we're bound
            # to all interfaces
            host = socket.gethostname()

        url = f"http://{host}:{options.port}/"

        self.log.info("Wildcatting server start")
        print(f"{version.VERSION_STRING} server listening at {url}")
        try:
            s.serve_forever()
        finally:
            self.log.info("Wildcatting server shutdown")


class ThemeInfoCommand(Command):
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
