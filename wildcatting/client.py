import curses
import logging
import time

from wildcatting.model import (
    ClientInfo,
    OilField,
    Setting,
    Site,
    Update,
    WeeklySummary,
    Well,
)
from wildcatting.server import ServerProtocol

from .report import WeeklyReport
from .state import UpdateResult, Wildcatting
from .view.playerview import PlayerCountView, PlayerNamesView
from .view.reportview import (
    PregameReportView,
    SurveyorsReportView,
    WeeklyReportView,
    WeeklySummaryView,
)
from .view.wildcattingview import DrillView, WildcattingView


class Client:
    log = logging.getLogger("Wildcatting")
    _server: ServerProtocol

    def __init__(
        self,
        weeks: int,
        game_id: str | None,
        connect_handle: str | None,
        connect_player: tuple[str, str] | None,
    ) -> None:
        self._connect_game_id: str | None = game_id
        self._connect_handle: str | None = connect_handle
        self._connect_players: list[tuple[str, str]] | None = None
        self._weeks: int = weeks

        if connect_player is not None:
            self._connect_players = [connect_player]

        self._client_info: ClientInfo | None = None

        self._wildcatting = Wildcatting()

    def _connect_to_game(self) -> None:
        if self._connect_handle is not None:
            self.log.info("Reconnecting to handle: %s", self._connect_handle)
        else:
            if self._connect_game_id is not None:
                # connecting to an existing game
                self._connect_handle = self._server.game.new_client_handle(
                    self._connect_game_id
                )
            else:
                # creating a new game
                w, h = self._get_available_field_size()
                self._connect_handle = self._server.game.new(w, h, self._weeks)
                self.log.info(
                    "Created a new game with client id: %s", self._connect_handle
                )

            # joining a new game
            assert self._connect_players is not None
            for username, symbol in self._connect_players:
                self._server.game.join(self._connect_handle, username, symbol)

        self._client_info = ClientInfo.deserialize(
            self._server.game.get_client_info(self._connect_handle)
        )

    def _get_current_handle(self) -> str:
        assert self._client_info is not None
        player = self._wildcatting.players_turn
        assert player is not None
        return self._client_info.get_player_handle(player)

    def _run_pre_game(self) -> None:
        assert self._client_info is not None
        game_id = self._client_info.game_id
        handle = self._client_info.client_handle

        self.log.info(self._client_info._players)

        while not self._server.game.is_started(handle):
            players = self._server.game.list_players(handle)
            master = players[0]

            is_master = False
            if self._client_info.has_player(master):
                is_master = True

            report = PregameReportView(self._stdscr, game_id, is_master, players)
            report.display()

            start = report.input()
            if start and is_master:
                master_handle = self._client_info.get_player_handle(master)
                self._server.game.start(master_handle)

    def _get_new_player_field(self) -> None:
        assert self._client_info is not None
        handle = self._client_info.client_handle
        player_field = OilField.deserialize(self._server.game.get_player_field(handle))
        self._wildcatting.player_field = player_field

    def _survey(self, row: int, col: int) -> bool:
        assert self._wildcatting.player_field is not None
        site = self._wildcatting.player_field.get_site(row, col)
        surveyed = site.surveyed
        if not surveyed:
            site = Site.deserialize(
                self._server.game.survey(self._get_current_handle(), row, col)
            )
            self._wildcatting.update_player_field(site)

        report = SurveyorsReportView(self._stdscr, site, surveyed)
        report.display()
        return report.input()

    def _drill_a_well(self, row: int, col: int) -> None:
        site = Site.deserialize(
            self._server.game.erect(self._get_current_handle(), row, col)
        )
        self._wildcatting.update_player_field(site)
        if site.well is None or site.well.output is None:
            self._run_drill(row, col)

    def _run_drill(self, row: int, col: int) -> Site:
        assert self._wildcatting.player_field is not None
        last_stop = False
        site = self._wildcatting.player_field.get_site(row, col)
        drill_view = DrillView(self._stdscr, site, self._setting)
        assert site.well is not None
        while site.well.output is None and site.well.drill_depth < 10:
            drill_view.display()
            action = drill_view.input()
            if action.drill:
                well_update = self._server.game.drill(
                    self._get_current_handle(), row, col
                )
                well = Well.deserialize(well_update)
                site.well = well
                drill_view.display()
            if action.stop:
                last_stop = True
                break

        if site.well.output is None:
            if not last_stop:
                drill_view.set_message("DRY HOLE!")
                drill_view.display()
                time.sleep(3)
        else:
            # extrapolate the site's oil depth rather than hit the
            # server again.  atleast for now.
            site.oil_depth = well.drill_depth

        return site

    def _end_turn(self) -> None:
        assert self._client_info is not None
        player = self._wildcatting.players_turn
        assert player is not None
        handle = self._client_info.get_player_handle(player)
        u, well_updates = self._server.game.end_turn(handle)
        if u is not None:
            update = Update.deserialize(u)
            updated, week_updated = self._wildcatting.update(update)
        else:
            _updated, week_updated = False, False

        assert self._wildcatting.player_field is not None
        for well_dict in well_updates:
            row, col = well_dict["row"], well_dict["col"]
            well = Well.deserialize(well_dict["well"])
            site = self._wildcatting.player_field.get_site(row, col)
            site.well = well

        if week_updated and not self._wildcatting.game_finished:
            self._run_weekly_summary()

    def _run_weekly_report(self) -> None:
        assert self._wildcatting.player_field is not None
        assert self._client_info is not None
        player = self._wildcatting.players_turn
        assert player is not None
        handle = self._client_info.get_player_handle(player)
        symbol = self._client_info.get_player_symbol(player)

        report = WeeklyReport(
            self._wildcatting.player_field,
            player,
            symbol,
            self._wildcatting.week,
            self._setting,
            self._wildcatting.oil_price,
        )
        report_view = WeeklyReportView(
            self._stdscr, report, self._wildcatting.player_field
        )
        report_view.display()

        while True:
            action = report_view.input()
            if action.sell is not None:
                row, col = action.sell
                site = self._wildcatting.player_field.get_site(row, col)
                if site.well is not None and site.well.sold:
                    continue
                self._server.game.sell(handle, row, col)
                site = Site.deserialize(
                    self._server.game.get_player_site(handle, row, col)
                )
                self._wildcatting.update_player_field(site)

                report = WeeklyReport(
                    self._wildcatting.player_field,
                    player,
                    symbol,
                    self._wildcatting.week,
                    self._setting,
                    self._wildcatting.oil_price,
                )

                report_view.set_field(self._wildcatting.player_field)
                report_view.set_report(report)
                report_view.display()
            if action.next_player:
                break

    def _run_weekly_summary(self) -> None:
        assert self._client_info is not None
        report = WeeklySummary.deserialize(
            self._server.game.get_weekly_summary(self._client_info.client_handle)
        )
        weekly_summary_view = WeeklySummaryView(self._stdscr, report)
        weekly_summary_view.display(self._wildcatting.game_finished)

        while not weekly_summary_view.input():
            pass

    def _update_wildcatting(self) -> UpdateResult:
        assert self._client_info is not None
        update = Update.deserialize(
            self._server.game.get_update(self._client_info.client_handle)
        )
        return self._wildcatting.update(update)

    def _is_my_turn(self) -> bool:
        assert self._client_info is not None
        player = self._wildcatting.players_turn
        if player is None:
            return False
        return self._client_info.has_player(player)

    def _get_available_field_size(self) -> tuple[int, int]:
        (h, w) = self._stdscr.getmaxyx()
        available_width = w - WildcattingView.SIDE_PADDING
        available_height = h - WildcattingView.TOP_PADDING
        return available_width, available_height

    def _input_user_names(self, stdscr: curses.window) -> None:
        count_view = PlayerCountView(stdscr)
        count_view.display()

        count = count_view.input()

        names_view = PlayerNamesView(stdscr, count)
        names_view.display()

        self._connect_players = names_view.input()

    def wildcatting(self, stdscr: curses.window) -> None:
        self._stdscr = stdscr

        if self._connect_players is None:
            self._input_user_names(stdscr)

        self._connect_to_game()
        self._run_pre_game()

        self._get_new_player_field()
        self._update_wildcatting()

        # make sure we can fit
        available_width, available_height = self._get_available_field_size()

        player_field = self._wildcatting.player_field
        assert player_field is not None
        too_short = available_height < player_field.height
        too_narrow = available_width < player_field.width
        if too_short or too_narrow:
            w, h = self._stdscr.getmaxyx()
            min_w = player_field.width + WildcattingView.SIDE_PADDING
            min_h = player_field.height + WildcattingView.TOP_PADDING
            raise Exception(f"Console must be at least {min_w}x{min_h} (is {w}x{h})")

        wildcattingView = WildcattingView(
            self._stdscr, self._wildcatting, self._setting
        )
        wildcattingView.display()

        # Measured in deciseconds.  Thanks, curses.
        orig_refresh = refresh = 50

        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.halfdelay(refresh)

        moved = False
        while not self._wildcatting.game_finished:
            c = None
            if self._is_my_turn() and not moved:
                wildcattingView.indicate_turn()
                curses.cbreak()
                c = self._stdscr.getch()
                moved = True

                # redisplay to clear all the turn indication stuff
                wildcattingView.display()

            action = wildcattingView.input(c, refresh)

            if action.survey is not None and self._is_my_turn():
                row, col = action.survey
                drill_a_well = self._survey(row, col)
                if drill_a_well:
                    self._drill_a_well(row, col)
                curses.flushinp()
                self._run_weekly_report()
                self._end_turn()
                updated, week_updated = self._update_wildcatting()
                if week_updated and not self._wildcatting.game_finished:
                    curses.flushinp()
                    self._run_weekly_summary()
                if updated:
                    wildcattingView.display()

                # back to the original refresh interval
                refresh = orig_refresh
                curses.halfdelay(refresh)
                moved = False
                wildcattingView.display()
            elif action.check_for_updates:
                now = time.time()
                updated, week_updated = self._update_wildcatting()
                then = time.time()

                if then - now > refresh:
                    # exponential backoff
                    refresh = refresh * 2
                    self.log.info(
                        "Update took %f seconds, backing off to %f", then - now, refresh
                    )
                    curses.halfdelay(refresh)

                if week_updated and not self._wildcatting.game_finished:
                    curses.flushinp()
                    self._run_weekly_summary()
                if updated:
                    wildcattingView.display()

        self._stdscr.refresh()
        self._get_new_player_field()
        wildcattingView.animate_game_end()
        curses.flushinp()

        curses.curs_set(0)
        while wildcattingView.input().survey is None:
            pass

        self._run_weekly_summary()

    def run(self, server: ServerProtocol) -> None:
        self._server = server
        self._setting = Setting.deserialize(self._server.setting.get_setting())

        try:
            curses.wrapper(self.wildcatting)
        except KeyboardInterrupt:
            self.log.info(f"To reconnect, run with --handle {self._connect_handle}")
            print(f"To reconnect, run with --handle {self._connect_handle}")
            raise
        except Exception as e:
            self.log.error(str(e))
            self.log.debug("Uncaught exception in client: %s", e, exc_info=True)
            if self._connect_handle is not None:
                print(f"To reconnect, run with --handle {self._connect_handle}")
