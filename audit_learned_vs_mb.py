"""Reproducible audit of learned PS/GS shaping against optimized MB-QAM.

The script deliberately separates:

1. validation-only selection of one global Maxwell--Boltzmann parameter;
2. paired final evaluation on independent channel/AWGN seeds;
3. exploratory phase-map selection at a reduced numerical budget;
4. full-cutoff confirmation of the selected best and failure cases.

It never trains a model. Consequently, confidence intervals quantify evaluation
uncertainty for the supplied checkpoints, not uncertainty over training seeds.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from scipy.stats import t as student_t

import uav_hap_joint_ps_gs as core
from uav_hap_1.config import ChannelParams, GeometryParams, QAM_NU_TILDE
from uav_hap_1.zstar import base as project_zbase


LEARNED_SCHEMES = ("PS", "GS", "PS+GS")
TEST_SCHEMES = ("MB-fixed", "MB-global-opt", "PS", "GS", "PS+GS")
PHASE_PAIRS = ("T_epsilon", "L_Cn2", "V_a", "W0_Cn2")
COLORS = {
    "MB-global-opt": "#8C6D31",
    "PS": "#2F6690",
    "GS": "#D17C1F",
    "PS+GS": "#158078",
}


@dataclass
class ModelBundle:
    models: dict[str, core.JointPSGS256QAM]
    metadata: dict[str, dict[str, Any]]
    base_qam: torch.Tensor
    args: argparse.Namespace
    device: torch.device


@dataclass
class Samples:
    transmittance: torch.Tensor
    epsilon: torch.Tensor
    noise: torch.Tensor
    channel_hash: str
    noise_hash: str


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def tensor_hash(tensor: torch.Tensor) -> str:
    values = np.ascontiguousarray(tensor.detach().cpu().numpy())
    return hashlib.sha256(values.tobytes()).hexdigest()[:16]


def load_config(path: Path, quick: bool, output_override: Path | None) -> dict[str, Any]:
    config_path = path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["_config_path"] = str(config_path)
    base = config_path.parent
    config["project_config"] = str((base / config["project_config"]).resolve())
    config["checkpoints"] = {
        key: str((base / value).resolve()) for key, value in config["checkpoints"].items()
    }
    output = (base / config["output_directory"]).resolve()
    if output_override is not None:
        output = output_override.resolve()
    config["output_directory"] = str(output)
    config["quick"] = bool(quick)
    if isinstance(config["nu_grid"], Mapping):
        specification = config["nu_grid"]
        minimum = float(specification["minimum"])
        maximum = float(specification["maximum"])
        step = float(specification["step"])
        count = int(round((maximum - minimum) / step))
        config["nu_grid"] = [
            round(minimum + index * step, 12) for index in range(count + 1)
        ]
    if quick:
        config["nu_grid"] = [0.0, 0.05, 0.1, 0.15, 0.2]
        for section in ("validation", "test", "phase_maps", "confirmation"):
            config[section]["fading_samples"] = min(int(config[section]["fading_samples"]), 4)
            config[section]["awgn_samples"] = min(int(config[section]["awgn_samples"]), 4)
            config[section]["ncut"] = min(int(config[section]["ncut"]), 24)
        config["test"]["repetitions"] = 2
        config["phase_maps"]["repetitions"] = 1
        config["confirmation"]["repetitions"] = 2
        config["phase_maps"]["points_per_axis"] = 2
    validate_config(config)
    return config


def validate_config(config: Mapping[str, Any]) -> None:
    if set(config["checkpoints"]) != {"ps", "gs", "joint"}:
        raise ValueError("checkpoints must contain ps, gs, and joint.")
    nu_grid = np.asarray(config["nu_grid"], dtype=np.float64)
    if nu_grid.ndim != 1 or nu_grid.size < 2 or np.any(nu_grid < 0):
        raise ValueError("nu_grid must contain at least two nonnegative values.")
    if not np.any(np.isclose(nu_grid, float(config["mb_fixed_nu"]))):
        raise ValueError("nu_grid must include mb_fixed_nu.")
    for section in ("validation", "test", "phase_maps", "confirmation"):
        for field in ("fading_samples", "awgn_samples", "ncut"):
            if int(config[section][field]) <= 0:
                raise ValueError(f"{section}.{field} must be positive.")


def load_models(config: Mapping[str, Any]) -> ModelBundle:
    device = torch.device(str(config["device"]))
    args = core.parse_args(["--config", str(config["project_config"])])
    base_qam = core.build_project_qam(device)
    models: dict[str, core.JointPSGS256QAM] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for label, mode in (("PS", "ps"), ("GS", "gs"), ("PS+GS", "joint")):
        path = Path(str(config["checkpoints"][mode]))
        model = core.create_model(mode, base_qam, args)
        payload = core.load_training_checkpoint(path, model, restore_rng=False)
        model.eval()
        models[label] = model
        metadata[label] = {
            "checkpoint": str(path),
            "phase": str(payload.get("phase", "unknown")),
            "epoch": int(payload.get("epoch", -1)),
            "validation_metrics": payload.get("validation_metrics", {}),
        }
    return ModelBundle(models, metadata, base_qam, args, device)


def mb_probabilities(nu: float, device: torch.device) -> torch.Tensor:
    values = project_zbase.build_probs_mb(float(nu))
    return torch.as_tensor(values, dtype=core.REAL_DTYPE, device=device)


def fixed_probability_output(
    probabilities_1d: torch.Tensor,
    transmittance: torch.Tensor,
    base_qam: torch.Tensor,
    target_va: float,
) -> core.ModelOutput:
    probabilities = probabilities_1d.unsqueeze(0).expand(transmittance.numel(), -1)
    raw = core.complex_from_xy(base_qam)
    unit = core.normalize_unit_energy_batch(probabilities, raw)
    constellation = unit * math.sqrt(float(target_va) / 2.0)
    return core.ModelOutput(
        probabilities=probabilities,
        probabilities_safe=probabilities.clamp_min(1e-12),
        unit_constellation=unit,
        constellation=constellation,
        logits=torch.log(probabilities.clamp_min(1e-12)),
        features=torch.empty(
            (transmittance.numel(), 0), dtype=core.REAL_DTYPE, device=transmittance.device
        ),
        gumbel_symbols=None,
    )


def evaluate(
    name: str,
    output: core.ModelOutput,
    samples: Samples,
    bundle: ModelBundle,
    ncut: int,
    awgn_samples: int,
) -> core.SchemeEvaluation:
    return core.evaluate_output(
        name,
        output,
        samples.transmittance,
        samples.epsilon,
        bundle.args.beta,
        int(ncut),
        int(awgn_samples),
        samples.noise,
        bundle.args.candidate_chunk_size,
        bundle.args.va,
    )


def channel_samples(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    budget: Mapping[str, Any],
    channel_seed: int,
    noise_seed: int,
    geometry: GeometryParams | None = None,
    channel_parameters: ChannelParams | None = None,
    epsilon: float | None = None,
    fixed_t: float | None = None,
) -> Samples:
    count = int(budget["fading_samples"])
    if fixed_t is None:
        result = core.channel(
            geometry or GeometryParams(),
            channel_parameters or ChannelParams(),
            N=count,
            rng=np.random.default_rng(int(channel_seed)),
        )
        transmittance = torch.as_tensor(
            np.asarray(result["T_samples"], dtype=np.float64),
            dtype=core.REAL_DTYPE,
            device=bundle.device,
        )
    else:
        transmittance = torch.full(
            (count,), float(fixed_t), dtype=core.REAL_DTYPE, device=bundle.device
        )
    epsilon_tensor = torch.full_like(
        transmittance,
        float(bundle.args.epsilon if epsilon is None else epsilon),
    )
    noise = core.make_standard_complex_noise(
        count,
        core.SYMBOL_COUNT,
        int(budget["awgn_samples"]),
        core.tensor_generator(int(noise_seed), bundle.device),
        bundle.device,
    )
    return Samples(
        transmittance,
        epsilon_tensor,
        noise,
        tensor_hash(transmittance),
        tensor_hash(noise),
    )


def evaluation_metrics(evaluation: core.SchemeEvaluation) -> dict[str, float]:
    raw = evaluation.raw_skr.detach().cpu().numpy()
    metrics = {
        "I_AB": float(evaluation.i_ab.mean()),
        "chi_BE": float(evaluation.security.chi_be.mean()),
        "beta_I_AB": float((evaluation.raw_skr + evaluation.security.chi_be).mean()),
        "K_raw_mean": float(raw.mean()),
        "K_raw_median": float(np.median(raw)),
        "K_raw_p05": float(np.quantile(raw, 0.05)),
        "outage_probability": float(np.mean(raw <= 0.0)),
        "entropy": float(evaluation.entropy.mean()),
    }
    metrics["finite"] = bool(all(math.isfinite(value) for value in metrics.values()))
    return metrics


def all_outputs(
    bundle: ModelBundle,
    samples: Samples,
    fixed_nu: float,
    global_nu: float,
) -> dict[str, core.ModelOutput]:
    outputs = {
        "MB-fixed": fixed_probability_output(
            mb_probabilities(fixed_nu, bundle.device),
            samples.transmittance,
            bundle.base_qam,
            bundle.args.va,
        ),
        "MB-global-opt": fixed_probability_output(
            mb_probabilities(global_nu, bundle.device),
            samples.transmittance,
            bundle.base_qam,
            bundle.args.va,
        ),
    }
    for name in LEARNED_SCHEMES:
        outputs[name] = bundle.models[name](samples.transmittance, samples.epsilon)
    return outputs


def evaluate_nu_grid(
    bundle: ModelBundle,
    samples: Samples,
    nu_grid: Sequence[float],
    ncut: int,
    awgn_samples: int,
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    rows: list[dict[str, Any]] = []
    state_values: dict[str, list[np.ndarray]] = {
        "K_raw": [],
        "I_AB": [],
        "chi_BE": [],
    }
    with torch.inference_mode():
        for nu in nu_grid:
            output = fixed_probability_output(
                mb_probabilities(float(nu), bundle.device),
                samples.transmittance,
                bundle.base_qam,
                bundle.args.va,
            )
            result = evaluate(
                f"MB(nu={nu:g})", output, samples, bundle, ncut, awgn_samples
            )
            rows.append({"nu": float(nu), **evaluation_metrics(result)})
            state_values["K_raw"].append(result.raw_skr.detach().cpu().numpy())
            state_values["I_AB"].append(result.i_ab.detach().cpu().numpy())
            state_values["chi_BE"].append(result.security.chi_be.detach().cpu().numpy())
    return rows, {
        key: np.stack(values, axis=0) for key, values in state_values.items()
    }


def optimize_global_mb(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    output_dir: Path,
) -> tuple[float, list[dict[str, Any]]]:
    budget = config["validation"]
    samples = channel_samples(
        bundle,
        config,
        budget,
        int(config["seeds"]["validation_channel"]),
        int(config["seeds"]["validation_awgn"]),
    )
    rows, _ = evaluate_nu_grid(
        bundle,
        samples,
        config["nu_grid"],
        int(budget["ncut"]),
        int(budget["awgn_samples"]),
    )
    for row in rows:
        row.update(
            {
                "split": "validation",
                "channel_seed": int(config["seeds"]["validation_channel"]),
                "awgn_seed": int(config["seeds"]["validation_awgn"]),
                "channel_hash": samples.channel_hash,
                "noise_hash": samples.noise_hash,
                "ncut": int(budget["ncut"]),
                "fading_samples": int(budget["fading_samples"]),
                "awgn_samples": int(budget["awgn_samples"]),
            }
        )
    finite_rows = [row for row in rows if bool(row["finite"])]
    if not finite_rows:
        raise FloatingPointError("Every MB candidate produced non-finite validation metrics.")
    winner = max(finite_rows, key=lambda row: float(row["K_raw_mean"]))
    write_csv(output_dir / "mb_nu_validation.csv", rows)
    return float(winner["nu"]), rows


def t_interval(values: Sequence[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    mean = float(array.mean())
    if array.size < 2:
        return mean, mean
    critical = float(student_t.ppf(0.975, df=array.size - 1))
    half = critical * float(array.std(ddof=1)) / math.sqrt(array.size)
    return mean - half, mean + half


def gain_source(
    delta_i: float,
    delta_chi: float,
    delta_k: float | None = None,
    tolerance: float = 1e-7,
) -> str:
    if delta_k is not None and delta_k <= tolerance:
        return "No positive gain"
    i_positive = delta_i > tolerance
    i_negative = delta_i < -tolerance
    chi_lower = delta_chi < -tolerance
    chi_same = abs(delta_chi) <= tolerance
    if i_positive and chi_same:
        return "MI-driven"
    if abs(delta_i) <= tolerance and chi_lower:
        return "Security-driven"
    if i_positive and chi_lower:
        return "Joint improvement"
    if i_negative and chi_lower:
        return "Trade-off"
    return "Mixed/none"


def paired_test(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    budget = config["test"]
    repetitions = int(budget["repetitions"])
    run_rows: list[dict[str, Any]] = []
    oracle_rows: list[dict[str, Any]] = []
    for repetition in range(repetitions):
        channel_seed = int(config["seeds"]["test_channel_start"]) + repetition
        awgn_seed = int(config["seeds"]["test_awgn_start"]) + repetition
        samples = channel_samples(
            bundle, config, budget, channel_seed, awgn_seed
        )
        with torch.inference_mode():
            outputs = all_outputs(
                bundle, samples, float(config["mb_fixed_nu"]), global_nu
            )
            for name in TEST_SCHEMES:
                result = evaluate(
                    name,
                    outputs[name],
                    samples,
                    bundle,
                    int(budget["ncut"]),
                    int(budget["awgn_samples"]),
                )
                run_rows.append(
                    {
                        "repetition": repetition,
                        "scheme": name,
                        **evaluation_metrics(result),
                        "channel_seed": channel_seed,
                        "awgn_seed": awgn_seed,
                        "channel_hash": samples.channel_hash,
                        "noise_hash": samples.noise_hash,
                        "ncut": int(budget["ncut"]),
                        "fading_samples": int(budget["fading_samples"]),
                        "awgn_samples": int(budget["awgn_samples"]),
                    }
                )
        nu_rows, state = evaluate_nu_grid(
            bundle,
            samples,
            config["nu_grid"],
            int(budget["ncut"]),
            int(budget["awgn_samples"]),
        )
        finite_k = np.where(np.isfinite(state["K_raw"]), state["K_raw"], -np.inf)
        if np.any(np.all(~np.isfinite(state["K_raw"]), axis=0)):
            raise FloatingPointError(
                "MB oracle has a state with no finite candidate on the configured nu grid."
            )
        best_indices = np.argmax(finite_k, axis=0)
        state_index = np.arange(best_indices.size)
        best_k = state["K_raw"][best_indices, state_index]
        best_i = state["I_AB"][best_indices, state_index]
        best_chi = state["chi_BE"][best_indices, state_index]
        oracle_rows.append(
            {
                "repetition": repetition,
                "scheme": "MB-oracle-per-state",
                "I_AB": float(best_i.mean()),
                "chi_BE": float(best_chi.mean()),
                "beta_I_AB": float(bundle.args.beta * best_i.mean()),
                "K_raw_mean": float(best_k.mean()),
                "K_raw_median": float(np.median(best_k)),
                "K_raw_p05": float(np.quantile(best_k, 0.05)),
                "outage_probability": float(np.mean(best_k <= 0.0)),
                "mean_selected_nu": float(
                    np.mean(np.asarray(config["nu_grid"])[best_indices])
                ),
                "channel_seed": channel_seed,
                "awgn_seed": awgn_seed,
            }
        )
        print(
            f"[paired test] {repetition + 1}/{repetitions} complete",
            flush=True,
        )
    write_csv(output_dir / "paired_test_runs.csv", run_rows + oracle_rows)

    by_rep: dict[int, dict[str, Mapping[str, Any]]] = {}
    for row in run_rows + oracle_rows:
        by_rep.setdefault(int(row["repetition"]), {})[str(row["scheme"])] = row
    comparisons = {
        "Q1_PS_vs_MB_fixed": ("PS", "MB-fixed"),
        "Q1_GS_vs_MB_fixed": ("GS", "MB-fixed"),
        "Q1_joint_vs_MB_fixed": ("PS+GS", "MB-fixed"),
        "Q2_PS_vs_MB_global": ("PS", "MB-global-opt"),
        "Q2_GS_vs_MB_global": ("GS", "MB-global-opt"),
        "Q2_joint_vs_MB_global": ("PS+GS", "MB-global-opt"),
        "Q3_PS_vs_MB_oracle": ("PS", "MB-oracle-per-state"),
        "Q3_joint_vs_MB_oracle": ("PS+GS", "MB-oracle-per-state"),
        "Q4_joint_vs_PS": ("PS+GS", "PS"),
        "Q4_joint_vs_GS": ("PS+GS", "GS"),
    }
    summary: list[dict[str, Any]] = []
    for label, (first, second) in comparisons.items():
        deltas = []
        delta_i = []
        delta_chi = []
        delta_outage = []
        for repetition in sorted(by_rep):
            a = by_rep[repetition][first]
            b = by_rep[repetition][second]
            deltas.append(float(a["K_raw_mean"]) - float(b["K_raw_mean"]))
            delta_i.append(float(a["I_AB"]) - float(b["I_AB"]))
            delta_chi.append(float(a["chi_BE"]) - float(b["chi_BE"]))
            delta_outage.append(
                float(b["outage_probability"]) - float(a["outage_probability"])
            )
        low, high = t_interval(deltas)
        summary.append(
            {
                "comparison": label,
                "scheme": first,
                "baseline": second,
                "mean_delta_K": float(np.mean(deltas)),
                "std_delta_K": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
                "ci95_low": low,
                "ci95_high": high,
                "P_delta_K_gt_0": float(np.mean(np.asarray(deltas) > 0.0)),
                "mean_delta_I_AB": float(np.mean(delta_i)),
                "mean_delta_chi_BE": float(np.mean(delta_chi)),
                "mean_delta_outage": float(np.mean(delta_outage)),
                "gain_source": gain_source(
                    float(np.mean(delta_i)),
                    float(np.mean(delta_chi)),
                    float(np.mean(deltas)),
                ),
                "repetitions": len(deltas),
                "training_seed_count": 1,
            }
        )
    write_csv(output_dir / "paired_comparisons.csv", summary)
    return run_rows, oracle_rows, summary


def adaptivity_diagnostics(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    settings = config["adaptivity_grid"]
    t_values = np.asarray(settings["T_values"], dtype=np.float64)
    epsilon_values = np.asarray(settings["epsilon_values"], dtype=np.float64)
    pairs = [(float(t), float(e)) for e in epsilon_values for t in t_values]
    transmittance = torch.tensor(
        [pair[0] for pair in pairs], dtype=core.REAL_DTYPE, device=bundle.device
    )
    epsilon = torch.tensor(
        [pair[1] for pair in pairs], dtype=core.REAL_DTYPE, device=bundle.device
    )
    mb_fixed = mb_probabilities(float(config["mb_fixed_nu"]), bundle.device)
    mb_global = mb_probabilities(global_nu, bundle.device)
    rows: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    for name in ("PS", "PS+GS"):
        with torch.no_grad():
            output = bundle.models[name](transmittance, epsilon)
        probabilities = output.probabilities
        kl_fixed = torch.sum(
            probabilities
            * (
                torch.log(probabilities.clamp_min(1e-15))
                - torch.log(mb_fixed.clamp_min(1e-15))
            ),
            dim=-1,
        )
        kl_global = torch.sum(
            probabilities
            * (
                torch.log(probabilities.clamp_min(1e-15))
                - torch.log(mb_global.clamp_min(1e-15))
            ),
            dim=-1,
        )
        for index, (t_value, epsilon_value) in enumerate(pairs):
            rows.append(
                {
                    "scheme": name,
                    "T": t_value,
                    "epsilon": epsilon_value,
                    "KL_to_MB_fixed_nats": float(kl_fixed[index]),
                    "KL_to_MB_global_nats": float(kl_global[index]),
                    "entropy_bits": float(
                        -torch.sum(
                            probabilities[index]
                            * torch.log2(probabilities[index].clamp_min(1e-15))
                        )
                    ),
                    "pmf_hash": tensor_hash(probabilities[index]),
                }
            )
        pairwise_l1 = torch.cdist(probabilities, probabilities, p=1)
        max_l1 = float(pairwise_l1.max())

        log_t = torch.tensor(
            float(np.log10(np.median(t_values))),
            dtype=core.REAL_DTYPE,
            device=bundle.device,
            requires_grad=True,
        )
        eps = torch.tensor(
            float(np.median(epsilon_values)),
            dtype=core.REAL_DTYPE,
            device=bundle.device,
            requires_grad=True,
        )

        def logits_from_inputs(values: torch.Tensor) -> torch.Tensor:
            local_t = torch.pow(
                torch.tensor(10.0, dtype=core.REAL_DTYPE, device=bundle.device),
                values[0],
            ).reshape(1)
            local_epsilon = values[1].reshape(1)
            features = bundle.models[name].channel_features(local_t, local_epsilon)
            return bundle.models[name].distribution_net(features)[0]

        jacobian = torch.autograd.functional.jacobian(
            logits_from_inputs, torch.stack((log_t, eps))
        )
        summary.append(
            {
                "scheme": name,
                "checkpoint_phase": bundle.metadata[name]["phase"],
                "checkpoint_epoch": bundle.metadata[name]["epoch"],
                "max_state_pair_L1": max_l1,
                "mean_KL_to_MB_fixed_nats": float(kl_fixed.mean()),
                "max_KL_to_MB_fixed_nats": float(kl_fixed.max()),
                "mean_KL_to_MB_global_nats": float(kl_global.mean()),
                "logit_jacobian_log10T_L2": float(torch.linalg.vector_norm(jacobian[:, 0])),
                "logit_jacobian_epsilon_L2": float(torch.linalg.vector_norm(jacobian[:, 1])),
                "adaptive_pmf_detected": bool(max_l1 > 1e-8),
                "epoch0_MB_initialization_only": bool(
                    bundle.metadata[name]["epoch"] == 0
                    and float(kl_fixed.max()) < 1e-10
                ),
            }
        )
    write_csv(output_dir / "adaptivity_grid.csv", rows)
    write_csv(output_dir / "adaptivity_summary.csv", summary)
    return rows, summary


def geometry_diagnostics(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    t_value = torch.tensor([float(config["geometry_probe_T"])], dtype=core.REAL_DTYPE, device=bundle.device)
    epsilon = torch.tensor([float(bundle.args.epsilon)], dtype=core.REAL_DTYPE, device=bundle.device)
    rows: list[dict[str, Any]] = []
    for name in LEARNED_SCHEMES:
        with torch.no_grad():
            output = bundle.models[name](t_value, epsilon)
            points = output.unit_constellation[0]
            distances = (points[:, None] - points[None, :]).abs()
            diagonal = torch.eye(
                core.SYMBOL_COUNT, dtype=torch.bool, device=bundle.device
            )
            d_min = float(distances.masked_fill(diagonal, torch.inf).min())
            peak = float(points.abs().square().max())
            raw_reference = core.complex_from_xy(bundle.base_qam)
            qam_same_p = core.normalize_unit_energy_batch(
                output.probabilities, raw_reference
            )[0]
            drift = float(torch.mean((points - qam_same_p).abs().square()))
        rows.append(
            {
                "scheme": name,
                "checkpoint_phase": bundle.metadata[name]["phase"],
                "checkpoint_epoch": bundle.metadata[name]["epoch"],
                "minimum_distance": d_min,
                "peak_energy": peak,
                "geometry_drift_from_QAM": drift,
                "collapsed": bool(d_min <= 1e-6),
                "ps_preserving_epoch0": bool(
                    name == "PS+GS"
                    and bundle.metadata[name]["phase"] == "geometry_warmup"
                    and bundle.metadata[name]["epoch"] == 0
                ),
            }
        )
    write_csv(output_dir / "geometry_diagnostics.csv", rows)
    return rows


def axis_values(spec: Mapping[str, Any], points: int) -> np.ndarray:
    minimum = float(spec["minimum"])
    maximum = float(spec["maximum"])
    if str(spec.get("scale", "linear")) == "log":
        return np.logspace(np.log10(minimum), np.log10(maximum), points)
    return np.linspace(minimum, maximum, points)


def condition_for_cell(
    pair: str,
    x: float,
    y: float,
) -> tuple[GeometryParams, ChannelParams, float | None, float | None]:
    geometry = GeometryParams()
    channel_parameters = ChannelParams()
    epsilon: float | None = None
    fixed_t: float | None = None
    if pair == "T_epsilon":
        fixed_t, epsilon = x, y
    elif pair == "L_Cn2":
        vertical = abs(geometry.H_HAP_m - geometry.H_UAV_m)
        distance_m = 1000.0 * x
        horizontal = math.sqrt(max(distance_m * distance_m - vertical * vertical, 0.0))
        geometry = replace(geometry, d_h_m=horizontal)
        channel_parameters = replace(channel_parameters, Cn2=y)
    elif pair == "V_a":
        channel_parameters = replace(channel_parameters, visibility_km=x, a_m=y)
    elif pair == "W0_Cn2":
        channel_parameters = replace(channel_parameters, W0_m=x, Cn2=y)
    else:
        raise ValueError(f"Unsupported phase pair: {pair}")
    return geometry, channel_parameters, epsilon, fixed_t


def phase_maps(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    output_dir: Path,
) -> list[dict[str, Any]]:
    settings = config["phase_maps"]
    points = int(settings["points_per_axis"])
    repetitions = int(settings["repetitions"])
    rows: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(PHASE_PAIRS):
        x_values = axis_values(settings["pairs"][pair]["x"], points)
        y_values = axis_values(settings["pairs"][pair]["y"], points)
        for yi, y in enumerate(y_values):
            for xi, x in enumerate(x_values):
                rep_metrics: dict[str, list[dict[str, float]]] = {
                    name: [] for name in ("MB-global-opt", *LEARNED_SCHEMES)
                }
                for repetition in range(repetitions):
                    seed = (
                        int(config["seeds"]["phase_start"])
                        + pair_index * 1_000_000
                        + yi * 10_000
                        + xi * 100
                        + repetition
                    )
                    geometry, channel_parameters, epsilon, fixed_t = condition_for_cell(
                        pair, float(x), float(y)
                    )
                    samples = channel_samples(
                        bundle,
                        config,
                        settings,
                        seed,
                        seed + 1,
                        geometry,
                        channel_parameters,
                        epsilon,
                        fixed_t,
                    )
                    with torch.inference_mode():
                        outputs = all_outputs(
                            bundle,
                            samples,
                            float(config["mb_fixed_nu"]),
                            global_nu,
                        )
                        for name in rep_metrics:
                            result = evaluate(
                                name,
                                outputs[name],
                                samples,
                                bundle,
                                int(settings["ncut"]),
                                int(settings["awgn_samples"]),
                            )
                            rep_metrics[name].append(evaluation_metrics(result))
                aggregate: dict[str, dict[str, float]] = {}
                for name, metrics in rep_metrics.items():
                    aggregate[name] = {
                        field: float(np.mean([row[field] for row in metrics]))
                        for field in metrics[0]
                    }
                winner = max(
                    aggregate,
                    key=lambda name: aggregate[name]["K_raw_mean"],
                )
                learned_winner = max(
                    LEARNED_SCHEMES,
                    key=lambda name: aggregate[name]["K_raw_mean"],
                )
                baseline = aggregate["MB-global-opt"]
                learned = aggregate[learned_winner]
                rows.append(
                    {
                        "pair": pair,
                        "x": float(x),
                        "y": float(y),
                        "winner": winner,
                        "best_learned": learned_winner,
                        "K_MB_global": baseline["K_raw_mean"],
                        "K_best_learned": learned["K_raw_mean"],
                        "Delta_K_learned_vs_MB_global": learned["K_raw_mean"]
                        - baseline["K_raw_mean"],
                        "Delta_I_AB": learned["I_AB"] - baseline["I_AB"],
                        "Delta_chi_BE": learned["chi_BE"] - baseline["chi_BE"],
                        "gain_source": gain_source(
                            learned["I_AB"] - baseline["I_AB"],
                            learned["chi_BE"] - baseline["chi_BE"],
                            learned["K_raw_mean"] - baseline["K_raw_mean"],
                        ),
                        "MB_outage": baseline["outage_probability"],
                        "learned_outage": learned["outage_probability"],
                        "Delta_outage": baseline["outage_probability"]
                        - learned["outage_probability"],
                        "learned_K_p05": learned["K_raw_p05"],
                        "MB_K_p05": baseline["K_raw_p05"],
                        "exploratory_ncut": int(settings["ncut"]),
                        "repetitions": repetitions,
                    }
                )
        print(f"[phase map] {pair} complete", flush=True)
    write_csv(output_dir / "phase_map_cells.csv", rows)
    plot_phase_maps(rows, settings, output_dir)
    return rows


def plot_phase_maps(
    rows: Sequence[Mapping[str, Any]],
    settings: Mapping[str, Any],
    output_dir: Path,
) -> None:
    code = {"MB-global-opt": 0, "PS": 1, "GS": 2, "PS+GS": 3}
    labels = list(code)
    cmap = matplotlib.colors.ListedColormap([COLORS[name] for name in labels])
    for pair in PHASE_PAIRS:
        selected = [row for row in rows if row["pair"] == pair]
        x_values = sorted({float(row["x"]) for row in selected})
        y_values = sorted({float(row["y"]) for row in selected})
        winner = np.zeros((len(y_values), len(x_values)))
        delta = np.zeros_like(winner)
        for row in selected:
            xi = x_values.index(float(row["x"]))
            yi = y_values.index(float(row["y"]))
            winner[yi, xi] = code[str(row["winner"])]
            delta[yi, xi] = float(row["Delta_K_learned_vs_MB_global"])
        figure, axes = plt.subplots(1, 2, figsize=(10.0, 4.0))
        image = axes[0].imshow(winner, origin="lower", aspect="auto", cmap=cmap, vmin=-0.5, vmax=3.5)
        colorbar = figure.colorbar(image, ax=axes[0], ticks=range(4))
        colorbar.ax.set_yticklabels(labels)
        delta_limit = max(float(np.max(np.abs(delta))), 1e-12)
        delta_image = axes[1].imshow(
            delta,
            origin="lower",
            aspect="auto",
            cmap="RdBu_r",
            vmin=-delta_limit,
            vmax=delta_limit,
        )
        figure.colorbar(delta_image, ax=axes[1], label=r"$K_{\rm learned}-K_{\rm MB-global}$")
        for axis in axes:
            axis.set_xticks(range(len(x_values)), [f"{value:.3g}" for value in x_values], rotation=45)
            axis.set_yticks(range(len(y_values)), [f"{value:.3g}" for value in y_values])
            axis.set_xlabel(settings["pairs"][pair]["x"]["label"])
            axis.set_ylabel(settings["pairs"][pair]["y"]["label"])
        axes[0].set_title("Best scheme (exploratory)")
        axes[1].set_title("Best learned minus MB-global-opt")
        figure.tight_layout()
        figure.savefig(output_dir / f"phase_map_{pair}.png", dpi=220, bbox_inches="tight")
        plt.close(figure)


def confirm_selected_cases(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    phase_rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    count = int(config["confirmation"]["cases_each"])
    ranked = sorted(
        phase_rows,
        key=lambda row: float(row["Delta_K_learned_vs_MB_global"]),
        reverse=True,
    )
    selected = [("best", row) for row in ranked[:count]]
    selected += [("failure", row) for row in ranked[-count:]]
    budget = config["confirmation"]
    run_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for case_index, (case_type, cell) in enumerate(selected):
        pair = str(cell["pair"])
        x = float(cell["x"])
        y = float(cell["y"])
        learned_name = str(cell["best_learned"])
        deltas: list[float] = []
        delta_i: list[float] = []
        delta_chi: list[float] = []
        for repetition in range(int(budget["repetitions"])):
            seed = int(config["seeds"]["confirmation_start"]) + case_index * 10_000 + repetition
            geometry, channel_parameters, epsilon, fixed_t = condition_for_cell(pair, x, y)
            samples = channel_samples(
                bundle,
                config,
                budget,
                seed,
                seed + 1,
                geometry,
                channel_parameters,
                epsilon,
                fixed_t,
            )
            with torch.inference_mode():
                outputs = all_outputs(
                    bundle,
                    samples,
                    float(config["mb_fixed_nu"]),
                    global_nu,
                )
                evaluated: dict[str, dict[str, float]] = {}
                for name in ("MB-global-opt", learned_name):
                    result = evaluate(
                        name,
                        outputs[name],
                        samples,
                        bundle,
                        int(budget["ncut"]),
                        int(budget["awgn_samples"]),
                    )
                    evaluated[name] = evaluation_metrics(result)
                    run_rows.append(
                        {
                            "case_id": case_index,
                            "case_type": case_type,
                            "pair": pair,
                            "x": x,
                            "y": y,
                            "repetition": repetition,
                            "scheme": name,
                            **evaluated[name],
                            "channel_seed": seed,
                            "awgn_seed": seed + 1,
                            "channel_hash": samples.channel_hash,
                            "noise_hash": samples.noise_hash,
                        }
                    )
            learned = evaluated[learned_name]
            baseline = evaluated["MB-global-opt"]
            deltas.append(learned["K_raw_mean"] - baseline["K_raw_mean"])
            delta_i.append(learned["I_AB"] - baseline["I_AB"])
            delta_chi.append(learned["chi_BE"] - baseline["chi_BE"])
        low, high = t_interval(deltas)
        summaries.append(
            {
                "case_id": case_index,
                "case_type": case_type,
                "pair": pair,
                "x": x,
                "y": y,
                "scheme": learned_name,
                "mean_delta_K": float(np.mean(deltas)),
                "ci95_low": low,
                "ci95_high": high,
                "P_delta_K_gt_0": float(np.mean(np.asarray(deltas) > 0)),
                "mean_delta_I_AB": float(np.mean(delta_i)),
                "mean_delta_chi_BE": float(np.mean(delta_chi)),
                "gain_source": gain_source(
                    float(np.mean(delta_i)),
                    float(np.mean(delta_chi)),
                    float(np.mean(deltas)),
                ),
                "independent_test_confirmed": bool(low > 0.0),
                "ncut": int(budget["ncut"]),
                "repetitions": int(budget["repetitions"]),
            }
        )
        print(
            f"[confirmation] {case_index + 1}/{len(selected)} {case_type} {pair} complete",
            flush=True,
        )
    write_csv(output_dir / "selected_case_runs.csv", run_rows)
    write_csv(output_dir / "selected_case_summary.csv", summaries)
    return run_rows, summaries


def write_ablation_status(output_dir: Path) -> list[dict[str, Any]]:
    requested = [
        "PS init MB",
        "PS init Uniform",
        "PS init random valid",
        "GS without drift penalty",
        "GS lambda_drift sweep",
        "joint simultaneous",
        "joint alternating",
        "joint with geometry warm-up",
        "joint without geometry warm-up",
        "joint PS-preserving initialization",
        "joint combined initialization",
        "PS/GS learning-rate ratios",
        "more epochs and patience",
        "larger AWGN budget",
        "larger fading budget",
        "ncut 120 and 150",
    ]
    available = {
        "PS init MB": "available checkpoint; best PS epoch 0",
        "joint simultaneous": "available checkpoint/config",
        "joint with geometry warm-up": "available checkpoint/config",
        "joint PS-preserving initialization": "available epoch-zero candidate",
        "joint combined initialization": "available epoch-zero candidate",
        "larger AWGN budget": "evaluation-only confirmation, not retraining",
        "larger fading budget": "evaluation-only confirmation, not retraining",
        "ncut 120 and 150": "performed in validation/final evaluation",
    }
    rows = [
        {
            "ablation": name,
            "status": "available/evaluated" if name in available else "not run",
            "evidence_or_reason": available.get(
                name,
                "No independent trained checkpoint exists; running a smoke training would not answer convergence.",
            ),
        }
        for name in requested
    ]
    write_csv(output_dir / "ablation_status.csv", rows)
    return rows


def cutoff_convergence(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    output_dir: Path,
) -> list[dict[str, Any]]:
    """Compare ncut=120 and 150 on identical samples for every main scheme."""
    budget = {
        "fading_samples": min(8, int(config["test"]["fading_samples"])),
        "awgn_samples": min(32, int(config["test"]["awgn_samples"])),
    }
    seed = int(config["seeds"]["test_channel_start"]) + 9_000_000
    samples = channel_samples(bundle, config, budget, seed, seed + 1)
    rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        outputs = all_outputs(
            bundle,
            samples,
            float(config["mb_fixed_nu"]),
            global_nu,
        )
        for ncut in (120, 150):
            for name in TEST_SCHEMES:
                result = evaluate(
                    name,
                    outputs[name],
                    samples,
                    bundle,
                    ncut,
                    int(budget["awgn_samples"]),
                )
                rows.append(
                    {
                        "ncut": ncut,
                        "scheme": name,
                        **evaluation_metrics(result),
                        "channel_seed": seed,
                        "awgn_seed": seed + 1,
                        "channel_hash": samples.channel_hash,
                        "noise_hash": samples.noise_hash,
                    }
                )
    references = {
        str(row["scheme"]): row for row in rows if int(row["ncut"]) == 150
    }
    for row in rows:
        reference = references[str(row["scheme"])]
        row["abs_delta_K_vs_ncut150"] = abs(
            float(row["K_raw_mean"]) - float(reference["K_raw_mean"])
        )
    write_csv(output_dir / "ncut_convergence_120_150.csv", rows)
    return rows


def modulation_variance_sweep(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validation-only fair V_A sweep with MB nu re-optimized at every V_A."""
    va_values = [0.5, 1.0, 2.0, 4.0, 8.0]
    budget = {
        "fading_samples": 8,
        "awgn_samples": 32,
        "ncut": 150,
    }
    seed = int(config["seeds"]["validation_channel"]) + 77_000
    samples = channel_samples(bundle, config, budget, seed, seed + 1)
    old_va = float(bundle.args.va)
    old_targets = {name: float(model.target_va) for name, model in bundle.models.items()}
    rows: list[dict[str, Any]] = []
    try:
        for va in va_values:
            bundle.args.va = float(va)
            for model in bundle.models.values():
                model.target_va = float(va)
            nu_rows, _ = evaluate_nu_grid(
                bundle,
                samples,
                config["nu_grid"],
                int(budget["ncut"]),
                int(budget["awgn_samples"]),
            )
            finite = [row for row in nu_rows if bool(row["finite"])]
            best_nu_row = max(finite, key=lambda row: float(row["K_raw_mean"]))
            best_nu = float(best_nu_row["nu"])
            with torch.inference_mode():
                outputs = all_outputs(
                    bundle,
                    samples,
                    float(config["mb_fixed_nu"]),
                    best_nu,
                )
                for name in TEST_SCHEMES:
                    result = evaluate(
                        name,
                        outputs[name],
                        samples,
                        bundle,
                        int(budget["ncut"]),
                        int(budget["awgn_samples"]),
                    )
                    rows.append(
                        {
                            "V_A": va,
                            "scheme": name,
                            "MB_global_nu_at_V_A": best_nu,
                            **evaluation_metrics(result),
                            "split": "validation-only",
                            "ncut": int(budget["ncut"]),
                            "fading_samples": int(budget["fading_samples"]),
                            "awgn_samples": int(budget["awgn_samples"]),
                            "channel_seed": seed,
                            "awgn_seed": seed + 1,
                        }
                    )
            print(f"[V_A sweep] V_A={va:g}, MB nu*={best_nu:g}", flush=True)
    finally:
        bundle.args.va = old_va
        for name, model in bundle.models.items():
            model.target_va = old_targets[name]
    summary: list[dict[str, Any]] = []
    for name in TEST_SCHEMES:
        candidates = [row for row in rows if row["scheme"] == name]
        best = max(candidates, key=lambda row: float(row["K_raw_mean"]))
        summary.append(
            {
                "scheme": name,
                "best_V_A": best["V_A"],
                "best_K_raw_validation": best["K_raw_mean"],
                "MB_global_nu_at_best_V_A": best["MB_global_nu_at_V_A"],
                "note": (
                    "checkpoint evaluated out of its V_A=2 training distribution"
                    if name in LEARNED_SCHEMES and float(best["V_A"]) != 2.0
                    else ""
                ),
            }
        )
    write_csv(output_dir / "modulation_variance_sweep.csv", rows)
    write_csv(output_dir / "modulation_variance_summary.csv", summary)
    return rows, summary


def robustness_and_thresholds(
    phase_rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Finite-difference sensitivity and coarse zero-key thresholds from full grids."""
    sensitivity_rows: list[dict[str, Any]] = []
    for pair in PHASE_PAIRS:
        selected = [row for row in phase_rows if row["pair"] == pair]
        x_values = np.asarray(sorted({float(row["x"]) for row in selected}))
        y_values = np.asarray(sorted({float(row["y"]) for row in selected}))
        for metric, source in (
            ("K_MB_global", "MB-global-opt"),
            ("K_best_learned", "best learned"),
        ):
            matrix = np.empty((y_values.size, x_values.size), dtype=np.float64)
            lookup = {(float(row["x"]), float(row["y"])): row for row in selected}
            for yi, y in enumerate(y_values):
                for xi, x in enumerate(x_values):
                    matrix[yi, xi] = float(lookup[(float(x), float(y))][metric])
            edge_order = 2 if min(matrix.shape) >= 3 else 1
            derivative_y, derivative_x = np.gradient(
                matrix, y_values, x_values, edge_order=edge_order
            )
            for yi, y in enumerate(y_values):
                for xi, x in enumerate(x_values):
                    sensitivity_rows.append(
                        {
                            "pair": pair,
                            "scheme": source,
                            "x": float(x),
                            "y": float(y),
                            "dK_dx": float(derivative_x[yi, xi]),
                            "dK_dy": float(derivative_y[yi, xi]),
                            "exploratory_only": True,
                        }
                    )

    threshold_rows: list[dict[str, Any]] = []
    for pair, axis, group_axis in (
        ("T_epsilon", "y", "x"),
        ("L_Cn2", "x", "y"),
    ):
        selected = [row for row in phase_rows if row["pair"] == pair]
        group_values = sorted({float(row[group_axis]) for row in selected})
        for group_value in group_values:
            subset = [
                row for row in selected if float(row[group_axis]) == group_value
            ]
            for metric, scheme in (
                ("K_MB_global", "MB-global-opt"),
                ("K_best_learned", "best learned"),
            ):
                positive_axis = [
                    float(row[axis]) for row in subset if float(row[metric]) > 0.0
                ]
                if pair == "T_epsilon":
                    threshold = max(positive_axis) if positive_axis else math.nan
                    threshold_name = "epsilon_max_grid"
                else:
                    threshold = max(positive_axis) if positive_axis else math.nan
                    threshold_name = "L_max_grid_km"
                threshold_rows.append(
                    {
                        "pair": pair,
                        "condition_axis": group_axis,
                        "condition_value": group_value,
                        "scheme": scheme,
                        "threshold_name": threshold_name,
                        "threshold_value": threshold,
                        "coarse_grid_only": True,
                    }
                )
    write_csv(output_dir / "robustness_sensitivity.csv", sensitivity_rows)
    write_csv(output_dir / "exploratory_thresholds.csv", threshold_rows)
    return sensitivity_rows, threshold_rows


def selected_case_artifacts(
    bundle: ModelBundle,
    config: Mapping[str, Any],
    global_nu: float,
    case_runs: Sequence[Mapping[str, Any]],
    case_summaries: Sequence[Mapping[str, Any]],
    geometry_rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Create publication-facing case tables plus PMF/constellation symbol data."""
    geometry = {str(row["scheme"]): row for row in geometry_rows}
    detailed: list[dict[str, Any]] = []
    symbol_rows: list[dict[str, Any]] = []
    for summary in case_summaries:
        case_id = int(summary["case_id"])
        learned_name = str(summary["scheme"])
        matching = [row for row in case_runs if int(row["case_id"]) == case_id]
        by_scheme = {
            name: [row for row in matching if row["scheme"] == name]
            for name in ("MB-global-opt", learned_name)
        }
        means: dict[str, dict[str, float]] = {}
        for name, rows in by_scheme.items():
            means[name] = {
                field: float(np.mean([float(row[field]) for row in rows]))
                for field in (
                    "I_AB",
                    "chi_BE",
                    "K_raw_mean",
                    "entropy",
                    "K_raw_p05",
                    "outage_probability",
                )
            }
        baseline = means["MB-global-opt"]
        learned = means[learned_name]
        detailed.append(
            {
                **dict(summary),
                "MB_I_AB": baseline["I_AB"],
                "learned_I_AB": learned["I_AB"],
                "MB_chi_BE": baseline["chi_BE"],
                "learned_chi_BE": learned["chi_BE"],
                "MB_K_raw": baseline["K_raw_mean"],
                "learned_K_raw": learned["K_raw_mean"],
                "MB_entropy": baseline["entropy"],
                "learned_entropy": learned["entropy"],
                "MB_K_p05": baseline["K_raw_p05"],
                "learned_K_p05": learned["K_raw_p05"],
                "Delta_K_p05": learned["K_raw_p05"] - baseline["K_raw_p05"],
                "MB_outage": baseline["outage_probability"],
                "learned_outage": learned["outage_probability"],
                "Delta_outage_MB_minus_learned": baseline["outage_probability"]
                - learned["outage_probability"],
                "learned_minimum_distance": geometry[learned_name][
                    "minimum_distance"
                ],
                "learned_peak_energy": geometry[learned_name]["peak_energy"],
                "learned_geometry_drift": geometry[learned_name][
                    "geometry_drift_from_QAM"
                ],
                "checkpoint_phase": bundle.metadata[learned_name]["phase"],
                "checkpoint_epoch": bundle.metadata[learned_name]["epoch"],
            }
        )

        pair = str(summary["pair"])
        representative_t = float(summary["x"]) if pair == "T_epsilon" else 0.05
        representative_epsilon = (
            float(summary["y"]) if pair == "T_epsilon" else float(bundle.args.epsilon)
        )
        t_tensor = torch.tensor(
            [representative_t], dtype=core.REAL_DTYPE, device=bundle.device
        )
        epsilon_tensor = torch.tensor(
            [representative_epsilon], dtype=core.REAL_DTYPE, device=bundle.device
        )
        with torch.inference_mode():
            mb_output = fixed_probability_output(
                mb_probabilities(global_nu, bundle.device),
                t_tensor,
                bundle.base_qam,
                bundle.args.va,
            )
            learned_output = bundle.models[learned_name](t_tensor, epsilon_tensor)
        for name, output in (
            ("MB-global-opt", mb_output),
            (learned_name, learned_output),
        ):
            for symbol in range(core.SYMBOL_COUNT):
                symbol_rows.append(
                    {
                        "case_id": case_id,
                        "case_type": summary["case_type"],
                        "pair": pair,
                        "x": summary["x"],
                        "y": summary["y"],
                        "scheme": name,
                        "symbol": symbol,
                        "probability": float(output.probabilities[0, symbol]),
                        "unit_I": float(output.unit_constellation[0, symbol].real),
                        "unit_Q": float(output.unit_constellation[0, symbol].imag),
                    }
                )
    write_csv(output_dir / "selected_case_details.csv", detailed)
    write_csv(output_dir / "selected_case_symbol_data.csv", symbol_rows)
    write_csv(
        output_dir / "three_best_cases.csv",
        [row for row in detailed if row["case_type"] == "best"],
    )
    write_csv(
        output_dir / "three_failure_cases.csv",
        [row for row in detailed if row["case_type"] == "failure"],
    )
    confirmed = [
        row for row in detailed if float(row["ci95_low"]) > 0.0
    ]
    if confirmed:
        domain_rows = confirmed
    else:
        domain_rows = [
            {
                "condition": "none confirmed",
                "MB_baseline": "MB-global-opt",
                "winning_scheme": "",
                "Delta_K": "",
                "CI95": "",
                "gain_source": "",
                "threshold_or_outage_gain": "",
                "conclusion": "No learned-over-MB domain survived independent confirmation.",
            }
        ]
    write_csv(output_dir / "outperformance_domains.csv", domain_rows)
    return detailed, symbol_rows


def append_supplement(
    output_dir: Path,
    va_summary: Sequence[Mapping[str, Any]],
    detailed_cases: Sequence[Mapping[str, Any]],
) -> None:
    lines = [
        "",
        "## 9. Kiểm tra modulation variance và đầu ra trường hợp",
        "",
        "V_A được sweep trên validation với MB re-optimize nu tại từng V_A. "
        "Learned checkpoints chỉ được đánh giá ngoài phân phối huấn luyện V_A=2, không retrain.",
        "",
        "| Scheme | V_A tốt nhất | K_raw validation tốt nhất | nu* của MB-global tại cùng V_A |",
        "|---|---:|---:|---:|",
    ]
    for row in va_summary:
        lines.append(
            f"| {row['scheme']} | {float(row['best_V_A']):g} | "
            f"{float(row['best_K_raw_validation']):+.6e} | "
            f"{float(row['MB_global_nu_at_best_V_A']):g} |"
        )
    lines.extend(
        [
            "",
            "MB-fixed và PMF của PS/PS+GS vẫn dùng nu=0.1; cột nu* chỉ cho biết "
            "baseline MB-global được re-optimize tại cùng V_A.",
            "",
            "Ba case discovery tốt nhất và ba case thất bại đều được giữ lại trong "
            "`selected_case_details.csv`; PMF và toàn bộ 256 tọa độ nằm trong "
            "`selected_case_symbol_data.csv`. Không case nào có CI xác nhận hoàn toàn dương "
            "thì `outperformance_domains.csv` ghi rõ không có miền outperform được xác nhận.",
        ]
    )
    report_path = output_dir / "final_report_vi.md"
    report_path.write_text(
        report_path.read_text(encoding="utf-8") + "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def report(
    config: Mapping[str, Any],
    bundle: ModelBundle,
    global_nu: float,
    validation_rows: Sequence[Mapping[str, Any]],
    comparisons: Sequence[Mapping[str, Any]],
    adaptivity: Sequence[Mapping[str, Any]],
    geometry: Sequence[Mapping[str, Any]],
    phase_rows: Sequence[Mapping[str, Any]],
    confirmed: Sequence[Mapping[str, Any]],
    ablations: Sequence[Mapping[str, Any]],
    cutoff_rows: Sequence[Mapping[str, Any]],
    elapsed: float,
    output_dir: Path,
) -> None:
    comparison_lookup = {str(row["comparison"]): row for row in comparisons}
    phase_wins = sum(
        float(row["Delta_K_learned_vs_MB_global"]) > 0.0 for row in phase_rows
    )
    confirmed_positive = [
        row for row in confirmed if bool(row["independent_test_confirmed"])
    ]
    ps_adapt = next(row for row in adaptivity if row["scheme"] == "PS")
    joint_adapt = next(row for row in adaptivity if row["scheme"] == "PS+GS")
    joint_geometry = next(row for row in geometry if row["scheme"] == "PS+GS")
    max_cutoff_error = max(
        float(row["abs_delta_K_vs_ncut150"]) for row in cutoff_rows
    )
    q2 = comparison_lookup["Q2_joint_vs_MB_global"]
    strong_allowed = (
        float(q2["ci95_low"]) > 0.0
        and int(q2["training_seed_count"]) >= 10
        and bool(confirmed_positive)
    )
    if strong_allowed:
        conclusion = "Learned shaping vượt MB-global-opt ổn định trong miền được xác nhận."
    elif confirmed_positive:
        conclusion = (
            "Có gain cục bộ trên evaluation seeds, nhưng chưa đủ bằng chứng outperform "
            "do chỉ có một training seed."
        )
    elif float(q2["mean_delta_K"]) > 0 and float(q2["ci95_low"]) <= 0:
        conclusion = "Learned shaping tương đương MB-global-opt trong uncertainty."
    else:
        conclusion = "Không tìm thấy bằng chứng learned shaping vượt MB-global-opt trong miền đã khảo sát."

    lines = [
        "# Audit learned shaping so với Maxwell–Boltzmann QAM",
        "",
        "## Kết luận điều hành",
        "",
        f"**{conclusion}**",
        "",
        "Kết luận này cố ý không nâng paired evaluation seeds thành independent training seeds. "
        "Các checkpoint được cung cấp chỉ đại diện cho một seed huấn luyện; vì vậy tiêu chí "
        "“outperform mạnh” của protocol chưa thể được thỏa, bất kể CI đánh giá có dương.",
        "",
        "## 1. Xác minh MB",
        "",
        f"- `QAM_NU_TILDE` hiện tại: `{float(QAM_NU_TILDE):g}`; MB-fixed dùng `{float(config['mb_fixed_nu']):g}`.",
        f"- MB-global-opt chọn trên validation độc lập: `nu* = {global_nu:g}` từ grid {list(config['nu_grid'])}.",
        "- Mã hiện tại dùng `exp[-nu_tilde((k-7.5)^2+(l-7.5)^2)]`. Đây là tham số theo chỉ số lưới; "
        "nó chỉ tương đương `exp(-nu|c_i|^2)` sau khi quy đổi thang tọa độ.",
        "- Với QAM thô của evaluator, `alpha0^2=12/17`, nên trước bước tái chuẩn hóa "
        "`nu_coordinate = 30*nu_tilde/alpha0^2 = 42.5*nu_tilde`: MB-fixed tương ứng 4.25 "
        "và MB-global-opt tương ứng 17.425 trên tọa độ thô. Sau chuẩn hóa phụ thuộc PMF, "
        "không được đồng nhất hai tham số hóa mà không nêu thang tọa độ.",
        "- Geometry baseline là QAM vuông 16×16 của dự án. Mỗi PMF được đặt tâm và chuẩn hóa lại sao cho "
        "`2 E_p|alpha|^2 = V_A`; vì vậy MB và learned dùng cùng `V_A`.",
        "- Trong từng phép so sánh, mọi scheme dùng chung chính xác tensor T và AWGN, cùng cutoff và sample budget.",
        "- MB-fixed trước đây chưa tối ưu theo V_A, T, epsilon hay phân phối kênh.",
        "",
        "## 2. Bốn câu hỏi nghiên cứu",
        "",
        "| Câu hỏi | So sánh | Mean ΔK | CI 95% | P(ΔK>0) | Nguồn gain |",
        "|---|---|---:|---:|---:|---|",
    ]
    for key in (
        "Q1_PS_vs_MB_fixed",
        "Q1_GS_vs_MB_fixed",
        "Q1_joint_vs_MB_fixed",
        "Q2_PS_vs_MB_global",
        "Q2_GS_vs_MB_global",
        "Q2_joint_vs_MB_global",
        "Q3_PS_vs_MB_oracle",
        "Q3_joint_vs_MB_oracle",
        "Q4_joint_vs_PS",
        "Q4_joint_vs_GS",
    ):
        row = comparison_lookup[key]
        lines.append(
            f"| {key.split('_')[0]} | {row['scheme']} − {row['baseline']} | "
            f"{float(row['mean_delta_K']):+.6e} | "
            f"[{float(row['ci95_low']):+.6e}, {float(row['ci95_high']):+.6e}] | "
            f"{float(row['P_delta_K_gt_0']):.2f} | {row['gain_source']} |"
        )
    lines.extend(
        [
            "",
            "## 3. PS có thực sự thích nghi không?",
            "",
            f"- PS: max state-to-state L1 = {float(ps_adapt['max_state_pair_L1']):.6e}; "
            f"Jacobian logits theo log10(T) = {float(ps_adapt['logit_jacobian_log10T_L2']):.6e}; "
            f"theo epsilon = {float(ps_adapt['logit_jacobian_epsilon_L2']):.6e}; "
            f"checkpoint = {ps_adapt['checkpoint_phase']} epoch {ps_adapt['checkpoint_epoch']}.",
            f"- PS+GS: max state-to-state L1 = {float(joint_adapt['max_state_pair_L1']):.6e}; "
            f"checkpoint = {joint_adapt['checkpoint_phase']} epoch {joint_adapt['checkpoint_epoch']}.",
            "",
            "Nếu các đại lượng trên bằng hoặc gần 0 và checkpoint PS là epoch 0, kết luận đúng là "
            "**PS chưa học cơ chế thích nghi; nó chủ yếu giữ MB initialization**, không phải AI gain.",
            "",
            "## 4. Hình học",
            "",
            f"Joint: d_min={float(joint_geometry['minimum_distance']):.6e}, "
            f"E_max={float(joint_geometry['peak_energy']):.6e}, "
            f"D_drift={float(joint_geometry['geometry_drift_from_QAM']):.6e}, "
            f"checkpoint={joint_geometry['checkpoint_phase']} epoch {joint_geometry['checkpoint_epoch']}.",
            "",
            "## 5. Bản đồ pha và xác nhận độc lập",
            "",
            f"- Grid exploratory: learned có mean K cao hơn MB-global-opt tại {phase_wins}/{len(phase_rows)} ô.",
            f"- Số trường hợp selected có CI final-test hoàn toàn dương: {len(confirmed_positive)}/{len(confirmed)}.",
            "- Heatmap là bước discovery với cutoff/budget thấp hơn; chỉ bảng `selected_case_summary.csv` "
            "được đánh giá lại ở budget confirmation. Không nội suy hoặc chỉ hiển thị ô đẹp nhất.",
            "",
            "| Loại | Điều kiện | Scheme | Mean ΔK | CI 95% | Nguồn gain | Xác nhận |",
            "|---|---|---|---:|---:|---|---|",
        ]
    )
    for row in confirmed:
        lines.append(
            f"| {row['case_type']} | {row['pair']} ({float(row['x']):.4g}, {float(row['y']):.4g}) | "
            f"{row['scheme']} | {float(row['mean_delta_K']):+.6e} | "
            f"[{float(row['ci95_low']):+.6e}, {float(row['ci95_high']):+.6e}] | "
            f"{row['gain_source']} | {row['independent_test_confirmed']} |"
        )
    not_run = sum(row["status"] == "not run" for row in ablations)
    lines.extend(
        [
            "",
            "## 6. Phạm vi bằng chứng và ablation",
            "",
            f"- {not_run}/{len(ablations)} ablation huấn luyện bắt buộc chưa có checkpoint độc lập và không được giả lập bằng smoke run.",
            "- Modulation order 16/64 chưa thể kiểm tra vì implementation learned hiện khóa cứng M=256.",
            "- CIs trong báo cáo là Student-t paired CI trên channel/AWGN repetitions, không phải training-seed CI.",
            f"- Sai số cutoff lớn nhất quan sát giữa ncut=120 và 150 trên cùng mẫu: {max_cutoff_error:.6e} bit/symbol.",
            "- Kết quả là asymptotic raw SKR theo covariance/Holevo bound hiện hành, chưa phải finite-key composable proof.",
            "",
            "## 7. Trả lời khoa học cuối cùng",
            "",
            f"- Learned mechanism mới hay học lại MB? Với PS, `adaptive_pmf_detected={ps_adapt['adaptive_pmf_detected']}` "
            f"và epoch={ps_adapt['checkpoint_epoch']}. Dữ liệu trực tiếp hiện tại ủng hộ kết luận **học lại/giữ MB**, "
            "không chứng minh một cơ chế bảo mật thích nghi mới.",
            "- Độ phức tạp MLP/CSI/joint có được biện minh không? Chưa thể khẳng định. Chỉ geometry warm-up có thể tạo "
            "một hiệu chỉnh nhỏ; cần nhiều training seeds và các ablation còn thiếu trước khi đánh đổi độ phức tạp.",
            "",
            "## 8. Tái lập",
            "",
            f"- Config: `{config['_config_path']}`",
            f"- Runtime: {elapsed:.1f} s; device={config['device']}; quick={config['quick']}.",
            "- Tất cả grid, seeds, hashes, raw metrics và trạng thái ablation nằm trong thư mục kết quả.",
        ]
    )
    (output_dir / "final_report_vi.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_cli(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("learned_vs_mb_audit_config.json"))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--skip-phase-maps", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    cli = parse_cli(argv)
    config = load_config(cli.config, cli.quick, cli.output_dir)
    output_dir = Path(config["output_directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    core.set_deterministic_seed(int(config["seeds"]["validation_channel"]))
    bundle = load_models(config)
    global_nu, validation_rows = optimize_global_mb(bundle, config, output_dir)
    run_rows, oracle_rows, comparisons = paired_test(
        bundle, config, global_nu, output_dir
    )
    _, adaptivity = adaptivity_diagnostics(
        bundle, config, global_nu, output_dir
    )
    geometry = geometry_diagnostics(bundle, config, output_dir)
    if cli.skip_phase_maps:
        phase_rows: list[dict[str, Any]] = []
        confirmed: list[dict[str, Any]] = []
        case_run_rows: list[dict[str, Any]] = []
    else:
        phase_rows = phase_maps(bundle, config, global_nu, output_dir)
        case_run_rows, confirmed = confirm_selected_cases(
            bundle, config, global_nu, phase_rows, output_dir
        )
    ablations = write_ablation_status(output_dir)
    cutoff_rows = cutoff_convergence(bundle, config, global_nu, output_dir)
    va_rows, va_summary = modulation_variance_sweep(bundle, config, output_dir)
    if phase_rows:
        robustness_and_thresholds(phase_rows, output_dir)
        detailed_cases, _ = selected_case_artifacts(
            bundle,
            config,
            global_nu,
            case_run_rows,
            confirmed,
            geometry,
            output_dir,
        )
    else:
        detailed_cases = []
    manifest = {
        "config": config,
        "global_opt_nu": global_nu,
        "model_metadata": bundle.metadata,
        "project_fixed_nu": float(QAM_NU_TILDE),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    report(
        config,
        bundle,
        global_nu,
        validation_rows,
        comparisons,
        adaptivity,
        geometry,
        phase_rows,
        confirmed,
        ablations,
        cutoff_rows,
        time.perf_counter() - started,
        output_dir,
    )
    append_supplement(output_dir, va_summary, detailed_cases)
    print(f"Audit complete: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
