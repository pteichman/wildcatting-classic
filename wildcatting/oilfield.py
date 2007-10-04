import random
import string
import math
import time

SIZE = 40

class Field:
    def __init__(self):
        self._peak = (int(random.random() * SIZE), int(random.random() * SIZE))

        self._field = [0]*SIZE
        for i in xrange(SIZE):
            self._field[i] = [0]*SIZE
            for j in xrange(SIZE):

                # calculate distance from peak
                a = i - self._peak[0]
                b = j - self._peak[1]
                c = math.sqrt(a*a + b*b)
                prob = abs(int(100 - c/2*c/1 - random.random() * 10))
                self._field[i][j] = Site(prob)

    def ansi(self):
        for i in xrange(SIZE):
            line = ""
            for j in xrange(SIZE):
                line += self._field[i][j].ansi() + " "
            print line

class Site:
    def __init__(self, prob):
        self._prob = prob

    def bracket(self):
        return int(self._prob / 10)
    
    def ansi(self):
        b = self.bracket() % 9
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi
