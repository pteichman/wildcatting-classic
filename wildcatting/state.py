from typing import NamedTuple

from wildcatting.model import OilField, Site, Update


class UpdateResult(NamedTuple):
    updated: bool
    week_updated: bool


class Wildcatting:
    def __init__(self) -> None:
        self.player_field: OilField | None = None
        self.week: int = 0
        self.oil_price: float = 0
        self.players_turn: str | None = None
        self.pending_players: list[str] = []
        self.game_finished: bool = False

    def update_player_field(self, site: Site) -> None:
        assert self.player_field is not None
        self.player_field.set_site(site.row, site.col, site)

    def update(self, update: Update) -> UpdateResult:
        game_finished = update.game_finished
        week = update.week
        players_turn = update.players_turn
        pending_players = update.pending_players
        oil_price = update.oil_price
        sites = update.sites

        updated = (
            len(sites) > 0
            or week > self.week
            or oil_price != self.oil_price
            or players_turn != self.players_turn
            or game_finished
        )
        week_updated = week > self.week

        for site in sites:
            self.update_player_field(site)

        self.week = week
        self.players_turn = players_turn
        self.pending_players = pending_players
        self.game_finished = game_finished
        self.oil_price = oil_price

        return UpdateResult(updated, week_updated)
