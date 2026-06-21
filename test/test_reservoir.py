import unittest

from wildcatting.model import Player, Site, Well
from wildcatting.oilprices import GaussianPrices
from wildcatting.reservoir import Reservoir
from wildcatting.welltheory import SimpleWellTheory


class TestReservoir(unittest.TestCase):
    def test_pump_forbids_drawing_last_barrel(self):
        reservoir = Reservoir(initialDepth=5, initialReserves=10)
        reservoir.pump(9)  # leaves 1 barrel
        with self.assertRaises(AssertionError):
            reservoir.pump(1)  # 1 is not < 1

    def test_ratio_pumped_monotonically_increases(self):
        reservoir = Reservoir(initialDepth=5, initialReserves=100)
        prev = reservoir.ratioPumped()
        self.assertEqual(prev, 0.0)

        for barrels in [20, 15, 10, 5]:
            reservoir.pump(barrels)
            current = reservoir.ratioPumped()
            self.assertGreater(current, prev)
            self.assertLess(current, 1.0)
            prev = current

    def test_join_averages_oil_depth(self):
        reservoir = Reservoir(initialDepth=4, initialReserves=100)
        reservoir.join(6, 100)
        self.assertEqual(reservoir.getOilDepth(), 5)  # floor((4+6)/2)


class TestWellOutputBounds(unittest.TestCase):
    def _make_producing_site(self, reserves, max_output=66):
        player = Player("alice", "A")
        site = Site(0, 0)
        site.setTax(0)
        reservoir = Reservoir(initialDepth=5, initialReserves=reserves)
        site.setReservoir(reservoir)
        well = Well()
        well.setPlayer(player)
        well.setWeek(1)
        site.setWell(well)
        return site, well, reservoir

    def test_initial_output_never_exceeds_half_reserves(self):
        site, well, reservoir = self._make_producing_site(reserves=100)
        output = SimpleWellTheory(66).start(site)
        well.setOutput(output)
        well.setInitialOutput(output)

        self.assertIsNotNone(well.getOutput())
        self.assertLessEqual(well.getOutput(), reservoir.getReserves() / 2.0)

    def test_weekly_output_never_overdrafts_reservoir(self):
        # Runs 20 simulated weekly ticks and verifies pump() never raises.
        site, well, reservoir = self._make_producing_site(reserves=1000)
        theory = SimpleWellTheory(66)
        output = theory.start(site)
        well.setOutput(output)
        well.setInitialOutput(output)

        for week_num in range(1, 21):
            output, capacity = theory.week(site, week_num)
            well.setOutput(output)
            well.setCapacity(capacity)
            if output is not None and output > 0:
                self.assertLess(
                    output,
                    reservoir.getReserves(),
                    f"Week {week_num}: output {output:.2f} >= reserves "
                    f"{reservoir.getReserves():.2f}",
                )
            well.week(site, oilPrice=4.50)


class TestOilPriceFloor(unittest.TestCase):
    def test_gaussian_prices_never_below_floor(self):
        # Extreme downward bias to stress-test the floor.
        prices = GaussianPrices(start=0.05, mu=-50.0, sigma=100.0)
        for _ in range(1000):
            self.assertGreaterEqual(next(prices), 0.01)


if __name__ == "__main__":
    unittest.main()
