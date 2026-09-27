import tempfile
import unittest
from pathlib import Path

import torch

from scripts import run_exact_mb_test2 as runner
from src.cvqkd.gram_moments import GramMomentResult


class ExactMBTest2Tests(unittest.TestCase):
    def setUp(self):
        self.config = runner.load_yaml(runner.ROOT / "configs" / "default.yaml")

    def test_raw_to_repo_conversion_and_historical_bug_guard(self):
        self.assertEqual(runner.nu_mb_repo(0.15), 6.375)
        self.assertEqual(runner.nu_mb_repo(0.50), 21.25)
        correct = runner.build_mb_ensemble(self.config, 0.15, 2.0)
        wrong = runner.reference_ensemble(
            "mb", batch_size=1, modulation_variance=2.0, nu_mb=0.15,
            v_min=0.1, v_max=4.0, n_peak_photons=30.0,
        )
        self.assertNotEqual(runner.ensemble_hash(correct), runner.ensemble_hash(wrong))

    def test_common_ensemble_hash_and_exact_identity_cache(self):
        calls = []

        def source(ensemble, **_kwargs):
            calls.append(runner.ensemble_hash(ensemble))
            return GramMomentResult(
                torch.tensor([1.414213237782491], dtype=torch.float64),
                torch.tensor([7.818684597230892e-7], dtype=torch.float64),
                ({"route": "TEST_EXACT", "support_size": 256},),
            )

        channel = {
            "T_eff": 0.0002548668306761576,
            "epsilon_base": 0.0186,
            "c_phi": 0.0053911584758131901,
        }
        with tempfile.TemporaryDirectory() as directory:
            evaluator = runner.ExactMBEvaluator(
                self.config,
                channel,
                Path(directory),
                crn_seeds=(1,),
                mi_samples=2,
                source_evaluator=source,
                allow_legacy_exact_import=False,
            )
            row = evaluator(0.15, 2.0)
            self.assertEqual(
                {row["ensemble_hash"], row["mi_ensemble_hash"], row["source_ensemble_hash"], row["holevo_ensemble_hash"]},
                {calls[0]},
            )
            self.assertFalse(row["cache_hit"])
            second = runner.ExactMBEvaluator(
                self.config,
                channel,
                Path(directory),
                crn_seeds=(1,),
                mi_samples=2,
                source_evaluator=source,
                allow_legacy_exact_import=False,
            )(0.15, 2.0)
            self.assertTrue(second["cache_hit"])
            self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
