import copy
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _train import _phase_coefficient, _phase_provenance


def config():
    return {
        "channel": {
            "phase_model": "configured_phase_noise",
            "h_hap_m": 20000.0,
            "h_uav_m": 1000.0,
            "zenith_angle_rad": 0.0,
            "wavelength_m": 1.55e-6,
            "phase_noise": {
                "cn2_phase_m_minus_two_thirds": 1.0e-16,
                "l_phase_m": 1000.0,
            },
        }
    }


class PhaseParameterFreezeTests(unittest.TestCase):
    def test_phase_uses_separate_fixed_parameters(self):
        record = _phase_provenance(config())
        self.assertEqual(record["parameterization"], "configured_phase_noise")
        self.assertEqual(record["cn2_phase_m_minus_two_thirds"], 1.0e-16)
        self.assertEqual(record["l_phase_m"], 1000.0)
        self.assertAlmostEqual(record["tau_phi2"], 3.981908770225408e-3)
        self.assertEqual(_phase_coefficient(config()), record["c_phi"])

    def test_main_link_distance_does_not_change_l_phase(self):
        first = config()
        second = copy.deepcopy(first)
        second["channel"]["h_hap_m"] = 24000.0
        self.assertEqual(_phase_provenance(first), _phase_provenance(second))

    def test_wrong_or_missing_phase_model_fails_closed(self):
        missing = config()
        del missing["channel"]["phase_model"]
        with self.assertRaisesRegex(ValueError, "phase_model"):
            _phase_provenance(missing)
        wrong = config()
        wrong["channel"]["phase_model"] = "rytov_equivalent_hufnagel_valley"
        with self.assertRaisesRegex(ValueError, "phase_model"):
            _phase_provenance(wrong)

    def test_missing_phase_parameters_fail_closed(self):
        wrong = config()
        del wrong["channel"]["phase_noise"]
        with self.assertRaisesRegex(ValueError, "phase_noise"):
            _phase_provenance(wrong)


if __name__ == "__main__":
    unittest.main()
