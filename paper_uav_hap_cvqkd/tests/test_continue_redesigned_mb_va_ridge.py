import unittest

from scripts.continue_redesigned_mb_va_ridge import PRIMARY, RIDGE_NUS, continuation_targets


class RedesignedContinuationTest(unittest.TestCase):
    def test_stage_one_is_six_targeted_points_and_stage_two_is_ridge_only(self):
        self.assertEqual(len(PRIMARY), 6)
        self.assertEqual(set(PRIMARY), {(0.10, 4.5), (0.10, 5.0), (0.10, 6.0), (0.15, 4.5), (0.15, 5.0), (0.15, 6.0)})
        rows = [{"nu_raw": "0.15", "VA": "3.5548673904962893", "SKR": "0.0756544"}]
        stage_two = continuation_targets(2, rows)
        self.assertEqual({nu for nu, _ in stage_two}, set(RIDGE_NUS))
        self.assertEqual({va for _, va in stage_two}, {6.0, 8.0})
        self.assertEqual(set(continuation_targets(5, rows)), {(0.16, 5.5), (0.17, 5.5), (0.18, 5.5), (0.19, 5.5), (0.175, 5.25), (0.175, 5.75)})
        self.assertEqual(set(continuation_targets(6, rows)), {(0.16, 5.4), (0.16, 5.6), (0.165, 5.4), (0.165, 5.5), (0.165, 5.6)})
        self.assertEqual(continuation_targets(7, rows), [(0.165, 5.55)])
        self.assertEqual(len(continuation_targets(8, rows)), 10)
        self.assertEqual({nu for nu, _ in continuation_targets(9, rows)}, {0.5, 0.6, 0.8})
        self.assertEqual({va for _, va in continuation_targets(10, rows)}, {1.5, 3.0})
        self.assertEqual(continuation_targets(11, rows), [(0.4, 3.0)])
        self.assertEqual(set(continuation_targets(4, rows)), {(0.25, 5.5), (0.3, 5.5), (0.4, 5.5), (0.1, 0.025), (0.165, 0.025), (0.3, 0.025), (0.165, 8.0)})


if __name__ == "__main__":
    unittest.main()
