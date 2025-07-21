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
        raise NotImplementedError
    def getEra(self):
        raise NotImplementedError

    # units
    def getDrillIncrement(self):
        raise NotImplementedError
    def getPriceFormat(self):
        raise NotImplementedError

    ## extraction
    def getWellTheory(self):
        raise NotImplementedError
    def getMeanSiteReserves(self):
        raise NotImplementedError

    ## economics
    def getMinDrillCost(self):
        raise NotImplementedError
    def getMaxDrillCost(self):
        raise NotImplementedError
    def getMinTax(self):
        raise NotImplementedError
    def getMaxTax(self):
        raise NotImplementedError
    def getMinOutput(self):
        raise NotImplementedError
    def getMaxOutput(self):
        raise NotImplementedError
    def getOilPrices(self):
        raise NotImplementedError

    ## oil probability distribution
    def getOilMinDropoff(self):
        raise NotImplementedError
    def getOilMaxDropoff(self):
        raise NotImplementedError
    def getOilMaxPeaks(self):
        raise NotImplementedError
    def getOilFudge(self):
        raise NotImplementedError
    def getOilLesserPeakFactor(self):
        raise NotImplementedError

    ## drill cost distribution
    def getDrillCostMinDropoff(self):
        raise NotImplementedError
    def getDrillCostMaxDropoff(self):
        raise NotImplementedError
    def getDrillCostMaxPeaks(self):
        raise NotImplementedError
    def getDrillCostFudge(self):
        raise NotImplementedError
    def getDrillCostLesserPeakFactor(self):
        raise NotImplementedError
