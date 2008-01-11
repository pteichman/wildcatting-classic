import os
import curses
import random
import logging
import textwrap

from view import View

from wildcatting.colors import Colors
import wildcatting.game
import wildcatting.model


class OilFieldTextView(View):
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

    def toAscii(self, site):
        assert isinstance(site, wildcatting.model.Site)
        b = self.bracket(site)
        return ".x%*&#"[b]

    def ascii(self):
        model = self._model
        for row in xrange(model.getHeight()):
            line = ""
            for col in xrange(model.getWidth()):
                line += self.toAscii(model.getSite(row, col))
            print line

    def toAnsi(self, site):
        b = self.bracket(site) % 9
        ansi = chr(27) + '['+ str(32+b) +'m' + "O"
        return ansi

    def ansi(self):
        model = self._model
        for row in xrange(model.getHeight()):
            line = ""
            for col in xrange(model.getWidth()):
                line += self.toAnsi(model.getSite(row, col))
            print line


class ColorChooser:
    def __init__(self):
        # for mac terminal workarounds - lazy mac check
        self._mac = os.path.exists("/mach_kernel")

        # increasing order of hotness
        self._colors = [
            Colors.get(curses.COLOR_WHITE, curses.COLOR_BLUE),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_CYAN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_GREEN),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_YELLOW),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_MAGENTA),
            Colors.get(curses.COLOR_WHITE, curses.COLOR_RED),
            ]

        self._blankColors = [
            Colors.get(curses.COLOR_BLUE, curses.COLOR_BLUE),
            Colors.get(curses.COLOR_CYAN, curses.COLOR_CYAN),
            Colors.get(curses.COLOR_GREEN, curses.COLOR_GREEN),
            Colors.get(curses.COLOR_YELLOW, curses.COLOR_YELLOW),
            Colors.get(curses.COLOR_MAGENTA, curses.COLOR_MAGENTA),
            Colors.get(curses.COLOR_RED, curses.COLOR_RED),
            ]

    def _chooseColor(self, site, colors):
        return "UnimplementedAbstractMethod"

    def getColors(self):
        return self._colors[:]

    def siteColor(self, site):
        if site is None:
            return Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)

        assert isinstance(site, wildcatting.model.Site)

        return self._chooseColor(site, self._colors)

    def blankColor(self, site):
        if site is None:
            return Colors.get(curses.COLOR_WHITE, curses.COLOR_BLACK)

        assert isinstance(site, wildcatting.model.Site)

        colors = self._colors
        if self._mac:
            colors = self._blankColors
            
        return self._chooseColor(site, colors)


class ProbabilityColorChooser(ColorChooser):
    
    def _chooseColor(self, site, colors):
        p = site.getProbability()
        if p == 100:
            return colors[-1]
        
        return colors[int(p / 100. * len(colors))]


class DrillCostColorChooser(ColorChooser):
    def __init__(self, minDrillCost, maxDrillCost):
        ColorChooser.__init__(self)

        self._minDrillCost = minDrillCost
        self._maxDrillCost = maxDrillCost

    def _chooseColor(self, site, colors):
        drillCost = site.getDrillCost() * 1.0
        costRange = self._maxDrillCost - self._minDrillCost
        idx = int(drillCost / costRange * (len(colors) - 1))

        return colors[idx]


class FadeInOilFieldCursesAnimator:
    def __init__(self, field):
        self._field = field

        self._coords = [(row, col) for row in xrange(field.getHeight())
                        for col in xrange(field.getWidth())]

    def isDone(self):
        return len(self._coords) == 0

    def animate(self):
        row, col = random.choice(self._coords)
        self._coords.remove((row, col))

        site = self._field.getSite(row, col)
        site.setSurveyed(True)


class OilFieldCursesView(View):
    def __init__(self, win, wildcatting_):
        View.__init__(self, win)
        self._win = win
        self._wildcatting = wildcatting_

        self._colorChooser = self._makeColorChooser()
        
    def _makeColorChooser(self):
        raise "UnimplementedAbstractMethod"

    def display(self):
        field = self._wildcatting.getPlayerField()


        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                if site.isSurveyed():
                    self.displaySite(site)

        self._eatAllKeyEvents(self._win)
        self._win.refresh()

    def displaySite(self, site):
        well = site.getWell()
        if well is None:
            # work around an MacOS X terminal problem with
            # displaying blank characters - it doesn't draw
            # the background if the well is " "
            if self._mac:
                symbol = "."
            else:
                symbol = " "
            color = self._colorChooser.blankColor(site)
        else:
            symbol = well.getPlayer().getSymbol()
            color = self._colorChooser.siteColor(site)

        self.putch(self._win, site.getRow(), site.getCol(), ord(symbol), color)

    def animateGameEnd(self):
        animator = FadeInOilFieldCursesAnimator(self._wildcatting.getPlayerField())
        while not animator.isDone():
            animator.animate()
            self.display()
        

class OilFieldProbabilityView(OilFieldCursesView):

    def _makeColorChooser(self):
        return ProbabilityColorChooser()

    def getKeyLabel(self):
        return "PROBABILITY"


class OilFieldDrillCostView(OilFieldCursesView):
    def __init__(self, win, wildcatting_, minDrillCost, maxDrillCost):
        self._minDrillCost = minDrillCost
        self._maxDrillCost = maxDrillCost
        
        OilFieldCursesView.__init__(self, win, wildcatting_)

    def getKeyLabel(self):
        return "DRILL COST"

    def _makeColorChooser(self):
        return DrillCostColorChooser(self._minDrillCost, self._maxDrillCost)

