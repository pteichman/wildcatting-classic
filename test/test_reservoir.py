import pytest

from wildcatting.model import Player, Site, Well
from wildcatting.reservoir import Reservoir
from wildcatting.welltheory import SimpleWellTheory


class TestReservoir:
    def test_pump_forbids_drawing_last_barrel(self) -> None:
        reservoir = Reservoir(initial_depth=5, initial_reserves=10)
        reservoir.pump(9)  # leaves 1 barrel
        with pytest.raises(AssertionError):
            reservoir.pump(1)  # 1 is not < 1

    def test_ratio_pumped_monotonically_increases(self) -> None:
        reservoir = Reservoir(initial_depth=5, initial_reserves=100)
        prev = reservoir.ratio_pumped()
        assert prev == 0.0

        for barrels in [20, 15, 10, 5]:
            reservoir.pump(barrels)
            current = reservoir.ratio_pumped()
            assert current > prev
            assert current < 1.0
            prev = current

    def test_join_averages_oil_depth(self) -> None:
        reservoir = Reservoir(initial_depth=4, initial_reserves=100)
        reservoir.join(6, 100)
        assert reservoir.oil_depth == 5  # floor((4+6)/2)


class TestWellOutputBounds:
    def _make_producing_site(
        self, reserves: int, max_output: int = 66
    ) -> tuple[Site, Well, Reservoir]:
        player = Player("alice", "A")
        site = Site(0, 0)
        site.tax = 0
        reservoir = Reservoir(initial_depth=5, initial_reserves=reserves)
        site.reservoir = reservoir
        well = Well(week=1, player=player)
        site.well = well
        return site, well, reservoir

    def test_weekly_output_never_overdrafts_reservoir(self) -> None:
        # Runs 20 simulated weekly ticks and verifies pump() never raises.
        site, well, reservoir = self._make_producing_site(reserves=1000)
        theory = SimpleWellTheory(66)
        output = theory.start(well, reservoir)
        well.output = output

        for week_num in range(1, 21):
            output, capacity = theory.tick(well, reservoir, week_num)
            well.output = output
            well.capacity = capacity
            if output is not None and output > 0:
                assert output < reservoir.reserves, (
                    f"Week {week_num}: output {output:.2f} >= reserves "
                    f"{reservoir.reserves:.2f}"
                )
            well.tick(site, oil_price=4.50)
