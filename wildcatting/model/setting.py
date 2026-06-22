from .serialize import Serializable


class Setting(Serializable):
    def __init__(self) -> None:
        self.min_drill_cost: int | None = None
        self.max_drill_cost: int | None = None

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, location: str) -> None:
        assert isinstance(location, str)
        self._location = location

    @property
    def era(self) -> str:
        return self._era

    @era.setter
    def era(self, era: str) -> None:
        assert isinstance(era, str)
        self._era = era

    @property
    def facts(self) -> list[str]:
        return self._facts

    @facts.setter
    def facts(self, facts: list[str]) -> None:
        assert isinstance(facts, list)
        self._facts = facts

    @property
    def drill_increment(self) -> int:
        return self._increment

    @drill_increment.setter
    def drill_increment(self, increment: int) -> None:
        assert isinstance(increment, int)
        self._increment = increment

    @property
    def price_format(self) -> str:
        return self._priceFormat

    @price_format.setter
    def price_format(self, priceFormat: str) -> None:
        assert isinstance(priceFormat, str)
        self._priceFormat = priceFormat
