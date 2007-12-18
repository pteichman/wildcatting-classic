import random
import math

from wildcatting.exceptions import WildcattingException
import wildcatting.model

class OilFiller:
    MIN_DROPOFF = 5
    MAX_DROPOFF = 20
    MAX_PEAKS = 5
    FUDGE = 5
    LESSER_PEAK_FACTOR = 10

    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)
        peaks = self.generatePeaks(field)
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

                d = random.randint(self.MIN_DROPOFF, self.MAX_DROPOFF) * minc * minc / math.sqrt(model.getWidth() * model.getHeight())
                prob = int(100 - closest * random.random() * self.LESSER_PEAK_FACTOR - d) - random.randint(0, self.FUDGE)
                prob = max(0, prob)

                site = model.getSite(row, col)
                site.setProbability(prob)

    def generatePeaks(self, model):
        peaks = [None]*random.randint(1, self.MAX_PEAKS)
        for i in xrange(len(peaks)):
            peaks[i] = (random.randint(0, model.getHeight()),
                        random.randint(0, model.getWidth()))
        return peaks

class TaxFiller:
    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)

                site.setDrillCost(random.randint(10, 30))
                site.setTax(random.randint(600, 1000))

class Game:
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._players = {}
        self._turn = 0
        
        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller().fill(self._oilField)
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
