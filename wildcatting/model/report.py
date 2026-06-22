from .serialize import Serializable


class WeeklySummary(Serializable):
    def __init__(self, playerOrder, week):
        self._playerOrder = playerOrder
        self._week = week

        self._reportRows = self._build_report_rows()

    def _build_report_rows(self):
        rows = []
        maxProfitAndLoss = None
        for player in self._playerOrder:
            profitAndLoss = player.profit_and_loss
            if maxProfitAndLoss is None or profitAndLoss > maxProfitAndLoss:
                maxProfitAndLoss = profitAndLoss
        for player in self._playerOrder:
            profitAndLoss = player.profit_and_loss
            row = {
                "username": player.username,
                "profitAndLoss": profitAndLoss,
                "leader": (profitAndLoss == maxProfitAndLoss),
            }
            rows.append(row)
        return rows

    @property
    def week(self):
        return self._week

    @week.setter
    def week(self, week):
        self._week = week

    @property
    def report_rows(self):
        return self._reportRows

    @report_rows.setter
    def report_rows(self, reportRows):
        self._reportRows = reportRows
