import importlib.util
import json
from pathlib import Path
import sys
import unittest

import mpmath as mp
import torch

from src.cvqkd.holevo import coherent_state_vectors


SCRIPT = Path(__file__).parents[1] / "scripts" / "oracle_near_coincident_gram.py"
SCRIPTS_DIRECTORY = str(SCRIPT.parent)
if SCRIPTS_DIRECTORY not in sys.path:
    sys.path.insert(0, SCRIPTS_DIRECTORY)
SPEC = importlib.util.spec_from_file_location("near_coincident_gram_oracle", SCRIPT)
ORACLE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ORACLE)


class GramOracleTests(unittest.TestCase):
    def test_exact_overlap_matches_fock_inner_product_and_has_unit_diagonal(self):
        with mp.workdps(50):
            alpha_i = mp.mpc("0.31", "-0.27")
            alpha_j = mp.mpc("-0.14", "0.22")
            overlap = ORACLE.coherent_state_overlap(alpha_i, alpha_j)
            self.assertEqual(ORACLE.coherent_state_overlap(alpha_i, alpha_i), 1)
            amplitudes = torch.tensor(
                [complex(alpha_i), complex(alpha_j)], dtype=torch.complex128
            )
            fock = coherent_state_vectors(amplitudes, 80)
            fock_overlap = torch.sum(fock[0].conj() * fock[1])
            self.assertAlmostEqual(float(mp.re(overlap)), float(fock_overlap.real), places=14)
            self.assertAlmostEqual(float(mp.im(overlap)), float(fock_overlap.imag), places=14)

    def test_minus_cross_term_is_not_a_coherent_state_gram_diagonal(self):
        with mp.workdps(50):
            alpha = mp.mpc("0.5", "0.25")
            wrong = mp.exp(-abs(alpha) ** 2 - mp.conj(alpha) * alpha)
            self.assertNotEqual(wrong, 1)
            self.assertEqual(ORACLE.coherent_state_overlap(alpha, alpha), 1)

    def test_successive_oracle_gate_applies_frozen_tolerances(self):
        config = {
            "numerical_validation": {"fock": {
                "moment_absolute_tolerance": 1e-7,
                "moment_relative_tolerance": 1e-6,
                "information_absolute_tolerance_bits": 1e-6,
                "information_relative_tolerance": 1e-5,
            }}
        }
        state = {
            "Z": "0.5", "lambda1": "2", "lambda2": "1.1",
            "lambda3": "1.5", "chi_BE": "0.2", "raw_K": "-0.1",
        }
        previous = {"C": "2", "w": "0.25", "states": [state]}
        current = {"C": "2.00000001", "w": "0.25000001", "states": [state]}
        passes, _ = ORACLE._successive_oracles_converge(previous, current, config)
        self.assertTrue(passes)
        current["w"] = "0.251"
        passes, comparisons = ORACLE._successive_oracles_converge(
            previous, current, config
        )
        self.assertFalse(passes)
        self.assertFalse(comparisons["w"]["passes"])

    def test_saved_full_support_oracle_and_float64_diagnosis_are_fail_closed(self):
        root = SCRIPT.parents[1]
        for schema_name in (
            "near_coincident_gram_oracle.schema.json",
            "float64_gram_comparison.schema.json",
        ):
            json.loads((root / "schemas" / schema_name).read_text(encoding="utf-8"))
        oracle = json.loads(
            (root / "results" / "near_coincident_gram_oracle.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(oracle["full_mathematical_support_oracle_obtained"])
        self.assertEqual(oracle["selected_full_support_oracle_digits"], 1250)
        self.assertEqual(oracle["confirmation_full_support_oracle_digits"], 1450)
        self.assertEqual(oracle["selected_full_support_oracle"]["support_size"], 256)
        self.assertEqual(oracle["mutual_information_sample_count_for_raw_K"], 2048)
        self.assertTrue(
            oracle["successive_full_support_converges_under_frozen_tolerances"]
        )
        self.assertTrue(
            oracle["successive_full_support_tolerance_comparisons"]["w"]["passes"]
        )

        comparison = json.loads(
            (root / "results" / "float64_gram_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        stress = {
            float(row["threshold"]): row for row in comparison["rows"]
            if row["fixture"] == "near_coincident_pseudoinverse_stress"
        }
        for threshold in (1e-14, 1e-13):
            reference = stress[threshold][
                "high_precision_full_support_1250_digit_reference"
            ]
            self.assertTrue(reference["passes_all_frozen_tolerances"])
            self.assertAlmostEqual(
                reference["maximum_absolute_gram_minus_hp"]["raw_K"],
                reference["maximum_absolute_gram_minus_hp"]["chi_BE"],
                places=15,
            )
        self.assertFalse(
            stress[1e-12]["high_precision_full_support_1250_digit_reference"][
                "passes_all_frozen_tolerances"
            ]
        )
        self.assertTrue(
            comparison["stress_threshold_plateau_1e_minus_14_vs_1e_minus_13"][
                "identical_support_and_passes_frozen_tolerances"
            ]
        )


if __name__ == "__main__":
    unittest.main()
