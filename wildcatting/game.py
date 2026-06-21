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


class Filler:
    def fill(self, field):
        raise NotImplementedError("UnimplementedAbstractMethod")


class PeakedFiller(Filler):
    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)
        peaks = self._generatePeaks(field)
        self._fillModel(field, peaks)

    def _cellRoll(self):
        return None

    def _fillModel(self, model, peaks):
        for row in range(model.getHeight()):
            for col in range(model.getWidth()):
                # calculate sum of distances from peak
                minc = 99999
                for p in range(len(peaks)):
                    (y, x) = peaks[p]

                    a = row - y
                    b = col - x
                    c = math.sqrt(a * a + b * b)
                    minc = min(c, minc)
                    if c == minc:
                        closest = p

                minValue, maxValue = self.getValueRange()
                lesserPeakFactor = self.getLesserPeakFactor()
                fudge = self.getFudge()
                field_size = math.sqrt(model.getWidth() * model.getHeight())
                d = (minc + random.random() * fudge) / field_size
                e = max(0.001, d)
                f = 1 - max(min((math.log(e) + 3) / 3, 1.0), 0)
                peakHeight = maxValue - minValue
                value = int(
                    f * peakHeight - closest * random.random() * lesserPeakFactor
                )
                value = max(minValue, value)
                value = min(maxValue, value)

                roll = self._cellRoll()
                site = model.getSite(row, col)
                self.fillSite(site, value, roll)

    def _generatePeaks(self, model):
        minValue, maxValue = self.getValueRange()
        maxPeaks = self.getMaxPeaks()
        peaks = [None] * random.randint(1, maxPeaks)
        for i in range(len(peaks)):
            peaks[i] = (
                random.randint(0, model.getHeight()),
                random.randint(0, model.getWidth()),
            )
        return peaks

    def getValueRange(self):
        raise NotImplementedError("AbstractMethodNotImplemented")

    def fillSite(self, site, value, roll):
        raise NotImplementedError("AbstractMethodNotImplemented")


class OilFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def getValueRange(self):
        return (10, 100)

    def _cellRoll(self):
        return random.randint(0, 100)

    def fillSite(self, site, value, roll):
        site.setProbability(value)
        if roll < value:
            site.setOilFlag(True)

    def getMinDropoff(self):
        return self._theme.getOilMinDropoff()

    def getMaxDropoff(self):
        return self._theme.getOilMaxDropoff()

    def getMaxPeaks(self):
        return self._theme.getOilMaxPeaks()

    def getFudge(self):
        return self._theme.getOilFudge()

    def getLesserPeakFactor(self):
        return self._theme.getOilLesserPeakFactor()


class DrillCostFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def getValueRange(self):
        return (self._theme.getMinDrillCost(), self._theme.getMaxDrillCost())

    def fillSite(self, site, discount, roll):
        site.setDrillCost(self._theme.getMaxDrillCost() - discount)

    def getMinDropoff(self):
        return self._theme.getDrillCostMinDropoff()

    def getMaxDropoff(self):
        return self._theme.getDrillCostMaxDropoff()

    def getMaxPeaks(self):
        return self._theme.getDrillCostMaxPeaks()

    def getFudge(self):
        return self._theme.getDrillCostFudge()

    def getLesserPeakFactor(self):
        return self._theme.getDrillCostLesserPeakFactor()


class PotentialOilDepthFiller(PeakedFiller):
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def getValueRange(self):
        return (1, 10)

    def fillSite(self, site, value, roll):
        if site.getOilFlag():
            site.setPotentialOilDepth(11 - value)

    def getMinDropoff(self):
        return 0

    def getMaxDropoff(self):
        return 0

    def getMaxPeaks(self):
        return 10

    def getFudge(self):
        return 0

    def getLesserPeakFactor(self):
        return 1


class ReservoirFiller(Filler):
    log = logging.getLogger("Wildcatting")

    def __init__(self, theme):
        assert isinstance(theme, Theme)

        self._theme = theme

    def fill(self, field):
        height, width = field.getHeight(), field.getWidth()
        reservoir_count = 0
        site_count = 0
        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                if not site.getOilFlag():
                    continue
                adjacentSites = []
                for adjacentRow, adjacentCol in [(row + 1, col), (row, col + 1)]:
                    if adjacentRow >= height or adjacentCol >= width:
                        continue

                    adjacentSite = field.getSite(adjacentRow, adjacentCol)
                    adjacentSites.append(adjacentSite)
                dr, ds = self._fillSite(site, adjacentSites)
                reservoir_count += dr
                site_count += ds

        self.log.info(
            "Created %d reservoirs covering %d sites", reservoir_count, site_count
        )

    def _getInitialReserves(self):
        reserves = int(max(0.1, random.gauss(1, 1)) * self._theme.getMeanSiteReserves())
        return reserves

    def _depthBracket(self, depth):
        if depth is None:
            return -1
        return int(depth * 1.0 / 9 * 6)

    def _fillSite(self, site, adjacentSites):
        initialDepth = site.getPotentialOilDepth()
        reservoir_count = 0
        site_count = 0

        for adjacentSite in adjacentSites:
            initialReserves = self._getInitialReserves()
            adj_depth = adjacentSite.getPotentialOilDepth()
            if self._depthBracket(initialDepth) == self._depthBracket(adj_depth):
                site_count += 1
                reservoir = site.getReservoir()
                if reservoir is None:
                    reservoir_count += 1
                    reservoir = Reservoir(initialDepth, initialReserves)
                    site.setReservoir(reservoir)

                reservoir.join(adjacentSite.getPotentialOilDepth(), initialReserves)
                adjacentSite.setReservoir(reservoir)
            else:
                reservoir_count += 1
                site.setReservoir(Reservoir(initialDepth, initialReserves))

        return reservoir_count, site_count


class TaxFiller:
    def __init__(self, theme):
        assert isinstance(theme, Theme)
        self._theme = theme

    def fill(self, field):
        assert isinstance(field, wildcatting.model.OilField)

        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                site.setTax(
                    random.randint(self._theme.getMinTax(), self._theme.getMaxTax())
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

        self._prices = theme.getOilPrices()

        self._oilField = wildcatting.model.OilField(width, height)
        OilFiller(theme).fill(self._oilField)
        PotentialOilDepthFiller(theme).fill(self._oilField)
        ReservoirFiller(theme).fill(self._oilField)
        DrillCostFiller(theme).fill(self._oilField)
        TaxFiller(theme).fill(self._oilField)

    def _newClientId(self):
        clientId = self._generateSecret()
        self._clientUpdates[clientId] = []
        return clientId

    def _generateSecret(self):
        return secrets.token_hex(8).upper()

    def getClientPlayers(self, clientId):
        return self._clients.get(clientId, [])

    def addPlayer(self, clientId, player):
        assert isinstance(player, wildcatting.model.Player)

        playerNames = [p.getUsername() for p in list(self._players.values())]
        if player.getUsername() in playerNames:
            raise WildcattingException(
                f"A user named {player.getUsername()} has already joined this game"
            )

        secret = self._generateSecret()
        player.setSecret(secret)

        self._players[secret] = player
        self._playerOrder.append(player)

        self._clients.setdefault(clientId, []).append(player)

    def getMaster(self):
        if len(self._playerOrder) > 0:
            return self._playerOrder[0]
        return None

    def getPlayer(self, username, secret):
        if not isinstance(username, str) or not isinstance(secret, str):
            raise WildcattingException("Invalid login")

        player = self._players.get(secret)

        if player is None or player.getUsername() != username:
            raise WildcattingException("Invalid login")

        return player

    def getPlayers(self):
        # return a copy, since we don't want outside callers to be able
        # to modify the order
        return self._playerOrder[:]

    def start(self):
        self._isStarted = True
        self._nextWeek()

    def _nextWeek(self):
        self._weekNum = self._weekNum + 1

        price = next(self._prices)
        self._week = wildcatting.week.Week(self._weekNum, self._playerOrder, price)
        self._oilField.week(price, self._theme.getWellTheory(), self._weekNum)

        if self._weekNum > self._turnCount:
            self._finish()

    def getWeek(self):
        return self._week

    def isStarted(self):
        return self._isStarted

    def _finish(self):
        self._isFinished = True

        players = sorted(self._players.values(), key=lambda p: -p.getProfitAndLoss())

        playerStrs = [f"{p.getUsername()} ({p.getProfitAndLoss()})" for p in players]

        self.log.info("Game is finished.  Scores: %s", ", ".join(playerStrs))

    def isFinished(self):
        return self._isFinished

    def drill(self, row, col):
        site = self._oilField.getSite(row, col)
        well = site.getWell()
        foundOil, cost = well.drill(site, self._theme.getDrillIncrement())
        well.getPlayer().expense(cost)

        if foundOil:
            site.setOilDepth(well.getDrillDepth())
            theory = self._theme.getWellTheory()
            output = theory.start(site)
            well.setOutput(output)
            well.setInitialOutput(output)

        return foundOil

    def endTurn(self, player):
        self._week.endTurn(player)

        if self._week.isFinished():
            self._nextWeek()

    def getWeeklySummary(self):
        return wildcatting.model.WeeklySummary(self._playerOrder, self._weekNum)

    def markSiteUpdated(self, player, site):
        for updateClient in self._clientUpdates:
            if player not in self._clients[updateClient]:
                updateSites = self._clientUpdates[updateClient]
                if site not in updateSites:
                    updateSites.append(site)

    def popUpdatedSites(self, clientId):
        updates = self._clientUpdates[clientId]
        self._clientUpdates[clientId] = []
        return updates

    def getOilPrice(self):
        return self._week.getPrice()

    def getOilField(self):
        return self._oilField
