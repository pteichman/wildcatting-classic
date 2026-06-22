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
from .view import (
    DrillView,
    PlayerCountView,
    PlayerNamesView,
    PregameReportView,
    SurveyorsReportView,
    WeeklyReportView,
    WeeklySummaryView,
    WildcattingView,
)


class Wildcatting:
    def __init__(self):
        self._playerField = None
        self._week = 0
        self._oilPrice = 0
        self._playersTurn = None
        self._pendingPlayers = []
        self._gameFinished = False

    @property
    def player_field(self):
        return self._playerField

    @player_field.setter
    def player_field(self, playerField):
        self._playerField = playerField

    @property
    def week(self):
        return self._week

    @week.setter
    def week(self, week):
        self._week = week

    @property
    def oil_price(self):
        return self._oilPrice

    @oil_price.setter
    def oil_price(self, oilPrice):
        self._oilPrice = oilPrice

    @property
    def players_turn(self):
        return self._playersTurn

    @players_turn.setter
    def players_turn(self, playersTurn):
        self._playersTurn = playersTurn

    @property
    def pending_players(self):
        return self._pendingPlayers

    @pending_players.setter
    def pending_players(self, players):
        self._pendingPlayers = players

    @property
    def game_finished(self):
        return self._gameFinished

    @game_finished.setter
    def game_finished(self, gameFinished):
        self._gameFinished = gameFinished

    def update_player_field(self, site):
        assert self._playerField is not None
        self._playerField.set_site(site.row, site.col, site)

    def update(self, update):
        gameFinished = update.game_finished
        week = update.week
        playersTurn = update.players_turn
        pendingPlayers = update.pending_players
        oilPrice = update.oil_price
        sites = update.sites

        updated = (
            len(sites) > 0
            or week > self._week
            or oilPrice != self._oilPrice
            or playersTurn != self._playersTurn
            or gameFinished
        )
        weekUpdated = week > self._week

        for site in sites:
            self.update_player_field(site)

        self._week = week
        self._playersTurn = playersTurn
        self._pendingPlayers = pendingPlayers
        self._gameFinished = gameFinished
        self._oilPrice = oilPrice

        return updated, weekUpdated


class Client:
    log = logging.getLogger("Wildcatting")
    _server: ServerProtocol

    def __init__(self, weeks, gameId, connectHandle, connectPlayer):
        self._connectGameId = gameId
        self._connectHandle = connectHandle
        self._connectPlayers = None
        self._weeks = weeks

        if connectPlayer is not None:
            self._connectPlayers = [connectPlayer]

        self._clientInfo = None

        self._wildcatting = Wildcatting()

    def _connect_to_game(self):
        if self._connectHandle is not None:
            self.log.info("Reconnecting to handle: %s", self._connectHandle)
        else:
            if self._connectGameId is not None:
                # connecting to an existing game
                self._connectHandle = self._server.game.new_client_handle(
                    self._connectGameId
                )
            else:
                # creating a new game
                w, h = self._get_available_field_size()
                self._connectHandle = self._server.game.new(w, h, self._weeks)
                self.log.info(
                    "Created a new game with client id: %s", self._connectHandle
                )

            # joining a new game
            assert self._connectPlayers is not None
            for username, symbol in self._connectPlayers:
                self._server.game.join(self._connectHandle, username, symbol)

        self._clientInfo = ClientInfo.deserialize(
            self._server.game.get_client_info(self._connectHandle)
        )

    def _get_current_handle(self):
        assert self._clientInfo is not None
        player = self._wildcatting.players_turn
        return self._clientInfo.get_player_handle(player)

    def _run_pre_game(self):
        assert self._clientInfo is not None
        gameId = self._clientInfo.game_id
        handle = self._clientInfo.client_handle

        self.log.info(self._clientInfo._players)

        while not self._server.game.is_started(handle):
            players = self._server.game.list_players(handle)
            master = players[0]

            isMaster = False
            if self._clientInfo.has_player(master):
                isMaster = True

            report = PregameReportView(self._stdscr, gameId, isMaster, players)
            report.display()

            start = report.input()
            if start and isMaster:
                masterHandle = self._clientInfo.get_player_handle(master)
                self._server.game.start(masterHandle)

    def _get_new_player_field(self):
        assert self._clientInfo is not None
        handle = self._clientInfo.client_handle
        playerField = OilField.deserialize(self._server.game.get_player_field(handle))
        self._wildcatting.player_field = playerField

    def _survey(self, row, col):
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

    def _drill_a_well(self, row, col):
        site = Site.deserialize(
            self._server.game.erect(self._get_current_handle(), row, col)
        )
        self._wildcatting.update_player_field(site)
        if site.well.output is None:
            self._run_drill(row, col)

    def _run_drill(self, row, col):
        last_stop = False
        site = self._wildcatting.player_field.get_site(row, col)
        drillView = DrillView(self._stdscr, site, self._setting)
        while (
            site.well.output is None
            and site.well.drill_depth < 10
        ):
            drillView.display()
            action = drillView.input()
            if action.drill:
                wellUpdate = self._server.game.drill(
                    self._get_current_handle(), row, col
                )
                well = Well.deserialize(wellUpdate)
                site.well = well
                drillView.display()
            if action.stop:
                last_stop = True
                break

        if site.well.output is None:
            if not last_stop:
                drillView.set_message("DRY HOLE!")
                drillView.display()
                time.sleep(3)
        else:
            # extrapolate the site's oil depth rather than hit the
            # server again.  atleast for now.
            site.oil_depth = well.drill_depth

        return site

    def _end_turn(self):
        assert self._clientInfo is not None
        player = self._wildcatting.players_turn
        handle = self._clientInfo.get_player_handle(player)
        u, wellUpdates = self._server.game.end_turn(handle)
        if u is not None:
            update = Update.deserialize(u)
            updated, weekUpdated = self._wildcatting.update(update)
        else:
            _updated, weekUpdated = False, False

        for wellDict in wellUpdates:
            row, col = wellDict["row"], wellDict["col"]
            well = Well.deserialize(wellDict["well"])
            site = self._wildcatting.player_field.get_site(row, col)
            site.well = well

        if weekUpdated and not self._wildcatting.game_finished:
            self._run_weekly_summary()

    def _run_weekly_report(self):
        assert self._clientInfo is not None
        player = self._wildcatting.players_turn
        handle = self._clientInfo.get_player_handle(player)
        symbol = self._clientInfo.get_player_symbol(player)

        report = WeeklyReport(
            self._wildcatting.player_field,
            player,
            symbol,
            self._wildcatting.week,
            self._setting,
            self._wildcatting.oil_price,
        )
        reportView = WeeklyReportView(
            self._stdscr, report, self._wildcatting.player_field
        )
        reportView.display()

        while True:
            action = reportView.input()
            if action.sell is not None:
                row, col = action.sell
                site = self._wildcatting.player_field.get_site(row, col)
                if site.well.sold:
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

                reportView.set_field(self._wildcatting.player_field)
                reportView.set_report(report)
                reportView.display()
            if action.next_player:
                break

    def _run_weekly_summary(self):
        assert self._clientInfo is not None
        report = WeeklySummary.deserialize(
            self._server.game.get_weekly_summary(self._clientInfo.client_handle)
        )
        weeklySummaryView = WeeklySummaryView(self._stdscr, report)
        weeklySummaryView.display(self._wildcatting.game_finished)

        while not weeklySummaryView.input():
            pass

    def _update_wildcatting(self):
        assert self._clientInfo is not None
        update = Update.deserialize(
            self._server.game.get_update(self._clientInfo.client_handle)
        )
        return self._wildcatting.update(update)

    def _is_my_turn(self):
        assert self._clientInfo is not None
        return self._clientInfo.has_player(self._wildcatting.players_turn)

    def _get_available_field_size(self):
        (h, w) = self._stdscr.getmaxyx()
        availableWidth = w - WildcattingView.SIDE_PADDING
        availableHeight = h - WildcattingView.TOP_PADDING
        return availableWidth, availableHeight

    def _input_user_names(self, stdscr):
        countView = PlayerCountView(stdscr)
        countView.display()

        count = countView.input()

        namesView = PlayerNamesView(stdscr, count)
        namesView.display()

        self._connectPlayers = namesView.input()

    def wildcatting(self, stdscr):
        self._stdscr = stdscr

        if self._connectPlayers is None:
            self._input_user_names(stdscr)

        self._connect_to_game()
        self._run_pre_game()

        self._get_new_player_field()
        self._update_wildcatting()

        # make sure we can fit
        availableWidth, availableHeight = self._get_available_field_size()

        playerField = self._wildcatting.player_field
        if (
            availableHeight < playerField.height
            or availableWidth < playerField.width
        ):
            w, h = self._stdscr.getmaxyx()
            min_w = playerField.width + WildcattingView.SIDE_PADDING
            min_h = playerField.height + WildcattingView.TOP_PADDING
            raise Exception(f"Console must be at least {min_w}x{min_h} (is {w}x{h})")

        self._wildcattingView = wildcattingView = WildcattingView(
            self._stdscr, self._wildcatting, self._setting
        )
        wildcattingView.display()

        # Measured in deciseconds.  Thanks, curses.
        origRefresh = refresh = 50

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
                drillAWell = self._survey(row, col)
                if drillAWell:
                    self._drill_a_well(row, col)
                curses.flushinp()
                self._run_weekly_report()
                self._end_turn()
                updated, weekUpdated = self._update_wildcatting()
                if weekUpdated and not self._wildcatting.game_finished:
                    curses.flushinp()
                    self._run_weekly_summary()
                if updated:
                    wildcattingView.display()

                # back to the original refresh interval
                refresh = origRefresh
                curses.halfdelay(refresh)
                moved = False
                wildcattingView.display()
            elif action.check_for_updates:
                now = time.time()
                updated, weekUpdated = self._update_wildcatting()
                then = time.time()

                if then - now > refresh:
                    # exponential backoff
                    refresh = refresh * 2
                    self.log.info(
                        "Update took %f seconds, backing off to %f", then - now, refresh
                    )
                    curses.halfdelay(refresh)

                if weekUpdated and not self._wildcatting.game_finished:
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
            self.log.info(f"To reconnect, run with --handle {self._connectHandle}")
            print(f"To reconnect, run with --handle {self._connectHandle}")
            raise
        except Exception as e:
            self.log.error(str(e))
            self.log.debug("Uncaught exception in client: %s", e, exc_info=True)
            if self._connectHandle is not None:
                print(f"To reconnect, run with --handle {self._connectHandle}")
