import contextlib
import io
import unittest

from scripts.diagnose_mb_va_adam import (
    central_difference,
    physical_source_coverage,
    run_synthetic,
    synthetic_objective,
)


class DiagnoseMBVAAdamTests(unittest.TestCase):
    def test_synthetic_adam_and_physical_fail_closed_gate(self):
        self.assertAlmostEqual(
            central_difference(synthetic_objective, 0.15, 2.0, "nu", 1e-3),
            0.04,
            places=12,
        )
        with contextlib.redirect_stdout(io.StringIO()):
            _, report = run_synthetic()
        self.assertEqual(report["status"], "PASS")
        self.assertAlmostEqual(report["final"]["nu_mb"], 0.17, delta=5e-3)
        self.assertAlmostEqual(report["final"]["V_A"], 2.2, delta=2e-2)
        self.assertEqual(
            physical_source_coverage()["status"],
            "NOT_RUN_SOURCE_MOMENTS_UNAVAILABLE",
        )


if __name__ == "__main__":
    unittest.main()
