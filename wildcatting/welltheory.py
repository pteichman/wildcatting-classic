import random
import math

class SimpleWellTheory:
    def __init__(self, minOutput, maxOutput):
        self._minOutput = minOutput
        self._maxOutput = maxOutput

    def __str__(self):
        pass
    
    def start(self, well):
        output = random.randint(self._minOutput, self._maxOutput)
        well.setOutput(output)
        well.setInitialOutput(output)

    def week(self, well, currentWeek):
        weeksOperational = currentWeek - well.getWeek()

        # simple 3 week peak with noise
        if weeksOperational <= 2:
            offset = (0.5 + random.random()) * math.pow(weeksOperational + 3, 2)
        else:
            offset = - (1 + random.random()) * math.pow(weeksOperational - 3, 2)            

        output = well.getOutput() + offset
        if output < 0:
            output = 0
        well.setOutput(output)
