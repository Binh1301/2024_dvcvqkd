"""Small exact-source batches using the unchanged evaluator and supervisor.

Numerical code is imported, never reimplemented. Windows Job accounting adds
CPU measurements only; source generation runs in the original probe worker.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_theta10_D55_alt_opt_closure_continuation as prep
from scripts import run_theta10_D55_alt_opt_convergence_validation as validation
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source


def supervised_probe(command, timeout, log):
    """Delegate the validated deadline/Job supervisor, read Job CPU at close."""
    original_win_dll = ctypes.WinDLL
    cpu = {}
    class Accounting(ctypes.Structure):
        _fields_ = [(name, ctypes.c_longlong) for name in
                    ("user", "kernel", "period_user", "period_kernel")] + [
                    (name, wintypes.DWORD) for name in ("faults", "processes", "active", "terminated")]
    class KernelAccounting:
        def __init__(self, kernel):
            self.kernel = kernel
            self.original_close = kernel.CloseHandle
            self.original_close.argtypes = [wintypes.HANDLE]
            self.original_close.restype = wintypes.BOOL
            query = kernel.QueryInformationJobObject
            query.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
            query.restype = wintypes.BOOL
            def close(handle):
                stats = Accounting()
                if query(handle, 1, ctypes.byref(stats), ctypes.sizeof(stats), None):
                    cpu.update(user_cpu_seconds=stats.user / 1e7, kernel_cpu_seconds=stats.kernel / 1e7,
                               aggregate_cpu_seconds=(stats.user + stats.kernel) / 1e7,
                               accounted_processes=int(stats.processes), cpu_measurement="WINDOWS_JOB_BASIC_ACCOUNTING")
                else:
                    cpu.update(cpu_measurement="FAILED", cpu_query_error=ctypes.get_last_error())
                return self.original_close(handle)
            self.CloseHandle = close
        def __getattr__(self, name):
            return getattr(self.kernel, name)
    def accounting_dll(name, *args, **kwargs):
        kernel = original_win_dll(name, *args, **kwargs)
        return KernelAccounting(kernel) if name.lower() == "kernel32" else kernel
    with patch.object(ctypes, "WinDLL", accounting_dll):
        result = validation.bounded_process(command, timeout, log)
    return {**result, **cpu}


def self_check():
    import tempfile
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
        result = supervised_probe([sys.executable, "-c", "while True: pass"], .4, log)
    assert result["deadline_exceeded"] and result["elapsed_seconds"] < 3
    assert result["cpu_measurement"] == "WINDOWS_JOB_BASIC_ACCOUNTING"
    assert result["aggregate_cpu_seconds"] > 0 and result["accounted_processes"] >= 1
    print(json.dumps(result, indent=2))


def verify_protected(out):
    manifest = json.loads((out / "protected_input_manifest.json").read_text())
    for name, expected in manifest.items():
        if validation.digest(ROOT / name) != expected:
            raise ValueError("Protected input changed: " + name)
    return len(manifest)


def controller_alive(pid):
    """Fail closed on a live checkpoint owner; never start a duplicate job."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        if ctypes.get_last_error() == 5:
            raise PermissionError("Cannot verify checkpoint owner")
        return False
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise OSError(ctypes.get_last_error(), "Cannot query checkpoint owner")
        return code.value == 259
    finally:
        kernel.CloseHandle(handle)


def run_batch(out, point, timeout, number, ledger):
    key = point["raw_current_cache_key"]
    probe_dir = out / "probe_results"
    probe_dir.mkdir(exist_ok=True)
    path = probe_dir / (key + ".json")
    validation.archive_probe_attempt(path)
    validation.save_json(path, {"status": "RUNNING", "cache_key": key,
        "nu_raw": float(point["nu_raw"]), "V_A": float(point["V_A"]),
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "timeout_seconds": timeout})
    command = [sys.executable, "-X", "utf8", "-u", str(Path(validation.__file__).resolve()),
               "--probe", "--output-dir", str(out), "--nu", point["nu_raw"], "--va", point["V_A"],
               "--per-probe-timeout", str(timeout)]
    print(f"Batch {number}: source nu={point['nu_raw']}, VA={point['V_A']}, deadline={timeout:.3f}s", flush=True)
    start = time.monotonic()
    with (probe_dir / (key + f"_attempt_{number}.log")).open("w", encoding="utf-8") as log:
        supervision = supervised_probe(command, timeout, log)
    wall = time.monotonic() - start
    record = json.loads(path.read_text())
    if record["status"] == "RUNNING":
        record["status"] = "TIMEOUT" if supervision["deadline_exceeded"] else "PROCESS_FAILURE"
    record.update(batch=number, wall_seconds=wall, supervision=supervision,
                  cpu_seconds=supervision.get("aggregate_cpu_seconds"), timeout_seconds=timeout)
    # Validate from actual overlay bytes, not the worker's COMPLETED label alone.
    payloads = source.load_source_payloads(source.unconstrained_config(), (source.SOURCE_CACHE, out / "exact_source_cache"))
    if record["status"] == "COMPLETED_EXACT":
        candidate = source.candidate_from_payload(source.unconstrained_config(), payloads, "MB",
                                                  float(point["nu_raw"]), float(point["V_A"]))
        if candidate is None or candidate["ensemble_hash"] != point["ensemble_hash"]:
            raise ValueError("Completed source failed ensemble/identity validation")
        record["source_payload_verified"] = True
    validation.save_json(path, record)
    ledger["attempts"].append(record)
    ledger["used_wall_seconds"] += wall
    ledger["completed_unique_ensembles"] = sum(r["status"] == "COMPLETED_EXACT" for r in ledger["attempts"])
    ledger["status"] = "BATCH_SAVED"
    validation.save_json(out / "source_generation_ledger.json", ledger)
    validation.write_csv(out / "new_exact_source_moments.csv", [{k: r.get(k) for k in
        ("batch", "nu_raw", "V_A", "cache_key", "status", "C", "w", "source_path", "wall_seconds", "cpu_seconds",
         "timeout_seconds", "source_payload_verified", "error")} for r in ledger["attempts"]])
    verify_protected(out)
    print(f"Batch {number} saved: {record['status']}, wall={wall:.3f}s, CPU={record.get('cpu_seconds')}s", flush=True)
    return record


def continue_stagnated(out, number):
    stage = out / "coordinate_batches" / f"batch_{number}"
    stage.mkdir(parents=True)
    config = source.unconstrained_config()
    audit = json.loads(validation.AUDIT.read_text(encoding="utf-8"))
    old_report = json.loads((sweep.OUTPUT / "run_report.json").read_text(encoding="utf-8"))
    # Hash-attested compatible objectives are reused by the original routine.
    cache_dir = out / "exact_objective_cache"
    cache_dir.mkdir(exist_ok=True)
    original_objective = ao.ExactObjective
    class CheckpointObjective(original_objective):
        # Operational persistence only: all calculations delegate unchanged.
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.checkpoint = cache_dir / (self.context_hash + ".json")
            if self.checkpoint.exists():
                saved = json.loads(self.checkpoint.read_text())
                self.restore_objective_rows(saved["rows"], saved["identity"])
        def __call__(self, nu, va):
            before = self.unique_exact_evaluations
            value = super().__call__(nu, va)
            if self.unique_exact_evaluations > before:
                validation.save_json(self.checkpoint, {"identity": self.objective_identity, "rows": list(self.rows.values())})
            return value
    with patch.object(ao, "ExactObjective", CheckpointObjective):
        result = validation.validate_distances(stage, prep.STAGNATED, config, audit, old_report,
            validation.read_csv(prep.REFERENCE / "mb_alt_opt_distance_summary.csv"),
            validation.read_csv(sweep.OUTPUT / "ao_objective_evaluations.csv"), out / "exact_source_cache")
    records, iterations, boundaries, runs = result
    gate = (all(r["status"] == "CONVERGED_NUMERICALLY" and r["local_coordinate_search_complete"]
                and r["final_pair_is_catalog_coordinate_optimum"] for r in records)
            and all(r["status"] == "CONVERGED_NUMERICALLY" for r in runs))
    if gate:
        # Extend only after representative validation, never blindly before it.
        remaining = tuple(l for l in sweep.DISTANCES_KM if l not in prep.STAGNATED)
        more = out / "coordinate_batches" / f"batch_{number}_remaining"
        more.mkdir()
        with patch.object(ao, "ExactObjective", CheckpointObjective):
            r2, i2, b2, runs2 = validation.validate_distances(more, remaining, config, audit, old_report,
                validation.read_csv(prep.REFERENCE / "mb_alt_opt_distance_summary.csv"),
                validation.read_csv(sweep.OUTPUT / "ao_objective_evaluations.csv"), out / "exact_source_cache")
        records += r2; iterations += i2; boundaries += b2; runs += runs2
    validation.save_json(stage / "batch_results.json", {"records": records, "iterations": iterations,
                         "boundaries": boundaries, "runs": runs, "representative_gate": gate})
    baseline_summary = validation.read_csv(prep.REFERENCE / "mb_alt_opt_distance_summary.csv")
    summary_by_l = {float(r["L_km"]): r for r in baseline_summary}
    for r in records:
        summary_by_l[r["L_km"]] = {**r, "selected_initialization": r["selected_start"], "AO_iterations": r["outer_iterations"]}
    evaluator = ao.ExactMBEvaluator(config, {"T_eff": 0., "epsilon_base": .0186, "c_phi": 0.}, out,
                                   source_cache_dir=out / "exact_source_cache", allow_legacy_exact_import=False)
    ranked = validation.priorities(config, evaluator, iterations, list(summary_by_l.values()))
    inventory, dependency_map = prep.inventory(iterations, list(summary_by_l.values()), ranked)
    validation.write_csv(out / "current_missing_source_priorities.csv", ranked)
    validation.write_csv(out / "current_missing_source_dependency_map.csv", dependency_map)
    validation.write_csv(out / "current_unresolved_search_inventory.csv", inventory)
    return stage


def finish_report(out, ledger, config, measured_budget_wall):
    # Filled from persisted batches, so interruption/resume does not invent an after result.
    historical = validation.read_csv(prep.REFERENCE / "mb_alt_opt_distance_summary.csv")
    latest, all_iterations, all_boundaries = {}, [], []
    for file in sorted((out / "coordinate_batches").glob("batch_*/batch_results.json"),
                       key=lambda p: int(p.parent.name.split("_")[1])):
        data = json.loads(file.read_text())
        for r in data["records"]:
            latest[float(r["L_km"])] = {**r, "execution": "CONTINUED_EXACT_BATCH_" + file.parent.name}
        all_iterations += [{**r, "batch": file.parent.name, "execution": "NEW_EXACT_COORDINATE_CONTINUATION"} for r in data["iterations"]]
        all_boundaries += [{**r, "batch": file.parent.name, "execution": "NEW_EXACT_COORDINATE_CONTINUATION"} for r in data["boundaries"]]
    results, comparisons = [], []
    for old in historical:
        distance = float(old["L_km"])
        r = latest.get(distance, {**old, "execution": "LAST_KNOWN_NOT_CONTINUED_NO_NEW_SOURCE_FOR_REPRESENTATIVE_GATE"})
        results.append(r)
        comparisons.append({"L_km": distance, "previous_nu": old["nu_raw_star"], "previous_V_A": old["V_A_star"],
            "previous_K": old["K"], "continued_nu": r["nu_raw_star"] if distance in latest else None,
            "continued_V_A": r["V_A_star"] if distance in latest else None,
            "continued_K": r["K"] if distance in latest else None,
            "delta_K": float(r["K"]) - float(old["K"]) if distance in latest else None,
            "execution": r["execution"], "status": r["status"]})
    payloads = source.load_source_payloads(config, (source.SOURCE_CACHE, out / "exact_source_cache"))
    deps = validation.read_csv(out / "missing_source_dependency_map.csv")
    available = {p["ensemble_hash"] for p in payloads.values()}
    remaining = [d for d in deps if d["ensemble_hash"] not in available]
    tests = subprocess.run([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
                            "-p", "test_alt_opt_provenance_and_stopping.py", "-v"], cwd=ROOT, capture_output=True, text=True)
    (out / "regression_tests.txt").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    validation.write_csv(out / "ao_26distance_results.csv", results)
    validation.write_csv(out / "previous_vs_continued_results.csv", comparisons)
    if all_iterations:
        validation.write_csv(out / "ao_iteration_history.csv", all_iterations)
        validation.write_csv(out / "ao_coordinate_search_status.csv", all_boundaries)
        validation.write_csv(out / "ao_boundary_closure_status.csv", all_boundaries)
    report = {"status": "EXACT_SOURCE_BATCHES_FINISHED_WITH_UNRESOLVED_SEARCH", "scope": "DIAGNOSTIC_ONLY",
        "total_budget_seconds": ledger["total_compute_budget_seconds"], "per_probe_limit_seconds": ledger["per_probe_timeout_seconds"],
        "budget_session_wall_seconds": measured_budget_wall, "source_wall_seconds": ledger["used_wall_seconds"],
        "source_cpu_seconds": sum(r.get("cpu_seconds") or 0 for r in ledger["attempts"]),
        "attempted_unique_sources": len({r["cache_key"] for r in ledger["attempts"]}),
        "completed_original_50_sources": len({d["ensemble_hash"] for d in deps} & (available - {
             p["ensemble_hash"] for p in source.load_source_payloads(config).values()})),
        "old_dependency_missing_requests_remaining": len(remaining), "old_unique_sources_remaining": len({d["ensemble_hash"] for d in remaining}),
        "actually_continued_distances": sorted(latest), "newly_converged_distances": [l for l, r in latest.items() if r["status"] == "CONVERGED_NUMERICALLY"],
        "after_all_26_fresh_invocation_counts": "NOT_RUN" if len(latest) < 26 else "SEE_EXECUTED_LOGS",
        "new_coordinate_invocations": len(all_boundaries),
        "new_numerically_closed_coordinate_invocations": sum(r["numeric_local_completion"] for r in all_boundaries),
        "new_open_boundary_invocations": sum(r["boundary_status"] == "BOUNDARY_NOT_CLOSED" for r in all_boundaries),
        "epsilon_opt": ao.K_TOLERANCE, "epsilon_param": ao.PARAMETER_TOLERANCE, "max_outer_iterations": ao.MAX_AO_ITERATIONS,
        "prior_artifacts_protected_count": verify_protected(out), "source_rows_verified": len(payloads),
        "regression_tests_pass": tests.returncode == 0, "git_diff_check_pass": diff.returncode == 0,
        "results": results, "comparisons": comparisons, "attempts": ledger["attempts"],
        "limitation": "Incomplete representatives prevent blindly replaying the remaining 21. Local brackets do not provide a global continuous-domain certificate.",
        "frozen_spec_discrepancy": "Previously recorded; unchanged. Publication remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS."}
    validation.save_json(out / "convergence_report.json", report)
    md = ["# Exact-source closure continuation", "", report["status"], "",
          f"Completed original missing ensembles: {report['completed_original_50_sources']}/50; remaining {report['old_unique_sources_remaining']}.",
          f"Source wall time {report['source_wall_seconds']!r}s; aggregate Job CPU {report['source_cpu_seconds']!r}s.",
          f"Actually continued distances: {report['actually_continued_distances']}; newly converged: {report['newly_converged_distances']}.",
          "Other result rows are LAST_KNOWN, not new optimization. No timeout is assigned an SKR.", "",
          "| Probe nu | VA | Status | Wall (s) | CPU (s) |", "|---:|---:|---|---:|---:|"]
    md += [f"| {r['nu_raw']} | {r['V_A']} | {r['status']} | {r['wall_seconds']} | {r.get('cpu_seconds')} |" for r in ledger["attempts"]]
    md += ["", "| L | nu | VA | K | Delta K | VA search | nu search | Final status | Execution |",
           "|---:|---:|---:|---:|---:|---|---|---|---|"]
    md += ["| " + " | ".join(str(r.get(k, "NOT_RUN")) for k in
          ("L_km", "nu_raw_star", "V_A_star", "K", "final_delta_K", "final_V_A_search_status", "final_nu_search_status", "status", "execution")) + " |" for r in results]
    md += ["", "## Before / after", "", "Before: 836 requests, 50 ensembles, 558 inner, 280 boundary, 5 stagnated, 21 unresolved-boundary, 0 converged.",
           f"After source availability: {len(remaining)} unresolved historical dependency requests; {report['old_unique_sources_remaining']} ensembles.",
           f"Fresh all-26 invocation comparison: {report['after_all_26_fresh_invocation_counts']}. New measured search counts are separate from historical counts.",
           "", report["limitation"], report["frozen_spec_discrepancy"],
           f"Regression tests PASS={report['regression_tests_pass']}; git diff --check PASS={report['git_diff_check_pass']}."]
    (out / "convergence_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "completed_original_50_sources", "old_unique_sources_remaining", "actually_continued_distances", "newly_converged_distances")}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=prep.OUTPUT)
    parser.add_argument("--total-compute-budget", type=float)
    parser.add_argument("--per-probe-timeout", type=float)
    parser.add_argument("--max-probes", type=int, default=50)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check(); return 0
    if args.total_compute_budget is None or args.per_probe_timeout is None:
        parser.error("Both hard budgets must be explicitly supplied")
    if args.total_compute_budget < 15 or args.per_probe_timeout < 15 or args.max_probes < 1:
        parser.error("Require positive probe count and budgets >=15s")
    out = args.output_dir.resolve()
    verify_protected(out)
    ledger = json.loads((out / "source_generation_ledger.json").read_text())
    if ledger.get("controller_pid") and controller_alive(ledger["controller_pid"]):
        parser.error("Checkpoint owner is still active; refusing a duplicate controller")
    if ledger.get("status") == "STOPPED_AT_HARD_BUDGET":
        parser.error("Authorized hard budget exhausted; a separately authorized continuation is required")
    if ledger["attempts"] and not args.resume:
        parser.error("Prior attempts exist; require --resume (failed probes will not be silently retried)")
    if ledger["total_compute_budget_seconds"] is not None and (
        ledger["total_compute_budget_seconds"] != args.total_compute_budget or ledger["per_probe_timeout_seconds"] != args.per_probe_timeout):
        parser.error("Budget identity changed; a separate authorization is required")
    ledger.update(total_compute_budget_seconds=args.total_compute_budget, per_probe_timeout_seconds=args.per_probe_timeout,
                  status="SOURCE_CONTINUATION_RUNNING", controller_pid=__import__('os').getpid())
    config = source.unconstrained_config()
    (out / "exact_source_cache").mkdir(exist_ok=True)
    (out / "coordinate_batches").mkdir(exist_ok=True)
    ledger["producer_sha256"] = validation.digest(__file__)
    validation.save_json(out / "source_generation_ledger.json", ledger)
    tried = {r["cache_key"] for r in ledger["attempts"]}
    start = time.monotonic()
    deadline = start + args.total_compute_budget - ledger["used_wall_seconds"]
    count = 0
    while count < args.max_probes and time.monotonic() < deadline - 15:
        priority_file = out / "current_missing_source_priorities.csv"
        priorities = validation.read_csv(priority_file if priority_file.exists() else out / "missing_source_priorities.csv")
        bank = source.load_source_payloads(config, (source.SOURCE_CACHE, out / "exact_source_cache"))
        candidates = [p for p in priorities if p["raw_current_cache_key"] not in tried and
            source.candidate_from_payload(config, bank, "MB", float(p["nu_raw"]), float(p["V_A"])) is None]
        if not candidates:
            break
        point = candidates[0]
        timeout = min(args.per_probe_timeout, deadline - time.monotonic() - 2.)
        record = run_batch(out, point, timeout, len(ledger["attempts"]) + 1, ledger)
        tried.add(point["raw_current_cache_key"])
        count += 1
        if record["status"] == "COMPLETED_EXACT" and time.monotonic() < deadline - 15:
            stage = continue_stagnated(out, len(ledger["attempts"]))
            ledger.setdefault("coordinate_checkpoints", []).append(str(stage.relative_to(out)))
            validation.save_json(out / "source_generation_ledger.json", ledger)
        # Report safely after every batch, before selecting any next independent probe.
        finish_report(out, ledger, config, time.monotonic() - start)
    ledger["status"] = "STOPPED_AT_HARD_BUDGET" if time.monotonic() >= deadline - 15 else "REQUESTED_BATCHES_COMPLETE"
    ledger["controller_finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    validation.save_json(out / "source_generation_ledger.json", ledger)
    finish_report(out, ledger, config, time.monotonic() - start)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
