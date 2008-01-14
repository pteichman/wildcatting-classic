import logging
import random
import math

from wildcatting.exceptions import WildcattingException

import wildcatting.model
import wildcatting.turn
import wildcatting.week

from oilprices import GaussianPrices
from theme import DefaultTheme, Theme
from reservoir import Reservoir

class Filler:

    def fill(self, field):
        raise "UnimplementedAbstractMethod"


class PeakedFiller(Filler):

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
            site.setOilFlag(True)

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


class PotentialOilDepthFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme
    
    def getValueRange(self):
        return (1, 10)

    def fillSite(self, site, value):
        if site.getOilFlag():
            site.setPotentialOilDepth(11 - value)

    def getMinDropoff(self):
        return 0
    
    def getMaxDropoff(self):
        return 0
    
    def getMaxPeaks(self):
        return 10
    
    def getFudge(self):
        return 0
    
    def getLesserPeakFactor(self):
        return 1


class ReservoirFiller(Filler):
    log = logging.getLogger("Wildcatting")
    def __init__(self, theme):
        assert isinstance(theme, Theme)

        self._theme = theme

        self._reservoirCount = 0
        self._siteCount = 0

    def fill(self, field):
        height, width = field.getHeight(), field.getWidth()
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                if not site.getOilFlag(): continue
                adjacentSites = []
                for (adjacentRow, adjacentCol) in [(row + 1, col), (row, col + 1)]:
                    if adjacentRow >= height or adjacentCol >= width:
                        continue
                        
                    adjacentSite = field.getSite(adjacentRow, adjacentCol)
                    adjacentSites.append(adjacentSite)
                self._fillSite(site, adjacentSites)

        self.log.info("Created %s reservoirs covering %s sites" % (self._reservoirCount, self._siteCount))

    def _getInitialReserves(self):
        reserves = int(max(0.1, random.gauss(1,1)) * self._theme.getMeanSiteReserves())
        return reserves

    def _depthBracket(self, depth):
        if depth is None:
            return -1
        return int(depth * 1.0 / 9 * 6)

    def _fillSite(self, site, adjacentSites):
        initialDepth = site.getPotentialOilDepth()

        for adjacentSite in adjacentSites:
            initialReserves = self._getInitialReserves()
            if self._depthBracket(initialDepth) == self._depthBracket(adjacentSite.getPotentialOilDepth()):
                self._siteCount += 1
                reservoir = site.getReservoir()
                if reservoir is None:
                    self._reservoirCount += 1
                    reservoir = Reservoir(initialDepth, initialReserves)
                    site.setReservoir(reservoir)
                
                reservoir.join(adjacentSite.getPotentialOilDepth(), initialReserves)
                adjacentSite.setReservoir(reservoir)
            else:
                ## only exceptionally plentiful single site reservoirs have enough oil to pump.
                ## this lowers the amount of oil in the world, but keeps things visually sane.
                ## it also makes the surveyors reports optimistic, but that seems in the spirit
                ## of wildcatting?
                if initialReserves > 2 * self._theme.getMeanSiteReserves():
                    self._reservoirCount += 1
                    site.setReservoir(Reservoir(initialDepth, initialReserves))


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
        self._isStarted = False
        self._isFinished = False
        self._weekNum = 0

        self._prices = theme.getOilPrices()
        
        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oilField)
        PotentialOilDepthFiller(theme).fill(self._oilField)
        ReservoirFiller(theme).fill(self._oilField)
        DrillCostFiller(theme).fill(self._oilField)
        TaxFiller(theme).fill(self._oilField)

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
        self._nextWeek()

    def _nextWeek(self):
        self._weekNum = self._weekNum + 1

        price = self._prices.next()
        self._week = wildcatting.week.Week(self._weekNum, self._playerOrder,
                                           price)
        self._oilField.week(price, self._theme.getWellTheory(),
                            self._weekNum)

        if self._weekNum > self._turnCount:
            self._finish()

    def getWeek(self):
        return self._week

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
            theory.start(site)

        return foundOil

    def sell(self, row, col):
        site = self._oilField.getSite(row, col)
        well = site.getWell()

        cost = site.getDrillCost() * well.getDrillDepth() * self._theme.getDrillIncrement()

        well.setSold(True)

        return cost / 2

    def endTurn(self, player):
        self._week.endTurn(player)

        if self._week.isFinished():
            self._nextWeek()

        return self._weekNum

    def getWeeklySummary(self):
        return wildcatting.model.WeeklySummary(self._playerOrder, self._weekNum)

    def markSiteUpdated(self, player, site):
        for updatePlayer in self._playerUpdates:
            if updatePlayer != player.getUsername():
                updateSites = self._playerUpdates[updatePlayer]
                if site not in updateSites:
                    updateSites.append(site)

    def getUpdatedSites(self, player):
        username = player.getUsername()
        updates = self._playerUpdates[username]
        self._playerUpdates[username] = []
        return updates

    def getOilPrice(self):
        return self._week.getPrice()

    def getOilField(self):
        return self._oilField
