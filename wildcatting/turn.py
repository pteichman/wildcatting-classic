from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wildcatting.model.oilfield import Site
    from wildcatting.model.player import Player


class Turn:
    def __init__(self) -> None:
        self.week: int = 0
        self.player: Player | None = None
        self.drilled_site: Site | None = None
        self.surveyed_site: Site | None = None
