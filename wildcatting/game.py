from wildcatting.oilfield import OilField

class Game:
    def __init__(self, width, height):
        self._oilField = OilField(width, height)

    def getOilField(self):
        return self._oilField
