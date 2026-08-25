"""Evaluate a frozen learned checkpoint on explicitly new channel/AWGN streams."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _train import _channel
from src.modulation.joint_ps_gs import JointTransmitter
from src.optimization.trainer import evaluate_transmitter
from src.utils.random import derive_seed, torch_generator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--channel-seed", type=int, required=True)
    parser.add_argument("--awgn-seed", type=int, required=True)
    parser.add_argument("--fading-samples", type=int, required=True)
    parser.add_argument("--awgn-samples", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.channel_seed == args.awgn_seed:
        raise ValueError("Independent evaluation channel and AWGN seeds must differ.")
    checkpoint = torch.load(args.checkpoint.resolve(), map_location="cpu", weights_only=False)
    mode = checkpoint["mode"]
    config = checkpoint["configuration"]
    cvqkd = config["cvqkd"]
    transmitter = JointTransmitter(
        mode,
        fixed_va=cvqkd.get("fixed_modulation_variance_snu"),
        v_min=cvqkd.get("v_min_snu"),
        v_max=cvqkd.get("v_max_snu"),
        reference_distribution="uniform",
        nu_mb=cvqkd.get("mb_nu"),
    )
    transmitter.load_state_dict(checkpoint["model_state_dict"])
    transmitter.eval()
    channel_seed = derive_seed(args.channel_seed, "independent_evaluation_channel")
    awgn_seed = derive_seed(args.awgn_seed, "independent_evaluation_awgn")
    channel = _channel(config, args.fading_samples, channel_seed)
    transmittance = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon = torch.full_like(transmittance, config["channel"]["excess_noise_snu"])
    standard_form_override = bool(checkpoint.get("standard_form_override", False))
    with torch.no_grad():
        evaluation = evaluate_transmitter(
            transmitter,
            transmittance,
            epsilon,
            beta_reconciliation=cvqkd["beta_reconciliation"],
            noise_samples_per_symbol=args.awgn_samples,
            fock_cutoff=cvqkd["fock_cutoff"],
            generator=torch_generator(awgn_seed),
            require_supported_symmetry=not standard_form_override,
        )
    payload = {
        "status": "independent frozen-checkpoint evaluation; not a paper result",
        "checkpoint": str(args.checkpoint.resolve()),
        "mode": mode,
        "standard_form_override": standard_form_override,
        "seeds": {"channel": args.channel_seed, "awgn": args.awgn_seed},
        "derived_seeds": {"channel": channel_seed, "awgn": awgn_seed},
        "channel_metadata": channel.metadata,
        "mean_raw_skr": float(evaluation.key_rate.fading_average_raw),
        "per_state": {
            "transmittance": transmittance.tolist(),
            "i_ab": evaluation.mutual_information.tolist(),
            "chi_be": evaluation.holevo.chi_be.tolist(),
            "raw_skr": evaluation.key_rate.instantaneous_raw.tolist(),
            "declared_va": evaluation.ensemble.declared_va.tolist(),
        },
        "holevo_diagnostics": evaluation.holevo.diagnostics,
        "constraints": evaluation.constraints,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote independent checkpoint evaluation to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
