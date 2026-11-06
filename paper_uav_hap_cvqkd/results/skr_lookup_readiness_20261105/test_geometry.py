import math
import unittest

from prepare_geometry import geometry, lookup_skr


class GeometryTests(unittest.TestCase):
    def test_center_and_corner(self):
        self.assertEqual(geometry(1000., 1000.), (19000., 0.))
        length, zenith = geometry(0., 0.)
        self.assertAlmostEqual(length, math.sqrt(19000.**2 + 2*1000.**2), places=10)
        self.assertAlmostEqual(zenith, math.degrees(math.atan2(math.sqrt(2)*1000, 19000.)), places=13)
        self.assertTrue(4.25 < zenith < 4.27)

    def test_lookup_refuses_to_return_an_uncomputed_rate(self):
        with self.assertRaisesRegex(RuntimeError, 'NOT_RUN'):
            lookup_skr(1000., 1000.)
        with self.assertRaises(ValueError):
            lookup_skr(-1., 1000.)


if __name__ == '__main__':
    unittest.main()
