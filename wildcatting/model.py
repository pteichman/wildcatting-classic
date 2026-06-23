from pprint import pformat
from typing import Any, NamedTuple, Protocol, Self

from wildcatting.reservoir import Reservoir


class Serializable:
    CLASS_KEY = "wildcatting.model.Serializable.class"
    STATE_KEY = "wildcatting.model.Serializable.state"
    _registry: "dict[str, type[Serializable]]" = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        Serializable._registry[cls.__name__] = cls

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return (
            f"<{cls} instance at 0x{id(self):x}> {pformat(self.__dict__, width=100000)}"
        )

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
            cls = Serializable._registry[clsname]
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


class Player(Serializable):
    def __init__(self, username: str, symbol: str) -> None:
        assert len(symbol) == 1

        self.username = username
        self.symbol = symbol
        self._secret: str | None = None

        self.profit_and_loss: int = 0

    @property
    def secret(self) -> str:
        return self._secret or ""

    @secret.setter
    def secret(self, secret: str) -> None:
        self._secret = secret

    def income(self, income: int) -> None:
        self.profit_and_loss += income

    def expense(self, expense: int) -> None:
        self.profit_and_loss -= expense


class ClientInfo(Serializable):
    def __init__(self, clientHandle: str, gameId: str) -> None:
        self._clientHandle = clientHandle
        self._gameId = gameId
        self._players: list[str] = []
        self._handles: dict[str, str] = {}
        self._symbols: dict[str, str] = {}

    @property
    def game_id(self) -> str:
        return self._gameId

    @game_id.setter
    def game_id(self, gameId: str) -> None:
        self._gameId = gameId

    @property
    def client_handle(self) -> str:
        return self._clientHandle

    @client_handle.setter
    def client_handle(self, clientHandle: str) -> None:
        self._clientHandle = clientHandle

    def add_player_info(self, username: str, handle: str, symbol: str) -> None:
        self._players.append(username)
        self._handles[username] = handle
        self._symbols[username] = symbol

    def has_player(self, username: str) -> bool:
        return username in self._players

    def get_player_handle(self, username: str) -> str:
        return self._handles[username]

    def get_player_symbol(self, username: str) -> str:
        return self._symbols[username]


class Setting(Serializable):
    def __init__(self) -> None:
        self.min_drill_cost: int | None = None
        self.max_drill_cost: int | None = None

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, location: str) -> None:
        self._location = location

    @property
    def era(self) -> str:
        return self._era

    @era.setter
    def era(self, era: str) -> None:
        self._era = era

    @property
    def facts(self) -> list[str]:
        return self._facts

    @facts.setter
    def facts(self, facts: list[str]) -> None:
        self._facts = facts

    @property
    def drill_increment(self) -> int:
        return self._increment

    @drill_increment.setter
    def drill_increment(self, increment: int) -> None:
        self._increment = increment

    @property
    def price_format(self) -> str:
        return self._price_format

    @price_format.setter
    def price_format(self, price_format: str) -> None:
        self._price_format = price_format


class DrillResult(NamedTuple):
    found_oil: bool
    cost: int


class TickResult(NamedTuple):
    output: float
    capacity: int


class WellTheory(Protocol):
    def tick(
        self, well: "Well", reservoir: Reservoir, current_week: int
    ) -> TickResult: ...

    def start(self, well: "Well", reservoir: Reservoir) -> float: ...


class OilField(Serializable):
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self._rows: list[list[Site]] = [
            [Site(row, col) for col in range(width)] for row in range(height)
        ]

    def tick(
        self, oil_price: float, well_theory: WellTheory, current_week: int
    ) -> None:
        for row in self._rows:
            for site in row:
                site.tick(oil_price, well_theory, current_week)

    def get_site(self, row: int, col: int) -> "Site":
        assert row < self.height
        assert col < self.width

        site = self._rows[row][col]

        assert site.row == row
        assert site.col == col

        return site

    def set_site(self, row: int, col: int, site: "Site") -> None:
        self._rows[row][col] = site


class Site(Serializable):
    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col

        self._prob: int = 0
        self._well: Well | None = None
        self._drill_cost: int = 0
        self._tax: int = 0
        self._surveyed: bool = False
        self.oil_depth: int | None = None

        ## don't serialize
        self.__reservoir: Reservoir | None = None
        self.__oil_flag: bool = False
        self.__potential_oil_depth: int | None = None

    @property
    def drill_cost(self) -> int:
        return self._drill_cost

    @drill_cost.setter
    def drill_cost(self, drill_cost: int) -> None:
        self._drill_cost = drill_cost

    @property
    def potential_oil_depth(self) -> int | None:
        return self.__potential_oil_depth

    @potential_oil_depth.setter
    def potential_oil_depth(self, potential_oil_depth: int | None) -> None:
        self.__potential_oil_depth = potential_oil_depth

    @property
    def probability(self) -> int:
        return self._prob

    @probability.setter
    def probability(self, prob: int) -> None:
        assert 0 <= prob <= 100
        self._prob = prob

    @property
    def well(self) -> "Well | None":
        return self._well

    @well.setter
    def well(self, well: "Well | None") -> None:
        self._well = well

    @property
    def surveyed(self) -> bool:
        return self._surveyed

    @surveyed.setter
    def surveyed(self, surveyed: bool) -> None:
        self._surveyed = surveyed

    @property
    def tax(self) -> int:
        return self._tax

    @tax.setter
    def tax(self, tax: int) -> None:
        self._tax = tax

    @property
    def reservoir(self) -> Reservoir | None:
        return self.__reservoir

    @reservoir.setter
    def reservoir(self, reservoir: Reservoir | None) -> None:
        self.__reservoir = reservoir

    @property
    def oil_flag(self) -> bool:
        return self.__oil_flag

    @oil_flag.setter
    def oil_flag(self, oil_flag: bool) -> None:
        self.__oil_flag = oil_flag

    def tick(
        self, oil_price: float, well_theory: WellTheory, current_week: int
    ) -> None:
        if self._well is not None:
            reservoir = self.__reservoir
            if (
                self._well.output is not None
                and not self._well.sold
                and reservoir is not None
            ):
                output, capacity = well_theory.tick(self._well, reservoir, current_week)
                self._well.output = output
                self._well.capacity = capacity
            self._well.tick(self, oil_price)


class Well(Serializable):
    def __init__(self, week: int, player: Player) -> None:
        self.week: int = week
        self.drill_depth: int = 0
        self.output: float | None = None
        self.sold: bool = False
        self.player: Player = player
        self.initial_cost: int = 0
        self.profit_and_loss: int = 0
        self.capacity: int = 1

    def __lt__(self, other: "Well") -> bool:
        return self.week < other.week

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Well) and self.week == other.week

    def __hash__(self) -> int:
        return id(self)

    def sell(self) -> int:
        self.sold = True
        price = self.initial_cost // 2
        self.profit_and_loss += price
        return price

    def drill(self, site: Site, drill_increment: int) -> DrillResult:
        assert 0 <= self.drill_depth <= 10

        oil_depth: int | None = None
        reservoir = site.reservoir
        if reservoir is not None:
            oil_depth = reservoir.oil_depth

        drill_cost = site.drill_cost

        assert oil_depth is None or self.drill_depth < oil_depth

        self.drill_depth += 1

        cost = drill_cost * drill_increment
        self.initial_cost += cost
        self.profit_and_loss -= cost

        return DrillResult(self.drill_depth == oil_depth, cost)

    @staticmethod
    def _compute_weekly_pnl(
        output: float, oil_price: float, tax: int
    ) -> tuple[int, int]:
        income = int(output * oil_price)
        return income, tax

    def tick(self, site: Site, oil_price: float) -> None:
        if not self.sold:
            output: float = self.output if self.output is not None else 0

            reservoir = site.reservoir
            if reservoir is not None:
                reservoir.pump(output)

            tax = site.tax
            income, expense = self._compute_weekly_pnl(output, oil_price, tax)

            self.profit_and_loss -= expense
            self.profit_and_loss += income

            if self.player is not None:
                self.player.expense(expense)
                self.player.income(income)


class WeeklySummary(Serializable):
    def __init__(self, player_order: list[Player], week: int) -> None:
        self._player_order = player_order
        self.week = week

        self.report_rows = self._build_report_rows()

    def _build_report_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        max_profit_and_loss: int | None = None
        for player in self._player_order:
            profit_and_loss = player.profit_and_loss
            if max_profit_and_loss is None or profit_and_loss > max_profit_and_loss:
                max_profit_and_loss = profit_and_loss
        for player in self._player_order:
            profit_and_loss = player.profit_and_loss
            row: dict[str, Any] = {
                "username": player.username,
                "profitAndLoss": profit_and_loss,
                "leader": (profit_and_loss == max_profit_and_loss),
            }
            rows.append(row)
        return rows


class Update(Serializable):
    def __init__(
        self,
        week: int,
        oil_price: float,
        players_turn: str | None,
        pending_players: list[str],
        game_finished: bool,
        sites: list[Site],
    ) -> None:
        self.week = week
        self.oil_price = oil_price
        self.players_turn = players_turn
        self.pending_players = pending_players
        self.game_finished = game_finished
        self.sites = sites
