"""Produce a bounded, prospective audit of C4-Gram support disagreements.

This script does not train, select baselines, evaluate test data, or change the
active numerical rule.  It post-processes the maintained forward-replay
artifact and independently reconstructs the C4 sector spectra needed to list
the eigenvalues that lie between the reference and candidate thresholds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from _common import ROOT, load_yaml
from _numerical_validation import (
    ensemble_sha256,
    representative_ensembles,
    unique_ensemble_roster,
    validation_representative_states,
)
from src.cvqkd.holevo import HolevoResult, holevo_information
from src.modulation.joint_ps_gs import Ensemble
from src.modulation.qam256 import c4_orbit_indices


METRICS = ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
MOMENT_ABSOLUTE_TOLERANCE = 1e-7
MOMENT_RELATIVE_TOLERANCE = 1e-6
INFORMATION_ABSOLUTE_TOLERANCE = 1e-6
INFORMATION_RELATIVE_TOLERANCE = 1e-5
ZERO_SAFE_RELATIVE_DENOMINATOR = 1e-300


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metric_tolerances(metric: str) -> tuple[float, float]:
    if metric in {"chi_BE", "raw_K"}:
        return INFORMATION_ABSOLUTE_TOLERANCE, INFORMATION_RELATIVE_TOLERANCE
    return MOMENT_ABSOLUTE_TOLERANCE, MOMENT_RELATIVE_TOLERANCE


def _comparison(candidate: list[float], reference: list[float], metric: str) -> dict[str, Any]:
    if len(candidate) != len(reference):
        raise ValueError(f"Mismatched state count for {metric}.")
    absolute_tolerance, relative_tolerance = _metric_tolerances(metric)
    absolute_errors = [abs(left - right) for left, right in zip(candidate, reference)]
    relative_errors = [
        error / max(abs(right), ZERO_SAFE_RELATIVE_DENOMINATOR)
        for error, right in zip(absolute_errors, reference)
    ]
    allowed_errors = [
        absolute_tolerance + relative_tolerance * abs(right) for right in reference
    ]
    normalized_errors = [
        error / allowed for error, allowed in zip(absolute_errors, allowed_errors)
    ]
    return {
        "absolute_errors_by_state": absolute_errors,
        "relative_errors_by_state": relative_errors,
        "allowed_errors_by_state": allowed_errors,
        "normalized_error_to_tolerance_by_state": normalized_errors,
        "maximum_absolute_error": max(absolute_errors),
        "maximum_relative_error": max(relative_errors),
        "maximum_normalized_error_to_tolerance": max(normalized_errors),
        "passes_frozen_tolerance": all(error <= allowed for error, allowed in zip(
            absolute_errors, allowed_errors
        )),
    }


def _sector_eigenvalues(ensemble: Ensemble) -> list[list[list[float]]]:
    """Reconstruct exact complex128 C4 block spectra for every batch member."""

    ensemble.validate()
    if not ensemble.c4_symmetric:
        raise ValueError("Support audit requires a declared C4 ensemble.")
    indices = c4_orbit_indices(device=ensemble.probabilities.device)
    rotations = torch.tensor(
        [1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j],
        dtype=torch.complex128,
        device=ensemble.probabilities.device,
    )
    result: list[list[list[float]]] = []
    for batch in range(ensemble.probabilities.shape[0]):
        grouped_probabilities = ensemble.probabilities[batch, indices]
        prototypes = ensemble.amplitudes[batch, indices[:, 0]]
        symbol_probabilities = grouped_probabilities[:, 0]
        square_root_weights = torch.sqrt(
            symbol_probabilities[:, None] * symbol_probabilities[None, :]
        )
        blocks = []
        for difference in range(4):
            rotated = rotations[difference] * prototypes
            overlap = torch.exp(
                -0.5 * (
                    prototypes.abs().square()[:, None]
                    + rotated.abs().square()[None, :]
                )
                + prototypes.conj()[:, None] * rotated[None, :]
            )
            blocks.append(square_root_weights * overlap)
        state = []
        for sector in range(4):
            matrix = sum(
                blocks[difference] * rotations[(sector * difference) % 4]
                for difference in range(4)
            )
            matrix = 0.5 * (matrix + matrix.mH)
            # Match the production evaluator's stable Hermitian decomposition
            # exactly: support is defined from the eigenvalues returned by
            # ``torch.linalg.eigh``, not a separate eigvalsh driver call.
            values, _ = torch.linalg.eigh(matrix)
            state.append(values.detach().tolist())
        result.append(state)
    return result


def _rank_by_state(diagnostics: list[dict[str, Any]]) -> list[int]:
    return [int(row["numerical_retained_rank"]) for row in diagnostics]


def _metric_values_with_raw_k(
    result: HolevoResult, mi: list[float], beta: float
) -> dict[str, list[float]]:
    values = {
        "C": result.coherent_correlation,
        "w": result.w,
        "Z": result.z,
        "lambda1": result.covariance.lambda1,
        "lambda2": result.covariance.lambda2,
        "lambda3": result.covariance.lambda3,
        "chi_BE": result.chi_be,
    }
    serialized = {name: value.detach().tolist() for name, value in values.items()}
    serialized["raw_K"] = [
        beta * value - chi for value, chi in zip(mi, serialized["chi_BE"])
    ]
    return serialized


def build_audit(
    config: dict[str, Any], production: dict[str, Any],
    *, config_path: Path, production_path: Path, output_path: Path,
) -> dict[str, Any]:
    reference_threshold = float(production["forward_reference_threshold"])
    candidate_threshold = float(production["candidate_density_eigenvalue_threshold"])
    active_threshold = float(config["cvqkd"]["holevo_numerics"][
        "density_eigenvalue_pseudoinverse_tolerance"
    ])
    if not reference_threshold < candidate_threshold < active_threshold:
        raise ValueError("Expected reference < proposed candidate < historical active threshold.")
    if config["cvqkd"]["holevo_numerics"].get(
        "density_eigenvalue_pseudoinverse_author_approved"
    ) is not False:
        raise ValueError("This proposed audit requires the active threshold to remain unapproved.")

    states, labels, transmittance, epsilon = validation_representative_states(config)
    complete = representative_ensembles(config, transmittance, epsilon)
    ensembles, aliases = unique_ensemble_roster(complete)
    replay = production["forward_replay"]
    if aliases != replay["exact_duplicate_aliases"]:
        raise ValueError("Canonical alias map differs from the maintained replay artifact.")
    if states.realization_sha256 != replay["validation_state_realization_sha256"]:
        raise ValueError("Validation realization differs from the maintained replay artifact.")
    replay_rows = {row["fixture"]: row for row in replay["rows"]}
    if set(replay_rows) != set(ensembles):
        raise ValueError("Canonical fixture roster differs from the maintained replay artifact.")
    for fixture, ensemble in ensembles.items():
        if ensemble_sha256(ensemble) != replay_rows[fixture]["ensemble_sha256"]:
            raise ValueError(f"Ensemble hash mismatch for {fixture}.")

    beta = float(config["cvqkd"]["beta_reconciliation"])
    holevo_kwargs = {
        "backend": "c4_gram",
        "fock_cutoff": None,
        "require_supported_symmetry": True,
        "symmetry_tolerance": float(config["cvqkd"]["holevo_numerics"]["symmetry_tolerance"]),
        "density_trace_tolerance": float(
            config["cvqkd"]["holevo_numerics"]["density_trace_tolerance"]
        ),
        "physicality_tolerance": float(
            config["cvqkd"]["holevo_numerics"]["physicality_tolerance"]
        ),
    }
    changed_rows = []
    all_rows = []
    worst_candidate_ratio = 0.0
    worst_active_ratio = 0.0
    for fixture, ensemble in ensembles.items():
        source = replay_rows[fixture]
        reference_record = source["reference_1e_minus_14"]
        candidate_record = source["production_1e_minus_13"]
        reference_values = reference_record["values"]
        candidate_values = candidate_record["values"]
        active_result = holevo_information(
            ensemble,
            transmittance,
            epsilon,
            density_eigenvalue_tolerance=active_threshold,
            **holevo_kwargs,
        )
        active_values = _metric_values_with_raw_k(
            active_result, source["mutual_information_source"]["mi_bits"], beta
        )
        candidate_comparison = {
            metric: _comparison(candidate_values[metric], reference_values[metric], metric)
            for metric in METRICS
        }
        active_comparison = {
            metric: _comparison(active_values[metric], reference_values[metric], metric)
            for metric in METRICS
        }
        worst_candidate_ratio = max(
            worst_candidate_ratio,
            *(row["maximum_normalized_error_to_tolerance"] for row in candidate_comparison.values()),
        )
        worst_active_ratio = max(
            worst_active_ratio,
            *(row["maximum_normalized_error_to_tolerance"] for row in active_comparison.values()),
        )
        reference_diagnostics = reference_record["source_diagnostics_by_state"]
        candidate_diagnostics = candidate_record["source_diagnostics_by_state"]
        reference_ranks = _rank_by_state(reference_diagnostics)
        candidate_ranks = _rank_by_state(candidate_diagnostics)
        support_changed = not source["support_plateau"]["support_identical"]
        summary = {
            "fixture": fixture,
            "ensemble_sha256": source["ensemble_sha256"],
            "support_changed": support_changed,
            "reference_retained_rank_by_state": reference_ranks,
            "candidate_retained_rank_by_state": candidate_ranks,
            "candidate_comparison_to_reference": candidate_comparison,
            "active_comparison_to_reference": active_comparison,
        }
        all_rows.append(summary)
        if not support_changed:
            continue

        spectra = _sector_eigenvalues(ensemble)
        between_by_state = []
        for state_index, sectors in enumerate(spectra):
            entries = []
            for sector_index, values in enumerate(sectors):
                for value in values:
                    if reference_threshold < value <= candidate_threshold:
                        entries.append({"sector": sector_index, "eigenvalue": value})
            entries.sort(key=lambda row: row["eigenvalue"])
            expected_loss = reference_ranks[state_index] - candidate_ranks[state_index]
            if len(entries) != expected_loss:
                raise ValueError(
                    f"Between-threshold spectrum count mismatch for {fixture}/{labels[state_index]}: "
                    f"observed {len(entries)}, expected {expected_loss}."
                )
            between_by_state.append({
                "state": labels[state_index],
                "transmittance": float(transmittance[state_index]),
                "epsilon_snu": float(epsilon[state_index]),
                "rank_reference": reference_ranks[state_index],
                "rank_candidate": candidate_ranks[state_index],
                "between_threshold_eigenvalues": entries,
            })
        changed_rows.append({
            **summary,
            "between_threshold_eigenvalues_by_state": between_by_state,
            "reference_values": reference_values,
            "candidate_values": candidate_values,
        })

    if len(changed_rows) != int(replay["support_changed_fixture_count"]):
        raise ValueError("Support-disagreement count differs from maintained replay artifact.")
    candidate_all_pass = all(
        detail["passes_frozen_tolerance"]
        for row in all_rows
        for detail in row["candidate_comparison_to_reference"].values()
    )
    active_all_pass = all(
        detail["passes_frozen_tolerance"]
        for row in all_rows
        for detail in row["active_comparison_to_reference"].values()
    )

    dependencies = {
        "config": config_path,
        "production_forward_artifact": production_path,
        "mi_convergence_artifact": ROOT / "results" / "mi_convergence.json",
        "high_precision_oracle_artifact": ROOT / "results" / "near_coincident_gram_oracle.json",
        "final_model_spec": ROOT / "docs" / "FINAL_MODEL_SPEC.md",
        "gram_implementation": ROOT / "src" / "cvqkd" / "gram_moments.py",
        "holevo_implementation": ROOT / "src" / "cvqkd" / "holevo.py",
        "audit_script": Path(__file__).resolve(),
    }
    missing = [name for name, path in dependencies.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing provenance dependencies: " + ", ".join(missing))
    dependency_hashes = {
        name: {"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)}
        for name, path in dependencies.items()
    }
    final_spec_hash = dependency_hashes["final_model_spec"]["sha256"]
    if final_spec_hash != "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1":
        raise ValueError("FINAL_MODEL_SPEC.md hash changed.")

    return {
        "schema_version": "support-threshold-protocol-audit-v1",
        "status": "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        "preregistered_design": {
            "scope": "sixteen hash-bound canonical fixtures on bad/medium/good validation states",
            "reference_threshold": reference_threshold,
            "candidate_threshold": candidate_threshold,
            "historical_active_threshold": active_threshold,
            "declared_observables": list(METRICS),
            "candidate_comparators": [candidate_threshold, active_threshold],
            "comparison_reference": reference_threshold,
            "moment_and_symplectic_tolerance": {
                "absolute": MOMENT_ABSOLUTE_TOLERANCE,
                "relative": MOMENT_RELATIVE_TOLERANCE,
            },
            "information_tolerance_bits": {
                "absolute": INFORMATION_ABSOLUTE_TOLERANCE,
                "relative": INFORMATION_RELATIVE_TOLERANCE,
            },
            "pass_formula": "abs(candidate-reference) <= absolute + relative*abs(reference)",
            "relative_error_formula": (
                "abs(candidate-reference)/max(abs(reference),1e-300); relative error is "
                "reported diagnostically and is not the frozen pass criterion"
            ),
            "support_identity_interpretation": (
                "recorded diagnostically; this artifact does not activate a replacement gate"
            ),
            "between_threshold_interval": "reference < eigenvalue <= candidate",
            "acceptance_interpretation": (
                "observable pass supports protocol review only; it is not threshold approval, "
                "production certification, or permission to train"
            ),
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
        "validation_state_realization_sha256": states.realization_sha256,
        "certification_roster_sha256": replay["certification_roster_sha256"],
        "state_labels": labels,
        "support_disagreement_count": len(changed_rows),
        "support_agreement_count": len(all_rows) - len(changed_rows),
        "support_disagreements": changed_rows,
        "candidate_threshold_assessment": {
            "candidate": candidate_threshold,
            "reference": reference_threshold,
            "all_declared_observables_pass": candidate_all_pass,
            "worst_normalized_error_to_frozen_tolerance": worst_candidate_ratio,
            "support_identity_passes": len(changed_rows) == 0,
            "status": "PROPOSED_NOT_APPROVED",
        },
        "historical_active_threshold_assessment": {
            "active": active_threshold,
            "reference": reference_threshold,
            "all_declared_observables_pass": active_all_pass,
            "worst_normalized_error_to_frozen_tolerance": worst_active_ratio,
            "status": "HISTORICAL_ACTIVE_INVALID_UNAPPROVED",
        },
        "all_fixture_comparison_summary": all_rows,
        "conclusion_scope": (
            "finite canonical realized-domain diagnostic only; no uniform continuous-domain claim"
        ),
        "provenance": {
            "input_and_source_hashes": dependency_hashes,
            "production_artifact_embedded_provenance": production["provenance"],
            "output_path": str(output_path.relative_to(ROOT)),
            "precision": "torch.float64 / torch.complex128 CPU sector reconstruction",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--production-artifact", type=Path,
        default=ROOT / "results" / "production_gram_certification.json",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "support_threshold_protocol_audit.json",
    )
    args = parser.parse_args()
    config = load_yaml(args.config)
    production = json.loads(args.production_artifact.read_text(encoding="utf-8"))
    audit = build_audit(
        config, production, config_path=args.config.resolve(),
        production_path=args.production_artifact.resolve(),
        output_path=args.output.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": audit["status"],
        "support_disagreement_count": audit["support_disagreement_count"],
        "candidate_threshold_assessment": audit["candidate_threshold_assessment"],
        "historical_active_threshold_assessment": audit[
            "historical_active_threshold_assessment"
        ],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
