from .serialize import Serializable

import logging


class WeeklySummary(Serializable):
    def __init__(self, playerOrder, week):
        self._playerOrder = playerOrder
        self._week = week

        self._reportRows = self._buildReportRows()

    def _buildReportRows(self):
        rows = []
        maxProfitAndLoss = None
        for player in self._playerOrder:
            profitAndLoss = player.getProfitAndLoss()
            if maxProfitAndLoss is None or profitAndLoss > maxProfitAndLoss:
                maxProfitAndLoss = profitAndLoss
        for player in self._playerOrder:
            profitAndLoss = player.getProfitAndLoss()
            row = {"username": player.getUsername(), "profitAndLoss": profitAndLoss, "leader": (profitAndLoss == maxProfitAndLoss)}
            rows.append(row)
        return rows

    def getWeek(self):
        return self._week

    def setWeek(self, week):
        self._week = week

    def getReportRows(self):
        return self._reportRows

    def setReportRows(self, reportRows):
        self._reportRows = reportRows
