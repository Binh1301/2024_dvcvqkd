import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from src.cvqkd import gram_moments as gm
from src.cvqkd.holevo import holevo_information
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.qam256 import c4_orbit_indices


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_baselines_cached_source_moments.py"


def load_runner():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("cached_baselines", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fast_c4_ensemble() -> Ensemble:
    indices = c4_orbit_indices()
    prototypes = torch.arange(1, 65, dtype=torch.float64).to(torch.complex128)
    probabilities = torch.full((1, 256), 1 / 256, dtype=torch.float64)
    amplitudes = torch.empty((1, 256), dtype=torch.complex128)
    for rotation in range(4):
        amplitudes[0, indices[:, rotation]] = (1j) ** rotation * prototypes
    declared_va = 2.0 * torch.sum(probabilities * amplitudes.abs().square(), dim=-1)
    return Ensemble(probabilities, amplitudes, declared_va, amplitudes[0], c4_symmetric=True)


class CachedBaselineSourceMomentTests(unittest.TestCase):
    def test_existing_identical_batch_calls_fallback_once_per_fading_row(self):
        ensemble = reference_ensemble("uniform", batch_size=2, modulation_variance=1.0)
        fallback = {
            "status": "FULL_SUPPORT_CONVERGED",
            "C": "0.0",
            "w": "0.0",
            "rows": [{"minimum_eigenvalue": "1e-30"}],
        }
        with patch.object(gm, "_fast", return_value=(None, {})), patch.object(
            gm, "_fallback", return_value=fallback
        ) as fallback_call:
            gm.c4_gram_source_moments(ensemble, density_eigenvalue_tolerance=1e-13)
        self.assertEqual(fallback_call.call_count, 2)

    def test_cached_runner_calls_source_once_for_two_channel_rows(self):
        runner = load_runner()
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
        calls = 0

        def source_once(source_ensemble, **_kwargs):
            nonlocal calls
            calls += 1
            return gm.GramMomentResult(
                coherent_correlation=torch.zeros(1, dtype=torch.float64),
                w=torch.zeros(1, dtype=torch.float64),
                diagnostics=({"route": "TEST", "fast_path_gate": {}},),
            )

        result = runner.evaluate_fixed_ensemble(
            ensemble,
            torch.tensor([0.02, 0.03], dtype=torch.float64),
            torch.tensor([0.001, 0.04], dtype=torch.float64),
            density_eigenvalue_tolerance=1e-13,
            beta_reconciliation=0.95,
            awgn_samples=2,
            awgn_generator=torch.Generator().manual_seed(7),
            source_moment_evaluator=source_once,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(result["source_moments"]["call_count"], 1)
        self.assertEqual(len(result["per_state"]), 2)
        self.assertTrue(result["all_finite"])

    def test_changed_physical_ensemble_requires_another_source_evaluation(self):
        runner = load_runner()
        calls = 0

        def source_once(source_ensemble, **_kwargs):
            nonlocal calls
            calls += 1
            return gm.GramMomentResult(
                coherent_correlation=torch.zeros(1, dtype=torch.float64),
                w=torch.zeros(1, dtype=torch.float64),
                diagnostics=({"route": "TEST", "fast_path_gate": {}},),
            )

        for kind, va, nu in (("uniform", 0.5, None), ("uniform", 1.0, None), ("mb", 1.0, 0.1), ("mb", 1.0, 0.2)):
            runner.evaluate_fixed_ensemble(
                reference_ensemble(kind, batch_size=1, modulation_variance=va, nu_mb=nu),
                torch.tensor([0.02], dtype=torch.float64),
                torch.tensor([0.001], dtype=torch.float64),
                density_eigenvalue_tolerance=1e-13,
                beta_reconciliation=0.95,
                awgn_samples=2,
                awgn_generator=torch.Generator().manual_seed(7),
                source_moment_evaluator=source_once,
            )
        self.assertEqual(calls, 4)

    def test_cached_downstream_matches_generic_holevo_on_fast_c4_fixture(self):
        runner = load_runner()
        source = fast_c4_ensemble()
        transmittance = torch.tensor([1.0e-6, 2.0e-6], dtype=torch.float64)
        epsilon = torch.tensor([0.001, 0.04], dtype=torch.float64)
        cached = runner.evaluate_fixed_ensemble(
            source,
            transmittance,
            epsilon,
            density_eigenvalue_tolerance=1e-13,
            beta_reconciliation=0.95,
            awgn_samples=2,
            awgn_generator=torch.Generator().manual_seed(7),
        )
        generic = holevo_information(
            runner._repeat_ensemble(source, 2),
            transmittance,
            epsilon,
            backend="c4_gram",
            density_eigenvalue_tolerance=1e-13,
        )
        torch.testing.assert_close(
            torch.tensor(
                [row["chi_BE"] for row in cached["per_state"]], dtype=torch.float64
            ),
            generic.chi_be,
            rtol=1e-12,
            atol=1e-12,
        )

    def test_checkpoint_serializes_cli_path(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            runner._write_json(checkpoint, {"parameters": {"config": Path("configs/default.yaml")}})
            self.assertEqual(
                json.loads(checkpoint.read_text(encoding="utf-8"))["parameters"]["config"],
                str(Path("configs/default.yaml")),
            )


if __name__ == "__main__":
    unittest.main()
