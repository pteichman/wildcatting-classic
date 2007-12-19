from serialize import Serializable

class Setting(Serializable):
    def getLocation(self):
        return self._location

    def setLocation(self, location):
        assert isinstance(location, str)
        
        self._location = location

    def getFacts(self):
        return self._facts

    def setFacts(self, facts):
        assert isinstance(facts, list)
        
        self._facts = facts
