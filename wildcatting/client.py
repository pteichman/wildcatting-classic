import logging
import curses
import random
import time

from views import OilFieldCursesView, CursesColorChooser, WildcattingView
from views import putch
from report import SurveyorsReport, PregameReport, WeeklyReport
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
        self._turn = 0

    def _refreshPlayerField(self):
        self._playerField = OilField.deserialize(self._server.game.getPlayerField(self._handle))
        self._wildcatting.updateField(self._playerField)

    def _endTurn(self):
        self._server.game.endTurn(self._handle)
        self._turn += 1
        self._wildcatting.updateTurn(self._turn)
        
    def survey(self, x, y):
        site = self._playerField.getSite(y, x)
        surveyed = site.isSurveyed()
        if not surveyed:
            site = Site.deserialize(self._server.game.survey(self._handle, y, x))

        report = SurveyorsReport(self._stdscr, site, surveyed)
        report.display()
        yes = report.input()
        if yes:
            self._server.game.erect(self._handle, y, x)
        self._endTurn()

    def _runPreGame(self, gameId, username):
        while not self._server.game.isStarted(self._handle):
            players = self._server.game.listPlayers(self._handle)

            isMaster = False
            if players[0] == username:
                isMaster = True

            report = PregameReport(self._stdscr, gameId, isMaster, players)
            report.display()

            start = report.input()
            if start and isMaster:
                self._server.game.start(self._handle)

    def wildcatting(self, stdscr):
        self._stdscr = stdscr

        (h,w) = stdscr.getmaxyx()
        border_h = h - 4
        border_w = w - 6
        field_w = border_w - 2
        field_h = border_h - 3

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
            actions = wildcatting.input()

            self.log.info(actions)
            
            checkForUpdates = actions["checkForUpdates"]
            survey = actions["survey"]

            if survey is not None:
                row, col = survey
                self.survey(col, row)
                self._refreshPlayerField()
                wildcatting.display()
            elif checkForUpdates and self._server.game.needsUpdate(self._handle):
                self._refreshPlayerField()
                wildcatting.display()

    def run(self, server):
        self._server = server
        self._setting = Setting.deserialize(self._server.setting.getSetting())

        try:
            curses.wrapper(self.wildcatting)
        except KeyboardInterrupt:
            print "To reconnect, run with --handle %s" % self._handle
            self.log.info("To reconnect, run with --handle %s" % self._handle)
            raise
