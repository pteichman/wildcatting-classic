from wildcatting.model import Player, Site, Well
from wildcatting.reservoir import Reservoir


class TestDrilling:
    def _make_well_on_site(self, drill_cost: int) -> tuple[Site, Well, Player]:
        player = Player("alice", "A")
        site = Site(0, 0)
        site.drill_cost = drill_cost
        well = Well(week=1, player=player)
        site.well = well
        return site, well, player

    def test_drill_cost_charged_to_player(self) -> None:
        drill_cost = 5
        drill_increment = 10
        site, well, player = self._make_well_on_site(drill_cost)

        _, cost = well.drill(site, drill_increment)
        player.expense(cost)

        assert well.initial_cost == drill_cost * drill_increment
        assert player.profit_and_loss == -(drill_cost * drill_increment)

    def test_drill_depth_increments_by_one(self) -> None:
        site, well, player = self._make_well_on_site(drill_cost=1)

        for expected_depth in range(1, 6):
            well.drill(site, 10)
            assert well.drill_depth == expected_depth

    def test_drill_returns_true_exactly_at_oil_depth(self) -> None:
        oil_depth = 3
        site = Site(0, 0)
        site.drill_cost = 1
        reservoir = Reservoir(initial_depth=oil_depth, initial_reserves=500)
        site.reservoir = reservoir

        player = Player("alice", "A")
        well = Well(week=1, player=player)
        site.well = well

        for _ in range(oil_depth - 1):
            found, _ = well.drill(site, 10)
            assert not found
            assert site.oil_depth is None

        found, _ = well.drill(site, 10)
        assert found
        site.oil_depth = well.drill_depth
        assert site.oil_depth == oil_depth
        assert well.drill_depth == oil_depth

    def test_sell_returns_half_initial_cost(self) -> None:
        site, well, player = self._make_well_on_site(drill_cost=7)

        well.drill(site, 10)
        well.drill(site, 10)
        well.drill(site, 10)

        initial_cost = well.initial_cost
        price = well.sell()

        assert price == initial_cost // 2
        assert well.sold

    def test_sell_credits_player_half_initial_cost(self) -> None:
        site, well, player = self._make_well_on_site(drill_cost=10)

        _, cost = well.drill(site, 10)
        player.expense(cost)
        pnl_after_drill = player.profit_and_loss

        initial_cost = well.initial_cost
        price = well.sell()
        player.income(price)

        assert player.profit_and_loss == pnl_after_drill + initial_cost // 2


class TestPlayerAccounting:
    def test_pnl_is_income_minus_expenses(self) -> None:
        player = Player("alice", "A")
        player.income(100)
        player.expense(30)
        player.income(50)
        player.expense(20)
        assert player.profit_and_loss == 100

    def test_weekly_income_applied_to_player(self) -> None:
        player = Player("alice", "A")
        site = Site(0, 0)
        site.tax = 5
        well = Well(week=1, player=player)
        well.output = 10.0
        site.well = well

        well.tick(site, oil_price=2.0)

        assert player.profit_and_loss == int(10.0 * 2.0) - 5

    def test_weekly_tax_charged_without_output(self) -> None:
        player = Player("alice", "A")
        site = Site(0, 0)
        site.tax = 100
        well = Well(week=1, player=player)
        # output is None by default — no oil found yet
        site.well = well

        well.tick(site, oil_price=5.0)

        assert player.profit_and_loss == -100

    def test_sold_well_skips_weekly_income_and_tax(self) -> None:
        player = Player("alice", "A")
        site = Site(0, 0)
        site.tax = 500
        well = Well(week=1, player=player)
        well.output = 50.0
        well.sold = True
        site.well = well

        pnl_before = player.profit_and_loss
        well.tick(site, oil_price=5.0)

        assert player.profit_and_loss == pnl_before
