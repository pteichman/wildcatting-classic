import unittest

from wildcatting.model import OilField
from wildcatting.game import OilFiller, TaxFiller, Game

class TestOilFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        filler = OilFiller()
        filler.fill(field)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assert_(site.getProbability() >= 0)
                self.assert_(site.getProbability() <= 100)

class TestTaxFiller(unittest.TestCase):
    def testFreshField(self):
        rows = cols = 10

        field = OilField(rows, cols)
        OilFiller().fill(field)
        TaxFiller().fill(field)

        for row in xrange(field.getHeight()):
            for col in xrange(field.getWidth()):
                site = field.getSite(row, col)

                self.assertNotEqual(site, None)
                self.assert_(site.getTax() >= 0)

if __name__ == "__main__":
    unittest.main()
