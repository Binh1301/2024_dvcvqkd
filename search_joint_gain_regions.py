"""Targeted search for Joint PS+GS gain near the CV-QKD key threshold.

This script is intentionally a discovery/confirmation pipeline:

* select a domain-specific MB-global parameter on validation samples;
* scan a coarse T--epsilon grid and refine around K_MB ~= 0;
* choose candidates without looking at final-test noise;
* confirm candidates with 10 paired repetitions at ncut=150;
* compare with MB-fixed, MB-global-opt, and a separately selected
  MB-oracle-per-state parameter;
* probe synthetic fading distributions with matched mean transmittance.

The supplied learned checkpoints represent one training seed. Therefore the
script can reject an outperform claim, but it cannot establish training-seed
stability even when an evaluation-seed confidence interval is positive.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from scipy.stats import t as student_t

import audit_learned_vs_mb as audit
import uav_hap_joint_ps_gs as core


SCHEMES = ("MB-fixed", "MB-global-opt", "PS", "GS", "PS+GS")
LEARNED = ("PS", "GS", "PS+GS")


@dataclass(frozen=True)
class Point:
    T: float
    epsilon: float

    @property
    def snr_db(self) -> float:
        snr = self.T * 2.0 / (1.0 + self.T * self.epsilon / 2.0)
        return float(10.0 * np.log10(max(snr, 1e-300)))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_config(path: Path, quick: bool, output_override: Path | None) -> dict[str, Any]:
    config_path = path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    root = config_path.parent
    config["_config_path"] = str(config_path)
    config["audit_config"] = str((root / config["audit_config"]).resolve())
    output = (root / config["output_directory"]).resolve()
    if output_override is not None:
        output = output_override.resolve()
    config["output_directory"] = str(output)
    config["quick"] = bool(quick)
    if quick:
        config["coarse"]["T_points"] = 7
        config["coarse"]["epsilon_points"] = 5
        config["coarse"]["repetitions"] = 1
        config["coarse"]["awgn_samples"] = 4
        config["coarse"]["ncut"] = 24
        config["fine"]["epsilon_points"] = 5
        config["fine"]["T_points_per_epsilon"] = 3
        config["fine"]["repetitions"] = 1
        config["fine"]["awgn_samples"] = 4
        config["fine"]["ncut"] = 24
        config["confirmation"]["repetitions"] = 2
        config["confirmation"]["awgn_samples"] = 4
        config["confirmation"]["ncut"] = 24
        config["fading"]["repetitions"] = 2
        config["fading"]["states_per_repetition"] = 4
        config["fading"]["awgn_samples"] = 4
        config["fading"]["ncut"] = 24
        config["domain_mb_validation"]["representative_points"] = 8
        config["domain_mb_validation"]["awgn_samples"] = 4
        config["domain_mb_validation"]["ncut"] = 24
        config["domain_mb_validation"]["finalists"] = 2
        config["oracle"]["awgn_samples"] = 4
        config["oracle"]["ncut"] = 24
        config["candidate_cases_each"] = 1
    return config


def t_interval(values: Sequence[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    if array.size < 2:
        return mean, mean
    critical = float(student_t.ppf(0.975, df=array.size - 1))
    half = critical * float(array.std(ddof=1)) / math.sqrt(array.size)
    return mean - half, mean + half


def standard_noise(
    count: int,
    samples: int,
    seed: int,
    device: torch.device,
) -> torch.Tensor:
    return core.make_standard_complex_noise(
        count,
        core.SYMBOL_COUNT,
        samples,
        core.tensor_generator(seed, device),
        device,
    )


def samples_for_points(
    points: Sequence[Point],
    awgn_samples: int,
    noise_seed: int,
    device: torch.device,
) -> audit.Samples:
    transmittance = torch.tensor(
        [point.T for point in points], dtype=core.REAL_DTYPE, device=device
    )
    epsilon = torch.tensor(
        [point.epsilon for point in points],
        dtype=core.REAL_DTYPE,
        device=device,
    )
    noise = standard_noise(len(points), awgn_samples, noise_seed, device)
    return audit.Samples(
        transmittance,
        epsilon,
        noise,
        audit.tensor_hash(transmittance),
        audit.tensor_hash(noise),
    )


def per_state_rows(
    result: core.SchemeEvaluation,
    points: Sequence[Point],
    scheme: str,
    repetition: int,
    noise_seed: int,
    stage: str,
    ncut: int,
    awgn_samples: int,
) -> list[dict[str, Any]]:
    i_ab = result.i_ab.detach().cpu().numpy()
    chi = result.security.chi_be.detach().cpu().numpy()
    raw = result.raw_skr.detach().cpu().numpy()
    entropy = result.entropy.detach().cpu().numpy()
    rows: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        rows.append(
            {
                "stage": stage,
                "point_index": index,
                "T": point.T,
                "epsilon": point.epsilon,
                "SNR_dB": point.snr_db,
                "scheme": scheme,
                "repetition": repetition,
                "I_AB": float(i_ab[index]),
                "chi_BE": float(chi[index]),
                "beta_I_AB": float(i_ab[index] * 0.95),
                "K_raw": float(raw[index]),
                "K_positive": float(max(raw[index], 0.0)),
                "entropy": float(entropy[index]),
                "outage": int(raw[index] <= 0.0),
                "noise_seed": noise_seed,
                "ncut": ncut,
                "awgn_samples": awgn_samples,
            }
        )
    return rows


def evaluate_points(
    bundle: audit.ModelBundle,
    points: Sequence[Point],
    fixed_nu: float,
    global_nu: float,
    repetitions: int,
    awgn_samples: int,
    ncut: int,
    seed_start: int,
    stage: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for repetition in range(repetitions):
        noise_seed = seed_start + repetition
        samples = samples_for_points(points, awgn_samples, noise_seed, bundle.device)
        with torch.inference_mode():
            outputs = audit.all_outputs(bundle, samples, fixed_nu, global_nu)
            for name in SCHEMES:
                result = audit.evaluate(
                    name, outputs[name], samples, bundle, ncut, awgn_samples
                )
                rows.extend(
                    per_state_rows(
                        result,
                        points,
                        name,
                        repetition,
                        noise_seed,
                        stage,
                        ncut,
                        awgn_samples,
                    )
                )
        print(f"[{stage}] repetition {repetition + 1}/{repetitions}", flush=True)
    return rows


def aggregate_grid(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[float, float, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        key = (float(row["T"]), float(row["epsilon"]), str(row["scheme"]))
        groups.setdefault(key, []).append(row)
    summary: list[dict[str, Any]] = []
    for (t_value, epsilon, scheme), group in groups.items():
        values = {
            field: np.asarray([float(row[field]) for row in group])
            for field in ("I_AB", "chi_BE", "K_raw", "K_positive", "entropy", "outage")
        }
        low, high = t_interval(values["K_raw"])
        summary.append(
            {
                "T": t_value,
                "epsilon": epsilon,
                "SNR_dB": float(group[0]["SNR_dB"]),
                "scheme": scheme,
                "mean_I_AB": float(values["I_AB"].mean()),
                "mean_chi_BE": float(values["chi_BE"].mean()),
                "mean_K_raw": float(values["K_raw"].mean()),
                "std_K_raw": float(values["K_raw"].std(ddof=1))
                if values["K_raw"].size > 1
                else 0.0,
                "ci95_low": low,
                "ci95_high": high,
                "mean_K_positive": float(values["K_positive"].mean()),
                "mean_entropy": float(values["entropy"].mean()),
                "outage_probability": float(values["outage"].mean()),
                "repetitions": len(group),
            }
        )
    return sorted(
        summary,
        key=lambda row: (float(row["epsilon"]), float(row["T"]), str(row["scheme"])),
    )


def coarse_points(config: Mapping[str, Any]) -> list[Point]:
    settings = config["coarse"]
    t_values = np.logspace(
        np.log10(float(settings["T_min"])),
        np.log10(float(settings["T_max"])),
        int(settings["T_points"]),
    )
    epsilon_values = np.linspace(
        float(settings["epsilon_min"]),
        float(settings["epsilon_max"]),
        int(settings["epsilon_points"]),
    )
    return [Point(float(t), float(epsilon)) for epsilon in epsilon_values for t in t_values]


def representative_subset(points: Sequence[Point], count: int) -> list[Point]:
    if count >= len(points):
        return list(points)
    indices = np.linspace(0, len(points) - 1, count).round().astype(int)
    return [points[index] for index in sorted(set(indices.tolist()))]


def arbitrary_mb_result(
    bundle: audit.ModelBundle,
    samples: audit.Samples,
    nu: float,
    ncut: int,
    awgn_samples: int,
) -> core.SchemeEvaluation:
    output = audit.fixed_probability_output(
        audit.mb_probabilities(nu, bundle.device),
        samples.transmittance,
        bundle.base_qam,
        bundle.args.va,
    )
    return audit.evaluate(
        f"MB(nu={nu:g})", output, samples, bundle, ncut, awgn_samples
    )


def select_domain_global_nu(
    bundle: audit.ModelBundle,
    config: Mapping[str, Any],
    points: Sequence[Point],
    output_dir: Path,
) -> tuple[float, list[dict[str, Any]]]:
    settings = config["domain_mb_validation"]
    selected = representative_subset(points, int(settings["representative_points"]))
    samples = samples_for_points(
        selected,
        int(settings["awgn_samples"]),
        int(config["seeds"]["mb_domain_validation"]),
        bundle.device,
    )
    candidates = [float(value) for value in config["nu_grid"]]
    rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        for nu in candidates:
            result = arbitrary_mb_result(
                bundle,
                samples,
                nu,
                int(settings["ncut"]),
                int(settings["awgn_samples"]),
            )
            metrics = audit.evaluation_metrics(result)
            rows.append(
                {
                    "pass": "coarse",
                    "nu": nu,
                    **metrics,
                    "points": len(selected),
                    "ncut": int(settings["ncut"]),
                    "awgn_samples": int(settings["awgn_samples"]),
                }
            )
    finite = [row for row in rows if bool(row["finite"])]
    finalists = sorted(
        finite, key=lambda row: float(row["K_raw_mean"]), reverse=True
    )[: int(settings["finalists"])]

    final_settings = config["domain_mb_final"]
    final_points = representative_subset(points, int(final_settings["representative_points"]))
    final_samples = samples_for_points(
        final_points,
        int(final_settings["awgn_samples"]),
        int(config["seeds"]["mb_domain_final"]),
        bundle.device,
    )
    with torch.inference_mode():
        for finalist in finalists:
            nu = float(finalist["nu"])
            result = arbitrary_mb_result(
                bundle,
                final_samples,
                nu,
                int(final_settings["ncut"]),
                int(final_settings["awgn_samples"]),
            )
            rows.append(
                {
                    "pass": "full-cutoff-finalist",
                    "nu": nu,
                    **audit.evaluation_metrics(result),
                    "points": len(final_points),
                    "ncut": int(final_settings["ncut"]),
                    "awgn_samples": int(final_settings["awgn_samples"]),
                }
            )
    final_rows = [
        row
        for row in rows
        if row["pass"] == "full-cutoff-finalist" and bool(row["finite"])
    ]
    winner = max(final_rows, key=lambda row: float(row["K_raw_mean"]))
    write_csv(output_dir / "domain_mb_global_selection.csv", rows)
    return float(winner["nu"]), rows


def lookup_summary(
    summary: Sequence[Mapping[str, Any]],
) -> dict[tuple[float, float, str], Mapping[str, Any]]:
    return {
        (float(row["T"]), float(row["epsilon"]), str(row["scheme"])): row
        for row in summary
    }


def build_fine_points(
    coarse_summary: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[Point]:
    settings = config["fine"]
    lookup = lookup_summary(coarse_summary)
    t_values = sorted({float(row["T"]) for row in coarse_summary})
    coarse_epsilon = np.asarray(
        sorted({float(row["epsilon"]) for row in coarse_summary})
    )
    dense_epsilon = np.linspace(
        float(coarse_epsilon.min()),
        float(coarse_epsilon.max()),
        int(settings["epsilon_points"]),
    )
    points: set[tuple[float, float]] = set()
    for epsilon in dense_epsilon:
        nearest_epsilon = float(
            coarse_epsilon[np.argmin(np.abs(coarse_epsilon - epsilon))]
        )
        values = np.asarray(
            [
                float(lookup[(t_value, nearest_epsilon, "MB-global-opt")]["mean_K_raw"])
                for t_value in t_values
            ]
        )
        center_index = int(np.argmin(np.abs(values)))
        center_t = t_values[center_index]
        lower = t_values[max(center_index - 1, 0)]
        upper = t_values[min(center_index + 1, len(t_values) - 1)]
        local = np.logspace(
            np.log10(lower),
            np.log10(upper),
            int(settings["T_points_per_epsilon"]),
        )
        for t_value in local:
            points.add((round(float(t_value), 15), round(float(epsilon), 15)))
    delta = float(settings["near_threshold_delta"])
    for row in coarse_summary:
        if (
            row["scheme"] == "MB-global-opt"
            and abs(float(row["mean_K_raw"])) <= delta
        ):
            points.add((round(float(row["T"]), 15), round(float(row["epsilon"]), 15)))
    return [Point(t, epsilon) for epsilon, t in sorted((e, t) for t, e in points)]


def paired_delta_summary(
    raw_rows: Sequence[Mapping[str, Any]],
    baseline: str = "MB-global-opt",
) -> list[dict[str, Any]]:
    groups: dict[tuple[float, float, int], dict[str, Mapping[str, Any]]] = {}
    for row in raw_rows:
        key = (float(row["T"]), float(row["epsilon"]), int(row["repetition"]))
        groups.setdefault(key, {})[str(row["scheme"])] = row
    point_values: dict[tuple[float, float, str], list[dict[str, float]]] = {}
    for (t_value, epsilon, _), schemes in groups.items():
        for learned in LEARNED:
            a = schemes[learned]
            b = schemes[baseline]
            point_values.setdefault((t_value, epsilon, learned), []).append(
                {
                    "delta_K": float(a["K_raw"]) - float(b["K_raw"]),
                    "delta_I": float(a["I_AB"]) - float(b["I_AB"]),
                    "delta_chi": float(a["chi_BE"]) - float(b["chi_BE"]),
                    "delta_outage": float(b["outage"]) - float(a["outage"]),
                }
            )
    rows: list[dict[str, Any]] = []
    for (t_value, epsilon, learned), values in point_values.items():
        deltas = [value["delta_K"] for value in values]
        low, high = t_interval(deltas)
        delta_i = float(np.mean([value["delta_I"] for value in values]))
        delta_chi = float(np.mean([value["delta_chi"] for value in values]))
        mean_delta = float(np.mean(deltas))
        rows.append(
            {
                "T": t_value,
                "epsilon": epsilon,
                "SNR_dB": Point(t_value, epsilon).snr_db,
                "scheme": learned,
                "baseline": baseline,
                "mean_delta_K": mean_delta,
                "std_delta_K": float(np.std(deltas, ddof=1))
                if len(deltas) > 1
                else 0.0,
                "ci95_low": low,
                "ci95_high": high,
                "P_delta_gt_0": float(np.mean(np.asarray(deltas) > 0.0)),
                "mean_delta_I_AB": delta_i,
                "mean_delta_chi_BE": delta_chi,
                "mean_delta_outage": float(
                    np.mean([value["delta_outage"] for value in values])
                ),
                "gain_source": audit.gain_source(
                    delta_i, delta_chi, mean_delta
                ),
                "repetitions": len(deltas),
            }
        )
    return sorted(rows, key=lambda row: float(row["mean_delta_K"]), reverse=True)


def select_candidates(
    fine_summary: Sequence[Mapping[str, Any]],
    delta_rows: Sequence[Mapping[str, Any]],
    cases_each: int,
) -> list[dict[str, Any]]:
    lookup = lookup_summary(fine_summary)
    joint_rows = [row for row in delta_rows if row["scheme"] == "PS+GS"]
    enriched: list[dict[str, Any]] = []
    for row in joint_rows:
        key_mb = (float(row["T"]), float(row["epsilon"]), "MB-global-opt")
        key_joint = (float(row["T"]), float(row["epsilon"]), "PS+GS")
        mb = lookup[key_mb]
        joint = lookup[key_joint]
        enriched.append(
            {
                **dict(row),
                "K_MB_discovery": float(mb["mean_K_raw"]),
                "K_joint_discovery": float(joint["mean_K_raw"]),
                "key_extension_discovery": bool(
                    float(mb["mean_K_raw"]) <= 0.0
                    and float(joint["mean_K_raw"]) > 0.0
                ),
            }
        )
    priority = sorted(
        enriched,
        key=lambda row: (
            bool(row["key_extension_discovery"]),
            float(row["mean_delta_K"]),
        ),
        reverse=True,
    )
    failures = sorted(enriched, key=lambda row: float(row["mean_delta_K"]))
    selected: list[dict[str, Any]] = []
    used: set[tuple[float, float]] = set()
    for case_type, candidates in (("best", priority), ("failure", failures)):
        count = 0
        for row in candidates:
            key = (float(row["T"]), float(row["epsilon"]))
            if key in used:
                continue
            selected.append(
                {
                    "case_id": len(selected),
                    "case_type": case_type,
                    **dict(row),
                }
            )
            used.add(key)
            count += 1
            if count >= cases_each:
                break
    return selected


def add_overall_best_candidates(
    candidates: Sequence[Mapping[str, Any]],
    coarse_summary: Sequence[Mapping[str, Any]],
    coarse_deltas: Sequence[Mapping[str, Any]],
    cases_each: int,
) -> list[dict[str, Any]]:
    """Add the largest discovery deltas over the full SNR domain."""
    lookup = lookup_summary(coarse_summary)
    joint = [
        row for row in coarse_deltas if str(row["scheme"]) == "PS+GS"
    ]
    joint.sort(key=lambda row: float(row["mean_delta_K"]), reverse=True)
    overall: list[dict[str, Any]] = []
    used: set[tuple[float, float]] = set()
    for row in joint:
        key = (float(row["T"]), float(row["epsilon"]))
        if key in used:
            continue
        mb = lookup[(key[0], key[1], "MB-global-opt")]
        learned = lookup[(key[0], key[1], "PS+GS")]
        overall.append(
            {
                "case_type": "best_overall",
                **dict(row),
                "K_MB_discovery": float(mb["mean_K_raw"]),
                "K_joint_discovery": float(learned["mean_K_raw"]),
                "key_extension_discovery": bool(
                    float(mb["mean_K_raw"]) <= 0.0
                    and float(learned["mean_K_raw"]) > 0.0
                ),
            }
        )
        used.add(key)
        if len(overall) >= cases_each:
            break

    combined = overall + [
        {
            **dict(row),
            "case_type": (
                "near_threshold"
                if str(row["case_type"]) == "best"
                else str(row["case_type"])
            ),
        }
        for row in candidates
        if (float(row["T"]), float(row["epsilon"])) not in used
    ]
    return [
        {"case_id": index, **{k: v for k, v in row.items() if k != "case_id"}}
        for index, row in enumerate(combined)
    ]


def select_oracle_nu(
    bundle: audit.ModelBundle,
    config: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> tuple[dict[int, float], list[dict[str, Any]]]:
    settings = config["oracle"]
    rows: list[dict[str, Any]] = []
    selected: dict[int, float] = {}
    for candidate in candidates:
        case_id = int(candidate["case_id"])
        point = Point(float(candidate["T"]), float(candidate["epsilon"]))
        samples = samples_for_points(
            [point],
            int(settings["awgn_samples"]),
            int(config["seeds"]["oracle_start"]) + case_id,
            bundle.device,
        )
        nu_rows, _ = audit.evaluate_nu_grid(
            bundle,
            samples,
            config["nu_grid"],
            int(settings["ncut"]),
            int(settings["awgn_samples"]),
        )
        finite = [row for row in nu_rows if bool(row["finite"])]
        best = max(finite, key=lambda row: float(row["K_raw_mean"]))
        selected[case_id] = float(best["nu"])
        for row in nu_rows:
            rows.append({"case_id": case_id, **row})
        print(f"[oracle] case {case_id}: nu*={selected[case_id]:g}", flush=True)
    write_csv(output_dir / "candidate_oracle_nu_validation.csv", rows)
    return selected, rows


def variable_mb_output(
    bundle: audit.ModelBundle,
    transmittance: torch.Tensor,
    nu_values: Sequence[float],
) -> core.ModelOutput:
    probabilities = torch.stack(
        [audit.mb_probabilities(float(nu), bundle.device) for nu in nu_values],
        dim=0,
    )
    raw = core.complex_from_xy(bundle.base_qam)
    unit = core.normalize_unit_energy_batch(probabilities, raw)
    constellation = unit * math.sqrt(float(bundle.args.va) / 2.0)
    return core.ModelOutput(
        probabilities=probabilities,
        probabilities_safe=probabilities.clamp_min(1e-12),
        unit_constellation=unit,
        constellation=constellation,
        logits=torch.log(probabilities.clamp_min(1e-12)),
        features=torch.empty(
            (transmittance.numel(), 0),
            dtype=core.REAL_DTYPE,
            device=bundle.device,
        ),
        gumbel_symbols=None,
    )


def confirm_candidates(
    bundle: audit.ModelBundle,
    config: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    fixed_nu: float,
    global_nu: float,
    oracle_nu: Mapping[int, float],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    settings = config["confirmation"]
    points = [
        Point(float(candidate["T"]), float(candidate["epsilon"]))
        for candidate in candidates
    ]
    rows: list[dict[str, Any]] = []
    for repetition in range(int(settings["repetitions"])):
        seed = int(config["seeds"]["confirmation_start"]) + repetition
        samples = samples_for_points(
            points, int(settings["awgn_samples"]), seed, bundle.device
        )
        with torch.inference_mode():
            outputs = audit.all_outputs(bundle, samples, fixed_nu, global_nu)
            outputs["MB-oracle-per-state"] = variable_mb_output(
                bundle,
                samples.transmittance,
                [oracle_nu[int(candidate["case_id"])] for candidate in candidates],
            )
            for name in (*SCHEMES, "MB-oracle-per-state"):
                result = audit.evaluate(
                    name,
                    outputs[name],
                    samples,
                    bundle,
                    int(settings["ncut"]),
                    int(settings["awgn_samples"]),
                )
                local = per_state_rows(
                    result,
                    points,
                    name,
                    repetition,
                    seed,
                    "confirmation",
                    int(settings["ncut"]),
                    int(settings["awgn_samples"]),
                )
                for row, candidate in zip(local, candidates):
                    row["case_id"] = int(candidate["case_id"])
                    row["case_type"] = candidate["case_type"]
                    row["oracle_nu"] = oracle_nu[int(candidate["case_id"])]
                    rows.append(row)
        print(
            f"[confirmation] repetition {repetition + 1}/{settings['repetitions']}",
            flush=True,
        )
    write_csv(output_dir / "candidate_confirmation_runs.csv", rows)

    grouped: dict[int, dict[int, dict[str, Mapping[str, Any]]]] = {}
    for row in rows:
        grouped.setdefault(int(row["case_id"]), {}).setdefault(
            int(row["repetition"]), {}
        )[str(row["scheme"])] = row
    summary: list[dict[str, Any]] = []
    for candidate in candidates:
        case_id = int(candidate["case_id"])
        repetitions = grouped[case_id]
        for baseline in ("MB-fixed", "MB-global-opt", "MB-oracle-per-state"):
            delta_k: list[float] = []
            delta_i: list[float] = []
            delta_chi: list[float] = []
            mb_values: list[float] = []
            joint_values: list[float] = []
            key_extensions: list[bool] = []
            for repetition in sorted(repetitions):
                joint = repetitions[repetition]["PS+GS"]
                mb = repetitions[repetition][baseline]
                delta_k.append(float(joint["K_raw"]) - float(mb["K_raw"]))
                delta_i.append(float(joint["I_AB"]) - float(mb["I_AB"]))
                delta_chi.append(float(joint["chi_BE"]) - float(mb["chi_BE"]))
                mb_values.append(float(mb["K_raw"]))
                joint_values.append(float(joint["K_raw"]))
                key_extensions.append(
                    float(mb["K_raw"]) <= 0.0 < float(joint["K_raw"])
                )
            low, high = t_interval(delta_k)
            mean_delta = float(np.mean(delta_k))
            mean_i = float(np.mean(delta_i))
            mean_chi = float(np.mean(delta_chi))
            summary.append(
                {
                    "case_id": case_id,
                    "case_type": candidate["case_type"],
                    "T": candidate["T"],
                    "epsilon": candidate["epsilon"],
                    "SNR_dB": candidate["SNR_dB"],
                    "baseline": baseline,
                    "oracle_nu": oracle_nu[case_id],
                    "mean_K_MB": float(np.mean(mb_values)),
                    "mean_K_joint": float(np.mean(joint_values)),
                    "mean_delta_K": mean_delta,
                    "std_delta_K": float(np.std(delta_k, ddof=1)),
                    "ci95_low": low,
                    "ci95_high": high,
                    "P_delta_gt_0": float(np.mean(np.asarray(delta_k) > 0.0)),
                    "key_extension_fraction": float(np.mean(key_extensions)),
                    "mean_delta_I_AB": mean_i,
                    "mean_delta_chi_BE": mean_chi,
                    "gain_source": audit.gain_source(mean_i, mean_chi, mean_delta),
                    "evaluation_seed_significant": bool(
                        low > float(config["minimum_meaningful_gain"])
                    ),
                    "training_seed_count": 1,
                    "outperform_allowed": False,
                }
            )
    write_csv(output_dir / "candidate_confirmation_summary.csv", summary)
    return rows, summary


def matched_mean_fading(
    kind: str,
    mean_t: float,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    mean_t = float(np.clip(mean_t, 1e-10, 0.95))
    if kind == "deterministic":
        values = np.full(count, mean_t)
    elif kind.startswith("beta_"):
        concentration = {
            "beta_low_variance": 500.0,
            "beta_medium_variance": 50.0,
            "beta_high_variance": 5.0,
        }[kind]
        alpha = mean_t * concentration
        beta = (1.0 - mean_t) * concentration
        values = rng.beta(alpha, beta, size=count)
    elif kind == "deep_fade_mixture":
        probability = 0.25
        low = 0.02 * mean_t
        high = (mean_t - probability * low) / (1.0 - probability)
        mask = rng.random(count) < probability
        values = np.where(mask, low, high)
    elif kind == "lognormal_heavy_tail":
        sigma = 1.2
        values = rng.lognormal(
            mean=math.log(mean_t) - 0.5 * sigma * sigma,
            sigma=sigma,
            size=count,
        )
        values = np.clip(values, 1e-12, 1.0)
        values *= mean_t / max(float(values.mean()), 1e-15)
    else:
        raise ValueError(kind)
    return np.clip(values, 1e-12, 1.0)


def fading_search(
    bundle: audit.ModelBundle,
    config: Mapping[str, Any],
    mean_point: Point,
    fixed_nu: float,
    global_nu: float,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    settings = config["fading"]
    kinds = (
        "deterministic",
        "beta_low_variance",
        "beta_medium_variance",
        "beta_high_variance",
        "deep_fade_mixture",
        "lognormal_heavy_tail",
    )
    rows: list[dict[str, Any]] = []
    for repetition in range(int(settings["repetitions"])):
        base_seed = int(config["seeds"]["fading_start"]) + repetition
        for kind_index, kind in enumerate(kinds):
            rng = np.random.default_rng(base_seed + kind_index * 10_000)
            values = matched_mean_fading(
                kind,
                mean_point.T,
                int(settings["states_per_repetition"]),
                rng,
            )
            t_tensor = torch.tensor(
                values, dtype=core.REAL_DTYPE, device=bundle.device
            )
            epsilon = torch.full_like(t_tensor, mean_point.epsilon)
            noise_seed = base_seed + kind_index * 10_000 + 1
            noise = standard_noise(
                values.size,
                int(settings["awgn_samples"]),
                noise_seed,
                bundle.device,
            )
            samples = audit.Samples(
                t_tensor,
                epsilon,
                noise,
                audit.tensor_hash(t_tensor),
                audit.tensor_hash(noise),
            )
            with torch.inference_mode():
                outputs = audit.all_outputs(bundle, samples, fixed_nu, global_nu)
                for name in SCHEMES:
                    result = audit.evaluate(
                        name,
                        outputs[name],
                        samples,
                        bundle,
                        int(settings["ncut"]),
                        int(settings["awgn_samples"]),
                    )
                    metrics = audit.evaluation_metrics(result)
                    rows.append(
                        {
                            "fading_distribution": kind,
                            "repetition": repetition,
                            "scheme": name,
                            "target_mean_T": mean_point.T,
                            "sample_mean_T": float(values.mean()),
                            "sample_variance_T": float(values.var(ddof=1))
                            if values.size > 1
                            else 0.0,
                            "deep_fade_probability_T_lt_0.1mean": float(
                                np.mean(values < 0.1 * mean_point.T)
                            ),
                            "epsilon": mean_point.epsilon,
                            **metrics,
                            "channel_seed": base_seed + kind_index * 10_000,
                            "awgn_seed": noise_seed,
                        }
                    )
        print(
            f"[fading] repetition {repetition + 1}/{settings['repetitions']}",
            flush=True,
        )
    write_csv(output_dir / "fading_distribution_runs.csv", rows)

    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (str(row["fading_distribution"]), str(row["scheme"])), []
        ).append(row)
    summary: list[dict[str, Any]] = []
    for (kind, scheme), group in grouped.items():
        summary.append(
            {
                "fading_distribution": kind,
                "scheme": scheme,
                "mean_variance_T": float(
                    np.mean([float(row["sample_variance_T"]) for row in group])
                ),
                "mean_deep_fade_probability": float(
                    np.mean(
                        [
                            float(row["deep_fade_probability_T_lt_0.1mean"])
                            for row in group
                        ]
                    )
                ),
                "mean_K": float(
                    np.mean([float(row["K_raw_mean"]) for row in group])
                ),
                "mean_median_K": float(
                    np.mean([float(row["K_raw_median"]) for row in group])
                ),
                "mean_K_p05": float(
                    np.mean([float(row["K_raw_p05"]) for row in group])
                ),
                "mean_outage": float(
                    np.mean([float(row["outage_probability"]) for row in group])
                ),
            }
        )
    write_csv(output_dir / "fading_distribution_summary.csv", summary)

    comparisons: list[dict[str, Any]] = []
    for kind in kinds:
        by_rep: dict[int, dict[str, Mapping[str, Any]]] = {}
        for row in rows:
            if row["fading_distribution"] == kind:
                by_rep.setdefault(int(row["repetition"]), {})[
                    str(row["scheme"])
                ] = row
        deltas = [
            float(schemes["PS+GS"]["K_raw_mean"])
            - float(schemes["MB-global-opt"]["K_raw_mean"])
            for schemes in by_rep.values()
        ]
        outage_deltas = [
            float(schemes["MB-global-opt"]["outage_probability"])
            - float(schemes["PS+GS"]["outage_probability"])
            for schemes in by_rep.values()
        ]
        low, high = t_interval(deltas)
        comparisons.append(
            {
                "fading_distribution": kind,
                "mean_delta_K_joint_vs_MB_global": float(np.mean(deltas)),
                "ci95_low": low,
                "ci95_high": high,
                "P_delta_gt_0": float(np.mean(np.asarray(deltas) > 0.0)),
                "mean_outage_reduction": float(np.mean(outage_deltas)),
                "evaluation_seed_significant": bool(
                    low > float(config["minimum_meaningful_gain"])
                ),
                "training_seed_count": 1,
                "outperform_allowed": False,
            }
        )
    write_csv(output_dir / "fading_paired_comparisons.csv", comparisons)
    return rows, comparisons


def plot_heatmap(
    summary: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> None:
    lookup = lookup_summary(summary)
    t_values = np.asarray(sorted({float(row["T"]) for row in summary}))
    epsilon_values = np.asarray(sorted({float(row["epsilon"]) for row in summary}))
    mb = np.empty((epsilon_values.size, t_values.size))
    joint = np.empty_like(mb)
    for yi, epsilon in enumerate(epsilon_values):
        for xi, t_value in enumerate(t_values):
            mb[yi, xi] = float(
                lookup[(float(t_value), float(epsilon), "MB-global-opt")][
                    "mean_K_raw"
                ]
            )
            joint[yi, xi] = float(
                lookup[(float(t_value), float(epsilon), "PS+GS")]["mean_K_raw"]
            )
    delta = joint - mb
    x = np.log10(t_values)
    y = epsilon_values
    figure, axis = plt.subplots(figsize=(7.4, 4.8))
    limit = max(float(np.max(np.abs(delta))), 1e-12)
    image = axis.pcolormesh(
        x, y, delta, shading="nearest", cmap="RdBu_r", vmin=-limit, vmax=limit
    )
    if float(mb.min()) <= 0.0 <= float(mb.max()):
        axis.contour(x, y, mb, levels=[0.0], colors="black", linewidths=1.5)
    if float(joint.min()) <= 0.0 <= float(joint.max()):
        axis.contour(
            x,
            y,
            joint,
            levels=[0.0],
            colors="#2CA02C",
            linewidths=1.5,
            linestyles="--",
        )
    figure.colorbar(
        image, ax=axis, label=r"$K_{\rm Joint}-K_{\rm MB-global-opt}$"
    )
    axis.set_xlabel(r"$\log_{10}T$")
    axis.set_ylabel(r"Excess noise $\epsilon$ [SNU]")
    axis.set_title("Near-threshold Joint gain search (discovery grid)")
    axis.text(
        0.02,
        0.98,
        "black: MB K=0; green dashed: Joint K=0",
        transform=axis.transAxes,
        va="top",
        fontsize=8,
    )
    figure.tight_layout()
    figure.savefig(output_dir / "delta_K_T_epsilon_heatmap.png", dpi=240)
    plt.close(figure)


def snr_band(snr_db: float) -> str:
    if snr_db < -35:
        return "very low"
    if snr_db < -25:
        return "low"
    if snr_db < -15:
        return "medium"
    if snr_db < -10:
        return "high"
    return "saturation/highest"


def plot_snr(
    summary: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in summary
        if row["scheme"] in {"MB-global-opt", "PS+GS"}
    ]
    figure, axes = plt.subplots(2, 1, figsize=(7.2, 7.0), sharex=True)
    epsilon_values = sorted({float(row["epsilon"]) for row in rows})
    chosen = [
        epsilon_values[0],
        epsilon_values[len(epsilon_values) // 2],
        epsilon_values[-1],
    ]
    band_rows: list[dict[str, Any]] = []
    for epsilon in chosen:
        mb = sorted(
            (
                row
                for row in rows
                if float(row["epsilon"]) == epsilon
                and row["scheme"] == "MB-global-opt"
            ),
            key=lambda row: float(row["SNR_dB"]),
        )
        joint = sorted(
            (
                row
                for row in rows
                if float(row["epsilon"]) == epsilon and row["scheme"] == "PS+GS"
            ),
            key=lambda row: float(row["SNR_dB"]),
        )
        snr = np.asarray([float(row["SNR_dB"]) for row in mb])
        mb_k = np.asarray([float(row["mean_K_raw"]) for row in mb])
        joint_k = np.asarray([float(row["mean_K_raw"]) for row in joint])
        axes[0].plot(snr, mb_k, "--", label=f"MB, eps={epsilon:.3g}")
        axes[0].plot(snr, joint_k, "-", label=f"Joint, eps={epsilon:.3g}")
        axes[1].plot(snr, joint_k - mb_k, "-", label=f"eps={epsilon:.3g}")
    axes[0].axhline(0.0, color="black", linewidth=0.8)
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[0].set_ylabel("Raw SKR [bit/symbol]")
    axes[1].set_ylabel(r"$\Delta K$")
    axes[1].set_xlabel("SNR [dB]")
    axes[0].legend(ncol=2, fontsize=7)
    axes[1].legend(fontsize=8)
    for axis in axes:
        axis.grid(True, alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_dir / "skr_and_delta_vs_snr.png", dpi=240)
    plt.close(figure)

    lookup = lookup_summary(summary)
    for row in summary:
        if row["scheme"] != "PS+GS":
            continue
        key = (float(row["T"]), float(row["epsilon"]), "MB-global-opt")
        band_rows.append(
            {
                "SNR_band": snr_band(float(row["SNR_dB"])),
                "SNR_dB": row["SNR_dB"],
                "T": row["T"],
                "epsilon": row["epsilon"],
                "delta_K": float(row["mean_K_raw"])
                - float(lookup[key]["mean_K_raw"]),
                "K_MB": lookup[key]["mean_K_raw"],
                "K_joint": row["mean_K_raw"],
            }
        )
    write_csv(output_dir / "snr_gain_points.csv", band_rows)
    return band_rows


def diagnostics(
    bundle: audit.ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _, adaptivity = audit.adaptivity_diagnostics(
        bundle, config, global_nu, output_dir
    )
    geometry = audit.geometry_diagnostics(bundle, config, output_dir)
    return adaptivity, geometry


def top_candidate_artifacts(
    bundle: audit.ModelBundle,
    global_nu: float,
    confirmation_runs: Sequence[Mapping[str, Any]],
    confirmation: Sequence[Mapping[str, Any]],
    geometry: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Write metrics and PMF/constellation data for the top three candidates."""
    best_cases = sorted(
        {
            int(row["case_id"])
            for row in confirmation
            if str(row["case_type"]) == "best_overall"
        }
    )[:3]
    geometry_by_scheme = {str(row["scheme"]): row for row in geometry}
    detailed: list[dict[str, Any]] = []
    symbols: list[dict[str, Any]] = []

    for case_id in best_cases:
        case_summary = [
            row for row in confirmation if int(row["case_id"]) == case_id
        ]
        global_summary = next(
            row for row in case_summary if row["baseline"] == "MB-global-opt"
        )
        fixed_summary = next(
            row for row in case_summary if row["baseline"] == "MB-fixed"
        )
        oracle_summary = next(
            row for row in case_summary if row["baseline"] == "MB-oracle-per-state"
        )
        matching_runs = [
            row for row in confirmation_runs if int(row["case_id"]) == case_id
        ]

        def scheme_means(name: str) -> dict[str, float]:
            rows = [row for row in matching_runs if row["scheme"] == name]
            return {
                field: float(np.mean([float(row[field]) for row in rows]))
                for field in (
                    "I_AB",
                    "chi_BE",
                    "K_raw",
                    "K_positive",
                    "entropy",
                    "outage",
                )
            }

        fixed = scheme_means("MB-fixed")
        global_mb = scheme_means("MB-global-opt")
        oracle = scheme_means("MB-oracle-per-state")
        joint = scheme_means("PS+GS")
        joint_geometry = geometry_by_scheme["PS+GS"]
        detailed.append(
            {
                "case_id": case_id,
                "case_type": global_summary["case_type"],
                "T": global_summary["T"],
                "epsilon": global_summary["epsilon"],
                "SNR_dB": global_summary["SNR_dB"],
                "physical_realization": (
                    "direct conditional T; inverse mapping to L/Cn2/visibility/"
                    "W0/aperture is non-unique"
                ),
                "MB_fixed_nu": 0.1,
                "MB_global_nu": global_nu,
                "MB_oracle_nu": global_summary["oracle_nu"],
                "MB_fixed_I_AB": fixed["I_AB"],
                "MB_global_I_AB": global_mb["I_AB"],
                "MB_oracle_I_AB": oracle["I_AB"],
                "Joint_I_AB": joint["I_AB"],
                "MB_fixed_chi_BE": fixed["chi_BE"],
                "MB_global_chi_BE": global_mb["chi_BE"],
                "MB_oracle_chi_BE": oracle["chi_BE"],
                "Joint_chi_BE": joint["chi_BE"],
                "MB_fixed_K_raw": fixed["K_raw"],
                "MB_global_K_raw": global_mb["K_raw"],
                "MB_oracle_K_raw": oracle["K_raw"],
                "Joint_K_raw": joint["K_raw"],
                "MB_global_K_positive": global_mb["K_positive"],
                "Joint_K_positive": joint["K_positive"],
                "MB_global_entropy": global_mb["entropy"],
                "Joint_entropy": joint["entropy"],
                "MB_global_outage": global_mb["outage"],
                "Joint_outage": joint["outage"],
                "Delta_K_vs_fixed": fixed_summary["mean_delta_K"],
                "CI95_low_vs_fixed": fixed_summary["ci95_low"],
                "CI95_high_vs_fixed": fixed_summary["ci95_high"],
                "Delta_K_vs_global": global_summary["mean_delta_K"],
                "CI95_low_vs_global": global_summary["ci95_low"],
                "CI95_high_vs_global": global_summary["ci95_high"],
                "Delta_K_vs_oracle": oracle_summary["mean_delta_K"],
                "CI95_low_vs_oracle": oracle_summary["ci95_low"],
                "CI95_high_vs_oracle": oracle_summary["ci95_high"],
                "gain_source_vs_global": global_summary["gain_source"],
                "joint_minimum_distance": joint_geometry["minimum_distance"],
                "joint_peak_energy": joint_geometry["peak_energy"],
                "joint_geometry_drift": joint_geometry[
                    "geometry_drift_from_QAM"
                ],
                "checkpoint_phase": bundle.metadata["PS+GS"]["phase"],
                "checkpoint_epoch": bundle.metadata["PS+GS"]["epoch"],
                "training_seed_count": 1,
                "outperform_allowed": False,
            }
        )

        t_tensor = torch.tensor(
            [float(global_summary["T"])],
            dtype=core.REAL_DTYPE,
            device=bundle.device,
        )
        epsilon_tensor = torch.tensor(
            [float(global_summary["epsilon"])],
            dtype=core.REAL_DTYPE,
            device=bundle.device,
        )
        oracle_nu = float(global_summary["oracle_nu"])
        with torch.inference_mode():
            outputs = {
                "MB-global-opt": audit.fixed_probability_output(
                    audit.mb_probabilities(global_nu, bundle.device),
                    t_tensor,
                    bundle.base_qam,
                    bundle.args.va,
                ),
                "MB-oracle-per-state": audit.fixed_probability_output(
                    audit.mb_probabilities(oracle_nu, bundle.device),
                    t_tensor,
                    bundle.base_qam,
                    bundle.args.va,
                ),
                "PS+GS": bundle.models["PS+GS"](t_tensor, epsilon_tensor),
            }
        for scheme, output in outputs.items():
            for symbol in range(core.SYMBOL_COUNT):
                symbols.append(
                    {
                        "case_id": case_id,
                        "T": global_summary["T"],
                        "epsilon": global_summary["epsilon"],
                        "scheme": scheme,
                        "nu": (
                            global_nu
                            if scheme == "MB-global-opt"
                            else oracle_nu
                            if scheme == "MB-oracle-per-state"
                            else ""
                        ),
                        "symbol": symbol,
                        "probability": float(output.probabilities[0, symbol]),
                        "unit_I": float(
                            output.unit_constellation[0, symbol].real
                        ),
                        "unit_Q": float(
                            output.unit_constellation[0, symbol].imag
                        ),
                        "scaled_I": float(output.constellation[0, symbol].real),
                        "scaled_Q": float(output.constellation[0, symbol].imag),
                    }
                )
    write_csv(output_dir / "three_best_case_details.csv", detailed)
    write_csv(output_dir / "three_best_case_symbol_data.csv", symbols)
    return detailed, symbols


def final_report(
    config: Mapping[str, Any],
    bundle: audit.ModelBundle,
    global_nu: float,
    coarse_summary: Sequence[Mapping[str, Any]],
    confirmation: Sequence[Mapping[str, Any]],
    fading: Sequence[Mapping[str, Any]],
    adaptivity: Sequence[Mapping[str, Any]],
    geometry: Sequence[Mapping[str, Any]],
    elapsed: float,
    output_dir: Path,
) -> None:
    joint_global = [
        row for row in confirmation if row["baseline"] == "MB-global-opt"
    ]
    joint_oracle = [
        row for row in confirmation if row["baseline"] == "MB-oracle-per-state"
    ]
    effect_floor = float(config["minimum_meaningful_gain"])
    confirmed_global = [
        row for row in joint_global if float(row["ci95_low"]) > effect_floor
    ]
    key_extensions = [
        row
        for row in joint_global
        if float(row["key_extension_fraction"]) > 0.0
        and float(row["ci95_low"]) > effect_floor
    ]
    fading_positive = [
        row for row in fading if float(row["ci95_low"]) > effect_floor
    ]
    if key_extensions and not fading_positive:
        conclusion = "1. Joint vượt MB-global-opt cục bộ gần ngưỡng trên evaluation seeds, nhưng chưa có 10 training seeds."
    elif fading_positive:
        conclusion = "2. Joint có gain evaluation-seed trong fading mạnh, nhưng chưa đủ training seeds để gọi outperform."
    elif any(
        float(row["ci95_low"]) > effect_floor
        for row in confirmation
        if row["baseline"] == "MB-fixed"
    ):
        conclusion = "3. Joint chỉ vượt MB-fixed; không vượt MB-global-opt một cách xác nhận được."
    else:
        conclusion = "4. Không tìm thấy bằng chứng Joint vượt MB trong miền khảo sát."

    ps_diag = next(row for row in adaptivity if row["scheme"] == "PS")
    joint_diag = next(row for row in adaptivity if row["scheme"] == "PS+GS")
    joint_geom = next(row for row in geometry if row["scheme"] == "PS+GS")

    all_snr_deltas: list[tuple[float, float, str]] = []
    lookup = lookup_summary(coarse_summary)
    for row in coarse_summary:
        if row["scheme"] == "PS+GS":
            key = (float(row["T"]), float(row["epsilon"]), "MB-global-opt")
            delta = float(row["mean_K_raw"]) - float(lookup[key]["mean_K_raw"])
            all_snr_deltas.append(
                (delta, float(row["SNR_dB"]), snr_band(float(row["SNR_dB"])))
            )
    best_snr = max(all_snr_deltas, key=lambda item: item[0])
    best_confirmed = (
        max(joint_global, key=lambda row: float(row["mean_delta_K"]))
        if joint_global
        else None
    )
    dominant_source = (
        str(best_confirmed["gain_source"]) if best_confirmed else "none"
    )
    max_fading_outage = (
        max(fading, key=lambda row: float(row["mean_outage_reduction"]))
        if fading
        else None
    )

    lines = [
        "# Tìm kiếm miền Joint PS+GS vượt MB gần ngưỡng tạo khóa",
        "",
        "## Kết luận bắt buộc",
        "",
        f"**{conclusion}**",
        "",
        f"MB-global-opt cho miền tìm kiếm dùng nu*={global_nu:g}; MB-fixed dùng nu=0.1. "
        "Oracle-per-state được chọn bằng AWGN validation riêng rồi mới đánh giá trên test noise.",
        "",
        "## Trả lời trực tiếp",
        "",
        f"- Chênh lệch discovery lớn nhất xuất hiện ở SNR {best_snr[1]:.3f} dB, "
        f"thuộc miền **{best_snr[2]}**, với Delta K={best_snr[0]:+.6e}. "
        "Giá trị này chỉ dùng để chọn ứng viên.",
        f"- Trong các case final-test, nguồn chênh lệch tốt nhất là **{dominant_source}**.",
        (
            f"- Giảm outage lớn nhất trong fading test là "
            f"{float(max_fading_outage['mean_outage_reduction']):+.6e} "
            f"ở {max_fading_outage['fading_distribution']}."
            if max_fading_outage
            else "- Không có fading result."
        ),
        "",
        "## Kiểm tra cơ chế",
        "",
        f"- PS checkpoint: {ps_diag['checkpoint_phase']} epoch {ps_diag['checkpoint_epoch']}; "
        f"max state L1={float(ps_diag['max_state_pair_L1']):.3e}.",
        f"- Joint checkpoint: {joint_diag['checkpoint_phase']} epoch {joint_diag['checkpoint_epoch']}; "
        f"max state L1={float(joint_diag['max_state_pair_L1']):.3e}.",
        f"- Joint geometry drift={float(joint_geom['geometry_drift_from_QAM']):.3e}, "
        f"d_min={float(joint_geom['minimum_distance']):.3e}, "
        f"peak={float(joint_geom['peak_energy']):.3e}.",
        "",
        "PMF Joint bất biến theo trạng thái trong checkpoint hiện tại; mọi gain cục bộ không được "
        "quy cho adaptive PS.",
        "",
        "## Xác nhận ứng viên",
        "",
        "| Case | T | epsilon | SNR dB | Baseline | K_MB | K_Joint | Delta K | CI 95% | Key extension | Nguồn |",
        "|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in confirmation:
        lines.append(
            f"| {row['case_id']} | {float(row['T']):.4e} | {float(row['epsilon']):.4f} | "
            f"{float(row['SNR_dB']):.2f} | {row['baseline']} | "
            f"{float(row['mean_K_MB']):+.4e} | {float(row['mean_K_joint']):+.4e} | "
            f"{float(row['mean_delta_K']):+.4e} | "
            f"[{float(row['ci95_low']):+.3e}, {float(row['ci95_high']):+.3e}] | "
            f"{float(row['key_extension_fraction']):.2f} | {row['gain_source']} |"
        )
    lines.extend(
        [
            "",
            "## Điều kiện để gọi outperform",
            "",
            f"- Case có paired evaluation CI dương so với MB-global-opt: {len(confirmed_global)}.",
            f"- Case key-extension có CI dương: {len(key_extensions)}.",
            f"- Fading distributions có CI dương: {len(fading_positive)}.",
            "- Independent training seeds hiện có: 1, không phải 10. Vì vậy cột "
            "`outperform_allowed` luôn False và không có tuyên bố ưu thế ổn định.",
            f"- Effect floor để loại gain thuần số: {effect_floor:.1e} bit/symbol.",
            "- Các ablation training chưa có checkpoint không được thay bằng smoke run.",
            "",
            "## Phạm vi và tái lập",
            "",
            "- Coarse/fine grid dùng direct conditional T. Một giá trị T không có ánh xạ ngược "
            "duy nhất sang L, Cn2, visibility, W0 và aperture; không bịa một cấu hình vật lý duy nhất.",
            "- Synthetic fading giữ cùng mean T nhưng thay variance, deep-fade probability và tail.",
            "- Heatmap discovery đánh dấu K_MB=0 và K_Joint=0; candidate confirmation dùng test "
            "noise độc lập và ncut theo config.",
            (
                f"- Runtime: {config['_runtime_note']}; quick={config['quick']}; "
                f"device={config['device']}."
                if config.get("_runtime_note")
                else f"- Runtime: {elapsed:.1f} s; quick={config['quick']}; "
                f"device={config['device']}."
            ),
        ]
    )
    (output_dir / "near_threshold_report_vi.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def parse_cli(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("near_threshold_search_config.json")
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--quick", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    cli = parse_cli(argv)
    config = load_config(cli.config, cli.quick, cli.output_dir)
    output_dir = Path(config["output_directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    audit_config = audit.load_config(
        Path(config["audit_config"]), quick=False, output_override=None
    )
    audit_config["device"] = config["device"]
    bundle = audit.load_models(audit_config)
    fixed_nu = float(audit_config["mb_fixed_nu"])
    config["nu_grid"] = audit_config["nu_grid"]

    coarse = coarse_points(config)
    global_nu, mb_selection = select_domain_global_nu(
        bundle, config, coarse, output_dir
    )
    coarse_raw = evaluate_points(
        bundle,
        coarse,
        fixed_nu,
        global_nu,
        int(config["coarse"]["repetitions"]),
        int(config["coarse"]["awgn_samples"]),
        int(config["coarse"]["ncut"]),
        int(config["seeds"]["coarse_start"]),
        "coarse",
    )
    coarse_summary = aggregate_grid(coarse_raw)
    coarse_deltas = paired_delta_summary(coarse_raw)
    write_csv(output_dir / "coarse_grid_raw.csv", coarse_raw)
    write_csv(output_dir / "coarse_grid_summary.csv", coarse_summary)
    write_csv(output_dir / "coarse_grid_paired_deltas.csv", coarse_deltas)
    plot_heatmap(coarse_summary, output_dir)
    plot_snr(coarse_summary, output_dir)

    fine = build_fine_points(coarse_summary, config)
    fine_raw = evaluate_points(
        bundle,
        fine,
        fixed_nu,
        global_nu,
        int(config["fine"]["repetitions"]),
        int(config["fine"]["awgn_samples"]),
        int(config["fine"]["ncut"]),
        int(config["seeds"]["fine_start"]),
        "fine",
    )
    fine_summary = aggregate_grid(fine_raw)
    fine_deltas = paired_delta_summary(fine_raw)
    write_csv(output_dir / "fine_grid_raw.csv", fine_raw)
    write_csv(output_dir / "fine_grid_summary.csv", fine_summary)
    write_csv(output_dir / "fine_grid_paired_deltas.csv", fine_deltas)

    threshold_candidates = select_candidates(
        fine_summary, fine_deltas, int(config["candidate_cases_each"])
    )
    candidates = add_overall_best_candidates(
        threshold_candidates,
        coarse_summary,
        coarse_deltas,
        int(config["candidate_cases_each"]),
    )
    write_csv(output_dir / "selected_candidates_discovery.csv", candidates)
    oracle_nu, oracle_rows = select_oracle_nu(
        bundle, config, candidates, output_dir
    )
    confirmation_runs, confirmation_summary = confirm_candidates(
        bundle,
        config,
        candidates,
        fixed_nu,
        global_nu,
        oracle_nu,
        output_dir,
    )

    global_rows = [
        row
        for row in confirmation_summary
        if row["baseline"] == "MB-global-opt"
    ]
    near_threshold = min(
        global_rows, key=lambda row: abs(float(row["mean_K_MB"]))
    )
    mean_point = Point(float(near_threshold["T"]), float(near_threshold["epsilon"]))
    fading_runs, fading_comparisons = fading_search(
        bundle,
        config,
        mean_point,
        fixed_nu,
        global_nu,
        output_dir,
    )
    adaptivity, geometry = diagnostics(
        bundle, audit_config, global_nu, output_dir
    )
    top_candidate_artifacts(
        bundle,
        global_nu,
        confirmation_runs,
        confirmation_summary,
        geometry,
        output_dir,
    )
    audit.write_ablation_status(output_dir)
    manifest = {
        "config": config,
        "domain_global_nu": global_nu,
        "fixed_nu": fixed_nu,
        "model_metadata": bundle.metadata,
        "coarse_points": len(coarse),
        "fine_points": len(fine),
        "candidate_count": len(candidates),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    final_report(
        config,
        bundle,
        global_nu,
        coarse_summary,
        confirmation_summary,
        fading_comparisons,
        adaptivity,
        geometry,
        time.perf_counter() - started,
        output_dir,
    )
    print(f"Near-threshold search complete: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
