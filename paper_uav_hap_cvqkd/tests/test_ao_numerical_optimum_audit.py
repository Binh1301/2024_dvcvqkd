import unittest
from scripts import audit_theta10_D55_ao_numerical_optimum as audit


class SavedAOAudit(unittest.TestCase):
    def test_real_search_alignment_and_binary64_midpoints(self):
        runs = audit.read(audit.BASE/'cache_only_runs.json')
        searches = audit.read(audit.BASE/'cache_only_searches.json')
        aligned, finals = audit.align_searches(runs, searches)
        self.assertEqual(len(aligned), 618)
        self.assertEqual(sum(len(r['iterations']) for r in runs), 283)
        self.assertEqual(len(runs), 129)
        self.assertEqual([s['fixed'] for s in finals[22.]], [.165, 5.475])
        self.assertNotEqual(((5.475+5.4875)/2).hex(), (5.48125).hex())
        corrupted = [dict(s) for s in searches]
        corrupted[1]['fixed'] = 9.
        with self.assertRaises(AssertionError):
            audit.align_searches(runs, corrupted)
        with self.assertRaises(AssertionError):
            audit.forbidden()


if __name__=='__main__':
    unittest.main()
