import logging
import curses
import random
import time

from view import OilFieldCursesView, WildcattingView, SurveyorsReportView, PregameReportView, WeeklyReportView, DrillView
from view import putch
from report import WeeklyReport
from game import Game
from colors import Colors

from wildcatting.model import OilField, Setting, Site, Well


class Client:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, gameId, handle, username, symbol):
        self._gameId = gameId
        self._handle = handle
        self._username = username
        self._symbol = symbol
        self._turn = 1

    def _refreshPlayerField(self):
        self._playerField = OilField.deserialize(self._server.game.getPlayerField(self._handle))
        self._wildcatting.updateField(self._playerField)

    def _endTurn(self):
        self._server.game.endTurn(self._handle)
        self._turn += 1
        self._wildcatting.updateTurn(self._turn)
        
    def _survey(self, row, col):
        site = self._playerField.getSite(row, col)
        surveyed = site.isSurveyed()
        if not surveyed:
            site = Site.deserialize(self._server.game.survey(self._handle, row, col))

        report = SurveyorsReportView(self._stdscr, site, surveyed)
        report.display()
        yes = report.input()
        return yes

    def _runPreGame(self, gameId, username):
        while not self._server.game.isStarted(self._handle):
            players = self._server.game.listPlayers(self._handle)

            isMaster = False
            if players[0] == username:
                isMaster = True

            report = PregameReportView(self._stdscr, gameId, isMaster, players)
            report.display()

            start = report.input()
            if start and isMaster:
                self._server.game.start(self._handle)

    def _runDrill(self, row, col):
        actions = {}
        site = self._playerField.getSite(row, col)
        drillView = DrillView(self._stdscr, site, self._setting)
        while site.getWell().getDrillDepth() < 10:
            drillView.display()
            actions = drillView.input()
            if "drill" in actions:
                self._server.game.drill(self._handle, site.getRow(), site.getCol())
                site = Site.deserialize(self._server.game.getPlayerSite(self._handle, site.getRow(), site.getCol()))
                drillView.updateSite(site)
                drillView.display()

                if site.getWell().getOutput() is not None:
                    break
            if "stop" in actions:
                break

        if site.getWell().getOutput() is None:
            drillView.setMessage("DRY HOLE!")
            drillView.display()
            time.sleep(3)

    def _runWeeklyReport(self):
        # TODO perhaps we should be retrieving this report from the server
        report = WeeklyReport(self._playerField, self._username, self._symbol, self._turn, self._setting)
        reportView = WeeklyReportView(self._stdscr, report)
        reportView.display()
        reportActions = {}
        while not "endTurn" in reportActions:
            reportActions = reportView.input()
        self._endTurn()
        
    def wildcatting(self, stdscr):
        self._stdscr = stdscr
        
        curses.curs_set(1)
        (h, w) = stdscr.getmaxyx()
        field_w, field_h = w - (WildcattingView.SIDE_BORDER * 2) - 2, h - (WildcattingView.TOP_BORDER * 2) - 3

        if self._handle is not None:
            # connecting to a game already in progress
            self._gameId = self._server.game.getGameId(self._handle)
            self.log.info("Reconnected to game handle: %s" % self._handle)
        elif self._gameId is not None:
            # joining a new game
            self._handle = self._server.game.join(self._gameId, self._username, self._symbol)
            self.log.info("Joined game: %s" % self._gameId)
        else:
            # creating a new game
            self._gameId = self._server.game.new(field_w, field_h, 13)
            self._handle = self._server.game.join(self._gameId, self._username, self._symbol)
            self.log.info("Created a new game: ID is %s" + self._gameId)

        self._runPreGame(self._gameId, self._username)
        
        self._wildcatting = wildcatting = WildcattingView(self._stdscr, field_h, field_w, self._setting)

        self._refreshPlayerField()

        wildcatting.display()
        while True:
            turnOver = False
            actions = wildcatting.input()
            if "survey" in actions:
                row, col = actions["survey"]
                drillAWell = self._survey(row, col)
                self._refreshPlayerField()
                if drillAWell:
                    self._server.game.erect(self._handle, row, col)
                    self._refreshPlayerField()
                    self._runDrill(row, col)
                    self._refreshPlayerField()                    
                self._runWeeklyReport()
                wildcatting.display()
            elif "checkForUpdates" in actions and self._server.game.needsUpdate(self._handle):
                self._refreshPlayerField()
                wildcatting.display()
            elif "weeklyReport" in actions:
                self._runWeeklyReport()

    def run(self, server):
        self._server = server
        self._setting = Setting.deserialize(self._server.setting.getSetting())

        try:
            curses.wrapper(self.wildcatting)
        except KeyboardInterrupt:
            print "To reconnect, run with --handle %s" % self._handle
            self.log.info("To reconnect, run with --handle %s" % self._handle)
            raise
