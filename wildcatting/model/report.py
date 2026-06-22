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
            profitAndLoss = player.get_profit_and_loss()
            if maxProfitAndLoss is None or profitAndLoss > maxProfitAndLoss:
                maxProfitAndLoss = profitAndLoss
        for player in self._playerOrder:
            profitAndLoss = player.get_profit_and_loss()
            row = {
                "username": player.get_username(),
                "profitAndLoss": profitAndLoss,
                "leader": (profitAndLoss == maxProfitAndLoss),
            }
            rows.append(row)
        return rows

    def get_week(self):
        return self._week

    def set_week(self, week):
        self._week = week

    def get_report_rows(self):
        return self._reportRows

    def set_report_rows(self, reportRows):
        self._reportRows = reportRows
