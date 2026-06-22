import random
from collections.abc import Iterator
from typing import Any

from wildcatting.model import OilField, Site
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


class TestClientVisibility:
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

        assert site.probability == 0
        assert site.drill_cost == 0
        assert site.tax == 0
        assert site.well is None
        assert not site.surveyed

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
            assert "oilFlag" not in key, f"oilFlag found in serialized key: {key!r}"
            assert "oil_flag" not in key, f"oil_flag found in serialized key: {key!r}"

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
            assert "reservoir" not in key.lower(), f"reservoir in key: {key!r}"
            assert "reserves" not in key.lower(), f"reserves in key: {key!r}"
            assert "ratioPumped" not in key, f"ratioPumped in key: {key!r}"

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
        assert target is not None, (
            "seed 42 must produce a 10x10 field with oil at depth > 1"
        )
        row, col = target

        def get_oil_depth() -> int | None:
            return Site.deserialize(
                service.get_player_site(player_handle, row, col)
            ).oil_depth

        service.survey(player_handle, row, col)
        assert get_oil_depth() is None

        service.erect(player_handle, row, col)
        assert get_oil_depth() is None

        reservoir = field.get_site(row, col).reservoir
        assert reservoir is not None
        oil_depth = reservoir.oil_depth
        assert oil_depth is not None
        for _ in range(oil_depth - 2):  # erect already drilled once
            service.drill(player_handle, row, col)
            assert get_oil_depth() is None

        service.drill(player_handle, row, col)
        assert get_oil_depth() is not None

    def test_player_field_reveals_all_sites_after_game_ends(self) -> None:
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)

        service.survey(player_handle, 0, 0)
        service.end_turn(player_handle)
        assert service.is_finished(client_handle)

        raw = service.get_player_field(client_handle)
        field = OilField.deserialize(raw)

        # OilFiller clamps probability to [10, 100] for every site.
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                assert site.probability > 0, (
                    f"site ({row},{col}) has zero probability after game ended"
                )
