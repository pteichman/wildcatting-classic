from .serialize import Serializable


class WeeklySummary(Serializable):
    def __init__(self, playerOrder, week):
        self._playerOrder = playerOrder
        self.week = week

        self.report_rows = self._build_report_rows()

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
