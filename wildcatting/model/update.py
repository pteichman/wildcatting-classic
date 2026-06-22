from .serialize import Serializable


class Update(Serializable):
    def __init__(
        self, week, oilPrice, playersTurn, pendingPlayers, gameFinished, sites
    ):
        self.week = week
        self.oil_price = oilPrice
        self.players_turn = playersTurn
        self.pending_players = pendingPlayers
        self.game_finished = gameFinished
        self.sites = sites
