import pytest

import wildcatting.model


class TestOilField:
    def testEmptySites(self) -> None:
        cols = 5
        rows = 10

        field = wildcatting.model.OilField(cols, rows)
        assert field.height == rows
        assert field.width == cols

        for row in range(rows):
            for col in range(cols):
                site = field.get_site(row, col)
                assert site is not None

    def testGetSiteOutOfBounds(self) -> None:
        field = wildcatting.model.OilField(5, 10)
        with pytest.raises(AssertionError):
            field.get_site(-1, 0)
        with pytest.raises(AssertionError):
            field.get_site(0, -1)
        with pytest.raises(AssertionError):
            field.get_site(10, 0)
        with pytest.raises(AssertionError):
            field.get_site(0, 5)
