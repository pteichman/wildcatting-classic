import os
import os.path
import logging

import wildcatting.model

class Theme:
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        self._facts = []

    def _loadFacts(self, rawFacts):
        facts = []
        for line in rawFacts.split("\n"):
            fact = line.strip()
            if fact == "":
                continue
            
            if fact[0] == "#":
                continue

            facts.append(fact)

        self._facts = facts
    
    def generateSetting(self):
        setting = wildcatting.model.Setting()
        setting.setLocation(self.getLocation())
        setting.setEra(self.getEra())
        setting.setPriceFormat(self.getPriceFormat())
        setting.setFacts(self.getFacts())
        setting.setMinDrillCost(self.getMinDrillCost())
        setting.setMaxDrillCost(self.getMaxDrillCost())
        setting.setDrillIncrement(self.getDrillIncrement())
        return setting

    def getFacts(self):
        return self._facts

    def setFacts(self, facts):
        self._facts = facts

    ## themes must implement the following abstract methods

    ## literary setting
    def getLocation(self):
        raise "UnimplementedAbstractMethod"
    def getEra(self):
        raise "UnimplementedAbstractMethod"

    # units
    def getDrillIncrement(self):
        raise "UnimplementedAbstractMethod"
    def getPriceFormat(self):
        raise "UnimplementedAbstractMethod"

    ## extraction
    def getWellTheory(self):
        raise "UnimplementedAbstractMethod"
    def getMeanSiteReserves(self):
        raise "UnimplementedAbstractMethod"

    ## economics
    def getMinDrillCost(self):
        raise "UnimplementedAbstractMethod"
    def getMaxDrillCost(self):
        raise "UnimplementedAbstractMethod"
    def getMinTax(self):
        raise "UnimplementedAbstractMethod"
    def getMaxTax(self):
        raise "UnimplementedAbstractMethod"
    def getMaxOutput(self):
        raise "UnimplementedAbstractMethod"
    def getOilPrices(self):
        raise "UnimplementedAbstractMethod"

    ## oil probability distribution
    def getOilMinDropoff(self):
        raise "AbstractMethodNotImplemented"
    def getOilMaxDropoff(self):
        raise "AbstractMethodNotImplemented"
    def getOilMaxPeaks(self):
        raise "AbstractMethodNotImplemented"
    def getOilFudge(self):
        raise "AbstractMethodNotImplemented"
    def getOilLesserPeakFactor(self):
        raise "AbstractMethodNotImplemented"

    ## drill cost distribution
    def getDrillCostMinDropoff(self):
        raise "AbstractMethodNotImplemented"
    def getDrillCostMaxDropoff(self):
        raise "AbstractMethodNotImplemented"
    def getDrillCostMaxPeaks(self):
        raise "AbstractMethodNotImplemented"
    def getDrillCostFudge(self):
        raise "AbstractMethodNotImplemented"
    def getDrillCostLesserPeakFactor(self):
        raise "AbstractMethodNotImplemented"
