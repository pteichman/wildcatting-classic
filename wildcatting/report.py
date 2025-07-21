import logging


class WeeklyReport:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, field, username, symbol, week, setting, oilPrice):
        self._username = username
        self._symbol = symbol
        self._week = week
        self._setting = setting
        self._oilPrice = oilPrice

        self._profitAndLoss = 0
        
        self._reportDict = self._buildReportDict(field)

    def _buildReportDict(self, field):
        sites = {}
        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                well = site.getWell()
                if well:
                    if well.getPlayer().getUsername() == self._username:
                        output = well.getOutput()
                        if output is None:
                            output = 0
                        
                        rowDict = {}
                        rowDict["row"] = row
                        rowDict["col"] = col
                        rowDict["cost"] = cost = well.getInitialCost()
                        rowDict["tax"] = tax = site.getTax()
                        rowDict["income"] = income = int(output * self._oilPrice)
                        wellProfitAndLoss = well.getProfitAndLoss()
                        rowDict["profitAndLoss"] = wellProfitAndLoss
                        self._profitAndLoss += wellProfitAndLoss
                        
                        sites[well.getWeek()] = rowDict
        return sites

    def getReportDict(self):
        return self._reportDict

    def getWeek(self):
        return self._week

    def getUsername(self):
        return self._username

    def getSymbol(self):
        return self._symbol

    def getOilPrice(self):
        return self._setting.getPriceFormat() % self._oilPrice

    def getProfitAndLoss(self):
        return self._profitAndLoss
