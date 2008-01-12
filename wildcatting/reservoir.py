import random

class Reservoir:
    def __init__(self, initialDepth):
        self._totalDepth = initialDepth
        self._oilDepth = initialDepth
        self._size = 1
        self._initialReserves = random.randint(1, 378000)
        self._reserves = self._initialReserves

    def join(self, oilDepth):
        self._size += 1
        self._totalDepth += oilDepth
        self._oilDepth = int(self._totalDepth / self._size)

    def getOilDepth(self):
        return self._oilDepth

    def getReserves(self):
        return self._reserves

    def ratioPumped(self):
        return self._reserves / self._initialReserves

    def pump(self, barrels):
        assert 0 < barrels < self._reserves

        self._reserves -= barrels
        
