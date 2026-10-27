"""Readiness/provenance/runner checks, with no pilot or new channel evaluation."""
import copy
import inspect
import unittest
from unittest.mock import patch

import model
import provenance
import run
from support import OUT, ROOT, PREVIOUS, prior_model, prior_run, read, sha, with_ensemble


class ReadinessTests(unittest.TestCase):
    def test_historical_spec_hash_recovered_and_versioned_spec_bound(self):
        protocol = read(OUT / "protocol.json")
        model.validate_protocol(protocol)
        spec = read(ROOT / protocol["experiment_spec_path"])
        self.assertEqual(sha(ROOT / spec["historical_spec"]["path"]),
            "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1")
        self.assertEqual(sha(ROOT / spec["current_repository_spec"]["path"]),
            "df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15")
        self.assertEqual(len(spec["source_identities"]), 81)
        run.check_pool_identity(spec["source_identities"], protocol)
        bad_pool = copy.deepcopy(spec["source_identities"])
        bad_pool[0]["ensemble_hash"] = "different"
        with self.assertRaises(model.ModelBlocked): run.check_pool_identity(bad_pool, protocol)
        for key in ["experiment_spec_sha256", "frozen_history_sha256"]:
            bad = copy.deepcopy(protocol); bad[key] = "changed"
            with self.assertRaises(ValueError): model.validate_protocol(bad)

    def test_exact_eq14_and_holevo_components_are_preserved(self):
        self.assertIs(model.correlation_eq14, prior_model.correlation_eq14)
        self.assertIs(model.components, prior_model.components)
        self.assertEqual(list(inspect.signature(model.evaluate).parameters), ["source", "context", "protocol"])
        self.assertNotIn("Z", inspect.signature(model.evaluate).parameters)

    def test_classifications_cover_the_proposed_pool_without_invalidating_missing_receipts(self):
        rows = prior_run.old.rows(OUT / "pilot_source_verification.csv")
        self.assertEqual(len(rows), 81)
        self.assertEqual(sum(r["family"] == "Uniform" for r in rows), 34)
        self.assertEqual(sum(r["family"] == "MB" for r in rows), 47)
        self.assertTrue(all(r["classification"] in provenance.ACCEPTED | {"INSUFFICIENT_EVIDENCE", "INVALID"} for r in rows))
        for r in rows:
            if r["reason"] == "FULL_NUMERICAL_CONVERGENCE_EVIDENCE_NOT_LOCATED":
                self.assertEqual(r["classification"], "INSUFFICIENT_EVIDENCE")
                self.assertEqual(r["identity_status"], "CURRENTLY_VERIFIED_PASS")

    def test_alternative_evidence_binds_both_exact_arrays_and_full_precision_history(self):
        rows = prior_run.old.rows(OUT / "pilot_source_verification.csv")
        row = next(r for r in rows if r["family"] == "Uniform" and float.fromhex(r["VA_hex"]) == 2.)
        row.update(VA=2., nu_raw=0., C=float(row["C"]), w=float(row["w"]))
        source = with_ensemble(row)
        node = read(ROOT / "results/effective_channel_va2/source_moments_va2.json")["sources"]["uniform"]
        self.assertIsNotNone(provenance.alternative_ladder(source, node))
        bad = copy.deepcopy(node); bad["amplitude_sha256"] = "different"
        self.assertIsNone(provenance.alternative_ladder(source, bad))
        bad = copy.deepcopy(node); bad["pmf_sha256"] = "different"
        self.assertIsNone(provenance.alternative_ladder(source, bad))
        bad = copy.deepcopy(node); bad["diagnostics"]["fallback_rows"] = []
        self.assertIsNone(provenance.alternative_ladder(source, bad))
        bad = copy.deepcopy(node); bad["diagnostics"]["fallback_rows"][-1]["C"] = "999"
        self.assertIsNone(provenance.alternative_ladder(source, bad))

    def test_metadata_or_same_Cw_without_input_digests_is_insufficient(self):
        self.assertIsNone(provenance.alternative_ladder({}, dict(C=1., w=0.,
            support_size=256, source_moment_route="ARBITRARY_PRECISION_FALLBACK",
            cache_origin="FRESH_EXACT_EVALUATION", precision_ladder=[1050,1250,1450])))

    def test_single_source_job_exact_VA_and_full_receipt(self):
        generated = list((OUT / "new_exact_source/exact_source_cache").glob("*.json"))
        if not generated:
            self.skipTest("Single authorized source job has not produced a payload; outcome remains blocked/pending")
        self.assertEqual(len(generated), 1)
        payload = read(generated[0])
        preflight = read(OUT / "source_job_preflight.json")
        self.assertEqual(payload["V_A_hex"], "0x1.9ffff84830112p+0")
        self.assertEqual(payload["nu_mb_raw_hex"], 0.0.hex())
        self.assertEqual(payload["ensemble_hash"], preflight["ensemble_hash"])
        receipt = read(OUT / "new_exact_source/source_receipts" / (payload["ensemble_hash"]+".json"))
        self.assertEqual(prior_run.check_receipt(payload, sha(generated[0]), receipt), "CURRENTLY_VERIFIED_PASS")

    def test_all_schemes_select_signed_raw_values_from_nested_candidates(self):
        protocol = read(OUT / "protocol.json")
        rows = [dict(zenith_deg=0, source_hash="uniform", family="Uniform", K_raw=-.2,
                     status="CURRENTLY_VERIFIED_PASS"),
                dict(zenith_deg=0, source_hash=protocol["fixed_MB"]["ensemble_hash"], family="MB",
                     K_raw=-.4, status="CURRENTLY_VERIFIED_PASS"),
                dict(zenith_deg=0, source_hash="otherMB", family="MB", K_raw=-.1,
                     status="CURRENTLY_VERIFIED_PASS")]
        selected = run.select(rows, protocol)
        self.assertEqual([r["K_raw"] for r in selected], [-.2, -.4, -.1])
        rows[0]["K_raw"] = -.01
        self.assertEqual(run.select(rows, protocol)[2]["source_hash"], "uniform")

    def test_candidate_evaluation_shares_context_and_preserves_negative_values(self):
        protocol = read(OUT / "protocol.json")
        common = object()
        base = dict(VA=.1, VA_hex=(.1).hex(), nu_raw=0., nu_raw_hex=0.0.hex(), C=.2, w=.01,
                    classification="VERIFIED_EXACT", source_path="fixture", source_sha256="fixture")
        sources = [dict(base, family=f, ensemble_hash=f) for f in ["Uniform", "MB"]]
        def evaluator(source, context, supplied):
            self.assertIs(context, common); self.assertIs(supplied, protocol)
            return dict(K_raw=-.1, I_AB=.1, beta_I_AB=.095, chi_BE=.195, Z_manuscript_eq14=.2)
        with patch.object(model, "evaluate", side_effect=evaluator) as call:
            records = run.candidate_records(0, common, sources, protocol)
        self.assertEqual(call.call_count, 2)
        self.assertEqual([r["K_raw"] for r in records], [-.1, -.1])

    def test_domain_failure_is_blank_status_without_Z_or_rate_repair(self):
        protocol = read(OUT / "protocol.json")
        source = dict(family="Uniform", VA=.1, VA_hex=(.1).hex(), nu_raw=0., nu_raw_hex=0.0.hex(),
            C=.2, w=.01, ensemble_hash="fixture", classification="VERIFIED_EXACT",
            source_path="fixture", source_sha256="fixture")
        with patch.object(model, "evaluate", side_effect=ValueError("Nonphysical covariance")):
            record = run.candidate_records(0, {}, [source], protocol)[0]
        self.assertEqual(record["status"], "FAILED_NUMERICAL_DOMAIN")
        self.assertIsNone(record["K_raw"])
        self.assertIsNone(record["Z_manuscript_eq14"])

    def test_readiness_guard_precedes_any_channel_calculation_or_output(self):
        with patch.object(run, "require_ready", side_effect=model.ModelBlocked("fixture dependency")), \
             patch.object(model, "channel_context", side_effect=AssertionError("Pilot must not start")), \
             self.assertRaises(model.ModelBlocked):
            run.pilot()
        self.assertFalse((OUT / "pilot").exists())

    def test_insufficient_source_is_blocked_before_rate_components(self):
        protocol = read(OUT / "protocol.json")
        context = read(PREVIOUS / "channel_preflight.json")[0]
        context["protocol_sha256"] = sha(OUT / "protocol.json")
        with patch.object(model, "components", side_effect=AssertionError("Premature rate component")), \
             self.assertRaisesRegex(model.ModelBlocked, "evidence insufficient"):
            model.evaluate(dict(classification="INSUFFICIENT_EVIDENCE"), context, protocol)


if __name__ == "__main__":
    unittest.main(verbosity=2)
