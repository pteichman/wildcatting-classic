import unittest

from wildcatting.model import Player, Site, Well
from wildcatting.reservoir import Reservoir


class TestDrilling(unittest.TestCase):
    def _make_well_on_site(self, drill_cost):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.setDrillCost(drill_cost)
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        site.setWell(well)
        return site, well, player

    def test_drill_cost_charged_to_player(self):
        drill_cost = 5
        drill_increment = 10
        site, well, player = self._make_well_on_site(drill_cost)

        _, cost = well.drill(site, drill_increment)
        player.expense(cost)

        self.assertEqual(well.getInitialCost(), drill_cost * drill_increment)
        self.assertEqual(player.getProfitAndLoss(), -(drill_cost * drill_increment))

    def test_drill_depth_increments_by_one(self):
        site, well, player = self._make_well_on_site(drill_cost=1)

        for expected_depth in range(1, 6):
            well.drill(site, 10)
            self.assertEqual(well.getDrillDepth(), expected_depth)

    def test_drill_returns_true_exactly_at_oil_depth(self):
        oil_depth = 3
        site = Site(0, 0)
        site.setDrillCost(1)
        reservoir = Reservoir(initialDepth=oil_depth, initialReserves=500)
        site.setReservoir(reservoir)

        player = Player("alice", "A")
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        site.setWell(well)

        for _ in range(oil_depth - 1):
            found, _ = well.drill(site, 10)
            self.assertFalse(found)
            self.assertIsNone(site.getOilDepth())

        found, _ = well.drill(site, 10)
        self.assertTrue(found)
        site.setOilDepth(well.getDrillDepth())
        self.assertEqual(site.getOilDepth(), oil_depth)
        self.assertEqual(well.getDrillDepth(), oil_depth)

    def test_sell_returns_half_initial_cost(self):
        site, well, player = self._make_well_on_site(drill_cost=7)

        well.drill(site, 10)
        well.drill(site, 10)
        well.drill(site, 10)

        initial_cost = well.getInitialCost()
        price = well.sell()

        self.assertEqual(price, initial_cost // 2)
        self.assertTrue(well.isSold())

    def test_sell_credits_player_half_initial_cost(self):
        site, well, player = self._make_well_on_site(drill_cost=10)

        _, cost = well.drill(site, 10)
        player.expense(cost)
        pnl_after_drill = player.getProfitAndLoss()

        initial_cost = well.getInitialCost()
        price = well.sell()
        player.income(price)

        self.assertEqual(player.getProfitAndLoss(), pnl_after_drill + initial_cost // 2)


class TestPlayerAccounting(unittest.TestCase):
    def test_pnl_is_income_minus_expenses(self):
        player = Player("alice", "A")
        player.income(100)
        player.expense(30)
        player.income(50)
        player.expense(20)
        self.assertEqual(player.getProfitAndLoss(), 100)

    def test_weekly_income_applied_to_player(self):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.setTax(5)
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        well.setOutput(10.0)
        site.setWell(well)

        well.week(site, oilPrice=2.0)

        self.assertEqual(player.getProfitAndLoss(), int(10.0 * 2.0) - 5)

    def test_weekly_tax_charged_without_output(self):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.setTax(100)
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        # output is None by default — no oil found yet
        site.setWell(well)

        well.week(site, oilPrice=5.0)

        self.assertEqual(player.getProfitAndLoss(), -100)

    def test_sold_well_skips_weekly_income_and_tax(self):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.setTax(500)
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        well.setOutput(50.0)
        well._sold = True
        site.setWell(well)

        pnl_before = player.getProfitAndLoss()
        well.week(site, oilPrice=5.0)

        self.assertEqual(player.getProfitAndLoss(), pnl_before)


if __name__ == "__main__":
    unittest.main()
