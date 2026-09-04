from pathlib import Path
import unittest

import yaml
import torch
from unittest.mock import patch

from src.cvqkd import gram_moments

ROOT = Path(__file__).resolve().parents[1]


class FastRouteFeasibilityAmendmentTests(unittest.TestCase):
    def test_frozen_amendment_preserves_ap_only_center_and_fast_synthetic_preflight(self):
        config = yaml.safe_load((ROOT / "configs/fast_route_gradient_vjp_feasibility_amendment_v1.yaml").read_text())
        self.assertEqual(config["frozen_center"]["route"], "ARBITRARY_PRECISION_FALLBACK")
        self.assertEqual(config["frozen_center"]["gradient_eligibility"], "INELIGIBLE")
        self.assertEqual(config["synthetic_fast_fixture"]["dimension"], 64)
        self.assertFalse(any(config["lifecycle_guards"].values()))

    def test_synthetic_sector_fixture_satisfies_existing_fast_gate(self):
        config = yaml.safe_load((ROOT / "configs/fast_route_gradient_vjp_feasibility_amendment_v1.yaml").read_text())
        fixture = config["synthetic_fast_fixture"]
        p = torch.full((fixture["dimension"],), fixture["symbol_probability"], dtype=torch.float64)
        z = torch.full((fixture["dimension"],), complex(fixture["prototype_real"], fixture["prototype_imag"]), dtype=torch.complex128)
        sectors = [torch.eye(fixture["dimension"], dtype=torch.complex128) * fixture["sector_eigenvalue"] for _ in range(fixture["sector_count"])]
        with patch.object(gram_moments, "_sectors", return_value=sectors):
            result, gate = gram_moments._fast(p, z)
        self.assertIsNotNone(result)
        self.assertTrue(gate["all_sectors_positive"])
        self.assertEqual(gate["sector_condition_number"], 1.0)


if __name__ == "__main__":
    unittest.main()
