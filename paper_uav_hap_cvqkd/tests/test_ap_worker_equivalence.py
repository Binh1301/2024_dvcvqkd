import inspect
import json
import os
from pathlib import Path
import unittest

import mpmath as mp
import torch

from src.cvqkd import gram_moments as gm
from scripts import full_support_c4_worker as worker


ROOT = Path(__file__).parents[1]


def _fixtures():
    x = torch.arange(1, 65, dtype=torch.float64)
    uniform = torch.full((64,), 1 / 64, dtype=torch.float64)
    mild = 1.0 + 0.01 * torch.sin(x)
    mild = mild / mild.sum()
    perturbed = (x + 0.1 * torch.sin(x)).to(torch.complex128)
    return (
        ("uniform", uniform, x.to(torch.complex128)),
        ("nonuniform", mild, x.to(torch.complex128)),
        ("perturbed_geometry", mild, perturbed),
    )


class APWorkerEquivalenceTests(unittest.TestCase):
    def test_worker_uses_production_a_block(self):
        source = inspect.getsource(worker._row)
        self.assertIn("aa = x2.T", source)
        self.assertNotIn("aa = sr * x2.T", source)

    @unittest.skipUnless(
        os.environ.get("RUN_SLOW_AP_WORKER_EQUIVALENCE") == "1",
        "explicit slow AP worker equivalence test",
    )
    def test_small_fixtures_match_production_c_and_w(self):
        for name, probabilities, amplitudes in _fixtures():
            fast, gate = gm._fast(probabilities, amplitudes)
            self.assertIsNotNone(fast, f"production gate failed for {name}: {gate}")
            ap_row = worker._row(
                [mp.mpf(float(value)) for value in probabilities.tolist()],
                [
                    mp.mpc(float(value.real), float(value.imag))
                    for value in amplitudes.tolist()
                ],
                20,
            )
            self.assertTrue(ap_row["resolved"], name)
            for key in ("C", "w"):
                expected = float(fast[key])
                observed = float(ap_row[key])
                self.assertLess(
                    abs(expected - observed),
                    1e-10 * max(1.0, abs(expected)),
                    f"{name} {key}",
                )

    def test_old_case_a_artifact_is_not_current_oracle(self):
        artifact = json.loads(
            (ROOT / "results" / "exploratory_case_A_full_security_20260910.json").read_text()
        )
        self.assertEqual(artifact["status"], "SUPERSEDED_WRONG_AP_W")
        self.assertEqual(artifact["source_moment_status"], "SUPERSEDED_WRONG_AP_W")

    def test_all_known_old_w_artifacts_are_superseded(self):
        names = (
            "exploratory_case_A_full_security_20260910.json",
            "exploratory_cases_BD_full_security_20260910.json",
            "baseline_cached_uniform.json",
            "baseline_cached_binomial.json",
            "baseline_cached_mb.json",
            "baseline_cached_source_moments_smoke.json",
            "full_support_c4_gram_evaluation_validation_v1.json",
        )
        for name in names:
            artifact = json.loads((ROOT / "results" / name).read_text())
            self.assertEqual(artifact["status"], "SUPERSEDED_WRONG_AP_W", name)

    def test_corrected_case_a_artifact_binds_worker_and_ensemble(self):
        artifact = json.loads(
            (ROOT / "results" / "ap_worker_corrected_case_A_20260911.json").read_text()
        )
        self.assertIn("CORRECTED_AP_FORWARD_VALIDATED", artifact["status"])
        self.assertEqual(artifact["ensemble"]["row_sha256"], "c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3")
        self.assertEqual(artifact["provenance"]["corrected_expression"], "aa = x2.T")
        self.assertEqual(len(artifact["rows"]), 2)


if __name__ == "__main__":
    unittest.main()
