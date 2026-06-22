from pprint import PrettyPrinter
from typing import Any, Self

import wildcatting.model

# pretty-printer for getting a single line (but sorted nicely)
# representation of objects
_pp = PrettyPrinter(width=100000)


class Serializable:
    CLASS_KEY = "wildcatting.model.Serializable.class"
    STATE_KEY = "wildcatting.model.Serializable.state"

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return f"<{cls} instance at 0x{id(self):x}> {_pp.pformat(self.__dict__)}"

    def serialize(self) -> dict[str, Any]:
        return self.__serialize_instance(self)

    @classmethod
    def deserialize(cls, state: dict[str, Any]) -> Self:
        clsname = state.get(Serializable.CLASS_KEY)
        if clsname != cls.__name__:
            raise Exception(f"Trying to deserialize a {cls.__name__} as a {clsname}")

        obj = cls.__new__(cls)
        obj.__dict__ = obj.__deserialize_item(state.get(Serializable.STATE_KEY))
        return obj

    def __serialize_instance(self, item: "Serializable") -> dict[str, Any]:
        return {
            Serializable.CLASS_KEY: item.__class__.__name__,
            Serializable.STATE_KEY: item.__serialize_item(item.__dict__),
        }

    def __deserialize_subinstance(self, state: Any) -> Any:
        if isinstance(state, dict) and Serializable.CLASS_KEY in state:
            clsname = state[Serializable.CLASS_KEY]

            cls = getattr(wildcatting.model, clsname)
            return cls.deserialize(state)

        return self.__deserialize_item(state)

    def __serialize_item(self, item: Any) -> Any:
        if isinstance(item, Serializable):
            return self.__serialize_instance(item)
        elif isinstance(item, dict):
            return self.__serialize_dict(item)
        elif isinstance(item, list):
            return self.__serialize_list(item)
        else:
            return item

    def __deserialize_item(self, item: Any) -> Any:
        if isinstance(item, dict):
            if Serializable.CLASS_KEY in item:
                return self.__deserialize_subinstance(item)
            return self.__deserialize_dict(item)
        elif isinstance(item, list):
            return self.__deserialize_list(item)
        else:
            return item

    def __serialize_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        for key, value in list(d.items()):
            if "__" in key:
                continue
            ret[key] = self.__serialize_item(value)
        return ret

    def __deserialize_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        for key, value in list(d.items()):
            ret[key] = self.__deserialize_item(value)
        return ret

    def __serialize_list(self, items: list[Any]) -> list[Any]:
        ret: list[Any] = []
        for item in items:
            ret.append(self.__serialize_item(item))
        return ret

    def __deserialize_list(self, items: list[Any]) -> list[Any]:
        ret: list[Any] = []
        for item in items:
            ret.append(self.__deserialize_item(item))
        return ret
