import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _train import _phase_coefficient, _phase_provenance
from src.channel.phase_noise import (
    phase_noise_coefficient,
    phase_parameter_provenance,
)
from src.validation.publication_manifest import canonical_json_sha256


def config(cn_phi2=2.0e-16, wavelength_m=1.55e-6, h_hap_m=20000.0, h_uav_m=1000.0):
    return {
        "channel": {
            "h_hap_m": h_hap_m,
            "h_uav_m": h_uav_m,
            "zenith_angle_rad": 0.0,
            "wavelength_m": wavelength_m,
            "cn2_m_minus_two_thirds": 1.0e-16,
            "cn_phi2_m_minus_two_thirds": cn_phi2,
            "cn_phi2_mapping_status": "validated",
            "cn_phi2_author_approved": True,
        }
    }


class PhaseParameterFreezeTests(unittest.TestCase):
    def test_provenance_contains_si_inputs_and_derived_values(self):
        record = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        self.assertEqual(record["parameterization"], "scenario_level_effective_Cn_phi2")
        self.assertEqual(record["cn_phi2_m_minus_two_thirds"], 2.0e-16)
        self.assertEqual(record["wavelength_m"], 1.55e-6)
        self.assertEqual(record["link_distance_m"], 19000.0)
        self.assertEqual(record["units"]["cn_phi2_m_minus_two_thirds"], "m^(-2/3)")
        self.assertEqual(record["units"]["wavelength_m"], "m")
        self.assertEqual(record["units"]["link_distance_m"], "m")
        self.assertEqual(record["units"]["tau_phi2"], "dimensionless")
        self.assertEqual(record["units"]["c_phi"], "dimensionless")
        self.assertTrue(record["c_phi_is_derived"])
        self.assertEqual(
            record["cn_phi2_relation_to_cn2_profile"],
            "effective scalar representation of the same physical turbulence; "
            "validated C_n^2(h)->C_n,phi^2 mapping remains unresolved",
        )

    def test_c_phi_is_derived_from_tau_and_has_no_independent_input(self):
        record = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        self.assertEqual(record["c_phi"], phase_noise_coefficient(record["tau_phi2"]))
        self.assertNotIn("c_phi_configured", record)

    def test_cn_phi2_changes_tau_and_c_phi(self):
        low = phase_parameter_provenance(1.0e-16, 1.55e-6, 19000.0)
        high = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        self.assertNotEqual(low["tau_phi2"], high["tau_phi2"])
        self.assertNotEqual(low["c_phi"], high["c_phi"])

    def test_wavelength_and_link_distance_change_phase_provenance(self):
        reference = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        different_wavelength = phase_parameter_provenance(2.0e-16, 1.50e-6, 19000.0)
        different_link = phase_parameter_provenance(2.0e-16, 1.55e-6, 20000.0)
        self.assertNotEqual(reference["tau_phi2"], different_wavelength["tau_phi2"])
        self.assertNotEqual(reference["tau_phi2"], different_link["tau_phi2"])

    def test_legacy_cn2_does_not_enter_phase_provenance(self):
        first = config()
        second = copy.deepcopy(first)
        second["channel"]["cn2_m_minus_two_thirds"] = 1.0e-15
        self.assertEqual(_phase_provenance(first), _phase_provenance(second))

    def test_configured_phase_provenance_is_resolved_from_link_geometry(self):
        record = _phase_provenance(config())
        self.assertEqual(record["link_distance_m"], 19000.0)
        self.assertEqual(_phase_coefficient(config()), record["c_phi"])
        self.assertEqual(record["c_phi"], phase_parameter_provenance(
            2.0e-16, 1.55e-6, 19000.0
        )["c_phi"])

    def test_missing_phase_value_fails_closed(self):
        unresolved = config(None)
        with self.assertRaisesRegex(ValueError, "author-approved"):
            _phase_provenance(unresolved)

    def test_nonzero_phase_with_unresolved_common_turbulence_mapping_fails_closed(self):
        unresolved = config()
        unresolved["channel"]["cn_phi2_mapping_status"] = "unresolved"
        unresolved["channel"]["cn_phi2_author_approved"] = False
        with self.assertRaisesRegex(ValueError, "validated"):
            _phase_provenance(unresolved)

    def test_explicit_zero_is_valid_for_test_only_callers(self):
        record = phase_parameter_provenance(0.0, 1.55e-6, 19000.0)
        self.assertEqual(record["tau_phi2"], 0.0)
        self.assertEqual(record["c_phi"], 0.0)

    def test_resolved_config_hash_changes_with_phase_inputs_and_link(self):
        base = config()
        changed_cn = copy.deepcopy(base)
        changed_cn["channel"]["cn_phi2_m_minus_two_thirds"] = 3.0e-16
        changed_wavelength = copy.deepcopy(base)
        changed_wavelength["channel"]["wavelength_m"] = 1.50e-6
        changed_link = copy.deepcopy(base)
        changed_link["channel"]["h_hap_m"] = 21000.0
        self.assertNotEqual(canonical_json_sha256(base), canonical_json_sha256(changed_cn))
        self.assertNotEqual(
            canonical_json_sha256(base), canonical_json_sha256(changed_wavelength)
        )
        self.assertNotEqual(canonical_json_sha256(base), canonical_json_sha256(changed_link))


if __name__ == "__main__":
    unittest.main()
