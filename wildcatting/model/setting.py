from .serialize import Serializable

class Setting(Serializable):
    def getLocation(self):
        return self._location

    def setLocation(self, location):
        assert isinstance(location, str)
        
        self._location = location

    def getEra(self):
        return self._era

    def setEra(self, era):
        assert isinstance(era, str)
        
        self._era = era

    def getFacts(self):
        return self._facts

    def setFacts(self, facts):
        assert isinstance(facts, list)
        
        self._facts = facts

    def getMinDrillCost(self):
        return self._minDrillCost

    def setMinDrillCost(self, minDrillCost):
        self._minDrillCost = minDrillCost

    def getMaxDrillCost(self):
        return self._maxDrillCost

    def setMaxDrillCost(self, maxDrillCost):
        self._maxDrillCost = maxDrillCost

    def getDrillIncrement(self):
        return self._increment

    def setDrillIncrement(self, increment):
        assert isinstance(increment, int)
    
        self._increment = increment

    def getPriceFormat(self):
        return self._priceFormat

    def setPriceFormat(self, priceFormat):
        assert isinstance(priceFormat, str)
        
        self._priceFormat = priceFormat
