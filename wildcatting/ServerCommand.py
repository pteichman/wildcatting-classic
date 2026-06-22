import logging
import socket
from argparse import Namespace

import wildcatting.server
import wildcatting.theme
import wildcatting.util
import wildcatting.version
from wildcatting.cmdparse import Command


class ServerCommand(Command):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        Command.__init__(self, "server", summary="Run the Wildcatting server")
        self.add_argument("-n", "--host", default="", help="server hostname")
        self.add_argument("-p", "--port", type=int, default=7777, help="server port")

    def run(self, options: Namespace, args: list[str]) -> None:
        wildcatting.util.start_logger("server.log")

        host = options.host

        s = wildcatting.server.TieredXMLRPCServer((host, options.port))

        theme = wildcatting.theme.DefaultTheme()

        base = wildcatting.server.BaseService()
        s.register_function(base.echo)
        s.register_function(base.ping)
        s.register_function(base.version)

        admin = wildcatting.server.AdminService()
        s.register_function(admin.ping, "admin.ping")

        game = wildcatting.server.GameService(theme)
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

        setting = wildcatting.server.SettingService(theme)
        s.register_function(setting.get_setting, "setting.getSetting")
        s.register_introspection_functions()

        if len(host) == 0:
            # use hostname for display purposes, even if we're bound
            # to all interfaces
            host = socket.gethostname()

        url = f"http://{host}:{options.port}/"

        self.log.info("Wildcatting server start")
        print(f"{wildcatting.version.VERSION_STRING} server listening at {url}")
        try:
            s.serve_forever()
        finally:
            self.log.info("Wildcatting server shutdown")
