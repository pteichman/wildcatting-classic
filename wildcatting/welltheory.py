from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wildcatting.model.oilfield import Well
    from wildcatting.reservoir import Reservoir


class SimpleWellTheory:
    def __init__(self, maxOutput: int) -> None:
        self._maxOutput = maxOutput

    def __str__(self) -> str:
        return f"SimpleWellTheory(maxOutput={self._maxOutput})"

    def _get_output(
        self, well: Well, reservoir: Reservoir, capacity: int | None = None
    ) -> float:
        ratio_pumped = reservoir.ratio_pumped()
        if capacity is None:
            capacity = well.capacity
        ## actually the maximum output for one unit of well capacity
        output: float = self._maxOutput
        ## diminishing returns for increased capacity.  not too relevant yet.
        c = capacity * 1.0
        output += (c - 1) * output - math.pow(c - 1, 2)
        ## the most you can ever get at once is half
        output = min(output, reservoir.reserves / 2.0)
        ## the first oil is the lightest, the sweetest, and the easiest to pump
        output = (1.0 - ratio_pumped) * output

        return output

    def start(self, well: Well, reservoir: Reservoir) -> float:
        return self._get_output(well, reservoir)

    def tick(
        self, well: Well, reservoir: Reservoir, currentWeek: int
    ) -> tuple[float, int]:
        weeksOperational = currentWeek - well.week

        new_capacity = well.capacity
        ## simlulate old well ramp up.
        if weeksOperational <= 3:
            new_capacity += 1

        output = self._get_output(well, reservoir, new_capacity)
        return output, new_capacity
