
from .serialize import Serializable


class OilField(Serializable):
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._width = width
        self._height = height

        self._rows = [ [ Site(row, col) for col in range(width) ]
                       for row in range(height) ]

    def week(self, oilPrice, wellTheory, currentWeek):
        for row in self._rows:
            for site in row:
                site.week(oilPrice, wellTheory, currentWeek)

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
        self._well = None
        self._drillCost = 0
        self._tax = 0
        self._surveyed = False
        self._oilDepth = None

        ## don't serialize
        self.__reservoir = None
        self.__oilFlag = False
        self.__potentialOilDepth = None

    def getCol(self):
        return self._col

    def getDrillCost(self):
        return self._drillCost

    def setDrillCost(self, drillCost):
        assert isinstance(drillCost, int)
        self._drillCost = drillCost

    def getPotentialOilDepth(self):
        return self.__potentialOilDepth

    def setPotentialOilDepth(self, potentialOilDepth):
        self.__potentialOilDepth = potentialOilDepth

    def getProbability(self):
        return self._prob

    def setProbability(self, prob):
        assert 0 <= prob <= 100
        self._prob = prob

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

    def getOilDepth(self):
        return self._oilDepth

    def setOilDepth(self, oilDepth):
        self._oilDepth = oilDepth

    def getTax(self):
        return self._tax

    def setTax(self, tax):
        assert isinstance(tax, int)
        self._tax = tax

    def getReservoir(self):
        return self.__reservoir

    def setReservoir(self, reservoir):
        self.__reservoir = reservoir

    def getOilFlag(self):
        return self.__oilFlag

    def setOilFlag(self, oilFlag):
        self.__oilFlag = oilFlag

    def week(self, oilPrice, wellTheory, currentWeek):
        if self._well is not None:
            if self._well.getOutput() is not None and not self._well.isSold():
                output, capacity = wellTheory.week(self, currentWeek)
                self._well.setOutput(output)
                self._well.setCapacity(capacity)
            self._well.week(self, oilPrice)


class Well(Serializable):
    def __init__(self):
        self._drillDepth = 0
        self._initialOutput = None
        self._output = None
        self._sold = False
        self._player = None
        self._initialCost = 0
        self._profitAndLoss = 0
        self._capacity = 1

    def __lt__(self, other):
        return self._week < other._week

    def __eq__(self, other):
        return self._week == other._week

    def __hash__(self):
        return id(self)

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

    def getInitialOutput(self):
        return self._initialOutput

    def setInitialOutput(self, initialOutput):
        self._initialOutput = initialOutput

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

    def getCapacity(self):
        return self._capacity

    def setCapacity(self, capacity):
        self._capacity = capacity

    def sell(self):
        self._sold = True
        price = self._initialCost // 2
        self._profitAndLoss += price
        return price

    def drill(self, site, drillIncrement):
        assert 0 <= self._drillDepth <= 10

        oilDepth = None
        reservoir = site.getReservoir()
        if reservoir is not None:
            oilDepth = reservoir.getOilDepth()

        drillCost = site.getDrillCost()

        assert oilDepth is None or self._drillDepth < oilDepth

        self._drillDepth += 1

        cost = drillCost * drillIncrement
        self._initialCost += cost
        self._profitAndLoss -= cost

        return self._drillDepth == oilDepth, cost

    @staticmethod
    def _computeWeeklyPnl(output, oilPrice, tax):
        income = int(output * oilPrice)
        return income, tax

    def week(self, site, oilPrice):
        if not self._sold:
            output = self._output if self._output is not None else 0

            reservoir = site.getReservoir()
            if reservoir is not None:
                reservoir.pump(output)

            tax = site.getTax()
            income, expense = self._computeWeeklyPnl(output, oilPrice, tax)

            self._profitAndLoss -= expense
            self._profitAndLoss += income

            self._player.expense(expense)
            self._player.income(income)
