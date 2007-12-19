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
        lines = f.readlines()
        self._facts = [line[:-1] for line in lines]
        self.log.info(self._facts)

    def getSetting(self):
        setting = wildcatting.model.Setting()
        setting.setLocation(self._location)
        setting.setFacts(self._facts)
        return setting
