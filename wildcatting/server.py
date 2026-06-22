import base64
import inspect
import logging
import re
from typing import Any, Protocol, cast
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

import wildcatting.model
from wildcatting.exceptions import WildcattingException
from wildcatting.game import Game

from . import version
from .theme import DefaultTheme


def _to_camel_case(name: str) -> str:
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), name)


class TieredXMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, *args, **kwargs):
        kwargs["allow_none"] = True
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    log = logging.getLogger("XMLRPCServer")

    def register_subinstance(self, tier, instance):
        for name, method in inspect.getmembers(instance, inspect.ismethod):
            if not name.startswith("_"):
                self.register_function(method, f"{tier}.{_to_camel_case(name)}")

    def _dispatch(self, *args, **kwargs):
        """Log all Exceptions raised by XML-RPC handlers"""
        try:
            response = SimpleXMLRPCServer._dispatch(self, *args, **kwargs)
        except:
            self.log.debug("XML-RPC Fault", exc_info=True)
            raise
        return response


class AdminService:
    def ping(self):
        return True


class BaseService:
    def echo(self, s):
        return s

    def ping(self):
        return True

    def version(self) -> str:
        return version.VERSION_STRING


class SettingService:
    def __init__(self, theme):
        self._setting = theme.generate_setting()

    def get_setting(self):
        return self._setting.serialize()


class GameService:
    HANDLE_SEP = "::"

    log = logging.getLogger("Wildcatting")

    def __init__(self, theme):
        self._games = {}
        self._nextGameId = 0
        self._theme = theme

    def _get_game(self, gameId):
        if not isinstance(gameId, str):
            raise WildcattingException("Invalid game id")

        game = self._games.get(gameId)
        if game is None:
            raise WildcattingException("Unknown game id: " + gameId)

        return game

    def _read_handle(self, handle):
        if not isinstance(handle, str):
            raise WildcattingException("Invalid handle")

        self.log.debug("Reading handle: %s", handle)
        (gameId, playerName, secret) = self._decode_game_handle(handle)

        game = self._get_game(gameId)
        player = game.get_player(playerName, secret)

        return (game, player)

    def _read_client_handle(self, handle):
        if not isinstance(handle, str):
            raise WildcattingException("Invalid handle")

        (gameId, clientId) = self._decode_client_handle(handle)
        self.log.info("gameId: %s, clientId: %s", gameId, clientId)

        game = self._get_game(gameId)

        return (game, clientId)

    def _ensure_survey_turn(self, game, player):
        if game.is_finished():
            raise WildcattingException("Game is over")

        week = game.get_week()

        if not week.is_survey_turn(player):
            raise WildcattingException("Not player's turn")

        return week.get_player_turn(player)

    def _ensure_turn(self, game, player):
        if game.is_finished():
            raise WildcattingException("Game is over")

        week = game.get_week()

        if week.is_turn_finished(player):
            raise WildcattingException("Player's turn is finished")

        return week.get_player_turn(player)

    def _encode_game_handle(self, gameId, player, secret):
        handle = GameService.HANDLE_SEP.join((gameId, player.get_username(), secret))
        return base64.b64encode(handle.encode("utf-8")).decode("utf-8")

    def _decode_game_handle(self, gameHandle):
        if not isinstance(gameHandle, str):
            raise WildcattingException("Invalid handle")

        try:
            gameHandle = base64.b64decode(gameHandle).decode("utf-8")
        except Exception:
            raise WildcattingException("Malformed handle")

        if not re.match(r"\d+::.+", gameHandle):
            raise WildcattingException("Malformed handle")

        return gameHandle.split(GameService.HANDLE_SEP, 2)

    def _encode_client_handle(self, gameId, clientId):
        handle = GameService.HANDLE_SEP.join((gameId, clientId))
        return base64.b64encode(handle.encode("utf-8")).decode("utf-8")

    def _decode_client_handle(self, clientHandle):
        if not isinstance(clientHandle, str):
            raise WildcattingException("Invalid handle")

        self.log.debug("Decoding %s", clientHandle)
        try:
            clientHandle = base64.b64decode(clientHandle).decode("utf-8")
        except Exception:
            raise WildcattingException("Malformed handle")
        self.log.debug("Got %s", clientHandle)

        if not re.match(r"\d+::.+", clientHandle):
            raise WildcattingException("Malformed handle")

        return clientHandle.split(GameService.HANDLE_SEP, 1)

    def new_client_handle(self, gameId):
        game = self._games[gameId]
        clientId = game._new_client_id()
        self.log.info("New client handle requested for game %s: %s", gameId, clientId)
        return self._encode_client_handle(gameId, clientId)

    def new(self, width, height, turnCount):
        if (
            not isinstance(width, int)
            or not isinstance(height, int)
            or not isinstance(turnCount, int)
        ):
            raise WildcattingException("Invalid parameters")

        gameId = str(self._nextGameId)
        self._nextGameId = self._nextGameId + 1

        self._games[gameId] = Game(width, height, turnCount, self._theme)

        return self.new_client_handle(gameId)

    def join(self, clientHandle, username, symbol):
        if not isinstance(clientHandle, str):
            raise WildcattingException("Invalid handle")
        if not isinstance(username, str):
            raise WildcattingException("Invalid username")

        gameId, clientId = self._decode_client_handle(clientHandle)
        game = self._games[gameId]

        player = wildcatting.model.Player(username, symbol)
        game.add_player(clientId, player)

        handle = self._encode_game_handle(gameId, player, player.get_secret())

        self.log.debug("%s joined game %s (%s)", player.get_username(), gameId, handle)

        return handle

    def get_client_info(self, clientHandle):
        if not isinstance(clientHandle, str):
            raise WildcattingException("Invalid handle")

        gameId, clientId = self._decode_client_handle(clientHandle)
        game = self._games[gameId]

        clientInfo = wildcatting.model.ClientInfo(clientHandle, gameId)

        for player in game.get_client_players(clientId):
            handle = self._encode_game_handle(gameId, player, player.get_secret())
            clientInfo.add_player_info(
                player.get_username(), handle, player.get_symbol()
            )

        return clientInfo.serialize()

    def survey(self, handle, row, col):
        game, player = self._read_handle(handle)
        turn = self._ensure_survey_turn(game, player)

        if turn.get_surveyed_site():
            raise WildcattingException("Already surveyed this turn")

        field = game.get_oil_field()

        site = field.get_site(row, col)
        if site.is_surveyed():
            raise WildcattingException("Site is already surveyed")

        site.set_surveyed(True)
        turn.set_surveyed_site(site)

        game.mark_site_updated(player, site)
        game.get_week().end_survey(player)

        return site.serialize()

    def erect(self, handle, row, col):
        game, player = self._read_handle(handle)
        turn = self._ensure_turn(game, player)

        if turn.get_drilled_site():
            raise WildcattingException("Already drilled this turn")

        field = game.get_oil_field()

        site = field.get_site(row, col)
        well = wildcatting.model.Well()
        well.set_player(player)
        well.set_week(game.get_week().get_week_num())
        site.set_well(well)
        game.drill(row, col)
        turn.set_drilled_site(site)
        game.mark_site_updated(player, site)

        return self._make_player_site(site).serialize()

    def get_game_id(self, handle):
        gameId, playerName, secret = self._decode_game_handle(handle)
        return gameId

    def get_week(self, handle):
        game, player = self._read_handle(handle)

        return game.get_week().get_week_num()

    def start(self, handle):
        game, player = self._read_handle(handle)

        master = game.get_master()
        if player != master:
            raise WildcattingException("Only the game master can start the game")
        game.start()

    def is_started(self, handle):
        game, clientId = self._read_client_handle(handle)
        return game.is_started()

    def is_finished(self, handle):
        game, clientId = self._read_client_handle(handle)
        return game.is_finished()

    def list_players(self, clientHandle):
        game, clientId = self._read_client_handle(clientHandle)

        players = game.get_players()
        ret = [player.get_username() for player in players]
        return ret

    def drill(self, handle, row, col):
        game, player = self._read_handle(handle)
        turn = self._ensure_turn(game, player)

        drilledSite = turn.get_drilled_site()
        if drilledSite and not (
            drilledSite.get_row() == row and drilledSite.get_col() == col
        ):
            raise WildcattingException("Already drilled somewhere else this turn")

        game.drill(row, col)
        site = game.get_oil_field().get_site(row, col)
        game.mark_site_updated(player, site)
        return site.get_well().serialize()

    def sell(self, handle, row, col):
        game, player = self._read_handle(handle)

        field = game.get_oil_field()
        site = field.get_site(row, col)
        well = site.get_well()

        if well is None:
            raise WildcattingException("There is no well at this location")

        if well.is_sold():
            raise WildcattingException("Well has already been sold")

        if well.get_player().get_username() != player.get_username():
            raise WildcattingException("Player does not own well")

        price = well.sell()
        well.get_player().income(price)
        return price

    def end_turn(self, handle):
        game, player = self._read_handle(handle)

        game.end_turn(player)

        wellUpdates = self.get_well_updates(handle)
        return None, wellUpdates

    def get_players_turn(self, clientHandle):
        game, clientId = self._read_client_handle(clientHandle)

        player = game.get_week().get_survey_player()
        if player is not None:
            return player.get_username()

    def get_pending_players(self, clientHandle):
        game, clientId = self._read_client_handle(clientHandle)

        players = game.get_week().get_pending_players()

        return [p.get_username() for p in players]

    def get_update(self, clientHandle):
        game, clientId = self._read_client_handle(clientHandle)

        week = game.get_week().get_week_num()
        oilPrice = game.get_oil_price()

        currentPlayer = game.get_week().get_survey_player()
        if currentPlayer is None:
            playersTurn = None
        else:
            playersTurn = currentPlayer.get_username()

        pendingPlayers = self.get_pending_players(clientHandle)
        gameFinished = game.is_finished()
        sites = game.pop_updated_sites(clientId)

        update = wildcatting.model.Update(
            week, oilPrice, playersTurn, pendingPlayers, gameFinished, sites
        )
        return update.serialize()

    def get_well_updates(self, handle):
        game, player = self._read_handle(handle)

        wellUpdates = []
        field = game.get_oil_field()
        for row in range(field.get_height()):
            for col in range(field.get_width()):
                well = field.get_site(row, col).get_well()
                if (
                    well is not None
                    and well.get_player().get_username() == player.get_username()
                ):
                    wellDict = {"row": row, "col": col, "well": well.serialize()}
                    wellUpdates.append(wellDict)

        return wellUpdates

    def _update_player_site(self, playerSite, site):
        playerSite.set_drill_cost(site.get_drill_cost())
        playerSite.set_probability(site.get_probability())
        playerSite.set_well(site.get_well())
        playerSite.set_tax(site.get_tax())
        playerSite.set_surveyed(site.is_surveyed())
        playerSite.set_oil_depth(site.get_oil_depth())

    def _make_player_site(self, site):
        playerSite = wildcatting.model.Site(site.get_row(), site.get_col())
        if site.is_surveyed():
            self._update_player_site(playerSite, site)

        return playerSite

    def get_player_site(self, handle, row, col):
        game, player = self._read_handle(handle)
        field = game.get_oil_field()
        site = field.get_site(row, col)
        playerSite = self._make_player_site(site)

        return playerSite.serialize()

    def get_oil_price(self, handle):
        game, player = self._read_handle(handle)
        return game.get_oil_price()

    def get_player_field(self, clientHandle):
        game, player = self._read_client_handle(clientHandle)
        field = game.get_oil_field()

        width, height = field.get_width(), field.get_height()
        playerField = wildcatting.model.OilField(width, height)

        gameFinished = game.is_finished()

        for row in range(height):
            for col in range(width):
                site = field.get_site(row, col)
                playerSite = playerField.get_site(row, col)

                if site.is_surveyed() or gameFinished:
                    self._update_player_site(playerSite, site)

                if gameFinished:
                    reservoir = site.get_reservoir()
                    if reservoir is not None:
                        playerSite.set_oil_depth(reservoir.get_oil_depth())

        return playerField.serialize()

    def get_weekly_summary(self, clientHandle):
        game, clientId = self._read_client_handle(clientHandle)

        return wildcatting.model.WeeklySummary.serialize(game.get_weekly_summary())


class GameProtocol(Protocol):
    def drill(self, handle: str, row: int, col: int) -> dict: ...
    def end_turn(self, handle: str) -> tuple[None, list[Any]]: ...
    def erect(self, handle: str, row: int, col: int) -> dict: ...
    def get_client_info(self, clientHandle: str) -> dict: ...
    def get_player_field(self, clientHandle: str) -> dict: ...
    def get_player_site(self, handle: str, row: int, col: int) -> dict: ...
    def get_update(self, clientHandle: str) -> dict: ...
    def get_weekly_summary(self, clientHandle: str) -> dict: ...
    def is_started(self, clientHandle: str) -> bool: ...
    def join(self, clientHandle: str, username: str, symbol: str) -> str: ...
    def list_players(self, clientHandle: str) -> list[str]: ...
    def new(self, width: int, height: int, turnCount: int) -> str: ...
    def new_client_handle(self, gameId: str) -> str: ...
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

    def __init__(self):
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

    def get_client_info(self, clientHandle: str) -> dict:
        return cast(dict, self._p.getClientInfo(clientHandle))

    def get_player_field(self, clientHandle: str) -> dict:
        return cast(dict, self._p.getPlayerField(clientHandle))

    def get_player_site(self, handle: str, row: int, col: int) -> dict:
        return cast(dict, self._p.getPlayerSite(handle, row, col))

    def get_update(self, clientHandle: str) -> dict:
        return cast(dict, self._p.getUpdate(clientHandle))

    def get_weekly_summary(self, clientHandle: str) -> dict:
        return cast(dict, self._p.getWeeklySummary(clientHandle))

    def is_started(self, clientHandle: str) -> bool:
        return bool(self._p.isStarted(clientHandle))

    def join(self, clientHandle: str, username: str, symbol: str) -> str:
        return str(self._p.join(clientHandle, username, symbol))

    def list_players(self, clientHandle: str) -> list[str]:
        return cast(list[str], self._p.listPlayers(clientHandle))

    def new(self, width: int, height: int, turnCount: int) -> str:
        return str(self._p.new(width, height, turnCount))

    def new_client_handle(self, gameId: str) -> str:
        return str(self._p.newClientHandle(gameId))

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
