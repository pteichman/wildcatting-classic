import random
import unittest

from wildcatting.model import OilField, Player, Site, WeeklySummary, Well
from wildcatting.server import GameService
from wildcatting.theme import DefaultTheme


def _all_keys(d):
    """Yield every key from a nested dict/list structure."""
    if isinstance(d, dict):
        for k, v in d.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(d, list):
        for item in d:
            yield from _all_keys(item)


class TestClientVisibility(unittest.TestCase):
    def _one_player_game(self, turn_count=13):
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, turn_count)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)
        return service, client_handle, player_handle

    def test_unsurveyed_site_is_empty(self):
        service, client_handle, player_handle = self._one_player_game()

        raw = service.getPlayerSite(player_handle, 0, 0)
        site = Site.deserialize(raw)

        self.assertEqual(site.getProbability(), 0)
        self.assertEqual(site.getDrillCost(), 0)
        self.assertEqual(site.getTax(), 0)
        self.assertIsNone(site.getWell())
        self.assertFalse(site.isSurveyed())

    def test_oil_flag_never_serialized(self):
        # End the game so all sites are revealed — this is the worst case for leakage.
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)
        service.survey(player_handle, 0, 0)
        service.endTurn(player_handle)

        raw = service.getPlayerField(client_handle)
        for key in _all_keys(raw):
            self.assertNotIn("oilFlag", key, f"oilFlag found in serialized key: {key!r}")
            self.assertNotIn("oil_flag", key, f"oil_flag found in serialized key: {key!r}")

    def test_reservoir_never_serialized(self):
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)
        service.survey(player_handle, 0, 0)
        service.endTurn(player_handle)

        raw = service.getPlayerField(client_handle)
        for key in _all_keys(raw):
            self.assertNotIn("reservoir", key.lower(), f"reservoir in key: {key!r}")
            self.assertNotIn("reserves", key.lower(), f"reserves in key: {key!r}")
            self.assertNotIn("ratioPumped", key, f"ratioPumped in key: {key!r}")

    def test_oil_depth_hidden_until_drill_hits_oil(self):
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 13)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)

        game, player = service._readHandle(player_handle)
        field = game.getOilField()

        # Find a site with a reservoir at depth > 1 so erect() alone won't find oil.
        target = None
        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                if site.getReservoir() is not None and site.getReservoir().getOilDepth() > 1:
                    target = (row, col)
                    break
            if target:
                break
        self.assertIsNotNone(target, "seed 42 must produce a 10x10 field with oil at depth > 1")
        row, col = target

        service.survey(player_handle, row, col)
        self.assertIsNone(Site.deserialize(service.getPlayerSite(player_handle, row, col)).getOilDepth())

        service.erect(player_handle, row, col)
        self.assertIsNone(Site.deserialize(service.getPlayerSite(player_handle, row, col)).getOilDepth())

        oil_depth = field.getSite(row, col).getReservoir().getOilDepth()
        for _ in range(oil_depth - 2):  # erect already drilled once
            service.drill(player_handle, row, col)
            self.assertIsNone(Site.deserialize(service.getPlayerSite(player_handle, row, col)).getOilDepth())

        service.drill(player_handle, row, col)
        self.assertIsNotNone(Site.deserialize(service.getPlayerSite(player_handle, row, col)).getOilDepth())

    def test_player_field_reveals_all_sites_after_game_ends(self):
        random.seed(42)
        service = GameService(DefaultTheme())
        client_handle = service.new(10, 10, 1)
        player_handle = service.join(client_handle, "alice", "A")
        service.start(player_handle)

        service.survey(player_handle, 0, 0)
        service.endTurn(player_handle)
        self.assertTrue(service.isFinished(client_handle))

        raw = service.getPlayerField(client_handle)
        field = OilField.deserialize(raw)

        # OilFiller clamps probability to [10, 100] for every site.
        for row in range(field.getHeight()):
            for col in range(field.getWidth()):
                site = field.getSite(row, col)
                self.assertGreater(
                    site.getProbability(), 0,
                    f"site ({row},{col}) has zero probability after game ended",
                )


class TestSerializationRoundTrips(unittest.TestCase):
    def test_well_round_trip(self):
        player = Player("alice", "A")
        well1 = Well()
        well1.setPlayer(player)
        well1.setWeek(3)
        well1.setDrillDepth(4)
        well1.setInitialOutput(30.0)
        well1.setOutput(20.0)
        well1.setCapacity(2)

        obj1 = well1.serialize()
        well2 = Well.deserialize(obj1)
        obj2 = well2.serialize()

        self.assertEqual(obj1, obj2)

    def test_player_round_trip(self):
        player1 = Player("bob", "B")
        player1.setSecret("DEADBEEF12345678")
        player1.income(500)
        player1.expense(200)

        obj1 = player1.serialize()
        player2 = Player.deserialize(obj1)
        obj2 = player2.serialize()

        self.assertEqual(obj1, obj2)

    def test_weekly_summary_round_trip(self):
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
