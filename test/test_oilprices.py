import random

import pytest

from wildcatting.oilprices import GaussianPrices, TrendingGaussianPrices


class TestGaussianPriceFloor:
    def test_prices_never_below_floor(self) -> None:
        # Extreme downward bias to stress-test the floor.
        prices = GaussianPrices(start=0.05, mu=-50.0, sigma=100.0)
        for _ in range(1000):
            assert next(prices) >= 0.01


class TestTrendingGaussianPrices:
    def test_prices_never_below_min(self) -> None:
        prices = TrendingGaussianPrices(
            start=5.0, min_price=1.0, max_price=20.0, trend_mu=5, trend_sigma=2
        )
        for _ in range(200):
            assert next(prices) >= 1.0

    def test_prices_never_above_max(self) -> None:
        prices = TrendingGaussianPrices(
            start=5.0, min_price=1.0, max_price=20.0, trend_mu=5, trend_sigma=2
        )
        for _ in range(200):
            assert next(prices) <= 20.0

    def test_get_initial_price_unchanged_after_advancing(self) -> None:
        prices = TrendingGaussianPrices(
            start=7.5, min_price=1.0, max_price=20.0, trend_mu=5, trend_sigma=2
        )
        assert prices.get_initial_price() == pytest.approx(7.5)
        next(prices)
        next(prices)
        assert prices.get_initial_price() == pytest.approx(7.5)

    def test_next_trend_resets_week_and_sets_positive_length(self) -> None:
        random.seed(42)
        prices = TrendingGaussianPrices(
            start=5.0, min_price=1.0, max_price=20.0, trend_mu=3, trend_sigma=1
        )
        prices._next_trend()
        assert prices._trend_week == 0
        assert prices._trend_length >= 1
