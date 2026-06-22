import base64
import inspect
import logging
import re
from typing import Any, Protocol, cast
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

import wildcatting.model
import wildcatting.turn
from wildcatting.exceptions import WildcattingException
from wildcatting.game import Game

from . import version
from .theme import DefaultTheme


def _to_camel_case(name: str) -> str:
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)


class TieredXMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["allow_none"] = True
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    log = logging.getLogger("XMLRPCServer")

    def register_subinstance(self, tier: str, instance: Any) -> None:
        for name, method in inspect.getmembers(instance, inspect.ismethod):
            if not name.startswith("_"):
                self.register_function(method, f"{tier}.{_to_camel_case(name)}")

    def _dispatch(self, *args: Any, **kwargs: Any) -> Any:
        """Log all Exceptions raised by XML-RPC handlers"""
        try:
            response = SimpleXMLRPCServer._dispatch(self, *args, **kwargs)
        except:
            self.log.debug("XML-RPC Fault", exc_info=True)
            raise
        return response


class AdminService:
    def ping(self) -> bool:
        return True


class BaseService:
    def echo(self, s: str) -> str:
        return s

    def ping(self) -> bool:
        return True

    def version(self) -> str:
        return version.VERSION_STRING


class SettingService:
    def __init__(self, theme: Any) -> None:
        self._setting = theme.generate_setting()

    def get_setting(self) -> dict[str, Any]:
        return cast(dict[str, Any], self._setting.serialize())


class GameService:
    HANDLE_SEP = "::"

    log = logging.getLogger("Wildcatting")

    def __init__(self, theme: Any) -> None:
        self._games: dict[str, Game] = {}
        self._next_game_id: int = 0
        self._theme = theme

    def _get_game(self, game_id: str) -> Game:
        if not isinstance(game_id, str):
            raise WildcattingException("Invalid game id")

        game = self._games.get(game_id)
        if game is None:
            raise WildcattingException("Unknown game id: " + game_id)

        return game

    def _read_handle(self, handle: str) -> tuple[Game, wildcatting.model.Player]:
        if not isinstance(handle, str):
            raise WildcattingException("Invalid handle")

        self.log.debug("Reading handle: %s", handle)
        (game_id, player_name, secret) = self._decode_game_handle(handle)

        game = self._get_game(game_id)
        player = game.get_player(player_name, secret)

        return (game, player)

    def _read_client_handle(self, handle: str) -> tuple[Game, str]:
        if not isinstance(handle, str):
            raise WildcattingException("Invalid handle")

        (game_id, client_id) = self._decode_client_handle(handle)
        self.log.info("game_id: %s, client_id: %s", game_id, client_id)

        game = self._get_game(game_id)

        return (game, client_id)

    def _ensure_survey_turn(
        self, game: Game, player: wildcatting.model.Player
    ) -> wildcatting.turn.Turn:
        if game.finished:
            raise WildcattingException("Game is over")

        week = game.week

        if not week.is_survey_turn(player):
            raise WildcattingException("Not player's turn")

        return week.get_player_turn(player)

    def _ensure_turn(
        self, game: Game, player: wildcatting.model.Player
    ) -> wildcatting.turn.Turn:
        if game.finished:
            raise WildcattingException("Game is over")

        week = game.week

        if week.is_turn_finished(player):
            raise WildcattingException("Player's turn is finished")

        return week.get_player_turn(player)

    def _encode_game_handle(
        self, game_id: str, player: wildcatting.model.Player, secret: str
    ) -> str:
        handle = GameService.HANDLE_SEP.join((game_id, player.username, secret))
        return base64.b64encode(handle.encode("utf-8")).decode("utf-8")

    def _decode_game_handle(self, game_handle: str) -> list[str]:
        if not isinstance(game_handle, str):
            raise WildcattingException("Invalid handle")

        try:
            game_handle = base64.b64decode(game_handle).decode("utf-8")
        except Exception:
            raise WildcattingException("Malformed handle")

        if not re.match(r"\d+::.+", game_handle):
            raise WildcattingException("Malformed handle")

        return game_handle.split(GameService.HANDLE_SEP, 2)

    def _encode_client_handle(self, game_id: str, client_id: str) -> str:
        handle = GameService.HANDLE_SEP.join((game_id, client_id))
        return base64.b64encode(handle.encode("utf-8")).decode("utf-8")

    def _decode_client_handle(self, client_handle: str) -> list[str]:
        if not isinstance(client_handle, str):
            raise WildcattingException("Invalid handle")

        self.log.debug("Decoding %s", client_handle)
        try:
            client_handle = base64.b64decode(client_handle).decode("utf-8")
        except Exception:
            raise WildcattingException("Malformed handle")
        self.log.debug("Got %s", client_handle)

        if not re.match(r"\d+::.+", client_handle):
            raise WildcattingException("Malformed handle")

        return client_handle.split(GameService.HANDLE_SEP, 1)

    def new_client_handle(self, game_id: str) -> str:
        game = self._games[game_id]
        client_id = game._new_client_id()
        self.log.info("New client handle requested for game %s: %s", game_id, client_id)
        return self._encode_client_handle(game_id, client_id)

    def new(self, width: int, height: int, turn_count: int) -> str:
        if (
            not isinstance(width, int)
            or not isinstance(height, int)
            or not isinstance(turn_count, int)
        ):
            raise WildcattingException("Invalid parameters")

        game_id = str(self._next_game_id)
        self._next_game_id = self._next_game_id + 1

        self._games[game_id] = Game(width, height, turn_count, self._theme)

        return self.new_client_handle(game_id)

    def join(self, client_handle: str, username: str, symbol: str) -> str:
        if not isinstance(client_handle, str):
            raise WildcattingException("Invalid handle")
        if not isinstance(username, str):
            raise WildcattingException("Invalid username")

        game_id, client_id = self._decode_client_handle(client_handle)
        game = self._games[game_id]

        player = wildcatting.model.Player(username, symbol)
        game.add_player(client_id, player)

        handle = self._encode_game_handle(game_id, player, player.secret)

        self.log.debug("%s joined game %s (%s)", player.username, game_id, handle)

        return handle

    def get_client_info(self, client_handle: str) -> dict[str, Any]:
        if not isinstance(client_handle, str):
            raise WildcattingException("Invalid handle")

        game_id, client_id = self._decode_client_handle(client_handle)
        game = self._games[game_id]

        client_info = wildcatting.model.ClientInfo(client_handle, game_id)

        for player in game.get_client_players(client_id):
            handle = self._encode_game_handle(game_id, player, player.secret)
            client_info.add_player_info(player.username, handle, player.symbol)

        return client_info.serialize()

    def survey(self, handle: str, row: int, col: int) -> dict[str, Any]:
        game, player = self._read_handle(handle)
        turn = self._ensure_survey_turn(game, player)

        if turn.surveyed_site:
            raise WildcattingException("Already surveyed this turn")

        field = game.oil_field

        site = field.get_site(row, col)
        if site.surveyed:
            raise WildcattingException("Site is already surveyed")

        site.surveyed = True
        turn.surveyed_site = site

        game.mark_site_updated(player, site)
        game.week.end_survey(player)

        return site.serialize()

    def erect(self, handle: str, row: int, col: int) -> dict[str, Any]:
        game, player = self._read_handle(handle)
        turn = self._ensure_turn(game, player)

        if turn.drilled_site:
            raise WildcattingException("Already drilled this turn")

        field = game.oil_field

        site = field.get_site(row, col)
        well = wildcatting.model.Well(week=game.week.week_num, player=player)
        site.well = well
        game.drill(row, col)
        turn.drilled_site = site
        game.mark_site_updated(player, site)

        return self._make_player_site(site).serialize()

    def get_game_id(self, handle: str) -> str:
        game_id, player_name, secret = self._decode_game_handle(handle)
        return game_id

    def get_week(self, handle: str) -> int:
        game, player = self._read_handle(handle)

        return game.week.week_num

    def start(self, handle: str) -> None:
        game, player = self._read_handle(handle)

        master = game.master
        if player != master:
            raise WildcattingException("Only the game master can start the game")
        game.start()

    def is_started(self, handle: str) -> bool:
        game, _ = self._read_client_handle(handle)
        return game.started

    def is_finished(self, handle: str) -> bool:
        game, _ = self._read_client_handle(handle)
        return game.finished

    def list_players(self, client_handle: str) -> list[str]:
        game, client_id = self._read_client_handle(client_handle)

        players = game.get_players()
        ret = [player.username for player in players]
        return ret

    def drill(self, handle: str, row: int, col: int) -> dict[str, Any]:
        game, player = self._read_handle(handle)
        turn = self._ensure_turn(game, player)

        drilled_site = turn.drilled_site
        if drilled_site and not (drilled_site.row == row and drilled_site.col == col):
            raise WildcattingException("Already drilled somewhere else this turn")

        game.drill(row, col)
        site = game.oil_field.get_site(row, col)
        game.mark_site_updated(player, site)
        assert site.well is not None
        return site.well.serialize()

    def sell(self, handle: str, row: int, col: int) -> int:
        game, player = self._read_handle(handle)

        field = game.oil_field
        site = field.get_site(row, col)
        well = site.well

        if well is None:
            raise WildcattingException("There is no well at this location")

        if well.sold:
            raise WildcattingException("Well has already been sold")

        if well.player.username != player.username:
            raise WildcattingException("Player does not own well")

        price = well.sell()
        well.player.income(price)
        return price

    def end_turn(self, handle: str) -> tuple[None, list[Any]]:
        game, player = self._read_handle(handle)

        game.end_turn(player)

        well_updates = self.get_well_updates(handle)
        return None, well_updates

    def get_players_turn(self, client_handle: str) -> str | None:
        game, client_id = self._read_client_handle(client_handle)

        player = game.week.survey_player
        if player is not None:
            return player.username
        return None

    def get_pending_players(self, client_handle: str) -> list[str]:
        game, client_id = self._read_client_handle(client_handle)

        players = game.week.pending_players

        return [p.username for p in players]

    def get_update(self, client_handle: str) -> dict[str, Any]:
        game, client_id = self._read_client_handle(client_handle)

        week = game.week.week_num
        oil_price = game.oil_price

        current_player = game.week.survey_player
        if current_player is None:
            players_turn = None
        else:
            players_turn = current_player.username

        pending_players = self.get_pending_players(client_handle)
        game_finished = game.finished
        sites = game.pop_updated_sites(client_id)

        update = wildcatting.model.Update(
            week, oil_price, players_turn, pending_players, game_finished, sites
        )
        return update.serialize()

    def get_well_updates(self, handle: str) -> list[dict[str, Any]]:
        game, player = self._read_handle(handle)

        well_updates: list[dict[str, Any]] = []
        field = game.oil_field
        for row in range(field.height):
            for col in range(field.width):
                well = field.get_site(row, col).well
                if (
                    well is not None
                    and well.player is not None
                    and well.player.username == player.username
                ):
                    well_dict: dict[str, Any] = {
                        "row": row,
                        "col": col,
                        "well": well.serialize(),
                    }
                    well_updates.append(well_dict)

        return well_updates

    def _update_player_site(
        self, player_site: wildcatting.model.Site, site: wildcatting.model.Site
    ) -> None:
        player_site.drill_cost = site.drill_cost
        player_site.probability = site.probability
        player_site.well = site.well
        player_site.tax = site.tax
        player_site.surveyed = site.surveyed
        player_site.oil_depth = site.oil_depth

    def _make_player_site(self, site: wildcatting.model.Site) -> wildcatting.model.Site:
        player_site = wildcatting.model.Site(site.row, site.col)
        if site.surveyed:
            self._update_player_site(player_site, site)

        return player_site

    def get_player_site(self, handle: str, row: int, col: int) -> dict[str, Any]:
        game, player = self._read_handle(handle)
        field = game.oil_field
        site = field.get_site(row, col)
        player_site = self._make_player_site(site)

        return player_site.serialize()

    def get_oil_price(self, handle: str) -> float:
        game, player = self._read_handle(handle)
        return game.oil_price

    def get_player_field(self, client_handle: str) -> dict[str, Any]:
        game, player = self._read_client_handle(client_handle)
        field = game.oil_field

        width, height = field.width, field.height
        player_field = wildcatting.model.OilField(width, height)

        game_finished = game.finished

        for row in range(height):
            for col in range(width):
                site = field.get_site(row, col)
                player_site = player_field.get_site(row, col)

                if site.surveyed or game_finished:
                    self._update_player_site(player_site, site)

                if game_finished:
                    reservoir = site.reservoir
                    if reservoir is not None:
                        player_site.oil_depth = reservoir.oil_depth

        return player_field.serialize()

    def get_weekly_summary(self, client_handle: str) -> dict[str, Any]:
        game, client_id = self._read_client_handle(client_handle)

        return wildcatting.model.WeeklySummary.serialize(game.weekly_summary)


class GameProtocol(Protocol):
    def drill(self, handle: str, row: int, col: int) -> dict: ...
    def end_turn(self, handle: str) -> tuple[None, list[Any]]: ...
    def erect(self, handle: str, row: int, col: int) -> dict: ...
    def get_client_info(self, client_handle: str) -> dict: ...
    def get_player_field(self, client_handle: str) -> dict: ...
    def get_player_site(self, handle: str, row: int, col: int) -> dict: ...
    def get_update(self, client_handle: str) -> dict: ...
    def get_weekly_summary(self, client_handle: str) -> dict: ...
    def is_started(self, client_handle: str) -> bool: ...
    def join(self, client_handle: str, username: str, symbol: str) -> str: ...
    def list_players(self, client_handle: str) -> list[str]: ...
    def new(self, width: int, height: int, turn_count: int) -> str: ...
    def new_client_handle(self, game_id: str) -> str: ...
    def sell(self, handle: str, row: int, col: int) -> int: ...
    def start(self, handle: str) -> None: ...
    def survey(self, handle: str, row: int, col: int) -> dict: ...


class SettingProtocol(Protocol):
    def get_setting(self) -> dict: ...


class ServerProtocol(Protocol):
    game: GameProtocol
    setting: SettingProtocol

    def version(self) -> str: ...


class StandaloneServer(BaseService):
    game: GameProtocol
    setting: SettingProtocol

    def __init__(self) -> None:
        theme = DefaultTheme()
        self.admin = AdminService()
        self.game = GameService(theme)
        self.setting = SettingService(theme)


class _XmlRpcGame:
    def __init__(self, proxy: Any) -> None:
        self._p = proxy

    def drill(self, handle: str, row: int, col: int) -> dict:
        return cast(dict, self._p.drill(handle, row, col))

    def end_turn(self, handle: str) -> tuple[None, list[Any]]:
        _u, well_updates = self._p.endTurn(handle)
        return None, list(well_updates)

    def erect(self, handle: str, row: int, col: int) -> dict:
        return cast(dict, self._p.erect(handle, row, col))

    def get_client_info(self, client_handle: str) -> dict:
        return cast(dict, self._p.getClientInfo(client_handle))

    def get_player_field(self, client_handle: str) -> dict:
        return cast(dict, self._p.getPlayerField(client_handle))

    def get_player_site(self, handle: str, row: int, col: int) -> dict:
        return cast(dict, self._p.getPlayerSite(handle, row, col))

    def get_update(self, client_handle: str) -> dict:
        return cast(dict, self._p.getUpdate(client_handle))

    def get_weekly_summary(self, client_handle: str) -> dict:
        return cast(dict, self._p.getWeeklySummary(client_handle))

    def is_started(self, client_handle: str) -> bool:
        return bool(self._p.isStarted(client_handle))

    def join(self, client_handle: str, username: str, symbol: str) -> str:
        return str(self._p.join(client_handle, username, symbol))

    def list_players(self, client_handle: str) -> list[str]:
        return cast(list[str], self._p.listPlayers(client_handle))

    def new(self, width: int, height: int, turn_count: int) -> str:
        return str(self._p.new(width, height, turn_count))

    def new_client_handle(self, game_id: str) -> str:
        return str(self._p.newClientHandle(game_id))

    def sell(self, handle: str, row: int, col: int) -> int:
        return int(self._p.sell(handle, row, col))

    def start(self, handle: str) -> None:
        self._p.start(handle)

    def survey(self, handle: str, row: int, col: int) -> dict:
        return cast(dict, self._p.survey(handle, row, col))


class _XmlRpcSetting:
    def __init__(self, proxy: Any) -> None:
        self._p = proxy

    def get_setting(self) -> dict:
        return cast(dict, self._p.getSetting())


class XmlRpcServer:
    game: GameProtocol
    setting: SettingProtocol

    def __init__(self, proxy: ServerProxy) -> None:
        self.game = _XmlRpcGame(proxy.game)
        self.setting = _XmlRpcSetting(proxy.setting)
        self._proxy = proxy

    def version(self) -> str:
        return str(self._proxy.version())
