from __future__ import annotations

from typing import TYPE_CHECKING

from .player import Player
from .serialize import Serializable

if TYPE_CHECKING:
    from wildcatting.reservoir import Reservoir
    from wildcatting.welltheory import SimpleWellTheory


class OilField(Serializable):
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self._rows: list[list[Site]] = [
            [Site(row, col) for col in range(width)] for row in range(height)
        ]

    def tick(
        self, oilPrice: float, wellTheory: SimpleWellTheory, currentWeek: int
    ) -> None:
        for row in self._rows:
            for site in row:
                site.tick(oilPrice, wellTheory, currentWeek)

    def get_site(self, row: int, col: int) -> Site:
        assert row < self.height
        assert col < self.width

        site = self._rows[row][col]

        assert site.row == row
        assert site.col == col

        return site

    def set_site(self, row: int, col: int, site: Site) -> None:
        self._rows[row][col] = site


class Site(Serializable):
    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col

        self._prob: int = 0
        self._well: Well | None = None
        self._drillCost: int = 0
        self._tax: int = 0
        self._surveyed: bool = False
        self.oil_depth: int | None = None

        ## don't serialize
        self.__reservoir: Reservoir | None = None
        self.__oilFlag: bool = False
        self.__potentialOilDepth: int | None = None

    @property
    def drill_cost(self) -> int:
        return self._drillCost

    @drill_cost.setter
    def drill_cost(self, drillCost: int) -> None:
        self._drillCost = drillCost

    @property
    def potential_oil_depth(self) -> int | None:
        return self.__potentialOilDepth

    @potential_oil_depth.setter
    def potential_oil_depth(self, potentialOilDepth: int | None) -> None:
        self.__potentialOilDepth = potentialOilDepth

    @property
    def probability(self) -> int:
        return self._prob

    @probability.setter
    def probability(self, prob: int) -> None:
        assert 0 <= prob <= 100
        self._prob = prob

    @property
    def well(self) -> Well | None:
        return self._well

    @well.setter
    def well(self, well: Well | None) -> None:
        self._well = well

    @property
    def surveyed(self) -> bool:
        return self._surveyed

    @surveyed.setter
    def surveyed(self, surveyed: bool) -> None:
        self._surveyed = surveyed

    @property
    def tax(self) -> int:
        return self._tax

    @tax.setter
    def tax(self, tax: int) -> None:
        self._tax = tax

    @property
    def reservoir(self) -> Reservoir | None:
        return self.__reservoir

    @reservoir.setter
    def reservoir(self, reservoir: Reservoir | None) -> None:
        self.__reservoir = reservoir

    @property
    def oil_flag(self) -> bool:
        return self.__oilFlag

    @oil_flag.setter
    def oil_flag(self, oilFlag: bool) -> None:
        self.__oilFlag = oilFlag

    def tick(
        self, oilPrice: float, wellTheory: SimpleWellTheory, currentWeek: int
    ) -> None:
        if self._well is not None:
            reservoir = self.__reservoir
            if (
                self._well.output is not None
                and not self._well.sold
                and reservoir is not None
            ):
                output, capacity = wellTheory.tick(self._well, reservoir, currentWeek)
                self._well.output = output
                self._well.capacity = capacity
            self._well.tick(self, oilPrice)


class Well(Serializable):
    def __init__(self, week: int, player: Player) -> None:
        self.week: int = week
        self.drill_depth: int = 0
        self.initial_output: float | None = None
        self.output: float | None = None
        self.sold: bool = False
        self.player: Player = player
        self.initial_cost: int = 0
        self.profit_and_loss: int = 0
        self.capacity: int = 1

    def __lt__(self, other: Well) -> bool:
        return self.week < other.week

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Well) and self.week == other.week

    def __hash__(self) -> int:
        return id(self)

    def sell(self) -> int:
        self.sold = True
        price = self.initial_cost // 2
        self.profit_and_loss += price
        return price

    def drill(self, site: Site, drillIncrement: int) -> tuple[bool, int]:
        assert 0 <= self.drill_depth <= 10

        oilDepth: int | None = None
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
    def _computeWeeklyPnl(output: float, oilPrice: float, tax: int) -> tuple[int, int]:
        income = int(output * oilPrice)
        return income, tax

    def tick(self, site: Site, oilPrice: float) -> None:
        if not self.sold:
            output: float = self.output if self.output is not None else 0

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
