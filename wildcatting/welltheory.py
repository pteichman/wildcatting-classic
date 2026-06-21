import math


class SimpleWellTheory:
    def __init__(self, maxOutput):
        self._maxOutput = maxOutput

    def __str__(self):
        return f"SimpleWellTheory(maxOutput={self._maxOutput})"

    def _getOutput(self, site, capacity=None):
        well = site.getWell()
        reservoir = site.getReservoir()
        ratioPumped = reservoir.ratioPumped()
        if capacity is None:
            capacity = well.getCapacity()
        ## actually the maximum output for one unit of well capacity
        output = self._maxOutput
        ## diminishing returns for increased capacity.  not too relevant yet.
        c = capacity * 1.0
        output += (c - 1) * output - math.pow(c - 1, 2)
        ## the most you can ever get at once is half
        output = min(output, reservoir.getReserves() / 2.0)
        ## the first oil is the lightest, the sweetest, and the easiest to pump
        output = (1.0 - ratioPumped) * output

        return output

    def start(self, site):
        return self._getOutput(site)

    def week(self, site, currentWeek):
        well = site.getWell()
        weeksOperational = currentWeek - well.getWeek()

        new_capacity = well.getCapacity()
        ## simlulate old well ramp up.
        if weeksOperational <= 3:
            new_capacity += 1

        output = self._getOutput(site, new_capacity)
        return output, new_capacity
