from __future__ import annotations

from typing import TYPE_CHECKING

from .serialize import Serializable

if TYPE_CHECKING:
    from .oilfield import Site


class Update(Serializable):
    def __init__(
        self,
        week: int,
        oilPrice: float,
        playersTurn: str | None,
        pendingPlayers: list[str],
        gameFinished: bool,
        sites: list[Site],
    ) -> None:
        self.week = week
        self.oil_price = oilPrice
        self.players_turn = playersTurn
        self.pending_players = pendingPlayers
        self.game_finished = gameFinished
        self.sites = sites
