import logging


def main(stdscr):
    pass


class WeeklyReport:
    log = logging.getLogger("Wildcatting")

    def __init__(self, field, username, symbol, week, setting, oilPrice):
        self.username = username
        self.symbol = symbol
        self.week = week
        self._setting = setting
        self._oilPrice = oilPrice

        self.profit_and_loss = 0

        self.report_dict = self._build_report_dict(field)

    def _build_report_dict(self, field):
        sites = {}
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                well = site.well
                if well:
                    if well.player.username == self.username:
                        output = well.output
                        if output is None:
                            output = 0

                        rowDict = {}
                        rowDict["row"] = row
                        rowDict["col"] = col
                        rowDict["cost"] = well.initial_cost
                        rowDict["tax"] = site.tax
                        rowDict["income"] = int(output * self._oilPrice)
                        wellProfitAndLoss = well.profit_and_loss
                        rowDict["profitAndLoss"] = wellProfitAndLoss
                        self.profit_and_loss += wellProfitAndLoss

                        sites[well.week] = rowDict
        return sites

    @property
    def oil_price(self):
        return self._setting.price_format % self._oilPrice
