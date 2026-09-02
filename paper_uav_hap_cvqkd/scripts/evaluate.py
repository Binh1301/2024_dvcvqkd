"""One-shot held-out evaluation gated by a frozen selection manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _common import holevo_numerical_kwargs, require_holevo_pseudoinverse_approval
from _train import _channel
from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.qam256 import c4_orbit_masses
from src.optimization.trainer import evaluate_transmitter
from src.optimization.constraints import heldout_budget_comparison_status
from src.validation.publication_manifest import (
    common_protocol_config,
    file_sha256,
    load_publication_manifest,
    selected_checkpoint,
    verify_bound_artifacts,
)
from src.validation.physical_domain import approved_peak_photon_limit
from src.utils.random import derive_seed, torch_generator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-manifest", type=Path, required=True)
    parser.add_argument("--checkpoint-id", type=str, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.selection_manifest.resolve()
    manifest = load_publication_manifest(manifest_path)
    resolved_config = verify_bound_artifacts(manifest_path, manifest)
    require_holevo_pseudoinverse_approval(resolved_config)
    checkpoint_entry = selected_checkpoint(manifest, args.checkpoint_id)
    checkpoint_path = Path(checkpoint_entry["path"])
    if not checkpoint_path.is_absolute():
        checkpoint_path = (manifest_path.parent / checkpoint_path).resolve()
    if file_sha256(checkpoint_path) != checkpoint_entry["sha256"]:
        raise ValueError("Checkpoint hash differs from the pre-test frozen manifest.")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if checkpoint.get("transmitter_spec") != "frozen_c4_v1":
        raise ValueError(
            "Checkpoint predates the frozen C4 transmitter and is intentionally incompatible."
        )
    mode = checkpoint["mode"]
    if mode != checkpoint_entry["mode"]:
        raise ValueError("Checkpoint mode differs from the pre-test frozen manifest.")
    if checkpoint.get("initialization_seed") != checkpoint_entry["initialization_seed"]:
        raise ValueError("Checkpoint initialization seed differs from the frozen manifest.")
    config = checkpoint["configuration"]
    checkpoint_fixed_va = config["cvqkd"].get("fixed_modulation_variance_snu")
    if checkpoint_entry["selected_fixed_va_snu"] != checkpoint_fixed_va:
        raise ValueError("Checkpoint fixed VA differs from its learned-selection manifest entry.")
    if common_protocol_config(config) != common_protocol_config(resolved_config):
        raise ValueError("Checkpoint common protocol differs from the bound resolved config.")
    cvqkd = config["cvqkd"]
    n_peak = approved_peak_photon_limit(config)
    if checkpoint.get("n_peak_photons") != n_peak:
        raise ValueError("Checkpoint peak-photon domain differs from the resolved config.")
    if checkpoint.get("selected_validation_peak_feasible") is not True:
        raise ValueError("Checkpoint lacks complete-validation peak feasibility.")
    if checkpoint.get("selected_validation_max_symbol_energy") != checkpoint_entry[
        "validation_max_symbol_energy"
    ]:
        raise ValueError("Checkpoint validation peak differs from the frozen manifest.")
    checkpoint_budget = checkpoint.get("selected_validation_expected_budget")
    if not isinstance(checkpoint_budget, dict) or checkpoint_budget.get(
        "expected_budget_feasible"
    ) is not True or checkpoint_budget.get("expected_budget_upper_snu") != checkpoint_entry[
        "validation_expected_budget_upper_snu"
    ] or checkpoint_budget.get("validation_mean_va_snu") != checkpoint_entry[
        "validation_mean_va_snu"
    ]:
        raise ValueError("Checkpoint expected-budget evidence differs from the frozen manifest.")
    va_budget = float(cvqkd["v_a_budget_snu"])
    transmitter = JointTransmitter(
        mode,
        fixed_va=checkpoint_entry["selected_fixed_va_snu"],
        v_min=cvqkd.get("v_min_snu"),
        v_max=cvqkd.get("v_max_snu"),
        reference_distribution="uniform",
        nu_mb=cvqkd.get("mb_nu"),
        n_peak_photons=n_peak,
    )
    transmitter.load_state_dict(checkpoint["model_state_dict"])
    transmitter.eval()
    frozen_evaluation = manifest["test_evaluation"]
    channel_seed = derive_seed(
        frozen_evaluation["channel_seed"], "held_out_test_channel"
    )
    awgn_seed = derive_seed(frozen_evaluation["awgn_seed"], "held_out_test_awgn")
    channel = _channel(config, frozen_evaluation["fading_samples"], channel_seed)
    transmittance = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(channel.excess_noise_snu, dtype=torch.float64)
    with torch.no_grad():
        evaluation = evaluate_transmitter(
            transmitter,
            transmittance,
            epsilon,
            beta_reconciliation=cvqkd["beta_reconciliation"],
            noise_samples_per_symbol=frozen_evaluation["awgn_samples_per_symbol"],
            generator=torch_generator(awgn_seed),
            require_supported_symmetry=True,
            **holevo_numerical_kwargs(config),
        )
    budget_status = heldout_budget_comparison_status(
        float(evaluation.ensemble.declared_va.mean()), va_budget
    )
    payload = {
        "status": (
            "held-out evaluation from pre-test frozen manifest; not yet a claim"
            if budget_status["comparison_valid"] else
            "INVALID_COMPARISON_HELDOUT_ENERGY_BUDGET_VIOLATION"
        ),
        "publication_eligible": bool(budget_status["comparison_valid"]),
        "heldout_budget_validity": budget_status,
        "selection_manifest": str(manifest_path),
        "selection_manifest_sha256": file_sha256(manifest_path),
        "checkpoint": str(checkpoint_path),
        "checkpoint_id": args.checkpoint_id,
        "mode": mode,
        "transmitter_spec": "frozen_c4_v1",
        "seeds": {
            "channel": frozen_evaluation["channel_seed"],
            "awgn": frozen_evaluation["awgn_seed"],
        },
        "derived_seeds": {"channel": channel_seed, "awgn": awgn_seed},
        "channel_metadata": channel.metadata,
        "mean_raw_skr": float(evaluation.key_rate.fading_average_raw),
        "va_budget": va_budget,
        "n_peak_photons": n_peak,
        "peak_photon_constraint_satisfied": True,
        "mean_va": float(evaluation.ensemble.declared_va.mean()),
        "va_budget_feasible": bool(budget_status["heldout_budget_feasible"]),
        "per_state": {
            "transmittance": transmittance.tolist(),
            "epsilon": epsilon.tolist(),
            "i_ab": evaluation.mutual_information.tolist(),
            "chi_be": evaluation.holevo.chi_be.tolist(),
            "raw_skr": evaluation.key_rate.instantaneous_raw.tolist(),
            "declared_va": evaluation.ensemble.declared_va.tolist(),
            **{name: value.tolist() for name, value in evaluation.state_diagnostics.items()},
        },
        "policy": {
            "orbit_masses": c4_orbit_masses(evaluation.ensemble.probabilities).tolist(),
            "probabilities": evaluation.ensemble.probabilities.tolist(),
            "global_relative_geometry_real": evaluation.ensemble.relative_constellation.real.tolist(),
            "global_relative_geometry_imag": evaluation.ensemble.relative_constellation.imag.tolist(),
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
