from .serialize import Serializable


class OilField(Serializable):
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._width = width
        self._height = height

        self._rows = [[Site(row, col) for col in range(width)] for row in range(height)]

    def tick(self, oilPrice, wellTheory, currentWeek):
        for row in self._rows:
            for site in row:
                site.tick(oilPrice, wellTheory, currentWeek)

    def get_site(self, row, col):
        assert row < self._height
        assert col < self._width

        site = self._rows[row][col]

        assert site.row == row
        assert site.col == col

        return site

    def set_site(self, row, col, site):
        assert isinstance(site, Site)

        self._rows[row][col] = site

    @property
    def height(self):
        return self._height

    @property
    def width(self):
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

    @property
    def col(self):
        return self._col

    @property
    def drill_cost(self):
        return self._drillCost

    @drill_cost.setter
    def drill_cost(self, drillCost):
        assert isinstance(drillCost, int)
        self._drillCost = drillCost

    @property
    def potential_oil_depth(self):
        return self.__potentialOilDepth

    @potential_oil_depth.setter
    def potential_oil_depth(self, potentialOilDepth):
        self.__potentialOilDepth = potentialOilDepth

    @property
    def probability(self):
        return self._prob

    @probability.setter
    def probability(self, prob):
        assert 0 <= prob <= 100
        self._prob = prob

    @property
    def well(self):
        return self._well

    @well.setter
    def well(self, well):
        if well is not None:
            assert isinstance(well, Well)
        self._well = well

    @property
    def row(self):
        return self._row

    @property
    def surveyed(self):
        return self._surveyed

    @surveyed.setter
    def surveyed(self, surveyed):
        assert isinstance(surveyed, bool)
        self._surveyed = surveyed

    @property
    def oil_depth(self):
        return self._oilDepth

    @oil_depth.setter
    def oil_depth(self, oilDepth):
        self._oilDepth = oilDepth

    @property
    def tax(self):
        return self._tax

    @tax.setter
    def tax(self, tax):
        assert isinstance(tax, int)
        self._tax = tax

    @property
    def reservoir(self):
        return self.__reservoir

    @reservoir.setter
    def reservoir(self, reservoir):
        self.__reservoir = reservoir

    @property
    def oil_flag(self):
        return self.__oilFlag

    @oil_flag.setter
    def oil_flag(self, oilFlag):
        self.__oilFlag = oilFlag

    def tick(self, oilPrice, wellTheory, currentWeek):
        if self._well is not None:
            if self._well.output is not None and not self._well.sold:
                output, capacity = wellTheory.tick(self, currentWeek)
                self._well.output = output
                self._well.capacity = capacity
            self._well.tick(self, oilPrice)


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

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, player):
        self._player = player

    @property
    def week(self):
        return self._week

    @week.setter
    def week(self, week):
        self._week = week

    @property
    def drill_depth(self):
        return self._drillDepth

    @drill_depth.setter
    def drill_depth(self, drillDepth):
        self._drillDepth = drillDepth

    @property
    def initial_output(self):
        return self._initialOutput

    @initial_output.setter
    def initial_output(self, initialOutput):
        self._initialOutput = initialOutput

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, output):
        self._output = output

    @property
    def sold(self):
        return self._sold

    @property
    def initial_cost(self):
        return self._initialCost

    @property
    def profit_and_loss(self):
        return self._profitAndLoss

    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, capacity):
        self._capacity = capacity

    def sell(self):
        self._sold = True
        price = self._initialCost // 2
        self._profitAndLoss += price
        return price

    def drill(self, site, drillIncrement):
        assert 0 <= self._drillDepth <= 10

        oilDepth = None
        reservoir = site.reservoir
        if reservoir is not None:
            oilDepth = reservoir.oil_depth

        drillCost = site.drill_cost

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

    def tick(self, site, oilPrice):
        if not self._sold:
            output = self._output if self._output is not None else 0

            reservoir = site.reservoir
            if reservoir is not None:
                reservoir.pump(output)

            tax = site.tax
            income, expense = self._computeWeeklyPnl(output, oilPrice, tax)

            self._profitAndLoss -= expense
            self._profitAndLoss += income

            if self._player is not None:
                self._player.expense(expense)
                self._player.income(income)
