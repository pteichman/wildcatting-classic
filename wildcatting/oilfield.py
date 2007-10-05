import random
import string
import math
import time
import curses

MIN_DROPOFF = 25
MAX_DROPOFF = 25
MAX_PEAKS = 15
FUDGE = 0
LESSER_PEAK_FACTOR = 0

class Field:
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._generatePeaks()

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
                self._field[i][j] = Site(prob)

    def _generatePeaks(self):
        self._peaks = [0]*int(random.randint(1,MAX_PEAKS))
        for i in xrange(len(self._peaks)):
            self._peaks[i] = (int(random.random() * self._height), int(random.random() * self._width))

    def ansi(self):
        for i in xrange(self._height):
            line = ""
            for j in xrange(self._width):
                line += self._field[i][j].ansi() + " "
            print line

    def ascii(self):
        for i in xrange(self._height):
            line = ""
            for j in xrange(self._width):
                line += self._field[i][j].ascii() + ""
            print line

    def curses(self, win):
        for i in xrange(self._height-1):
            for j in xrange(self._width-2):
                win.addch(i, j, ord("O"), self._field[i][j].color())
        win.refresh()

class Site:
    def __init__(self, prob):
        self._prob = prob

    def bracket(self):
        p = self._prob
        if (p > 95):
            b = 0
        elif (p > 85):
            b = 1
        elif (p > 70):
            b = 2
        elif (p > 55):
            b = 3
        elif (p > 35):
            b = 4
        else:
            b = 5
        return b 

    def choice(self, seq):
        p = self._prob
        if p == 100:
            return seq[-1]
        return seq[int(p / 100. * len(seq))]
    
    def ansi(self):
        b = self.choice(range(1, 9))
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi

    def color(self):
        seq = range(0,6)
        seq.reverse()
        b = self.choice(seq)
        return curses.color_pair(b + 1)

    def ascii(self):
        return self.choice(".+%2YODAUQ#HM")

