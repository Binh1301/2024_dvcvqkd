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


def _toy_global_gram():
    q = torch.tensor([0.35, 0.65], dtype=torch.float64)
    z = torch.tensor([0.21 + 0.13j, -0.37 + 0.29j], dtype=torch.complex128)
    rotations = torch.tensor([1.0, 1.0j, -1.0, -1.0j], dtype=torch.complex128)
    alpha = torch.stack([z[orbit] * rotations[rotation] for orbit in range(2) for rotation in range(4)])
    p = torch.repeat_interleave(q / 4.0, 4)
    weight = torch.sqrt(p[:, None] * p[None, :])
    gram = weight * torch.exp(
        -0.5 * (alpha.abs().square()[:, None] + alpha.abs().square()[None, :])
        + alpha.conj()[:, None] * alpha[None, :]
    )
    blocks = [
        torch.sqrt((q / 4.0)[:, None] * (q / 4.0)[None, :])
        * torch.exp(
            -0.5 * (z.abs().square()[:, None] + (rotations[d] * z).abs().square()[None, :])
            + z.conj()[:, None] * (rotations[d] * z)[None, :]
        )
        for d in range(4)
    ]
    fourier = torch.tensor(
        [[rotations[(a * r) % 4] for a in range(4)] for r in range(4)],
        dtype=torch.complex128,
    ) / 2.0
    unitary = torch.kron(torch.eye(2, dtype=torch.complex128), fourier)
    transformed = unitary.mH @ gram @ unitary
    sectors = [
        sum(blocks[d] * rotations[(sector * d) % 4] for d in range(4))
        for sector in range(4)
    ]
    extracted = [
        transformed[
            torch.tensor([4 * orbit + sector for orbit in range(2)]
                         ),
            :,
        ][:, torch.tensor([4 * orbit + sector for orbit in range(2)])]
        for sector in range(4)
    ]
    return gram, unitary, transformed, sectors, extracted


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


class GlobalWeightedGramAuditTests(unittest.TestCase):
    def test_fourier_transform_is_unitary_on_cheap_fixture(self):
        _gram, unitary, _transformed, _sectors, _extracted = _toy_global_gram()
        identity = torch.eye(unitary.shape[0], dtype=torch.complex128)
        self.assertLess(float((unitary.mH @ unitary - identity).abs().max()), 1e-14)

    def test_global_invariants_and_c4_off_block_structure(self):
        gram, _unitary, transformed, sectors, extracted = _toy_global_gram()
        identity = torch.eye(gram.shape[0], dtype=torch.complex128)
        self.assertLess(float((gram - gram.mH).abs().max()), 1e-14)
        self.assertAlmostEqual(float(torch.trace(gram).real), 1.0, places=14)
        self.assertLess(float((torch.trace(gram @ gram) - sum(torch.trace(sector @ sector) for sector in sectors)).abs()), 1e-13)
        for sector in range(4):
            for other in range(4):
                if sector != other:
                    rows = torch.tensor([4 * orbit + sector for orbit in range(2)])
                    columns = torch.tensor([4 * orbit + other for orbit in range(2)])
                    self.assertLess(float(transformed[rows, :][:, columns].abs().max()), 1e-13)
            self.assertLess(float((extracted[sector] - sectors[sector]).abs().max()), 1e-13)
        self.assertEqual(gram.shape, identity.shape)

    def test_global_spectrum_equals_cheap_sector_union(self):
        gram, _unitary, _transformed, sectors, _extracted = _toy_global_gram()
        global_values = torch.linalg.eigvalsh(gram)
        sector_values = torch.cat([torch.linalg.eigvalsh(sector) for sector in sectors])
        self.assertLess(
            float((global_values.sort().values - sector_values.sort().values).abs().max()),
            1e-13,
        )


if __name__ == "__main__":
    unittest.main()
