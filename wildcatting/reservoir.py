class Reservoir:
    def __init__(self, initialDepth):
        self._totalDepth = initialDepth
        self._oilDepth = initialDepth
        self._size = 1

    def join(self, oilDepth):
        self._size += 1
        self._totalDepth += oilDepth
        oilDepth += self._totalDepth / self._size

    def getOilDepth(self):
        return self._oilDepth
        
