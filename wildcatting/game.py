import random
import math

from wildcatting.exceptions import WildcattingException
import wildcatting.model

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

    def getMinDropoff(self):
        raise "AbstractMethodNotImplemented"

    def getMaxDropoff(self):
        raise "AbstractMethodNotImplemented"

    def getMaxPeaks(self):
        raise "AbstractMethodNotImplemented"

    def getFudge(self):
        raise "AbstractMethodNotImplemented"

    def getLesserPeakFactor(self):
        raise "AbstractMethodNotImplemented"

    def getValueRange(self):
        raise "AbstractMethodNotImplemented"

    def fillSite(self, site):
        raise "AbstractMethodNotImplemented"

class OilFiller(PeakedFiller):
    def getValueRange(self):
        return (0, 100)

    def fillSite(self, site, value):
        site.setProbability(value)

    def getMinDropoff(self):
        return 5

    def getMaxDropoff(self):
        return 20

    def getMaxPeaks(self):
        return 5

    def getFudge(self):
        return 5

    def getLesserPeakFactor(self):
        return 10

class DrillCostFiller(PeakedFiller):
    MAX_DRILL_COST = 50
    
    def getValueRange(self):
        return (1, self.MAX_DRILL_COST)

    def fillSite(self, site, discount):
        site.setDrillCost(self.MAX_DRILL_COST - discount)

    def getMinDropoff(self):
        return 5

    def getMaxDropoff(self):
        return 5

    def getMaxPeaks(self):
        return 5

    def getFudge(self):
        return 0

    def getLesserPeakFactor(self):
        return 10


class TaxFiller:
    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                site.setTax(random.randint(600, 1000))

class Game:
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._players = {}
        self._turn = 0
        
        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller().fill(self._oilField)
        DrillCostFiller().fill(self._oilField)
        TaxFiller().fill(self._oilField)

    def _generateSecret(self, player):
        return "".join([random.choice(("0", "1", "2", "3", "4",
                                       "5", "6", "7", "8", "9",
                                       "A", "B", "C", "D", "E", "F"))
                  for i in xrange(0, 16)])

    def addPlayer(self, player):
        assert isinstance(player, wildcatting.model.Player)

        id = player.getUsername()
        if self._players.has_key(id):
            raise WildcattingException("Player has already joined game: " + id)

        secret = self._generateSecret(player)

        self._players[secret] = player

        return secret

    def getPlayer(self, username, secret):
        assert isinstance(username, str)
        assert isinstance(secret, str)
        
        player = self._players.get(secret)
        if player is None or player.getUsername() != username:
            raise WildcattingException("Invalid login")

        return player

    def getTurn(self):
        return self._turn

    def getOilField(self):
        return self._oilField
