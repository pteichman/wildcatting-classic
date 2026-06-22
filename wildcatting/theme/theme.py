import abc
import logging
from typing import TYPE_CHECKING, Any

import wildcatting.model

if TYPE_CHECKING:
    from wildcatting.welltheory import SimpleWellTheory


class Theme(abc.ABC):
    log = logging.getLogger("Wildcatting")

    def __init__(self) -> None:
        self._facts: list[str] = []

    def _load_facts(self, rawFacts: str) -> None:
        facts = []
        for line in rawFacts.split("\n"):
            fact = line.strip()
            if fact == "":
                continue

            if fact[0] == "#":
                continue

            facts.append(fact)

        self._facts = facts

    def generate_setting(self) -> wildcatting.model.Setting:
        setting = wildcatting.model.Setting()
        setting.location = self.get_location()
        setting.era = self.get_era()
        setting.price_format = self.get_price_format()
        setting.facts = self.facts
        setting.min_drill_cost = self.get_min_drill_cost()
        setting.max_drill_cost = self.get_max_drill_cost()
        setting.drill_increment = self.get_drill_increment()
        return setting

    @property
    def facts(self) -> list[str]:
        return self._facts

    ## literary setting
    @abc.abstractmethod
    def get_location(self) -> str: ...

    @abc.abstractmethod
    def get_era(self) -> str: ...

    # units
    @abc.abstractmethod
    def get_drill_increment(self) -> int: ...

    @abc.abstractmethod
    def get_price_format(self) -> str: ...

    ## extraction
    @abc.abstractmethod
    def get_well_theory(self) -> "SimpleWellTheory": ...

    @abc.abstractmethod
    def get_mean_site_reserves(self) -> int: ...

    ## economics
    @abc.abstractmethod
    def get_min_drill_cost(self) -> int: ...

    @abc.abstractmethod
    def get_max_drill_cost(self) -> int: ...

    @abc.abstractmethod
    def get_min_tax(self) -> int: ...

    @abc.abstractmethod
    def get_max_tax(self) -> int: ...

    @abc.abstractmethod
    def get_min_output(self) -> int: ...

    @abc.abstractmethod
    def get_max_output(self) -> int: ...

    @abc.abstractmethod
    def get_oil_prices(self) -> Any: ...

    ## oil probability distribution
    @abc.abstractmethod
    def get_oil_max_peaks(self) -> int: ...

    @abc.abstractmethod
    def get_oil_fudge(self) -> int: ...

    @abc.abstractmethod
    def get_oil_lesser_peak_factor(self) -> int: ...

    ## drill cost distribution
    @abc.abstractmethod
    def get_drill_cost_max_peaks(self) -> int: ...

    @abc.abstractmethod
    def get_drill_cost_fudge(self) -> int: ...

    @abc.abstractmethod
    def get_drill_cost_lesser_peak_factor(self) -> int: ...
