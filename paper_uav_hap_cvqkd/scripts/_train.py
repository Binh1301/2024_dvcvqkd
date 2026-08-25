"""Shared deterministic training CLI implementation."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from _common import ROOT, load_yaml, missing_required
from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.modulation.joint_ps_gs import JointTransmitter
from src.optimization.trainer import evaluate_transmitter, train_step
from src.utils.random import SplitSeeds, derive_seed, seed_process, torch_generator


TRAIN_REQUIRED = [
    "channel.h_hap_m", "channel.h_uav_m", "channel.wavelength_m", "channel.visibility_km",
    "channel.beam_waist_m", "channel.aperture_radius_m", "channel.cn2_m_minus_two_thirds",
    "channel.excess_noise_snu", "cvqkd.beta_reconciliation",
    "cvqkd.fock_cutoff", "training.epochs",
    "training.learning_rate", "training.train_fading_samples",
    "training.validation_fading_samples", "training.test_fading_samples",
    "training.train_awgn_samples_per_symbol", "training.validation_awgn_samples_per_symbol",
    "training.test_awgn_samples_per_symbol", "training.seeds.train_channel",
    "training.seeds.train_awgn", "training.seeds.validation_channel",
    "training.seeds.validation_awgn", "training.seeds.test_channel", "training.seeds.test_awgn",
]


def _channel(config: dict[str, Any], count: int, seed: int):
    values = config["channel"]
    geometry = LinkGeometry(values["h_hap_m"], values["h_uav_m"], values.get("zenith_angle_rad", 0.0))
    return sample_fso_channel(
        geometry=geometry,
        wavelength_m=values["wavelength_m"],
        visibility_km=values["visibility_km"],
        beam_waist_m=values["beam_waist_m"],
        aperture_radius_m=values["aperture_radius_m"],
        cn2_m_minus_two_thirds=values["cn2_m_minus_two_thirds"],
        sample_count=int(count),
        rng=np.random.default_rng(seed),
    )


def run_training(mode: str) -> int:
    parser = argparse.ArgumentParser(description=f"Train paper transmitter mode {mode}.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--allow-unproven-standard-form",
        action="store_true",
        help="Exploratory only: evaluate asymmetric ensembles with the paper covariance despite missing proof.",
    )
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    required = list(TRAIN_REQUIRED)
    if mode in {"ps_va", "gs_va", "full"}:
        required += ["cvqkd.v_min_snu", "cvqkd.v_max_snu"]
    else:
        required += ["cvqkd.fixed_modulation_variance_snu"]
    missing = missing_required(config, required)
    if missing:
        raise ValueError("Unresolved required configuration: " + ", ".join(missing))
    seeds = SplitSeeds(**config["training"]["seeds"])
    seeds.validate()
    seed_process(derive_seed(seeds.train_channel, "process"))
    cvqkd = config["cvqkd"]
    training = config["training"]
    transmitter = JointTransmitter(
        mode,
        fixed_va=cvqkd["fixed_modulation_variance_snu"],
        v_min=cvqkd.get("v_min_snu"),
        v_max=cvqkd.get("v_max_snu"),
        reference_distribution="uniform",
        nu_mb=cvqkd.get("mb_nu"),
    )
    optimizer = torch.optim.Adam(transmitter.parameters(), lr=float(training["learning_rate"]))
    validation_channel = _channel(
        config,
        training["validation_fading_samples"],
        derive_seed(seeds.validation_channel, "validation_channel"),
    )
    validation_t = torch.as_tensor(validation_channel.transmittance, dtype=torch.float64)
    validation_epsilon = torch.full_like(validation_t, config["channel"]["excess_noise_snu"])
    strict = not args.allow_unproven_standard_form
    best_value = float("-inf")
    best_state: dict[str, torch.Tensor] | None = None
    history: list[dict[str, float | int]] = []
    for epoch in range(int(training["epochs"])):
        train_channel = _channel(
            config,
            training["train_fading_samples"],
            derive_seed(seeds.train_channel, "train_channel", epoch),
        )
        train_t = torch.as_tensor(train_channel.transmittance, dtype=torch.float64)
        train_epsilon = torch.full_like(train_t, config["channel"]["excess_noise_snu"])
        train_eval = train_step(
            transmitter,
            optimizer,
            train_t,
            train_epsilon,
            beta_reconciliation=cvqkd["beta_reconciliation"],
            noise_samples_per_symbol=training["train_awgn_samples_per_symbol"],
            fock_cutoff=cvqkd["fock_cutoff"],
            generator=torch_generator(derive_seed(seeds.train_awgn, "train_awgn", epoch)),
            require_supported_symmetry=strict,
            gradient_clip_norm=1.0,
        )
        transmitter.eval()
        with torch.no_grad():
            validation_eval = evaluate_transmitter(
                transmitter,
                validation_t,
                validation_epsilon,
                beta_reconciliation=cvqkd["beta_reconciliation"],
                noise_samples_per_symbol=training["validation_awgn_samples_per_symbol"],
                fock_cutoff=cvqkd["fock_cutoff"],
                generator=torch_generator(
                    derive_seed(seeds.validation_awgn, "validation_awgn")
                ),
                require_supported_symmetry=strict,
            )
        validation_value = float(validation_eval.key_rate.fading_average_raw)
        history.append(
            {
                "epoch": epoch,
                "train_raw_skr": float(train_eval.key_rate.fading_average_raw),
                "validation_raw_skr": validation_value,
            }
        )
        if validation_value > best_value:
            best_value = validation_value
            best_state = copy.deepcopy(transmitter.state_dict())
    if best_state is None:
        raise RuntimeError("No valid checkpoint was selected.")
    transmitter.load_state_dict(best_state)
    test_channel = _channel(
        config,
        training["test_fading_samples"],
        derive_seed(seeds.test_channel, "test_channel"),
    )
    test_t = torch.as_tensor(test_channel.transmittance, dtype=torch.float64)
    test_epsilon = torch.full_like(test_t, config["channel"]["excess_noise_snu"])
    transmitter.eval()
    with torch.no_grad():
        test_eval = evaluate_transmitter(
            transmitter,
            test_t,
            test_epsilon,
            beta_reconciliation=cvqkd["beta_reconciliation"],
            noise_samples_per_symbol=training["test_awgn_samples_per_symbol"],
            fock_cutoff=cvqkd["fock_cutoff"],
            generator=torch_generator(derive_seed(seeds.test_awgn, "test_awgn")),
            require_supported_symmetry=strict,
        )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": best_state,
            "mode": mode,
            "configuration": config,
            "standard_form_override": args.allow_unproven_standard_form,
            "best_validation_raw_skr": best_value,
        },
        output_dir / "best.pt",
    )
    report = {
        "status": "exploratory training output; paper Sections V-VI are empty",
        "mode": mode,
        "standard_form_override": args.allow_unproven_standard_form,
        "history": history,
        "test_raw_skr": float(test_eval.key_rate.fading_average_raw),
        "test_channel_metadata": test_channel.metadata,
        "seeds": config["training"]["seeds"],
    }
    (output_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote checkpoint and raw metrics to {output_dir}")
    return 0
