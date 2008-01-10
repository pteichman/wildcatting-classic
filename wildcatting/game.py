import logging
import random
import math

from wildcatting.exceptions import WildcattingException

import wildcatting.model
import wildcatting.turn

from oilprices import GaussianPrices
from theme import DefaultTheme, Theme


class PeakedFiller:

    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)
        peaks = self._generatePeaks(field)
        self._fillModel(field, peaks)

    def _fillModel(self, model, peaks):
        for row in xrange(model.getHeight()):
            for col in xrange(model.getWidth()):
                # calculate sum of distances from peak
                minc = 99999
                for p in xrange(len(peaks)):
                    (y, x) = peaks[p]

                    a = row - y
                    b = col - x
                    c = math.sqrt(a*a + b*b)
                    minc = min(c, minc)
                    if c == minc:
                        closest = p

                minValue, maxValue = self.getValueRange()
                minDropoff = self.getMinDropoff()
                maxDropoff = self.getMaxDropoff()
                lesserPeakFactor = self.getLesserPeakFactor()
                fudge = self.getFudge()
                d = (minc + random.random() * fudge) / math.sqrt(model.getWidth() * model.getHeight())
                e = max(0.001, d)
                f = 1 - max(min((math.log(e) + 3) / 3, 1.0), 0)
                peakHeight = maxValue - minValue
                value = int(f * peakHeight - closest * random.random() * lesserPeakFactor)
                value = max(minValue, value)
                value = min(maxValue, value)

                site = model.getSite(row, col)
                self.fillSite(site, value)

    def _generatePeaks(self, model):
        minValue, maxValue = self.getValueRange()        
        maxPeaks = self.getMaxPeaks()
        peaks = [None]*random.randint(1, maxPeaks)
        for i in xrange(len(peaks)):
            peaks[i] = (random.randint(0, model.getHeight()),
                        random.randint(0, model.getWidth()))
        return peaks

    def getValueRange(self):
        raise "AbstractMethodNotImplemented"

    def fillSite(self, site):
        raise "AbstractMethodNotImplemented"


class OilFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme
    
    def getValueRange(self):
        return (10, 100)

    def fillSite(self, site, value):
        site.setProbability(value)

        r = random.randint(0, 100)
        if (r < value):
            site.setOilDepth(int((1.0 - (r / 100.0)) * 9 + 1))

    def getMinDropoff(self):
        return self._theme.getOilMinDropoff()
    
    def getMaxDropoff(self):
        return self._theme.getOilMaxDropoff()
    
    def getMaxPeaks(self):
        return self._theme.getOilMaxPeaks()
    
    def getFudge(self):
        return self._theme.getOilFudge()
    
    def getLesserPeakFactor(self):
        return self._theme.getOilLesserPeakFactor()


class DrillCostFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme
    
    def getValueRange(self):
        return (self._theme.getMinDrillCost(), self._theme.getMaxDrillCost())

    def fillSite(self, site, discount):
        site.setDrillCost(self._theme.getMaxDrillCost() - discount)

    def getMinDropoff(self):
        return self._theme.getDrillCostMinDropoff()
    
    def getMaxDropoff(self):
        return self._theme.getDrillCostMaxDropoff()
    
    def getMaxPeaks(self):
        return self._theme.getDrillCostMaxPeaks()
    
    def getFudge(self):
        return self._theme.getDrillCostFudge()
    
    def getLesserPeakFactor(self):
        return self._theme.getDrillCostLesserPeakFactor()


class TaxFiller:
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme
    
    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                site.setTax(random.randint(self._theme.getMinTax(), self._theme.getMaxTax()))


class Game:
    log = logging.getLogger("Wildcatting")

    def __init__(self, width, height, turnCount=13, theme=None):
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert isinstance(turnCount, int)

        if theme is None:
            theme = DefaultTheme()

        assert isinstance(theme, Theme)

        self._turnCount = turnCount
        self._theme = theme
        self._players = {}
        self._playerOrder = []
        self._playerUpdates = {}
        self._turn = None
        self._isStarted = False
        self._isFinished = False

        self._prices = theme.getOilPrices()
        self._updatePrice(self._prices.next())
        
        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oilField)
        DrillCostFiller(theme).fill(self._oilField)
        TaxFiller(theme).fill(self._oilField)

    def _updatePrice(self, price):
        self._oilPrice = price

    def _generateSecret(self, player):
        return "".join([random.choice(("0", "1", "2", "3", "4",
                                       "5", "6", "7", "8", "9",
                                       "A", "B", "C", "D", "E", "F"))
                  for i in xrange(0, 16)])

    def addPlayer(self, player):
        assert isinstance(player, wildcatting.model.Player)

        playerNames = [p.getUsername() for p in self._players.values()]
        if player.getUsername() in playerNames:
            raise WildcattingException("A user named %s has already joined this game" % player.getUsername())

        secret = self._generateSecret(player)
        player.setSecret(secret)

        self._players[secret] = player
        self._playerOrder.append(player)
        self._playerUpdates[player.getUsername()] = []

        return secret

    def getMaster(self):
        if len(self._playerOrder) > 0:
            return self._playerOrder[0]
        return None

    def getPlayer(self, username, secret):
        assert isinstance(username, str)
        assert isinstance(secret, str)

        player = self._players.get(secret)
        
        if player is None or player.getUsername() != username:
            raise WildcattingException("Invalid login")

        return player

    def getPlayers(self):
        # return a copy, since we don't want outside callers to be able
        # to modify the order
        return self._playerOrder[:]

    def start(self):
        self._isStarted = True

        self._turn = wildcatting.turn.Turn()
        self._turn.setPlayer(self._playerOrder[0])
        self._turn.setWeek(1)

    def isStarted(self):
        return self._isStarted

    def _finish(self):
        self._isFinished = True

        players = self._players.values()
        players.sort(lambda a, b: cmp(b.getProfitAndLoss(), a.getProfitAndLoss()))

        playerStrs = ["%s (%d)" % (p.getUsername(), p.getProfitAndLoss())
                      for p in players]

        self.log.info("Game is finished.  Scores: %s", ", ".join(playerStrs))

    def isFinished(self):
        return self._isFinished

    def drill(self, row, col):
        site = self._oilField.getSite(row, col)
        well = site.getWell()
        foundOil = well.drill(site, self._theme.getDrillIncrement())

        if foundOil:
            theory = self._theme.getWellTheory()
            theory.start(well)

        return foundOil

    def sell(self, row, col):
        site = self._oilField.getSite(row, col)
        well = site.getWell()

        cost = site.getDrillCost() * well.getDrillDepth() * self._theme.getDrillIncrement()

        well.setSold(True)

        return cost / 2

    def endTurn(self, player):
        week = self._turn.getWeek()

        curIndex = self._playerOrder.index(player)
        nextPlayer = self._playerOrder[(curIndex + 1) % len(self._playerOrder)]

        self._turn = wildcatting.turn.Turn()

        if curIndex < len(self._playerOrder) - 1:
            nextPlayer = self._playerOrder[curIndex + 1]
        else:
            nextPlayer = self._playerOrder[0]
            week = week + 1
            
            self._updatePrice(self._prices.next())
            self._oilField.week(self._oilPrice, self._theme.getWellTheory(), week)

        self._turn.setPlayer(nextPlayer)
        self._turn.setWeek(week)

        if week > self._turnCount:
            self._finish()

        return week

    def getWeeklySummary(self):
        report = wildcatting.model.WeeklySummary(self._playerOrder, self._turn.getWeek())

        return report

    def markSiteUpdated(self, player, site):
        for updatePlayer in self._playerUpdates:
            if updatePlayer != player.getUsername():
                updateSites = self._playerUpdates[updatePlayer]
                updateSites.append(site)

    def getUpdatedSites(self, player):
        username = player.getUsername()
        updates = self._playerUpdates[username]
        self._playerUpdates[username] = []
        return updates

    def getTurn(self):
        return self._turn

    def getOilPrice(self):
        return self._oilPrice

    def getOilField(self):
        return self._oilField
