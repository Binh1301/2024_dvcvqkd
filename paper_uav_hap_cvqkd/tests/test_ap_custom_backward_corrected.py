import unittest

from scripts.validate_corrected_ap_custom_backward import build_cheap_artifact


class CorrectedAPCustomBackwardValidationTests(unittest.TestCase):
    def test_cheap_fixtures_components_and_complex_convention_pass(self):
        artifact = build_cheap_artifact()

        self.assertEqual(artifact["status"], "CHEAP_FIXTURE_VALIDATION_PASS")
        self.assertEqual(len(artifact["fixtures"]), 4)
        for fixture in artifact["fixtures"]:
            self.assertTrue(fixture["direction"]["passes"], fixture["fixture"])
            self.assertTrue(fixture["component_direction"]["passes"], fixture["fixture"])

        convention = artifact["complex_gradient_convention"]
        self.assertTrue(convention["passes"])
        self.assertTrue(convention["checks"]["real_alpha"]["passes"])
        self.assertTrue(convention["checks"]["imaginary_alpha"]["passes"])

        self.assertEqual(
            [row["family"] for row in artifact["target_structure_preflight"]],
            ["ps", "gs_real", "gs_imag", "va"],
        )
        for row in artifact["target_structure_preflight"]:
            self.assertTrue(row["positive_probabilities"], row["family"])
            self.assertEqual(row["probability_sum"], 1.0)
            self.assertEqual(row["unique_state_count"], 256)
            self.assertNotEqual(row["directional_z_norm"], 0.0)


if __name__ == "__main__":
    unittest.main()
