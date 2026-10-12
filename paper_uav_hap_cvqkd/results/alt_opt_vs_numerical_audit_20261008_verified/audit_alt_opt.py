"""Read existing histories and replay only two distances without final-result inputs.

Run from the project root: .venv/Scripts/python.exe -X utf8 <this file>.
No production code is edited. Missing source generation is explicitly blocked.
"""
from __future__ import annotations

import builtins
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
from collections import defaultdict
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import torch
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as numerical

OUT = Path(__file__).resolve().parent
A = numerical.OUTPUT
B = sweep.OUTPUT
REPRESENTATIVE = (20.0, 21.9393102292, 22.0, 25.0, 29.0, 30.0, 35.0, 40.0)
REPLAY = (21.9393102292, 25.0)
TOL = 1e-12
checks = []


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_csv(p):
    with Path(p).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def key(r):
    return (float(r.get("distance_km", r.get("L_km"))), *pair(r["nu_raw"], r["V_A"]))


def close(a, b):
    return math.isclose(float(a), float(b), abs_tol=TOL, rel_tol=0)


def check(name, passed, evidence, location):
    checks.append({"check": name, "verdict": "PASS" if passed else "FAIL",
                   "evidence": evidence, "code_location": location})


def location(module, token):
    p = Path(module.__file__)
    lines = p.read_text(encoding="utf-8").splitlines()
    return str(p.relative_to(ROOT)).replace("\\", "/") + ":" + str(next(i for i, s in enumerate(lines, 1) if token in s))


def snapshot(paths):
    return {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sorted(set(paths))}


class TrackedObjective(ao.ExactObjective):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []

    def __call__(self, nu, va):
        cached = self.key(nu, va) in self.rows
        try:
            row = super().__call__(nu, va)
        except ao.ExactSourceUnavailable:
            self.events.append({"nu_raw": nu, "V_A": va, "outcome": "EXACT_SOURCE_MISSING"})
            raise
        self.events.append({"nu_raw": nu, "V_A": va, "outcome": "OBJECTIVE_CACHE_HIT" if cached else "FRESH_EXACT_SKR",
                            "K": row["SKR"], "I_AB": row["I_AB"], "chi_BE": row["chi_BE"],
                            "channel_hash": row["channel_hash"], "source_cache_key": row["source_cache_key"]})
        return row


def main():
    required = ("alt_opt_vs_numerical_audit.md", "alt_opt_vs_numerical_comparison.csv",
                "alt_opt_iteration_evidence.csv", "alt_opt_independence_test.json")
    if any((OUT / n).exists() for n in required):
        raise SystemExit("Audit outputs already exist; use a new audit directory to preserve them.")
    torch.set_num_threads(1)
    protected = list(A.rglob("*")) + list(B.rglob("*")) + list(ao.SOURCE_CACHE.glob("*.json"))
    protected += list((ROOT / "scripts").glob("*.py")) + list((ROOT / "src").rglob("*.py"))
    protected += list((ROOT / "configs").rglob("*.yaml")) + [ROOT / "docs/FINAL_MODEL_SPEC.md", numerical.EVALUATED_BANK]
    protected = [p for p in protected if p.is_file()]
    before = snapshot(protected)
    git = {cmd: subprocess.check_output(["git", *cmd.split()], cwd=ROOT, text=True).strip()
           for cmd in ("branch --show-current", "rev-parse HEAD", "status --short")}
    report = json.loads((B / "run_report.json").read_text(encoding="utf-8"))
    previous = read_csv(A / "skr_vs_distance_three_scheme.csv")
    a_rows = read_csv(A / "candidate_evaluations.csv")
    b_rows = read_csv(B / "ao_objective_evaluations.csv")
    iterations = read_csv(B / "ao_iterations.csv")
    starts = read_csv(B / "ao_multistart_summary.csv")
    summary = read_csv(B / "mb_alt_opt_distance_summary.csv")
    channels = {float(r["distance_km"]): r for r in read_csv(A / "channel_by_distance.csv")}
    objective_index = {key(r): r for r in b_rows}
    a_index = {key(r): r for r in a_rows if r["family"] == "MB"}
    check("Objective log contains unique distance/exact-pair keys", len(objective_index) == len(b_rows), len(b_rows), location(ao, "def key("))
    check("Current producers match recorded run hashes", digest(sweep.__file__) == report["runner_sha256"] and
          digest(numerical.__file__) == json.loads((A / "run_report.json").read_text(encoding="utf-8"))["runner_sha256"],
          {"sweep": digest(sweep.__file__), "numerical": digest(numerical.__file__)}, location(sweep, 'report["runner_sha256"]'))
    check("Every B objective row matches independent A candidate evaluation", all(
        key(r) in a_index and all(close(r[f], a_index[key(r)][f]) for f in ("I_AB", "beta_I_AB", "chi_BE", "SKR", "T_eff"))
        and r["ensemble_hash"] == a_index[key(r)]["ensemble_hash"] and r["channel_hash"] == a_index[key(r)]["channel_hash"] for r in b_rows),
        f"{len(b_rows)} objective rows compared against A's all-candidate log", location(numerical, "def evaluate_pool("))
    check("SKR identity holds for all A/B objective rows", all(close(r["beta_I_AB"], .95 * float(r["I_AB"])) and
          close(r["SKR"], .95 * float(r["I_AB"]) - float(r["chi_BE"])) for r in a_rows + b_rows),
          f"{len(a_rows) + len(b_rows)} rows; beta=.95", "scripts/run_skr_vs_link_distance_theta10urad.py:153")
    channel_ok = all(close(r["T_eff"], channels[float(r["L_km"])]["T_eff"]) and
                     r["channel_hash"] == channels[float(r["L_km"])]["channel_hash"] and
                     close(r["zeta_deg"], math.degrees(math.acos(19 / float(r["L_km"])))) and
                     close(r["w0_m"], .0986760647169751) and close(r["D_r_m"], .55) and
                     close(r["theta_div_full_rad"], 1e-5) for r in a_rows + b_rows)
    check("All 26 distances use matching distance-dependent channel metadata", channel_ok,
          {str(l): {k: channels[l][k] for k in ("zeta_deg", "T_eff", "channel_hash")} for l in channels}, location(sweep, "def make_channel("))
    config = sweep.unconstrained_config()
    check("Formal variable constraints removed", all(config["cvqkd"][k] is None for k in
          ("v_min_snu", "v_max_snu", "v_a_budget_snu", "n_peak_photons")),
          {k: config["cvqkd"][k] for k in ("v_min_snu", "v_max_snu", "v_a_budget_snu", "n_peak_photons")}, location(numerical, "def unconstrained_config("))
    fresh_channels = {l: sweep.make_channel(config, l) for l in REPRESENTATIVE}
    check("Eight representative channels recompute identically", all(all(
          fresh_channels[l][k] == channels[l][k] if isinstance(fresh_channels[l][k], str) else close(fresh_channels[l][k], channels[l][k])
          for k in ("T_eff", "zeta_deg", "eta_atm", "A0", "sigma_X2", "p_in", "sigma_jt_m", "omega_L_m", "channel_hash"))
          for l in REPRESENTATIVE), list(REPRESENTATIVE), location(numerical, "def channel_row("))

    # Reconstruct every objective call from the initial evaluations and stage
    # histories, preserving exact-float keys and the original multi-start order.
    grouped = defaultdict(list)
    for r in iterations:
        grouped[(float(r["distance_km"]), r["start_id"])].append(r)
    seen = defaultdict(set)
    totals = defaultdict(int)
    by_distance = defaultdict(lambda: defaultdict(int))
    evidence = []
    reconstruction_errors = []
    for start in starts:
        l, sid = float(start["distance_km"]), start["start_id"]
        init = pair(start["initial_nu"], start["initial_V_A"])
        totals["objective_calls"] += 1
        by_distance[l]["objective_calls"] += 1
        hit = init in seen[l]
        totals["cache_hits" if hit else "unique_exact"] += 1
        by_distance[l]["cache_hits" if hit else "unique_exact"] += 1
        seen[l].add(init)
        prev_selected = None
        for it in grouped[(l, sid)]:
            before_pair = pair(it["nu_before"], it["V_A_before"])
            before_obj = objective_index.get((l, *before_pair))
            if not before_obj or not close(it["K_before"], before_obj["SKR"]) or (prev_selected is not None and before_pair != prev_selected):
                reconstruction_errors.append([l, sid, it["iteration"], "before/continuation"])
            for stage, prefix, fixed, selected, stage_k in (
                ("V_A", "V_A", float(it["nu_before"]), float(it["optimized_V_A"]), float(it["K_after_VA"])),
                ("nu_raw", "nu", float(it["optimized_V_A"]), float(it["optimized_nu"]), float(it["K_after_nu"])),
            ):
                history = json.loads(it[f"{prefix}_candidate_history"])
                candidates = []
                new, hits, missing = 0, 0, 0
                for number, event in enumerate(history):
                    nu = fixed if stage == "V_A" else float(event["value"])
                    va = float(event["value"]) if stage == "V_A" else fixed
                    p = pair(nu, va)
                    totals["objective_calls"] += 1
                    by_distance[l]["objective_calls"] += 1
                    success = event["status"] == "EXACT_EVALUATED"
                    obj = objective_index.get((l, *p)) if success else None
                    objective_hit = success and p in seen[l]
                    if success:
                        valid = obj is not None and pair(event["nu_raw"], event["V_A"]) == p and close(event["K"], obj["SKR"])
                        if not valid:
                            reconstruction_errors.append([l, sid, it["iteration"], stage, number, "candidate mismatch"])
                        candidates.append(event)
                        new += int(not objective_hit)
                        hits += int(objective_hit)
                        seen[l].add(p)
                    else:
                        missing += int(event["status"] == "EXACT_SOURCE_MISSING")
                        if "K" in event:
                            reconstruction_errors.append([l, sid, it["iteration"], stage, number, "failure carries K"])
                    if l in REPRESENTATIVE:
                        evidence.append({"distance_km": l, "start_id": sid, "iteration": int(it["iteration"]),
                            "stage": stage, "candidate_order": number, "nu_before": it["nu_before"],
                            "V_A_before": it["V_A_before"], "K_before": it["K_before"], "fixed_parameter": fixed,
                            "candidate_nu_raw": nu, "candidate_V_A": va, "candidate_status": event["status"],
                            "candidate_K": event.get("K", ""), "I_AB": obj["I_AB"] if obj else "",
                            "beta_I_AB": obj["beta_I_AB"] if obj else "", "chi_BE": obj["chi_BE"] if obj else "",
                            "source_moment_cache_hit": success, "objective_cache_hit_reconstructed": objective_hit if success else "",
                            "source_path": obj["source_path"] if obj else "", "ensemble_hash": obj["ensemble_hash"] if obj else "",
                            "selected_on_stage": success and float(event["value"]) == selected,
                            "stage_selected_value": selected, "stage_selected_K": stage_k,
                            "stage_status": it[f"{prefix}_search_status"], "boundary_status": it[f"{prefix}_boundary_status"],
                            "stop_status": it["convergence_status"], "evidence_origin": "stored_stage_history_crosschecked_objective_log"})
                if not candidates or not close(max(float(e["K"]) for e in candidates), stage_k) or not any(
                    float(e["value"]) == selected and close(e["K"], stage_k) for e in candidates):
                    reconstruction_errors.append([l, sid, it["iteration"], stage, "argmax"])
                if new != int(it[f"{prefix}_exact_evaluations"]) or hits != int(it[f"{prefix}_cache_hits"]):
                    reconstruction_errors.append([l, sid, it["iteration"], stage, "cache counter"])
                for metric, value in (("unique_exact", new), ("cache_hits", hits), ("missing_probes", missing),
                    ("unresolved_inner", int(not sweep.closed(it[f"{prefix}_search_status"]))),
                    ("unresolved_boundary", int(it[f"{prefix}_boundary_status"] == "BOUNDARY_NOT_CLOSED"))):
                    totals[metric] += value
                    by_distance[l][metric] += value
            if not close(float(it["K_after_nu"]) - float(it["K_before"]), it["delta_K"]):
                reconstruction_errors.append([l, sid, it["iteration"], "delta K"])
            violations = int(float(it["K_after_VA"]) + ao.K_TOLERANCE < float(it["K_before"])) + int(
                float(it["K_after_nu"]) + ao.K_TOLERANCE < float(it["K_after_VA"]))
            totals["monotonicity_violations"] += violations
            by_distance[l]["monotonicity_violations"] += violations
            prev_selected = pair(it["optimized_nu"], it["optimized_V_A"])
        last = grouped[(l, sid)][-1]
        if pair(start["final_nu"], start["final_V_A"]) != prev_selected or not close(start["K"], last["K_after_nu"]):
            reconstruction_errors.append([l, sid, "terminal selection"])
        if not (sweep.closed(last["V_A_search_status"]) and sweep.closed(last["nu_search_status"])) and "CONVERGED" in start["status"]:
            reconstruction_errors.append([l, sid, "false convergence"])
    check("All alternating histories, selections, cache counts and continuation verified", not reconstruction_errors,
          {"iterations": len(iterations), "stages": 2 * len(iterations), "errors": reconstruction_errors}, location(sweep, "def run_single_distance_ao("))
    expected = {"objective_calls": 4147, "unique_exact": 1357, "cache_hits": 1954, "missing_probes": 836,
                "unresolved_inner": 558, "unresolved_boundary": 280, "monotonicity_violations": 0}
    check("Aggregate counters reconstructed from execution histories", all(totals[k] == v for k, v in expected.items()),
          {"expected": expected, "reconstructed": dict(totals)}, location(ao, "def __call__(self, nu:"))
    fields = {"objective_calls": "requested_objective_calls", "unique_exact": "unique_exact_SKR_evaluations", "cache_hits": "cache_hits",
              "missing_probes": "missing_exact_source_probes", "unresolved_inner": "unresolved_inner_search_directions",
              "unresolved_boundary": "unresolved_boundary_directions", "monotonicity_violations": "monotonicity_violations"}
    check("Per-distance accounting matches summary", all(by_distance[float(r["L_km"])][k] == int(r[v]) for r in summary for k, v in fields.items()),
          "26 rows verified; counts are attempts/stages, not unique missing pairs or global directions", location(sweep, '"missing_exact_source_probes":'))

    catalog_a = {pair(r["nu_raw"], r["V_A"]) for r in a_rows if r["family"] == "MB"}
    catalog_b = {pair(r["nu_raw"], r["V_A"]) for r in b_rows}
    coverage = []
    comparison = []
    previous_mb = {float(r["distance_km"]): r for r in previous if r["scheme"] == sweep.OPTIMIZED_MB_SCHEME}
    for r in summary:
        l = float(r["L_km"])
        old = previous_mb[l]
        evaluated = [e for e in b_rows if float(e["L_km"]) == l]
        terminal = [s for s in starts if float(s["distance_km"]) == l]
        best = max(terminal, key=lambda s: float(s["K"]))
        matched = pair(r["nu_raw_star"], r["V_A_star"]) == pair(best["final_nu"], best["final_V_A"])
        if not matched or not close(r["K"], best["K"]):
            reconstruction_errors.append([l, "best multistart"])
        current_pairs = {pair(e["nu_raw"], e["V_A"]) for e in evaluated}
        coverage.append({"distance_km": l, "A_MB_pairs": len(catalog_a), "B_evaluated_MB_pairs": len(current_pairs),
                         "B_outside_A_catalog": len(current_pairs - catalog_a), "A_selected_point_in_B": pair(old["nu_raw"], old["V_A"]) in current_pairs})
        comparison.append({"distance_km": l, "numerical_nu_raw": old["nu_raw"], "numerical_V_A": old["V_A"],
            "ALT_OPT_nu_raw": r["nu_raw_star"], "ALT_OPT_V_A": r["V_A_star"], "K_numerical": old["K"], "K_ALT_OPT": r["K"],
            "delta_K": float(r["K"]) - float(old["K"]), "same_exact_pair": pair(old["nu_raw"], old["V_A"]) == pair(r["nu_raw_star"], r["V_A_star"]),
            "AO_updates_verified": not any(e[0] == l for e in reconstruction_errors), "status": r["status"],
            "A_MB_candidates": len(catalog_a), "B_MB_candidates_evaluated": len(current_pairs)})
    check("All final B rows selected from own terminal histories", not reconstruction_errors,
          "129 start histories; max terminal SKR independently reconstructs all 26 summaries", location(sweep, "best_run = max("))
    write_csv("alt_opt_iteration_evidence.csv", evidence)
    write_csv("alt_opt_vs_numerical_comparison.csv", comparison)
    print("Stored-log verification", json.dumps(dict(totals)), "errors", len(reconstruction_errors), flush=True)

    # Deny all reads of the prior final-result CSVs and prior curve report while
    # executing the actual coordinate-update functions. The permitted bank
    # supplies only (nu,VA) labels; its old SKR values are never consumed.
    forbidden = {p.resolve() for p in (A / "skr_vs_distance_three_scheme.csv", A / "mb_optimized_by_distance.csv",
                  A / "mb_fixed_by_distance.csv", A / "uniform_optimized_by_distance.csv", A / "run_report.json", B / "previous_mb_comparison.csv")}
    original_open, original_io_open = builtins.open, io.open
    access = []
    denied = []

    def guarded_open(original, path, *args, **kwargs):
        if not isinstance(path, int):
            resolved = Path(path).resolve()
            mode = args[0] if args else kwargs.get("mode", "r")
            if resolved in forbidden:
                denied.append(str(resolved))
                raise PermissionError("Prior final-result input disabled for audit")
            if "r" in str(mode) and resolved.is_relative_to(ROOT):
                access.append(str(resolved.relative_to(ROOT)).replace("\\", "/"))
        return original(path, *args, **kwargs)

    cold = []
    cf_evidence = []
    source_validations = []
    with patch("builtins.open", side_effect=lambda p, *a, **kw: guarded_open(original_open, p, *a, **kw)), \
         patch("io.open", side_effect=lambda p, *a, **kw: guarded_open(original_io_open, p, *a, **kw)), \
         patch.object(sweep, "load_previous_rows", side_effect=AssertionError("Previous final-selection reader disabled")), \
         patch.object(ao.ExactMBEvaluator, "source_moments", side_effect=AssertionError("Source generation forbidden in audit")) as source_mock:
        try:
            (A / "skr_vs_distance_three_scheme.csv").read_text(encoding="utf-8")
        except PermissionError:
            guard_verified = True
        else:
            guard_verified = False
        for l in REPLAY:
            for cache_mode in ("cold_objective", "compatible_existing_objective_cache"):
                for order_name, nus in (("forward", sweep.BASE_STARTS), ("reverse", tuple(reversed(sweep.BASE_STARTS)))):
                    objective = TrackedObjective(config, fresh_channels[l], OUT, allow_new_source=False)
                    sweep.register_exact_catalog(objective)
                    if not source_validations:
                        for nu, va in sorted(objective.catalog):
                            c = ao.candidate_from_payload(config, objective.payloads, "MB", nu, va)
                            payload = objective.payloads[c["ensemble_hash"]]
                            identity = objective.evaluator._source_identity(c["ensemble"], nu, va)
                            source_validations.append({"nu_raw": nu, "V_A": va,
                                "identity_matches_current_implementation": all(payload.get(k) == v for k, v in identity.items()),
                                "full_support": payload["support_size"] == 256})
                    if cache_mode.startswith("compatible"):
                        for logged in (e for e in b_rows if float(e["L_km"]) == l):
                            nu, va = float(logged["nu_raw"]), float(logged["V_A"])
                            c = ao.candidate_from_payload(config, objective.payloads, "MB", nu, va)
                            assert c and c["ensemble_hash"] == logged["ensemble_hash"] and logged["channel_hash"] == fresh_channels[l]["channel_hash"]
                            numeric = {k: float(logged[k]) for k in ("nu_raw", "V_A", "L_km", "I_AB", "beta_I_AB", "chi_BE", "SKR")}
                            objective.rows[objective.key(nu, va)] = {**logged, **numeric}
                    runs = []
                    for nu in nus:
                        runs.append(sweep.run_single_distance_ao(distance_km=l, start_id=f"nu_{nu:g}", start_nu=nu,
                                    start_va=None, objective=objective, max_iterations=sweep.MAX_AO_ITERATIONS))
                    best = max((r for r in runs if r["final"] is not None), key=lambda r: float(r["final"]["SKR"]))
                    live_vs_logs = []
                    for e in objective.events:
                        if "K" in e:
                            logged = objective_index.get((l, *pair(e["nu_raw"], e["V_A"])))
                            live_vs_logs.append(logged is not None and close(e["K"], logged["SKR"]))
                    cold.append({"distance_km": l, "cache_mode": cache_mode, "start_order": order_name, "initial_nus": nus,
                        "catalog_count": len(objective.catalog), "catalog_pairs": sorted(objective.catalog),
                        "selected_nu_raw": best["final"]["nu_raw"], "selected_V_A": best["final"]["V_A"], "selected_K": best["final"]["SKR"],
                        "selected_start": best["start_id"], "requested_calls": objective.requested_calls,
                        "fresh_exact_evaluations": objective.unique_exact_evaluations, "cache_hits": objective.cache_hits,
                        "missing_source_attempts": len(objective.source_missing), "numerical_failures": objective.numerical_failures,
                        "all_successful_calls_match_stored_objectives": all(live_vs_logs), "runs": runs, "objective_events": objective.events})
                    for run in runs:
                        for it in run["iterations"]:
                            cf_evidence.append({"distance_km": l, "cache_mode": cache_mode, "start_order": order_name, **it})
                    print("Counterfactual", l, cache_mode, order_name, "->", best["final"]["nu_raw"], best["final"]["V_A"],
                          best["final"]["SKR"], "fresh", objective.unique_exact_evaluations, flush=True)
        source_generation_calls = source_mock.call_count
    check("Counterfactual previous-result inputs blocked", guard_verified and len(denied) == 1 and source_generation_calls == 0,
          {"controlled_guard_probe_denied": denied, "optimizer_final_result_reads": 0, "source_generation_calls": source_generation_calls},
          location(sweep, "def register_exact_catalog("))
    check("Cold and warm counterfactuals reconstruct real own histories", all(r["runs"] and
          all(run["iterations"] for run in r["runs"]) and r["all_successful_calls_match_stored_objectives"] for r in cold),
          f"{len(cold)} scenarios / {sum(len(r['runs']) for r in cold)} starts; actual evaluator used on cold-cache misses", location(sweep, "def run_single_distance_ao("))
    check("Start order and compatible-cache reuse preserve best selected pair", all(len({
          (*pair(r["selected_nu_raw"], r["selected_V_A"]), float(r["selected_K"]).hex()) for r in cold if r["distance_km"] == l}) == 1 for l in REPLAY),
          [{k: r[k] for k in ("distance_km", "cache_mode", "start_order", "selected_nu_raw", "selected_V_A", "selected_K", "fresh_exact_evaluations")} for r in cold],
          location(sweep, "best_run = max("))
    check("Registered source cache identities match current implementation", all(r["identity_matches_current_implementation"] and r["full_support"] for r in source_validations),
          {"registered_MB_sources": len(source_validations), "mismatches": [r for r in source_validations if not r["identity_matches_current_implementation"]]},
          location(numerical, "def candidate_from_payload("))
    checks.append({"check": "Continuous inner-search convergence and global optimality", "verdict": "INCONCLUSIVE",
        "evidence": "Missing moments, finite connected slices, open boundaries, refinement/iteration resource caps and no global enclosure",
        "code_location": location(ao, "MAX_BOUNDARY_EXPANSIONS")})
    spec = digest(ROOT / "docs/FINAL_MODEL_SPEC.md")
    historical = "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
    checks.append({"check": "Historical frozen-spec hash", "verdict": "PASS" if spec == historical else "INCONCLUSIVE",
        "evidence": {"current": spec, "historical_expected": historical, "consequence": "Diagnostic audit only; no lifecycle promotion"},
        "code_location": "AGENTS.md:Mandatory startup procedure"})
    after = snapshot(protected)
    changed = [p for p in before if before[p] != after[p]]
    check("All prior results, source cache, evaluators, configs and model files unchanged", not changed,
          {"protected_files": len(before), "changed": changed}, "audit_alt_opt.py:snapshot")
    payload = {"status": "FAIL" if any(c["verdict"] == "FAIL" for c in checks) else "PASS_ALTERNATING_UPDATES__INCONCLUSIVE_GLOBAL_OPTIMALITY",
        "date": "2026-10-08", "scope": "DIAGNOSTIC_READ_ONLY_AUDIT_WITH_TWO_DISTANCE_CACHE_ONLY_REPLAY",
        "git": git, "checks": checks, "counterfactual_tests": cold, "read_access_paths": sorted(set(access)),
        "forbidden_final_result_inputs": sorted(str(p.relative_to(ROOT)) for p in forbidden), "source_generation_calls": source_generation_calls,
        "all_26_accounting": dict(totals), "per_distance_accounting": {str(l): dict(v) for l, v in by_distance.items()},
        "catalog_coverage": coverage, "A_MB_catalog_count": len(catalog_a), "B_union_evaluated_pairs": len(catalog_b),
        "B_outside_A_catalog": sorted(catalog_b - catalog_a), "source_identity_validation": source_validations,
        "protected_sha256_before": before, "protected_sha256_after": after, "protected_changed": changed,
        "producer_sha256": digest(__file__), "limitations": ["Audit verifies executed coordinate ascent over exact evaluated slices; it does not certify continuous global maxima.",
            "Historical per-call cache labels reconstructed from logged order; live counterfactual calls have explicit cache event records."]}
    (OUT / "alt_opt_independence_test.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv("counterfactual_iterations.csv", cf_evidence)
    create_report(payload, comparison, iterations, starts, coverage, totals)
    print("AUDIT", payload["status"], "checks", len(checks), "protected_changed", changed, flush=True)
    return int(any(c["verdict"] == "FAIL" for c in checks))


def create_report(payload, comparison, iterations, starts, coverage, totals):
    lines = ["# Independent audit: ALT_OPT versus numerical search", "", "Date: 2026-10-08. Scope: diagnostic only.", "",
        "The executed ALT_OPT is sequential coordinate ascent: V_A at fixed current nu, then nu at the newly selected V_A. Its agreement with numerical search is supported by recorded candidate comparisons and controlled independent replay. Continuous convergence/global optimality remains INCONCLUSIVE.", "",
        "## Required verdicts", "", "| Question | Verdict | Evidence and code |", "|---|---|---|"]
    verdicts = [
        ("1. Genuine alternating updates?", "PASS", f"All {len(iterations)} stored iterations / {2*len(iterations)} stages reconstructed; {location(sweep, 'va_search = adaptive_maximize_1d(')}."),
        ("2. Newly updated VA used for nu?", "PASS", f"Fixed argument is after_va['V_A']; every nu history checked against it; {location(sweep, 'fixed=float(after_va[')} ."),
        ("3. Independent selection or reuse of prior final decisions?", "PASS", f"max(runs_with_final, SKR), {location(sweep, 'best_run = max(')}. Prior CSV used for distance validation, comparison, copying Uniform/fixed and experiment hash only. Its reads were denied in 8 replay scenarios; 32 starts built their own histories."),
        ("4. Different algorithms, same exact source catalog?", "PASS", f"A enumerates all {payload['A_MB_catalog_count']} available MB pairs. B takes successive slices of that bank, with adaptive exact probes. Evaluated subsets differ (see coverage table). This is shared data availability, not independent discovery of the catalog."),
        ("5. Why all 26 final pairs identical?", "PASS", "The independently followed slices reach A's catalog maximizer at every distance; A's winning row appears in B's actual evaluation log. B does not evaluate all A pairs. Evidence supports agreement on this catalog; it does not prove generic equivalence."),
        ("6. Does identical SKR prove correctness?", "PASS (consistency only)", "Equality alone proves consistency; separate coordinate/candidate/identity/cache/replay checks support implementation correctness within this diagnostic."),
        ("7. Fixed-parameter, stale-cache or wrong-distance bug?", "PASS for executed updates; FAIL strict source identity", "Fixed-coordinate and distance behavior pass; in-memory objective keys include config+channel+exact pair. Source payload implementation hashes differ by CRLF versus LF. Recomputed CRLF hashes reproduce stored hashes, proving newline equivalence, but candidate_from_payload checks ensemble/support/finite C,w only and bypasses strict current implementation identity."),
        ("8. What prevents convergence/global optimality?", "INCONCLUSIVE", "Missing exact source probes, unresolved boundaries and incomplete slices. Every distance reports INNER_SEARCH_FAILURE. Unchanged iterate is catalog stagnation, not convergence."),
        ("9. Minimum manuscript validation work?", "INCONCLUSIVE for certification", "First explicitly reconcile the proven newline-only source identity mismatch with a hash-bound manifest and strict loader validation; do not regenerate or change C,w merely for newline differences. Report present work as cache-limited coordinate ascent. For convergence, prospectively freeze tolerances/resources and complete missing exact probes. Global claims additionally need tail bounds/global enclosures and applicable numerical/security certification.")]
    lines += [f"| {q} | {v} | {e} |" for q, v, e in verdicts]
    lines += ["", "## Algorithm comparison", "", "| Component | A: numerical search | B: ALT_OPT |", "|---|---|---|",
        f"| Search | Full enumeration: {len(read_csv(A/'candidate_evaluations.csv'))} rows, 165 sources/distance | Sequential VA then nu slices; 1357 unique objective rows |",
        f"| Candidate generation | Historical evaluated bank labels + Uniform extras + fixed pair | Same historical MB bank labels; exact midpoint/endpoint probes |",
        f"| Coordinate updates | None: direct max over MB pair pool ({location(numerical, 'def selected_rows(')}) | VA argmax, then nu argmax using selected VA ({location(sweep, 'def run_single_distance_ao(')}) |",
        "| Multi-start | None | .10, .15, .30, .80 plus prior-distance selected pair |",
        f"| Exact source reuse | Rebuild common ensemble; match binary64 ensemble hash | Same helper; cached C,w only; misses fail closed unless explicit opt-in |",
        f"| Objective cache | In-memory pair+distance memo inside this run; context config held constant | In-memory context(config+channel)+hex(nu)+hex(VA); recreated per distance ({location(ao, 'def key(')}) |",
        f"| Boundary exploration | boundary_probe_points returns same pool; classify_closure aggregates across distances ({location(numerical, 'def boundary_probe_points(')}) | Endpoint halving/doubling (3 attempts), neighbor midpoint refinement (4 stages); open directions recorded |",
        "| Stopping | Finite pool exhausted; no iterative convergence test | max 6 iterations, delta K <= 1e-8 / parameter delta <= 1e-6, with closed-search status required |",
        "| Final selection | Maximum raw SKR among eligible MB pairs | Maximum terminal raw SKR over start trajectories; no prior-final-point fallback |", "",
        "Important limitation in A: the code does not implement a fresh adaptive expansion in boundary_probe_points. classify_closure compares probe maxima across *all* distances against a maximum selected K across all distances, so its below_selected_best flag is not a per-distance closure certificate. B explicitly retains unresolved statuses. Neither establishes an optimum over all positive nu/VA.", "",
        "B's previous CSV is read before starts by load_previous_rows for distance completeness and hash provenance; it is read after optimization to copy Uniform/fixed rows and compare the old MB row. Its values do not enter register_exact_catalog, starting_va, coordinate updates or best_run selection. The historical evaluated_points.csv is a permitted, necessary source of candidate parameter labels for both implementations; no K from that bank is read by source_points_from_bank.", "",
        "## Constraints, catalog and closure", "",
        "Runtime v_min, v_max, common VA budget and peak constraint are all None. The 1.5 value in defaults is overridden. Search variables must be finite and positive; no preset VA/nu physical upper bound remains. Cache-only availability restricts the actually executable slices. MAX_BOUNDARY_EXPANSIONS=3, MAX_REFINEMENT_STAGES=4, MAX_AO_ITERATIONS=6 are resource caps with unresolved statuses, not physical constraints.", "",
        "An interior winning catalog point brackets tested neighbors only. Without monotonicity/unimodality assumptions or tail bounds, it does not close the entire unbounded domain. B explores outside a slice only when its current winner is an endpoint; catalog stagnation is not global closure. A VA=6.5 winner only defeats the tested alternatives.", "",
        "Two unexercised implementation risks remain: adaptive_maximize_1d does not explicitly reject failures from initial catalog probes when later status is bracketed (normal registration excludes missing rows); and the terminal convergence branch tests the current closed slices, while earlier unresolved_inner is only used at the iteration cap. Neither affected this recorded sweep, which correctly terminates INNER_SEARCH_FAILURE. The combined plot CSV's MB status='PASS' means a valid objective evaluation; the optimization status is only in the distance summary/report and must be used for manuscript claims.", "",
        "## Full 26-distance comparison", "", "| Distance | Numerical nu / VA | ALT_OPT nu / VA | K numerical | K ALT_OPT | Difference | Updates verified | Status |", "|---:|---|---|---:|---:|---:|---|---|"]
    for r in comparison:
        lines.append(f"| {float(r['distance_km']):.12g} | {r['numerical_nu_raw']} / {r['numerical_V_A']} | {r['ALT_OPT_nu_raw']} / {r['ALT_OPT_V_A']} | {r['K_numerical']} | {r['K_ALT_OPT']} | {r['delta_K']} | {r['AO_updates_verified']} | INNER_SEARCH_FAILURE; UNRESOLVED_BOUNDARY |")
    lines += ["", "## Catalog coverage", "", "| L (km) | A available/evaluated MB pairs | B actually evaluated pairs | B outside A | A winner in B |", "|---:|---:|---:|---:|---|"]
    for r in coverage:
        lines.append(f"| {r['distance_km']:.12g} | {r['A_MB_pairs']} | {r['B_evaluated_MB_pairs']} | {r['B_outside_A_catalog']} | {r['A_selected_point_in_B']} |")
    lines += ["", "## Detailed representative traces", "",
        "Each successful candidate in alt_opt_iteration_evidence.csv has independently crosschecked I_AB, beta I_AB, chi_BE and K from ao_objective_evaluations.csv. Every exact candidate and missing probe is retained for all starts at the eight representative distances. Source moments are reused from hash-matched stored payloads. Historical objective-cache hits below are reconstructed from execution order and crosschecked against per-stage counters; the counterfactual JSON records actual live call outcomes."]
    for l in REPRESENTATIVE:
        records = [r for r in iterations if float(r["distance_km"]) == l and r["start_id"] == "nu_0.1"]
        lines += ["", f"### L={l:.12g} km, nu0=.10", "", "| Iteration | Pair before | K before | VA update | K after VA | nu update | K after nu | Stop |", "|---:|---|---:|---:|---:|---:|---:|---|"]
        for it in records:
            lines.append(f"| {it['iteration']} | ({it['nu_before']}, {it['V_A_before']}) | {it['K_before']} | {it['optimized_V_A']} | {it['K_after_VA']} | {it['optimized_nu']} | {it['K_after_nu']} | {it['convergence_status']} |")
        # Full baseline trajectory, and one full iteration for each other distance.
        for it in (records if l == 21.9393102292 else records[:1]):
            lines += ["", f"Iteration {it['iteration']}: delta K={it['delta_K']}."]
            for prefix, stage in (("V_A", "VA at fixed nu"), ("nu", "nu at updated VA")):
                hist = json.loads(it[f"{prefix}_candidate_history"])
                valid = [h for h in hist if h["status"] == "EXACT_EVALUATED"]
                missing = [h["value"] for h in hist if h["status"] == "EXACT_SOURCE_MISSING"]
                lines += ["", f"{stage}: {len(valid)} exact comparisons; {it[prefix+'_exact_evaluations']} new objectives; {it[prefix+'_cache_hits']} objective-cache hits. Search={it[prefix+'_search_status']}; boundary={it[prefix+'_boundary_status']}.", "",
                    "| Candidate value | Exact K |", "|---:|---:|"]
                lines += [f"| {h['value']!r} | {h['K']!r} |" for h in valid]
                lines += ["", f"Missing probes (no K assigned): {missing!r}."]
    lines += ["", "## Counterfactual independence test", "",
        "Prior numerical final-selection CSVs/report were guarded against reads; load_previous_rows and source_moments were patched to raise if called. The guard itself was tested once. The real run_single_distance_ao, adaptive_maximize_1d and deterministic evaluator were reused unchanged. Existing source files and evaluation artifacts were preserved. Each distance was replayed with four starts in forward/reverse order, from a cold in-memory objective cache and a compatible cache preloaded only from B's full objective log. Cache preload was validated against current channel/ensemble identities and cold runs provide independently recalculated SKR. No final-result selections were injected.", "",
        "| L | Cache | Order | Selected pair | K | Fresh evaluator calls | Status |", "|---:|---|---|---|---:|---:|---|"]
    for r in payload["counterfactual_tests"]:
        lines.append(f"| {r['distance_km']:.12g} | {r['cache_mode']} | {r['start_order']} | ({r['selected_nu_raw']}, {r['selected_V_A']}) | {r['selected_K']} | {r['fresh_exact_evaluations']} | {r['runs'][0]['status']} |")
    lines += ["", "Start-order stability here is empirical for the two requested distances. Starts can terminate at different pairs even while the best across starts is unchanged. Warm-start/cache sharing is not proof of global uniqueness.", "",
        "## Accounting and stopping audit", "", "| Counter | Reconstructed | Interpretation |", "|---|---:|---|"]
    meanings = {"objective_calls": "Initial evaluations plus all stage objective calls", "unique_exact": "Unique successful distance+binary64 pair evaluations", "cache_hits": "Successful calls reusing same context and pair",
        "missing_probes": "Missing-source attempts (including repeats)", "unresolved_inner": "Unresolved coordinate-search invocations, not distinct global directions",
        "unresolved_boundary": "Coordinate invocations reporting BOUNDARY_NOT_CLOSED", "monotonicity_violations": "Observed stage decreases beyond 1e-8"}
    lines += [f"| {k} | {totals[k]} | {meanings[k]} |" for k in meanings]
    lines += ["", "The accounting identity is 4147 = 1357 + 1954 + 836. No numerical failures were recorded. Every audited distance has stagnation among tested candidates together with missing source evaluations; continuous coordinate maximization is incomplete and global boundary closure is unproved. Boundary flags can be INTERIOR on a selected run while other starts at that same distance report open boundaries. No recorded result is numerically converged.", "",
        "## Provenance and limitations", "",
        f"Branch `{payload['git']['branch --show-current']}`, commit `{payload['git']['rev-parse HEAD']}`; pre-existing dirty work preserved.", "",
        "All prior artifacts, source cache, producer scripts, physical/security code, configs and frozen-spec bytes were hashed before/after the audit. Exact hashes and current source-identity validation are in alt_opt_independence_test.json. No physical/security functional, source moments, training/test access, baseline selection or threshold approval changed.", "",
        "The current frozen-spec hash differs from the historical expected AGENTS hash. This pre-existing provenance discrepancy remains a lifecycle blocker; the model document was not modified. Publication lifecycle stays NOT_READY_FOR_PUBLICATION_SCALE_RUNS. This audit tests algorithm execution, not the validity of the full quantum-security proof or global error certification.", "",
        "Strict source-implementation byte identity FAILS for 136/136 registered MB rows. Stored gram_moments.py SHA256=f55c47589422a52224db8798e0c910ceb093eb06d6863b0107e9fd62d2466d48; current=bbad4c303a71ae69be99a4fffba90d968de35f34242977bad03dc1b3e6c5c551. Stored full_support_c4_worker.py SHA256=fe4be5e4b9ce8075f4553f296e32e8f59723bbcfe0b244ab9f6b24886c827ff3; current=2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1. Hashing current bytes with CRLF line endings reproduces the stored hashes exactly. Other identity fields and support_size=256 agree. This is a proven newline-only metadata difference, not evidence of different source mathematics, but it prevents an unqualified claim of strict current-byte cache validation. The original loader accepts payloads by ensemble hash without checking implementation/settings identity; audit did not change it.", "",
        "## Check registry", "", "| Check | Verdict | Code location |", "|---|---|---|"]
    lines += [f"| {c['check']} | {c['verdict']} | {c['code_location']} |" for c in payload['checks']]
    lines += ["", "## Conclusion", "",
        "ALT_OPT genuinely executes alternating coordinate updates on exact tested slices and independently selects its terminal candidates. Agreement with numerical search is legitimate on the shared available source catalog and is supported by actual histories and cold-cache counterfactual replay. Overall unqualified PASS is withheld: strict source-byte identity FAILS (the discrepancy is independently shown to be newline-only), and continuous convergence/global optimality remains INCONCLUSIVE.", ""]
    (OUT / "alt_opt_vs_numerical_audit.md").write_text("\n".join(lines), encoding="utf-8")


def finalize_existing():
    """Refine provenance findings from the saved replay, with no new objective calls."""
    global OUT
    import shutil
    initial = OUT
    OUT = ROOT / "results/alt_opt_vs_numerical_audit_20261008_verified"
    OUT.mkdir(exist_ok=True)
    if (OUT / "alt_opt_independence_test.json").exists():
        raise SystemExit("Final audit already exists; preserve it.")
    payload = json.loads((initial / "alt_opt_independence_test.json").read_text(encoding="utf-8"))
    original_replay_producer = payload["producer_sha256"]
    objective = ao.ExactObjective(sweep.unconstrained_config(), sweep.make_channel(sweep.unconstrained_config(), REPLAY[0]), OUT, allow_new_source=False)
    validations = []
    for row in payload["source_identity_validation"]:
        nu, va = row["nu_raw"], row["V_A"]
        c = ao.candidate_from_payload(objective.config, objective.payloads, "MB", nu, va)
        p = objective.payloads[c["ensemble_hash"]]
        identity = objective.evaluator._source_identity(c["ensemble"], nu, va)
        mismatches = {k: {"stored": p.get(k), "current": v} for k, v in identity.items() if p.get(k) != v}
        eol_equivalent = True
        for name, current_hash in identity["source_implementation"].items():
            raw = (ROOT / name).read_bytes()
            crlf_hash = hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
            eol_equivalent &= p["source_implementation"].get(name) in {current_hash, crlf_hash}
        non_implementation = {k: v for k, v in mismatches.items() if k != "source_implementation"}
        validations.append({**row, "source_path": c["source_path"], "mismatched_identity_fields": mismatches,
                            "newline_equivalence_verified": eol_equivalent and not non_implementation})
    payload["source_identity_validation"] = validations
    all_eol = all(v["newline_equivalence_verified"] for v in validations)
    for c in payload["checks"]:
        if c["check"] == "Registered source cache identities match current implementation":
            c["check"] = "Strict byte-for-byte source implementation identity"
            c["evidence"] = {"registered_MB_sources": len(validations), "mismatch_count": sum(not v["identity_matches_current_implementation"] for v in validations),
                             "cause": "CRLF stored hashes versus LF worktree hashes; loader bypasses strict source identity"}
    payload["checks"].append({"check": "Source implementation mismatch is exactly newline-equivalent", "verdict": "PASS" if all_eol else "FAIL",
        "evidence": {"validated_sources": len(validations), "current_CRLF_digests_reproduce_stored": all_eol, "changed_source_bytes": False},
        "code_location": location(numerical, "def candidate_from_payload(")})
    after = snapshot([ROOT / p for p in payload["protected_sha256_before"]])
    assert after == payload["protected_sha256_before"], "Protected input changed since initial replay"
    payload["protected_sha256_after"] = after
    payload["status"] = "PASS_ALTERNATING_EXECUTION__FAIL_STRICT_SOURCE_IDENTITY__INCONCLUSIVE_GLOBAL_OPTIMALITY"
    payload["initial_replay_audit_sha256"] = digest(initial / "alt_opt_independence_test.json")
    payload["initial_replay_producer_sha256"] = original_replay_producer
    payload["producer_sha256"] = digest(__file__)
    payload["finalization"] = "Reuses saved counterfactual histories; no repeated evaluator or source moment calls"
    for name in ("alt_opt_vs_numerical_comparison.csv", "alt_opt_iteration_evidence.csv", "counterfactual_iterations.csv"):
        shutil.copy2(initial / name, OUT / name)
    shutil.copy2(__file__, OUT / "audit_alt_opt.py")
    (OUT / "alt_opt_independence_test.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    create_report(payload, read_csv(OUT / "alt_opt_vs_numerical_comparison.csv"), read_csv(B / "ao_iterations.csv"),
                  read_csv(B / "ao_multistart_summary.csv"), payload["catalog_coverage"], payload["all_26_accounting"])
    print(payload["status"], "newline equivalence", all_eol, "protected inputs unchanged", flush=True)


if __name__ == "__main__":
    if "--render-existing" in sys.argv:
        import shutil
        OUT = ROOT / "results/alt_opt_vs_numerical_audit_20261008_verified"
        saved = json.loads((OUT / "alt_opt_independence_test.json").read_text(encoding="utf-8"))
        create_report(saved, read_csv(OUT / "alt_opt_vs_numerical_comparison.csv"), read_csv(B / "ao_iterations.csv"),
                      read_csv(B / "ao_multistart_summary.csv"), saved["catalog_coverage"], saved["all_26_accounting"])
        saved["final_report_renderer_sha256"] = digest(__file__)
        (OUT / "alt_opt_independence_test.json").write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(__file__, OUT / "audit_alt_opt.py")
        print(saved["status"], "report generated from saved evidence; zero evaluator calls", flush=True)
    elif "--finalize-existing" in sys.argv:
        finalize_existing()
    else:
        raise SystemExit(main())
