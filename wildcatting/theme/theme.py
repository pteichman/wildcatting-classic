import abc
import logging

import wildcatting.model


class Theme(abc.ABC):
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        self._facts = []

    def _load_facts(self, rawFacts):
        facts = []
        for line in rawFacts.split("\n"):
            fact = line.strip()
            if fact == "":
                continue

            if fact[0] == "#":
                continue

            facts.append(fact)

        self._facts = facts

    def generate_setting(self):
        setting = wildcatting.model.Setting()
        setting.set_location(self.get_location())
        setting.set_era(self.get_era())
        setting.set_price_format(self.get_price_format())
        setting.set_facts(self.get_facts())
        setting.set_min_drill_cost(self.get_min_drill_cost())
        setting.set_max_drill_cost(self.get_max_drill_cost())
        setting.set_drill_increment(self.get_drill_increment())
        return setting

    def get_facts(self):
        return self._facts

    def set_facts(self, facts):
        self._facts = facts

    ## literary setting
    @abc.abstractmethod
    def get_location(self): ...

    @abc.abstractmethod
    def get_era(self): ...

    # units
    @abc.abstractmethod
    def get_drill_increment(self): ...

    @abc.abstractmethod
    def get_price_format(self): ...

    ## extraction
    @abc.abstractmethod
    def get_well_theory(self): ...

    @abc.abstractmethod
    def get_mean_site_reserves(self): ...

    ## economics
    @abc.abstractmethod
    def get_min_drill_cost(self): ...

    @abc.abstractmethod
    def get_max_drill_cost(self): ...

    @abc.abstractmethod
    def get_min_tax(self): ...

    @abc.abstractmethod
    def get_max_tax(self): ...

    @abc.abstractmethod
    def get_min_output(self): ...

    @abc.abstractmethod
    def get_max_output(self): ...

    @abc.abstractmethod
    def get_oil_prices(self): ...

    ## oil probability distribution
    @abc.abstractmethod
    def get_oil_min_dropoff(self): ...

    @abc.abstractmethod
    def get_oil_max_dropoff(self): ...

    @abc.abstractmethod
    def get_oil_max_peaks(self): ...

    @abc.abstractmethod
    def get_oil_fudge(self): ...

    @abc.abstractmethod
    def get_oil_lesser_peak_factor(self): ...

    ## drill cost distribution
    @abc.abstractmethod
    def get_drill_cost_min_dropoff(self): ...

    @abc.abstractmethod
    def get_drill_cost_max_dropoff(self): ...

    @abc.abstractmethod
    def get_drill_cost_max_peaks(self): ...

    @abc.abstractmethod
    def get_drill_cost_fudge(self): ...

    @abc.abstractmethod
    def get_drill_cost_lesser_peak_factor(self): ...
