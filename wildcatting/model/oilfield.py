from serialize import Serializable

class OilField(Serializable):
    def __init__(self, width, height):
        self._width = width
        self._height = height

        self._rows = []
        for row in xrange(height):
            newrow = []
            for col in xrange(width):
                newrow.append(None)
            self._rows.append(newrow)

    def getSite(self, row, col):
        assert row < self._height
        assert col < self._width
        
        return self._rows[row][col]

    def setSite(self, row, col, site):
        assert isinstance(site, Site)

        self._rows[row][col] = site

    def getHeight(self):
        return self._height

    def getWidth(self):
        return self._width

class Site(Serializable):
    def __init__(self, prob):
        self._prob = prob
        self._rig = " "

    def __repr__(self):
        return str(self._prob)

    def getProbability(self):
        return self._prob

    def getRig(self):
        return self._rig

