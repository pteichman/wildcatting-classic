from .serialize import Serializable


class Setting(Serializable):
    def get_location(self):
        return self._location

    def set_location(self, location):
        assert isinstance(location, str)

        self._location = location

    def get_era(self):
        return self._era

    def set_era(self, era):
        assert isinstance(era, str)

        self._era = era

    def get_facts(self):
        return self._facts

    def set_facts(self, facts):
        assert isinstance(facts, list)

        self._facts = facts

    def get_min_drill_cost(self):
        return self._minDrillCost

    def set_min_drill_cost(self, minDrillCost):
        self._minDrillCost = minDrillCost

    def get_max_drill_cost(self):
        return self._maxDrillCost

    def set_max_drill_cost(self, maxDrillCost):
        self._maxDrillCost = maxDrillCost

    def get_drill_increment(self):
        return self._increment

    def set_drill_increment(self, increment):
        assert isinstance(increment, int)

        self._increment = increment

    def get_price_format(self):
        return self._priceFormat

    def set_price_format(self, priceFormat):
        assert isinstance(priceFormat, str)

        self._priceFormat = priceFormat
