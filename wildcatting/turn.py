from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wildcatting.model.oilfield import Site
    from wildcatting.model.player import Player


class Turn:
    def __init__(self, week: int, player: Player) -> None:
        self.week: int = week
        self.player: Player = player
        self.drilled_site: Site | None = None
        self.surveyed_site: Site | None = None
