from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wildcatting.model.oilfield import OilField
    from wildcatting.model.setting import Setting


def main(stdscr: Any) -> None:
    pass


class WeeklyReport:
    log = logging.getLogger("Wildcatting")

    def __init__(
        self,
        field: OilField,
        username: str,
        symbol: str,
        week: int,
        setting: Setting,
        oil_price: float,
    ) -> None:
        self.username = username
        self.symbol = symbol
        self.week = week
        self._setting = setting
        self._oil_price = oil_price

        self.profit_and_loss: int = 0

        self.report_dict = self._build_report_dict(field)

    def _build_report_dict(self, field: OilField) -> dict[int | None, dict[str, Any]]:
        sites: dict[int | None, dict[str, Any]] = {}
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                well = site.well
                if well:
                    if (
                        well.player is not None
                        and well.player.username == self.username
                    ):
                        output = well.output
                        if output is None:
                            output = 0

                        row_dict: dict[str, Any] = {}
                        row_dict["row"] = row
                        row_dict["col"] = col
                        row_dict["cost"] = well.initial_cost
                        row_dict["tax"] = site.tax
                        row_dict["income"] = int(output * self._oil_price)
                        well_profit_and_loss = well.profit_and_loss
                        row_dict["profitAndLoss"] = well_profit_and_loss
                        self.profit_and_loss += well_profit_and_loss

                        sites[well.week] = row_dict
        return sites

    @property
    def oil_price(self) -> str:
        return self._setting.price_format % self._oil_price
