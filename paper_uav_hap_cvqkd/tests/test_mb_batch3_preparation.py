import unittest
from scripts import prepare_theta10_D55_mb_batch3 as prep


class Batch3PreparationTests(unittest.TestCase):
    def test_exact_midpoints_and_fail_closed_accuracy(self):
        self.assertEqual(prep.PRIORITY, ((.165,5.4625),(.165,5.4875),(.16531250000000003,5.5)))
        self.assertEqual(len({prep.pair(*p) for p in prep.PRIORITY}), 3)
        self.assertNotEqual(prep.pair(.165,5.425), prep.pair(.165,5.425000000000001))
        self.assertEqual(prep.classify_accuracy(True), 'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED')
        self.assertEqual(prep.classify_accuracy(False), 'NUMERICAL_RANKING_INCONCLUSIVE')
        with self.assertRaises(AssertionError):
            prep.forbidden()


if __name__ == '__main__':
    unittest.main()
