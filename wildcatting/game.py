import abc
import logging
import math
import random
import secrets

import wildcatting.model
import wildcatting.turn
import wildcatting.week
from wildcatting.exceptions import WildcattingException

from .reservoir import Reservoir
from .theme import DefaultTheme, Theme


class Filler(abc.ABC):
    @abc.abstractmethod
    def fill(self, field: wildcatting.model.OilField) -> None: ...


class PeakedFiller(Filler):
    def fill(self, field: wildcatting.model.OilField) -> None:
        peaks = self._generate_peaks(field)
        self._fill_model(field, peaks)

    def _cell_roll(self) -> int | None:
        return None

    def _fill_model(
        self, model: wildcatting.model.OilField, peaks: list[tuple[int, int]]
    ) -> None:
        for row in range(model.height):
            for col in range(model.width):
                # calculate sum of distances from peak
                minc: float = 99999
                closest: int = 0
                for p in range(len(peaks)):
                    (y, x) = peaks[p]

                    a = row - y
                    b = col - x
                    c = math.sqrt(a * a + b * b)
                    minc = min(c, minc)
                    if c == minc:
                        closest = p

                minValue, maxValue = self.get_value_range()
                lesser_peak_factor = self.get_lesser_peak_factor()
                fudge = self.get_fudge()
                field_size = math.sqrt(model.width * model.height)
                d = (minc + random.random() * fudge) / field_size
                e = max(0.001, d)
                f = 1 - max(min((math.log(e) + 3) / 3, 1.0), 0)
                peak_height = maxValue - minValue
                value = int(
                    f * peak_height - closest * random.random() * lesser_peak_factor
                )
                value = max(minValue, value)
                value = min(maxValue, value)

                roll = self._cell_roll()
                site = model.get_site(row, col)
                self.fill_site(site, value, roll)

    def _generate_peaks(
        self, model: wildcatting.model.OilField
    ) -> list[tuple[int, int]]:
        max_peaks = self.get_max_peaks()
        return [
            (random.randint(0, model.height), random.randint(0, model.width))
            for _ in range(random.randint(1, max_peaks))
        ]

    @abc.abstractmethod
    def get_value_range(self) -> tuple[int, int]: ...

    @abc.abstractmethod
    def get_lesser_peak_factor(self) -> int | float: ...

    @abc.abstractmethod
    def get_fudge(self) -> int | float: ...

    @abc.abstractmethod
    def get_max_peaks(self) -> int: ...

    @abc.abstractmethod
    def fill_site(
        self, site: wildcatting.model.Site, value: int, roll: int | None
    ) -> None: ...


class OilFiller(PeakedFiller):
    def __init__(self, theme: Theme) -> None:
        self._theme = theme

    def get_value_range(self) -> tuple[int, int]:
        return (10, 100)

    def _cell_roll(self) -> int:
        return random.randint(0, 100)

    def fill_site(
        self, site: wildcatting.model.Site, value: int, roll: int | None
    ) -> None:
        site.probability = value
        if roll is not None and roll < value:
            site.oil_flag = True

    def get_min_dropoff(self) -> int:
        return self._theme.get_oil_min_dropoff()

    def get_max_dropoff(self) -> int:
        return self._theme.get_oil_max_dropoff()

    def get_max_peaks(self) -> int:
        return self._theme.get_oil_max_peaks()

    def get_fudge(self) -> int:
        return self._theme.get_oil_fudge()

    def get_lesser_peak_factor(self) -> int:
        return self._theme.get_oil_lesser_peak_factor()


class DrillCostFiller(PeakedFiller):
    def __init__(self, theme: Theme) -> None:
        self._theme = theme

    def get_value_range(self) -> tuple[int, int]:
        return (self._theme.get_min_drill_cost(), self._theme.get_max_drill_cost())

    def fill_site(
        self, site: wildcatting.model.Site, discount: int, roll: int | None
    ) -> None:
        site.drill_cost = self._theme.get_max_drill_cost() - discount

    def get_min_dropoff(self) -> int:
        return self._theme.get_drill_cost_min_dropoff()

    def get_max_dropoff(self) -> int:
        return self._theme.get_drill_cost_max_dropoff()

    def get_max_peaks(self) -> int:
        return self._theme.get_drill_cost_max_peaks()

    def get_fudge(self) -> int:
        return self._theme.get_drill_cost_fudge()

    def get_lesser_peak_factor(self) -> int:
        return self._theme.get_drill_cost_lesser_peak_factor()


class PotentialOilDepthFiller(PeakedFiller):
    def __init__(self, theme: Theme) -> None:
        self._theme = theme

    def get_value_range(self) -> tuple[int, int]:
        return (1, 10)

    def fill_site(
        self, site: wildcatting.model.Site, value: int, roll: int | None
    ) -> None:
        if site.oil_flag:
            site.potential_oil_depth = 11 - value

    def get_min_dropoff(self) -> int:
        return 0

    def get_max_dropoff(self) -> int:
        return 0

    def get_max_peaks(self) -> int:
        return 10

    def get_fudge(self) -> int:
        return 0

    def get_lesser_peak_factor(self) -> int:
        return 1


class ReservoirFiller(Filler):
    log = logging.getLogger("Wildcatting")

    def __init__(self, theme: Theme) -> None:
        self._theme = theme

    def fill(self, field: wildcatting.model.OilField) -> None:
        height, width = field.height, field.width
        reservoir_count = 0
        site_count = 0
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                if not site.oil_flag:
                    continue
                adjacent_sites: list[wildcatting.model.Site] = []
                for adjacent_row, adjacent_col in [(row + 1, col), (row, col + 1)]:
                    if adjacent_row >= height or adjacent_col >= width:
                        continue

                    adjacent_site = field.get_site(adjacent_row, adjacent_col)
                    adjacent_sites.append(adjacent_site)
                dr, ds = self._fill_site(site, adjacent_sites)
                reservoir_count += dr
                site_count += ds

        self.log.info(
            "Created %d reservoirs covering %d sites", reservoir_count, site_count
        )

    def _get_initial_reserves(self) -> int:
        reserves = int(
            max(0.1, random.gauss(1, 1)) * self._theme.get_mean_site_reserves()
        )
        return reserves

    def _depth_bracket(self, depth: int | None) -> int:
        if depth is None:
            return -1
        return int(depth * 1.0 / 9 * 6)

    def _fill_site(
        self,
        site: wildcatting.model.Site,
        adjacent_sites: list[wildcatting.model.Site],
    ) -> tuple[int, int]:
        initial_depth = site.potential_oil_depth
        reservoir_count = 0
        site_count = 0

        for adjacent_site in adjacent_sites:
            initial_reserves = self._get_initial_reserves()
            adj_depth = adjacent_site.potential_oil_depth
            if self._depth_bracket(initial_depth) == self._depth_bracket(adj_depth):
                site_count += 1
                reservoir = site.reservoir
                if reservoir is None:
                    reservoir_count += 1
                    reservoir = Reservoir(initial_depth, initial_reserves)
                    site.reservoir = reservoir

                reservoir.join(adjacent_site.potential_oil_depth, initial_reserves)
                adjacent_site.reservoir = reservoir
            else:
                reservoir_count += 1
                site.reservoir = Reservoir(initial_depth, initial_reserves)

        return reservoir_count, site_count


class TaxFiller:
    def __init__(self, theme: Theme) -> None:
        self._theme = theme

    def fill(self, field: wildcatting.model.OilField) -> None:
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                site.tax = random.randint(
                    self._theme.get_min_tax(), self._theme.get_max_tax()
                )


class Game:
    log = logging.getLogger("Wildcatting")

    def __init__(
        self, width: int, height: int, turn_count: int = 13, theme: Theme | None = None
    ) -> None:
        if theme is None:
            theme = DefaultTheme()

        self._turn_count = turn_count
        self._theme = theme
        self._players: dict[str, wildcatting.model.Player] = {}
        self._player_order: list[wildcatting.model.Player] = []
        self._is_started: bool = False
        self._is_finished: bool = False
        self._week_num: int = 0
        self._clients: dict[str, list[wildcatting.model.Player]] = {}
        self._client_updates: dict[str, list[wildcatting.model.Site]] = {}

        self._prices = theme.get_oil_prices()

        self._oil_field = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oil_field)
        PotentialOilDepthFiller(theme).fill(self._oil_field)
        ReservoirFiller(theme).fill(self._oil_field)
        DrillCostFiller(theme).fill(self._oil_field)
        TaxFiller(theme).fill(self._oil_field)

    def _new_client_id(self) -> str:
        client_id = self._generate_secret()
        self._client_updates[client_id] = []
        return client_id

    def _generate_secret(self) -> str:
        return secrets.token_hex(8).upper()

    def get_client_players(self, client_id: str) -> list[wildcatting.model.Player]:
        return self._clients.get(client_id, [])

    def add_player(self, client_id: str, player: wildcatting.model.Player) -> None:
        player_names = [p.username for p in list(self._players.values())]
        if player.username in player_names:
            raise WildcattingException(
                f"A user named {player.username} has already joined this game"
            )

        secret = self._generate_secret()
        player.secret = secret

        self._players[secret] = player
        self._player_order.append(player)

        self._clients.setdefault(client_id, []).append(player)

    @property
    def master(self) -> wildcatting.model.Player | None:
        if len(self._player_order) > 0:
            return self._player_order[0]
        return None

    def get_player(self, username: str, secret: str) -> wildcatting.model.Player:
        if not isinstance(username, str) or not isinstance(secret, str):
            raise WildcattingException("Invalid login")

        player = self._players.get(secret)

        if player is None or player.username != username:
            raise WildcattingException("Invalid login")

        return player

    def get_players(self) -> list[wildcatting.model.Player]:
        # return a copy, since we don't want outside callers to be able
        # to modify the order
        return self._player_order[:]

    def start(self) -> None:
        self._is_started = True
        self._next_week()

    def _next_week(self) -> None:
        self._week_num = self._week_num + 1

        price = next(self._prices)
        self._week = wildcatting.week.Week(self._week_num, self._player_order, price)
        self._oil_field.tick(price, self._theme.get_well_theory(), self._week_num)

        if self._week_num > self._turn_count:
            self._finish()

    @property
    def week(self) -> wildcatting.week.Week:
        return self._week

    @property
    def started(self) -> bool:
        return self._is_started

    def _finish(self) -> None:
        self._is_finished = True

        players = sorted(self._players.values(), key=lambda p: -p.profit_and_loss)

        player_strs = [f"{p.username} ({p.profit_and_loss})" for p in players]

        self.log.info("Game is finished.  Scores: %s", ", ".join(player_strs))

    @property
    def finished(self) -> bool:
        return self._is_finished

    def drill(self, row: int, col: int) -> bool:
        site = self._oil_field.get_site(row, col)
        well = site.well
        assert well is not None
        foundOil, cost = well.drill(site, self._theme.get_drill_increment())
        well.player.expense(cost)

        if foundOil:
            site.oil_depth = well.drill_depth
            theory = self._theme.get_well_theory()
            reservoir = site.reservoir
            assert reservoir is not None
            output = theory.start(well, reservoir)
            well.output = output

        return foundOil

    def end_turn(self, player: wildcatting.model.Player) -> None:
        self._week.end_turn(player)

        if self._week.finished:
            self._next_week()

    @property
    def weekly_summary(self) -> wildcatting.model.WeeklySummary:
        return wildcatting.model.WeeklySummary(self._player_order, self._week_num)

    def mark_site_updated(
        self, player: wildcatting.model.Player, site: wildcatting.model.Site
    ) -> None:
        for update_client in self._client_updates:
            if player not in self._clients[update_client]:
                update_sites = self._client_updates[update_client]
                if site not in update_sites:
                    update_sites.append(site)

    def pop_updated_sites(self, client_id: str) -> list[wildcatting.model.Site]:
        updates = self._client_updates[client_id]
        self._client_updates[client_id] = []
        return updates

    @property
    def oil_price(self) -> float:
        return self._week.price

    @property
    def oil_field(self) -> wildcatting.model.OilField:
        return self._oil_field
