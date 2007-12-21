import logging
import random
import math

from wildcatting.exceptions import WildcattingException

import wildcatting.model
import wildcatting.turn

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
                d = random.randint(minDropoff, maxDropoff) * minc * minc / math.sqrt(model.getWidth() * model.getHeight())
                value = int(maxValue - closest * random.random() * lesserPeakFactor - d) - random.randint(0, fudge)
                value = max(minValue, value)

                site = model.getSite(row, col)
                self.fillSite(site, value)

    def _generatePeaks(self, model):
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
        self._theme = theme
    
    def getValueRange(self):
        return (0, 100)

    def fillSite(self, site, value):
        site.setProbability(value)

        for i in xrange(10):
            if(random.randint(0,100) < value/10):
                site.setOilDepth(i + 1)
                break

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
        self._theme = theme
    
    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                site.setTax(random.randint(self._theme.getMinTax(), self._theme.getMaxTax()))

class Game:
    log = logging.getLogger("Wildcatting")

    def __init__(self, width, height, theme):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._theme = theme
        self._players = {}
        self._turn = wildcatting.turn.Turn()
        
        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oilField)
        DrillCostFiller(theme).fill(self._oilField)
        TaxFiller(theme).fill(self._oilField)

    def _generateSecret(self, player):
        return "".join([random.choice(("0", "1", "2", "3", "4",
                                       "5", "6", "7", "8", "9",
                                       "A", "B", "C", "D", "E", "F"))
                  for i in xrange(0, 16)])

    def addPlayer(self, player):
        assert isinstance(player, wildcatting.model.Player)

        # FIXME populate this in some sane way
        self._turn.setPlayer(player)

        id = player.getUsername()
        if self._players.has_key(id):
            raise WildcattingException("Player has already joined game: " + id)

        secret = self._generateSecret(player)
        player.setSecret(secret)

        self._players[id] = player

        return secret

    def getPlayer(self, username, secret):
        assert isinstance(username, str)
        assert isinstance(secret, str)
        
        player = self._players.get(username)
        
        if player is None or player.getSecret() != secret:
            raise WildcattingException("Invalid login")

        return player

    def endTurn(self, player):
        week = self._turn.getWeek()
        self._turn = wildcatting.turn.Turn()
        self._turn.setPlayer(player)
        self._turn.setWeek(week)

    def getTurn(self):
        return self._turn

    def getOilField(self):
        return self._oilField
