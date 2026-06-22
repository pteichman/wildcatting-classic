# vulture allowlist — names referenced dynamically or via framework introspection

from wildcatting.cmdparse import Command, CommandParser
from wildcatting.server import StandaloneServer

# OptionParser overrides: called polymorphically by the parent class
Command("").set_usage(None)
Command("").get_usage()

# CommandParser public API (not called internally but part of the public interface)
CommandParser().check_required("")

# StandaloneServer.admin: stored for the lifetime of the server object
StandaloneServer().admin

# client._wildcatting_view: holds a reference to keep the view alive
from wildcatting.client import ClientRunner  # type: ignore[attr-defined]

ClientRunner()._wildcatting_view  # type: ignore[attr-defined]

# Interface methods on PeakedFiller subclasses — defined but not yet called by base class
from wildcatting.game import DrillCostFiller, OilFiller, PotentialOilDepthFiller

OilFiller(None).get_min_dropoff()  # type: ignore[arg-type]
OilFiller(None).get_max_dropoff()  # type: ignore[arg-type]
DrillCostFiller(None).get_min_dropoff()  # type: ignore[arg-type]
DrillCostFiller(None).get_max_dropoff()  # type: ignore[arg-type]
PotentialOilDepthFiller(None).get_min_dropoff()  # type: ignore[arg-type]
PotentialOilDepthFiller(None).get_max_dropoff()  # type: ignore[arg-type]

# ThemeInfo: found via add_commands() which uses inspect.getmembers() on the module
from wildcatting.ThemeInfoCommand import ThemeInfo

ThemeInfo()

# Dead classes kept in-tree — candidates for removal
from wildcatting.oilprices import HistoricalGaussianPrices, HistoricalPrices
from wildcatting.ReportCommand import ReportCommand

HistoricalPrices(0)
HistoricalGaussianPrices(0, 0, 0)  # type: ignore[call-arg]
ReportCommand()

# Well.initial_output: set in game.py and tests but never read — candidate for removal
from wildcatting.model.oilfield import Well

Well(0, None).initial_output  # type: ignore[arg-type]
