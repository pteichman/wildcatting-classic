from serialize import Serializable

class Bar(Serializable):
    def __init__(self):
        self._hrm = "hrm"

class Foo(Serializable):
    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value

    def getBar(self):
        return self._bar

    def setBar(self, bar):
        self._bar = bar
