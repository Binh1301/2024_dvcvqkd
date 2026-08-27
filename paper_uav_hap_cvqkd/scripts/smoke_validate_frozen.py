"""Tiny deterministic validation of the frozen full transmitter; not a research run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _common import ROOT
from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.qam256 import c4_orbit_masses
from src.optimization.trainer import EnergyBudgetController, evaluate_transmitter, train_step
from src.utils.random import derive_seed, seed_process, torch_generator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--ps-learning-rate", type=float, default=3e-4)
    parser.add_argument("--gs-learning-rate", type=float, default=1e-4)
    parser.add_argument("--va-learning-rate", type=float, default=1e-4)
    parser.add_argument("--awgn-samples", type=int, default=2)
    parser.add_argument("--fock-cutoff", type=int, default=40)
    parser.add_argument("--beta", type=float, default=0.95)
    parser.add_argument("--v-min", type=float, default=0.5)
    parser.add_argument("--v-max", type=float, default=3.0)
    parser.add_argument("--va-budget", type=float, required=True)
    parser.add_argument("--dual-learning-rate", type=float, required=True)
    parser.add_argument("--seed", type=int, default=260826)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "results" / "frozen_transmitter_smoke.json"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.steps <= 0 or args.awgn_samples <= 0:
        raise ValueError("steps and awgn-samples must be positive integers.")
    seed_process(args.seed)
    transmittance = torch.tensor([0.02, 0.08, 0.2], dtype=torch.float64)
    epsilon = torch.tensor([0.004, 0.002, 0.0005], dtype=torch.float64)
    model = JointTransmitter("full", v_min=args.v_min, v_max=args.v_max)
    family_modules = {"ps": model.ps_network, "gs": model.gs_model, "va": model.va_network}
    family_rates = {
        "ps": args.ps_learning_rate, "gs": args.gs_learning_rate,
        "va": args.va_learning_rate,
    }
    if any(value <= 0.0 for value in family_rates.values()):
        raise ValueError("All family learning rates must be positive.")
    optimizer = torch.optim.Adam([
        {"params": family_modules[name].parameters(), "lr": family_rates[name], "name": name}
        for name in model.trainable_parameter_families()
    ])
    energy_controller = EnergyBudgetController(args.va_budget, args.dual_learning_rate)
    awgn_seed = derive_seed(args.seed, "frozen_smoke_common_awgn")

    def evaluate_fixed_noise():
        return evaluate_transmitter(
            model,
            transmittance,
            epsilon,
            beta_reconciliation=args.beta,
            noise_samples_per_symbol=args.awgn_samples,
            fock_cutoff=args.fock_cutoff,
            generator=torch_generator(awgn_seed),
            require_supported_symmetry=True,
        )

    model.eval()
    with torch.no_grad():
        initial = evaluate_fixed_noise()
    initial_va = initial.ensemble.declared_va.detach().clone()
    history: list[dict[str, object]] = []
    for step in range(args.steps):
        before_update = train_step(
            model,
            optimizer,
            transmittance,
            epsilon,
            beta_reconciliation=args.beta,
            noise_samples_per_symbol=args.awgn_samples,
            fock_cutoff=args.fock_cutoff,
            generator=torch_generator(awgn_seed),
            require_supported_symmetry=True,
            gradient_clip_norm=1.0,
            energy_budget_controller=energy_controller,
        )
        history.append({
            "step": step,
            "pre_update_loss": float(-before_update.key_rate.fading_average_raw.detach()),
            "pre_update_raw_skr": before_update.key_rate.instantaneous_raw.detach().tolist(),
            "optimization_loss": float(before_update.optimization_loss),
            "energy_budget_violation": float(before_update.energy_constraint_violation),
            "energy_dual_before_update": before_update.energy_dual_before_update,
            "energy_dual_after_update": before_update.energy_dual_after_update,
            "diagnostics": {
                name: value.detach().tolist()
                for name, value in before_update.state_diagnostics.items()
            },
        })

    model.eval()
    with torch.no_grad():
        final = evaluate_fixed_noise()
    final.ensemble.validate(tolerance=1e-9)
    initial_q = c4_orbit_masses(initial.ensemble.probabilities.detach())
    final_q = c4_orbit_masses(final.ensemble.probabilities.detach())
    q_state_span = torch.linalg.vector_norm(final_q - final_q[:1], dim=-1).max()
    va_state_span = (final.ensemble.declared_va.max() - final.ensemble.declared_va.min()).abs()
    relative_once = model.gs_model().detach()
    relative_twice = model.gs_model().detach()
    initial_loss = float(-initial.key_rate.fading_average_raw)
    final_loss = float(-final.key_rate.fading_average_raw)
    checks = {
        "finite_initial_and_final_loss": bool(torch.isfinite(torch.tensor([initial_loss, final_loss])).all()),
        "loss_decreased": final_loss < initial_loss,
        "q_outputs_diverged_across_states": float(q_state_span) > 0.0,
        "q_policy_changed_from_initial": float(torch.linalg.vector_norm(final_q - initial_q)) > 0.0,
        "va_outputs_differ_across_states": float(va_state_span) > 0.0,
        "va_policy_changed_from_initial": bool(
            torch.linalg.vector_norm(final.ensemble.declared_va - initial_va) > 0.0
        ),
        "gs_is_one_global_geometry": bool(torch.equal(relative_once, relative_twice)),
        "final_invariants_valid": True,
        "final_average_va_within_budget": (
            float(final.ensemble.declared_va.mean()) <= args.va_budget + 1e-12
        ),
    }
    payload = {
        "status": "software/mathematical smoke validation; not a paper result",
        "transmitter_spec": "frozen_c4_v1",
        "parameters": {
            **vars(args),
            "output": str(args.output.resolve()),
            "transmittance": transmittance.tolist(),
            "epsilon": epsilon.tolist(),
            "derived_common_awgn_seed": awgn_seed,
        },
        "optimizer_freeze_probe": {
            "optimizer": "Adam",
            "parameter_group_learning_rates": family_rates,
            "gradient_clip_norm": 1.0,
            "regularization_coefficients": {"separation": 0.0, "peak": 0.0, "drift": 0.0},
            "publication_training": False,
            "test_set_used": False,
        },
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "checks": checks,
        "history": history,
        "final": {
            "orbit_masses": final_q.tolist(),
            "raw_skr": final.key_rate.instantaneous_raw.detach().tolist(),
            "diagnostics": {
                name: value.detach().tolist()
                for name, value in final.state_diagnostics.items()
            },
            "constraints": final.constraints,
            "holevo_diagnostics": final.holevo.diagnostics,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "checks": checks}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
