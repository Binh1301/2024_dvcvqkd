"""Prospectively audit fail-closed support-stable optimizer proposals.

The proposals are synthetic unit-norm parameter perturbations.  They are not
optimizer steps from a loss, do not train the transmitter, and use only the
three hash-bound representative validation states.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any

import torch

from _common import ROOT, load_yaml
from _numerical_validation import validation_representative_states
from audit_support_threshold_protocol import _sector_eigenvalues
from src.modulation.joint_ps_gs import JointTransmitter
from src.utils.random import derive_seed


INITIALIZATION_SEED = 202613
CANDIDATE_THRESHOLD = 1e-13
PROPOSALS_PER_CELL = 64
MULTIPLIERS = (1, 3, 10, 30, 100)
NOMINAL_LEARNING_RATES = {"ps": 3e-4, "gs": 1e-4, "va": 1e-4}
FAMILIES = ("ps", "gs", "va")
TRAJECTORY_COUNT_PER_FAMILY = 8
TRAJECTORY_HORIZON = 32
TRAJECTORY_MULTIPLIER = 100


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tensor_map_sha256(values: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(values):
        value = values[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _family_parameters(model: JointTransmitter, family: str) -> dict[str, torch.Tensor]:
    prefix = {"ps": "ps_network.", "gs": "gs_model.", "va": "va_network."}[family]
    result = {
        name: parameter for name, parameter in model.named_parameters()
        if name.startswith(prefix)
    }
    if not result:
        raise ValueError(f"Full model has no {family} parameters.")
    return result


def _unit_direction(
    parameters: dict[str, torch.Tensor], *, family: str, proposal_index: int,
    namespace: str = "support_rollback",
) -> tuple[dict[str, torch.Tensor], int, str]:
    seed = derive_seed(INITIALIZATION_SEED, f"{namespace}_{family}", proposal_index)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    direction = {
        name: torch.randn(
            parameter.shape, dtype=parameter.dtype, device="cpu", generator=generator
        )
        for name, parameter in parameters.items()
    }
    norm = torch.sqrt(sum(torch.sum(value.square()) for value in direction.values()))
    if not bool(torch.isfinite(norm)) or float(norm) == 0.0:
        raise FloatingPointError("Unable to construct a finite nonzero proposal direction.")
    direction = {name: value / norm for name, value in direction.items()}
    observed_norm = torch.sqrt(sum(torch.sum(value.square()) for value in direction.values()))
    if not torch.allclose(observed_norm, torch.ones_like(observed_norm), rtol=0.0, atol=1e-14):
        raise FloatingPointError("Proposal direction is not unit norm.")
    return direction, seed, _tensor_map_sha256(direction)


def _support_snapshot(
    model: JointTransmitter, transmittance: torch.Tensor, epsilon: torch.Tensor,
) -> dict[str, Any]:
    with torch.no_grad():
        ensemble = model(transmittance, epsilon)
        spectra = _sector_eigenvalues(ensemble)
    masks = []
    states = []
    for sectors in spectra:
        sector_masks = [[value > CANDIDATE_THRESHOLD for value in values] for values in sectors]
        flat = [value for values in sectors for value in values]
        nearest = min(flat, key=lambda value: abs(value - CANDIDATE_THRESHOLD))
        masks.append(sector_masks)
        states.append({
            "retained_rank": sum(sum(mask) for mask in sector_masks),
            "sector_retained_ranks": [sum(mask) for mask in sector_masks],
            "nearest_eigenvalue_to_threshold": nearest,
            "absolute_distance_to_threshold": abs(nearest - CANDIDATE_THRESHOLD),
            "relative_distance_to_threshold": abs(nearest - CANDIDATE_THRESHOLD)
            / CANDIDATE_THRESHOLD,
        })
    return {"masks": masks, "states": states}


def _restore(parameters: dict[str, torch.Tensor], base: dict[str, torch.Tensor]) -> None:
    with torch.no_grad():
        for name, parameter in parameters.items():
            parameter.copy_(base[name])


def _parameter_distance(
    parameters: dict[str, torch.Tensor], base: dict[str, torch.Tensor]
) -> float:
    return float(torch.sqrt(sum(
        torch.sum((parameter.detach() - base[name]).square())
        for name, parameter in parameters.items()
    )))


def _physical_motion(
    model: JointTransmitter, transmittance: torch.Tensor, epsilon: torch.Tensor,
    base_probabilities: torch.Tensor, base_amplitudes: torch.Tensor,
    base_va: torch.Tensor,
) -> dict[str, float]:
    with torch.no_grad():
        ensemble = model(transmittance, epsilon)
    return {
        "maximum_probability_l1_by_state": float(
            torch.sum(torch.abs(ensemble.probabilities - base_probabilities), dim=-1).max()
        ),
        "maximum_amplitude_rms_by_state": float(torch.sqrt(
            torch.mean(torch.abs(ensemble.amplitudes - base_amplitudes).square(), dim=-1)
        ).max()),
        "maximum_va_absolute_change_snu": float(
            torch.abs(ensemble.declared_va - base_va).max()
        ),
    }


def _run_rollback_trajectories(
    model: JointTransmitter, all_parameters: dict[str, torch.Tensor],
    base_parameters: dict[str, torch.Tensor], base_snapshot: dict[str, Any],
    transmittance: torch.Tensor, epsilon: torch.Tensor,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run predeclared objective-free random walks with segment rollback."""

    _restore(all_parameters, base_parameters)
    with torch.no_grad():
        base_ensemble = model(transmittance, epsilon)
        base_probabilities = base_ensemble.probabilities.detach().clone()
        base_amplitudes = base_ensemble.amplitudes.detach().clone()
        base_va = base_ensemble.declared_va.detach().clone()
    rows = []
    aggregates = []
    for family in FAMILIES:
        family_parameters = _family_parameters(model, family)
        step_norm = NOMINAL_LEARNING_RATES[family] * TRAJECTORY_MULTIPLIER
        family_rows = []
        for trajectory_index in range(TRAJECTORY_COUNT_PER_FAMILY):
            _restore(all_parameters, base_parameters)
            current_snapshot = base_snapshot
            accepted = 0
            support_rejected = 0
            invalid_rejected = 0
            segment_rows = []
            for step_index in range(TRAJECTORY_HORIZON):
                current_parameters = {
                    name: value.detach().clone() for name, value in all_parameters.items()
                }
                proposal_index = trajectory_index * TRAJECTORY_HORIZON + step_index
                direction, direction_seed, direction_sha256 = _unit_direction(
                    family_parameters, family=family, proposal_index=proposal_index,
                    namespace="support_rollback_walk",
                )
                with torch.no_grad():
                    for name, parameter in family_parameters.items():
                        parameter.add_(step_norm * direction[name])
                try:
                    proposed_snapshot = _support_snapshot(model, transmittance, epsilon)
                    changed_states = [
                        index for index, (left, right) in enumerate(zip(
                            current_snapshot["masks"], proposed_snapshot["masks"]
                        )) if left != right
                    ]
                    if changed_states:
                        status = "rejected_support_transition_rolled_back"
                        support_rejected += 1
                        _restore(all_parameters, current_parameters)
                    else:
                        status = "accepted_support_stable"
                        accepted += 1
                        current_snapshot = proposed_snapshot
                except (ValueError, FloatingPointError, RuntimeError) as caught:
                    changed_states = []
                    status = "rejected_invalid_rolled_back"
                    invalid_rejected += 1
                    _restore(all_parameters, current_parameters)
                    proposed_snapshot = None
                    error = f"{type(caught).__name__}: {caught}"
                else:
                    error = None
                segment_rows.append({
                    "step_index": step_index,
                    "direction_seed": direction_seed,
                    "direction_sha256": direction_sha256,
                    "status": status,
                    "changed_state_indices": changed_states,
                    "error": error,
                })
            motion = _physical_motion(
                model, transmittance, epsilon, base_probabilities, base_amplitudes, base_va
            )
            row = {
                "family": family,
                "trajectory_index": trajectory_index,
                "horizon": TRAJECTORY_HORIZON,
                "step_norm": step_norm,
                "accepted_step_count": accepted,
                "rejected_support_transition_count": support_rejected,
                "rejected_invalid_count": invalid_rejected,
                "accepted_step_fraction": accepted / TRAJECTORY_HORIZON,
                "net_parameter_l2_motion": _parameter_distance(all_parameters, base_parameters),
                "net_physical_motion": motion,
                "trapped_no_accepted_motion": accepted == 0,
                "segment_rows": segment_rows,
            }
            rows.append(row)
            family_rows.append(row)
        aggregates.append({
            "family": family,
            "trajectory_count": len(family_rows),
            "horizon": TRAJECTORY_HORIZON,
            "step_norm": step_norm,
            "accepted_step_fraction": sum(
                row["accepted_step_count"] for row in family_rows
            ) / (len(family_rows) * TRAJECTORY_HORIZON),
            "trapped_trajectory_count": sum(
                row["trapped_no_accepted_motion"] for row in family_rows
            ),
            "minimum_net_parameter_l2_motion": min(
                row["net_parameter_l2_motion"] for row in family_rows
            ),
            "maximum_net_parameter_l2_motion": max(
                row["net_parameter_l2_motion"] for row in family_rows
            ),
        })
    _restore(all_parameters, base_parameters)
    return aggregates, rows


def run_grid(
    config: dict[str, Any], *, proposals_per_cell: int, config_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    if proposals_per_cell <= 0:
        raise ValueError("proposals_per_cell must be positive.")
    active = float(config["cvqkd"]["holevo_numerics"][
        "density_eigenvalue_pseudoinverse_tolerance"
    ])
    if active != 1e-12:
        raise ValueError("Historical active 1e-12 rule unexpectedly changed.")
    if config["cvqkd"]["holevo_numerics"].get(
        "density_eigenvalue_pseudoinverse_author_approved"
    ) is not False:
        raise ValueError("This prospective audit requires the active rule to remain unapproved.")

    validation, labels, transmittance, epsilon = validation_representative_states(config)
    cvqkd = config["cvqkd"]
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(INITIALIZATION_SEED)
        model = JointTransmitter(
            "full",
            v_min=float(cvqkd["v_min_snu"]),
            v_max=float(cvqkd["v_max_snu"]),
            n_peak_photons=float(cvqkd["n_peak_photons"]),
        )
    all_parameters = {name: value for name, value in model.named_parameters()}
    base_parameters = {name: value.detach().clone() for name, value in all_parameters.items()}
    base_parameter_sha256 = _tensor_map_sha256(base_parameters)
    base_snapshot = _support_snapshot(model, transmittance, epsilon)

    started = time.perf_counter()
    rows = []
    aggregates = []
    for family in FAMILIES:
        family_parameters = _family_parameters(model, family)
        for multiplier in MULTIPLIERS:
            step_norm = NOMINAL_LEARNING_RATES[family] * multiplier
            accepted = 0
            support_rejected = 0
            invalid_rejected = 0
            cell_rows = []
            for proposal_index in range(proposals_per_cell):
                direction, direction_seed, direction_sha256 = _unit_direction(
                    family_parameters, family=family, proposal_index=proposal_index
                )
                _restore(all_parameters, base_parameters)
                with torch.no_grad():
                    for name, parameter in family_parameters.items():
                        parameter.add_(step_norm * direction[name])
                observed_delta = {
                    name: parameter.detach() - base_parameters[name]
                    for name, parameter in all_parameters.items()
                    if name in family_parameters
                }
                observed_step_norm = float(torch.sqrt(sum(
                    torch.sum(value.square()) for value in observed_delta.values()
                )))
                status = "accepted_support_stable"
                proposed_snapshot = None
                error = None
                try:
                    proposed_snapshot = _support_snapshot(model, transmittance, epsilon)
                    changed_states = [
                        index for index, (left, right) in enumerate(zip(
                            base_snapshot["masks"], proposed_snapshot["masks"]
                        )) if left != right
                    ]
                    if changed_states:
                        status = "rejected_support_transition"
                        support_rejected += 1
                    else:
                        accepted += 1
                except (ValueError, FloatingPointError, RuntimeError) as caught:
                    changed_states = []
                    status = "rejected_invalid_proposal"
                    error = f"{type(caught).__name__}: {caught}"
                    invalid_rejected += 1
                state_changes = []
                if proposed_snapshot is not None:
                    for index in changed_states:
                        state_changes.append({
                            "state": labels[index],
                            "rank_before": base_snapshot["states"][index]["retained_rank"],
                            "rank_after": proposed_snapshot["states"][index]["retained_rank"],
                            "sector_ranks_before": base_snapshot["states"][index][
                                "sector_retained_ranks"
                            ],
                            "sector_ranks_after": proposed_snapshot["states"][index][
                                "sector_retained_ranks"
                            ],
                            "nearest_eigenvalue_after": proposed_snapshot["states"][index][
                                "nearest_eigenvalue_to_threshold"
                            ],
                            "distance_to_threshold_after": proposed_snapshot["states"][index][
                                "absolute_distance_to_threshold"
                            ],
                        })
                record = {
                    "family": family,
                    "multiplier": multiplier,
                    "proposal_index": proposal_index,
                    "direction_seed": direction_seed,
                    "direction_sha256": direction_sha256,
                    "nominal_learning_rate": NOMINAL_LEARNING_RATES[family],
                    "declared_step_norm": step_norm,
                    "observed_step_norm": observed_step_norm,
                    "status": status,
                    "changed_state_count": len(changed_states),
                    "state_changes": state_changes,
                    "minimum_postproposal_distance_to_threshold": (
                        min(row["absolute_distance_to_threshold"] for row in proposed_snapshot["states"])
                        if proposed_snapshot is not None else None
                    ),
                    "error": error,
                }
                rows.append(record)
                cell_rows.append(record)
            total = accepted + support_rejected + invalid_rejected
            aggregates.append({
                "family": family,
                "multiplier": multiplier,
                "nominal_learning_rate": NOMINAL_LEARNING_RATES[family],
                "step_norm": step_norm,
                "proposal_count": total,
                "accepted_support_stable_count": accepted,
                "rejected_support_transition_count": support_rejected,
                "rejected_invalid_count": invalid_rejected,
                "support_transition_fraction": support_rejected / total,
                "fail_closed_rejection_fraction": (support_rejected + invalid_rejected) / total,
                "minimum_observed_postproposal_distance_to_threshold": min(
                    row["minimum_postproposal_distance_to_threshold"]
                    for row in cell_rows
                    if row["minimum_postproposal_distance_to_threshold"] is not None
                ),
            })
    _restore(all_parameters, base_parameters)
    trajectory_aggregates, trajectory_rows = _run_rollback_trajectories(
        model, all_parameters, base_parameters, base_snapshot, transmittance, epsilon
    )
    if _tensor_map_sha256({name: value.detach() for name, value in all_parameters.items()}) != base_parameter_sha256:
        raise RuntimeError("Model parameters were not restored after the diagnostic grid.")

    dependencies = {
        "config": config_path,
        "final_model_spec": ROOT / "docs" / "FINAL_MODEL_SPEC.md",
        "joint_transmitter": ROOT / "src" / "modulation" / "joint_ps_gs.py",
        "gram_implementation": ROOT / "src" / "cvqkd" / "gram_moments.py",
        "support_spectrum_helper": ROOT / "scripts" / "audit_support_threshold_protocol.py",
        "audit_script": Path(__file__).resolve(),
    }
    hashes = {
        name: {"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)}
        for name, path in dependencies.items()
    }
    if hashes["final_model_spec"]["sha256"] != (
        "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
    ):
        raise ValueError("FINAL_MODEL_SPEC.md hash changed.")
    total_proposals = len(rows)
    total_support_rejections = sum(
        row["status"] == "rejected_support_transition" for row in rows
    )
    total_invalid = sum(row["status"] == "rejected_invalid_proposal" for row in rows)
    deterministic_outcomes = {
        "base_support": base_snapshot["states"],
        "aggregate_by_family_multiplier": aggregates,
        "proposal_rows": rows,
        "rollback_trajectory_aggregate_by_family": trajectory_aggregates,
        "rollback_trajectory_rows": trajectory_rows,
    }
    return {
        "schema_version": "support-rollback-feasibility-v1",
        "status": "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        "preregistered_design": {
            "candidate_threshold": CANDIDATE_THRESHOLD,
            "initialization_seed": INITIALIZATION_SEED,
            "model_mode": "full",
            "proposal_families": list(FAMILIES),
            "nominal_learning_rates": NOMINAL_LEARNING_RATES,
            "multipliers": list(MULTIPLIERS),
            "proposals_per_family_multiplier_cell": proposals_per_cell,
            "direction_rule": (
                "one independent namespaced torch.float64 Gaussian parameter vector per "
                "family/proposal index, normalized jointly across that family's parameters; "
                "the same direction is reused across multipliers"
            ),
            "proposal_rule": "theta_proposed = theta_initial + multiplier*nominal_lr*unit_direction",
            "acceptance_rule": (
                "accept only if every C4 sector support mask at bad/medium/good remains "
                "bitwise identical; invalid evaluations fail closed separately"
            ),
            "interpretation": (
                "synthetic feasibility diagnostic only; not loss-gradient optimization, "
                "threshold approval, or a frozen protocol"
            ),
            "rollback_trajectory_design": {
                "trajectory_count_per_family": TRAJECTORY_COUNT_PER_FAMILY,
                "horizon": TRAJECTORY_HORIZON,
                "multiplier": TRAJECTORY_MULTIPLIER,
                "step_norm_by_family": {
                    family: NOMINAL_LEARNING_RATES[family] * TRAJECTORY_MULTIPLIER
                    for family in FAMILIES
                },
                "direction_rule": (
                    "independent deterministic namespaced unit-Gaussian direction per segment"
                ),
                "rollback_rule": (
                    "compare each proposed segment to its current accepted support; on any "
                    "mask change or invalid evaluation restore the exact prior parameters"
                ),
                "objective_used": False,
                "trapping_diagnostic": (
                    "accepted-step fraction, zero-accepted trajectory count, net parameter "
                    "motion, PMF L1 motion, physical-amplitude RMS motion, and VA motion"
                ),
            },
        },
        "lifecycle_guards": {
            "publication_training_performed": False,
            "test_set_accessed": False,
            "final_held_out_evaluation_performed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "active_config_changed": False,
            "physical_or_security_functional_changed": False,
        },
        "validation_state_realization_sha256": validation.realization_sha256,
        "state_labels": labels,
        "transmittance": transmittance.tolist(),
        "epsilon_snu": epsilon.tolist(),
        "base_parameter_sha256": base_parameter_sha256,
        "base_support": base_snapshot["states"],
        "aggregate_by_family_multiplier": aggregates,
        "proposal_rows": rows,
        "rollback_trajectory_aggregate_by_family": trajectory_aggregates,
        "rollback_trajectory_rows": trajectory_rows,
        "deterministic_outcomes_sha256": _json_sha256(deterministic_outcomes),
        "overall": {
            "proposal_count": total_proposals,
            "rejected_support_transition_count": total_support_rejections,
            "rejected_invalid_count": total_invalid,
            "support_transition_fraction": total_support_rejections / total_proposals,
            "fail_closed_rejection_fraction": (
                total_support_rejections + total_invalid
            ) / total_proposals,
        },
        "runtime_seconds": time.perf_counter() - started,
        "conclusion_scope": (
            "one deterministic initialization and three representative validation states; "
            "no global optimization-domain feasibility claim"
        ),
        "provenance": {
            "input_and_source_hashes": hashes,
            "output_path": str(output_path.relative_to(ROOT)),
            "precision": "torch.float64 / torch.complex128 CPU support spectra",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--proposals-per-cell", type=int, default=PROPOSALS_PER_CELL)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "support_rollback_feasibility.json",
    )
    args = parser.parse_args()
    result = run_grid(
        load_yaml(args.config), proposals_per_cell=args.proposals_per_cell,
        config_path=args.config.resolve(), output_path=args.output.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "overall": result["overall"],
        "runtime_seconds": result["runtime_seconds"],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
