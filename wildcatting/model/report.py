from serialize import Serializable

import logging


class WeeklySummary(Serializable):
    def __init__(self, playerOrder, week):
        self._playerOrder = playerOrder
        self._week = week

        self._reportRows = self._buildReportRows()

    def _buildReportRows(self):
        rows = []
        for player in self._playerOrder:
            rows.append({"username": player.getUsername(), "profitAndLoss": player.getProfitAndLoss()})
        return rows

    def getWeek(self):
        return self._week

    def setWeek(self, week):
        self._week = week

    def getReportRows(self):
        return self._reportRows

    def setReportRows(self, reportRows):
        self._reportRows = reportRows
