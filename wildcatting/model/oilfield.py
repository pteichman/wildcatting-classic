from .serialize import Serializable


class OilField(Serializable):
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self.width = width
        self.height = height

        self._rows = [[Site(row, col) for col in range(width)] for row in range(height)]

    def tick(self, oilPrice, wellTheory, currentWeek):
        for row in self._rows:
            for site in row:
                site.tick(oilPrice, wellTheory, currentWeek)

    def get_site(self, row, col):
        assert row < self.height
        assert col < self.width

        site = self._rows[row][col]

        assert site.row == row
        assert site.col == col

        return site

    def set_site(self, row, col, site):
        assert isinstance(site, Site)

        self._rows[row][col] = site


class Site(Serializable):
    def __init__(self, row, col):
        assert isinstance(row, int)
        assert isinstance(col, int)

        self.row = row
        self.col = col

        self._prob = 0
        self._well = None
        self._drillCost = 0
        self._tax = 0
        self._surveyed = False
        self.oil_depth = None

        ## don't serialize
        self.__reservoir = None
        self.__oilFlag = False
        self.__potentialOilDepth = None

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
    def surveyed(self):
        return self._surveyed

    @surveyed.setter
    def surveyed(self, surveyed):
        assert isinstance(surveyed, bool)
        self._surveyed = surveyed

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
        self.week = None
        self.drill_depth = 0
        self.initial_output = None
        self.output = None
        self.sold = False
        self.player = None
        self.initial_cost = 0
        self.profit_and_loss = 0
        self.capacity = 1

    def __lt__(self, other):
        return self.week < other.week

    def __eq__(self, other):
        return self.week == other.week

    def __hash__(self):
        return id(self)

    def sell(self):
        self.sold = True
        price = self.initial_cost // 2
        self.profit_and_loss += price
        return price

    def drill(self, site, drillIncrement):
        assert 0 <= self.drill_depth <= 10

        oilDepth = None
        reservoir = site.reservoir
        if reservoir is not None:
            oilDepth = reservoir.oil_depth

        drillCost = site.drill_cost

        assert oilDepth is None or self.drill_depth < oilDepth

        self.drill_depth += 1

        cost = drillCost * drillIncrement
        self.initial_cost += cost
        self.profit_and_loss -= cost

        return self.drill_depth == oilDepth, cost

    @staticmethod
    def _computeWeeklyPnl(output, oilPrice, tax):
        income = int(output * oilPrice)
        return income, tax

    def tick(self, site, oilPrice):
        if not self.sold:
            output = self.output if self.output is not None else 0

            reservoir = site.reservoir
            if reservoir is not None:
                reservoir.pump(output)

            tax = site.tax
            income, expense = self._computeWeeklyPnl(output, oilPrice, tax)

            self.profit_and_loss -= expense
            self.profit_and_loss += income

            if self.player is not None:
                self.player.expense(expense)
                self.player.income(income)
