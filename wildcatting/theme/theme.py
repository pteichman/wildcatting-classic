import logging

import wildcatting.model


class Theme:
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

    ## themes must implement the following abstract methods

    ## literary setting
    def get_location(self):
        raise NotImplementedError

    def get_era(self):
        raise NotImplementedError

    # units
    def get_drill_increment(self):
        raise NotImplementedError

    def get_price_format(self):
        raise NotImplementedError

    ## extraction
    def get_well_theory(self):
        raise NotImplementedError

    def get_mean_site_reserves(self):
        raise NotImplementedError

    ## economics
    def get_min_drill_cost(self):
        raise NotImplementedError

    def get_max_drill_cost(self):
        raise NotImplementedError

    def get_min_tax(self):
        raise NotImplementedError

    def get_max_tax(self):
        raise NotImplementedError

    def get_min_output(self):
        raise NotImplementedError

    def get_max_output(self):
        raise NotImplementedError

    def get_oil_prices(self):
        raise NotImplementedError

    ## oil probability distribution
    def get_oil_min_dropoff(self):
        raise NotImplementedError

    def get_oil_max_dropoff(self):
        raise NotImplementedError

    def get_oil_max_peaks(self):
        raise NotImplementedError

    def get_oil_fudge(self):
        raise NotImplementedError

    def get_oil_lesser_peak_factor(self):
        raise NotImplementedError

    ## drill cost distribution
    def get_drill_cost_min_dropoff(self):
        raise NotImplementedError

    def get_drill_cost_max_dropoff(self):
        raise NotImplementedError

    def get_drill_cost_max_peaks(self):
        raise NotImplementedError

    def get_drill_cost_fudge(self):
        raise NotImplementedError

    def get_drill_cost_lesser_peak_factor(self):
        raise NotImplementedError
