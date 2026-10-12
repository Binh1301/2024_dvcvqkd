"""Staged, resumable exact ALT_OPT validation with a bounded source pilot.

Uses an overlay cache; original source/curve/audit artifacts are immutable.
Defaults: 90 seconds/probe, 270 seconds total, three prioritized pilot probes.
"""
from __future__ import annotations
import argparse
import cProfile
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import pstats
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source
from scripts.exact_cache_provenance import SOURCE_FILES, json_hash, objective_identity, source_hashes, source_settings, verify_source_payload

OUTPUT = ROOT / "results/theta10_D55_alt_opt_convergence_validation"
AUDIT = ROOT / "results/alt_opt_vs_numerical_audit_20261008_verified/alt_opt_independence_test.json"
REPRESENTATIVE = (20.0, 21.9393102292, 25.0, 30.0, 40.0)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_json(path, value):
    tmp = Path(path).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r)) or ["status"]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def locate(module, token):
    return str(Path(module.__file__).relative_to(ROOT)).replace("\\", "/") + ":" + str(next(i for i, line in enumerate(Path(module.__file__).read_text(encoding="utf-8").splitlines(), 1) if token in line))


def raw_snapshot(paths):
    return {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sorted(set(paths)) if p.is_file()}


def profile_worker(profile_path):
    # Sampling cProfile snapshots preserves partial profiles on process timeout.
    # The original worker.main is invoked without changing any numeric code.
    from scripts import full_support_c4_worker as worker
    profiler = cProfile.Profile()
    stop = threading.Event()
    def checkpoint():
        while not stop.wait(10):
            profiler.dump_stats(profile_path)
    thread = threading.Thread(target=checkpoint, daemon=True)
    thread.start()
    try:
        profiler.runcall(worker.main)
    finally:
        stop.set()
        profiler.dump_stats(profile_path)


def probe_worker(args):
    import torch
    from scripts.run_exact_mb_test2 import ExactMBEvaluator
    from src.cvqkd import gram_moments
    torch.set_num_threads(1)
    out = args.output_dir.resolve()
    config = source.unconstrained_config()
    overlay = out / "exact_source_cache"
    overlay.mkdir(exist_ok=True)
    evaluator = ExactMBEvaluator(config, {"T_eff": 0.0, "epsilon_base": .0186, "c_phi": 0.0}, out,
                                 source_cache_dir=overlay, allow_legacy_exact_import=False)
    nu, va = args.nu, args.va
    ensemble = source.make_ensemble(config, "MB", nu, va)
    identity = evaluator._source_identity(ensemble, nu, va)
    key = json_hash(identity)
    result_path = out / "probe_results" / (key + ".json")
    profile_path = out / "probe_results" / (key + ".prof")
    from src.modulation.qam256 import c4_orbit_indices
    inds = c4_orbit_indices()
    _, gate = gram_moments._fast(ensemble.probabilities[0, inds[:, 0]], ensemble.amplitudes[0, inds[:, 0]])
    original_run = subprocess.run
    def bounded_run(command, *a, **kw):
        if len(command) >= 2 and Path(command[1]).name == "full_support_c4_worker.py":
            command = [sys.executable, str(Path(__file__)), "--profile-worker", str(profile_path)]
            kw["timeout"] = max(1.0, args.per_probe_timeout - 8.0)
        return original_run(command, *a, **kw)
    # Only subprocess timeout/instrumentation changes; the C4 worker and
    # precision ladder execute their original functions and parameters.
    started = time.monotonic()
    gram_moments.subprocess.run = bounded_run
    try:
        moment = evaluator.source_moments(ensemble, nu, va)
        verification = verify_source_payload(moment, source_settings(config))
        status = "COMPLETED_EXACT"
        result = {"C": moment["C"], "w": moment["w"], "source_path": str((overlay / (key + ".json")).relative_to(ROOT)),
                  "provenance": verification}
    except Exception as error:
        status = "TIMEOUT" if "timeout" in str(error).lower() else "NUMERICAL_FAILURE"
        result = {"error": f"{type(error).__name__}: {error}"}
    finally:
        gram_moments.subprocess.run = original_run
    record = {"nu_raw": nu, "V_A": va, "cache_key": key, "status": status, "elapsed_seconds": time.monotonic() - started,
              "fast_path_gate": gate, "precision_ladder": list(gram_moments.PRECISION_LADDER),
              "profile_path": str(profile_path.relative_to(ROOT)), **result}
    save_json(result_path, record)
    print(json.dumps({k: record[k] for k in ("nu_raw", "V_A", "status", "elapsed_seconds")}), flush=True)
    return 0


def priorities(config, evaluator, old_iterations, old_summary):
    from scripts.run_exact_mb_test2 import ensemble_hash
    selected = {float(r["L_km"]): r for r in old_summary}
    points = {}
    for it in old_iterations:
        l = float(it["distance_km"])
        best = selected[l]
        for prefix, variable in (("V_A", "V_A"), ("nu", "nu_raw")):
            for e in json.loads(it[prefix + "_candidate_history"]):
                if e["status"] != "EXACT_SOURCE_MISSING":
                    continue
                nu = float(it["nu_before"]) if variable == "V_A" else float(e["value"])
                va = float(e["value"]) if variable == "V_A" else float(it["optimized_V_A"])
                pair = (nu.hex(), va.hex())
                if pair not in points:
                    ensemble = source.make_ensemble(config, "MB", nu, va)
                    identity = evaluator._source_identity(ensemble, nu, va)
                    canonical = {**identity, "source_implementation": {n: source_hashes((ROOT / n).read_bytes())["canonical_lf_sha256"] for n in SOURCE_FILES}}
                    points[pair] = {"nu_raw": nu, "V_A": va, "raw_current_cache_key": json_hash(identity),
                                    "canonical_source_cache_key": json_hash(canonical), "ensemble_hash": ensemble_hash(ensemble),
                                    "requests": 0, "distances": set(), "ridge_requests": 0, "boundary_requests": 0,
                                    "competitive_requests": 0, "final_ridge_requests": 0, "representative_requests": 0}
                p = points[pair]
                p["requests"] += 1
                p["distances"].add(l)
                ridge = (nu == float(best["nu_raw_star"])) if variable == "V_A" else (va == float(best["V_A_star"]))
                competitive = float(it["K_after_nu"]) >= float(best["K"]) - max(.002, .05 * abs(float(best["K"])))
                p["ridge_requests"] += int(ridge)
                p["boundary_requests"] += int(it[prefix + "_boundary_status"] == "BOUNDARY_NOT_CLOSED")
                p["competitive_requests"] += int(competitive)
                p["final_ridge_requests"] += int(ridge and it["start_id"] == best["selected_initialization"] and int(it["iteration"]) == int(best["AO_iterations"]) - 1)
                p["representative_requests"] += int(ridge and l in REPRESENTATIVE)
    ordered = sorted(points.values(), key=lambda p: (-p["final_ridge_requests"], -p["representative_requests"], -p["ridge_requests"], -p["competitive_requests"], p["nu_raw"], p["V_A"]))
    for rank, p in enumerate(ordered, 1):
        p["priority_rank"] = rank
        p["distances_km"] = json.dumps(sorted(p.pop("distances")))
        p["reason"] = "SELECTED_RIDGE_COORDINATE_CLOSURE" if p["final_ridge_requests"] else "COMPETITIVE_COORDINATE_OR_BOUNDARY" if p["competitive_requests"] else "DEFER_NONCOMPETITIVE_BRANCH"
    return ordered


def attest_old_objectives(config, channel, audit, old_report):
    identity = objective_identity(config, channel)
    for name in identity["identity"]["scientific_implementation"]:
        expected = audit["protected_sha256_after"].get(name)
        if expected is None or digest(ROOT / name) != expected:
            raise ValueError(f"Historical objective implementation attestation unavailable: {name}")
    for name in ("configs/default.yaml", "results/theta10_D55_alt_opt_distance_sweep/ao_objective_evaluations.csv"):
        if digest(ROOT / name) != audit["protected_sha256_after"].get(name):
            raise ValueError(f"Historical objective artifact/configuration changed: {name}")
    expected_config = {"w0_m": source.W0_M, "theta_div_full_rad": source.THETA_DIV_FULL_RAD, "D_r_m": .55,
                       "epsilon_ch": .0186, "beta": .95, "AO_physical": "OFF", "phase_noise": "OFF", "holevo": "direct_Z_minus"}
    if any(old_report["configuration"].get(k) != v for k, v in expected_config.items()):
        raise ValueError("Historical objective scientific settings mismatch")
    return {**identity, "historical_attestation": "HASH_BOUND_PREVIOUS_INDEPENDENT_AUDIT",
            "historical_audit_sha256": digest(AUDIT)}


def criteria_report(out, old_iterations):
    known = [r for r in old_iterations if float(r["distance_km"]) == 21.9393102292 and r["start_id"] == "nu_0.1"]
    lines = ["# Actual AO stopping criteria and correction", "", f"SKR epsilon_opt={ao.K_TOLERANCE!r} bits/use, defined at {locate(ao, 'K_TOLERANCE =')}; runtime source: imported module constant (no CLI epsilon override).",
        f"Parameter / inner-bracket tolerance={ao.PARAMETER_TOLERANCE!r}; outer max={ao.MAX_AO_ITERATIONS}; {locate(ao, 'MAX_AO_ITERATIONS =')}. --max-ao-iterations overrides the six-iteration default in original drivers; this validation uses six.",
        f"Endpoint expansion cap={ao.MAX_BOUNDARY_EXPANSIONS}; refinement-stage cap={ao.MAX_REFINEMENT_STAGES}. There is no independent fixed maximum objective-call count for a slice: initial exact slice size plus up to three endpoint probes and eight midpoint attempts (some successful calls reused locally).",
        "Previous criterion: abs(delta K)<=1e-8 OR both parameter displacements<=1e-6, conditional on reported bracket statuses. A bracketed catalog could be treated as complete even with untested regions; initial missing probes were not universally considered. Earlier unresolved searches were not checked on every convergence branch.",
        "Corrected policy retains epsilon=1e-8. Both coordinate searches must reach NUMERICALLY_CLOSED_LOCAL_BRACKET (two-sided bracket radius<=1e-6, no missing probes or numerical failures), no unresolved earlier search may invalidate stopping, and -1e-8<=delta K<=1e-8 is allowed only with no stage decrease exceeding numeric tolerance. The parameter-displacement alternative no longer certifies convergence.",
        "This is a local numerical bracket condition, not a certificate for an unbounded global maximum. Missing probes have no K value. Zero improvement with incomplete coverage is STAGNATED_IN_EXACT_CATALOG; open endpoint is UNRESOLVED_BOUNDARY; no valid inner candidate is INNER_SEARCH_FAILURE; actual evaluator failures/decreases are NUMERICAL_FAILURE; exhausting six outer iterations is MAX_ITERATIONS_REACHED. No parameter, peak or modulation upper bound was added.",
        "", "## Known baseline trajectory from immutable execution records", "", "| iteration | VA after | nu after | K before | K after VA | K after nu | delta K | epsilon comparison | current interpretation |", "|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in known:
        lines.append(f"| {r['iteration']} | {r['optimized_V_A']} | {r['optimized_nu']} | {r['K_before']} | {r['K_after_VA']} | {r['K_after_nu']} | {r['delta_K']} | abs(delta)<=epsilon: {abs(float(r['delta_K']))<=ao.K_TOLERANCE} | {'STAGNATED_IN_EXACT_CATALOG' if abs(float(r['delta_K']))<=ao.K_TOLERANCE else 'CONTINUE'}; both inner searches missing exact probes |")
    lines += ["", "The final zero delta meets the scalar epsilon comparison but does not establish convergence. Detailed candidate comparisons were verified in the independent audit and are rechecked during representative replay.", ""]
    (out / "ao_stopping_criteria_audit.md").write_text("\n".join(lines), encoding="utf-8")


def validate_distances(out, distances, config, audit, old_report, old_summary, old_objectives, overlay):
    records, iterations, boundaries, all_runs, identity_records = [], [], [], [], []
    previous_by_l = {float(r["L_km"]): r for r in old_summary}
    for l in distances:
        channel = sweep.make_channel(config, l)
        objective = ao.ExactObjective(config, channel, out, allow_new_source=False, source_cache_dirs=(source.SOURCE_CACHE, overlay))
        sweep.register_exact_catalog(objective)
        # Overlay discoveries join the source bank without rectangular search.
        for p in objective.payloads.values():
            nu, va = float.fromhex(p["nu_mb_raw_hex"]), float.fromhex(p["V_A_hex"])
            if nu > 0:
                objective.register_catalog(nu, va)
        attestation = attest_old_objectives(config, channel, audit, old_report)
        restored = objective.restore_objective_rows([r for r in old_objectives if float(r["L_km"]) == l], attestation)
        identity_records.append({"L_km": l, **attestation, "restored_rows": restored})
        start_defs = [(f"nu_{nu:g}", nu, None) for nu in sweep.BASE_STARTS]
        grid = list(sweep.DISTANCES_KM)
        neighbor_l = grid[max(0, grid.index(l) - 1)]
        neighbor = previous_by_l[neighbor_l]
        start_defs.append(("neighbor_continuation", float(neighbor["nu_raw_star"]), float(neighbor["V_A_star"])))
        runs = [sweep.run_single_distance_ao(distance_km=l, start_id=sid, start_nu=nu, start_va=va, objective=objective,
                 max_iterations=ao.MAX_AO_ITERATIONS) for sid, nu, va in start_defs]
        valid = [r for r in runs if r["final"]]
        best = max(valid, key=lambda r: float(r["final"]["SKR"]))
        final = best["final"]
        for run in runs:
            all_runs.append({"L_km": l, "start_id": run["start_id"], "status": run["status"],
                             "final_nu": run["final"]["nu_raw"] if run["final"] else None,
                             "final_V_A": run["final"]["V_A"] if run["final"] else None,
                             "K": run["final"]["SKR"] if run["final"] else None, "iterations": run["iterations"]})
            for r in run["iterations"]:
                iterations.append(r)
                for prefix, variable in (("V_A", "V_A"), ("nu", "nu_raw")):
                    boundaries.append({"L_km": l, "start_id": run["start_id"], "iteration": r["iteration"], "variable": variable,
                        "search_status": r[prefix + "_search_status"], "boundary_status": r[prefix + "_boundary_status"],
                        "refinement_status": r[prefix + "_refinement_status"], "range": r[prefix + "_search_range"], "bracket": r[prefix + "_bracket"],
                        "numeric_local_completion": r[prefix + "_search_status"] == "NUMERICALLY_CLOSED_LOCAL_BRACKET", "global_continuous_certificate": False})
        unresolved = sum(not r["numeric_local_completion"] for r in boundaries if r["L_km"] == l)
        open_boundary = sum(r["boundary_status"] == "BOUNDARY_NOT_CLOSED" for r in boundaries if r["L_km"] == l)
        last = best["iterations"][-1] if best["iterations"] else {}
        # Verify both coordinates at the FINAL pair too: the VA step inside
        # the iteration may have used the pre-update nu.
        final_va = ao.adaptive_maximize_1d(variable="V_A", fixed=float(final["nu_raw"]), values=objective.catalog_values("V_A", float(final["nu_raw"])), objective=objective)
        final_nu = ao.adaptive_maximize_1d(variable="nu_raw", fixed=float(final["V_A"]), values=objective.catalog_values("nu_raw", float(final["V_A"])), objective=objective)
        final_checks = (final_va, final_nu)
        for search in final_checks:
            boundaries.append({"L_km": l, "start_id": "final_pair_verification", "iteration": "postcheck", "variable": search["variable"],
                "search_status": search["status"], "boundary_status": search.get("boundary_status"), "refinement_status": search.get("refinement_status"),
                "range": json.dumps(search.get("range")), "bracket": json.dumps(search.get("bracket")),
                "numeric_local_completion": ao.coordinate_search_complete(search), "global_continuous_certificate": False})
        completed = all(ao.coordinate_search_complete(s) for s in final_checks)
        records.append({"L_km": l, "nu_raw_star": final["nu_raw"], "V_A_star": final["V_A"], "I_AB": final["I_AB"],
            "beta_I_AB": final["beta_I_AB"], "chi_BE": final["chi_BE"], "K": final["SKR"], "execution": "REVALIDATED_REPRESENTATIVE",
            "status": best["status"], "epsilon_opt": ao.K_TOLERANCE, "max_outer_iterations": ao.MAX_AO_ITERATIONS,
            "outer_iterations": len(best["iterations"]), "final_delta_K": last.get("delta_K"), "objective_rows_restored": restored,
            "new_exact_objective_evaluations": objective.unique_exact_evaluations, "objective_cache_hits": objective.cache_hits,
            "missing_source_attempts": len(objective.source_missing), "unresolved_coordinate_invocations": unresolved,
            "unresolved_boundary_invocations": open_boundary, "local_coordinate_search_complete": completed,
            "final_V_A_search_status": final_va["status"], "final_nu_search_status": final_nu["status"],
            "global_optimum_resolved": False, "selected_start": best["start_id"]})
        print("Representative validation", l, best["status"], "best", final["nu_raw"], final["V_A"], final["SKR"], flush=True)
        write_csv(out / "ao_iteration_history.csv", iterations)
        write_csv(out / "ao_boundary_closure.csv", boundaries)
        write_csv(out / "ao_convergence_summary.csv", records)
        save_json(out / "objective_compatibility_manifest.json", identity_records)
    return records, iterations, boundaries, all_runs


def main(args):
    import torch
    torch.set_num_threads(1)
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "validation_report.json").exists() and not args.resume:
        raise SystemExit("Validation exists: specify --resume; historical experiments will not be overwritten.")
    overlay = out / "exact_source_cache"
    overlay.mkdir(exist_ok=True)
    (out / "probe_results").mkdir(exist_ok=True)
    protected = list(source.OUTPUT.rglob("*")) + list(sweep.OUTPUT.rglob("*")) + list(AUDIT.parent.rglob("*")) + list(ao.OUTPUT.rglob("*"))
    protected += list(source.SOURCE_CACHE.glob("*.json")) + [ROOT / n for n in SOURCE_FILES]
    protected += [ROOT / "docs/FINAL_MODEL_SPEC.md", ROOT / "scripts/run_skr_vs_link_distance_theta10urad.py", ROOT / "scripts/run_exact_mb_test2.py"]
    checkpoint_path = out / "protected_input_manifest.json"
    current = raw_snapshot(protected)
    if checkpoint_path.exists():
        protected_before = json.loads(checkpoint_path.read_text())
        if current != protected_before:
            raise ValueError("Protected historical/model input changed since checkpoint")
    else:
        protected_before = current
        save_json(checkpoint_path, protected_before)
    config = source.unconstrained_config()
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    old_report = json.loads((sweep.OUTPUT / "run_report.json").read_text(encoding="utf-8"))
    old_summary = read_csv(sweep.OUTPUT / "mb_alt_opt_distance_summary.csv")
    old_iterations = read_csv(sweep.OUTPUT / "ao_iterations.csv")
    old_objectives = read_csv(sweep.OUTPUT / "ao_objective_evaluations.csv")
    cache = source.load_source_payloads(config, (source.SOURCE_CACHE, overlay))
    source_records = [{"source_path": p["_path"], "ensemble_hash": p["ensemble_hash"], **p["_provenance"]} for p in cache.values()]
    # Stage 1 requires both source and objective compatibility to pass BEFORE
    # enabling source generation. Historical objective reuse has an explicit
    # proof from the hash-bound independent audit, not an inferred identity.
    attestations = [attest_old_objectives(config, sweep.make_channel(config, l), audit, old_report) for l in REPRESENTATIVE]
    provenance = {"status": "PROVENANCE_VERIFICATION_PASS", "policy": "LF_ONLY_WITH_PROVEN_HISTORICAL_RAW_ALIAS_V1",
        "original_source_files_untouched": True, "verified_source_count": len(source_records), "sources": source_records,
        "settings": source_settings(config), "settings_sha256": json_hash(source_settings(config)),
        "source_and_objective_identities_separate": True, "objective_attestations": attestations,
        "missing_unknown_or_incompatible_identity": "FAIL_CLOSED", "historical_hashes_preserved": True}
    save_json(out / "provenance_audit.json", provenance)
    (out / "provenance_audit.md").write_text("# Provenance verification\n\nPROVENANCE_VERIFICATION_PASS\n\n"
        "Only CRLF/CR/LF line endings are canonicalized to LF. Every historical raw hash must match current bytes or a reproduced LF/CRLF encoding. Original payloads are untouched; canonical keys/implementation/settings hashes are separate sidecar fields in provenance_audit.json. Unknown implementation hashes, missing identity fields, altered settings or corrupt cache keys fail closed. Candidate loading now requires verified settings and exact nu/VA metadata. Objective reuse requires a separate scientific code/config/channel identity; old rows are adopted only through the hash-bound independent audit.\n", encoding="utf-8")
    criteria_report(out, old_iterations)
    pilot_evaluator = ao.ExactObjective(config, sweep.make_channel(config, REPRESENTATIVE[1]), out, allow_new_source=False, source_cache_dirs=(source.SOURCE_CACHE, overlay)).evaluator
    ranked = priorities(config, pilot_evaluator, old_iterations, old_summary)
    write_csv(out / "missing_source_priorities.csv", ranked)
    print("PROVENANCE_VERIFICATION_PASS", len(cache), "sources; unique missing keys", len(ranked), "requests", sum(p["requests"] for p in ranked), flush=True)
    ledgers = [json.loads(p.read_text()) for p in sorted((out / "probe_results").glob("*.json"))]
    completed = {r["cache_key"] for r in ledgers if r["status"] == "COMPLETED_EXACT"}
    tried = {r["cache_key"] for r in ledgers if r["status"] in {"COMPLETED_EXACT", "TIMEOUT", "NUMERICAL_FAILURE"}}
    used_seconds = sum(float(r.get("controller_elapsed_seconds", r.get("elapsed_seconds", 0))) for r in ledgers)
    pilot = [p for p in ranked if p["final_ridge_requests"] and p["raw_current_cache_key"] not in completed and (args.retry_failures or p["raw_current_cache_key"] not in tried)]
    pilot = pilot[:args.pilot_probes]
    for p in pilot:
        remaining = args.total_compute_budget - used_seconds
        if remaining < 15:
            break
        timeout = min(args.per_probe_timeout, remaining)
        key = p["raw_current_cache_key"]
        result_path = out / "probe_results" / (key + ".json")
        save_json(result_path, {"nu_raw": p["nu_raw"], "V_A": p["V_A"], "cache_key": key, "status": "RUNNING", "elapsed_seconds": 0,
                               "timeout_seconds": timeout, "controller_started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        command = [sys.executable, "-X", "utf8", str(Path(__file__)), "--probe", "--output-dir", str(out), "--nu", str(p["nu_raw"]), "--va", str(p["V_A"]), "--per-probe-timeout", str(timeout)]
        log_path = out / "probe_results" / (key + ".log")
        print("Pilot source", p["nu_raw"], p["V_A"], "timeout", timeout, "reason", p["reason"], flush=True)
        started = time.monotonic()
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Kill only this explicitly spawned probe and its worker tree.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
                process.wait()
        elapsed = time.monotonic() - started
        used_seconds += elapsed
        record = json.loads(result_path.read_text())
        if record["status"] == "RUNNING":
            record.update({"status": "TIMEOUT" if elapsed >= timeout else "PROCESS_FAILURE", "error": log_path.read_text(encoding="utf-8")[-2000:]})
        record.update({"controller_elapsed_seconds": elapsed, "timeout_seconds": timeout, "total_budget_used_seconds": used_seconds})
        save_json(result_path, record)
        ledgers = [json.loads(q.read_text()) for q in sorted((out / "probe_results").glob("*.json"))]
        write_csv(out / "new_exact_source_evaluations.csv", [{k: v for k, v in r.items() if k not in {"provenance", "fast_path_gate"}} for r in ledgers])
        print("Pilot outcome", record["status"], "elapsed", round(elapsed, 2), flush=True)
    # Continue only ranked, justified work. A stalled pilot consumes no further
    # exploratory batch. Successful entries persist and can be resumed later.
    if not ledgers:
        write_csv(out / "new_exact_source_evaluations.csv", [])
    records, iters, boundaries, runs = validate_distances(out, REPRESENTATIVE, config, audit, old_report, old_summary, old_objectives, overlay)
    representative_gate = all(r["status"] == "CONVERGED_NUMERICALLY" and r["local_coordinate_search_complete"] for r in records)
    full_rerun = []
    if representative_gate:
        remainder = tuple(l for l in sweep.DISTANCES_KM if l not in REPRESENTATIVE)
        full_rerun, more_i, more_b, more_r = validate_distances(out, remainder, config, audit, old_report, old_summary, old_objectives, overlay)
        records += full_rerun
        iters += more_i
        boundaries += more_b
        runs += more_r
    known = {r["L_km"]: r for r in records}
    for r in old_summary:
        l = float(r["L_km"])
        if l not in known:
            records.append({"L_km": l, **{k: float(r[k]) for k in ("nu_raw_star", "V_A_star", "I_AB", "beta_I_AB", "chi_BE", "K")},
                "execution": "NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED", "status": "LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY",
                "epsilon_opt": ao.K_TOLERANCE, "max_outer_iterations": ao.MAX_AO_ITERATIONS, "local_coordinate_search_complete": False,
                "unresolved_coordinate_invocations": int(r["unresolved_inner_search_directions"]),
                "unresolved_boundary_invocations": int(r["unresolved_boundary_directions"]), "global_optimum_resolved": False})
    records.sort(key=lambda r: r["L_km"])
    comparisons = []
    for r in records:
        old = next(x for x in old_summary if float(x["L_km"]) == r["L_km"])
        comparisons.append({"L_km": r["L_km"], "previous_nu_raw": old["nu_raw_star"], "validated_or_last_known_nu_raw": r["nu_raw_star"],
            "previous_V_A": old["V_A_star"], "validated_or_last_known_V_A": r["V_A_star"], "previous_K": old["K"],
            "validated_or_last_known_K": r["K"], "delta_K": r["K"] - float(old["K"]), "execution": r["execution"], "status": r["status"]})
    write_csv(out / "ao_convergence_summary.csv", records)
    write_csv(out / "ao_iteration_history.csv", iters)
    write_csv(out / "ao_boundary_closure.csv", boundaries)
    write_csv(out / "previous_vs_validated_alt_opt.csv", comparisons)
    cache_after = source.load_source_payloads(config, (source.SOURCE_CACHE, overlay))
    provenance["new_overlay_verified_sources"] = [{"source_path": p["_path"], **p["_provenance"]} for p in cache_after.values() if p["_path"].startswith(str(out.relative_to(ROOT)).replace("\\", "/"))]
    save_json(out / "provenance_audit.json", provenance)
    profiles = []
    for p in (out / "probe_results").glob("*.prof"):
        stream = io.StringIO()
        try:
            stats = pstats.Stats(str(p), stream=stream).sort_stats("cumulative")
            stats.print_stats(20)
            profiles.append({"path": str(p.relative_to(ROOT)), "partial_profile": True, "top_cumulative": stream.getvalue()})
        except Exception as e:
            profiles.append({"path": str(p.relative_to(ROOT)), "error": str(e)})
    preserved = raw_snapshot(protected) == protected_before
    tests = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-p", "test_alt_opt_provenance_and_stopping.py", "-v"], cwd=ROOT, text=True, capture_output=True)
    (out / "regression_tests.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    diffcheck = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True)
    summary = {"status": "VALIDATION_COMPLETE_WITH_UNRESOLVED_EXACT_SOURCE_PROBES", "scope": "DIAGNOSTIC_ONLY",
        "provenance_status": provenance["status"], "epsilon_opt": ao.K_TOLERANCE, "parameter_tolerance": ao.PARAMETER_TOLERANCE,
        "max_outer_iterations": ao.MAX_AO_ITERATIONS, "max_boundary_expansions": ao.MAX_BOUNDARY_EXPANSIONS, "max_refinement_stages": ao.MAX_REFINEMENT_STAGES,
        "source_precision_ladder": source_settings(config)["precision_ladder"], "per_probe_timeout_seconds": args.per_probe_timeout,
        "total_compute_budget_seconds": args.total_compute_budget, "pilot_probes_configured": args.pilot_probes,
        "source_compute_elapsed_seconds": used_seconds, "unique_missing_source_cache_keys": len(ranked),
        "unique_missing_exact_ensemble_hashes": len({p["ensemble_hash"] for p in ranked}), "previous_missing_requests": sum(p["requests"] for p in ranked),
        "new_exact_source_moments_completed": sum(r["status"] == "COMPLETED_EXACT" for r in ledgers),
        "new_exact_source_failures": ledgers, "profiles": profiles, "representative_distances": list(REPRESENTATIVE),
        "representative_gate_passed": representative_gate, "full_remaining_distance_optimization_run": bool(full_rerun),
        "remaining_distances": [r["L_km"] for r in records if r["execution"].startswith("NOT_RUN")],
        "global_optimum_resolved": False, "numerical_convergence_established": representative_gate and bool(full_rerun),
        "max_abs_delta_K": max(abs(r["delta_K"]) for r in comparisons), "summaries": records, "runs": runs,
        "objective_cache_manifest": "objective_compatibility_manifest.json", "prior_artifacts_and_source_cache_preserved": preserved,
        "scientific_source_security_and_physical_files_unchanged": preserved, "python_regression_tests_pass": tests.returncode == 0,
        "git_diff_check_pass": diffcheck.returncode == 0, "producer_sha256": digest(__file__),
        "frozen_spec_sha256": digest(ROOT / "docs/FINAL_MODEL_SPEC.md"),
        "acceleration_review": "C,w source rows can be shared across distances; exact duplicate probes deduplicated. Cache holds C,w only, no reusable eigensystems. Changing nu/VA changes Gram operators: no cross-ensemble matrix reuse asserted. Original worker uses repeated solves for diagonal systems; a direct diagonal division acceleration would require independent validation and a new execution identity. No source mathematics or precision ladder was changed.",
        "limitations": ["Catalog stagnation is not numerical convergence.", "Historical fields for 21 nonrepresentative distances are LAST_KNOWN values, not fresh optima.", "Finite local brackets are not global certificates over positive unbounded variables."]}
    save_json(out / "validation_report.json", summary)
    report_lines = ["# ALT_OPT convergence validation", "", f"Status: {summary['status']}", "", f"Provenance: {summary['provenance_status']}; original cache and artifacts preserved: {preserved}.",
        f"epsilon_opt={ao.K_TOLERANCE!r}, parameter tolerance={ao.PARAMETER_TOLERANCE!r}, outer max={ao.MAX_AO_ITERATIONS}. See ao_stopping_criteria_audit.md for original/new conditions and code locations.",
        f"Missing requests={summary['previous_missing_requests']}; unique cache keys={len(ranked)}; unique exact ensemble hashes={summary['unique_missing_exact_ensemble_hashes']}.",
        f"New exact sources completed={summary['new_exact_source_moments_completed']}; pilot compute={used_seconds:.6f} seconds. Per-probe timeout={args.per_probe_timeout}; total budget={args.total_compute_budget}. All unavailable probes remain listed in missing_source_priorities.csv and source ledgers.",
        f"Representative gate passed={representative_gate}; remaining-distance optimization executed={bool(full_rerun)}. Nonrepresentative rows are explicit LAST_KNOWN data. No global optimum is asserted.",
        f"Max absolute K change on updated/last-known table={summary['max_abs_delta_K']!r}. Python tests PASS={tests.returncode==0}; git diff --check PASS={diffcheck.returncode==0}.", "", "## Parameters and exact SKR", "",
        "| L | nu_raw | VA | I_AB | beta I_AB | chi_BE | K | execution | status |", "|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    report_lines += [f"| {r['L_km']:.12g} | {r['nu_raw_star']!r} | {r['V_A_star']!r} | {r['I_AB']!r} | {r['beta_I_AB']!r} | {r['chi_BE']!r} | {r['K']!r} | {r['execution']} | {r['status']} |" for r in records]
    report_lines += ["", "## Exact-source pilot", ""]
    report_lines += [f"- nu={r['nu_raw']}, VA={r['V_A']}: {r['status']}, {r.get('controller_elapsed_seconds',r.get('elapsed_seconds'))} seconds; {r.get('error','')}" for r in ledgers]
    report_lines += ["", "## Acceleration and precision review", "", summary["acceleration_review"], "",
        "The fixed 1050/1250/1450 precision ladder is retained; it cannot be reduced from these runtime outcomes. Partial live profiles identify where the original worker spent pilot time. Timeouts do not receive SKR values and do not erase successful cache rows. Resume uses --resume, the same verified input manifest and persistent overlay. Timed-out probes are skipped unless --retry-failures is explicitly supplied with a larger budget.", "",
        "## Numerical verdict", "", "No distance is promoted to convergence solely from an unchanged iterate. A corrected terminal state may be STAGNATED_IN_EXACT_CATALOG or UNRESOLVED_BOUNDARY. All missing coordinate/outer probes and final-pair checks are explicit in the CSVs. Continuous global optimality and publication readiness remain unresolved.", ""]
    (out / "validation_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("status", "provenance_status", "unique_missing_source_cache_keys", "new_exact_source_moments_completed", "source_compute_elapsed_seconds", "representative_gate_passed", "prior_artifacts_and_source_cache_preserved", "python_regression_tests_pass")}), flush=True)
    return 0 if preserved and tests.returncode == 0 and diffcheck.returncode == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--profile-worker":
        profile_worker(sys.argv[2])
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--output-dir", type=Path, default=OUTPUT)
        parser.add_argument("--per-probe-timeout", type=float, default=90.0)
        parser.add_argument("--total-compute-budget", type=float, default=270.0)
        parser.add_argument("--pilot-probes", type=int, default=3)
        parser.add_argument("--resume", action="store_true")
        parser.add_argument("--retry-failures", action="store_true")
        parser.add_argument("--probe", action="store_true")
        parser.add_argument("--nu", type=float)
        parser.add_argument("--va", type=float)
        args = parser.parse_args()
        if args.per_probe_timeout < 15 or args.total_compute_budget < 0 or args.pilot_probes < 0:
            parser.error("Require timeout>=15 s, total budget>=0, pilot count>=0")
        raise SystemExit(probe_worker(args) if args.probe else main(args))
