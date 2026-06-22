import unittest

from wildcatting.model import Player, Site, Well
from wildcatting.oilprices import GaussianPrices
from wildcatting.reservoir import Reservoir
from wildcatting.welltheory import SimpleWellTheory


class TestReservoir(unittest.TestCase):
    def test_pump_forbids_drawing_last_barrel(self) -> None:
        reservoir = Reservoir(initialDepth=5, initialReserves=10)
        reservoir.pump(9)  # leaves 1 barrel
        with self.assertRaises(AssertionError):
            reservoir.pump(1)  # 1 is not < 1

    def test_ratio_pumped_monotonically_increases(self) -> None:
        reservoir = Reservoir(initialDepth=5, initialReserves=100)
        prev = reservoir.ratio_pumped()
        self.assertEqual(prev, 0.0)

        for barrels in [20, 15, 10, 5]:
            reservoir.pump(barrels)
            current = reservoir.ratio_pumped()
            self.assertGreater(current, prev)
            self.assertLess(current, 1.0)
            prev = current

    def test_join_averages_oil_depth(self) -> None:
        reservoir = Reservoir(initialDepth=4, initialReserves=100)
        reservoir.join(6, 100)
        self.assertEqual(reservoir.oil_depth, 5)  # floor((4+6)/2)


class TestWellOutputBounds(unittest.TestCase):
    def _make_producing_site(
        self, reserves: int, max_output: int = 66
    ) -> tuple[Site, Well, Reservoir]:
        player = Player("alice", "A")
        site = Site(0, 0)
        site.tax = 0
        reservoir = Reservoir(initialDepth=5, initialReserves=reserves)
        site.reservoir = reservoir
        well = Well(week=1, player=player)
        site.well = well
        return site, well, reservoir

    def test_initial_output_never_exceeds_half_reserves(self) -> None:
        site, well, reservoir = self._make_producing_site(reserves=100)
        output = SimpleWellTheory(66).start(site)
        well.output = output
        well.initial_output = output

        self.assertIsNotNone(well.output)
        self.assertLessEqual(well.output, reservoir.reserves / 2.0)

    def test_weekly_output_never_overdrafts_reservoir(self) -> None:
        # Runs 20 simulated weekly ticks and verifies pump() never raises.
        site, well, reservoir = self._make_producing_site(reserves=1000)
        theory = SimpleWellTheory(66)
        output = theory.start(site)
        well.output = output
        well.initial_output = output

        for week_num in range(1, 21):
            output, capacity = theory.tick(site, week_num)
            well.output = output
            well.capacity = capacity
            if output is not None and output > 0:
                self.assertLess(
                    output,
                    reservoir.reserves,
                    f"Week {week_num}: output {output:.2f} >= reserves "
                    f"{reservoir.reserves:.2f}",
                )
            well.tick(site, oilPrice=4.50)


class TestOilPriceFloor(unittest.TestCase):
    def test_gaussian_prices_never_below_floor(self) -> None:
        # Extreme downward bias to stress-test the floor.
        prices = GaussianPrices(start=0.05, mu=-50.0, sigma=100.0)
        for _ in range(1000):
            self.assertGreaterEqual(next(prices), 0.01)


if __name__ == "__main__":
    unittest.main()
