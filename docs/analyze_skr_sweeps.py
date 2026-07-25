"""Reproducible audit of the six full UAV-HAP CV-QKD parameter sweeps.

This script does not train or modify a model. It reads the recorded raw sweep
CSVs, reconstructs the channel samples from their stored seeds, and writes
compact audit tables used by ``sweep_scientific_analysis_vi.md``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import visualize_skr_parameter_sweeps as sweep  # noqa: E402


OUT_DIR = ROOT / "docs" / "sweep_audit"
CONFIG_PATH = ROOT / "skr_visualization_config.json"

RAW_PATHS = {
    "aperture": ROOT / "skr_parameter_sweep_results" / "skr_vs_aperture_radius.csv",
    "visibility": ROOT / "skr_parameter_sweep_results" / "skr_vs_visibility.csv",
    "beam_waist": ROOT / "skr_parameter_sweep_results" / "skr_vs_beam_waist.csv",
    "turbulence": ROOT / "skr_parameter_sweep_results" / "skr_vs_turbulence.csv",
    "excess_noise": ROOT / "skr_parameter_sweep_results" / "skr_vs_excess_noise.csv",
    "distance": ROOT / "skr_distance_sweep_results_gpu" / "skr_vs_distance.csv",
}

BASELINES = {
    "aperture": 0.2,
    "visibility": 10.0,
    "beam_waist": 0.0626,
    "turbulence": 1e-15,
    "excess_noise": 0.001,
    "distance": 20.0,
}


def t_interval(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if values.size < 2:
        return mean, mean
    half = float(
        student_t.ppf(0.975, values.size - 1)
        * values.std(ddof=1)
        / math.sqrt(values.size)
    )
    return mean - half, mean + half


def interpolate_root(x0: float, x1: float, y0: float, y1: float) -> float:
    return float(x0 - y0 * (x1 - x0) / (y1 - y0))


def crossings(frame: pd.DataFrame, first: str, second: str) -> list[float]:
    pivot = frame.pivot(index="parameter_value", columns="scheme", values="mean_K_raw")
    values = pivot.index.to_numpy(float)
    delta = (pivot[first] - pivot[second]).to_numpy(float)
    result: list[float] = []
    for index in range(len(values) - 1):
        if delta[index] == 0.0:
            result.append(float(values[index]))
        elif delta[index] * delta[index + 1] < 0.0:
            result.append(
                interpolate_root(
                    values[index],
                    values[index + 1],
                    delta[index],
                    delta[index + 1],
                )
            )
    return result


def zero_thresholds(frame: pd.DataFrame) -> dict[str, list[float]]:
    result: dict[str, list[float]] = {}
    for scheme_name, group in frame.groupby("scheme", sort=False):
        group = group.sort_values("parameter_value")
        values = group["parameter_value"].to_numpy(float)
        raw = group["mean_K_raw"].to_numpy(float)
        roots: list[float] = []
        for index in range(len(values) - 1):
            if raw[index] == 0.0:
                roots.append(float(values[index]))
            elif raw[index] * raw[index + 1] < 0.0:
                roots.append(
                    interpolate_root(
                        values[index],
                        values[index + 1],
                        raw[index],
                        raw[index + 1],
                    )
                )
        result[str(scheme_name)] = roots
    return result


def local_extrema(frame: pd.DataFrame) -> dict[str, list[dict[str, float | str]]]:
    result: dict[str, list[dict[str, float | str]]] = {}
    for scheme_name, group in frame.groupby("scheme", sort=False):
        group = group.sort_values("parameter_value")
        x = group["parameter_value"].to_numpy(float)
        y = group["mean_K_raw"].to_numpy(float)
        entries: list[dict[str, float | str]] = []
        slopes = np.diff(y)
        for index in range(1, len(y) - 1):
            if slopes[index - 1] * slopes[index] < 0.0:
                entries.append(
                    {
                        "type": "maximum" if slopes[index - 1] > 0.0 else "minimum",
                        "x": float(x[index]),
                        "mean_K_raw": float(y[index]),
                    }
                )
        result[str(scheme_name)] = entries
    return result


def interpolated_value_and_elasticity(
    group: pd.DataFrame, baseline: float
) -> tuple[float, float]:
    group = group.sort_values("parameter_value")
    x = group["parameter_value"].to_numpy(float)
    y = group["mean_K_raw"].to_numpy(float)
    value = float(np.interp(baseline, x, y))
    upper = int(np.searchsorted(x, baseline, side="right"))
    if upper == 0:
        lower, upper = 0, 1
    elif upper >= len(x):
        lower, upper = len(x) - 2, len(x) - 1
    else:
        lower = upper - 1
    derivative = float((y[upper] - y[lower]) / (x[upper] - x[lower]))
    elasticity = float(baseline * derivative / value) if abs(value) > 1e-12 else math.nan
    return value, elasticity


def reconstruct_channel_rows(
    key: str, raw: pd.DataFrame, config: dict
) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    unique = raw[raw["scheme"] == sweep.SCHEME_ORDER[0]].copy()
    for record in unique.itertuples(index=False):
        parameters, _ = sweep.parameter_context(config, key, float(record.parameter_value))
        geometry = sweep.geometry_for_sweep(config, key, float(record.parameter_value))
        channel = sweep.core.channel(
            geometry,
            parameters,
            N=int(record.fading_samples),
            rng=np.random.default_rng(int(record.channel_seed)),
        )
        rows.append(
            {
                "sweep": key,
                "parameter_name": str(record.parameter_name),
                "parameter_value": float(record.parameter_value),
                "repetition": int(record.repetition),
                "seed": int(record.seed),
                "mean_T": float(np.mean(channel["T_samples"])),
                "std_T_samples": float(np.std(channel["T_samples"], ddof=1)),
                "T_eff": float(channel["T_eff"]),
                "eta_atm": float(channel["eta_atm"]),
                "eta_geo": float(channel["eta_geo"]),
                "sigma2_turb_m2": float(channel["sigma2_turb_m2"]),
                "sigma2_UAV_m2": float(channel["sigma2_UAV_m2"]),
                "link_distance_km": float(channel["L_km"]),
            }
        )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = sweep.load_config(CONFIG_PATH, quick=False)
    all_point_summaries: list[pd.DataFrame] = []
    all_channel_rows: list[dict[str, float | int | str]] = []
    all_delta_rows: list[dict[str, float | int | str]] = []
    all_threshold_rows: list[dict[str, float | int | str]] = []
    all_sensitivity_rows: list[dict[str, float | str]] = []
    findings: dict[str, dict] = {}

    for key, path in RAW_PATHS.items():
        raw = pd.read_csv(path)
        channel_rows = reconstruct_channel_rows(key, raw, config)
        all_channel_rows.extend(channel_rows)
        channel_summary = (
            pd.DataFrame(channel_rows)
            .groupby("parameter_value", as_index=False)
            .agg(
                mean_T=("mean_T", "mean"),
                std_repetition_mean_T=("mean_T", "std"),
                mean_eta_atm=("eta_atm", "mean"),
                mean_eta_geo=("eta_geo", "mean"),
                mean_sigma2_turb_m2=("sigma2_turb_m2", "mean"),
                mean_sigma2_UAV_m2=("sigma2_UAV_m2", "mean"),
                link_distance_km=("link_distance_km", "mean"),
            )
        )
        summary = (
            raw.groupby(
                ["parameter_name", "parameter_value", "parameter_unit", "scheme"],
                as_index=False,
                sort=False,
            )
            .agg(
                mean_I_AB=("I_AB", "mean"),
                std_I_AB=("I_AB", "std"),
                mean_chi_BE=("chi_BE", "mean"),
                std_chi_BE=("chi_BE", "std"),
                mean_K_raw=("K_raw", "mean"),
                std_K_raw=("K_raw", "std"),
                mean_K_positive=("K_positive", "mean"),
                std_K_positive=("K_positive", "std"),
            )
            .merge(channel_summary, on="parameter_value", how="left")
        )
        summary.insert(0, "sweep", key)
        all_point_summaries.append(summary)

        pivot = summary.pivot(index="parameter_value", columns="scheme", values="mean_K_raw")
        ranks = {
            f"{float(value):.16g}": list(row.sort_values(ascending=False).index)
            for value, row in pivot.iterrows()
        }
        all_crossings: dict[str, list[float]] = {}
        for first_index, first in enumerate(sweep.SCHEME_ORDER):
            for second in sweep.SCHEME_ORDER[first_index + 1 :]:
                roots = crossings(summary, first, second)
                if roots:
                    all_crossings[f"{first} / {second}"] = roots

        paired: dict[str, dict[str, float | int]] = {}
        metric_pivots = {
            metric: raw.pivot(
                index=["parameter_value", "repetition"], columns="scheme", values=metric
            )
            for metric in ("I_AB", "chi_BE", "K_raw")
        }
        raw_pivot = metric_pivots["K_raw"]
        for comparison, first, second in (
            ("PS-Uniform", "PS", "Uniform QAM"),
            ("GS-Uniform", "GS", "Uniform QAM"),
            ("PS+GS-Uniform", "PS+GS", "Uniform QAM"),
            ("PS+GS-PS", "PS+GS", "PS"),
            ("PS+GS-GS", "PS+GS", "GS"),
        ):
            significant_positive = 0
            significant_negative = 0
            for parameter_value, point in raw_pivot.groupby(level=0):
                delta = (point[first] - point[second]).to_numpy(float)
                low, high = t_interval(delta)
                significant_positive += int(low > 0.0)
                significant_negative += int(high < 0.0)
                delta_i = (
                    metric_pivots["I_AB"].loc[parameter_value, first]
                    - metric_pivots["I_AB"].loc[parameter_value, second]
                ).to_numpy(float)
                delta_chi = (
                    metric_pivots["chi_BE"].loc[parameter_value, first]
                    - metric_pivots["chi_BE"].loc[parameter_value, second]
                ).to_numpy(float)
                all_delta_rows.append(
                    {
                        "sweep": key,
                        "parameter_value": float(parameter_value),
                        "comparison": comparison,
                        "first": first,
                        "second": second,
                        "mean_delta_K_raw": float(delta.mean()),
                        "ci95_low_delta_K_raw": low,
                        "ci95_high_delta_K_raw": high,
                        "mean_beta_delta_I_AB": float(config["beta"] * delta_i.mean()),
                        "mean_negative_delta_chi_BE": float(-delta_chi.mean()),
                    }
                )
            paired[comparison] = {
                "positive_CI_points": significant_positive,
                "negative_CI_points": significant_negative,
                "points": int(raw["parameter_value"].nunique()),
            }

        uniform = summary[summary["scheme"] == "Uniform QAM"].sort_values("parameter_value")
        sensitivities: dict[str, dict[str, float]] = {}
        for scheme_name, group in summary.groupby("scheme", sort=False):
            value, elasticity = interpolated_value_and_elasticity(
                group, BASELINES[key]
            )
            sensitivities[str(scheme_name)] = {
                "K_raw_at_baseline": value,
                "baseline_elasticity": elasticity,
                "full_range_over_abs_baseline": float(
                    (group["mean_K_raw"].max() - group["mean_K_raw"].min())
                    / abs(value)
                )
                if abs(value) > 1e-12
                else math.nan,
            }
            all_sensitivity_rows.append(
                {
                    "sweep": key,
                    "scheme": str(scheme_name),
                    "baseline_parameter_value": BASELINES[key],
                    **sensitivities[str(scheme_name)],
                }
            )

        for scheme_name, scheme_rows in raw.groupby("scheme", sort=False):
            for repetition, repetition_rows in scheme_rows.groupby("repetition"):
                repetition_rows = repetition_rows.sort_values("parameter_value")
                x = repetition_rows["parameter_value"].to_numpy(float)
                y = repetition_rows["K_raw"].to_numpy(float)
                for index in range(len(x) - 1):
                    if y[index] * y[index + 1] < 0.0:
                        all_threshold_rows.append(
                            {
                                "sweep": key,
                                "scheme": str(scheme_name),
                                "repetition": int(repetition),
                                "root_parameter_value": interpolate_root(
                                    x[index], x[index + 1], y[index], y[index + 1]
                                ),
                                "bracket_low": float(x[index]),
                                "bracket_high": float(x[index + 1]),
                            }
                        )

        baseline_uniform, _ = interpolated_value_and_elasticity(
            uniform, BASELINES[key]
        )
        findings[key] = {
            "source": str(path.relative_to(ROOT)),
            "baseline": BASELINES[key],
            "range": [
                float(raw["parameter_value"].min()),
                float(raw["parameter_value"].max()),
            ],
            "ranks": ranks,
            "crossings_mean_K_raw_linear_interpolation": all_crossings,
            "zero_thresholds_mean_K_raw_linear_interpolation": zero_thresholds(summary),
            "local_extrema_mean_K_raw": local_extrema(summary),
            "paired_student_t_95_percent": paired,
            "sensitivity": sensitivities,
            "uniform_near_zero_warning": abs(baseline_uniform) < 1e-6,
        }

    point_summary = pd.concat(all_point_summaries, ignore_index=True)
    point_summary.to_csv(OUT_DIR / "point_summary_with_channel.csv", index=False)
    pd.DataFrame(all_channel_rows).to_csv(
        OUT_DIR / "reconstructed_channel_samples.csv", index=False
    )
    pd.DataFrame(all_delta_rows).to_csv(
        OUT_DIR / "paired_delta_decomposition.csv", index=False
    )
    pd.DataFrame(all_threshold_rows).to_csv(
        OUT_DIR / "threshold_roots_by_repetition.csv", index=False
    )
    pd.DataFrame(all_sensitivity_rows).to_csv(
        OUT_DIR / "sensitivity_summary.csv", index=False
    )

    bundle = sweep.load_scheme_checkpoints(config)
    probe_t = torch.tensor(
        [1e-6, 1e-4, 1e-2, 0.1, 0.5],
        dtype=sweep.core.REAL_DTYPE,
        device=bundle.device,
    )
    with torch.inference_mode():
        outputs = sweep.build_scheme_outputs(
            bundle, probe_t, float(config["baseline_excess_noise_snu"])
        )
    shape_rows: list[dict[str, float | str]] = []
    for scheme_name, output in outputs.items():
        probabilities = output.probabilities
        unit = output.unit_constellation
        entropy = -torch.sum(
            probabilities * torch.log2(probabilities.clamp_min(1e-300)), dim=-1
        )
        distances = torch.cdist(torch.view_as_real(unit), torch.view_as_real(unit))
        diagonal = torch.eye(
            sweep.core.SYMBOL_COUNT, dtype=torch.bool, device=bundle.device
        ).unsqueeze(0)
        minimum_distance = distances.masked_fill(diagonal, math.inf).amin(dim=(-2, -1))
        metadata = bundle.checkpoint_metadata.get(scheme_name, {})
        shape_rows.append(
            {
                "scheme": scheme_name,
                "entropy_bits": float(entropy.mean()),
                "peak_energy": float(unit.abs().square().amax(dim=-1).mean()),
                "minimum_pairwise_distance": float(minimum_distance.mean()),
                "minimum_probability": float(probabilities.min()),
                "maximum_probability": float(probabilities.max()),
                "maximum_PMF_change_over_probe_T": float(
                    (probabilities - probabilities[:1]).abs().max()
                ),
                "maximum_geometry_change_over_probe_T": float(
                    (unit - unit[:1]).abs().max()
                ),
                "checkpoint_phase": str(metadata.get("phase", "fixed baseline")),
                "checkpoint_epoch": float(metadata.get("epoch", math.nan)),
            }
        )
    pd.DataFrame(shape_rows).to_csv(OUT_DIR / "scheme_shape_statistics.csv", index=False)
    (OUT_DIR / "findings.json").write_text(
        json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote audit artifacts to {OUT_DIR}")


if __name__ == "__main__":
    main()
