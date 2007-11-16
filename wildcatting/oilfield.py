import random
import string
import math
import time
import curses

MIN_DROPOFF = 5
MAX_DROPOFF = 20
MAX_PEAKS = 5
FUDGE = 5
LESSER_PEAK_FACTOR = 10

class OilField:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.generatePeaks()

        self._field = [0]*height
        for i in xrange(height):
            self._field[i] = [0]*width
            for j in xrange(width):
                # calculate sum of distances from peak
                minc = 99999
                for k in xrange(len(self._peaks)):
                    a = i - self._peaks[k][0]
                    b = j - self._peaks[k][1]
                    c = math.sqrt(a*a + b*b)
                    minc = min(c, minc)
                    if c == minc:
                        closest = k
                d = random.randint(MIN_DROPOFF, MAX_DROPOFF) * minc * minc / math.sqrt(width * height)
                prob = int(100 - closest * random.random() * LESSER_PEAK_FACTOR - d) - random.randint(0, FUDGE)
                prob = max(0, prob)
                self._field[i][j] = Site(i, j, prob)

    def generatePeaks(self):
        self._peaks = [0]*int(random.randint(1,MAX_PEAKS))
        for i in xrange(len(self._peaks)):
            self._peaks[i] = (int(random.random() * self.height), int(random.random() * self.width))

    def ansi(self):
        for i in xrange(self.height):
            line = ""
            for j in xrange(self.width):
                line += self._field[i][j].ansi()
            print line

    def ascii(self):
        for i in xrange(self.height):
            line = ""
            for j in xrange(self.width):
                line += self._field[i][j].ascii()
            print line

    def getSite(self, x, y):
        return self._field[y][x]


class Site:
    def __init__(self, x, y, prob):
        self.x = x
        self.y = y
        self.prob = prob
        self.cost = 12
        self.tax = 615
        self.surveyed = False
        self.rig = " "

    def ansi(self):
        b = self.choice(range(1, 9))
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi

    def ascii(self):
        return self.choice(".+%2YODAUQ#HM")
