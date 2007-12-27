import logging


class WeeklyReport:
    log = logging.getLogger("Wildcatting")
    
    def __init__(self, field, username, symbol, week):
        self._username = username
        self._symbol = symbol
        self._week = week
        
        self._reportDict = self._buildReportDict(field, username)

    def _buildReportDict(self, field, username):
        sites = {}
        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)
                well = site.getWell()
                if well:
                    if well.getPlayer().getUsername() == username:
                        rowDict = {}
                        # we need this for the color, perhaps we can put the bracket here instead?
                        rowDict["site"] = site
                        rowDict["row"] = row
                        rowDict["col"] = col
                        # FIXME multiply drillCost by depth to get cost
                        rowDict["cost"] = site.getDrillCost()
                        rowDict["tax"] = site.getTax()
                        rowDict["income"] = 0
                        rowDict["profitAndLoss"] = 0
                        
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
