class Reservoir:
    def __init__(self, initialDepth: int | None, initialReserves: int) -> None:
        self._totalDepth: int | None = initialDepth
        self._oilDepth: int | None = initialDepth
        self._size: int = 1
        self._initialReserves: int = initialReserves
        self._reserves: int | float = initialReserves

    def join(self, oilDepth: int | None, initialReserves: int) -> None:
        self._size += 1
        # _totalDepth and oilDepth are int when called from ReservoirFiller
        self._totalDepth += oilDepth  # type: ignore[operator]
        self._oilDepth = int(self._totalDepth / self._size)
        self._initialReserves += initialReserves
        self._reserves = self._initialReserves

    @property
    def oil_depth(self) -> int | None:
        return self._oilDepth

    @property
    def reserves(self) -> int | float:
        return self._reserves

    def ratio_pumped(self) -> float:
        return 1.0 - (self._reserves * 1.0 / self._initialReserves)

    def pump(self, barrels: float) -> None:
        assert 0 <= barrels < self._reserves

        self._reserves -= barrels
