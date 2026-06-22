import unittest

import wildcatting.model


class TestOilField(unittest.TestCase):
    def testEmptySites(self):
        cols = 5
        rows = 10

        field = wildcatting.model.OilField(cols, rows)
        self.assertEqual(field.get_height(), rows)
        self.assertEqual(field.get_width(), cols)

        for row in range(rows):
            for col in range(cols):
                site = field.get_site(row, col)

                self.assertNotEqual(site, None)


if __name__ == "__main__":
    unittest.main()
