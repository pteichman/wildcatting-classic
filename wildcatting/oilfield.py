import random
import string
import math
import time
import curses

import wildcatting.model

MIN_DROPOFF = 5
MAX_DROPOFF = 20
MAX_PEAKS = 5
FUDGE = 5
LESSER_PEAK_FACTOR = 10

class OilField:
    def __init__(self, width, height):
        model = wildcatting.model.OilField(width, height)
        peaks = self.generatePeaks(model)

        self._fillModel(model, peaks)
        self._model = model
        self._peaks = peaks

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

                d = random.randint(MIN_DROPOFF, MAX_DROPOFF) * minc * minc / math.sqrt(model.getWidth() * model.getHeight())
                prob = int(100 - closest * random.random() * LESSER_PEAK_FACTOR - d) - random.randint(0, FUDGE)
                prob = max(0, prob)
                model.setSite(row, col, wildcatting.model.Site(prob))

    def generatePeaks(self, model):
        peaks = [None]*random.randint(1, MAX_PEAKS)
        for i in xrange(len(peaks)):
            peaks[i] = (random.randint(0, model.getHeight()),
                        random.randint(0, model.getWidth()))
        return peaks

    def getModel(self):
        return self._model

class OilFieldView:
    def __init__(self, model):
        assert isinstance(model, wildcatting.model.OilField)
        self._model = model

    def bracket(self, site):
        p = site.getProbability()
        if p > 95:
            b = 0
        elif p > 85:
            b = 1
        elif p > 70:
            b = 2
        elif p > 55:
            b = 3
        elif p > 35:
            b = 4
        else:
            b = 5
        return b

    def toAnsi(self, site):
        b = self.bracket(site) % 9
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi

    def ansi(self):
        for row in xrange(self._model.getHeight()):
            line = ""
            for col in xrange(self._model.getWidth()):
                line += self.toAnsi(self._model.getSite(row, col))
            print line
