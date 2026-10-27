"""Focused regression checks for the explicitly approved Phase A changes."""
import copy
import unittest
from unittest.mock import patch

import mpmath as mp
import numpy as np

import model as m
import run

PROTOCOL = COVERAGE = CONTEXTS = None
EVALUATIONS = []


class ApprovedConventionTests(unittest.TestCase):
    def test_equations_reused_without_replacement(self):
        self.assertIs(m.correlation_eq14, m.previous.correlation_eq14)
        self.assertIs(m.components, m.previous.components)
        for digits in (80, 110):
            with mp.workdps(digits):
                t, xi, c, w = map(mp.mpf, (".25", ".125", ".75", ".0625"))
                self.assertEqual(m.correlation_eq14(t, xi, c, w),
                                 2*mp.sqrt(t)*c-mp.sqrt(2*t*xi*w))
                self.assertEqual(m.correlation_eq14(t, 0, c, w), 2*mp.sqrt(t)*c)
                self.assertEqual(m.correlation_eq14(t, xi, c, 0), 2*mp.sqrt(t)*c)
        with self.assertRaises(ValueError): m.components(1, 1, 0, 100, 0)

    def test_all_existing_uniform_and_mb_sources_use_approved_variance(self):
        for family, expected in [("Uniform", 33), ("MB", 179)]:
            rows = [r for r in COVERAGE if r["family"] == family and r.get("source_path")]
            self.assertEqual(len(rows), expected)
            for r in rows:
                with self.subTest(family=family, VA=r["VA"], nu=r["nu_raw"]):
                    self.assertEqual(r["identity_status"], "CURRENTLY_VERIFIED_PASS")
                    self.assertEqual(r["variance_convention_status"], "CURRENTLY_VERIFIED_PASS")
                    self.assertLessEqual(abs(2*r["nbar"]-r["Vmod"]), 2e-12)
                    self.assertLessEqual(abs(r["source_variance"]-r["Vmod"]), 2e-12)

    def test_truncation_accepted_without_normalizing_or_moving_atom(self):
        for context in CONTEXTS:
            self.assertTrue(context["numerical_experiment_accepted"])
            self.assertFalse(context["law_mathematically_valid"])
            self.assertFalse(context["renormalized"])
            self.assertFalse(context["clipped"])
            self.assertEqual(context["mathematical_status"], "TRUNCATED_LAW_NOT_NORMALIZED")
            hi = context["precision"][-1]
            self.assertGreater(hi["stable_tail"], 0)
            self.assertAlmostEqual(hi["mean_eta_xi"], .0186*hi["m1"]+.005*hi["M0"], places=15)
            # The two binary64 exports can differ by one rounding unit.
            self.assertLessEqual(abs(hi["atom_noise"]-.005*hi["P0"]), np.spacing(hi["atom_noise"]))
        zero = CONTEXTS[0]
        self.assertGreater(zero["probability_deficit"], PROTOCOL["numerical"]["mass_tolerance"])
        self.assertLess(zero["moments"]["M0"], 1)
        saved = m.read(m.PREVIOUS/"channel_preflight.json")
        for k in ["M0", "mh", "m1", "mean_eta_xi", "atom_noise", "stable_tail"]:
            self.assertEqual(zero["precision"][-1][k], saved["precision"][-1][k])

    def test_end_to_end_uniform_and_mb_same_effective_channel_in_mi_and_covariance(self):
        helper = m.helpers()
        for family in ["Uniform", "MB"]:
            row = min((r for r in COVERAGE if r["family"] == family
                and r["convergence_status"] == "CURRENTLY_VERIFIED_PASS"), key=lambda r: r["VA"])
            source = run.source_with_ensemble(row)
            with patch.object(helper.legacy, "full_holevo", side_effect=AssertionError("Full Z forbidden")), \
                 patch.object(helper.legacy, "spectrum", side_effect=AssertionError("Cap forbidden")):
                value = m.evaluate(source, CONTEXTS[0], PROTOCOL)
            moments = CONTEXTS[0]["moments"]
            t = moments["mh"]**2
            noise = (moments["m1"]-t)*source["VA"]+.0186*moments["m1"]+.005*moments["M0"]
            self.assertEqual(value["eta_f"], t)
            self.assertEqual(value["N_effective"], noise)
            self.assertEqual(value["Vmod"], source["VA"])
            self.assertEqual(value["V"], 1+source["VA"])
            self.assertAlmostEqual(value["W"], 1+t*source["VA"]+noise, places=14)
            p, alpha = source["p"], source["alpha"]
            gh64 = helper.homodyne_mi(p, alpha, t, 1+noise, order=64)
            independent, error = helper.independent_mi(p, alpha, t, 1+noise)
            self.assertLess(abs(gh64-value["I_AB"]), 2e-10)
            self.assertLess(abs(independent-value["I_AB"]), 2e-10)
            self.assertLess(error, 2e-10)
            for kwargs in [dict(grouped=False), dict(axis="P")]:
                self.assertLess(abs(helper.homodyne_mi(p, alpha, t, 1+noise, order=128, **kwargs)
                                    - value["I_AB"]), 2e-10)
            lo = m.components(source["VA"], t, noise/t, source["C"], source["w"], digits=80)
            with mp.workdps(120):
                for k in ["Z_manuscript_eq14", "chi_BE"]:
                    self.assertLess(abs(mp.mpf(lo["decimal"][k])-mp.mpf(value["decimal"][k])), mp.mpf("2e-11"))
            a, b, z = value["V"], value["W"], value["Z_manuscript_eq14"]
            gamma = np.array([[a,0,z,0], [0,a,0,-z], [z,0,b,0], [0,-z,0,b]])
            omega = np.kron(np.eye(2), [[0.,1.],[-1.,0.]])
            spectrum = np.sort(np.abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
            np.testing.assert_allclose(spectrum, sorted([value["nu_1"], value["nu_2"]]), atol=2e-11, rtol=0)
            self.assertEqual(value["K_raw"], .95*value["I_AB"]-value["chi_BE"])
            EVALUATIONS.append(dict(family=family, VA=source["VA"], nu_raw=source["nu_raw"],
                zenith_deg=0, scope="FOCUSED_REGRESSION_FIXTURE_NOT_PILOT", **value,
                GH64=gh64, independent_MI=independent, independent_MI_error=error))

    def test_missing_receipt_is_evidence_gap_not_incorrect_cw(self):
        fixed = next(r for r in COVERAGE if r.get("ensemble_hash") == PROTOCOL["fixed_MB"]["ensemble_hash"])
        self.assertEqual(fixed["identity_status"], "CURRENTLY_VERIFIED_PASS")
        self.assertEqual(fixed["convergence_status"], "CONVERGENCE_EVIDENCE_NOT_LOCATED")
        self.assertEqual(fixed["cw_verdict"], "NOT_CLASSIFIED_INCORRECT")
        with patch.object(m, "components", side_effect=AssertionError("Premature rate evaluation")), \
             self.assertRaisesRegex(m.ModelBlocked, "not classified as incorrect"):
            m.evaluate(fixed, CONTEXTS[0], PROTOCOL)

    def test_unapproved_variance_policy_or_physics_rejected(self):
        for field, value in [("VA_to_Vmod_mapping", "UNRESOLVED_AUTHOR_REVIEW_REQUIRED"),
                ("source_normalization", "Vmod=nbar/2"), ("correlation_policy", "full_Z"), ("xi_det", .001)]:
            protocol = copy.deepcopy(PROTOCOL); protocol[field] = value
            with self.assertRaises(ValueError): m.validate_protocol(protocol)
        protocol = copy.deepcopy(PROTOCOL); protocol["physical"]["Dr_m"] = .55
        with self.assertRaises(ValueError): m.validate_protocol(protocol)
        protocol = copy.deepcopy(PROTOCOL); protocol["truncation_policy"]["renormalize"] = True
        with self.assertRaises(ValueError): m.validate_protocol(protocol)

    def test_failed_or_unbound_context_still_blocks(self):
        for field, value in [("numerical_status", "FAILED"), ("renormalized", True),
                ("clipped", True), ("protocol_sha256", "different"), ("numerical_experiment_accepted", False)]:
            context = copy.deepcopy(CONTEXTS[0]); context[field] = value
            with self.assertRaisesRegex(m.ModelBlocked, "channel context"):
                m.evaluate({}, context, PROTOCOL)

    def test_receipt_binding_and_full_ladder_still_required(self):
        audit = run.read(run.OUT/"receipt_investigation.json")
        for item in audit["source_evidence"]:
            if not item["receipts"]: continue
            payload = run.read(run.ROOT/item["payload_path"])
            receipt = run.read(run.ROOT/item["receipts"][0]["path"])
            self.assertEqual(run.check_receipt(payload, item["payload_sha256"], receipt), "CURRENTLY_VERIFIED_PASS")
            bad = copy.deepcopy(receipt)
            for key in ["payload_sha256", "payload_file_sha256", "source_sha256"]: bad.pop(key, None)
            self.assertEqual(run.check_receipt(payload, item["payload_sha256"], bad), "UNBOUND")
            bad = copy.deepcopy(receipt)
            diagnostic = bad["diagnostic"] if "diagnostic" in bad else bad["diagnostics"][0]
            diagnostic["fallback_rows"] = []
            self.assertEqual(run.check_receipt(payload, item["payload_sha256"], bad), "BOUND_INCOMPLETE_LADDER")

    def test_source_tampering_rejected(self):
        row = next(r for r in COVERAGE if r["convergence_status"] == "CURRENTLY_VERIFIED_PASS")
        for field, value in [("C", row["C"]+.01), ("w", -1), ("VA", row["VA"]/4)]:
            source = run.source_with_ensemble(row); source[field] = value
            with self.assertRaises(ValueError): m.evaluate(source, CONTEXTS[0], PROTOCOL)
