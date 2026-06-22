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
    def fill(self, field): ...


class PeakedFiller(Filler):
    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)
        peaks = self._generate_peaks(field)
        self._fill_model(field, peaks)

    def _cell_roll(self):
        return None

    def _fill_model(self, model, peaks):
        for row in range(model.get_height()):
            for col in range(model.get_width()):
                # calculate sum of distances from peak
                minc: float = 99999
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
                field_size = math.sqrt(model.get_width() * model.get_height())
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

    def _generate_peaks(self, model):
        minValue, maxValue = self.get_value_range()
        maxPeaks = self.get_max_peaks()
        peaks: list[tuple[int, int] | None] = [None] * random.randint(1, maxPeaks)
        for i in range(len(peaks)):
            peaks[i] = (
                random.randint(0, model.get_height()),
                random.randint(0, model.get_width()),
            )
        return peaks

    @abc.abstractmethod
    def get_value_range(self): ...

    @abc.abstractmethod
    def get_lesser_peak_factor(self): ...

    @abc.abstractmethod
    def get_fudge(self): ...

    @abc.abstractmethod
    def get_max_peaks(self): ...

    @abc.abstractmethod
    def fill_site(self, site, value, roll): ...


class OilFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def get_value_range(self):
        return (10, 100)

    def _cell_roll(self):
        return random.randint(0, 100)

    def fill_site(self, site, value, roll):
        site.set_probability(value)
        if roll < value:
            site.set_oil_flag(True)

    def get_min_dropoff(self):
        return self._theme.get_oil_min_dropoff()

    def get_max_dropoff(self):
        return self._theme.get_oil_max_dropoff()

    def get_max_peaks(self):
        return self._theme.get_oil_max_peaks()

    def get_fudge(self):
        return self._theme.get_oil_fudge()

    def get_lesser_peak_factor(self):
        return self._theme.get_oil_lesser_peak_factor()


class DrillCostFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def get_value_range(self):
        return (self._theme.get_min_drill_cost(), self._theme.get_max_drill_cost())

    def fill_site(self, site, discount, roll):
        site.set_drill_cost(self._theme.get_max_drill_cost() - discount)

    def get_min_dropoff(self):
        return self._theme.get_drill_cost_min_dropoff()

    def get_max_dropoff(self):
        return self._theme.get_drill_cost_max_dropoff()

    def get_max_peaks(self):
        return self._theme.get_drill_cost_max_peaks()

    def get_fudge(self):
        return self._theme.get_drill_cost_fudge()

    def get_lesser_peak_factor(self):
        return self._theme.get_drill_cost_lesser_peak_factor()


class PotentialOilDepthFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def get_value_range(self):
        return (1, 10)

    def fill_site(self, site, value, roll):
        if site.get_oil_flag():
            site.set_potential_oil_depth(11 - value)

    def get_min_dropoff(self):
        return 0

    def get_max_dropoff(self):
        return 0

    def get_max_peaks(self):
        return 10

    def get_fudge(self):
        return 0

    def get_lesser_peak_factor(self):
        return 1


class ReservoirFiller(Filler):
    log = logging.getLogger("Wildcatting")

    def __init__(self, theme):
        assert isinstance(theme, Theme)

        self._theme = theme

    def fill(self, field):
        height, width = field.get_height(), field.get_width()
        reservoir_count = 0
        site_count = 0
        for row in range(field.get_height()):
            for col in range(field.get_width()):
                site = field.get_site(row, col)
                if not site.get_oil_flag():
                    continue
                adjacentSites = []
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

    def _get_initial_reserves(self):
        reserves = int(
            max(0.1, random.gauss(1, 1)) * self._theme.get_mean_site_reserves()
        )
        return reserves

    def _depth_bracket(self, depth):
        if depth is None:
            return -1
        return int(depth * 1.0 / 9 * 6)

    def _fill_site(self, site, adjacentSites):
        initialDepth = site.get_potential_oil_depth()
        reservoir_count = 0
        site_count = 0

        for adjacentSite in adjacentSites:
            initialReserves = self._get_initial_reserves()
            adj_depth = adjacentSite.get_potential_oil_depth()
            if self._depth_bracket(initialDepth) == self._depth_bracket(adj_depth):
                site_count += 1
                reservoir = site.get_reservoir()
                if reservoir is None:
                    reservoir_count += 1
                    reservoir = Reservoir(initialDepth, initialReserves)
                    site.set_reservoir(reservoir)

                reservoir.join(adjacentSite.get_potential_oil_depth(), initialReserves)
                adjacentSite.set_reservoir(reservoir)
            else:
                reservoir_count += 1
                site.set_reservoir(Reservoir(initialDepth, initialReserves))

        return reservoir_count, site_count


class TaxFiller:
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)

        for row in range(field.get_height()):
            for col in range(field.get_width()):
                site = field.get_site(row, col)
                site.set_tax(
                    random.randint(self._theme.get_min_tax(), self._theme.get_max_tax())
                )


class Game:
    log = logging.getLogger("Wildcatting")

    def __init__(self, width, height, turnCount=13, theme=None):
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert isinstance(turnCount, int)

        if theme is None:
            theme = DefaultTheme()

        assert isinstance(theme, Theme)

        self._turnCount = turnCount
        self._theme = theme
        self._players = {}
        self._playerOrder = []
        self._isStarted = False
        self._isFinished = False
        self._weekNum = 0
        self._clients = {}
        self._clientUpdates = {}

        self._prices = theme.get_oil_prices()

        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oilField)
        PotentialOilDepthFiller(theme).fill(self._oilField)
        ReservoirFiller(theme).fill(self._oilField)
        DrillCostFiller(theme).fill(self._oilField)
        TaxFiller(theme).fill(self._oilField)

    def _new_client_id(self):
        clientId = self._generate_secret()
        self._clientUpdates[clientId] = []
        return clientId

    def _generate_secret(self):
        return secrets.token_hex(8).upper()

    def get_client_players(self, clientId):
        return self._clients.get(clientId, [])

    def add_player(self, clientId, player):
        assert isinstance(player, wildcatting.model.Player)

        playerNames = [p.get_username() for p in list(self._players.values())]
        if player.get_username() in playerNames:
            raise WildcattingException(
                f"A user named {player.get_username()} has already joined this game"
            )

        secret = self._generate_secret()
        player.set_secret(secret)

        self._players[secret] = player
        self._playerOrder.append(player)

        self._clients.setdefault(clientId, []).append(player)

    def get_master(self):
        if len(self._playerOrder) > 0:
            return self._playerOrder[0]
        return None

    def get_player(self, username, secret):
        if not isinstance(username, str) or not isinstance(secret, str):
            raise WildcattingException("Invalid login")

        player = self._players.get(secret)

        if player is None or player.get_username() != username:
            raise WildcattingException("Invalid login")

        return player

    def get_players(self):
        # return a copy, since we don't want outside callers to be able
        # to modify the order
        return self._playerOrder[:]

    def start(self):
        self._isStarted = True
        self._next_week()

    def _next_week(self):
        self._weekNum = self._weekNum + 1

        price = next(self._prices)
        self._week = wildcatting.week.Week(self._weekNum, self._playerOrder, price)
        self._oilField.week(price, self._theme.get_well_theory(), self._weekNum)

        if self._weekNum > self._turnCount:
            self._finish()

    def get_week(self):
        return self._week

    def is_started(self):
        return self._isStarted

    def _finish(self):
        self._isFinished = True

        players = sorted(self._players.values(), key=lambda p: -p.get_profit_and_loss())

        playerStrs = [
            f"{p.get_username()} ({p.get_profit_and_loss()})" for p in players
        ]

        self.log.info("Game is finished.  Scores: %s", ", ".join(playerStrs))

    def is_finished(self):
        return self._isFinished

    def drill(self, row, col):
        site = self._oilField.get_site(row, col)
        well = site.get_well()
        foundOil, cost = well.drill(site, self._theme.get_drill_increment())
        well.get_player().expense(cost)

        if foundOil:
            site.set_oil_depth(well.get_drill_depth())
            theory = self._theme.get_well_theory()
            output = theory.start(site)
            well.set_output(output)
            well.set_initial_output(output)

        return foundOil

    def end_turn(self, player):
        self._week.end_turn(player)

        if self._week.is_finished():
            self._next_week()

    def get_weekly_summary(self):
        return wildcatting.model.WeeklySummary(self._playerOrder, self._weekNum)

    def mark_site_updated(self, player, site):
        for updateClient in self._clientUpdates:
            if player not in self._clients[updateClient]:
                updateSites = self._clientUpdates[updateClient]
                if site not in updateSites:
                    updateSites.append(site)

    def pop_updated_sites(self, clientId):
        updates = self._clientUpdates[clientId]
        self._clientUpdates[clientId] = []
        return updates

    def get_oil_price(self):
        return self._week.get_price()

    def get_oil_field(self):
        return self._oilField
