"""Shared deterministic training CLI implementation."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import torch

from _common import (
    ROOT, holevo_numerical_kwargs, load_yaml, missing_required,
    require_holevo_pseudoinverse_approval,
)
from src.channel.geometry import LinkGeometry
from src.channel.state_distribution import (
    IndependentUniformExcessNoise,
    assert_disjoint_state_realizations,
    sample_channel_state_distribution,
)
from src.channel.turbulence import UavMotion
from src.modulation.joint_ps_gs import JointTransmitter
from src.optimization.trainer import (
    EnergyBudgetController,
    Evaluation,
    evaluate_transmitter,
    train_step,
)
from src.optimization.constraints import validation_expected_budget_status
from src.validation.publication_manifest import canonical_json_sha256
from src.validation.physical_domain import (
    approved_peak_photon_limit, require_preconvergence_domain_ready,
)
from src.utils.random import derive_seed, seed_process, torch_generator


TRAIN_REQUIRED = [
    "channel.h_hap_m", "channel.h_uav_m", "channel.wavelength_m", "channel.visibility_km",
    "channel.beam_waist_m", "channel.aperture_radius_m", "channel.cn2_m_minus_two_thirds",
    "channel.uav_motion.sigma_x_m", "channel.uav_motion.sigma_y_m",
    "channel.uav_motion.sigma_z_m", "channel.uav_motion.sigma_theta_rad",
    "channel.uav_motion.sigma_phi_rad", "channel.uav_motion.sigma_psi_rad",
    "channel.excess_noise_distribution.kind",
    "channel.excess_noise_distribution.minimum_snu",
    "channel.excess_noise_distribution.maximum_snu", "cvqkd.beta_reconciliation",
    "cvqkd.fock_cutoff", "cvqkd.v_a_budget_snu", "cvqkd.v_min_snu",
    "cvqkd.v_max_snu", "training.epochs",
    "cvqkd.n_peak_photons", "cvqkd.peak_domain_scope",
    "cvqkd.holevo_numerics.symmetry_tolerance",
    "cvqkd.holevo_numerics.density_trace_tolerance",
    "cvqkd.holevo_numerics.density_eigenvalue_pseudoinverse_tolerance",
    "cvqkd.holevo_numerics.physicality_tolerance",
    "training.train_fading_samples",
    "training.optimizer", "training.batch_size", "training.validation_patience_epochs",
    "training.validation_min_delta_bits", "training.gradient_clip_norm",
    "training.validation_energy_budget_margin_snu",
    "training.regularization.separation_coefficient",
    "training.regularization.peak_coefficient",
    "training.regularization.drift_coefficient",
    "training.independent_training_initialization_seeds",
    "training.validation_fading_samples",
    "training.train_awgn_samples_per_symbol", "training.validation_awgn_samples_per_symbol",
    "training.seeds.train_channel",
    "training.seeds.train_awgn", "training.seeds.validation_channel",
    "training.seeds.validation_awgn",
]


def _channel(config: dict[str, Any], count: int, seed: int):
    values = config["channel"]
    geometry = LinkGeometry(values["h_hap_m"], values["h_uav_m"], values.get("zenith_angle_rad", 0.0))
    epsilon_values = values["excess_noise_distribution"]
    motion_values = values.get("uav_motion")
    if not isinstance(motion_values, dict):
        raise ValueError("channel.uav_motion must explicitly resolve all six jitter values.")
    if epsilon_values.get("kind") != "independent_uniform":
        raise ValueError(
            "The frozen numerical protocol requires channel.excess_noise_distribution.kind "
            "to be 'independent_uniform'."
        )
    return sample_channel_state_distribution(
        geometry=geometry,
        wavelength_m=values["wavelength_m"],
        visibility_km=values["visibility_km"],
        beam_waist_m=values["beam_waist_m"],
        aperture_radius_m=values["aperture_radius_m"],
        cn2_m_minus_two_thirds=values["cn2_m_minus_two_thirds"],
        excess_noise=IndependentUniformExcessNoise(
            minimum_snu=epsilon_values["minimum_snu"],
            maximum_snu=epsilon_values["maximum_snu"],
        ),
        sample_count=int(count),
        seed=seed,
        uav_motion=UavMotion(**motion_values),
    )


def _state_payload(
    evaluation: Evaluation, transmittance: torch.Tensor, epsilon: torch.Tensor
) -> dict[str, Any]:
    """Serialize the raw per-state values needed to audit every evaluation."""

    return {
        "transmittance": transmittance.detach().tolist(),
        "epsilon": epsilon.detach().tolist(),
        "i_ab": evaluation.mutual_information.detach().tolist(),
        "chi_be": evaluation.holevo.chi_be.detach().tolist(),
        "raw_skr": evaluation.key_rate.instantaneous_raw.detach().tolist(),
        **{
            name: value.detach().tolist()
            for name, value in evaluation.state_diagnostics.items()
        },
    }


def run_training(mode: str) -> int:
    parser = argparse.ArgumentParser(description=f"Train paper transmitter mode {mode}.")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--initialization-seed", type=int, required=True)
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    required = list(TRAIN_REQUIRED)
    if mode in {"va", "ps_va", "gs_va", "full"}:
        required += ["training.energy_dual_learning_rate"]
    else:
        required += ["cvqkd.fixed_modulation_variance_snu"]
    missing = missing_required(config, required)
    if missing:
        raise ValueError("Unresolved required configuration: " + ", ".join(missing))
    seeds = config["training"]["seeds"]
    development_seed_names = (
        "train_channel", "train_awgn", "validation_channel", "validation_awgn"
    )
    development_seeds = tuple(seeds[name] for name in development_seed_names)
    if any(not isinstance(value, int) or value < 0 for value in development_seeds):
        raise ValueError("Training/validation seeds must be nonnegative integers.")
    if len(set(development_seeds)) != len(development_seeds):
        raise ValueError("Training/validation seeds must be distinct.")
    cvqkd = config["cvqkd"]
    training = config["training"]
    n_peak = approved_peak_photon_limit(config)
    require_preconvergence_domain_ready(config)
    require_holevo_pseudoinverse_approval(config)
    initialization_seeds = training["independent_training_initialization_seeds"]
    if not isinstance(initialization_seeds, list) or not initialization_seeds:
        raise ValueError("independent_training_initialization_seeds must be a nonempty list.")
    if args.initialization_seed not in initialization_seeds:
        raise ValueError("--initialization-seed must be preregistered in the configuration.")
    if any(not isinstance(value, int) or value < 0 for value in initialization_seeds):
        raise ValueError("All initialization seeds must be nonnegative integers.")
    if len(set(initialization_seeds)) != len(initialization_seeds):
        raise ValueError("Independent initialization seeds must be distinct.")
    seed_process(derive_seed(args.initialization_seed, "model_initialization"))
    if training["optimizer"] != "adam":
        raise ValueError("The frozen implementation currently supports optimizer: adam only.")
    if int(training["batch_size"]) != int(training["train_fading_samples"]):
        raise ValueError(
            "The current iid one-minibatch-per-epoch protocol requires batch_size "
            "to equal train_fading_samples."
        )
    regularization = training["regularization"]
    if any(float(regularization[name]) != 0.0 for name in (
        "separation_coefficient", "peak_coefficient", "drift_coefficient"
    )):
        raise ValueError("Primary frozen training requires all regularization coefficients zero.")
    patience = int(training["validation_patience_epochs"])
    minimum_delta = float(training["validation_min_delta_bits"])
    validation_budget_margin = float(training["validation_energy_budget_margin_snu"])
    if patience <= 0 or minimum_delta < 0.0 or validation_budget_margin < 0.0:
        raise ValueError(
            "Require positive validation patience and nonnegative minimum delta/budget margin."
        )
    gradient_clip_norm = float(training["gradient_clip_norm"])
    if gradient_clip_norm <= 0.0:
        raise ValueError("gradient_clip_norm must be positive.")
    transmitter = JointTransmitter(
        mode,
        fixed_va=cvqkd.get("fixed_modulation_variance_snu"),
        v_min=cvqkd.get("v_min_snu"),
        v_max=cvqkd.get("v_max_snu"),
        reference_distribution="uniform",
        nu_mb=cvqkd.get("mb_nu"),
        n_peak_photons=n_peak,
    )
    va_budget = float(cvqkd["v_a_budget_snu"])
    if va_budget < float(cvqkd["v_min_snu"]):
        raise ValueError("v_a_budget_snu must be at least v_min_snu for feasibility.")
    adaptive_va = mode in {"va", "ps_va", "gs_va", "full"}
    energy_controller = (
        EnergyBudgetController(
            va_budget=va_budget,
            dual_learning_rate=float(training["energy_dual_learning_rate"]),
        )
        if adaptive_va
        else None
    )
    if not adaptive_va and float(cvqkd["fixed_modulation_variance_snu"]) > va_budget:
        raise ValueError("fixed_modulation_variance_snu exceeds the common V_A budget.")
    family_modules = {
        "ps": transmitter.ps_network,
        "gs": transmitter.gs_model,
        "va": transmitter.va_network,
    }
    learning_rates = training.get("learning_rates")
    if not isinstance(learning_rates, dict):
        raise ValueError("training.learning_rates must contain author-frozen PS/GS/VA rates.")
    parameter_groups = []
    for family in transmitter.trainable_parameter_families():
        value = learning_rates.get(family)
        if not isinstance(value, (int, float)) or float(value) <= 0.0:
            raise ValueError(f"training.learning_rates.{family} must be finite and positive.")
        module = family_modules[family]
        if module is None:
            raise RuntimeError(f"Missing trainable module for family {family}.")
        parameter_groups.append({"params": module.parameters(), "lr": float(value), "name": family})
    optimizer = torch.optim.Adam(parameter_groups)
    validation_channel = _channel(
        config,
        training["validation_fading_samples"],
        derive_seed(seeds["validation_channel"], "validation_channel"),
    )
    validation_t = torch.as_tensor(validation_channel.transmittance, dtype=torch.float64)
    validation_epsilon = torch.as_tensor(
        validation_channel.excess_noise_snu, dtype=torch.float64
    )
    best_value = float("-inf")
    best_state: dict[str, torch.Tensor] | None = None
    history: list[dict[str, Any]] = []
    epochs_without_material_improvement = 0
    early_stopping_reference = float("-inf")
    for epoch in range(int(training["epochs"])):
        train_channel = _channel(
            config,
            training["train_fading_samples"],
            derive_seed(seeds["train_channel"], "train_channel", epoch),
        )
        assert_disjoint_state_realizations(
            (
                (f"train_epoch_{epoch}", train_channel),
                ("validation", validation_channel),
            )
        )
        train_t = torch.as_tensor(train_channel.transmittance, dtype=torch.float64)
        train_epsilon = torch.as_tensor(train_channel.excess_noise_snu, dtype=torch.float64)
        train_eval = train_step(
            transmitter,
            optimizer,
            train_t,
            train_epsilon,
            beta_reconciliation=cvqkd["beta_reconciliation"],
            noise_samples_per_symbol=training["train_awgn_samples_per_symbol"],
            fock_cutoff=cvqkd["fock_cutoff"],
            generator=torch_generator(
                derive_seed(seeds["train_awgn"], "train_awgn", epoch)
            ),
            require_supported_symmetry=True,
            gradient_clip_norm=gradient_clip_norm,
            energy_budget_controller=energy_controller,
            **holevo_numerical_kwargs(config),
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
                    derive_seed(seeds["validation_awgn"], "validation_awgn")
                ),
                require_supported_symmetry=True,
                **holevo_numerical_kwargs(config),
            )
        validation_value = float(validation_eval.key_rate.fading_average_raw)
        validation_mean_va = float(validation_eval.ensemble.declared_va.mean())
        validation_budget = validation_expected_budget_status(
            validation_mean_va, va_budget,
            validation_budget_margin if adaptive_va else 0.0,
        )
        validation_budget_feasible = bool(validation_budget["expected_budget_feasible"])
        history.append(
            {
                "epoch": epoch,
                "train_raw_skr": float(train_eval.key_rate.fading_average_raw.detach()),
                "validation_raw_skr": validation_value,
                "optimization_loss": float(train_eval.optimization_loss),
                "energy_budget_violation": (
                    None if train_eval.energy_constraint_violation is None
                    else float(train_eval.energy_constraint_violation)
                ),
                "energy_dual_before_update": train_eval.energy_dual_before_update,
                "energy_dual_after_update": train_eval.energy_dual_after_update,
                "validation_mean_va": validation_mean_va,
                "validation_budget_feasible": validation_budget_feasible,
                "validation_expected_budget": validation_budget,
                "peak_feasible_step_accepted": train_eval.peak_feasible_step_accepted,
                "validation_peak_photon_constraint_satisfied": True,
                "train_per_state": _state_payload(train_eval, train_t, train_epsilon),
                "validation_per_state": _state_payload(
                    validation_eval, validation_t, validation_epsilon
                ),
            }
        )
        if validation_budget_feasible and validation_value > best_value:
            best_value = validation_value
            best_state = copy.deepcopy(transmitter.state_dict())
        if validation_budget_feasible and validation_value > early_stopping_reference + minimum_delta:
            early_stopping_reference = validation_value
            epochs_without_material_improvement = 0
        else:
            epochs_without_material_improvement += 1
        history[-1]["epochs_without_material_improvement"] = epochs_without_material_improvement
        if epochs_without_material_improvement >= patience:
            history[-1]["early_stopping_triggered"] = True
            break
    if best_state is None:
        raise RuntimeError("No valid checkpoint was selected.")
    transmitter.load_state_dict(best_state)
    transmitter.eval()
    with torch.no_grad():
        selected_validation_eval = evaluate_transmitter(
            transmitter,
            validation_t,
            validation_epsilon,
            beta_reconciliation=cvqkd["beta_reconciliation"],
            noise_samples_per_symbol=training["validation_awgn_samples_per_symbol"],
            fock_cutoff=cvqkd["fock_cutoff"],
            generator=torch_generator(
                derive_seed(seeds["validation_awgn"], "validation_awgn")
            ),
            require_supported_symmetry=True,
            **holevo_numerical_kwargs(config),
        )
    selected_validation_mean_va = float(
        selected_validation_eval.ensemble.declared_va.mean()
    )
    selected_budget = validation_expected_budget_status(
        selected_validation_mean_va, va_budget,
        validation_budget_margin if adaptive_va else 0.0,
    )
    if not selected_budget["expected_budget_feasible"]:
        raise RuntimeError("Selected policy violates the complete-validation V_A budget.")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": best_state,
            "mode": mode,
            "configuration": config,
            "transmitter_spec": "frozen_c4_v1",
            "n_peak_photons": n_peak,
            "energy_budget_controller": (
                None if energy_controller is None else energy_controller.state_dict()
            ),
            "best_validation_raw_skr": best_value,
            "selected_validation_max_symbol_energy": selected_validation_eval.constraints[
                "maximum_symbol_energy"
            ],
            "selected_validation_peak_feasible": True,
            "selected_validation_expected_budget": selected_budget,
            "initialization_seed": args.initialization_seed,
        },
        output_dir / "best.pt",
    )
    report = {
        "status": "training/validation-only output; held-out test is inaccessible",
        "mode": mode,
        "checkpoint_id": f"{mode}-seed-{args.initialization_seed}-va-{cvqkd.get('fixed_modulation_variance_snu')}",
        "transmitter_spec": "frozen_c4_v1",
        "fixed_modulation_variance_snu": cvqkd.get("fixed_modulation_variance_snu"),
        "training_protocol_sha256": canonical_json_sha256(
            {
                "training": {
                    key: value for key, value in training.items()
                    if key not in {"seeds", "independent_training_initialization_seeds"}
                },
                "development_seeds": {
                    name: seeds[name] for name in development_seed_names
                },
                "cvqkd": {
                    key: value for key, value in cvqkd.items()
                    if key != "fixed_modulation_variance_snu"
                },
            }
        ),
        "history": history,
        "selected_validation_raw_skr": float(
            selected_validation_eval.key_rate.fading_average_raw
        ),
        "selected_validation_mean_va": selected_validation_mean_va,
        "validation_budget_feasible": True,
        "validation_expected_budget": selected_budget,
        "va_budget": va_budget,
        "n_peak_photons": n_peak,
        "n_peak_author_approved": True,
        "peak_domain_scope": cvqkd["peak_domain_scope"],
        "selected_validation_peak_feasible": True,
        "selected_validation_max_symbol_energy": selected_validation_eval.constraints[
            "maximum_symbol_energy"
        ],
        "selected_validation_per_state": _state_payload(
            selected_validation_eval, validation_t, validation_epsilon
        ),
        "selected_validation_constraints": selected_validation_eval.constraints,
        "selected_validation_holevo_diagnostics": (
            selected_validation_eval.holevo.diagnostics
        ),
        "validation_channel_metadata": validation_channel.metadata,
        "validation_state_realization_sha256": validation_channel.realization_sha256,
        "development_seeds": {
            name: seeds[name] for name in development_seed_names
        },
        "test_set_accessed": False,
        "initialization_seed": args.initialization_seed,
        "epochs_completed": len(history),
        "stopping_rule": {
            "maximum_epochs": training["epochs"],
            "validation_patience_epochs": patience,
            "validation_min_delta_bits": minimum_delta,
        },
    }
    (output_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote checkpoint and raw metrics to {output_dir}")
    return 0
