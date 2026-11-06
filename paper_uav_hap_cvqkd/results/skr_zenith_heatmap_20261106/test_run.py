import math
import hashlib
import unittest

from run import angle_samples, geometry_groups, select_family, dependency_status


class MapTests(unittest.TestCase):
    def test_sweep_includes_exact_slant_endpoint(self):
        samples = angle_samples()
        self.assertEqual(samples[0], 0.)
        self.assertIn(30., samples)
        self.assertAlmostEqual(19000/math.cos(math.radians(samples[-1])), 22000., places=8)
        self.assertEqual(len(samples), len(set(samples)))

    def test_equal_radius_reuses_only_equal_geometry(self):
        rows = [{'x_m':x,'y_m':y,'zenith_deg':2.,'distance_m':19001.}
                for x,y in [(0.,1000.),(2000.,1000.),(1000.,0.)]]
        groups = geometry_groups(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[1000000.]['indices'], [0,1,2])

    def test_signed_ranking_and_failure(self):
        rows = [dict(family='MB', K_raw=k, numerical_status='CURRENTLY_VERIFIED_PASS') for k in (-.2,-.1)]
        self.assertEqual(select_family(rows,'MB')['K_raw'], -.1)
        rows.append(dict(family='MB', K_raw=None, numerical_status='FAILED'))
        self.assertIsNone(select_family(rows,'MB'))

    def test_newline_binding_rejects_content_changes(self):
        expected=hashlib.sha256(b'a=1\n').hexdigest()
        self.assertEqual(dependency_status(b'a=1\r\n',expected),'VERIFIED_NEWLINE_EQUIVALENT')
        self.assertEqual(dependency_status(b'a=2\n',expected),'CHANGED')


if __name__ == '__main__':
    unittest.main()
