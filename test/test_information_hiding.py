import random
import unittest
from collections.abc import Iterator
from typing import Any

from wildcatting.model import OilField, Player, Site, WeeklySummary, Well
from wildcatting.server import GameService
from wildcatting.theme import DefaultTheme


def _all_keys(d: Any) -> Iterator[Any]:
    """Yield every key from a nested dict/list structure."""
    if isinstance(d, dict):
        for k, v in d.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(d, list):
        for item in d:
            yield from _all_keys(item)


class TestClientVisibility(unittest.TestCase):
    def _one_player_game(self, turn_count: int = 13) -> tuple[GameService, str, str]:
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, turn_count)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)
        return service, client_handle, player_handle

    def test_unsurveyed_site_is_empty(self) -> None:
        service, client_handle, player_handle = self._one_player_game()

        raw = service.get_player_site(player_handle, 0, 0)
        site = Site.deserialize(raw)

        self.assertEqual(site.probability, 0)
        self.assertEqual(site.drill_cost, 0)
        self.assertEqual(site.tax, 0)
        self.assertIsNone(site.well)
        self.assertFalse(site.surveyed)

    def test_oil_flag_never_serialized(self) -> None:
        # End the game so all sites are revealed — this is the worst case for leakage.
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)
        service.survey(player_handle, 0, 0)
        service.end_turn(player_handle)

        raw = service.get_player_field(client_handle)
        for key in _all_keys(raw):
            self.assertNotIn(
                "oilFlag", key, f"oilFlag found in serialized key: {key!r}"
            )
            self.assertNotIn(
                "oil_flag", key, f"oil_flag found in serialized key: {key!r}"
            )

    def test_reservoir_never_serialized(self) -> None:
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)
        service.survey(player_handle, 0, 0)
        service.end_turn(player_handle)

        raw = service.get_player_field(client_handle)
        for key in _all_keys(raw):
            self.assertNotIn("reservoir", key.lower(), f"reservoir in key: {key!r}")
            self.assertNotIn("reserves", key.lower(), f"reserves in key: {key!r}")
            self.assertNotIn("ratioPumped", key, f"ratioPumped in key: {key!r}")

    def test_oil_depth_hidden_until_drill_hits_oil(self) -> None:
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 13)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)

        game, player = service._read_handle(player_handle)
        field = game.oil_field

        # Find a site with a reservoir at depth > 1 so erect() alone won't find oil.
        target = None
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                reservoir = site.reservoir
                if (
                    reservoir is not None
                    and reservoir.oil_depth is not None
                    and reservoir.oil_depth > 1
                ):
                    target = (row, col)
                    break
            if target:
                break
        self.assertIsNotNone(
            target, "seed 42 must produce a 10x10 field with oil at depth > 1"
        )
        assert target is not None
        row, col = target

        def get_oil_depth() -> int | None:
            return Site.deserialize(
                service.get_player_site(player_handle, row, col)
            ).oil_depth

        service.survey(player_handle, row, col)
        self.assertIsNone(get_oil_depth())

        service.erect(player_handle, row, col)
        self.assertIsNone(get_oil_depth())

        reservoir = field.get_site(row, col).reservoir
        assert reservoir is not None
        oil_depth = reservoir.oil_depth
        assert oil_depth is not None
        for _ in range(oil_depth - 2):  # erect already drilled once
            service.drill(player_handle, row, col)
            self.assertIsNone(get_oil_depth())

        service.drill(player_handle, row, col)
        self.assertIsNotNone(get_oil_depth())

    def test_player_field_reveals_all_sites_after_game_ends(self) -> None:
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)

        service.survey(player_handle, 0, 0)
        service.end_turn(player_handle)
        self.assertTrue(service.is_finished(client_handle))

        raw = service.get_player_field(client_handle)
        field = OilField.deserialize(raw)

        # OilFiller clamps probability to [10, 100] for every site.
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                self.assertGreater(
                    site.probability,
                    0,
                    f"site ({row},{col}) has zero probability after game ended",
                )


class TestSerializationRoundTrips(unittest.TestCase):
    def test_well_round_trip(self) -> None:
        player = Player("alice", "A")
        well1 = Well(week=3, player=player)
        well1.drill_depth = 4
        well1.initial_output = 30.0
        well1.output = 20.0
        well1.capacity = 2

        obj1 = well1.serialize()
        well2 = Well.deserialize(obj1)
        obj2 = well2.serialize()

        self.assertEqual(obj1, obj2)

    def test_player_round_trip(self) -> None:
        player1 = Player("bob", "B")
        player1.secret = "DEADBEEF12345678"
        player1.income(500)
        player1.expense(200)

        obj1 = player1.serialize()
        player2 = Player.deserialize(obj1)
        obj2 = player2.serialize()

        self.assertEqual(obj1, obj2)

    def test_weekly_summary_round_trip(self) -> None:
        players = [Player("alice", "A"), Player("bob", "B")]
        players[0].income(1000)
        players[1].expense(200)

        summary1 = WeeklySummary(players, 5)
        obj1 = summary1.serialize()
        summary2 = WeeklySummary.deserialize(obj1)
        obj2 = summary2.serialize()

        self.assertEqual(obj1, obj2)


if __name__ == "__main__":
    unittest.main()
