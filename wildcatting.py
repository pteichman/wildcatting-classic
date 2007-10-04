#!/usr/bin/python

import random
import string
import math
import time

SIZE = 40

class field:
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
                self._field[i][j] = site(prob)

    def ansi(self):
        for i in xrange(SIZE):
            line = ""
            for j in xrange(SIZE):
                line += self._field[i][j].ansi() + " "
            print line

class site:
    def __init__(self, prob):
        #self._prob = int(random.random() * 100)
        self._prob = prob
    
    def ansi(self):
        bracket = (self._prob / 30) % 9
        ansi = chr(27) + '['+ str(32+bracket) +'m' + "O"
        return ansi

if __name__ == "__main__":
    while 1:
        f = field()
        f.ansi()
        time.sleep(.25)