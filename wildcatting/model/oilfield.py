from serialize import Serializable

class OilField(Serializable):
    def __init__(self, width, height):
        assert isinstance(width, int)
        assert isinstance(height, int)

        self._width = width
        self._height = height

        self._rows = [ [ Site(row, col) for col in xrange(width) ]
                       for row in xrange(height) ]

    def getSite(self, row, col):
        assert row < self._height
        assert col < self._width
        
        site = self._rows[row][col]

        assert site.getRow() == row
        assert site.getCol() == col

        return site

    def setSite(self, row, col, site):
        assert False
        assert isinstance(site, Site)

        self._rows[row][col] = site

    def getHeight(self):
        return self._height

    def getWidth(self):
        return self._width

class Site(Serializable):
    def __init__(self, row, col):
        assert isinstance(row, int)
        assert isinstance(col, int)

        self._row = row
        self._col = col

        self._prob = 0
        self._rig = " "
        self._drillCost = 0
        self._tax = 0

        self._surveyed = False

    def getCol(self):
        return self._col

    def getDrillCost(self):
        return self._drillCost

    def setDrillCost(self, drillCost):
        assert isinstance(drillCost, int)
        self._drillCost = drillCost

    def getProbability(self):
        return self._prob

    def setProbability(self, prob):
        assert 0 <= prob <= 100
        self._prob = prob

    def getRig(self):
        return self._rig

    def setRig(self, rig):
        assert isinstance(rig, str)
        assert len(rig) == 1
        self._rig = rig

    def getRow(self):
        return self._row

    def getSurveyed(self):
        return self._surveyed

    def setSurveyed(self, surveyed):
        assert isinstance(surveyed, bool)
        self._surveyed = surveyed

    def getTax(self):
        return self._tax

    def setTax(self, tax):
        assert isinstance(tax, int)
        self._tax = tax
