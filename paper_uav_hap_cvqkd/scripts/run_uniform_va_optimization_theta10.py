"""Uniform-only V_A verification for the frozen theta10/D10cm channel."""

from __future__ import annotations

import argparse
import csv
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs
from scripts.run_exact_mb_test2 import ExactMBEvaluator, ensemble_hash
from scripts.run_skr_vs_link_distance_theta10urad import (
    DISTANCES_KM, EPSILON, PEAK_PHOTONS, RECEIVER_RADIUS_M, THETA_NEW,
    evaluate_candidate, load_distance_config, channel_row,
)
from src.modulation.joint_ps_gs import PeakPhotonConstraintViolation, reference_ensemble


OUTPUT = ROOT / "results" / "uniform_va_optimization_theta10_D10cm"
REQUESTED_VA = (0.02, 0.04, 0.06, 0.08, 0.10, 0.11, 0.12, 0.13, 0.15, 0.20, 0.30, 0.50, 0.75, 1.0, 1.075, 1.25, 1.5, 2.0, 3.0, 5.0)
EXACT_INITIAL_VA = (0.05, 0.1, 0.6, 0.7, 0.8, 1.075, 2.05, 3.025, 4.0)
REPORTED_DISTANCES = (20.0, 22.0, 25.0, 30.0, 35.0, 40.0)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({k for row in rows for k in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def uniform_ensemble(config: dict, va: float):
    return reference_ensemble("uniform", batch_size=1, modulation_variance=float(va), v_min=0.001, v_max=100.0, n_peak_photons=PEAK_PHOTONS)


def load_cached_uniform(config: dict, va: float) -> dict | None:
    try:
        ensemble = uniform_ensemble(config, va)
        identity = ensemble_hash(ensemble)
    except Exception:
        return None
    for path in (ROOT / "results" / "exact_mb_test2" / "exact_source_cache").glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("ensemble_hash") == identity and int(payload.get("support_size", 256)) == 256 and math.isfinite(float(payload["C"])) and math.isfinite(float(payload["w"])):
                return {"family": "Uniform", "nu_raw": 0.0, "nu_repo": None, "V_A": va, "ensemble": ensemble, "ensemble_hash": identity, "source_cache_key": payload.get("cache_key", path.stem), "source_path": str(path.relative_to(ROOT)).replace("\\", "/"), "C": float(payload["C"]), "w": float(payload["w"]), "peak_photon": float(ensemble.amplitudes.abs().square().max()), "cache_origin": "EXACT_HASH_MATCH"}
        except Exception:
            continue
    return None


def build_missing_source(config: dict, va: float, evaluator: ExactMBEvaluator) -> dict:
    ensemble = uniform_ensemble(config, va)
    payload = evaluator.source_moments(ensemble, 0.0, va)
    return {"family": "Uniform", "nu_raw": 0.0, "nu_repo": None, "V_A": va, "ensemble": ensemble, "ensemble_hash": ensemble_hash(ensemble), "source_cache_key": payload["cache_key"], "source_path": str((evaluator.cache_dir / f"{payload['cache_key']}.json").relative_to(ROOT)).replace("\\", "/"), "C": float(payload["C"]), "w": float(payload["w"]), "peak_photon": float(ensemble.amplitudes.abs().square().max()), "cache_origin": payload.get("cache_origin")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--build-missing", action="store_true")
    parser.add_argument("--max-new-source-points", type=int, default=0)
    parser.add_argument("--source-workers", type=int, default=1)
    parser.add_argument("--only-va", type=float, action="append", default=[], help="Evaluate only these exact V_A values and merge them into the existing CSV.")
    args = parser.parse_args()
    torch.set_num_threads(1)
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    config = load_distance_config()
    peak_vmax = 2.0 * PEAK_PHOTONS / (2.6470588235294126)
    cached = {}; missing=[]
    for va in sorted(set(REQUESTED_VA + EXACT_INITIAL_VA)):
        candidate = load_cached_uniform(config, va)
        if candidate is None: missing.append(va)
        else: cached[va] = candidate
    evaluator = ExactMBEvaluator(config, {"T_eff": 0.0, "epsilon_base": EPSILON, "c_phi": 0.0}, output, source_cache_dir=ROOT / "results" / "exact_mb_test2" / "exact_source_cache", allow_legacy_exact_import=False)
    selected_missing = ([value for value in args.only_va if value in missing]
                        if args.only_va else sorted(missing, key=lambda value: abs(float(value) - 0.1))[:max(0, args.max_new_source_points)]) if args.build_missing else []
    if selected_missing:
        def build(va): return va, build_missing_source(config, va, evaluator)
        with ThreadPoolExecutor(max_workers=max(1, args.source_workers)) as pool:
            for va, candidate in pool.map(build, selected_missing): cached[va] = candidate
    eval_vas = sorted({float(value) for value in args.only_va}) if args.only_va else sorted(cached)
    if any(value not in cached for value in eval_vas):
        raise RuntimeError(f"Requested --only-va values are not exact-cached: {eval_vas}")
    all_rows=[]
    existing_path = output / "uniform_va_evaluated_points.csv"
    if args.only_va and existing_path.is_file():
        with existing_path.open(newline="", encoding="utf-8") as stream:
            all_rows = [row for row in csv.DictReader(stream) if float(row["VA_exact"]) not in eval_vas]
    for distance in DISTANCES_KM:
        channel=channel_row(config, distance, THETA_NEW)
        for va in eval_vas:
            candidate = cached[va]
            row=evaluate_candidate(candidate,channel,config)
            row.update({"distance_km":distance,"VA_exact":va,"channel_hash":channel["channel_hash"],"source_cache_origin":candidate["cache_origin"]})
            all_rows.append(row)
    selected=[]
    for distance in DISTANCES_KM:
        rows=[r for r in all_rows if float(r["distance_km"])==distance]
        if rows: selected.append(max(rows,key=lambda r:float(r["SKR"])))
    landscapes=[r for r in all_rows if float(r["distance_km"]) in REPORTED_DISTANCES]
    remaining_missing = [va for va in missing if va not in cached]
    report={"status":"UNIFORM_VA_OPTIMIZATION_DIAGNOSTIC_COMPLETE","theta_div_full_rad":THETA_NEW,"w0_m":2*1.55e-6/(math.pi*THETA_NEW),"D_r_m":0.10,"epsilon_total":EPSILON,"beta":0.95,"AO":"OFF","phase_noise":"OFF","peak_photons":PEAK_PHOTONS,"derived_VA_max_peak":peak_vmax,"requested_VA":list(REQUESTED_VA),"cached_VA":sorted(cached),"missing_VA":remaining_missing,"new_source_points_attempted":selected_missing,"distances_km":list(DISTANCES_KM),"optimization_scope":"cached exact Uniform VA bank plus any explicitly budgeted AP fills; no MB","status_note":"A global continuous VA claim requires exact source coverage at the requested refinement points.","operational_summary":[]}
    for distance in DISTANCES_KM:
        rows=[r for r in selected if float(r["distance_km"])==distance]
        report["operational_summary"].append({"distance_km":distance,"VA_star":None if not rows else rows[0]["V_A"],"K_max":None if not rows else rows[0]["SKR"]})
    write_csv(output/"uniform_va_evaluated_points.csv",all_rows); write_csv(output/"uniform_va_selected_by_distance.csv",selected); write_csv(output/"uniform_va_landscapes_20_30_35_40.csv",landscapes); write_csv(output/"uniform_va_missing_source_points.csv",[{"V_A":va,"status":"MISSING_EXACT_SOURCE_MOMENT"} for va in remaining_missing]);
    (output/"uniform_va_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
