import logging
import curses
import random
import time

from view import OilFieldCursesView, WildcattingView, SurveyorsReportView, \
     PregameReportView, WeeklyReportView, DrillView, WeeklySummaryView, \
     FadeInOilFieldCursesAnimator, PlayerCountView, PlayerNamesView
from report import WeeklyReport
from game import Game
from colors import Colors
from exceptions import WildcattingException

from wildcatting.model import ClientInfo, OilField, Setting, Site, Well, WeeklySummary, Update

class Wildcatting:
    def __init__(self):
        self._playerField = None
        self._week = 0
        self._oilPrice = 0
        self._playersTurn = None
        self._pendingPlayers = []
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

    def getPendingPlayers(self):
        return self._pendingPlayers

    def setPendingPlayers(self, players):
        self._pendingPlayers = players

    def isGameFinished(self):
        return self._gameFinished

    def setGameFinished(self, gameFinished):
        self._gameFinished = gameFinished

    def updatePlayerField(self, site):
        self._playerField.setSite(site.getRow(), site.getCol(), site)

    def update(self, update):
        gameFinished = update.getGameFinished()
        week = update.getWeek()
        playersTurn = update.getPlayersTurn()
        pendingPlayers = update.getPendingPlayers()
        oilPrice = update.getOilPrice()
        sites = update.getSites()

        updated = len(sites) > 0 or week > self._week or oilPrice != self._oilPrice \
                  or playersTurn !=  self._playersTurn or gameFinished
        weekUpdated = week > self._week

        for site in sites:
            self.updatePlayerField(site)

        self._week = week
        self._playersTurn = playersTurn
        self._pendingPlayers = pendingPlayers
        self._gameFinished = gameFinished
        self._oilPrice = oilPrice

        return updated, weekUpdated


class Client:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, weeks, gameId, connectHandle, connectPlayer):
        self._connectGameId = gameId
        self._connectHandle = connectHandle
        self._connectPlayers = None
        self._weeks = weeks

        if connectPlayer is not None:
            self._connectPlayers = [connectPlayer]

        self._clientInfo = None

        self._wildcatting = Wildcatting()

    def _connectToGame(self):
        if self._connectHandle is not None:
            self.log.info("Reconnecting to handle: %s", self._connectHandle)
        elif self._connectGameId is not None:
            # connecting to an existing game
            self._connectHandle = self._server.game.newClient(self._connectGameId)
        else:
            # creating a new game
            w, h = self._getAvailableFieldSize()
            self._connectHandle = self._server.game.new(w, h, self._weeks)
            self.log.info("Created a new game with client id: %s", self._connectHandle)

            # joining a new game
            for (username, symbol) in self._connectPlayers:
                self._server.game.join(self._connectHandle, username, symbol)

        self._clientInfo = ClientInfo.deserialize(self._server.game.getClientInfo(self._connectHandle))

    def _getCurrentHandle(self):
        player = self._wildcatting.getPlayersTurn()
        return self._clientInfo.getPlayerHandle(player)

    def _runPreGame(self):
        gameId = self._clientInfo.getGameId()
        handle = self._clientInfo.getClientHandle()

        while not self._server.game.isStarted(handle):
            players = self._server.game.listPlayers(handle)

            isMaster = False
            for player in players:
                if self._clientInfo.hasPlayer(player):
                    isMaster = True

            report = PregameReportView(self._stdscr, gameId, True, players)
            report.display()

            start = report.input()
            if start and isMaster:
                self._server.game.start(handle)

    def _getNewPlayerField(self):
        handle = self._clientInfo.getClientHandle()
        playerField = OilField.deserialize(self._server.game.getPlayerField(handle))
        self._wildcatting.setPlayerField(playerField)

    def _survey(self, row, col):
        site = self._wildcatting.getPlayerField().getSite(row, col)
        surveyed = site.isSurveyed()
        if not surveyed:
            site = Site.deserialize(self._server.game.survey(self._getCurrentHandle(), row, col))
            self._wildcatting.updatePlayerField(site)

        report = SurveyorsReportView(self._stdscr, site, surveyed)
        report.display()
        return report.input()

    def _drillAWell(self, row, col):
        site = Site.deserialize(self._server.game.erect(self._getCurrentHandle(), row, col))
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
                wellUpdate = self._server.game.drill(self._getCurrentHandle(), row, col)
                well = Well.deserialize(wellUpdate)
                site.setWell(well)
                drillView.display()
            if "stop" in actions:
                break
        
        if site.getWell().getOutput() is None:
            if not "stop" in actions:
                drillView.setMessage("DRY HOLE!")
                drillView.display()
                time.sleep(3)
        else:
            # extrapolate the site's oil depth rather than hit the
            # server again.  atleast for now.
            site.setOilDepth(well.getDrillDepth())

        return site

    def _endTurn(self):
        u, wellUpdates = self._server.game.endTurn(self._clientInfo.getClientHandle(), self._getCurrentHandle())
        update = Update.deserialize(u)
        
        updated, weekUpdated = self._wildcatting.update(update)
        
        for wellDict in wellUpdates:
            row, col = wellDict["row"], wellDict["col"]
            well = Well.deserialize(wellDict["well"])
            site = self._wildcatting.getPlayerField().getSite(row, col)
            site.setWell(well)

        if weekUpdated and not self._wildcatting.isGameFinished():
            self._runWeeklySummary()

    def _runWeeklyReport(self):
        player = self._wildcatting.getPlayersTurn()
        handle = self._clientInfo.getPlayerHandle(player)
        symbol = self._clientInfo.getPlayerSymbol(player)

        report = WeeklyReport(self._wildcatting.getPlayerField(),
                              player, symbol,
                              self._wildcatting.getWeek(), self._setting,
                              self._wildcatting.getOilPrice())
        reportView = WeeklyReportView(self._stdscr, report,
                                      self._wildcatting.getPlayerField())
        reportView.display()

        actions = {}
        while not "nextPlayer" in actions:
            actions = reportView.input()
            if "sell" in actions:
                row, col = actions["sell"]
                site = self._wildcatting.getPlayerField().getSite(row, col)
                if site.getWell().isSold():
                    continue
                self._server.game.sell(handle, row, col)
                site = Site.deserialize(self._server.game.getPlayerSite(handle, row, col))
                self._wildcatting.updatePlayerField(site)

                report = WeeklyReport(self._wildcatting.getPlayerField(),
                                      player, symbol,
                                      self._wildcatting.getWeek(), self._setting,
                                      self._wildcatting.getOilPrice())

                reportView.setField(self._wildcatting.getPlayerField())
                reportView.setReport(report)
                reportView.display()

    def _runWeeklySummary(self):
        report = WeeklySummary.deserialize(self._server.game.getWeeklySummary(self._clientInfo.getClientHandle()))
        weeklySummaryView = WeeklySummaryView(self._stdscr, report)
        weeklySummaryView.display(self._wildcatting.isGameFinished())
        
        actions = {}
        while not "done" in actions:
            actions = weeklySummaryView.input()

    def _updateWildcatting(self):
        update = Update.deserialize(self._server.game.getUpdate(self._clientInfo.getClientHandle()))
        return self._wildcatting.update(update)

    def _isMyTurn(self):
        return self._clientInfo.hasPlayer(self._wildcatting.getPlayersTurn())

    def _getAvailableFieldSize(self):
        (h, w) = self._stdscr.getmaxyx()
        availableWidth = w - WildcattingView.SIDE_PADDING
        availableHeight = h - WildcattingView.TOP_PADDING
        return availableWidth, availableHeight

    def _inputUserNames(self, stdscr):
        view = PlayerCountView(stdscr)
        view.display()

        count = view.input()

        view = PlayerNamesView(stdscr, count)
        view.display()

        self._connectPlayers = view.input()
        
    def wildcatting(self, stdscr):
        self._stdscr = stdscr

        if self._connectPlayers is None:
            self._inputUserNames(stdscr)

        self._connectToGame()
        self._runPreGame()

        self._getNewPlayerField()
        self._updateWildcatting()
        
        # make sure we can fit
        availableWidth, availableHeight = self._getAvailableFieldSize()

        playerField = self._wildcatting.getPlayerField()
        if availableHeight < playerField.getHeight() \
               or availableWidth < playerField.getWidth():
            w, h = self._stdscr.getmaxyx()
            raise Exception("Console must be at least %dx%d (is %dx%d)"
                            % (playerField.getWidth() + WildcattingView.SIDE_PADDING,
                               playerField.getHeight() + WildcattingView.TOP_PADDING,
                               w, h))
            
        self._wildcattingView = wildcattingView = WildcattingView(self._stdscr,
                                                                  self._wildcatting,
                                                                  self._setting)
        wildcattingView.display()

        # Measured in deciseconds.  Thanks, curses.
        origRefresh = refresh = 50

        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.halfdelay(refresh)
        
        moved = False 
        while not self._wildcatting.isGameFinished():
            c = None
            if self._isMyTurn() and not moved:
                wildcattingView.indicateTurn()
                curses.cbreak()
                c = self._stdscr.getch()
                moved = True

                # redisplay to clear all the turn indication stuff
                wildcattingView.display()
            
            actions = wildcattingView.input(c, refresh)

            if "survey" in actions and self._isMyTurn():
                row, col = actions["survey"]
                drillAWell = self._survey(row, col)
                if drillAWell:
                    self._drillAWell(row, col)
                self._runWeeklyReport()
                self._endTurn()
                updated, weekUpdated = self._updateWildcatting()
                if updated:
                    wildcattingView.display()

                # back to the original refresh interval
                refresh = origRefresh
                curses.halfdelay(refresh)
                moved = False
                wildcattingView.display()
            elif "checkForUpdates" in actions:
                now = time.time()
                updated, weekUpdated = self._updateWildcatting()
                then = time.time()

                if then - now > refresh:
                    # exponential backoff
                    refresh = refresh * 2
                    self.log.info("Update took %f seconds, backing off to %f",
                                  then-now, refresh)
                    curses.halfdelay(refresh)
                
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
            self.log.info("To reconnect, run with --handle %s" % self._connectHandle)
            print "To reconnect, run with --handle %s" % self._connectHandle
            raise
        except Exception, e:
            self.log.error(str(e))
            self.log.debug("Uncaught exception in client: %s", e, exc_info=True)
            if self._connectHandle is not None:
                print "To reconnect, run with --handle %s" % self._connectHandle
