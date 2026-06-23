from dataclasses import dataclass

from wildcatting.model.oilfield import Site
from wildcatting.model.player import Player


@dataclass
class Turn:
    week: int
    player: Player
    drilled_site: Site | None = None
    surveyed_site: Site | None = None
