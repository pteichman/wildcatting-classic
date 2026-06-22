from .serialize import Serializable


class Setting(Serializable):
    def __init__(self):
        self.min_drill_cost = None
        self.max_drill_cost = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        assert isinstance(location, str)
        self._location = location

    @property
    def era(self):
        return self._era

    @era.setter
    def era(self, era):
        assert isinstance(era, str)
        self._era = era

    @property
    def facts(self):
        return self._facts

    @facts.setter
    def facts(self, facts):
        assert isinstance(facts, list)
        self._facts = facts

    @property
    def drill_increment(self):
        return self._increment

    @drill_increment.setter
    def drill_increment(self, increment):
        assert isinstance(increment, int)
        self._increment = increment

    @property
    def price_format(self):
        return self._priceFormat

    @price_format.setter
    def price_format(self, priceFormat):
        assert isinstance(priceFormat, str)
        self._priceFormat = priceFormat
