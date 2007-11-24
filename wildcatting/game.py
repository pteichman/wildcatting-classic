import random
import math

import wildcatting.model

class OilFieldFiller:
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
                model.setSite(row, col, wildcatting.model.Site(row, col, prob))

    def generatePeaks(self, model):
        peaks = [None]*random.randint(1, self.MAX_PEAKS)
        for i in xrange(len(peaks)):
            peaks[i] = (random.randint(0, model.getHeight()),
                        random.randint(0, model.getWidth()))
        return peaks

class Game:
    def __init__(self, width, height):
        self._oilField = wildcatting.model.OilField(width, height)
        OilFieldFiller().fill(self._oilField)

    def getOilField(self):
        return self._oilField
