from typing import TYPE_CHECKING, Any

from .serialize import Serializable

if TYPE_CHECKING:
    from .player import Player


class WeeklySummary(Serializable):
    def __init__(self, player_order: list[Player], week: int) -> None:
        self._player_order = player_order
        self.week = week

        self.report_rows = self._build_report_rows()

    def _build_report_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        max_profit_and_loss: int | None = None
        for player in self._player_order:
            profit_and_loss = player.profit_and_loss
            if max_profit_and_loss is None or profit_and_loss > max_profit_and_loss:
                max_profit_and_loss = profit_and_loss
        for player in self._player_order:
            profit_and_loss = player.profit_and_loss
            row: dict[str, Any] = {
                "username": player.username,
                "profitAndLoss": profit_and_loss,
                "leader": (profit_and_loss == max_profit_and_loss),
            }
            rows.append(row)
        return rows
