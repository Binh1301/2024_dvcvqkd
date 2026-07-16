#!/usr/bin/env python3
"""Reproducible UAV-HAP CV-QKD secret-key-rate parameter sweeps.

This script loads validated GS, PS, and PS+GS checkpoints and compares them
with the project's exact Uniform, Maxwell-Boltzmann, and Binomial 256-QAM
symbol distributions. Rayleigh appears only inside the existing channel model
as beam-displacement fading; it is never treated as a symbol PMF here.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.ticker import LogFormatterSciNotation
from scipy.stats import t as student_t

import uav_hap_joint_ps_gs as core


SCHEME_ORDER = (
    "Uniform QAM",
    "Maxwell-Boltzmann QAM",
    "Binomial QAM",
    "GS",
    "PS",
    "PS+GS",
)

SCHEME_STYLES: dict[str, dict[str, Any]] = {
    "Uniform QAM": {"color": "#6C757D", "linestyle": "--", "marker": "o", "linewidth": 1.9},
    "Maxwell-Boltzmann QAM": {"color": "#8C6D31", "linestyle": "-.", "marker": "s", "linewidth": 1.9},
    "Binomial QAM": {"color": "#4C78A8", "linestyle": ":", "marker": "v", "linewidth": 2.0},
    "GS": {"color": "#D17C1F", "linestyle": "--", "marker": "D", "linewidth": 2.0},
    "PS": {"color": "#2F6690", "linestyle": "-", "marker": "^", "linewidth": 2.1},
    "PS+GS": {"color": "#158078", "linestyle": "-", "marker": "P", "linewidth": 2.5},
}

RAW_FIELDS = (
    "parameter_name",
    "parameter_value",
    "parameter_unit",
    "scheme",
    "repetition",
    "I_AB",
    "chi_BE",
    "beta_I_AB",
    "K_raw",
    "K_positive",
    "ncut",
    "seed",
    "channel_seed",
    "awgn_seed",
    "fading_samples",
    "awgn_samples",
    "channel_sample_hash",
    "awgn_sample_hash",
    "checkpoint",
)

SUMMARY_FIELDS = (
    "parameter_name",
    "parameter_value",
    "parameter_unit",
    "scheme",
    "mean_I_AB",
    "std_I_AB",
    "mean_chi_BE",
    "std_chi_BE",
    "mean_beta_I_AB",
    "std_beta_I_AB",
    "mean_K_raw",
    "std_K_raw",
    "mean_K_positive",
    "std_K_positive",
    "ci95_low",
    "ci95_high",
    "repetitions",
    "ncut",
)

DELTA_FIELDS = (
    "parameter_name",
    "parameter_value",
    "parameter_unit",
    "repetition",
    "seed",
    "Delta_K_PS_vs_Uniform",
    "Delta_K_GS_vs_Uniform",
    "Delta_K_PS+GS_vs_PS",
)


@dataclass(frozen=True)
class SweepSpec:
    key: str
    parameter_name: str
    unit: str
    channel_field: str | None
    raw_filename: str
    figure_stem: str
    x_label: str
    logarithmic: bool = False


SWEEP_SPECS: dict[str, SweepSpec] = {
    "aperture": SweepSpec(
        "aperture",
        "aperture_radius",
        "m",
        "a_m",
        "skr_vs_aperture_radius.csv",
        "skr_vs_aperture_radius",
        r"Receiver aperture radius $a$ [m]",
    ),
    "visibility": SweepSpec(
        "visibility",
        "visibility",
        "km",
        "visibility_km",
        "skr_vs_visibility.csv",
        "skr_vs_visibility",
        r"Atmospheric visibility $V$ [km]",
    ),
    "beam_waist": SweepSpec(
        "beam_waist",
        "beam_waist",
        "m",
        "W0_m",
        "skr_vs_beam_waist.csv",
        "skr_vs_beam_waist",
        r"Transmitter beam waist $W_0$ [m]",
    ),
    "turbulence": SweepSpec(
        "turbulence",
        "turbulence_strength",
        "m^(-2/3)",
        "Cn2",
        "skr_vs_turbulence.csv",
        "skr_vs_turbulence",
        r"Turbulence strength $C_n^2$ [m$^{-2/3}$]",
        logarithmic=True,
    ),
    "excess_noise": SweepSpec(
        "excess_noise",
        "excess_noise",
        "SNU",
        None,
        "skr_vs_excess_noise.csv",
        "skr_vs_excess_noise",
        r"Excess noise $\xi$ [SNU]",
    ),
}


@dataclass
class SchemeBundle:
    models: dict[str, core.JointPSGS256QAM]
    checkpoint_paths: dict[str, Path]
    checkpoint_metadata: dict[str, dict[str, Any]]
    state_before: dict[str, dict[str, torch.Tensor]]
    base_qam: torch.Tensor
    core_args: argparse.Namespace
    device: torch.device


@dataclass
class PipelineResult:
    output_dir: Path
    raw_rows: dict[str, list[dict[str, Any]]]
    summary_rows: list[dict[str, Any]]
    delta_rows: list[dict[str, Any]]
    convergence_rows: list[dict[str, Any]]
    figure_paths: list[Path]
    report_path: Path
    plot_xscales: dict[str, str]


def resolve_path(value: str | Path, base_dir: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base_dir / path).resolve()


def load_config(path: Path, quick: bool = False, output_override: Path | None = None) -> dict[str, Any]:
    config_path = path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["_config_path"] = str(config_path)
    config["_config_dir"] = str(config_path.parent)
    config["baseline_project_config"] = str(
        resolve_path(config["baseline_project_config"], config_path.parent)
    )
    config["checkpoints"] = {
        key: str(resolve_path(value, config_path.parent))
        for key, value in config["checkpoints"].items()
    }
    configured_output = resolve_path(config["output_directory"], config_path.parent)
    if quick:
        configured_output = configured_output.with_name(configured_output.name + "_quick")
        config["quick_mode"] = True
        config["repetitions"] = 2
        config["seed_list"] = list(config["seed_list"][:2])
        config["fading_sample_budget"] = 2
        config["awgn_sample_budget"] = 2
        config["ncut"] = min(int(config["ncut"]), 24)
        config["ncut_convergence"]["comparison_ncut"] = min(
            int(config["ncut_convergence"]["comparison_ncut"]), 20
        )
        config["ncut_convergence"]["fading_samples"] = 1
        config["ncut_convergence"]["awgn_samples"] = 2
        for sweep in config["sweeps"].values():
            sweep["points"] = 2
    else:
        config["quick_mode"] = False
    if output_override is not None:
        configured_output = output_override.resolve()
    config["output_directory"] = str(configured_output)
    validate_config(config)
    return config


def validate_config(config: Mapping[str, Any]) -> None:
    if int(config["modulation_order"]) != core.SYMBOL_COUNT:
        raise ValueError(f"Only {core.SYMBOL_COUNT}-QAM is supported by the trained models.")
    if int(config["repetitions"]) <= 0:
        raise ValueError("repetitions must be positive.")
    if len(config["seed_list"]) < int(config["repetitions"]):
        raise ValueError("seed_list must contain at least repetitions entries.")
    if int(config["ncut"]) <= 1:
        raise ValueError("ncut must exceed one.")
    for key in SWEEP_SPECS:
        if key not in config["sweeps"]:
            raise ValueError(f"Missing sweep configuration: {key}")
        sweep = config["sweeps"][key]
        if int(sweep["points"]) <= 0:
            raise ValueError(f"Sweep {key} must contain at least one point.")
        if float(sweep["minimum"]) > float(sweep["maximum"]):
            raise ValueError(f"Sweep {key} minimum exceeds maximum.")
    required_checkpoints = {"gs", "ps", "joint"}
    if set(config["checkpoints"]) != required_checkpoints:
        raise ValueError(f"checkpoints must contain exactly {sorted(required_checkpoints)}.")


def load_scheme_checkpoints(config: Mapping[str, Any]) -> SchemeBundle:
    device = torch.device(str(config.get("device", "cpu")))
    core_args = core.parse_args(["--config", str(config["baseline_project_config"])])
    base_qam = core.build_project_qam(device)
    models: dict[str, core.JointPSGS256QAM] = {}
    checkpoint_paths: dict[str, Path] = {}
    metadata: dict[str, dict[str, Any]] = {}
    state_before: dict[str, dict[str, torch.Tensor]] = {}
    mappings = (("GS", "gs"), ("PS", "ps"), ("PS+GS", "joint"))
    for display_name, mode in mappings:
        checkpoint_path = Path(str(config["checkpoints"][mode])).resolve()
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Missing {mode} checkpoint: {checkpoint_path}")
        model = core.create_model(mode, base_qam, core_args)
        payload = core.load_training_checkpoint(checkpoint_path, model, restore_rng=False)
        if str(payload.get("model_mode")) != mode:
            raise ValueError(
                f"Checkpoint {checkpoint_path} reports mode {payload.get('model_mode')!r}, "
                f"expected {mode!r}."
            )
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        models[display_name] = model
        checkpoint_paths[display_name] = checkpoint_path
        metadata[display_name] = {
            "mode": mode,
            "epoch": int(payload.get("epoch", -1)),
            "phase": str(payload.get("phase", "unknown")),
        }
        state_before[display_name] = {
            key: value.detach().cpu().clone() for key, value in model.state_dict().items()
        }
    return SchemeBundle(
        models=models,
        checkpoint_paths=checkpoint_paths,
        checkpoint_metadata=metadata,
        state_before=state_before,
        base_qam=base_qam,
        core_args=core_args,
        device=device,
    )


def assert_models_unchanged(bundle: SchemeBundle) -> None:
    for name, model in bundle.models.items():
        current = model.state_dict()
        for key, expected in bundle.state_before[name].items():
            if not torch.equal(current[key].detach().cpu(), expected):
                raise AssertionError(f"Visualization modified {name} parameter or buffer {key!r}.")


def build_scheme_outputs(
    bundle: SchemeBundle,
    transmittance: torch.Tensor,
    epsilon: float,
) -> dict[str, core.ModelOutput]:
    outputs = {
        "Uniform QAM": core.model_output_for_baseline(
            "uniform", transmittance, bundle.base_qam, bundle.core_args.va
        ),
        "Maxwell-Boltzmann QAM": core.model_output_for_baseline(
            "mb", transmittance, bundle.base_qam, bundle.core_args.va
        ),
        "Binomial QAM": core.model_output_for_baseline(
            "binomial", transmittance, bundle.base_qam, bundle.core_args.va
        ),
    }
    for name in ("GS", "PS", "PS+GS"):
        outputs[name] = bundle.models[name](transmittance, epsilon)
    if tuple(outputs) != SCHEME_ORDER:
        raise AssertionError("Scheme order changed unexpectedly.")
    return outputs


def verify_energy_normalization(outputs: Mapping[str, core.ModelOutput], atol: float = 5e-10) -> None:
    for name, output in outputs.items():
        weighted_mean = torch.sum(output.probabilities * output.unit_constellation, dim=-1)
        weighted_energy = torch.sum(
            output.probabilities * output.unit_constellation.abs().square(), dim=-1
        )
        probability_sum = output.probabilities.sum(dim=-1)
        if not torch.allclose(probability_sum, torch.ones_like(probability_sum), atol=atol, rtol=0.0):
            raise AssertionError(f"{name}: probabilities do not sum to one.")
        if float(weighted_mean.abs().max()) > atol:
            raise AssertionError(f"{name}: weighted constellation mean is nonzero.")
        if not torch.allclose(weighted_energy, torch.ones_like(weighted_energy), atol=atol, rtol=0.0):
            raise AssertionError(f"{name}: weighted constellation energy is not one.")


def tensor_hash(tensor: torch.Tensor) -> str:
    array = np.ascontiguousarray(tensor.detach().cpu().numpy())
    return hashlib.sha256(array.tobytes()).hexdigest()[:16]


def build_geometry(config: Mapping[str, Any]) -> core.GeometryParams:
    return core.GeometryParams(**dict(config.get("baseline_geometry", {})))


def build_channel_parameters(config: Mapping[str, Any]) -> core.ChannelParams:
    return core.ChannelParams(**dict(config["baseline_channel_parameters"]))


def sweep_values(config: Mapping[str, Any], sweep_key: str) -> np.ndarray:
    sweep = config["sweeps"][sweep_key]
    minimum = float(sweep["minimum"])
    maximum = float(sweep["maximum"])
    points = int(sweep["points"])
    scale = str(sweep.get("scale", "linear"))
    if scale == "log":
        values = np.logspace(np.log10(minimum), np.log10(maximum), points)
    elif scale == "linear":
        values = np.linspace(minimum, maximum, points)
    else:
        raise ValueError(f"Unsupported scale {scale!r} for sweep {sweep_key}.")
    return np.sort(values.astype(np.float64))


def common_samples(
    geometry: core.GeometryParams,
    channel_parameters: core.ChannelParams,
    fading_samples: int,
    awgn_samples: int,
    channel_seed: int,
    awgn_seed: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, str, str]:
    channel_result = core.channel(
        geometry,
        channel_parameters,
        N=int(fading_samples),
        rng=np.random.default_rng(int(channel_seed)),
    )
    transmittance = torch.as_tensor(
        np.asarray(channel_result["T_samples"], dtype=np.float64),
        dtype=core.REAL_DTYPE,
        device=device,
    )
    standard_noise = core.make_standard_complex_noise(
        transmittance.numel(),
        core.SYMBOL_COUNT,
        int(awgn_samples),
        core.tensor_generator(int(awgn_seed), device),
        device,
    )
    return transmittance, standard_noise, tensor_hash(transmittance), tensor_hash(standard_noise)


def evaluate_scheme(
    name: str,
    output: core.ModelOutput,
    transmittance: torch.Tensor,
    standard_noise: torch.Tensor,
    epsilon: float,
    config: Mapping[str, Any],
) -> dict[str, float]:
    evaluation = core.evaluate_output(
        name,
        output,
        transmittance,
        epsilon,
        float(config["beta"]),
        int(config["ncut"]),
        int(config["awgn_sample_budget"]),
        standard_noise,
        int(config["candidate_chunk_size"]),
        float(config["modulation_variance"]),
    )
    positive = torch.clamp(evaluation.raw_skr, min=0.0)
    metrics = {
        "I_AB": float(evaluation.i_ab.mean()),
        "chi_BE": float(evaluation.security.chi_be.mean()),
        "beta_I_AB": float((float(config["beta"]) * evaluation.i_ab).mean()),
        "K_raw": float(evaluation.raw_skr.mean()),
        "K_positive": float(positive.mean()),
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        raise FloatingPointError(f"Non-finite metrics for {name}: {metrics}")
    return metrics


def parameter_context(
    config: Mapping[str, Any],
    sweep_key: str,
    parameter_value: float,
) -> tuple[core.ChannelParams, float]:
    spec = SWEEP_SPECS[sweep_key]
    channel_parameters = build_channel_parameters(config)
    epsilon = float(config["baseline_excess_noise_snu"])
    if spec.channel_field is None:
        epsilon = float(parameter_value)
    else:
        channel_parameters = replace(
            channel_parameters,
            **{spec.channel_field: float(parameter_value)},
        )
    return channel_parameters, epsilon


def evaluate_parameter_point(
    bundle: SchemeBundle,
    config: Mapping[str, Any],
    sweep_key: str,
    parameter_value: float,
    point_index: int,
    repetition: int,
) -> list[dict[str, Any]]:
    spec = SWEEP_SPECS[sweep_key]
    base_seed = int(config["seed_list"][repetition])
    sweep_offset = list(SWEEP_SPECS).index(sweep_key) * 1_000_000
    channel_seed = base_seed + sweep_offset + point_index * 10_000
    awgn_seed = channel_seed + 1
    channel_parameters, epsilon = parameter_context(config, sweep_key, parameter_value)
    transmittance, standard_noise, channel_hash, awgn_hash = common_samples(
        build_geometry(config),
        channel_parameters,
        int(config["fading_sample_budget"]),
        int(config["awgn_sample_budget"]),
        channel_seed,
        awgn_seed,
        bundle.device,
    )
    with torch.inference_mode():
        outputs = build_scheme_outputs(bundle, transmittance, epsilon)
        verify_energy_normalization(outputs)
        rows: list[dict[str, Any]] = []
        for name in SCHEME_ORDER:
            metrics = evaluate_scheme(
                name,
                outputs[name],
                transmittance,
                standard_noise,
                epsilon,
                config,
            )
            checkpoint = "fixed project PMF"
            if name in bundle.checkpoint_paths:
                checkpoint = str(bundle.checkpoint_paths[name])
            row = {
                "parameter_name": spec.parameter_name,
                "parameter_value": float(parameter_value),
                "parameter_unit": spec.unit,
                "scheme": name,
                "repetition": repetition,
                **metrics,
                "ncut": int(config["ncut"]),
                "seed": base_seed,
                "channel_seed": channel_seed,
                "awgn_seed": awgn_seed,
                "fading_samples": int(config["fading_sample_budget"]),
                "awgn_samples": int(config["awgn_sample_budget"]),
                "channel_sample_hash": channel_hash,
                "awgn_sample_hash": awgn_hash,
                "checkpoint": checkpoint,
            }
            rows.append(row)
            print(
                f"[{sweep_key:12s}] point {point_index + 1:2d} "
                f"value={parameter_value:.6g} rep={repetition + 1} "
                f"scheme={name:<24s} I_AB={metrics['I_AB']:.6e} "
                f"chi_BE={metrics['chi_BE']:.6e} K_raw={metrics['K_raw']:+.6e}",
                flush=True,
            )
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def run_parameter_sweep(
    bundle: SchemeBundle,
    config: Mapping[str, Any],
    sweep_key: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    values = sweep_values(config, sweep_key)
    repetitions = int(config["repetitions"])
    started = time.perf_counter()
    print(f"\nStarting {sweep_key} sweep: {len(values)} points x {repetitions} repetitions")
    for point_index, parameter_value in enumerate(values):
        for repetition in range(repetitions):
            rows.extend(
                evaluate_parameter_point(
                    bundle,
                    config,
                    sweep_key,
                    float(parameter_value),
                    point_index,
                    repetition,
                )
            )
        write_csv(output_dir / SWEEP_SPECS[sweep_key].raw_filename, rows, RAW_FIELDS)
    print(f"Completed {sweep_key} sweep in {time.perf_counter() - started:.1f} s")
    return rows


def sample_std(values: np.ndarray) -> float:
    return float(values.std(ddof=1)) if values.size > 1 else 0.0


def compute_student_t_ci(values: Sequence[float], confidence: float = 0.95) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        raise ValueError("Cannot compute a confidence interval for no values.")
    mean = float(array.mean())
    if array.size == 1:
        return mean, mean
    standard_error = sample_std(array) / math.sqrt(array.size)
    critical = float(student_t.ppf(0.5 + confidence / 2.0, df=array.size - 1))
    half_width = critical * standard_error
    return mean - half_width, mean + half_width


def aggregate_repetitions(raw_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, float, str, str], list[Mapping[str, Any]]] = {}
    for row in raw_rows:
        key = (
            str(row["parameter_name"]),
            float(row["parameter_value"]),
            str(row["parameter_unit"]),
            str(row["scheme"]),
        )
        groups.setdefault(key, []).append(row)
    summary: list[dict[str, Any]] = []
    for (parameter_name, value, unit, scheme), rows in groups.items():
        arrays = {
            field: np.asarray([float(row[field]) for row in rows], dtype=np.float64)
            for field in ("I_AB", "chi_BE", "beta_I_AB", "K_raw", "K_positive")
        }
        ci_low, ci_high = compute_student_t_ci(arrays["K_positive"])
        summary.append(
            {
                "parameter_name": parameter_name,
                "parameter_value": value,
                "parameter_unit": unit,
                "scheme": scheme,
                "mean_I_AB": float(arrays["I_AB"].mean()),
                "std_I_AB": sample_std(arrays["I_AB"]),
                "mean_chi_BE": float(arrays["chi_BE"].mean()),
                "std_chi_BE": sample_std(arrays["chi_BE"]),
                "mean_beta_I_AB": float(arrays["beta_I_AB"].mean()),
                "std_beta_I_AB": sample_std(arrays["beta_I_AB"]),
                "mean_K_raw": float(arrays["K_raw"].mean()),
                "std_K_raw": sample_std(arrays["K_raw"]),
                "mean_K_positive": float(arrays["K_positive"].mean()),
                "std_K_positive": sample_std(arrays["K_positive"]),
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "repetitions": len(rows),
                "ncut": int(rows[0]["ncut"]),
            }
        )
    scheme_rank = {name: index for index, name in enumerate(SCHEME_ORDER)}
    summary.sort(
        key=lambda row: (
            row["parameter_name"],
            float(row["parameter_value"]),
            scheme_rank[str(row["scheme"])],
        )
    )
    return summary


def compute_delta_rows(raw_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, float, str, int, int], dict[str, Mapping[str, Any]]] = {}
    for row in raw_rows:
        key = (
            str(row["parameter_name"]),
            float(row["parameter_value"]),
            str(row["parameter_unit"]),
            int(row["repetition"]),
            int(row["seed"]),
        )
        groups.setdefault(key, {})[str(row["scheme"])] = row
    deltas: list[dict[str, Any]] = []
    for (parameter_name, value, unit, repetition, seed), schemes in groups.items():
        missing = set(SCHEME_ORDER).difference(schemes)
        if missing:
            raise ValueError(f"Cannot compute paired deltas; missing schemes: {sorted(missing)}")
        positive = {name: float(row["K_positive"]) for name, row in schemes.items()}
        deltas.append(
            {
                "parameter_name": parameter_name,
                "parameter_value": value,
                "parameter_unit": unit,
                "repetition": repetition,
                "seed": seed,
                "Delta_K_PS_vs_Uniform": positive["PS"] - positive["Uniform QAM"],
                "Delta_K_GS_vs_Uniform": positive["GS"] - positive["Uniform QAM"],
                "Delta_K_PS+GS_vs_PS": positive["PS+GS"] - positive["PS"],
            }
        )
    return sorted(
        deltas,
        key=lambda row: (
            row["parameter_name"],
            float(row["parameter_value"]),
            int(row["repetition"]),
        ),
    )


def configure_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 10,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "axes.linewidth": 0.8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def plot_skr_comparison(
    summary_rows: Sequence[Mapping[str, Any]],
    sweep_key: str,
    output_dir: Path,
    config: Mapping[str, Any],
) -> tuple[list[Path], str]:
    spec = SWEEP_SPECS[sweep_key]
    parameter_rows = [row for row in summary_rows if row["parameter_name"] == spec.parameter_name]
    if not parameter_rows:
        raise ValueError(f"No summary rows found for {sweep_key}.")
    figure, axis = plt.subplots(figsize=(6.7, 4.4))
    markevery = max(1, int(config["sweeps"][sweep_key]["points"]) // 7)
    plotted_field = "mean_K_positive" if bool(config["plot_positive_skr"]) else "mean_K_raw"
    for scheme in SCHEME_ORDER:
        rows = sorted(
            (row for row in parameter_rows if row["scheme"] == scheme),
            key=lambda row: float(row["parameter_value"]),
        )
        x = np.asarray([float(row["parameter_value"]) for row in rows])
        y = np.asarray([float(row[plotted_field]) for row in rows])
        low = np.asarray([float(row["ci95_low"]) for row in rows])
        high = np.asarray([float(row["ci95_high"]) for row in rows])
        style = SCHEME_STYLES[scheme]
        axis.plot(
            x,
            y,
            label=scheme,
            color=style["color"],
            linestyle=style["linestyle"],
            linewidth=style["linewidth"],
            marker=style["marker"],
            markersize=5.2 if scheme != "PS+GS" else 6.0,
            markevery=markevery,
        )
        if bool(config["show_confidence_bands"]):
            axis.fill_between(
                x,
                np.maximum(low, 0.0) if bool(config["plot_positive_skr"]) else low,
                high,
                color=style["color"],
                alpha=0.08,
                linewidth=0.0,
            )
    axis.set_xlabel(spec.x_label)
    axis.set_ylabel("Positive secret-key rate [bit/symbol]" if config["plot_positive_skr"] else "Raw secret-key rate [bit/symbol]")
    if spec.logarithmic:
        axis.set_xscale("log")
        axis.xaxis.set_major_formatter(LogFormatterSciNotation())
    axis.grid(True, which="major", color="#D9DDE0", linewidth=0.7, alpha=0.8)
    axis.legend(loc="best", ncol=2)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    paths: list[Path] = []
    for output_format in config["output_formats"]:
        path = output_dir / f"{spec.figure_stem}.{output_format}"
        save_kwargs = {"bbox_inches": "tight"}
        if output_format.lower() == "png":
            save_kwargs["dpi"] = int(config["dpi"])
        figure.savefig(path, **save_kwargs)
        paths.append(path)
    xscale = axis.get_xscale()
    plt.close(figure)
    return paths, xscale


def verify_full_ncut_convergence(
    bundle: SchemeBundle,
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    settings = config["ncut_convergence"]
    cutoffs = sorted({int(settings["comparison_ncut"]), int(config["ncut"])})
    seed = int(config["seed_list"][0]) + 9_000_000
    transmittance, noise, _, _ = common_samples(
        build_geometry(config),
        build_channel_parameters(config),
        int(settings["fading_samples"]),
        int(settings["awgn_samples"]),
        seed,
        seed + 1,
        bundle.device,
    )
    epsilon = float(config["baseline_excess_noise_snu"])
    rows: list[dict[str, Any]] = []
    with torch.inference_mode():
        outputs = build_scheme_outputs(bundle, transmittance, epsilon)
        for cutoff in cutoffs:
            local_config = dict(config)
            local_config["ncut"] = cutoff
            local_config["awgn_sample_budget"] = int(settings["awgn_samples"])
            for scheme in SCHEME_ORDER:
                metrics = evaluate_scheme(
                    scheme,
                    outputs[scheme],
                    transmittance,
                    noise,
                    epsilon,
                    local_config,
                )
                rows.append({"ncut": cutoff, "scheme": scheme, **metrics})
    final = {
        row["scheme"]: row for row in rows if int(row["ncut"]) == int(config["ncut"])
    }
    for row in rows:
        reference = final[row["scheme"]]
        row["abs_delta_K_raw_vs_full"] = abs(float(row["K_raw"]) - float(reference["K_raw"]))
    return rows


def paired_significance(delta_rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, float], tuple[float, float, float]]:
    groups: dict[tuple[str, float], list[float]] = {}
    for row in delta_rows:
        key = (str(row["parameter_name"]), float(row["parameter_value"]))
        groups.setdefault(key, []).append(float(row["Delta_K_PS+GS_vs_PS"]))
    result: dict[tuple[str, float], tuple[float, float, float]] = {}
    for key, values in groups.items():
        low, high = compute_student_t_ci(values)
        result[key] = (float(np.mean(values)), low, high)
    return result


def curve_crossings(summary_rows: Sequence[Mapping[str, Any]], parameter_name: str) -> list[str]:
    rows = [row for row in summary_rows if row["parameter_name"] == parameter_name]
    by_scheme = {
        scheme: sorted(
            (row for row in rows if row["scheme"] == scheme),
            key=lambda row: float(row["parameter_value"]),
        )
        for scheme in SCHEME_ORDER
    }
    crossings: list[str] = []
    for first_index, first in enumerate(SCHEME_ORDER):
        for second in SCHEME_ORDER[first_index + 1 :]:
            differences = np.asarray(
                [
                    float(a["mean_K_positive"]) - float(b["mean_K_positive"])
                    for a, b in zip(by_scheme[first], by_scheme[second])
                ]
            )
            signs = np.sign(differences)
            if np.any(signs[:-1] * signs[1:] < 0.0):
                crossings.append(f"{first} / {second}")
    return crossings


def physical_trend_messages(summary_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    expected = {
        "aperture_radius": 1,
        "visibility": 1,
        "turbulence_strength": -1,
        "excess_noise": -1,
    }
    messages: list[str] = []
    for parameter_name, direction in expected.items():
        rows = [
            row
            for row in summary_rows
            if row["parameter_name"] == parameter_name and row["scheme"] == "PS+GS"
        ]
        rows.sort(key=lambda row: float(row["parameter_value"]))
        differences = np.diff([float(row["mean_K_positive"]) for row in rows])
        if differences.size == 0:
            continue
        agreement = float(np.mean(direction * differences >= -1e-12))
        status = "consistent" if agreement >= 0.75 else "potentially inconsistent"
        messages.append(
            f"{parameter_name}: {status} with the expected general trend "
            f"({agreement:.0%} of adjacent PS+GS steps agree)."
        )
    messages.append(
        "beam_waist: no monotonic constraint was imposed; an interior optimum is physically plausible."
    )
    return messages


def write_report(
    path: Path,
    config: Mapping[str, Any],
    bundle: SchemeBundle,
    selected_sweeps: Sequence[str],
    summary_rows: Sequence[Mapping[str, Any]],
    delta_rows: Sequence[Mapping[str, Any]],
    convergence_rows: Sequence[Mapping[str, Any]],
) -> None:
    significance = paired_significance(delta_rows)
    lines = [
        "UAV-HAP CV-QKD SKR parameter-sweep visualization report",
        "========================================================",
        "",
        f"Run mode: {'QUICK PIPELINE VERIFICATION (not publication evidence)' if config['quick_mode'] else 'FULL CONFIGURATION'}",
        f"Plotted metric: {'K_positive = max(0, beta*I_AB-chi_BE)' if config['plot_positive_skr'] else 'K_raw = beta*I_AB-chi_BE'}",
        "Raw CSVs contain both K_raw and K_positive.",
        "Confidence interval: two-sided Student-t 95% interval over independent repetitions.",
        "Common random numbers: identical channel and AWGN samples are reused by all six schemes at each point/repetition.",
        "Rayleigh terminology: Rayleigh is channel beam-displacement fading only; the third fixed symbol PMF is the exact project Binomial PMF.",
        "",
        "Checkpoints",
        "-----------",
    ]
    for name in ("GS", "PS", "PS+GS"):
        metadata = bundle.checkpoint_metadata[name]
        lines.append(
            f"{name}: {bundle.checkpoint_paths[name]} "
            f"(mode={metadata['mode']}, phase={metadata['phase']}, epoch={metadata['epoch']})"
        )
    lines.extend(
        [
            "",
            "Fixed baseline parameters",
            "-------------------------",
            *[
                f"{key}: {value}"
                for key, value in config["baseline_channel_parameters"].items()
            ],
            f"excess_noise_snu: {config['baseline_excess_noise_snu']}",
            f"beta: {config['beta']}",
            f"modulation_order: {config['modulation_order']}",
            f"modulation_variance: {config['modulation_variance']}",
            f"detector assumptions: {config['detector_assumptions']}",
            f"ncut: {config['ncut']}",
            f"fading samples per repetition: {config['fading_sample_budget']}",
            f"AWGN samples per symbol: {config['awgn_sample_budget']}",
            f"repetition seeds: {config['seed_list'][:config['repetitions']]}",
            "",
            "Sweep definitions",
            "-----------------",
        ]
    )
    for key in selected_sweeps:
        sweep = config["sweeps"][key]
        lines.append(
            f"{key}: {sweep['minimum']} to {sweep['maximum']} {SWEEP_SPECS[key].unit}, "
            f"{sweep['points']} points, {sweep.get('scale', 'linear')} scale"
        )
    lines.extend(["", "Numerical results", "-----------------"])
    for key in selected_sweeps:
        spec = SWEEP_SPECS[key]
        rows = [row for row in summary_rows if row["parameter_name"] == spec.parameter_name]
        values = sorted({float(row["parameter_value"]) for row in rows})
        winner_counts = {scheme: 0 for scheme in SCHEME_ORDER}
        for value in values:
            candidates = [row for row in rows if float(row["parameter_value"]) == value]
            winner = max(candidates, key=lambda row: float(row["mean_K_positive"]))
            winner_counts[str(winner["scheme"])] += 1
        winners = ", ".join(
            f"{scheme} ({count}/{len(values)} points)"
            for scheme, count in winner_counts.items()
            if count
        )
        crossings = curve_crossings(summary_rows, spec.parameter_name)
        lines.append(f"{key}: highest mean K_positive -> {winners}")
        lines.append(
            f"{key}: curve crossings -> {', '.join(crossings) if crossings else 'none detected between evaluated points'}"
        )
        paired = [
            interval
            for (parameter_name, _), interval in significance.items()
            if parameter_name == spec.parameter_name
        ]
        consistently_better = bool(paired) and all(mean > 0.0 for mean, _, _ in paired)
        significantly_better = sum(low > 0.0 for _, low, _ in paired)
        lines.append(
            f"{key}: PS+GS exceeds PS at every evaluated point -> {consistently_better}; "
            f"paired 95% CI excludes zero positively at {significantly_better}/{len(paired)} points."
        )
    max_convergence_delta = max(
        (float(row["abs_delta_K_raw_vs_full"]) for row in convergence_rows),
        default=math.nan,
    )
    lines.extend(
        [
            "",
            "Validation and interpretation",
            "-----------------------------",
            f"Fock-cutoff comparison ncut={config['ncut_convergence']['comparison_ncut']} "
            f"versus ncut={config['ncut']}; maximum |Delta K_raw|: "
            f"{max_convergence_delta:.6e} bit/symbol.",
            *physical_trend_messages(summary_rows),
            "Numerical visualization results and paired evaluation-seed significance do not establish fundamental superiority.",
            "Independent training seeds are still required to quantify optimization uncertainty.",
            "No curve values were smoothed, interpolated, or forced to match expected physical trends.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(
    config: Mapping[str, Any],
    selected_sweeps: Sequence[str],
) -> PipelineResult:
    unknown = set(selected_sweeps).difference(SWEEP_SPECS)
    if unknown:
        raise ValueError(f"Unknown sweeps: {sorted(unknown)}")
    output_dir = Path(str(config["output_directory"])).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_plot_style()
    core.set_deterministic_seed(int(config["seed_list"][0]))
    bundle = load_scheme_checkpoints(config)

    raw_by_sweep: dict[str, list[dict[str, Any]]] = {}
    all_raw: list[dict[str, Any]] = []
    for sweep_key in selected_sweeps:
        rows = run_parameter_sweep(bundle, config, sweep_key, output_dir)
        raw_by_sweep[sweep_key] = rows
        all_raw.extend(rows)

    summary_rows = aggregate_repetitions(all_raw)
    delta_rows = compute_delta_rows(all_raw)
    write_csv(output_dir / "skr_parameter_sweep_summary.csv", summary_rows, SUMMARY_FIELDS)
    write_csv(output_dir / "skr_parameter_sweep_deltas.csv", delta_rows, DELTA_FIELDS)

    figure_paths: list[Path] = []
    plot_xscales: dict[str, str] = {}
    for sweep_key in selected_sweeps:
        paths, xscale = plot_skr_comparison(summary_rows, sweep_key, output_dir, config)
        figure_paths.extend(paths)
        plot_xscales[sweep_key] = xscale

    convergence_rows = verify_full_ncut_convergence(bundle, config)
    convergence_fields = (
        "ncut",
        "scheme",
        "I_AB",
        "chi_BE",
        "beta_I_AB",
        "K_raw",
        "K_positive",
        "abs_delta_K_raw_vs_full",
    )
    write_csv(output_dir / "ncut_convergence.csv", convergence_rows, convergence_fields)
    assert_models_unchanged(bundle)
    report_path = output_dir / "skr_visualization_report.txt"
    write_report(
        report_path,
        config,
        bundle,
        selected_sweeps,
        summary_rows,
        delta_rows,
        convergence_rows,
    )
    return PipelineResult(
        output_dir=output_dir,
        raw_rows=raw_by_sweep,
        summary_rows=summary_rows,
        delta_rows=delta_rows,
        convergence_rows=convergence_rows,
        figure_paths=figure_paths,
        report_path=report_path,
        plot_xscales=plot_xscales,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("skr_visualization_config.json"))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true", help="Run all five parameter sweeps.")
    selection.add_argument("--sweep", choices=tuple(SWEEP_SPECS))
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a reduced pipeline verification; outputs are labeled non-publication.",
    )
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config, quick=args.quick, output_override=args.output_dir)
    selected_sweeps = tuple(SWEEP_SPECS) if args.all else (args.sweep,)
    result = run_pipeline(config, selected_sweeps)
    print(f"\nCreated {len(result.figure_paths)} figure files in {result.output_dir}")
    print(f"Summary: {result.output_dir / 'skr_parameter_sweep_summary.csv'}")
    print(f"Report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
