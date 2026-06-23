from wildcatting.model import Player, Well
from wildcatting.reservoir import Reservoir
from wildcatting.welltheory import SimpleWellTheory


class TestSimpleWellTheory:
    def _make_setup(self, reserves: int = 1000) -> tuple[Well, Reservoir]:
        player = Player("alice", "A")
        well = Well(week=1, player=player)
        well.capacity = 1
        reservoir = Reservoir(initial_depth=5, initial_reserves=reserves)
        return well, reservoir

    def test_capacity_increments_during_ramp_up(self) -> None:
        # well.week=1; weeks_operational = current_week - 1
        # increments at weeks_operational in [1, 2, 3] → current_week in [2, 3, 4]
        well, reservoir = self._make_setup()
        theory = SimpleWellTheory(66)
        initial_capacity = well.capacity
        for current_week in (2, 3, 4):
            result = theory.tick(well, reservoir, current_week)
            assert result.capacity == initial_capacity + 1

    def test_capacity_stable_after_ramp_up(self) -> None:
        # weeks_operational=4 (current_week=5, well.week=1) → no increment
        well, reservoir = self._make_setup()
        theory = SimpleWellTheory(66)
        result = theory.tick(well, reservoir, 5)
        assert result.capacity == well.capacity

    def test_output_positive_with_reserves(self) -> None:
        well, reservoir = self._make_setup()
        theory = SimpleWellTheory(66)
        output = theory.start(well, reservoir)
        assert output > 0

    def test_output_at_most_half_reserves(self) -> None:
        well, reservoir = self._make_setup(reserves=100)
        theory = SimpleWellTheory(66)
        output = theory.start(well, reservoir)
        assert output <= reservoir.reserves / 2.0
