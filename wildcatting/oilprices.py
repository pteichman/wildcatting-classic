import logging
import random


class GaussianPrices:
    """Gaussian distribution"""

    def __init__(
        self, start: float, mu: float | None = None, sigma: float | None = None
    ) -> None:
        self._initial_price = self._price = start

        if mu is None:
            mu = 0.0

        if sigma is None:
            sigma = 1.0

        self._mu = mu
        self._sigma = sigma

    def __str__(self) -> str:
        lines = [str(self.__class__)]

        lines.append(f"  Initial oil price: ${self._price:.2f}")
        lines.append(f"  Mean change between turns: {self._mu:.3f}%")
        lines.append(f"  Standard deviation: {self._sigma:.3f}%")
        lo1 = f"{self._mu - self._sigma:.3f}"
        hi1 = f"{self._mu + self._sigma:.3f}"
        lines.append(
            f"    1. 68.27% of price changes will be in the range: {lo1}% .. {hi1}%"
        )
        lo2 = f"{self._mu - self._sigma * 2:.3f}"
        hi2 = f"{self._mu + self._sigma * 2:.3f}"
        lines.append(
            f"    2. 95.45% of price changes will be in the range: {lo2}% .. {hi2}%"
        )
        sd_lo = f"${self._price + self._price * (self._mu - self._sigma) / 100:.2f}"
        sd_hi = f"${self._price + self._price * (self._mu + self._sigma) / 100:.2f}"
        lines.append(f"  Initial price +/- one standard deviation: {sd_lo} .. {sd_hi}")

        return "\n".join(lines)

    def get_initial_price(self) -> float:
        return self._initial_price

    def __next__(self) -> float:
        change = random.gauss(self._mu, self._sigma)
        self._price = max(0.01, self._price + self._price * change / 100)
        return self._price


class TrendingGaussianPrices:
    log = logging.getLogger("Wildcatting")

    """Gaussian distribution that trends in a given direction every N or so turns"""

    def __init__(
        self,
        start: float,
        min_price: float,
        max_price: float,
        trend_mu: float,
        trend_sigma: float,
    ) -> None:
        self._initial_price = self._price = start
        self._min_price = min_price
        self._max_price = max_price
        self._trend_mu = trend_mu
        self._trend_sigma = trend_sigma

        self._trend_week: int = 0
        self._trend_length: int = 0

        self._mu: float = 0.0
        self._sigma: float = 2.0

    def _next_trend(self) -> None:
        self._trend_week = 0
        self._trend_length = max(
            1, int(random.gauss(self._trend_mu, self._trend_sigma))
        )

        self._mu = random.gauss(0.0, 3.0)
        self._sigma = 2.0

    def __next__(self) -> float:
        if self._trend_length == self._trend_week:
            self._next_trend()

        self._trend_week = self._trend_week + 1

        change = random.gauss(self._mu, self._sigma)
        self._price = self._price + self._price * change / 100

        # clamp to our min/max values
        self._price = max(self._min_price, min(self._max_price, self._price))

        return self._price

    def get_initial_price(self) -> float:
        return self._initial_price


if __name__ == "__main__":
    prices = GaussianPrices(10.00)
    prev = next(prices)
    print(f"{prev:.2f}")
    for i in range(0, 10):
        cur = next(prices)
        print(f"{cur:.2f} ({(cur - prev) / prev * 100:.2f}%)")
        prev = cur
