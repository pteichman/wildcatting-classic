import math


class SimpleWellTheory:
    def __init__(self, maxOutput):
        self._maxOutput = maxOutput

    def __str__(self):
        return f"SimpleWellTheory(maxOutput={self._maxOutput})"

    def _get_output(self, site, capacity=None):
        well = site.get_well()
        reservoir = site.get_reservoir()
        ratio_pumped = reservoir.ratio_pumped()
        if capacity is None:
            capacity = well.get_capacity()
        ## actually the maximum output for one unit of well capacity
        output = self._maxOutput
        ## diminishing returns for increased capacity.  not too relevant yet.
        c = capacity * 1.0
        output += (c - 1) * output - math.pow(c - 1, 2)
        ## the most you can ever get at once is half
        output = min(output, reservoir.get_reserves() / 2.0)
        ## the first oil is the lightest, the sweetest, and the easiest to pump
        output = (1.0 - ratio_pumped) * output

        return output

    def start(self, site):
        return self._get_output(site)

    def week(self, site, currentWeek):
        well = site.get_well()
        weeksOperational = currentWeek - well.get_week()

        new_capacity = well.get_capacity()
        ## simlulate old well ramp up.
        if weeksOperational <= 3:
            new_capacity += 1

        output = self._get_output(site, new_capacity)
        return output, new_capacity
