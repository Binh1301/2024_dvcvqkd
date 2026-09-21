"""Extend the deterministic scalar-T distance diagnostic beyond 24 km."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_updated_noise_smooth_distance import (
    MB_NUS,
    MI_SAMPLES_PER_SYMBOL,
    MI_SEEDS,
    _load_sources,
    _ensembles,
    _evaluate_distance,
)
import src.cvqkd.holevo as holevo_module
from src.cvqkd.mutual_information import standard_complex_noise
from src.utils.random import torch_generator


TRACKED = ("binomial",) + tuple(f"mb_{nu:g}" for nu in MB_NUS if nu != 0.02)
MAX_DISTANCE_KM = 100.0
COARSE_STEP_KM = 0.5
REFINEMENT_TOLERANCE_KM = 0.05


def _key(row: dict) -> str:
    if row["modulation"] == "Uniform":
        return "uniform"
    if row["modulation"] == "Binomial":
        return "binomial"
    return f"mb_{float(row['nu_MB']):g}"


def _read_existing_rows(path: Path) -> dict[tuple[str, float], dict]:
    rows = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            key = _key(row)
            rows[(key, float(row["L_km"]))] = row
    return rows


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    old_artifact = ROOT / "results" / "updated_noise_smooth_distance_va2" / "updated_noise_smooth_distance_va2.csv"
    output_dir = ROOT / "results" / "updated_noise_extended_distance_va2"
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "_progress_cache.json"
    old_rows = _read_existing_rows(old_artifact)
    if any((key, 19.0) not in old_rows for key in TRACKED):
        raise RuntimeError("The current smooth artifact lacks a required 19 km row.")
    expected_19 = {
        "binomial": 0.003958973306,
        "mb_0.2": 0.004327928681,
    }
    observed_19 = {key: float(old_rows[(key, 19.0)]["K_raw"]) for key in expected_19}
    deltas_19 = {key: observed_19[key] - expected_19[key] for key in expected_19}
    if any(abs(value) > 5.0e-12 for value in deltas_19.values()):
        raise RuntimeError(f"19 km checkpoint mismatch: {deltas_19}")
    if any((key, 24.0) not in old_rows for key in TRACKED):
        raise RuntimeError("The current smooth artifact lacks a required 24 km row.")

    sources, source_metadata = _load_sources()
    sources = {key: sources[key] for key in TRACKED}
    ensembles = _ensembles(config)
    ensembles = {key: ensembles[key] for key in TRACKED}
    noises = {
        seed: standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }

    cache: dict[float, list[dict]] = {}
    if progress_path.is_file():
        cache = {
            float(distance): rows
            for distance, rows in json.loads(progress_path.read_text(encoding="utf-8")).items()
        }
    channel_cache: dict[float, dict] = {}
    for L_km in (24.0,):
        cache[L_km] = [old_rows[(key, L_km)] for key in TRACKED]
    for key in TRACKED:
        source_metadata.pop("uniform", None)
        source_metadata.pop("mb_0.02", None)

    original_maximizer = holevo_module._maximize_bounded_scalar
    holevo_module._maximize_bounded_scalar = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        RuntimeError("Extended smooth diagnostic reached forbidden full-Z path.")
    )
    try:
        def evaluate_new(L_km: float) -> list[dict]:
            if L_km in cache:
                return cache[L_km]
            channel_row, rows = _evaluate_distance(
                config, sources, ensembles, noises, L_km
            )
            channel_cache[L_km] = channel_row
            cache[L_km] = rows
            progress_path.write_text(json.dumps(cache) + "\n", encoding="utf-8")
            print(f"evaluated L={L_km:.3f} km", flush=True)
            return rows

        # Coarse extension. Stop only after every tracked curve has crossed.
        brackets: dict[str, tuple[float, float]] = {}
        L_km = 24.0 + COARSE_STEP_KM
        while L_km <= MAX_DISTANCE_KM and len(brackets) < len(TRACKED):
            rows = evaluate_new(round(L_km, 10))
            for key in TRACKED:
                if key in brackets:
                    continue
                previous_L = max(
                    distance for (row_key, distance) in [(key, d) for d in cache]
                    if distance < L_km and float(next(r["K_raw"] for r in cache[distance] if _key(r) == key)) > 0.0
                ) if any(
                    distance < L_km and float(next(r["K_raw"] for r in cache[distance] if _key(r) == key)) > 0.0
                    for distance in cache
                ) else None
                current = float(next(r["K_raw"] for r in rows if _key(r) == key))
                if previous_L is not None and current <= 0.0:
                    brackets[key] = (previous_L, L_km)
            L_km += COARSE_STEP_KM
        missing = sorted(set(TRACKED) - set(brackets))

        # Bisection uses the same deterministic scalar pipeline at every new point.
        zero_summary = []
        for key in sorted(brackets):
            low, high = brackets[key]
            while high - low > REFINEMENT_TOLERANCE_KM:
                midpoint = round((low + high) / 2.0, 10)
                mid_row = next(r for r in evaluate_new(midpoint) if _key(r) == key)
                if float(mid_row["K_raw"]) > 0.0:
                    low = midpoint
                else:
                    high = midpoint
            low_row = next(r for r in evaluate_new(low) if _key(r) == key)
            high_row = next(r for r in evaluate_new(high) if _key(r) == key)
            zero_summary.append({
                "modulation": "Binomial" if key == "binomial" else "MB",
                "nu_MB": None if key == "binomial" else float(key[3:]),
                "L_last_positive_km": low,
                "K_last_positive": float(low_row["K_raw"]),
                "L_first_nonpositive_km": high,
                "K_first_nonpositive": float(high_row["K_raw"]),
                "L_zero_estimate_km": (low + high) / 2.0,
            })
        for key in missing:
            zero_summary.append({
                "modulation": "Binomial" if key == "binomial" else "MB",
                "nu_MB": None if key == "binomial" else float(key[3:]),
                "L_last_positive_km": MAX_DISTANCE_KM,
                "K_last_positive": float(next(r["K_raw"] for r in cache[MAX_DISTANCE_KM] if _key(r) == key)),
                "L_first_nonpositive_km": None,
                "K_first_nonpositive": None,
                "L_zero_estimate_km": None,
            })
    finally:
        holevo_module._maximize_bounded_scalar = original_maximizer

    all_rows = []
    for distance in sorted(cache):
        all_rows.extend(cache[distance])
    payload = {
        "artifact": "UPDATED_NOISE_EXTENDED_SMOOTH_DISTANCE_VA2",
        "status": "DIAGNOSTIC_ONLY",
        "T_convention": "deterministic analytic mean_sqrt_eta squared; no per-realization K averaging",
        "coarse_step_km": COARSE_STEP_KM,
        "refinement_tolerance_km": REFINEMENT_TOLERANCE_KM,
        "maximum_distance_km": MAX_DISTANCE_KM,
        "zero_crossing_not_found_by_max_distance": missing,
        "regression_19km": {"expected": expected_19, "observed": observed_19, "deltas": deltas_19, "passed": True},
        "source_moments_recomputed": False,
        "ap_worker_invoked": False,
        "full_z_optimization_invoked": False,
        "channel_rows": channel_cache,
        "threshold_summary": zero_summary,
        "rows": all_rows,
        "source_moments": source_metadata,
        "runtime_seconds": time.perf_counter() - started,
    }
    (output_dir / "extended_distance_va2.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "extended_distance_va2.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    with (output_dir / "zero_crossing_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(zero_summary[0]))
        writer.writeheader()
        writer.writerows(zero_summary)
    if progress_path.is_file():
        progress_path.unlink()
    print(json.dumps({"rows": len(all_rows), "thresholds": zero_summary, "output_dir": str(output_dir), "runtime_seconds": payload["runtime_seconds"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
