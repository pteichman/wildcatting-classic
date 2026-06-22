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
        for row in range(field.get_height()):
            for col in range(field.get_width()):
                site = field.get_site(row, col)
                well = site.get_well()
                if well:
                    if well.get_player().get_username() == self._username:
                        output = well.get_output()
                        if output is None:
                            output = 0

                        rowDict = {}
                        rowDict["row"] = row
                        rowDict["col"] = col
                        rowDict["cost"] = well.get_initial_cost()
                        rowDict["tax"] = site.get_tax()
                        rowDict["income"] = int(output * self._oilPrice)
                        wellProfitAndLoss = well.get_profit_and_loss()
                        rowDict["profitAndLoss"] = wellProfitAndLoss
                        self._profitAndLoss += wellProfitAndLoss

                        sites[well.get_week()] = rowDict
        return sites

    def get_report_dict(self):
        return self._reportDict

    def get_week(self):
        return self._week

    def get_username(self):
        return self._username

    def get_symbol(self):
        return self._symbol

    def get_oil_price(self):
        return self._setting.get_price_format() % self._oilPrice

    def get_profit_and_loss(self):
        return self._profitAndLoss
