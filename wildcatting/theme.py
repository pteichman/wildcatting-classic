import os
import os.path
import logging

import wildcatting.model

class Theme:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, themeDir):
        self.log.info("themeDir: %s" % themeDir)
        path, self._location = os.path.split(themeDir)
        
        f = open("%s/facts" % themeDir)

        facts = []
        for line in f.xreadlines():
            fact = line.strip()
            if fact == "":
                continue
            
            if fact[0] == "#":
                continue

            facts.append(fact)

        self._facts = facts
        self.log.info(self._facts)

    def getSetting(self):
        setting = wildcatting.model.Setting()
        setting.setLocation(self._location)
        setting.setFacts(self._facts)
        return setting
