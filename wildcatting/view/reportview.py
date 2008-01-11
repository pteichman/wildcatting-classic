import logging
import random
import curses

from view import View

from wildcatting.colors import Colors
import wildcatting.model


class WeeklySummaryView(View):
    def __init__(self, stdscr, report):
        View.__init__(self, stdscr)

        self._report = report

        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self, gameFinished=False):
        self._stdscr.clear()
        self._stdscr.refresh()

        fg, bg = self.getGreenFGBG()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "... WILDCATTING ...")
        if not gameFinished:
            self.addCentered(self._win, 3, "WEEK %03s" % self._report.getWeek())
        else:
            self.addCentered(self._win, 3, "FINAL REPORT")
        row = 6
        reportRows = self._report.getReportRows()
        for rowDict in reportRows:
            username = rowDict["username"]
            profitAndLoss = rowDict["profitAndLoss"]
            leader = rowDict["leader"]
            if leader:
                self.addLeft(self._win, row, "*", pad=10)
            self.addLeft(self._win, row, username, pad=12)

            # could be profit, but probably a loss
            loss = "$ %8d" % profitAndLoss

            self.addRight(self._win, row, loss, pad=12)
            
            # support up to 9 or more players
            if len(reportRows) > 5:
                row += 1
            else:
                row += 2

        self._eatAllKeyEvents(self._win)
        self._win.refresh()

    def input(self):
        actions = {}
        c = self._stdscr.getch()
        if c == -1:
            pass
        else:
            actions["done"] = True

        return actions

class WeeklyReportView(View):
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, stdscr, report, field):
        View.__init__(self, stdscr)

        self._report = report
        self._field = field

        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)
        self._colorChooser = wildcatting.view.ProbabilityColorChooser()

        # start cursor on nextPlayer prompt
        self._cursorTurn = None

    def setReport(self, report):
        self._report = report

    def setField(self, field):
        self._field = field

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()
        (h, w) = self._win.getmaxyx()        

        fg, bg = self.getGreenFGBG()
        self.setFGBG(self._win, fg, bg)

        self._win.addstr(0, 0, self._report.getUsername().upper())
        self.addCentered(self._win, 0, "%s PER BARREL" % self._report.getOilPrice())
        self.addRight(self._win, 0, "WEEK %s" % self._report.getWeek())
        self._win.addstr(1, 1, "  X   Y   COST     TAX     INCOME     P&L")

        sumProfitAndLoss = 0
        week = self._report.getWeek()
        reportDict = self._report.getReportDict()
        for turn in xrange(1, week + 1):
            if turn in reportDict:
                rowDict = reportDict[turn]
                row = rowDict["row"]
                col = rowDict["col"]
                site = self._field.getSite(row, col)
                if site.getWell().isSold():
                    symbol = " "
                else:
                    symbol = self._report.getSymbol()
                self._win.addstr(turn + 1, 0, symbol, self._colorChooser.siteColor(site))
            else:
                rowDict = {"row": 0, "col":0, "cost":0, "tax":0, "income":0, "profitAndLoss":0}

            well_str = " %(col)02s %(row)03s   $%(cost)04s    $%(tax)04s   $%(income)04s      $%(profitAndLoss)7s" % rowDict
            self._win.addstr(turn + 1, 1, well_str)
            sumProfitAndLoss += rowDict["profitAndLoss"]

        self._win.addstr(15, 0, " NEXT PLAYER")
        self._win.addstr(15, 35, "$ %s" % str(sumProfitAndLoss).rjust(10))
        self._moveCursor()
        self._eatAllKeyEvents(self._win)
        self._win.refresh()

    def _moveCursor(self):
        if self._cursorTurn is None:
            row = 15
        else:
            row = self._cursorTurn + 1
        self._win.move(row, 0)

    def _input(self):
        actions = {}

        self._moveCursor()
        c = self._stdscr.getch()
        if c == curses.KEY_UP:
            if self._cursorTurn is None:
                self._cursorTurn = self._report.getWeek()
                self._moveCursor()
            elif self._cursorTurn == 1:
                pass
            else:
                self._cursorTurn -= 1
                self._moveCursor()
        elif c == curses.KEY_DOWN:
            if self._cursorTurn is None:
                pass
            elif self._cursorTurn == self._report.getWeek():
                self._cursorTurn = None
                self._moveCursor()
            else:
                self._cursorTurn += 1
                self._moveCursor()
        elif c == ord(" ") or c == ord("\n"):
            if self._cursorTurn is None:
                actions["nextPlayer"] = True
            else:
                report = self._report.getReportDict()
                if report.has_key(self._cursorTurn):
                    rowDict = report[self._cursorTurn]
                    row = rowDict["row"]
                    col = rowDict["col"]
                    actions["sell"] = row, col
           
        self._eatAllKeyEvents(self._win)
        self._win.refresh()

        return actions

    def input(self):
        curses.cbreak()
        try:
            return self._input()
        finally:
            curses.halfdelay(50)


class SurveyorsReportView(View):
    def __init__(self, stdscr, site, surveyed):
        View.__init__(self, stdscr)

        self._site = site
        self._surveyed = surveyed
        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()
        self._eatAllKeyEvents(self._stdscr)

        (h, w) = self._win.getmaxyx()
        coord_str = "X=%s  Y=%s" % (self._site.getCol(), self._site.getRow())
        prob_str = str(self._site.getProbability()).rjust(2) + "%"
        cost_str = "$" + str(self._site.getDrillCost()).rjust(4)
        tax_str = "$" + str(self._site.getTax()).rjust(4)

        fg, bg = self.getGreenFGBG()
        self.setFGBG(self._win, fg, bg)

        self._win.addstr(1, 14, "SURVEYOR'S REPORT")
        self._win.addstr(4, 12, "LOCATION")
        self._win.addstr(4, 24, coord_str)
        self._win.addstr(6, 12, "PROBABILITY OF OIL")
        self._win.addstr(6, 31, prob_str)
        self._win.addstr(8, 12, "COST PER METER")
        self._win.addstr(8, 29, cost_str)
        self._win.addstr(10, 12, "TAXES PER WEEK")
        self._win.addstr(10, 29, tax_str)

        if not self._surveyed:
            self._win.addstr(15, 13, "DRILL A WELL? (Y-N) ")
        else:
            self._win.addstr(15, 16, "PRESS ANY KEY")

        self._win.refresh()

    def input(self):
        (h, w) = self._stdscr.getmaxyx()
        (wh, ww) = self._win.getmaxyx()
        done = False
        cur = 'n'
        self._win.keypad(1)
        self._win.move(15, 30)
        self._win.refresh()
        curses.mousemask(curses.BUTTON1_CLICKED)
        curses.curs_set(1)
        while not done:
            c = self._win.getch()
            if self._surveyed:
                break

            if c == curses.KEY_UP or c == curses.KEY_LEFT:
                cur = 'y'
            elif c == curses.KEY_DOWN or c == curses.KEY_RIGHT:
                cur = 'n'
            elif c == ord('y'):
                cur = 'y'
                done = True
            elif c == ord('n'):
                cur = 'n'
                done = True
            elif (c == ord(' ')) or (c == 10):
                done = True
            elif c == curses.KEY_MOUSE:
                mid, mx, my, mz, bstate = curses.getmouse()
                x = mx - (w-ww)/2
                y = my - (h-wh)/2

                if y == 15 and x == 28:
                    cur = 'y'
                    done = True
                if y == 15 and x == 30:
                    cur = 'n'
                    done = True

            if cur == 'y':
                self._win.move(15, 28)
            else:
                self._win.move(15, 30)

            self._win.refresh()

        return cur == 'y'


class PregameReportView(View):
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr, gameId, isMaster, players):
        View.__init__(self, stdscr)

        self._gameId = gameId
        self._isMaster = isMaster
        self._players = players

        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()

        (h, w) = self._win.getmaxyx()

        fg, bg = self.getGreenFGBG()
        self.setFGBG(self._win, fg, bg)

        self.addCentered(self._win, 1, "PLAYERS: GAME %s" % self._gameId)

        row = 3
        for player in self._players:
            self._win.addstr(row, 2, player)
            row = row + 1

        if self._isMaster:
            self.addCentered(self._win, h-1, "ANY KEY TO START")

        self._eatAllKeyEvents(self._win)
        self._win.refresh()

    def input(self):
        (h, w) = self._stdscr.getmaxyx()
        (wh, ww) = self._win.getmaxyx()

        # We're getting two clicks here somehow, disabling mouse for now
        # curses.mousemask(curses.BUTTON1_DOUBLE_CLICKED)

        try:
            try:
                curses.halfdelay(50)
                c = self._win.getch()

                # the docs claim that an exception is thrown if the halfdelay()
                # timeout is hit, but in practice it seems to return -1 instead
                if c == -1:
                    return False
            except KeyboardInterrupt:
                raise
            except Exception:
                return False
        finally:
            curses.cbreak()

        return True

