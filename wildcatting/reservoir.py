class Reservoir:
    def __init__(self, initialDepth):
        self._initialDepth = initialDepth
        self._oilDepth = initialDepth
        self._size = 1

    def join(self, oilDepth):
        self._size += 1
        oilDepth += oilDepth / self._size

    def getOilDepth(self):
        return self._oilDepth
        
