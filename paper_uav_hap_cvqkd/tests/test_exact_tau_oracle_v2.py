"""Synthetic-only regression tests for the V2 exact-tau oracle producer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    from flint import acb, arb, ctx
    import mpmath as mp
except ImportError:  # certification dependencies are isolated from production
    acb = arb = ctx = mp = None


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "certify_exact_tau_oracle_v2.py"
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))


@unittest.skipIf(arb is None or mp is None, "requires combined isolated certification environment")
class ExactTauOracleV2Tests(unittest.TestCase):
    def test_high_precision_spectrum_uses_available_mpmath_hermitian_solver(self):
        import mpmath as mp
        from scripts.certify_exact_tau_oracle_v2 import high_precision_spectrum

        sectors = [mp.matrix([[mp.mpf("0.25"), 0], [0, mp.mpf("0.75")]])]
        with patch(
            "scripts.certify_exact_tau_oracle_v2.build_mp_sectors",
            return_value=sectors,
        ):
            result = high_precision_spectrum([0.5, 0.5], [0j, 1 + 0j], 50)
        self.assertEqual(len(result["sector_eigenvalues"]), 1)
        self.assertEqual(len(result["sector_eigenvalues"][0]), 2)

    @classmethod
    def setUpClass(cls) -> None:
        specification = importlib.util.spec_from_file_location("exact_tau_oracle_v2", SCRIPT)
        cls.oracle = importlib.util.module_from_spec(specification)
        assert specification.loader is not None
        specification.loader.exec_module(cls.oracle)

    @staticmethod
    def _diagonal_sector(values):
        size = len(values)
        return [[acb(values[row]) if row == column else acb(0)
                 for column in range(size)] for row in range(size)]

    def test_exact_candidate_tau_is_the_requested_binary64_dyadic(self) -> None:
        payload = self.oracle.exact_tau_payload()
        numerator, power = self.oracle.exact_dyadic_from_float_hex(
            "0x1.c25c268497682p-44"
        )
        self.assertEqual(payload["binary64_hex"], "0x1.c25c268497682p-44")
        self.assertEqual(int(payload["numerator"]), numerator)
        self.assertEqual(payload["denominator_power_two"], power)
        self.assertEqual(float.fromhex(payload["binary64_hex"]), 1e-13)

    def test_binary64_lift_is_exact_not_short_decimal_reparse(self) -> None:
        value = float.fromhex("0x1.0000000000001p-1")
        with mp.workdps(80):
            lifted = self.oracle.mp_from_binary64(value)
            numerator, denominator = value.as_integer_ratio()
            self.assertEqual(lifted, mp.mpf(numerator) / denominator)

    def test_dyadic_bracket_floor_preserves_high_precision_outside_context(self) -> None:
        with mp.workdps(100):
            value = mp.mpf(
                "4.4775903260919510331829160012222374503988850229960684562176e-14"
            )
        with mp.workprec(300):
            expected = int(mp.floor(value * mp.power(2, 180)))
        with mp.workdps(15):
            observed = self.oracle._dyadic_floor(value, 180)
        self.assertEqual(observed, expected)

    def test_shifted_inertia_proves_above_below_and_zero_unresolved(self) -> None:
        tau = arb((1, -20))
        delta = arb((1, -60))
        sectors = [self._diagonal_sector([tau - delta, tau + delta])]
        numerator, power = 1, 20
        result = self.oracle.certify_inertia_at_dyadic_threshold(
            sectors, numerator, power,
            precision_bits=[160, 256], maximum_seconds_per_point=5,
        )
        self.assertEqual(result["status"], "CERTIFIED_INERTIA")
        self.assertEqual(
            (result["n_positive"], result["n_negative"], result["n_zero_or_unresolved"]),
            (1, 1, 0),
        )
        exact_zero = [self._diagonal_sector([tau])]
        unresolved = self.oracle.certify_inertia_at_dyadic_threshold(
            exact_zero, numerator, power,
            precision_bits=[160], maximum_seconds_per_point=5,
        )
        self.assertEqual(unresolved["status"], "UNCERTIFIED")
        self.assertEqual(unresolved["n_zero_or_unresolved"], 1)

    def test_inertia_change_proves_single_eigenvalue_bracket_and_distance(self) -> None:
        ctx.prec = 256
        tau_numerator, tau_power = 1, 20
        tau = mp.mpf(1) / (1 << 20)
        below = tau - mp.mpf(1) / (1 << 30)
        above = tau + mp.mpf(1) / (1 << 29)
        sector = self._diagonal_sector([
            arb((int(below * (1 << 40)), -40)),
            arb((int(above * (1 << 40)), -40)),
        ])
        below_bracket = self.oracle.prove_eigenvalue_bracket(
            [sector], below,
            expected_below_at_left=0, expected_below_at_right=1,
            bracket_denominator_power_two=80, maximum_expansions=2,
            precision_bits=[160, 256], maximum_seconds_per_point=5,
        )
        above_bracket = self.oracle.prove_eigenvalue_bracket(
            [sector], above,
            expected_below_at_left=1, expected_below_at_right=2,
            bracket_denominator_power_two=80, maximum_expansions=2,
            precision_bits=[160, 256], maximum_seconds_per_point=5,
        )
        self.assertEqual(below_bracket["status"], "CERTIFIED_SINGLE_EIGENVALUE_BRACKET")
        self.assertEqual(above_bracket["status"], "CERTIFIED_SINGLE_EIGENVALUE_BRACKET")
        below_distance = self.oracle.certified_distance_from_tau(
            below_bracket,
            tau_numerator=tau_numerator,
            tau_denominator_power_two=tau_power,
            side="BELOW",
        )
        above_distance = self.oracle.certified_distance_from_tau(
            above_bracket,
            tau_numerator=tau_numerator,
            tau_denominator_power_two=tau_power,
            side="ABOVE",
        )
        self.assertEqual(below_distance["status"], "CERTIFIED_POSITIVE_DISTANCE_INTERVAL")
        self.assertEqual(above_distance["status"], "CERTIFIED_POSITIVE_DISTANCE_INTERVAL")

    def test_distance_rejects_a_bracket_that_touches_wrong_side(self) -> None:
        tau_numerator, tau_power = self.oracle.exact_dyadic_from_float_hex(
            "0x1.c25c268497682p-44"
        )
        bracket = {
            "status": "CERTIFIED_SINGLE_EIGENVALUE_BRACKET",
            "lower": self.oracle._dyadic_payload(tau_numerator - 1, tau_power),
            "upper": self.oracle._dyadic_payload(tau_numerator, tau_power),
        }
        result = self.oracle.certified_distance_from_tau(
            bracket,
            tau_numerator=tau_numerator,
            tau_denominator_power_two=tau_power,
            side="BELOW",
        )
        self.assertEqual(result["status"], "UNCERTIFIED_DISTANCE")

    def test_schema_and_source_prohibit_complex128_reference(self) -> None:
        schema = json.loads((ROOT / "schemas" / "exact_tau_oracle_v2.schema.json").read_text(
            encoding="utf-8"
        ))
        self.assertEqual(schema["properties"]["candidate_threshold_status"]["const"],
                         "PROPOSED_UNAPPROVED")
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("eigvalsh(0.5", source)
        self.assertNotIn("np.", source)
        self.assertIn("complex128_reference_used", source)


if __name__ == "__main__":
    unittest.main()
