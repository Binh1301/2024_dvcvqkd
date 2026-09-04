from pathlib import Path
import unittest

import yaml
import hashlib
import json
import torch

from src.cvqkd import gram_moments

ROOT = Path(__file__).resolve().parents[1]


class ManifoldConsistentCwVjpAmendmentTests(unittest.TestCase):
    def test_frozen_fixture_b_is_prototype_generated_not_sector_perturbed(self):
        config = yaml.safe_load((ROOT / "configs/manifold_consistent_cw_vjp_validation_amendment_v1.yaml").read_text())
        fixture = config["fixture_b"]
        self.assertEqual(fixture["probability_rule"], "uniform_symbol_probability_1_over_256")
        self.assertEqual(fixture["prototype_rule"], "z_k=(k+1)+0i_for_k_0_to_63")
        self.assertEqual(fixture["direction_rule"], "dz_k=z_k")
        self.assertEqual(fixture["sector_construction"], "gram_moments._sectors(p,z)")
        self.assertFalse(any(config["lifecycle_guards"].values()))

    def test_center_and_endpoints_are_generated_on_the_c4_manifold(self):
        config = yaml.safe_load((ROOT / "configs/manifold_consistent_cw_vjp_validation_amendment_v1.yaml").read_text())
        fixture = config["fixture_b"]
        p = torch.full((64,), 1 / 256, dtype=torch.float64)
        z = torch.arange(1, 65, dtype=torch.float64).to(torch.complex128)
        dz = z
        source = yaml.safe_load((ROOT / config["fixture_b"]["finite_difference_source"]).read_text())
        h = source["finite_difference"]["step"]
        sectors = [gram_moments._sectors(p, value) for value in (z, z + h * dz, z - h * dz)]
        for values, expected in zip((z, z + h * dz, z - h * dz), (fixture["center_fast_gate"], fixture["plus_fast_gate"], fixture["minus_fast_gate"])):
            result, gate = gram_moments._fast(p, values)
            self.assertIsNotNone(result)
            self.assertTrue(gate["all_sectors_positive"])
            self.assertLessEqual(gate["sector_condition_number"], gram_moments.FAST_MAX_CONDITION)
            self.assertLessEqual(gate["sector_reconstruction_residual"], gram_moments.FAST_MAX_RESIDUAL)
            self.assertLessEqual(gate["residual_identity_relative_error"], gram_moments.FAST_MAX_RESIDUAL)
            self.assertAlmostEqual(gate["minimum_eigenvalue"], expected["minimum_eigenvalue"])
        self.assertTrue(all(not torch.equal(left, right) for left, right in zip(sectors[0], sectors[1])))
        payload = {"p": [value.hex() for value in p.tolist()], "z": [[value.real.hex(), value.imag.hex()] for value in z.tolist()], "dz": [[value.real.hex(), value.imag.hex()] for value in dz.tolist()]}
        self.assertEqual(hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), fixture["fixture_sha256"])


if __name__ == "__main__":
    unittest.main()
