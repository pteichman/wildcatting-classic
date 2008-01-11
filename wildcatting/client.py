import logging
import curses
import random
import time

from view import OilFieldCursesView, WildcattingView, SurveyorsReportView, PregameReportView, WeeklyReportView, DrillView, WeeklySummaryView, FadeInOilFieldCursesAnimator
from report import WeeklyReport
from game import Game
from colors import Colors
from exceptions import WildcattingException

from wildcatting.model import OilField, Setting, Site, Well, WeeklySummary

class Wildcatting:
    def __init__(self):
        self._playerField = None
        self._week = 0
        self._oilPrice = 0
        self._playersTurn = None
        self._gameFinished = False
    
    def getPlayerField(self):
        return self._playerField

    def setPlayerField(self, playerField):
        self._playerField = playerField

    def getWeek(self):
        return self._week

    def setWeek(self, week):
        self._week = week

    def getOilPrice(self):
        return self._oilPrice

    def setOilPrice(self, oilPrice):
        self._oilPrice = oilPrice

    def getPlayersTurn(self):
        return self._playersTurn

    def setPlayersTurn(self, playersTurn):
        self._playersTurn = playersTurn

    def isGameFinished(self):
        return self._gameFinished

    def setGameFinished(self, gameFinished):
        self._gameFinished = gameFinished

    def updatePlayerField(self, site):
        self._playerField.setSite(site.getRow(), site.getCol(), site)

    def update(self, updateDict):
        gameFinished = updateDict["gameFinished"]
        week = updateDict["week"]
        playersTurn = updateDict["playersTurn"]
        oilPrice = updateDict["oilPrice"]
        sites = [Site.deserialize(s) for s in updateDict["sites"]]

        updated = len(sites) > 0 or week > self._week or oilPrice != self._oilPrice or playersTurn !=  self._playersTurn or gameFinished
        weekUpdated = week > self._week

        for site in sites:
            self.updatePlayerField(site)

        self._week = week
        self._playersTurn = playersTurn
        self._gameFinished = gameFinished
        self._oilPrice = oilPrice

        return updated, weekUpdated


class Client:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, gameId, handle, username, symbol):
        self._gameId = gameId
        self._handle = handle
        self._username = username
        self._symbol = symbol

        self._wildcatting = Wildcatting()

    def _connectToGame(self):
        if self._handle is not None:
            # connecting to a game already in progress
            self._gameId = self._server.game.getGameId(self._handle)
            self.log.info("Reconnected to game handle: %s", self._handle)
        elif self._gameId is not None:
            # joining a new game
            self._handle = self._server.game.join(self._gameId, self._username, self._symbol)
            self.log.info("Joined game: %s", self._gameId)
            self.log.info("To reconnect, run with --handle %s" % self._handle)
        else:
            # creating a new game
            w, h = self._getAvailableFieldSize()
            self._gameId = self._server.game.new(w, h, 13)
            self._handle = self._server.game.join(self._gameId, self._username, self._symbol)
            self.log.info("Created a new game: ID is %s", self._gameId)
            self.log.info("To reconnect, run with --handle %s" % self._handle)

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

    def _getNewPlayerField(self):
        playerField = OilField.deserialize(self._server.game.getPlayerField(self._handle))
        self._wildcatting.setPlayerField(playerField)

    def _survey(self, row, col):
        site = self._wildcatting.getPlayerField().getSite(row, col)
        surveyed = site.isSurveyed()
        if not surveyed:
            site = Site.deserialize(self._server.game.survey(self._handle, row, col))
            self._wildcatting.updatePlayerField(site)

        report = SurveyorsReportView(self._stdscr, site, surveyed)
        report.display()
        return report.input()

    def _drillAWell(self, row, col):
        site = Site.deserialize(self._server.game.erect(self._handle, row, col))
        self._wildcatting.updatePlayerField(site)
        if site.getWell().getOutput() is None:
            self._runDrill(row, col)
        
    def _runDrill(self, row, col):
        actions = {}
        site = self._wildcatting.getPlayerField().getSite(row, col)
        drillView = DrillView(self._stdscr, site, self._setting)
        while site.getWell().getOutput() is None and site.getWell().getDrillDepth() < 10:
            drillView.display()
            actions = drillView.input()
            if "drill" in actions:
                wellUpdate = self._server.game.drill(self._handle, row, col)
                well = Well.deserialize(wellUpdate)
                site.setWell(well)
                drillView.display()
            if "stop" in actions:
                break
        
        if site.getWell().getOutput() is None and not "stop" in actions:
            drillView.setMessage("DRY HOLE!")
            drillView.display()
            time.sleep(3)

        return site

    def _endTurn(self):
        updateDict, wellUpdates = self._server.game.endTurn(self._handle)
        
        updated, weekUpdated = self._wildcatting.update(updateDict)
        
        for wellDict in wellUpdates:
            row, col = wellDict["row"], wellDict["col"]
            well = Well.deserialize(wellDict["well"])
            site = self._wildcatting.getPlayerField().getSite(row, col)
            site.setWell(well)

        if weekUpdated and not self._wildcatting.isGameFinished():
            self._runWeeklySummary()

    def _runWeeklyReport(self):
        ## FIXME we want to move WeeklyReport generation to the server side.
        ## oil prices and other economic details live there
        report = WeeklyReport(self._wildcatting.getPlayerField(), self._username, self._symbol, self._wildcatting.getWeek(), self._setting, self._wildcatting.getOilPrice())
        reportView = WeeklyReportView(self._stdscr, report, self._wildcatting.getPlayerField())
        reportView.display()
        actions = {}
        while not "nextPlayer" in actions:
            actions = reportView.input()
            if "sell" in actions:
                row, col = actions["sell"]
                site = self._wildcatting.getPlayerField().getSite(row, col)
                if site.getWell().isSold():
                    continue
                self._server.game.sell(self._handle, row, col)
                site = Site.deserialize(self._server.game.getPlayerSite(self._handle, row, col))
                self._wildcatting.updatePlayerField(site)
                ## FIXME we want to move WeeklyReport generation to the server side
                ## oil prices and other economic details live there
                report = WeeklyReport(self._wildcatting.getPlayerField(), self._username, self._symbol, self._wildcatting.getWeek(), self._setting, self._wildcatting.getOilPrice())
                reportView.setField(self._wildcatting.getPlayerField())
                reportView.setReport(report)
                reportView.display()

    def _runWeeklySummary(self):
        report = WeeklySummary.deserialize(self._server.game.getWeeklySummary(self._handle))
        weeklySummaryView = WeeklySummaryView(self._stdscr, report)
        weeklySummaryView.display(self._wildcatting.isGameFinished())
        
        actions = {}
        while not "done" in actions:
            actions = weeklySummaryView.input()

    def _updateWildcatting(self):
        updateDict = self._server.game.getUpdateDict(self._handle)
        return self._wildcatting.update(updateDict)

    def _isMyTurn(self):
        return self._wildcatting.getPlayersTurn() == self._username

    def _getAvailableFieldSize(self):
        (h, w) = self._stdscr.getmaxyx()
        availableWidth = w - WildcattingView.SIDE_PADDING
        availableHeight = h - WildcattingView.TOP_PADDING
        return availableWidth, availableHeight
        
    def wildcatting(self, stdscr):
        self._stdscr = stdscr

        self._connectToGame()
        self._runPreGame(self._gameId, self._username)

        self._getNewPlayerField()
        self._updateWildcatting()
        
        # make sure we can fit
        availableWidth, availableHeight = self._getAvailableFieldSize()
        if availableHeight < self._wildcatting.getPlayerField().getHeight() \
               or availableWidth < self._wildcatting.getPlayerField().getWidth():
            w, h = self._stdscr.getmaxyx()
            raise Exception("Console must be at least %dx%d (is %dx%d)"
                            % (playerField.getWidth() + WildcattingView.SIDE_PADDING,
                               playerField.getHeight() + WildcattingView.TOP_PADDING,
                               w, h))
            
        self._wildcattingView = wildcattingView = WildcattingView(self._stdscr,
                                                                  self._wildcatting,
                                                                  self._setting)
        wildcattingView.display()

        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.halfdelay(50)
        
        moved = False 
        while not self._wildcatting.isGameFinished():
            c = None
            if self._isMyTurn() and not moved:
                wildcattingView.indicateTurn()
                curses.cbreak()
                c = self._stdscr.getch()
                moved = True
            
            actions = wildcattingView.input(c)
                
            if "survey" in actions and self._isMyTurn():
                row, col = actions["survey"]
                drillAWell = self._survey(row, col)
                if drillAWell:
                    self._drillAWell(row, col)
                self._runWeeklyReport()
                self._endTurn()
                curses.halfdelay(50)
                moved = False
                wildcattingView.display()
            elif "checkForUpdates" in actions:
                updated, weekUpdated = self._updateWildcatting()
                if weekUpdated and not self._wildcatting.isGameFinished():
                    self._runWeeklySummary()                    
                if updated:
                    wildcattingView.display()
 
        self._stdscr.refresh()
        self._getNewPlayerField()
        wildcattingView.animateGameEnd()

        curses.curs_set(0)
        actions = {}
        while not "survey" in actions:
            actions = wildcattingView.input()

        self._runWeeklySummary()

    def run(self, server):
        self._server = server
        self._setting = Setting.deserialize(self._server.setting.getSetting())

        try:
            curses.wrapper(self.wildcatting)
        except KeyboardInterrupt:
            self.log.info("To reconnect, run with --handle %s" % self._handle)
            print "To reconnect, run with --handle %s" % self._handle
            raise
        except Exception, e:
            self.log.error(str(e))
            self.log.debug("Uncaught exception in client: %s", e, exc_info=True)
            if self._handle is not None:
                print "To reconnect, run with --handle %s" % self._handle
