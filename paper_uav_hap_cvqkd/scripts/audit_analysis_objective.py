"""Audit the bounded analysis objective against the saved full-Z data.

This is a read-only, analysis-estimate producer.  It does not train a model,
touch final-test data, or change the production security path.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_analysis_figures as runner  # noqa: E402
from src.modulation.joint_ps_gs import Ensemble  # noqa: E402


DATE = "20260911"
INPUT = ROOT / "results" / f"analysis_figure_data_{DATE}.json"
OUTPUT = ROOT / "results" / f"analysis_objective_audit_{DATE}.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _json(value: object) -> None:
    OUTPUT.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _proxy_z(point: dict[str, float], row: dict[str, float], va: float) -> tuple[float, float, float, float]:
    t = float(point["T"])
    epsilon = float(point["epsilon_base"])
    c = float(row["C"])
    w = float(row["w"])
    a = va + 1.0
    b = 1.0 + t * va + t * epsilon
    physical_radicand = a * b - 1.0 - abs(a - b)
    z_phys = float(np.sqrt(max(physical_radicand, 0.0)))
    width = float(np.sqrt(max(2.0 * t * epsilon * w, 0.0) + 1.0e-18))
    representative = 2.0 * np.sqrt(t) * c + width
    bounded = 0.98 * z_phys * np.tanh(
        representative / (0.98 * z_phys + 1.0e-12)
    )
    z_minus = 2.0 * np.sqrt(t) * c - np.sqrt(max(2.0 * t * epsilon * w, 0.0))
    z_plus = representative
    z_lower = max(z_minus, -z_phys)
    z_upper = min(z_plus, z_phys)
    return bounded, z_lower, z_upper, z_phys


def _full_z_candidate_summary(
    payload: dict[str, object],
    points: list[dict[str, float]],
) -> dict[str, dict[str, object]]:
    weights = torch.tensor(
        [float(point["weight"]) for point in points], dtype=torch.float64
    )
    t = torch.tensor([float(point["T"]) for point in points], dtype=torch.float64)
    epsilon = torch.tensor(
        [float(point["epsilon_base"]) for point in points], dtype=torch.float64
    )
    noise = runner.standard_complex_noise(
        (len(points), 256, runner.GRID_NOISE_SAMPLES),
        generator=torch.Generator(device="cpu").manual_seed(
            runner.existing_case.AWGN_SEED
        ),
        device=torch.device("cpu"),
    )
    output: dict[str, dict[str, object]] = {}
    for mode, _, _ in runner.METHODS:
        rows = payload["candidates"][mode]["rows"]
        probabilities = torch.tensor(
            [row["probabilities"] for row in rows], dtype=torch.float64
        )
        amplitudes = torch.tensor(
            [
                [complex(value[0], value[1]) for value in row["amplitudes"]]
                for row in rows
            ],
            dtype=torch.complex128,
        )
        declared_va = torch.tensor(
            [row["V_A"] for row in rows], dtype=torch.float64
        )
        ensemble = Ensemble(
            probabilities=probabilities,
            amplitudes=amplitudes,
            declared_va=declared_va,
            raw_constellation=amplitudes,
            exact_csi_oracle=True,
            c4_symmetric=True,
        )
        ensemble.validate()
        c = torch.tensor(
            [row["C_surrogate"] for row in rows], dtype=torch.float64
        )
        w = torch.tensor(
            [row["w_surrogate"] for row in rows], dtype=torch.float64
        )
        mi = runner.discrete_mutual_information(
            ensemble,
            t,
            epsilon,
            noise_samples_per_symbol=noise.shape[-1],
            standard_noise_samples=noise,
            noise_sample_chunk_size=noise.shape[-1],
        )
        holevo = runner._holevo_from_moments(
            ensemble,
            t,
            epsilon,
            c,
            w,
            analysis_grid=False,
        )
        key_rate = runner.BETA * mi - holevo.chi_be
        output[mode] = {
            "source_moments": "saved TRAINING_SURROGATE values",
            "security_status": "ANALYSIS_ESTIMATE; not AP source moments",
            "full_Z_surrogate_source_weighted_raw_K": float(
                torch.sum(weights * key_rate)
            ),
            "full_Z_surrogate_source_positive_active_states": int(
                (key_rate > 0.0).sum()
            ),
            "full_Z_surrogate_source_mean_raw_K": float(key_rate.mean()),
            "proxy_weighted_raw_K": float(
                np.sum(
                    np.asarray([point["weight"] for point in points])
                    * np.asarray(
                        [row["raw_K"] for row in payload["grid_security_surrogate"][mode]["rows"]]
                    )
                )
            ),
        }
    return output


def main() -> int:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    points = [point for point in payload["grid"]["points"] if point["active"]]
    weights = np.asarray([point["weight"] for point in points], dtype=np.float64)
    audit: dict[str, object] = {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "status": "OBJECTIVE_AUDIT_READY",
        "not_security_certification": True,
        "scope": (
            "saved analysis grid, smooth search proxy, exact baseline full-Z rows, "
            "and full-Z re-evaluation of saved candidate ensembles using surrogate C/w"
        ),
        "inputs": {
            "figure_data": str(INPUT.relative_to(ROOT)),
            "figure_data_sha256": _sha256(INPUT),
            "runner": "scripts/run_analysis_figures.py",
            "runner_sha256": _sha256(ROOT / "scripts" / "run_analysis_figures.py"),
            "final_model_spec_sha256": _sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
        "weight_audit": {
            "active_state_count": len(points),
            "active_mass": float(sum(weights)),
            "outage_mass": float(payload["grid"]["outage_mass"]),
            "active_weight_min": float(weights.min()),
            "active_weight_max": float(weights.max()),
            "all_weights_sum": float(sum(weights) + float(payload["grid"]["outage_mass"])),
            "conditional_active_normalization_factor": float(1.0 / sum(weights)),
            "interpretation": (
                "The optimization sum includes unconditional active mass; dividing by "
                "active mass would rescale every method equally and cannot explain a rank reversal."
            ),
        },
        "proxy_interval_audit": {},
        "baseline_full_Z_vs_search_proxy": {},
        "saved_candidate_full_Z_recheck": {},
        "provenance": {
            "repository_commit": _git("rev-parse", "HEAD"),
            "repository_dirty": bool(_git("status", "--porcelain")),
            "producer": str(Path(__file__).relative_to(ROOT)),
            "producer_sha256": _sha256(Path(__file__)),
        },
        "lifecycle": {
            "publication_scale_training": False,
            "final_test_accessed": False,
            "adaptive_training_authorized": False,
        },
    }

    for mode in runner.METHODS:
        key = mode[0]
        rows = payload["grid_security_surrogate"][key]["rows"]
        candidate_rows = payload["candidates"][key]["rows"]
        interval_rows = []
        for point, row, candidate in zip(points, rows, candidate_rows):
            va = float(candidate["V_A"])
            bounded, lower, upper, z_phys = _proxy_z(point, row, va)
            interval_rows.append(
                {
                    "T": float(point["T"]),
                    "epsilon_base": float(point["epsilon_base"]),
                    "V_A": va,
                    "Z_proxy": bounded,
                    "Z_L_from_proxy_source_moments": lower,
                    "Z_U_from_proxy_source_moments": upper,
                    "Z_phys": z_phys,
                    "below_lower": bool(bounded < lower - 1.0e-12),
                    "above_upper": bool(bounded > upper + 1.0e-12),
                    "Z_proxy_over_Z_L": bounded / lower if lower else None,
                }
            )
        ratios = [row["Z_proxy_over_Z_L"] for row in interval_rows if row["Z_proxy_over_Z_L"] is not None]
        audit["proxy_interval_audit"][key] = {
            "rows": interval_rows,
            "below_lower_count": sum(row["below_lower"] for row in interval_rows),
            "above_upper_count": sum(row["above_upper"] for row in interval_rows),
            "ratio_min": min(ratios),
            "ratio_max": max(ratios),
            "ratio_mean": float(np.mean(ratios)),
        }

    for key in ("uniform", "mb"):
        exact = payload["grid_security_exact"][key]["rows"]
        proxy = payload["grid_security_surrogate"][key]["rows"]
        exact_k = np.asarray([row["raw_K"] for row in exact], dtype=np.float64)
        proxy_k = np.asarray([row["raw_K"] for row in proxy], dtype=np.float64)
        exact_chi = np.asarray([row["chi_BE"] for row in exact], dtype=np.float64)
        proxy_chi = np.asarray([row["chi_BE"] for row in proxy], dtype=np.float64)
        audit["baseline_full_Z_vs_search_proxy"][key] = {
            "exact_full_Z_weighted_raw_K": float(np.sum(weights * exact_k)),
            "search_proxy_weighted_raw_K": float(np.sum(weights * proxy_k)),
            "exact_positive_active_states": int(np.sum(exact_k > 0.0)),
            "search_proxy_positive_active_states": int(np.sum(proxy_k > 0.0)),
            "mean_absolute_raw_K_difference": float(np.mean(np.abs(exact_k - proxy_k))),
            "mean_chi_proxy_minus_exact": float(np.mean(proxy_chi - exact_chi)),
            "max_chi_proxy_minus_exact": float(np.max(proxy_chi - exact_chi)),
        }

    audit["saved_candidate_full_Z_recheck"] = _full_z_candidate_summary(payload, points)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _json(audit)
    print(f"OBJECTIVE_AUDIT_READY: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
