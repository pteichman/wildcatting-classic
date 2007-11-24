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

class OilPlayerField(Serializable):
    def __init__(self, field):
        assert isinstance(field, OilField)

        self._rows = []

        for row in xrange(field.getHeight()):
            newrow = []
            for col in xrange(field.getWidth()):
                newrow.append(OilPlayerSite(field.getSite(row, col)))
            self._rows.append(newrow)

class Site(Serializable):
    def __init__(self, row, col, prob):
        assert isinstance(row, int)
        assert isinstance(col, int)
        assert isinstance(prob, int)

        assert 0 <= prob <= 100

        self._row = row
        self._col = col
        self._prob = prob
        self._rig = " "
        self._cost = 0
        self._tax = 0

    def getCol(self):
        return self._col

    def getCost(self):
        return self._cost

    def getProbability(self):
        return self._prob

    def getRig(self):
        return self._rig

    def getRow(self):
        return self._row

    def getTax(self):
        return self._tax

class OilPlayerSite(Serializable):
    def __init__(self, site):
        assert isinstance(site, Site)

        self._rig = site.getRig()

    def getRig(self):
        return self._rig
