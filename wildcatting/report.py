import logging


class WeeklyReport:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, field, username, symbol, week, setting):
        self._username = username
        self._symbol = symbol
        self._week = week
        self._setting = setting
        
        self._reportDict = self._buildReportDict(field, username)

    def _buildReportDict(self, field, username):
        sites = {}
        oilPrice = 97
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                well = site.getWell()
                if well:
                    if well.getPlayer().getUsername() == username:
                        output = well.getOutput()
                        if output is None:
                            output = 0
                        
                        rowDict = {}
                        # we need this for the color, perhaps we can put the bracket here instead?
                        rowDict["site"] = site
                        rowDict["row"] = row
                        rowDict["col"] = col
                        rowDict["cost"] = cost = site.getDrillCost() * well.getDrillDepth() * self._setting.getDrillIncrement()
                        rowDict["tax"] = tax = site.getTax()
                        rowDict["income"] = income = output * oilPrice
                        rowDict["profitAndLoss"] = (income - tax) * (self._week - well.getWeek() + 1) - cost
                        
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
