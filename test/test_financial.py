import unittest

from wildcatting.model import Player, Site, Well
from wildcatting.reservoir import Reservoir


class TestDrilling(unittest.TestCase):
    def _make_well_on_site(self, drill_cost):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.set_drill_cost(drill_cost)
        well = Well()
        well.set_player(player)
        well.set_week(1)
        site.set_well(well)
        return site, well, player

    def test_drill_cost_charged_to_player(self):
        drill_cost = 5
        drill_increment = 10
        site, well, player = self._make_well_on_site(drill_cost)

        _, cost = well.drill(site, drill_increment)
        player.expense(cost)

        self.assertEqual(well.get_initial_cost(), drill_cost * drill_increment)
        self.assertEqual(player.get_profit_and_loss(), -(drill_cost * drill_increment))

    def test_drill_depth_increments_by_one(self):
        site, well, player = self._make_well_on_site(drill_cost=1)

        for expected_depth in range(1, 6):
            well.drill(site, 10)
            self.assertEqual(well.get_drill_depth(), expected_depth)

    def test_drill_returns_true_exactly_at_oil_depth(self):
        oil_depth = 3
        site = Site(0, 0)
        site.set_drill_cost(1)
        reservoir = Reservoir(initialDepth=oil_depth, initialReserves=500)
        site.set_reservoir(reservoir)

        player = Player("alice", "A")
        well = Well()
        well.set_player(player)
        well.set_week(1)
        site.set_well(well)

        for _ in range(oil_depth - 1):
            found, _ = well.drill(site, 10)
            self.assertFalse(found)
            self.assertIsNone(site.get_oil_depth())

        found, _ = well.drill(site, 10)
        self.assertTrue(found)
        site.set_oil_depth(well.get_drill_depth())
        self.assertEqual(site.get_oil_depth(), oil_depth)
        self.assertEqual(well.get_drill_depth(), oil_depth)

    def test_sell_returns_half_initial_cost(self):
        site, well, player = self._make_well_on_site(drill_cost=7)

        well.drill(site, 10)
        well.drill(site, 10)
        well.drill(site, 10)

        initial_cost = well.get_initial_cost()
        price = well.sell()

        self.assertEqual(price, initial_cost // 2)
        self.assertTrue(well.is_sold())

    def test_sell_credits_player_half_initial_cost(self):
        site, well, player = self._make_well_on_site(drill_cost=10)

        _, cost = well.drill(site, 10)
        player.expense(cost)
        pnl_after_drill = player.get_profit_and_loss()

        initial_cost = well.get_initial_cost()
        price = well.sell()
        player.income(price)

        self.assertEqual(
            player.get_profit_and_loss(), pnl_after_drill + initial_cost // 2
        )


class TestPlayerAccounting(unittest.TestCase):
    def test_pnl_is_income_minus_expenses(self):
        player = Player("alice", "A")
        player.income(100)
        player.expense(30)
        player.income(50)
        player.expense(20)
        self.assertEqual(player.get_profit_and_loss(), 100)

    def test_weekly_income_applied_to_player(self):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.set_tax(5)
        well = Well()
        well.set_player(player)
        well.set_week(1)
        well.set_output(10.0)
        site.set_well(well)

        well.week(site, oilPrice=2.0)

        self.assertEqual(player.get_profit_and_loss(), int(10.0 * 2.0) - 5)

    def test_weekly_tax_charged_without_output(self):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.set_tax(100)
        well = Well()
        well.set_player(player)
        well.set_week(1)
        # output is None by default — no oil found yet
        site.set_well(well)

        well.week(site, oilPrice=5.0)

        self.assertEqual(player.get_profit_and_loss(), -100)

    def test_sold_well_skips_weekly_income_and_tax(self):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.set_tax(500)
        well = Well()
        well.set_player(player)
        well.set_week(1)
        well.set_output(50.0)
        well._sold = True
        site.set_well(well)

        pnl_before = player.get_profit_and_loss()
        well.week(site, oilPrice=5.0)

        self.assertEqual(player.get_profit_and_loss(), pnl_before)


if __name__ == "__main__":
    unittest.main()
