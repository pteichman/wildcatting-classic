import logging
import random
import curses

from wildcatting.colors import Colors

import wildcatting.model

class Report:
    log = logging.getLogger("Wildcatting")

    def __init__(self, stdscr):
        self._stdscr = stdscr

    def addCentered(self, win, row, text):
        (h, w) = win.getmaxyx()

        col = (w - len(text))/2
        win.addstr(row, col, text)

    def setFGBG(self, win, fg, bg):
        (h, w) = self._win.getmaxyx()
        
        # work around a problem with the MacOS X Terminal - draw the
        # background explicitly by drawing BG on BG "." characters
        win.bkgdset(" ", fg)
        for row in xrange(h):
            win.addstr(row, 0, "." * (w-1), bg)

class WeeklyReport(Report):
    def __init__(self, stdscr, field, player, turns):
        Report.__init__(self, stdscr)

        self._player = player
        self._turns = turns
        self._sites = self._buildSiteDict(field, player)
        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def _buildSiteDict(self, field, player):
        sites = {}
        for y in xrange(field.getHeight()):
            for x in xrange(field.getWidth()):
                site = field.getSite(x, y)
                well = site.getWell()
                if well:
                    if well.getPlayer().getUsername() == player.getUsername():
                        sites[well.getWeek()] = site
        return sites

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()
        (h, w) = self._win.getmaxyx()        
        bkgd = Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN)
        text = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)

        self.setFGBG(self._win, text, bkgd)

        self._win.addstr(0, 0, self._player.getUsername().upper())
        self._win.addstr(0, 36, "WEEK %s" % self._turns)
        self._win.addstr(1, 1, "  X   Y   COST     TAX   INCOME        P&L")

        sumProfitAndLoss = 0
        for turn in xrange(self._turns):
            if turn in self._sites:
                site = self._sites[turn]
                x = site.getCol()
                y = site.getRow()
                well = site.getWell()
                cost = site.getDrillCost()
                tax = site.getTax()
                income = random.randint(0, 142)
                profitAndLoss = random.randint(-75000, 75000)
            else:
                x = y = cost = tax = income = profitAndLoss = 0
            
            well_str = "  %s  %s" % (str(x).rjust(2), str(y).rjust(2))
            well_str += "  $%s   $%s    $%s  $%s" % (str(cost).rjust(4), str(tax).rjust(4), str(income).rjust(4), str(profitAndLoss).rjust(8))
            self._win.addstr(2 + turn, 0, well_str)
            sumProfitAndLoss += profitAndLoss
        
        self._win.addstr(15, 1, "NEXT PLAYER")
        self._win.addstr(15, 35, "$ %s" % str(sumProfitAndLoss).rjust(10))
        self._win.move(15, 0)
        self._win.refresh()

class SurveyorsReport(Report):
    def __init__(self, stdscr, site, surveyed):
        Report.__init__(self, stdscr)

        self._site = site
        self._surveyed = surveyed
        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()

        (h, w) = self._win.getmaxyx()
        coord_str = "X=%s  Y=%s" % (self._site.getCol(), self._site.getRow())
        prob_str = str(self._site.getProbability()).rjust(2) + "%"
        cost_str = "$" + str(self._site.getDrillCost()).rjust(4)
        tax_str = "$" + str(self._site.getTax()).rjust(4)

        bkgd = Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN)
        text = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)

        self.setFGBG(self._win, text, bkgd)

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
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
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

class PregameReport(Report):
    def __init__(self, stdscr, gameId, isMaster, players):
        Report.__init__(self, stdscr)

        self._gameId = gameId
        self._isMaster = isMaster
        self._players = players

        (h,w) = self._stdscr.getmaxyx()
        self._win = self._stdscr.derwin(16, 48, (h-16)/2, (w-48)/2)

    def display(self):
        self._stdscr.clear()
        self._stdscr.refresh()

        (h, w) = self._win.getmaxyx()

        bkgd = Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN)
        text = Colors.get(curses.COLOR_BLACK, curses.COLOR_GREEN)

        self.setFGBG(self._win, text, bkgd)

        self.addCentered(self._win, 1, "PLAYERS: GAME %s" % self._gameId)

        row = 3
        for player in self._players:
            self._win.addstr(row, 2, player)
            row = row + 1

        if self._isMaster:
            self.addCentered(self._win, h-1, "ANY KEY TO START")

        self._win.refresh()

    def input(self):
        (h, w) = self._stdscr.getmaxyx()
        (wh, ww) = self._win.getmaxyx()

        curses.mousemask(curses.ALL_MOUSE_EVENTS)

        try:
            curses.halfdelay(50)
            c = self._win.getch()

            # the docs claim that an exception is thrown if the halfdelay()
            # timeout is hit, but in practice it seems to return -1 instead
            if c == -1:
                return False
        except KeyboardInterrupt:
            raise
        except:
            return False
        finally:
            curses.nocbreak()

        return True

def main(stdscr):
    player = wildcatting.model.Player("bob", "B")
    field = wildcatting.model.OilField(100, 100)

    weeks = random.randint(0,12)
    for week in xrange(weeks):
        if random.random() > 0.5:
            continue
        
        row = random.randint(0, 99)
        col = random.randint(0, 99)
        
        site = wildcatting.model.Site(row, col)
        site.setProbability(random.randint(0, 100))
        site.setDrillCost(random.randint(10, 30))
        site.setTax(random.randint(600, 1000))
        well = wildcatting.model.Well()
        well.setPlayer(player)
        well.setWeek(week)
        site.setWell(well)
        field.setSite(row, col, site)

    report = WeeklyReport(stdscr, field, player, weeks)
    report.display()
    while True:
        pass

if __name__ == "__main__":
    curses.wrapper(main)
