import os
import os.path
import logging

import wildcatting.model

class Theme:
    log = logging.getLogger("Wildcatting")

    def __init__(self):
        self._processFacts()

    def _processFacts(self):
        facts = []
        factLines = self.rawFacts.split("\n")
        for line in factLines:
            fact = line.strip()
            if fact == "":
                continue
            
            if fact[0] == "#":
                continue

            facts.append(fact)

        self._facts = facts
    
    def generateSetting(self):
        setting = wildcatting.model.Setting()
        setting.setLocation(self._location)
        setting.setEra(self._era)
        setting.setFacts(self._facts)
        return setting

    def getMinDrillCost(self):
        return self._minDrillCost

    def getLocation(self):
        return self._location

    def setLocation(self, location):
        self._location = location

    def getEra(self):
        return self._era

    def setEra(self, era):
        self._era = era

    def setMinDrillCost(self, minDrillCost):
        self._minDrillCost = minDrillCost

    def getMaxDrillCost(self):
        return self._maxDrillCost

    def setMaxDrillCost(self, maxDrillCost):
        self._maxDrillCost = maxDrillCost

    def getMinTax(self):
        return self._minTax

    def setMinTax(self, minTax):
        self._minTax = minTax

    def getMaxTax(self):
        return self._maxTax

    def setMaxTax(self, maxTax):
        self._maxTax = maxTax

    def getMaxOutput(self):
        return self._maxOutput

    def setMaxOutput(self, maxOutput):
        self._maxOutput = maxOutput

    def getInflationAdjustment(self):
        return self._inflationAdjustment

    def setInflationAdjustment(self, inflationAdjustment):
        self._inflationAdjustment = inflationAdjustment
        
