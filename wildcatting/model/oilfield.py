from .serialize import Serializable


class OilField(Serializable):
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._width = width
        self._height = height

        self._rows = [[Site(row, col) for col in range(width)] for row in range(height)]

    def week(self, oilPrice, wellTheory, currentWeek):
        for row in self._rows:
            for site in row:
                site.week(oilPrice, wellTheory, currentWeek)

    def get_site(self, row, col):
        assert row < self._height
        assert col < self._width

        site = self._rows[row][col]

        assert site.get_row() == row
        assert site.get_col() == col

        return site

    def set_site(self, row, col, site):
        assert isinstance(site, Site)

        self._rows[row][col] = site

    def get_height(self):
        return self._height

    def get_width(self):
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

    def get_col(self):
        return self._col

    def get_drill_cost(self):
        return self._drillCost

    def set_drill_cost(self, drillCost):
        assert isinstance(drillCost, int)
        self._drillCost = drillCost

    def get_potential_oil_depth(self):
        return self.__potentialOilDepth

    def set_potential_oil_depth(self, potentialOilDepth):
        self.__potentialOilDepth = potentialOilDepth

    def get_probability(self):
        return self._prob

    def set_probability(self, prob):
        assert 0 <= prob <= 100
        self._prob = prob

    def get_well(self):
        return self._well

    def set_well(self, well):
        if well is not None:
            assert isinstance(well, Well)
        self._well = well

    def get_row(self):
        return self._row

    def is_surveyed(self):
        return self._surveyed

    def set_surveyed(self, surveyed):
        assert isinstance(surveyed, bool)
        self._surveyed = surveyed

    def get_oil_depth(self):
        return self._oilDepth

    def set_oil_depth(self, oilDepth):
        self._oilDepth = oilDepth

    def get_tax(self):
        return self._tax

    def set_tax(self, tax):
        assert isinstance(tax, int)
        self._tax = tax

    def get_reservoir(self):
        return self.__reservoir

    def set_reservoir(self, reservoir):
        self.__reservoir = reservoir

    def get_oil_flag(self):
        return self.__oilFlag

    def set_oil_flag(self, oilFlag):
        self.__oilFlag = oilFlag

    def week(self, oilPrice, wellTheory, currentWeek):
        if self._well is not None:
            if self._well.get_output() is not None and not self._well.is_sold():
                output, capacity = wellTheory.week(self, currentWeek)
                self._well.set_output(output)
                self._well.set_capacity(capacity)
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

    def get_player(self):
        return self._player

    def set_player(self, player):
        self._player = player

    def get_week(self):
        return self._week

    def set_week(self, week):
        self._week = week

    def get_drill_depth(self):
        return self._drillDepth

    def set_drill_depth(self, drillDepth):
        self._drillDepth = drillDepth

    def get_initial_output(self):
        return self._initialOutput

    def set_initial_output(self, initialOutput):
        self._initialOutput = initialOutput

    def get_output(self):
        return self._output

    def set_output(self, output):
        self._output = output

    def is_sold(self):
        return self._sold

    def get_initial_cost(self):
        return self._initialCost

    def get_profit_and_loss(self):
        return self._profitAndLoss

    def get_capacity(self):
        return self._capacity

    def set_capacity(self, capacity):
        self._capacity = capacity

    def sell(self):
        self._sold = True
        price = self._initialCost // 2
        self._profitAndLoss += price
        return price

    def drill(self, site, drillIncrement):
        assert 0 <= self._drillDepth <= 10

        oilDepth = None
        reservoir = site.get_reservoir()
        if reservoir is not None:
            oilDepth = reservoir.get_oil_depth()

        drillCost = site.get_drill_cost()

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

            reservoir = site.get_reservoir()
            if reservoir is not None:
                reservoir.pump(output)

            tax = site.get_tax()
            income, expense = self._computeWeeklyPnl(output, oilPrice, tax)

            self._profitAndLoss -= expense
            self._profitAndLoss += income

            if self._player is not None:
                self._player.expense(expense)
                self._player.income(income)
