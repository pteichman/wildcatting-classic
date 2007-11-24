import unittest

from wildcatting.model import OilField
from wildcatting.game import OilFieldFiller, Game

class TestOilFieldFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        filler = OilFieldFiller()
        filler.fill(field)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assert_(site.getProbability() >= 0)
                self.assert_(site.getProbability() <= 100)

if __name__ == "__main__":
    unittest.main()
