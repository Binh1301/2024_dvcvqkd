"""Validate derivative enclosures and fail closed without a rigorous eigensolver bound."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import torch

from _common import ROOT, load_yaml
from src.modulation.joint_ps_gs import JointTransmitter
from src.validation.whole_segment_support import (
    certify_segment_by_bisection,
    certify_support_from_validated_intervals,
    gram_derivative_frobenius_bound,
    transmitter_segment_bounds,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gram(ensemble) -> np.ndarray:
    probability = ensemble.probabilities[0].detach().numpy()
    amplitude = ensemble.amplitudes[0].detach().numpy()
    root = np.sqrt(probability)
    return root[:, None] * root[None, :] * np.exp(
        -0.5 * (np.abs(amplitude)[:, None] ** 2 + np.abs(amplitude)[None, :] ** 2)
        + amplitude.conj()[:, None] * amplitude[None, :]
    )


def endpoint_model(start: JointTransmitter, family: str, seed: int,
                   scales: dict[str, float]) -> JointTransmitter:
    end = copy.deepcopy(start)
    generator = torch.Generator().manual_seed(seed)
    selected = ("ps", "gs", "va") if family == "mixed" else (family,)
    with torch.no_grad():
        for name, parameter in end.named_parameters():
            owner = "ps" if name.startswith("ps_network") else "gs" if name.startswith("gs_model") else "va"
            if owner in selected:
                parameter.add_(
                    float(scales[owner])
                    * torch.randn(parameter.shape, dtype=parameter.dtype, generator=generator)
                )
    return end


def interpolated_model(start: JointTransmitter, end: JointTransmitter,
                       fraction: float) -> JointTransmitter:
    trial = copy.deepcopy(start)
    with torch.no_grad():
        for (_, target), (_, left), (_, right) in zip(
            trial.named_parameters(), start.named_parameters(), end.named_parameters()
        ):
            target.copy_(left + fraction * (right - left))
    return trial


def run(config_path: Path, default_config_path: Path, roster_path: Path,
        environment_path: Path, schema_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    default = load_yaml(default_config_path)
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    if roster["status"] != "FROZEN_OUTCOME_UNINSPECTED":
        raise ValueError("Independent roster was not frozen before evaluation.")
    threshold = float(settings["candidate_threshold_under_evaluation"])
    if settings["threshold_approval_permitted"] is not False:
        raise ValueError("This diagnostic must not approve a threshold.")

    no_crossing = certify_segment_by_bisection(
        lambda t: ([0.1, 0.8 + 0.02 * t], [0.1, 0.8 + 0.02 * t]),
        lambda left, right: 0.02,
        retained_rank=1, threshold=0.5, numerical_radius=0.0,
        maximum_depth=8, minimum_interval_width=2.0 ** -8,
    )
    crossing = certify_segment_by_bisection(
        lambda t: ([0.1, 0.51 - 0.04 * t], [0.1, 0.51 - 0.04 * t]),
        lambda left, right: 0.04,
        retained_rank=1, threshold=0.5, numerical_radius=0.0,
        maximum_depth=10, minimum_interval_width=2.0 ** -10,
    )

    torch.manual_seed(int(settings["segment_seed"]))
    start = JointTransmitter(
        "full",
        v_min=float(default["cvqkd"]["v_min_snu"]),
        v_max=float(default["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(default["cvqkd"]["n_peak_photons"]),
    )
    scales = settings["parameter_family_scales"]
    endpoints = {
        family: endpoint_model(start, family, int(settings["segment_seed"]) + index + 1, scales)
        for index, family in enumerate(("ps", "gs", "va", "mixed"))
    }
    nodes = np.linspace(0.0, 1.0, int(settings["diagnostic_nodes"]))
    rows: list[dict[str, Any]] = []
    for state in roster["representative_states"]:
        t = float(state["transmittance"])
        epsilon = float(state["epsilon_snu"])
        for family, end in endpoints.items():
            bounds = transmitter_segment_bounds(start, end, t, epsilon)
            derivative_bound = gram_derivative_frobenius_bound(bounds)
            matrices = []
            diagnostic_ranks = []
            nearest_gaps = []
            for node in nodes:
                ensemble = interpolated_model(start, end, float(node))(
                    torch.tensor([t], dtype=torch.float64),
                    torch.tensor([epsilon], dtype=torch.float64),
                )
                matrix = gram(ensemble)
                matrices.append(matrix)
                eigenvalues = np.linalg.eigvalsh(0.5 * (matrix + matrix.conj().T))
                rank = int(np.sum(eigenvalues > threshold))
                diagnostic_ranks.append(rank)
                nearest_gaps.append(float(np.min(np.abs(eigenvalues - threshold))))
            initial_eigenvalues = np.linalg.eigvalsh(0.5 * (matrices[0] + matrices[0].conj().T))
            initial_rank = int(np.sum(initial_eigenvalues > threshold))
            certificate = certify_support_from_validated_intervals(
                initial_eigenvalues, initial_eigenvalues,
                retained_rank=max(1, initial_rank), threshold=threshold,
                variation_radius=derivative_bound, numerical_radius=None,
            )
            observed_endpoint_change = float(np.linalg.norm(matrices[-1] - matrices[0], ord="fro"))
            rows.append({
                "state_label": state["label"],
                "family": family,
                "candidate_threshold_under_evaluation": threshold,
                "gram_derivative_frobenius_upper_bound": derivative_bound,
                "observed_endpoint_change_diagnostic": observed_endpoint_change,
                "bound_to_observed_ratio": derivative_bound / max(observed_endpoint_change, np.finfo(float).tiny),
                "initial_float64_retained_rank_diagnostic": initial_rank,
                "finite_node_rank_sequence_diagnostic_only": diagnostic_ranks,
                "minimum_finite_node_gap_diagnostic_only": min(nearest_gaps),
                "validated_initial_eigensystem_enclosure_available": False,
                "whole_segment_support_certified": certificate.certified,
                "fail_closed_reason": certificate.reason,
                "derivative_chain": list(bounds.derivative_chain),
            })
    artifact: dict[str, Any] = {
        "schema_version": "whole-segment-support-enclosure-validation-v1",
        "status": "EXPERIMENTAL_DERIVATIVE_ENCLOSURE_INITIAL_EIGENSYSTEM_BLOCKED",
        "method_scope": {
            "derivative_bound": "outward-expanded interval values and absolute derivative bounds through the full PS/GS/VA chain",
            "support_rule": "Weyl midpoint guard with fail-closed adaptive bisection",
            "finite_nodes_are_proof": False,
            "validated_initial_eigensystem_enclosure": False,
            "threshold_approval": False,
        },
        "synthetic_regressions": {
            "obvious_no_crossing_certified": no_crossing.certified,
            "known_crossing_rejected": not crossing.certified,
            "known_crossing_unresolved_interval_count": len(crossing.unresolved_intervals),
        },
        "confirmation_roster_sha256": sha256(roster_path),
        "confirmation_roster_payload_sha256": roster["roster_payload_sha256"],
        "segment_rows": rows,
        "aggregate": {
            "row_count": len(rows),
            "derivative_enclosure_endpoint_diagnostics_pass": all(
                row["observed_endpoint_change_diagnostic"] <= row["gram_derivative_frobenius_upper_bound"]
                for row in rows
            ),
            "whole_segment_support_certificate_count": sum(
                int(row["whole_segment_support_certified"]) for row in rows
            ),
            "all_whole_segment_support_certificates_pass": all(
                row["whole_segment_support_certified"] for row in rows
            ),
            "blocking_component": "validated_initial_gram_assembly_and_hermitian_eigensystem_enclosure_eta_num",
        },
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "module_sha256": sha256(ROOT / "src" / "validation" / "whole_segment_support.py"),
            "config_sha256": sha256(config_path),
            "default_config_sha256": sha256(default_config_path),
            "roster_sha256": sha256(roster_path),
            "environment_manifest_sha256": sha256(environment_path),
            "schema_sha256": sha256(schema_path),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "whole_segment_support_enclosure.yaml")
    parser.add_argument("--default-config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--roster", type=Path, default=ROOT / "results" / "independent_confirmation_roster.json")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "current_environment_manifest.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "whole_segment_support_enclosure.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "whole_segment_support_enclosure_validation.json")
    args = parser.parse_args()
    artifact = run(args.config, args.default_config, args.roster, args.environment, args.schema, args.output)
    print(json.dumps({"status": artifact["status"], **artifact["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
