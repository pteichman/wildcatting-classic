import random
import math


class SimpleWellTheory:
    def __init__(self, maxOutput):
        self._maxOutput = maxOutput

    def __str__(self):
        pass

    def _getOutput(self, site):
        well = site.getWell()
        reservoir = site.getReservoir()
        ratioPumped = reservoir.ratioPumped()
        ## actually the maximum output for one unit of well capacity
        output = self._maxOutput
        ## diminishing returns for increased capacity.  not too relevant yet.
        c = well.getCapacity() * 1.0
        output += (c - 1) * output - math.pow(c - 1, 2)
        ## the most you can ever get at once is half
        output = min(output, reservoir.getReserves() / 2.0)
        ## the first oil is the lightest, the sweetest, and the easiest to pump
        output = (1.0 - ratioPumped) * output
        
        return output
    
    def start(self, site):
        output = self._getOutput(site)
        well = site.getWell()
        well.setOutput(output)
        well.setInitialOutput(output)

    def week(self, site, currentWeek):
        well = site.getWell()
        weeksOperational = currentWeek - well.getWeek()

        ## simlulate old well ramp up.
        if weeksOperational <= 3:
            well.setCapacity(well.getCapacity() + 1)

        output = self._getOutput(site)
        well.setOutput(output)
