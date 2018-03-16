import unittest
from .. import geom
from ..geom import Point, Seg, ps_dist, min_dist
import math

class Test_Geom(unittest.TestCase):
    def setUp(self):
        self.z = Point(0,0)
        self.x = Point(1,0)
        self.y = Point(0,1)

    def test_add(self):
        self.assertTrue(self.x + self.z == self.x)
        self.assertTrue(self.y + self.z == self.y)
        self.assertTrue(self.x + self.y == Point(1,1))

    def test_subtract(self):
        self.assertTrue(self.x - self.z == self.x)
        self.assertTrue(self.y - self.z == self.y)
        self.assertTrue(self.x - self.y == Point(1,-1))

    def test_ps_dist(self):
        a = Point(1,1)
        b = Point(-1,-1)
        self.assertTrue(ps_dist(self.z, Seg(a,b)) == 0)
        self.assertTrue(ps_dist(self.z, Seg(a,a)) == math.sqrt(2))
        self.assertTrue(ps_dist(self.z, Seg(a, a+a)) == math.sqrt(2))
        self.assertTrue(ps_dist(self.z, Seg(a+a, a)) == math.sqrt(2))

    def test_min_dist(self):
        segz = Seg(self.z, self.z)
        seg1 = Seg(self.x, self.y)
        seg2 = Seg(self.y, self.x)
        seg3 = Seg(self.y, self.z)
        seg4 = Seg(self.z, self.x)
        seg5 = Seg(Point(1,1), Point(-1,-1))
        seg6 = Seg(Point(-1,1), Point(1,-1))
        self.assertTrue(min_dist(segz, seg1) == math.sqrt(2)/2)
        self.assertTrue(min_dist(seg1,seg1) == 0)
        self.assertTrue(min_dist(seg1,seg2) == 0)
        self.assertTrue(min_dist(seg2,seg1) == 0)
        self.assertTrue(min_dist(seg3,seg4) == math.sqrt(2)/2)
        self.assertTrue(min_dist(seg5,seg6) == 0)

if __name__ == '__main__':
    unittest.main()