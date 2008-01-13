import random


class Reservoir:
    def __init__(self, initialDepth, initialReserves):
        self._totalDepth = initialDepth
        self._oilDepth = initialDepth
        self._size = 1
        self._initialReserves = initialReserves
        self._reserves = initialReserves

    def join(self, oilDepth, initialReserves):
        self._size += 1
        self._totalDepth += oilDepth
        self._oilDepth = int(self._totalDepth / self._size)
        self._initialReserves += initialReserves
        self._reserves = self._initialReserves

    def getOilDepth(self):
        return self._oilDepth

    def getReserves(self):
        return self._reserves

    def ratioPumped(self):
        return 1.0 - (self._reserves * 1. / self._initialReserves)

    def pump(self, barrels):
        import logging
        log = logging.getLogger("Wildcatting")
        log.info("Pumping %s barrels from %s in reserves" % (barrels, self._reserves))
        assert 0 < barrels < self._reserves

        self._reserves -= barrels
        
