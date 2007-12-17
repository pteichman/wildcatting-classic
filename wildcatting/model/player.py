from serialize import Serializable

class Player(Serializable):
    def __init__(self, username, rig):
        assert isinstance(username, str)
        assert isinstance(rig, str)
        assert len(rig) == 1

        self._username = username
        self._rig = rig

    def getUsername(self):
        return self._username

    def getRig(self):
        return self._rig
