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
        assert isinstance(field, wildcatting.model.OilField)
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
                lesserPeakFactor = self.get_lesser_peak_factor()
                fudge = self.get_fudge()
                field_size = math.sqrt(model.width * model.height)
                d = (minc + random.random() * fudge) / field_size
                e = max(0.001, d)
                f = 1 - max(min((math.log(e) + 3) / 3, 1.0), 0)
                peakHeight = maxValue - minValue
                value = int(
                    f * peakHeight - closest * random.random() * lesserPeakFactor
                )
                value = max(minValue, value)
                value = min(maxValue, value)

                roll = self._cell_roll()
                site = model.get_site(row, col)
                self.fill_site(site, value, roll)

    def _generate_peaks(
        self, model: wildcatting.model.OilField
    ) -> list[tuple[int, int]]:
        maxPeaks = self.get_max_peaks()
        return [
            (random.randint(0, model.height), random.randint(0, model.width))
            for _ in range(random.randint(1, maxPeaks))
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
        assert isinstance(theme, Theme)
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
        assert isinstance(theme, Theme)
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
        assert isinstance(theme, Theme)
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
        assert isinstance(theme, Theme)

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
                adjacentSites: list[wildcatting.model.Site] = []
                for adjacentRow, adjacentCol in [(row + 1, col), (row, col + 1)]:
                    if adjacentRow >= height or adjacentCol >= width:
                        continue

                    adjacentSite = field.get_site(adjacentRow, adjacentCol)
                    adjacentSites.append(adjacentSite)
                dr, ds = self._fill_site(site, adjacentSites)
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
        adjacentSites: list[wildcatting.model.Site],
    ) -> tuple[int, int]:
        initialDepth = site.potential_oil_depth
        reservoir_count = 0
        site_count = 0

        for adjacentSite in adjacentSites:
            initialReserves = self._get_initial_reserves()
            adj_depth = adjacentSite.potential_oil_depth
            if self._depth_bracket(initialDepth) == self._depth_bracket(adj_depth):
                site_count += 1
                reservoir = site.reservoir
                if reservoir is None:
                    reservoir_count += 1
                    reservoir = Reservoir(initialDepth, initialReserves)
                    site.reservoir = reservoir

                reservoir.join(adjacentSite.potential_oil_depth, initialReserves)
                adjacentSite.reservoir = reservoir
            else:
                reservoir_count += 1
                site.reservoir = Reservoir(initialDepth, initialReserves)

        return reservoir_count, site_count


class TaxFiller:
    def __init__(self, theme: Theme) -> None:
        assert isinstance(theme, Theme)
        self._theme = theme

    def fill(self, field: wildcatting.model.OilField) -> None:
        assert isinstance(field, wildcatting.model.OilField)

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                site.tax = random.randint(
                    self._theme.get_min_tax(), self._theme.get_max_tax()
                )


class Game:
    log = logging.getLogger("Wildcatting")

    def __init__(
        self, width: int, height: int, turnCount: int = 13, theme: Theme | None = None
    ) -> None:
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert isinstance(turnCount, int)

        if theme is None:
            theme = DefaultTheme()

        assert isinstance(theme, Theme)

        self._turnCount = turnCount
        self._theme = theme
        self._players: dict[str, wildcatting.model.Player] = {}
        self._playerOrder: list[wildcatting.model.Player] = []
        self._isStarted: bool = False
        self._isFinished: bool = False
        self._weekNum: int = 0
        self._clients: dict[str, list[wildcatting.model.Player]] = {}
        self._clientUpdates: dict[str, list[wildcatting.model.Site]] = {}

        self._prices = theme.get_oil_prices()

        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oilField)
        PotentialOilDepthFiller(theme).fill(self._oilField)
        ReservoirFiller(theme).fill(self._oilField)
        DrillCostFiller(theme).fill(self._oilField)
        TaxFiller(theme).fill(self._oilField)

    def _new_client_id(self) -> str:
        clientId = self._generate_secret()
        self._clientUpdates[clientId] = []
        return clientId

    def _generate_secret(self) -> str:
        return secrets.token_hex(8).upper()

    def get_client_players(self, clientId: str) -> list[wildcatting.model.Player]:
        return self._clients.get(clientId, [])

    def add_player(self, clientId: str, player: wildcatting.model.Player) -> None:
        assert isinstance(player, wildcatting.model.Player)

        playerNames = [p.username for p in list(self._players.values())]
        if player.username in playerNames:
            raise WildcattingException(
                f"A user named {player.username} has already joined this game"
            )

        secret = self._generate_secret()
        player.secret = secret

        self._players[secret] = player
        self._playerOrder.append(player)

        self._clients.setdefault(clientId, []).append(player)

    @property
    def master(self) -> wildcatting.model.Player | None:
        if len(self._playerOrder) > 0:
            return self._playerOrder[0]
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
        return self._playerOrder[:]

    def start(self) -> None:
        self._isStarted = True
        self._next_week()

    def _next_week(self) -> None:
        self._weekNum = self._weekNum + 1

        price = next(self._prices)
        self._week = wildcatting.week.Week(self._weekNum, self._playerOrder, price)
        self._oilField.tick(price, self._theme.get_well_theory(), self._weekNum)

        if self._weekNum > self._turnCount:
            self._finish()

    @property
    def week(self) -> wildcatting.week.Week:
        return self._week

    @property
    def started(self) -> bool:
        return self._isStarted

    def _finish(self) -> None:
        self._isFinished = True

        players = sorted(self._players.values(), key=lambda p: -p.profit_and_loss)

        playerStrs = [f"{p.username} ({p.profit_and_loss})" for p in players]

        self.log.info("Game is finished.  Scores: %s", ", ".join(playerStrs))

    @property
    def finished(self) -> bool:
        return self._isFinished

    def drill(self, row: int, col: int) -> bool:
        site = self._oilField.get_site(row, col)
        well = site.well
        assert well is not None
        foundOil, cost = well.drill(site, self._theme.get_drill_increment())
        assert well.player is not None
        well.player.expense(cost)

        if foundOil:
            site.oil_depth = well.drill_depth
            theory = self._theme.get_well_theory()
            output = theory.start(site)
            well.output = output
            well.initial_output = output

        return foundOil

    def end_turn(self, player: wildcatting.model.Player) -> None:
        self._week.end_turn(player)

        if self._week.finished:
            self._next_week()

    @property
    def weekly_summary(self) -> wildcatting.model.WeeklySummary:
        return wildcatting.model.WeeklySummary(self._playerOrder, self._weekNum)

    def mark_site_updated(
        self, player: wildcatting.model.Player, site: wildcatting.model.Site
    ) -> None:
        for updateClient in self._clientUpdates:
            if player not in self._clients[updateClient]:
                updateSites = self._clientUpdates[updateClient]
                if site not in updateSites:
                    updateSites.append(site)

    def pop_updated_sites(self, clientId: str) -> list[wildcatting.model.Site]:
        updates = self._clientUpdates[clientId]
        self._clientUpdates[clientId] = []
        return updates

    @property
    def oil_price(self) -> float:
        return self._week.price

    @property
    def oil_field(self) -> wildcatting.model.OilField:
        return self._oilField
