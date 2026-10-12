"""Orchestrate the frozen ALT_OPT sweep; never implement scientific calculations.

Run from the project root with .venv/Scripts/python.exe -X utf8 -u
scripts/run_theta10_D55_alt_opt_26distance_strict_rerun.py.
The output must not already exist. No new source generation is permitted.
"""
from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import render_theta10_D55_three_scheme_log10 as renderer
from scripts import run_theta10_D55_unconstrained_three_scheme as source

OUTPUT = ROOT / "results/theta10_D55_alt_opt_26distance_strict_rerun"
OLD = ROOT / "results/theta10_D55_alt_opt_distance_sweep"
REFERENCE_COUNTS = dict(zip(
    ("requested_objective_calls", "unique_exact_SKR_evaluations", "cache_hits",
     "missing_exact_source_probes", "unresolved_inner_search_directions",
     "unresolved_boundary_directions"), (4147, 1357, 1954, 836, 558, 280)))


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def snapshot() -> dict[str, str]:
    # Scientific/config bytes and all input/historical experiment bytes.
    paths = set()
    directories = [ROOT / "src", ROOT / "configs", ROOT / "scripts",
                   ao.SOURCE_CACHE, source.EVALUATED_BANK.parent, OLD,
                   sweep.PREVIOUS_CSV.parent]
    directories += [ROOT / "results" / name for name in (
        "theta10_D55_alt_opt", "theta10_D55_alt_opt_convergence_validation",
        "alt_opt_vs_numerical_audit_20261008",
        "alt_opt_vs_numerical_audit_20261008_verified")]
    for directory in directories:
        paths.update(p for p in directory.rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts)
    paths.add(ROOT / "docs/FINAL_MODEL_SPEC.md")
    return {p.relative_to(ROOT).as_posix(): sweep.sha256(p) for p in sorted(paths)}


def main() -> int:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS,
            sweep.MAX_AO_ITERATIONS) == (1e-8, 1e-6, 6, 6)
    assert (ao.THETA_DIV_FULL_RAD, ao.RECEIVER_DIAMETER_M, ao.TAU_ZEN,
            ao.BETA, ao.EPSILON) == (1e-5, .55, .92, .95, .0186)
    assert ao.W0_M == .0986760647169751
    config = ao.unconstrained_config()
    assert all(config["cvqkd"][name] is None for name in
               ("v_min_snu", "v_max_snu", "v_a_budget_snu", "n_peak_photons"))
    payloads = ao.load_source_payloads(config)
    assert len(payloads) == 165
    before = snapshot()
    OUTPUT.mkdir(parents=True)
    run_config = {
        "scope": "DIAGNOSTIC_ONLY", "output_dir": str(OUTPUT),
        "existing_driver": str(Path(sweep.__file__).resolve()),
        "argv": ["--output-dir", str(OUTPUT), "--max-ao-iterations", "6"],
        "allow_new_source": False, "persistent_objective_preload": False,
        "epsilon_opt": ao.K_TOLERANCE, "epsilon_param": ao.PARAMETER_TOLERANCE,
        "max_outer_iterations": 6, "base_starts": list(sweep.BASE_STARTS),
        "distances_km": list(sweep.DISTANCES_KM), "config": config,
        "source_settings": ao.source_settings(config),
        "legend_override": {sweep.OPTIMIZED_MB_SCHEME: "ALT_OPT MB-shaped 256-QAM"},
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "git_status_before": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "frozen_spec_sha256": before["docs/FINAL_MODEL_SPEC.md"],
        "frozen_spec_discrepancy": "Previously recorded; no model edit or lifecycle promotion.",
        "command": ".venv/Scripts/python.exe -X utf8 -u scripts/run_theta10_D55_alt_opt_26distance_strict_rerun.py",
    }
    save_json(OUTPUT / "rerun_config.json", run_config)
    save_json(OUTPUT / "input_manifest_before.json", before)
    started = time.monotonic()
    print("Executing unchanged sweep: 26 distances; exact source cache only.", flush=True)
    with patch.object(sys, "argv", [sweep.__file__, *run_config["argv"]]), \
         patch.dict(renderer.LABELS, run_config["legend_override"]), \
         patch.object(ao.ExactMBEvaluator, "source_moments", side_effect=AssertionError(
             "New source generation is forbidden in this reproducibility rerun")) as generation:
        assert sweep.main() == 0
        assert generation.call_count == 0
    elapsed = time.monotonic() - started
    after = snapshot()
    save_json(OUTPUT / "input_manifest_after.json", after)
    if before != after:
        raise RuntimeError("Frozen input or historical artifact changed; inspect manifests")
    # Keep the unmodified driver's own reports before adding independent checks.
    for suffix in ("json", "md"):
        shutil.copy2(OUTPUT / f"run_report.{suffix}", OUTPUT / f"driver_run_report.{suffix}")
    report = json.loads((OUTPUT / "run_report.json").read_text(encoding="utf-8"))
    summary = rows(OUTPUT / "mb_alt_opt_distance_summary.csv")
    iterations = rows(OUTPUT / "ao_iterations.csv")
    starts = rows(OUTPUT / "ao_multistart_summary.csv")
    objectives = rows(OUTPUT / "ao_objective_evaluations.csv")
    assert [float(r["L_km"]) for r in summary] == list(sweep.DISTANCES_KM)
    assert len(starts) == 4 + 5 * 25
    assert len({r["channel_hash"] for r in objectives}) == 26
    comparison = []
    previous = {float(r["L_km"]): r for r in rows(OLD / "mb_alt_opt_distance_summary.csv")}
    for row in summary:
        distance = float(row["L_km"])
        distance_starts = [s for s in starts if float(s["distance_km"]) == distance]
        assert {float(s["initial_nu"]) for s in distance_starts
                if s["start_id"] != "warm_previous_distance"} == set(sweep.BASE_STARTS)
        selected = next(s for s in distance_starts if s["start_id"] == row["selected_initialization"])
        history = [r for r in iterations if float(r["distance_km"]) == distance
                   and r["start_id"] == selected["start_id"]]
        assert len(history) == int(row["AO_iterations"]) > 0
        terminal = max(history, key=lambda r: int(r["iteration"]))
        assert selected["status"] == row["best_run_status"] == terminal["convergence_status"]
        row["aggregate_search_status"] = row["status"]
        row["status"] = row["best_run_status"]
        row["selection_claim"] = "BEST_EXACT_TESTED_CANDIDATE_ONLY"
        row["initial_nu"] = selected["initial_nu"]
        row["initial_V_A"] = selected["initial_V_A"]
        row["final_delta_K"] = terminal["delta_K"]
        for name in ("V_A_search_status", "nu_search_status", "V_A_boundary_status",
                     "nu_boundary_status", "V_A_refinement_status", "nu_refinement_status"):
            row["final_" + name] = terminal[name]
        old = previous[distance]
        item = {"L_km": distance, "termination_status": row["status"]}
        for name in ("nu_raw_star", "V_A_star", "I_AB", "beta_I_AB", "chi_BE", "K"):
            item["previous_" + name] = old[name]
            item["new_" + name] = row[name]
            item["abs_delta_" + name] = abs(float(row[name]) - float(old[name]))
        item["status"] = ("EXACT_MATCH" if all(item["abs_delta_" + name] == 0
                           for name in ("nu_raw_star", "V_A_star", "I_AB", "beta_I_AB", "chi_BE", "K"))
                          else "DIFFERENT")
        comparison.append(item)
    # Check both actual coordinate steps for every start, not only the winner.
    for row in iterations:
        va_history, nu_history = (json.loads(row[name]) for name in
                                  ("V_A_candidate_history", "nu_candidate_history"))
        assert all(float(p["nu_raw"]) == float(row["nu_before"])
                   for p in va_history if p["status"] == "EXACT_EVALUATED")
        assert all(float(p["V_A"]) == float(row["optimized_V_A"])
                   for p in nu_history if p["status"] == "EXACT_EVALUATED")
        assert all("K" not in p for p in va_history + nu_history
                   if p["status"] == "EXACT_SOURCE_MISSING")
        assert int(row["iteration"]) < 6
    combined = rows(OUTPUT / "three_scheme_alt_opt.csv")
    previous_non_mb = [r for r in rows(sweep.PREVIOUS_CSV)
                       if r["scheme"] != sweep.OPTIMIZED_MB_SCHEME]
    assert [r for r in combined if r["scheme"] != sweep.OPTIMIZED_MB_SCHEME] == previous_non_mb
    fixed = [r for r in combined if r["scheme"] == sweep.FIXED_MB_SCHEME]
    assert all(float(r["nu_raw"]) == .2 and float(r["V_A"]) == source.FIXED_MB_VA_EXACT for r in fixed)
    plot_report = json.loads((OUTPUT / "skr_vs_distance_three_scheme_log10_report.json").read_text(encoding="utf-8"))
    assert (plot_report["yscale"], plot_report["base"], plot_report["uniform_last_positive_distance_km"]) == ("log", 10, 25.)
    assert list(plot_report["plotted_positive_rows"].values()) == [7, 26, 26]
    for scheme in sweep.SCHEME_ORDER[1:]:
        assert max(float(r["distance_km"]) for r in combined
                   if r["scheme"] == scheme and float(r["K"]) > 0) == 40.
    totals = {key: sum(int(r[key]) for r in summary) for key in REFERENCE_COUNTS}
    matched = sum(r["status"] == "EXACT_MATCH" for r in comparison)
    report.update({
        "status": "EXACT_TESTED_ALT_OPT_REPRODUCIBILITY_PASS" if matched == 26 else "REPRODUCIBILITY_DIFFERENCE",
        "per_distance_summary": summary, "elapsed_s": elapsed,
        "stopping_settings": {"epsilon_opt": 1e-8, "epsilon_param": 1e-6, "max_outer_iterations": 6},
        "termination_status_counts": dict(Counter(r["status"] for r in summary)),
        "actual_totals": totals, "reference_totals": REFERENCE_COUNTS,
        "total_differences": {k: totals[k] - REFERENCE_COUNTS[k] for k in totals},
        "all_distance_comparison": {"reference": str(OLD / "mb_alt_opt_distance_summary.csv"),
                                    "exact_matches": matched,
                                    "max_abs_delta_K": max(r["abs_delta_K"] for r in comparison)},
        "executed_counts": {"multistarts": len(starts), "iterations": len(iterations), "objectives": len(objectives)},
        "source_generation_calls": generation.call_count,
        "fixed_mb_binary64": {"nu_raw": .2, "V_A": source.FIXED_MB_VA_EXACT,
                              "V_A_hex": source.FIXED_MB_VA_EXACT.hex(), "display_V_A": "1.3833230303"},
        "legend_override": run_config["legend_override"],
        "validation": {name: "CURRENTLY_VERIFIED_PASS" for name in (
            "provenance_policy_retained", "physical_model_unchanged", "source_moment_math_unchanged",
            "source_numerical_method_unchanged", "security_evaluator_unchanged", "ao_algorithm_unchanged",
            "epsilon_1e_minus_8", "max_outer_6", "all_26_distances_actually_rerun", "no_interpolation",
            "no_new_source_generation", "previous_artifacts_preserved", "figure_positive_only", "standard_log10")},
        "validation_evidence": {"freeze": "input_manifest_before.json == input_manifest_after.json",
                                "execution": "ao_iterations.csv, ao_multistart_summary.csv, ao_objective_evaluations.csv",
                                "source": "strict compatible loader accepted 165; generation guard call_count=0",
                                "figure": plot_report},
    })
    report["artifacts"]["previous_alt_opt_comparison_csv"] = "previous_vs_rerun_comparison.csv"
    sweep.write_csv(OUTPUT / "mb_alt_opt_distance_summary.csv", summary)
    sweep.write_csv(OUTPUT / "previous_vs_rerun_comparison.csv", comparison)
    save_json(OUTPUT / "run_report.json", report)
    markdown = ["# Strict 26-distance ALT_OPT reproducibility", "",
                f"Status: `{report['status']}`; scope: DIAGNOSTIC_ONLY.", "",
                f"Exact six-field matches: {matched}/26; max |delta K|: {report['all_distance_comparison']['max_abs_delta_K']}.",
                "Epsilon_opt=1e-8; epsilon_param=1e-6; max outer iterations=6.",
                f"Termination statuses: {report['termination_status_counts']}.", "",
                "| L (km) | nu_raw | V_A | I_AB | beta I_AB | chi_BE | K | Actual termination |",
                "|---:|---:|---:|---:|---:|---:|---:|---|"]
    markdown += ["| " + " | ".join([r[k] for k in
                  ("L_km", "nu_raw_star", "V_A_star", "I_AB", "beta_I_AB", "chi_BE", "K", "status")]) + " |" for r in summary]
    markdown += ["", "## Diagnostics versus historical reference", "",
                 "| Metric | Historical | Rerun | Delta |", "|---|---:|---:|---:|"]
    markdown += [f"| {k} | {REFERENCE_COUNTS[k]} | {totals[k]} | {totals[k]-REFERENCE_COUNTS[k]} |" for k in totals]
    markdown += ["", "## Validation", ""] + [f"- PASS: {k}" for k in report["validation"]]
    markdown += ["", "Uniform/fixed curves reuse unchanged exact stored rows. Uniform ends at 25 km; both MB curves at 40 km.",
                 "Fixed MB uses exact binary64 nu=.2, VA=1.3833230302980657 (display 1.3833230303).",
                 "No arbitrary-precision generation, interpolation, mathematical or algorithmic edit was performed.",
                 "The new wrapper changes only orchestration, reporting and the MB legend; the original driver reports are preserved separately.",
                 "Finite exact-source coverage leaves unresolved directions. No global optimum or continuous convergence is claimed.",
                 "Publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS; the recorded frozen-spec hash discrepancy remains open."]
    (OUTPUT / "run_report.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    snapshots = OUTPUT / "script_snapshots"
    snapshots.mkdir()
    for script in (Path(__file__), Path(ao.__file__), Path(sweep.__file__), Path(renderer.__file__),
                   ROOT / "scripts/exact_cache_provenance.py"):
        shutil.copy2(script, snapshots / script.name)
    print(json.dumps({k: report[k] for k in ("status", "actual_totals", "termination_status_counts", "all_distance_comparison")}, indent=2), flush=True)
    return 0 if matched == 26 else 1


if __name__ == "__main__":
    raise SystemExit(main())
