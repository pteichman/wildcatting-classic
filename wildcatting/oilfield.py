import random
import string
import math
import time

import curses

class Field:
    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._peak = (int(random.random() * width), int(random.random() * height))

        self._field = [0]*height
        for i in xrange(height):
            self._field[i] = [0]*width
            for j in xrange(width):

                # calculate distance from peak
                a = i - self._peak[0]
                b = j - self._peak[1]
                c = math.sqrt(a*a + b*b)
                d = 20 * c / math.sqrt(width * height)
                prob = abs(int(100 - d/2*d/2 - random.random() * 10))
                self._field[i][j] = Site(prob)

    def ansi(self):
        for i in xrange(self._height):
            line = ""
            for j in xrange(self._width):
                line += self._field[i][j].ansi() + " "
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
    
    def ansi(self):
        b = self.bracket() % 9
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi

    def color(self):
        b = self.bracket() % 6
        return curses.color_pair(b + 1)

