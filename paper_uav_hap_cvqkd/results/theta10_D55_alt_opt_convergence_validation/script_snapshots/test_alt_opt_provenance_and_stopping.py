"""Regression checks for cache identity and incomplete-search stopping."""
import copy
import unittest
from scripts.exact_cache_provenance import json_hash, source_hashes, verify_source_payload, objective_compatible
from scripts.run_theta10_D55_alt_opt import K_TOLERANCE, adaptive_maximize_1d, stopping_status, ExactSourceUnavailable, ExactCandidateFailure


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.code = b"x = 1\ny = 2\n"
        self.settings = {"precision_ladder": [1050, 1250, 1450]}
        self.payload = {"schema": "exact-mb-source-cache-v1", "ensemble_hash": "test-exact-ensemble",
            "nu_mb_raw_hex": .2.hex(), "nu_mb_repo_hex": (42.5 * .2).hex(), "V_A_hex": 5.5.hex(),
            "mb_convention": "nu_mb_repo=42.5*nu_mb_raw; raw grid is square_qam256(alpha0=sqrt(30))",
            "source_implementation": {"fixture.py": source_hashes(self.code)["raw_sha256"]}, "source_settings": self.settings,
            "support_size": 256, "C": 1.0, "w": .001, "source_moment_route": "ARBITRARY_PRECISION_FALLBACK"}
        self.rekey(self.payload)

    def rekey(self, p):
        from scripts.exact_cache_provenance import IDENTITY_FIELDS
        p["cache_key"] = json_hash({k: p[k] for k in IDENTITY_FIELDS})

    def test_lf_crlf_share_canonical_identity_preserve_raw(self):
        lf = verify_source_payload(self.payload, self.settings, {"fixture.py": self.code})
        crlf = verify_source_payload(self.payload, self.settings, {"fixture.py": self.code.replace(b"\n", b"\r\n")})
        self.assertEqual(lf["canonical_source_cache_key"], crlf["canonical_source_cache_key"])
        self.assertEqual(self.payload["cache_key"], crlf["historical_cache_key"])
        self.assertNotEqual(crlf["implementation"]["fixture.py"]["raw_sha256"], crlf["implementation"]["fixture.py"]["canonical_lf_sha256"])

    def test_actual_source_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "IMPLEMENTATION_INCOMPATIBLE"):
            verify_source_payload(self.payload, self.settings, {"fixture.py": b"x = 3\ny = 2\n"})

    def test_whitespace_not_normalized(self):
        with self.assertRaises(ValueError):
            verify_source_payload(self.payload, self.settings, {"fixture.py": b"x=1\ny = 2\n"})

    def test_settings_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "SETTINGS_INCOMPATIBLE"):
            verify_source_payload(self.payload, {"precision_ladder": [80]}, {"fixture.py": self.code})

    def test_missing_identity_rejected(self):
        p = dict(self.payload)
        del p["source_implementation"]
        with self.assertRaisesRegex(ValueError, "IDENTITY_MISSING"):
            verify_source_payload(p, self.settings, {"fixture.py": self.code})

    def test_unknown_raw_hash_rejected(self):
        p = copy.deepcopy(self.payload)
        p["source_implementation"]["fixture.py"] = "0" * 64
        self.rekey(p)
        with self.assertRaisesRegex(ValueError, "IMPLEMENTATION_INCOMPATIBLE"):
            verify_source_payload(p, self.settings, {"fixture.py": self.code})

    def test_corrupted_historical_key_rejected(self):
        p = dict(self.payload, cache_key="unknown")
        with self.assertRaisesRegex(ValueError, "KEY_CORRUPTED"):
            verify_source_payload(p, self.settings, {"fixture.py": self.code})

    def test_objective_security_channel_or_code_change_rejected(self):
        identity = {"epsilon": .0186, "channel": .1, "evaluator": "direct_Z_minus", "code": "known"}
        expected = {"identity": identity, "sha256": json_hash(identity)}
        self.assertTrue(objective_compatible(expected, expected))
        for k, v in (("epsilon", .02), ("channel", .2), ("evaluator", "full_Z"), ("code", "changed")):
            altered = {**identity, k: v}
            self.assertFalse(objective_compatible({"identity": altered, "sha256": json_hash(altered)}, expected))
        self.assertFalse(objective_compatible(None, expected))

    def test_restore_rejects_unattested_objective_cache(self):
        from scripts.run_theta10_D55_alt_opt import ExactObjective
        obj = ExactObjective.__new__(ExactObjective)
        obj.objective_identity = {"identity": {"security": "direct_Z_minus"}, "sha256": json_hash({"security": "direct_Z_minus"})}
        with self.assertRaisesRegex(ValueError, "IDENTITY_INCOMPATIBLE_OR_MISSING"):
            obj.restore_objective_rows([], None)

    def test_cache_hit_rejects_mutated_channel_or_settings(self):
        from scripts.run_theta10_D55_alt_opt import ExactObjective
        obj = ExactObjective.__new__(ExactObjective)
        obj.config = {"epsilon": .0186}
        obj.channel = {"T": .1}
        obj.runtime_settings_hash = json_hash({"config": obj.config, "channel": obj.channel})
        obj.channel["T"] = .2
        with self.assertRaisesRegex(ValueError, "OBJECTIVE_CONTEXT_MUTATED"):
            obj(.1, 5.5)

    def runtime_objective_fixture(self):
        from scripts.run_theta10_D55_alt_opt import ExactObjective, evaluate_candidate, unconstrained_config
        from scripts.exact_cache_provenance import source_settings
        obj = ExactObjective.__new__(ExactObjective)
        obj.config = unconstrained_config()
        obj.channel = {"T": .1}
        obj.runtime_settings_hash = json_hash({"config": obj.config, "channel": obj.channel})
        obj.runtime_source_settings_hash = json_hash(source_settings(obj.config))
        obj.runtime_evaluator_constants = tuple(evaluate_candidate.__globals__[k] for k in ("BETA", "EPSILON", "GH_ORDER"))
        return obj

    def test_cache_hit_rejects_changed_runtime_precision(self):
        from unittest.mock import patch
        obj = self.runtime_objective_fixture()
        with patch("src.cvqkd.gram_moments.PRECISION_LADDER", (80, 120)):
            with self.assertRaisesRegex(ValueError, "OBJECTIVE_SOURCE_SETTINGS_CHANGED"):
                obj(.1, 5.5)

    def test_cache_hit_rejects_changed_runtime_quadrature(self):
        from unittest.mock import patch
        from scripts.run_theta10_D55_alt_opt import evaluate_candidate
        obj = self.runtime_objective_fixture()
        with patch.dict(evaluate_candidate.__globals__, {"GH_ORDER": 16}):
            with self.assertRaisesRegex(ValueError, "OBJECTIVE_RUNTIME_EVALUATOR_SETTINGS_CHANGED"):
                obj(.1, 5.5)

    def test_nonfinite_parameter_identity_rejected(self):
        p = copy.deepcopy(self.payload)
        p["V_A_hex"] = float("inf").hex()
        self.rekey(p)
        with self.assertRaisesRegex(ValueError, "PARAMETERS_INCOMPATIBLE"):
            verify_source_payload(p, self.settings, {"fixture.py": self.code})


class StoppingTests(unittest.TestCase):
    def closed(self):
        return {"status": "NUMERICALLY_CLOSED_LOCAL_BRACKET", "source_missing": [], "numerical_failures": [], "boundary_status": "INTERIOR"}

    def test_epsilon_value_and_completed_search(self):
        self.assertEqual(K_TOLERANCE, 1e-8)
        self.assertEqual(stopping_status(K_TOLERANCE, (self.closed(), self.closed())), "CONVERGED_NUMERICALLY")
        self.assertIsNone(stopping_status(2 * K_TOLERANCE, (self.closed(), self.closed())))

    def test_missing_probes_are_catalog_stagnation(self):
        s = {**self.closed(), "source_missing": [{"value": 5.45}]}
        self.assertEqual(stopping_status(0, (s, self.closed())), "STAGNATED_IN_EXACT_CATALOG")

    def test_earlier_unresolved_search_blocks_convergence(self):
        self.assertEqual(stopping_status(0, (self.closed(), self.closed()), previous_unresolved=True), "STAGNATED_IN_EXACT_CATALOG")

    def test_open_boundary_is_distinct(self):
        s = {**self.closed(), "boundary_status": "BOUNDARY_NOT_CLOSED"}
        self.assertEqual(stopping_status(0, (s, self.closed())), "UNRESOLVED_BOUNDARY")

    def test_failure_or_monotonicity_drop(self):
        self.assertEqual(stopping_status(0, ({**self.closed(), "numerical_failures": [{}]}, self.closed())), "NUMERICAL_FAILURE")
        self.assertEqual(stopping_status(-1e-4, (self.closed(), self.closed()), monotonic_warning=True), "NUMERICAL_FAILURE")
        self.assertEqual(stopping_status(-1e-4, (self.closed(), self.closed())), "NUMERICAL_FAILURE")

    def test_nonfinite_improvement_cannot_converge(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            self.assertEqual(stopping_status(value, (self.closed(), self.closed())), "NUMERICAL_FAILURE")

    def test_missing_initial_catalog_probe_never_closes_search(self):
        def objective(nu, va):
            if va == 1.0:
                raise ExactSourceUnavailable("missing initial point")
            return {"nu_raw": nu, "V_A": va, "SKR": -(va - 2.0) ** 2}
        result = adaptive_maximize_1d(variable="V_A", fixed=.1, values=[1.0, 1.9999999, 2.0, 2.0000001], objective=objective)
        self.assertEqual(result["status"], "BRACKETED_EXACT_CATALOG_SOURCE_MISSING")
        self.assertTrue(result["source_missing"])
        self.assertTrue(all("K" not in h for h in result["history"] if h["status"] == "EXACT_SOURCE_MISSING"))

    def test_all_numerical_failures_are_not_missing_source(self):
        def objective(nu, va):
            raise ExactCandidateFailure("invalid evaluator value")
        result = adaptive_maximize_1d(variable="V_A", fixed=.1, values=[1.0, 2.0], objective=objective)
        self.assertEqual(result["status"], "NUMERICAL_FAILURE")
        self.assertFalse(result["source_missing"])

    def test_singleton_search_checks_both_outer_sides(self):
        visited = []
        def objective(nu, va):
            visited.append(va)
            return {"nu_raw": nu, "V_A": va, "SKR": -(va - 1) ** 2}
        adaptive_maximize_1d(variable="V_A", fixed=.1, values=[1.0], objective=objective, parameter_tolerance=1)
        self.assertIn(.5, visited)
        self.assertIn(2., visited)


class BudgetTests(unittest.TestCase):
    def test_probe_retry_preserves_previous_failure(self):
        import tempfile
        from pathlib import Path
        from scripts.run_theta10_D55_alt_opt_convergence_validation import archive_probe_attempt
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "probe.json"
            old = '{"status":"TIMEOUT","elapsed_seconds":90}'
            p.write_text(old, encoding="utf-8")
            archive = archive_probe_attempt(p)
            p.write_text('{"status":"RUNNING"}', encoding="utf-8")
            self.assertEqual(archive.read_text(encoding="utf-8"), old)

    def test_source_supervisor_enforces_absolute_deadline(self):
        import sys
        import tempfile
        from scripts.run_theta10_D55_alt_opt_convergence_validation import bounded_process
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
            result = bounded_process([sys.executable, "-c", "import time; time.sleep(5)"], .4, log, poll_seconds=.02)
        self.assertTrue(result["deadline_exceeded"])
        self.assertLess(result["elapsed_seconds"], 3)
        self.assertNotEqual(result["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
