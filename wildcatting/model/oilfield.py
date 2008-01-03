from serialize import Serializable

import random


class OilField(Serializable):
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._width = width
        self._height = height

        self._rows = [ [ Site(row, col) for col in xrange(width) ]
                       for row in xrange(height) ]

    def week(self, oilPrice):
        for row in self._rows:
            for site in row:
                site.week(oilPrice)

    def getSite(self, row, col):
        assert row < self._height
        assert col < self._width

        site = self._rows[row][col]

        assert site.getRow() == row
        assert site.getCol() == col

        return site

    def setSite(self, row, col, site):
        assert isinstance(site, Site)

        self._rows[row][col] = site

    def getHeight(self):
        return self._height

    def getWidth(self):
        return self._width


class Site(Serializable):
    def __init__(self, row, col):
        assert isinstance(row, int)
        assert isinstance(col, int)

        self._row = row
        self._col = col

        self._prob = 0
        self._oilDepth = None
        self._well = None
        self._drillCost = 0
        self._tax = 0

        self._surveyed = False

    def getCol(self):
        return self._col

    def getDrillCost(self):
        return self._drillCost

    def setDrillCost(self, drillCost):
        assert isinstance(drillCost, int)
        self._drillCost = drillCost

    def getProbability(self):
        return self._prob

    def setProbability(self, prob):
        assert 0 <= prob <= 100
        self._prob = prob

    def getOilDepth(self):
        return self._oilDepth

    def setOilDepth(self, oilDepth):
        assert 1 <= oilDepth <= 10
        self._oilDepth = oilDepth

    def getWell(self):
        return self._well

    def setWell(self, well):
        if well is not None:
            assert isinstance(well, Well)
        self._well = well

    def getRow(self):
        return self._row

    def isSurveyed(self):
        return self._surveyed

    def setSurveyed(self, surveyed):
        assert isinstance(surveyed, bool)
        self._surveyed = surveyed

    def getTax(self):
        return self._tax

    def setTax(self, tax):
        assert isinstance(tax, int)
        self._tax = tax

    def week(self, oilPrice):
        if self._well is not None:
            self._well.week(self, oilPrice)


class Well(Serializable):
    def __init__(self):
        self._drillDepth = 1
        self._output = None
        self._sold = False
        
        self._initialCost = 0
        self._profitAndLoss = 0

    def __cmp__(self, other):
        return cmp(self._turn, other._turn)

    def _generateOutput(self):
        self._output = random.randint(1,250)

    def getPlayer(self):
        return self._player

    def setPlayer(self, player):
        self._player = player

    def getWeek(self):
        return self._week

    def setWeek(self, week):
        self._week = week

    def getDrillDepth(self):
        return self._drillDepth

    def setDrillDepth(self, drillDepth):
        self._drillDepth = drillDepth

    def getOutput(self):
        return self._output

    def setOutput(self, output):
        self._output = output

    def isSold(self):
        return self._sold

    def getInitialCost(self):
        return self._initialCost

    def getProfitAndLoss(self):
        return self._profitAndLoss

    def sell(self):
        self._sold = True
        price = self._initialCost / 2
        self._profitAndLoss += price
        return price

    def drill(self, site, drillIncrement):
        assert 1 <= self._drillDepth <= 12

        oilDepth = site.getOilDepth()
        drillCost = site.getDrillCost()
        
        assert oilDepth == None or self._drillDepth < oilDepth
        
        self._drillDepth += 1

        cost = drillCost * drillIncrement
        self._initialCost += cost
        self._profitAndLoss -= cost

        foundOil = (self._drillDepth == oilDepth)
        if foundOil:
            self._generateOutput()
            
        return foundOil

    def week(self, site, oilPrice):
        if not self._sold:

            if self._output is None:
                output = 0
            else:
                output = self._output
            
            self._profitAndLoss -= site.getTax()
            self._profitAndLoss += int(output * oilPrice)
