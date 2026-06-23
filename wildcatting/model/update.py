from .oilfield import Site
from .serialize import Serializable


class Update(Serializable):
    def __init__(
        self,
        week: int,
        oil_price: float,
        players_turn: str | None,
        pending_players: list[str],
        game_finished: bool,
        sites: list[Site],
    ) -> None:
        self.week = week
        self.oil_price = oil_price
        self.players_turn = players_turn
        self.pending_players = pending_players
        self.game_finished = game_finished
        self.sites = sites
