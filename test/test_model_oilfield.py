import unittest

import wildcatting.model

class TestOilField(unittest.TestCase):
    def testEmptySites(self):
        cols = 5
        rows = 10

        field = wildcatting.model.OilField(cols, rows)
        self.assertEqual(field.getHeight(), rows)
        self.assertEqual(field.getWidth(), cols)

        for row in xrange(rows):
            for col in xrange(cols):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)

if __name__ == "__main__":
    unittest.main()
