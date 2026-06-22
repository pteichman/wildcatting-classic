import logging


def main(stdscr):
    pass


class WeeklyReport:
    log = logging.getLogger("Wildcatting")

    def __init__(self, field, username, symbol, week, setting, oilPrice):
        self._username = username
        self._symbol = symbol
        self._week = week
        self._setting = setting
        self._oilPrice = oilPrice

        self._profitAndLoss = 0

        self._reportDict = self._build_report_dict(field)

    def _build_report_dict(self, field):
        sites = {}
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                well = site.well
                if well:
                    if well.player.username == self._username:
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
                        self._profitAndLoss += wellProfitAndLoss

                        sites[well.week] = rowDict
        return sites

    @property
    def report_dict(self):
        return self._reportDict

    @property
    def week(self):
        return self._week

    @property
    def username(self):
        return self._username

    @property
    def symbol(self):
        return self._symbol

    @property
    def oil_price(self):
        return self._setting.price_format % self._oilPrice

    @property
    def profit_and_loss(self):
        return self._profitAndLoss
