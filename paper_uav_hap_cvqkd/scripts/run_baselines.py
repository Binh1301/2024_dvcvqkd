"""Run a fully explicit smoke evaluation of Uniform/Binomial/MB baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from _common import ROOT
from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "h-hap-m", "h-uav-m", "wavelength-m", "visibility-km", "beam-waist-m",
        "aperture-radius-m", "cn2", "epsilon", "va", "beta",
    ):
        parser.add_argument(f"--{name}", type=float, required=True)
    parser.add_argument("--mb-nu", type=float, default=0.1)
    parser.add_argument("--fading-samples", type=int, required=True)
    parser.add_argument("--awgn-samples", type=int, required=True)
    parser.add_argument("--fock-cutoff", type=int, required=True)
    parser.add_argument("--channel-seed", type=int, required=True)
    parser.add_argument("--awgn-seed", type=int, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "baseline_smoke.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    geometry = LinkGeometry(args.h_hap_m, args.h_uav_m, 0.0)
    channel = sample_fso_channel(
        geometry=geometry,
        wavelength_m=args.wavelength_m,
        visibility_km=args.visibility_km,
        beam_waist_m=args.beam_waist_m,
        aperture_radius_m=args.aperture_radius_m,
        cn2_m_minus_two_thirds=args.cn2,
        sample_count=args.fading_samples,
        rng=np.random.default_rng(args.channel_seed),
    )
    t = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon = torch.full_like(t, args.epsilon)
    rows: list[dict[str, float | str]] = []
    for index, kind in enumerate(("uniform", "binomial", "mb")):
        ensemble = reference_ensemble(
            kind,
            batch_size=t.numel(),
            modulation_variance=args.va,
            nu_mb=args.mb_nu if kind == "mb" else None,
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
        rows.append(
            {
                "scheme": kind,
                "mean_i_ab": float(mi.mean()),
                "mean_chi_be": float(holevo.chi_be.mean()),
                "mean_raw_skr": float(rate.fading_average_raw),
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

