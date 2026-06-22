from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .serialize import Serializable

if TYPE_CHECKING:
    from .player import Player


class WeeklySummary(Serializable):
    def __init__(self, playerOrder: list[Player], week: int) -> None:
        self._playerOrder = playerOrder
        self.week = week

        self.report_rows = self._build_report_rows()

    def _build_report_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        maxProfitAndLoss: int | None = None
        for player in self._playerOrder:
            profitAndLoss = player.profit_and_loss
            if maxProfitAndLoss is None or profitAndLoss > maxProfitAndLoss:
                maxProfitAndLoss = profitAndLoss
        for player in self._playerOrder:
            profitAndLoss = player.profit_and_loss
            row: dict[str, Any] = {
                "username": player.username,
                "profitAndLoss": profitAndLoss,
                "leader": (profitAndLoss == maxProfitAndLoss),
            }
            rows.append(row)
        return rows
