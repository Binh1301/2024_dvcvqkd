"""Focused Phase A update. Never launches a source job, pilot, or sweep."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
REPO = ROOT.parent
PREVIOUS = ROOT / "results/skr_vs_zenith_eq14_v43_20261023"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("_previous_phase_a", PREVIOUS / "run.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
sha, read = old.sha, old.read


def save(name, value):
    (OUT/name).write_bytes((json.dumps(old.clean(value), indent=2, ensure_ascii=False,
                                      allow_nan=False)+"\n").encode("utf-8"))


def write(name, rows):
    import csv
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def check_receipt(payload, file_digest, receipt):
    """Recognize both saved receipt formats; preserve the previous strict ladder check."""
    import mpmath as mp
    canonical = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    bound = (receipt.get("payload_file_sha256") == file_digest
             or receipt.get("source_sha256") == file_digest
             or receipt.get("payload_sha256") == canonical)
    if not bound:
        return "UNBOUND"
    diagnostics = receipt.get("diagnostics", [])
    diagnostic = receipt.get("diagnostic", diagnostics[0] if len(diagnostics) == 1 else {})
    ladder = receipt.get("precision_ladder", diagnostic.get("fallback_precisions"))
    levels = diagnostic.get("fallback_rows", [])
    if (ladder != payload["source_settings"]["precision_ladder"]
            or [x.get("digits") for x in levels] != ladder or not levels
            or diagnostic.get("support_size") != 256):
        return "BOUND_INCOMPLETE_LADDER"
    try:
        if any(x.get("rank") != 256 or x.get("resolved") is not True
               or not mp.isfinite(mp.mpf(x["minimum_eigenvalue"]))
               or mp.mpf(x["minimum_eigenvalue"]) <= 0 for x in levels):
            return "BOUND_UNRESOLVED_SUPPORT"
        if any(float(x[k]) != payload[k] for x in levels for k in ["C", "w"]):
            return "BOUND_LADDER_REQUIRES_REVIEW"
    except (KeyError, ValueError, TypeError):
        return "BOUND_MALFORMED_LADDER"
    return "CURRENTLY_VERIFIED_PASS"


def investigate_receipts(coverage):
    roots = sorted({(ROOT/r["source_path"]).parent.parent for r in coverage if r.get("source_path")})
    command = ["rg", "-l", "--glob", "*.json",
               '"fallback_rows"|"precision_ladder_decimal_digits"|"FULL_SUPPORT_CONVERGED"',
               *map(str, roots)]
    found = subprocess.run(command, capture_output=True, text=True)
    if found.returncode not in [0, 1]:
        raise RuntimeError(found.stderr)
    paths = sorted(set(Path(s) for s in found.stdout.splitlines()))
    receipts = [(p, read(p)) for p in paths]
    reviewed = []
    for row in coverage:
        if not row.get("source_path"):
            continue
        payload = read(ROOT/row["source_path"])
        matches, reviews = [], []
        for path, receipt in receipts:
            verdict = check_receipt(payload, row["source_sha256"], receipt)
            if verdict != "UNBOUND":
                record = dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), status=verdict)
                (matches if verdict == "CURRENTLY_VERIFIED_PASS" else reviews).append(record)
        row["previous_convergence_status"] = row["convergence_status"]
        row["convergence_status"] = ("CURRENTLY_VERIFIED_PASS" if matches else
            "BOUND_EVIDENCE_REQUIRES_REVIEW" if reviews else "CONVERGENCE_EVIDENCE_NOT_LOCATED")
        row["receipt_paths"] = ";".join(r["path"] for r in matches)
        row["cw_verdict"] = "IDENTITY_VERIFIED_NOT_RECOMPUTED" if matches else "NOT_CLASSIFIED_INCORRECT"
        row["Vmod"] = row["VA"]
        row["variance_convention_status"] = ("CURRENTLY_VERIFIED_PASS"
            if row["identity_status"] == "CURRENTLY_VERIFIED_PASS"
            and abs(2*row["nbar"]-row["VA"]) <= 2e-12
            and abs(row["source_variance"]-row["VA"]) <= 2e-12 else "FAILED")
        reviewed.append(dict(ensemble_hash=row["ensemble_hash"], payload_path=row["source_path"],
            payload_sha256=row["source_sha256"], pilot_member=row["pilot_member"],
            convergence_status=row["convergence_status"], receipts=matches, review_required=reviews,
            cache_origin=payload.get("cache_origin"), source_moment_route=payload.get("source_moment_route")))
    return dict(search_scope=[p.relative_to(ROOT).as_posix() for p in roots],
        candidate_files={p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
        source_evidence=reviewed, source_jobs=0, source_values_recomputed=False,
        conclusion="Missing saved ladder evidence does not establish incorrect C,w; no receipt was fabricated.")


def source_with_ensemble(row):
    from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config
    ensemble = make_ensemble(unconstrained_config(), row["family"], row["nu_raw"], row["VA"])
    return {**row, "p": ensemble.probabilities[0].numpy(), "alpha": ensemble.amplitudes[0].numpy()}


def phase_a():
    if (OUT/"gate.json").exists() or (OUT/"artifact_manifest.json").exists():
        raise FileExistsError("Preserve completed revision; use --verify-only")
    import model as m
    m.validate_protocol(read(OUT/"protocol.json"))
    protocol = read(OUT/"protocol.json")
    coverage, identity = old.inspect_catalog(protocol)
    receipts = investigate_receipts(coverage)
    save("receipt_investigation.json", receipts)
    write("source_catalog_coverage.csv", coverage)
    save("source_identity_audit.json", identity)
    contexts = [m.channel_context(angle, protocol) for angle in protocol["preflight_angles_deg"]]
    save("channel_preflight.json", contexts)
    import test_model
    test_model.PROTOCOL, test_model.COVERAGE, test_model.CONTEXTS = protocol, coverage, contexts
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(test_model))
    (OUT/"focused_tests.log").write_bytes(log.getvalue().encode())
    tests = dict(status="CURRENTLY_VERIFIED_PASS" if result.wasSuccessful() else "FAILED",
                 tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors))
    save("focused_tests.json", tests)
    save("focused_evaluator_checks.json", test_model.EVALUATIONS)
    pilot = [r for r in coverage if r.get("pilot_member") and r.get("source_path")]
    missing = [r for r in pilot if r["convergence_status"] != "CURRENTLY_VERIFIED_PASS"]
    model_ready = (result.wasSuccessful() and identity["identity_fail"] == 0
        and all(c["numerical_experiment_accepted"] for c in contexts)
        and all(r["variance_convention_status"] == "CURRENTLY_VERIFIED_PASS"
                for r in coverage if r.get("source_path")))
    blockers = [] if model_ready else ["FOCUSED_VALIDATION_FAILED"]
    if missing: blockers.append("PILOT_CONVERGENCE_EVIDENCE_INCOMPLETE")
    if identity["missing_Uniform_at_fixed_VA"]: blockers.append("MISSING_UNIFORM_AT_EXACT_FIXED_MB_VA")
    frozen = sha(ROOT/"docs/FINAL_MODEL_SPEC.md")
    if frozen != "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1":
        blockers.append("FROZEN_SPEC_HASH_DISCREPANCY")
    blockers.append("PILOT_ORCHESTRATION_NOT_IMPLEMENTED")
    gate = dict(status="PHASE_A_CONVENTIONS_VALIDATED_PILOT_DEPENDENCIES_PENDING" if model_ready else "FAILED",
        phase_A_model_conventions_ready=model_ready, phase_B_ready=False, blockers=blockers,
        resolved_blockers=["EQ10_SUPPORT_NORMALIZATION_FOR_THIS_EXPERIMENT", "VA_VMOD_MAPPING_UNRESOLVED"],
        probability_law_mathematically_normalized=False, source_counts=identity["counts"],
        existing_source_identity_pass=identity["identity_pass"],
        receipt_pass=sum(r.get("convergence_status") == "CURRENTLY_VERIFIED_PASS" for r in coverage),
        receipt_not_located=sum(r.get("convergence_status") == "CONVERGENCE_EVIDENCE_NOT_LOCATED" for r in coverage),
        pilot_existing=len(pilot), pilot_receipt_pass=len(pilot)-len(missing), pilot_evidence_pending=len(missing),
        pilot_sources_required=81, missing_uniform_VA_hex=protocol["fixed_MB"]["VA_hex"],
        frozen_spec_sha256=frozen, focused_test_status=tests["status"], focused_tests=tests["tests_run"],
        focused_channel_angles=protocol["preflight_angles_deg"],
        focused_source_angle_fixtures=len(test_model.EVALUATIONS), operational_candidate_evaluations=0,
        source_jobs=0, phases_B_to_F="NOT_RUN", manuscript_changed=False, production_changed=False,
        source_cache_changed=False, correlation_policy=m.POLICY,
        security_status=protocol["security_status"], lifecycle=protocol["lifecycle"],
        protocol_sha256=sha(OUT/"protocol.json"),
        producer_sha256={n: sha(OUT/n) for n in ["model.py", "run.py", "test_model.py"]})
    save("gate.json", gate)
    return gate


def verify():
    manifest = read(OUT/"artifact_manifest.json")
    for name, digest in manifest["files"].items():
        if sha(OUT/name) != digest: raise ValueError("Revision changed: "+name)
    start = read(OUT/"startup_manifest.json")
    for name, digest in start["protected"].items():
        if sha(REPO/name) != digest: raise ValueError("Historical file changed: "+name)
    for name, digest in read(OUT/"receipt_investigation.json")["candidate_files"].items():
        if sha(ROOT/name) != digest: raise ValueError("Receipt evidence changed: "+name)
    gate = read(OUT/"gate.json")
    if gate["source_jobs"] != 0 or gate["operational_candidate_evaluations"] != 0:
        raise ValueError("Focused Phase A scope exceeded")
    return dict(status="CURRENTLY_VERIFIED_PASS", artifacts=len(manifest["files"]),
        protected_historical_files=len(start["protected"]), evaluator_rerun=False,
        phase_A_model_conventions_ready=gate["phase_A_model_conventions_ready"], phase_B_ready=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phase", choices=list("ABCDEF"))
    group.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(), indent=2)); return 0
    if args.phase != "A":
        print(json.dumps(dict(status="BLOCKED_PHASE_DEPENDENCY", phase=args.phase,
            message="This revision implements focused Phase A only; consult gate.json for pilot dependencies.")))
        return 2
    print(json.dumps(phase_a(), indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
