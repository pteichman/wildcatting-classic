from serialize import Serializable

class Setting(Serializable):
    def __init__(self):
        self._name = None

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name
