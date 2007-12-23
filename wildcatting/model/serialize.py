import new
import wildcatting.model
from pprint import PrettyPrinter

# pretty-printer for getting a single line (but sorted nicely)
# representation of objects
_pp = PrettyPrinter(width=100000)

class Serializable:
    CLASS_KEY = "wildcatting.model.Serializable.class"
    STATE_KEY = "wildcatting.model.Serializable.state"

    def __repr__(self):
        return "<%s instance at 0x%s> %s" % (self.__class__.__name__,
                                             id(self),
                                             _pp.pformat(self.__dict__))
    
    def serialize(self):
        return self.__serialize_instance(self)

    def deserialize(cls, state):
        clsname = state.get(Serializable.CLASS_KEY)
        if clsname != cls.__name__:
            raise Exception("Trying to deserialize a %s as a %s" % (cls.__name__, clsname))

        obj = new.instance(cls)
        obj.__dict__ = obj.__deserialize_item(state.get(Serializable.STATE_KEY))
        return obj
    deserialize = classmethod(deserialize)

    def __serialize_instance(self, item):
        return {Serializable.CLASS_KEY : item.__class__.__name__,
                Serializable.STATE_KEY : item.__serialize_item(item.__dict__)}

    def __deserialize_subinstance(self, state):
        if isinstance(state, dict) and state.has_key(Serializable.CLASS_KEY):
            clsname = state[Serializable.CLASS_KEY]

            cls = getattr(wildcatting.model, clsname)
            return cls.deserialize(state)

        return self.__deserialize_item(state)

    def __serialize_item(self, item):
        if isinstance(item, Serializable):
            return self.__serialize_instance(item)
        elif isinstance(item, dict):
            return self.__serialize_dict(item)
        elif isinstance(item, list):
            return self.__serialize_list(item)
        else:
            return item

    def __deserialize_item(self, item):
        if isinstance(item, dict):
            if item.has_key(Serializable.CLASS_KEY):
                return self.__deserialize_subinstance(item)
            return self.__deserialize_dict(item)
        elif isinstance(item, list):
            return self.__deserialize_list(item)
        else:
            return item

    def __serialize_dict(self, dict):
        ret = {}
        for key, value in dict.items():
            ret[key] = self.__serialize_item(value)
        return ret

    def __deserialize_dict(self, dict):
        ret = {}
        for key, value in dict.items():
            ret[key] = self.__deserialize_item(value)
        return ret

    def __serialize_list(self, items):
        ret = []
        for item in items:
            ret.append(self.__serialize_item(item))
        return ret

    def __deserialize_list(self, items):
        ret = []
        for item in items:
            ret.append(self.__deserialize_item(item))
        return ret

