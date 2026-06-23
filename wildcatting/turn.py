from dataclasses import dataclass

from wildcatting.model import Player, Site


@dataclass
class Turn:
    week: int
    player: Player
    drilled_site: Site | None = None
    surveyed_site: Site | None = None
