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
            "phase_model": "rytov_equivalent_hufnagel_valley",
            "h_hap_m": 20000.0,
            "h_uav_m": 1000.0,
            "zenith_angle_rad": 0.0,
            "wavelength_m": 1.55e-6,
            "aperture_radius_m": 0.04,
            "turbulence_profile": {
                "model": "hufnagel_valley",
                "wind_speed_m_per_s": 21.0,
                "cn2_ground_m_minus_two_thirds": 5e-14,
            },
        }
    }


class PhaseParameterFreezeTests(unittest.TestCase):
    def test_phase_is_derived_from_the_common_hv_integral(self):
        record = _phase_provenance(config())
        self.assertEqual(record["parameterization"], "rytov_equivalent_hufnagel_valley")
        self.assertEqual(record["link_distance_m"], 19000.0)
        self.assertAlmostEqual(record["tau_phi2"], 2.0 * record["sigma_R0_squared"])
        self.assertEqual(_phase_coefficient(config()), record["c_phi"])

    def test_old_free_phase_fields_do_not_override_the_derived_value(self):
        first = config()
        second = copy.deepcopy(first)
        second["channel"].update({
            "cn_phi2_m_minus_two_thirds": 999.0,
            "cn_phi2_mapping_status": "validated",
            "cn_phi2_author_approved": True,
        })
        self.assertEqual(_phase_provenance(first), _phase_provenance(second))

    def test_wrong_or_missing_phase_model_fails_closed(self):
        missing = config()
        del missing["channel"]["phase_model"]
        with self.assertRaisesRegex(ValueError, "phase_model"):
            _phase_provenance(missing)
        wrong = config()
        wrong["channel"]["phase_model"] = "free_cn_phi2"
        with self.assertRaisesRegex(ValueError, "phase_model"):
            _phase_provenance(wrong)

    def test_non_hv_profile_fails_closed(self):
        wrong = config()
        wrong["channel"]["turbulence_profile"]["model"] = "external_altitude_profile"
        with self.assertRaisesRegex(ValueError, "Hufnagel-Valley"):
            _phase_provenance(wrong)


if __name__ == "__main__":
    unittest.main()
