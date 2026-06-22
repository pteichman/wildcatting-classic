import random

from wildcatting.game import Game
from wildcatting.model import Player, Well
from wildcatting.theme import DefaultTheme


class TestSeededDeterminism:
    def test_same_seed_same_field(self) -> None:
        random.seed(42)
        field1 = Game(10, 10).oil_field.serialize()

        random.seed(42)
        field2 = Game(10, 10).oil_field.serialize()

        assert field1 == field2

    def test_different_seeds_differ(self) -> None:
        random.seed(1)
        field1 = Game(10, 10).oil_field.serialize()

        random.seed(2)
        field2 = Game(10, 10).oil_field.serialize()

        assert field1 != field2


class TestFieldPropertyRanges:
    def test_all_sites_within_theme_bounds(self) -> None:
        theme = DefaultTheme()
        field = Game(20, 20, theme=theme).oil_field

        min_drill = theme.get_min_drill_cost()
        max_drill = theme.get_max_drill_cost()
        min_tax = theme.get_min_tax()
        max_tax = theme.get_max_tax()

        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                assert site.probability >= 0
                assert site.probability <= 100
                assert site.drill_cost >= min_drill
                assert site.drill_cost <= max_drill
                assert site.tax >= min_tax
                assert site.tax <= max_tax

    def test_oil_prices_always_positive(self) -> None:
        prices = DefaultTheme().get_oil_prices()
        for _ in range(100):
            assert next(prices) > 0.0


class TestCompleteGameFlow:
    def test_idle_two_player_game_completes(self) -> None:
        turn_count = 5
        game = Game(10, 10, turn_count=turn_count)
        p1 = Player("alice", "A")
        p2 = Player("bob", "B")
        game.add_player("c1", p1)
        game.add_player("c2", p2)
        game.start()

        while not game.finished:
            game.end_turn(p1)
            if not game.finished:
                game.end_turn(p2)

        assert game.finished

    def test_idle_players_pnl_stays_zero(self) -> None:
        turn_count = 5
        game = Game(10, 10, turn_count=turn_count)
        p1 = Player("alice", "A")
        p2 = Player("bob", "B")
        game.add_player("c1", p1)
        game.add_player("c2", p2)
        game.start()

        while not game.finished:
            assert p1.profit_and_loss == 0
            assert p2.profit_and_loss == 0
            game.end_turn(p1)
            if not game.finished:
                game.end_turn(p2)

        assert p1.profit_and_loss == 0
        assert p2.profit_and_loss == 0


class TestOilDiscovery:
    def test_drilling_finds_oil_at_correct_depth(self) -> None:
        random.seed(42)
        theme = DefaultTheme()
        game = Game(10, 10, theme=theme)
        field = game.oil_field

        oil_site = None
        for row in range(field.height):
            for col in range(field.width):
                site = field.get_site(row, col)
                if site.reservoir is not None:
                    oil_site = site
                    break
            if oil_site is not None:
                break

        msg = "seed 42 must produce at least one oil site on 10x10"
        assert oil_site is not None, msg

        player = Player("alice", "A")
        well = Well(week=1, player=player)
        oil_site.well = well

        assert oil_site.reservoir is not None
        oil_depth = oil_site.reservoir.oil_depth
        assert oil_depth is not None

        for _ in range(oil_depth - 1):
            found, _ = well.drill(oil_site, theme.get_drill_increment())
            assert not found
            assert oil_site.oil_depth is None

        found, _ = well.drill(oil_site, theme.get_drill_increment())
        assert found
        oil_site.oil_depth = well.drill_depth
        assert oil_site.oil_depth == oil_depth
        assert well.drill_depth == oil_depth
