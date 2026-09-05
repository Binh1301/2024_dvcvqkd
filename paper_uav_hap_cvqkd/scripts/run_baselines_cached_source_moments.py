"""Smoke fixed baselines with one full-support source-moment evaluation each."""

from __future__ import annotations

import argparse
import json
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "h-hap-m", "h-uav-m", "wavelength-m", "visibility-km", "beam-waist-m",
        "aperture-radius-m", "cn2", "epsilon-min", "epsilon-max", "va", "v-min", "v-max",
        "va-budget", "n-peak-photons", "beta",
    ):
        parser.add_argument(f"--{name}", type=float, required=True)
    parser.add_argument("--mb-nu", type=float, required=True)
    parser.add_argument("--fading-samples", type=int, required=True)
    parser.add_argument("--awgn-samples", type=int, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--channel-seed", type=int, required=True)
    parser.add_argument("--awgn-seed", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
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
    config = load_yaml(args.config.resolve())
    active_threshold = float(
        config["cvqkd"]["holevo_numerics"]["density_eigenvalue_pseudoinverse_tolerance"]
    )
    if args.va > args.va_budget:
        raise ValueError("The fixed baseline V_A exceeds the declared common V_A budget.")
    if not 0.0 < args.v_min < args.v_max or not args.v_min <= args.va <= args.v_max:
        raise ValueError("Require V_A inside the declared common 0 < v_min < v_max box.")
    channel = sample_channel_state_distribution(
        geometry=LinkGeometry(args.h_hap_m, args.h_uav_m, 0.0),
        wavelength_m=args.wavelength_m,
        visibility_km=args.visibility_km,
        beam_waist_m=args.beam_waist_m,
        aperture_radius_m=args.aperture_radius_m,
        cn2_m_minus_two_thirds=args.cn2,
        excess_noise=IndependentUniformExcessNoise(args.epsilon_min, args.epsilon_max),
        sample_count=args.fading_samples,
        seed=args.channel_seed,
    )
    transmittance = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(channel.excess_noise_snu, dtype=torch.float64)
    parameters = vars(args) | {"output_dir": str(args.output_dir)}
    rows: list[dict[str, Any]] = []
    for kind in ("uniform", "binomial", "mb"):
        source_ensemble = reference_ensemble(
            kind,
            batch_size=1,
            modulation_variance=args.va,
            nu_mb=args.mb_nu if kind == "mb" else None,
            v_min=args.v_min,
            v_max=args.v_max,
            n_peak_photons=args.n_peak_photons,
        )
        print(f"[{kind}] source moments start", flush=True)
        row = evaluate_fixed_ensemble(
            source_ensemble,
            transmittance,
            epsilon,
            density_eigenvalue_tolerance=active_threshold,
            beta_reconciliation=args.beta,
            awgn_samples=args.awgn_samples,
            awgn_generator=torch_generator(args.awgn_seed, transmittance.device),
        )
        print(f"[{kind}] source moments finished in {row['source_moments']['elapsed_seconds']:.3f} s", flush=True)
        print(f"[{kind}] downstream fading evaluation finished in {row['downstream_elapsed_seconds']:.3f} s", flush=True)
        row["scheme"] = kind
        rows.append(row)
        _write_json(args.output_dir / f"baseline_cached_{kind}.json", {
            "status": "smoke evaluation; not a paper result",
            "parameters": parameters,
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
    _write_json(args.output_dir / "baseline_cached_source_moments_smoke.json", {
        "status": "smoke evaluation; not a paper result",
        "parameters": parameters,
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
