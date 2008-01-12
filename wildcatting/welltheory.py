import random
import math

class SimpleWellTheory:
    def __init__(self, minOutput, maxOutput):
        self._minOutput = minOutput
        self._maxOutput = maxOutput

    def __str__(self):
        pass

    def _getOutput(self, site):
        well = site.getWell()
        reservoir = site.getReservoir()
        ratioPumped = reservoir.ratioPumped()
        output = int(0.001 * well.getCapacity() * reservoir.getReserves())
        ## FIXME use some kind of above 6th grade level mathmatical
        ## construct here to make the first half of the oil the easiest
        ## to pump, and the second half get progressively harder
        if ratioPumped > 0.5:
            output -= (ratioPumped - 0.5) * output
        return output
    
    def start(self, site):
        output = self._getOutput(site)
        well = site.getWell()
        well.setOutput(output)
        well.setInitialOutput(output)

    def week(self, site, currentWeek):
        well = site.getWell()
        weeksOperational = currentWeek - well.getWeek()

        # well ramp up
        if weeksOperational <= random.randint(1,3):
            well.setCapacity(well.getCapacity() + 1)

        output = self._getOutput(site)
        well.setOutput(output)
