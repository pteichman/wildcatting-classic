import unittest

from wildcatting.model import OilField, Site, Setting

class TestSerializer(unittest.TestCase):
    def testSite(self):
        site1 = Site(1, 1)
        obj1 = site1.serialize()
        site2 = Site.deserialize(obj1)
        obj2 = site2.serialize()

        self.assertEqual(obj1, obj2)

    def testOilField(self):
        field1 = OilField(2, 2)
        obj1 = field1.serialize()
        field2 = OilField.deserialize(obj1)
        obj2 = field2.serialize()

        self.assertEqual(obj1, obj2)

    def testSetting(self):
        setting1 = Setting()
        obj1 = setting1.serialize()
        setting2 = Setting.deserialize(obj1)
        obj2 = setting2.serialize()

        self.assertEqual(obj1, obj2)
        
if __name__ == "__main__":
    unittest.main()
