import unittest

from scripts.run_exact_mb_test2 import build_mb_ensemble
from scripts.run_redesigned_global_mb_va_optimization import channel_audit, load_frozen_config


class RedesignedGlobalMBVATest(unittest.TestCase):
    def test_author_frozen_audit_and_unbounded_ensemble(self):
        config, freeze = load_frozen_config()
        audit, channel = channel_audit(config, freeze)
        self.assertEqual(audit["audit_status"], "CURRENTLY_VERIFIED_PASS")
        self.assertEqual(channel["c_phi"], 0.0)
        self.assertIsNone(config["cvqkd"]["n_peak_photons"])
        self.assertIsNone(config["cvqkd"]["v_a_budget_snu"])
        ensemble = build_mb_ensemble(config, 1.6, 12.0)
        self.assertAlmostEqual(float(ensemble.computed_va()[0]), 12.0, places=11)


if __name__ == "__main__":
    unittest.main()
