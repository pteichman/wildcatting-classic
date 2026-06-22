class Reservoir:
    def __init__(self, initial_depth: int | None, initial_reserves: int) -> None:
        self._total_depth: int | None = initial_depth
        self._oil_depth: int | None = initial_depth
        self._size: int = 1
        self._initial_reserves: int = initial_reserves
        self._reserves: int | float = initial_reserves

    def join(self, oil_depth: int | None, initial_reserves: int) -> None:
        self._size += 1
        # _total_depth and oil_depth are int when called from ReservoirFiller
        self._total_depth += oil_depth  # type: ignore[operator]
        self._oil_depth = int(self._total_depth / self._size)
        self._initial_reserves += initial_reserves
        self._reserves = self._initial_reserves

    @property
    def oil_depth(self) -> int | None:
        return self._oil_depth

    @property
    def reserves(self) -> int | float:
        return self._reserves

    def ratio_pumped(self) -> float:
        return 1.0 - (self._reserves * 1.0 / self._initial_reserves)

    def pump(self, barrels: float) -> None:
        assert 0 <= barrels < self._reserves

        self._reserves -= barrels
