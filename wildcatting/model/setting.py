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
        self._location = location

    @property
    def era(self) -> str:
        return self._era

    @era.setter
    def era(self, era: str) -> None:
        self._era = era

    @property
    def facts(self) -> list[str]:
        return self._facts

    @facts.setter
    def facts(self, facts: list[str]) -> None:
        self._facts = facts

    @property
    def drill_increment(self) -> int:
        return self._increment

    @drill_increment.setter
    def drill_increment(self, increment: int) -> None:
        self._increment = increment

    @property
    def price_format(self) -> str:
        return self._priceFormat

    @price_format.setter
    def price_format(self, priceFormat: str) -> None:
        self._priceFormat = priceFormat
