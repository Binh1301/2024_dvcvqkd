"""Smoke fixed baselines with one full-support source-moment evaluation each."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

import torch

from _common import ROOT, load_yaml
from src.channel.geometry import LinkGeometry
from src.channel.state_distribution import (
    IndependentUniformExcessNoise,
    sample_channel_state_distribution,
)
from src.cvqkd.gram_moments import GramMomentResult, c4_gram_source_moments
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information
from src.cvqkd.protocol import validate_channel_state
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.optimization.constraints import ensemble_state_diagnostics
from src.utils.random import torch_generator


def load_experiment_config(path: Path, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8")) if path.suffix.lower() == ".json" else load_yaml(path)
    sections = ("channel", "modulation", "security", "simulation", "output")
    settings: dict[str, Any] = {key: raw[key] for key in ("experiment_name",) if key in raw}
    for section in sections:
        values = raw.get(section, {})
        if not isinstance(values, dict):
            raise ValueError(f"config section {section!r} must be a mapping")
        settings.update(values)
    settings.update({key: value for key, value in (overrides or {}).items() if value is not None})
    required = (
        "h_hap_m", "h_uav_m", "wavelength_m", "visibility_km", "beam_waist_m",
        "aperture_radius_m", "cn2", "epsilon_min", "epsilon_max", "va", "v_min",
        "v_max", "va_budget", "n_peak_photons", "beta", "mb_nu", "fading_samples",
        "awgn_samples", "channel_seed", "awgn_seed",
    )
    missing = [key for key in required if key not in settings]
    if missing:
        raise ValueError("missing required config values: " + ", ".join(missing))
    settings.setdefault("output_dir", ROOT / "results")
    settings.setdefault("checkpoint_each_scheme", True)
    settings.setdefault("schemes", ["uniform", "binomial", "mb"])
    return settings


def collect_run_metadata(config_path: Path, seeds: dict[str, Any]) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip())
    except OSError:
        print("warning: Git metadata unavailable; continuing in development mode", flush=True)
        commit, dirty = None, None
    try:
        config_value = config_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        config_value = str(config_path)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit or None,
        "git_dirty": dirty,
        "script": "scripts/run_baselines_cached_source_moments.py",
        "config_path": config_value,
        "seeds": dict(seeds),
    }


def checkpoint_matches(path: Path, config: dict[str, Any]) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("run_config") == config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "h-hap-m", "h-uav-m", "wavelength-m", "visibility-km", "beam-waist-m",
        "aperture-radius-m", "cn2", "epsilon-min", "epsilon-max", "va", "v-min", "v-max",
        "va-budget", "n-peak-photons", "beta",
    ):
        parser.add_argument(f"--{name}", type=float)
    parser.add_argument("--mb-nu", type=float)
    parser.add_argument("--fading-samples", type=int)
    parser.add_argument("--awgn-samples", type=int)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline_smoke.json")
    parser.add_argument("--channel-seed", type=int)
    parser.add_argument("--awgn-seed", type=int)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def _repeat_ensemble(source: Ensemble, batch_size: int) -> Ensemble:
    if source.probabilities.shape[0] != 1:
        raise ValueError("Cached fixed-baseline source must have batch_size=1.")
    return Ensemble(
        probabilities=source.probabilities.expand(batch_size, -1),
        amplitudes=source.amplitudes.expand(batch_size, -1),
        declared_va=source.declared_va.expand(batch_size),
        raw_constellation=source.raw_constellation,
        exact_csi_oracle=source.exact_csi_oracle,
        c4_symmetric=source.c4_symmetric,
    )


def evaluate_fixed_ensemble(
    source_ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    density_eigenvalue_tolerance: float,
    beta_reconciliation: float,
    awgn_samples: int,
    awgn_generator: torch.Generator,
    source_moment_evaluator: Callable[..., GramMomentResult] = c4_gram_source_moments,
) -> dict[str, Any]:
    """Evaluate one fixed physical ensemble over channel rows without source reuse across ensembles."""

    source_ensemble.validate()
    transmittance, epsilon = validate_channel_state(transmittance, epsilon)
    if transmittance.device != source_ensemble.probabilities.device:
        transmittance = transmittance.to(source_ensemble.probabilities.device)
        epsilon = epsilon.to(source_ensemble.probabilities.device)
    batch_ensemble = _repeat_ensemble(source_ensemble, transmittance.numel())

    source_start = time.perf_counter()
    moments = source_moment_evaluator(
        source_ensemble,
        density_eigenvalue_tolerance=density_eigenvalue_tolerance,
    )
    source_elapsed = time.perf_counter() - source_start
    if moments.coherent_correlation.shape != (1,) or moments.w.shape != (1,):
        raise ValueError("Cached source evaluator must return exactly one C and w value.")
    coherent_correlation = moments.coherent_correlation.expand_as(transmittance)
    w_raw = moments.w.expand_as(transmittance)

    downstream_start = time.perf_counter()
    mi = discrete_mutual_information(
        batch_ensemble,
        transmittance,
        epsilon,
        noise_samples_per_symbol=awgn_samples,
        generator=awgn_generator,
    )
    holevo = _holevo_from_source_moments(
        batch_ensemble,
        transmittance,
        epsilon,
        coherent_correlation=coherent_correlation,
        w_raw=w_raw,
        tau=None,
        tau_trace=batch_ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=1e-8,
        physicality_tolerance=1e-10,
        diagnostics={
            "backend": "c4_gram_cached_source_moments",
            "source_moment_diagnostics": moments.diagnostics,
            "density_eigenvalue_pseudoinverse_tolerance": density_eigenvalue_tolerance,
        },
    )
    rate = fading_secret_key_rate(mi, holevo.chi_be, beta_reconciliation)
    downstream_elapsed = time.perf_counter() - downstream_start
    diagnostics = ensemble_state_diagnostics(batch_ensemble)
    source_diagnostic = moments.diagnostics[0]
    finite = all(
        bool(torch.all(torch.isfinite(value)))
        for value in (moments.coherent_correlation, moments.w, mi, holevo.chi_be, rate.instantaneous_raw)
    )
    return {
        "source_moments": {
            "call_count": 1,
            "C": float(moments.coherent_correlation.item()),
            "w": float(moments.w.item()),
            "route": source_diagnostic.get("route"),
            "elapsed_seconds": source_elapsed,
            "diagnostics": source_diagnostic,
        },
        "downstream_elapsed_seconds": downstream_elapsed,
        "mean_i_ab": float(mi.mean()),
        "mean_chi_be": float(holevo.chi_be.mean()),
        "mean_raw_skr": float(rate.fading_average_raw),
        "min_raw_skr": float(rate.instantaneous_raw.min()),
        "max_raw_skr": float(rate.instantaneous_raw.max()),
        "average_photon_number": float(diagnostics["mean_photon_number"].mean()),
        "peak_photon_number": float(diagnostics["maximum_symbol_energy"].max()),
        "per_state": [
            {
                "T": float(transmittance[index]),
                "epsilon": float(epsilon[index]),
                "I_AB": float(mi[index]),
                "chi_BE": float(holevo.chi_be[index]),
                "raw_K": float(rate.instantaneous_raw[index]),
            }
            for index in range(transmittance.numel())
        ],
        "all_finite": finite,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    overrides = {
        key: value for key, value in vars(args).items()
        if key not in {"config", "output_dir", "resume"}
    }
    if args.output_dir is not None:
        overrides["output_dir"] = str(args.output_dir)
    settings = load_experiment_config(args.config.resolve(), overrides)
    output_dir = Path(settings["output_dir"])
    active_threshold = float(
        settings.get("density_eigenvalue_pseudoinverse_tolerance", 1e-13)
    )
    if settings["va"] > settings["va_budget"]:
        raise ValueError("The fixed baseline V_A exceeds the declared common V_A budget.")
    if not 0.0 < settings["v_min"] < settings["v_max"] or not settings["v_min"] <= settings["va"] <= settings["v_max"]:
        raise ValueError("Require V_A inside the declared common 0 < v_min < v_max box.")
    channel = sample_channel_state_distribution(
        geometry=LinkGeometry(settings["h_hap_m"], settings["h_uav_m"], 0.0),
        wavelength_m=settings["wavelength_m"], visibility_km=settings["visibility_km"],
        beam_waist_m=settings["beam_waist_m"], aperture_radius_m=settings["aperture_radius_m"],
        cn2_m_minus_two_thirds=settings["cn2"],
        excess_noise=IndependentUniformExcessNoise(settings["epsilon_min"], settings["epsilon_max"]),
        sample_count=settings["fading_samples"], seed=settings["channel_seed"],
    )
    transmittance = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(channel.excess_noise_snu, dtype=torch.float64)
    settings["output_dir"] = str(output_dir)
    metadata = collect_run_metadata(args.config, {
        "channel_seed": settings["channel_seed"], "awgn_seed": settings["awgn_seed"]
    })
    rows: list[dict[str, Any]] = []
    for configured_kind in settings["schemes"]:
        kind = {"uniform": "uniform", "binomial": "binomial", "mb": "mb", "fixed-mb": "mb"}[configured_kind.lower()]
        checkpoint = output_dir / f"baseline_cached_{kind}.json"
        if args.resume and checkpoint_matches(checkpoint, settings):
            rows.append(json.loads(checkpoint.read_text(encoding="utf-8"))["result"])
            print(f"[{kind}] resumed from checkpoint", flush=True)
            continue
        source_ensemble = reference_ensemble(
            kind,
            batch_size=1,
            modulation_variance=settings["va"], nu_mb=settings["mb_nu"] if kind == "mb" else None,
            v_min=settings["v_min"], v_max=settings["v_max"], n_peak_photons=settings["n_peak_photons"],
        )
        print(f"[{kind}] source moments start", flush=True)
        row = evaluate_fixed_ensemble(
            source_ensemble,
            transmittance,
            epsilon,
            density_eigenvalue_tolerance=active_threshold,
            beta_reconciliation=settings["beta"], awgn_samples=settings["awgn_samples"],
            awgn_generator=torch_generator(settings["awgn_seed"], transmittance.device),
        )
        print(f"[{kind}] source moments finished in {row['source_moments']['elapsed_seconds']:.3f} s", flush=True)
        print(f"[{kind}] downstream fading evaluation finished in {row['downstream_elapsed_seconds']:.3f} s", flush=True)
        row["scheme"] = kind
        rows.append(row)
        _write_json(checkpoint, {
            "status": "smoke evaluation; not a paper result",
            "run_config": settings,
            "run_metadata": metadata,
            "channel_metadata": channel.metadata,
            "channel": {
                "sample_count": int(transmittance.numel()),
                "mean_T": float(transmittance.mean()),
                "min_T": float(transmittance.min()),
                "max_T": float(transmittance.max()),
                "mean_epsilon": float(epsilon.mean()),
                "min_epsilon": float(epsilon.min()),
                "max_epsilon": float(epsilon.max()),
            },
            "result": row,
        })
    _write_json(output_dir / "baseline_cached_source_moments_smoke.json", {
        "status": "smoke evaluation; not a paper result",
        "run_config": settings,
        "run_metadata": metadata,
        "channel_metadata": channel.metadata,
        "channel": {
            "sample_count": int(transmittance.numel()),
            "mean_T": float(transmittance.mean()),
            "min_T": float(transmittance.min()),
            "max_T": float(transmittance.max()),
            "mean_epsilon": float(epsilon.mean()),
            "min_epsilon": float(epsilon.min()),
            "max_epsilon": float(epsilon.max()),
        },
        "results": rows,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
