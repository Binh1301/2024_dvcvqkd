"""Run a fully explicit smoke evaluation of Uniform/Binomial/MB baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _common import ROOT
from src.channel.geometry import LinkGeometry
from src.channel.state_distribution import (
    IndependentUniformExcessNoise,
    sample_channel_state_distribution,
)
from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import reference_ensemble
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
    parser.add_argument("--fock-cutoff", type=int, required=True)
    parser.add_argument("--channel-seed", type=int, required=True)
    parser.add_argument("--awgn-seed", type=int, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "baseline_smoke.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.va > args.va_budget:
        raise ValueError("The fixed baseline V_A exceeds the declared common V_A budget.")
    if not 0.0 < args.v_min < args.v_max or not args.v_min <= args.va <= args.v_max:
        raise ValueError("Require V_A inside the declared common 0 < v_min < v_max box.")
    geometry = LinkGeometry(args.h_hap_m, args.h_uav_m, 0.0)
    channel = sample_channel_state_distribution(
        geometry=geometry,
        wavelength_m=args.wavelength_m,
        visibility_km=args.visibility_km,
        beam_waist_m=args.beam_waist_m,
        aperture_radius_m=args.aperture_radius_m,
        cn2_m_minus_two_thirds=args.cn2,
        excess_noise=IndependentUniformExcessNoise(args.epsilon_min, args.epsilon_max),
        sample_count=args.fading_samples,
        seed=args.channel_seed,
    )
    t = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(channel.excess_noise_snu, dtype=torch.float64)
    rows: list[dict[str, object]] = []
    for index, kind in enumerate(("uniform", "binomial", "mb")):
        ensemble = reference_ensemble(
            kind,
            batch_size=t.numel(),
            modulation_variance=args.va,
            nu_mb=args.mb_nu if kind == "mb" else None,
            v_min=args.v_min,
            v_max=args.v_max,
            n_peak_photons=args.n_peak_photons,
        )
        mi = discrete_mutual_information(
            ensemble,
            t,
            epsilon,
            noise_samples_per_symbol=args.awgn_samples,
            generator=torch_generator(args.awgn_seed, t.device),
        )
        holevo = holevo_information(
            ensemble,
            t,
            epsilon,
            fock_cutoff=args.fock_cutoff,
        )
        rate = fading_secret_key_rate(mi, holevo.chi_be, args.beta)
        diagnostics = ensemble_state_diagnostics(ensemble)
        rows.append(
            {
                "scheme": kind,
                "mean_i_ab": float(mi.mean()),
                "mean_chi_be": float(holevo.chi_be.mean()),
                "mean_raw_skr": float(rate.fading_average_raw),
                "per_state_diagnostics": {
                    name: value.tolist() for name, value in diagnostics.items()
                },
            }
        )
    payload = {
        "status": "smoke evaluation; not a paper result",
        "parameters": vars(args) | {"output": str(args.output)},
        "channel_metadata": channel.metadata,
        "results": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote raw smoke metrics and parameters to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
