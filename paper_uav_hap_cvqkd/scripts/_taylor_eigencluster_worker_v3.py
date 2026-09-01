"""One V3 coefficient-congruence/sequential-Schur segment worker.

The parent places this process in a Windows Job Object.  The worker commits
path-domain evidence before spectral work and fsyncs NODE_STARTED/NODE_COMMITTED
events so timeout recovery never depends on its in-memory counters.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Sequence

import numpy as np
from flint import acb, arb, ctx

try:
    from _common import ROOT, load_yaml
except ModuleNotFoundError:
    from scripts._common import ROOT, load_yaml
from src.validation.coefficient_taylor_v3 import (
    build_c4_sector_taylor_models,
    evaluate_taylor_model_enclosure,
    shifted_rounded_congruence_taylor_model,
)
from src.validation.durable_journal_v3 import DurableJournal
from src.validation.rigorous_flint_support import (
    BallTransmitterPath,
    exact_arb_from_fraction,
)
from src.validation.rigorous_shifted_inertia_segment import frobenius_perturbation_upper
from src.validation.rigorous_shifted_inertia import shift_hermitian
from src.validation.rigorous_taylor_eigencluster_v2 import (
    certify_rounded_basis,
    exact_congruence_enclosure,
)
from src.validation.sequential_schur_v3 import sequential_signed_schur_reduction
from src.validation.validated_scalar_taylor_v2 import TaylorTransmitterPath


def _durable_atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.perf_counter_ns()}")
    encoded = (json.dumps(
        payload, indent=2, sort_keys=True, allow_nan=False,
    ) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _complex_midpoint(value: acb) -> complex:
    return complex(float(value.real.mid()), float(value.imag.mid()))


def _midpoint_eigensystem(
    sector: Sequence[Sequence[acb]],
) -> tuple[list[float], list[list[complex]]]:
    values = np.asarray(
        [[_complex_midpoint(value) for value in row] for row in sector],
        dtype=np.complex128,
    )
    values = (values + values.conj().T) / 2
    eigenvalues, eigenvectors = np.linalg.eigh(values)
    return eigenvalues.tolist(), eigenvectors.tolist()


def _frobenius_upper(matrix: Sequence[Sequence[acb]]) -> arb:
    total = arb(0)
    for row in matrix:
        for value in row:
            bound = value.abs_upper()
            total += bound * bound
    return total.sqrt()


def _off_diagonal_upper(matrix: Sequence[Sequence[acb]]) -> arb:
    total = arb(0)
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            if row_index != column_index:
                bound = value.abs_upper()
                total += bound * bound
    return total.sqrt()


def _minimum_shifted_margins(eigenvalues: Sequence[float], threshold: float) -> dict[str, float | None]:
    positive = [value - threshold for value in eigenvalues if value > threshold]
    negative = [threshold - value for value in eigenvalues if value < threshold]
    return {
        "minimum_positive_shifted_midpoint_margin": min(positive) if positive else None,
        "minimum_negative_shifted_midpoint_margin": min(negative) if negative else None,
    }


def _exact_threshold(settings: dict[str, Any]) -> arb:
    text = settings["candidate_threshold_exact_dyadic"]
    numerator_text, denominator_text = text.split("/2^")
    return exact_arb_from_fraction(
        Fraction(int(numerator_text), 2 ** int(denominator_text))
    )


def _critical_domain_bounds(
    path: TaylorTransmitterPath,
    path_domain: dict[str, Any],
    *,
    order: int,
) -> dict[str, Any]:
    """Re-evaluate certified leaves and retain the critical rigorous bounds.

    The V2 domain routine returns the proof checks but intentionally keeps only
    two scalar lower bounds.  V3 persists the complete denominator/VA summary
    before spectral work so later Job termination cannot erase it.
    """

    orbit_lower: list[arb] = []
    raw_gauge_lower: list[arb] = []
    physical_energy_lower: list[arb] = []
    physical_scale_lower: list[arb] = []
    variance_lower: list[arb] = []
    variance_lower_margin: list[arb] = []
    variance_upper_margin: list[arb] = []
    finite_amplitudes = True
    for leaf in path_domain.get("certified_leaves", []):
        left = Fraction(str(leaf["left"]))
        right = Fraction(str(leaf["right"]))
        enclosed = path.cell_enclosures(left, right, order=order)
        masses = enclosed["orbit_masses"]
        orbit_lower.append(min((value.lower() for value in masses), key=float))
        raw_gauge_lower.append(enclosed["raw_mean_energy"].lower())
        # This is the same exact gauge identity used by certify_path_domain:
        # sum q_k |z_k|^2 >= K min_k q_k because mean_k |z_k|^2 = 1.
        physical_energy_lower.append(
            (len(masses) * orbit_lower[-1]).lower()
        )
        physical_scale_lower.append(enclosed["physical_scale"].lower())
        variance = enclosed["variance"]
        variance_lower.append(variance.lower())
        variance_lower_margin.append((variance.lower() - path.v_min.upper()).lower())
        variance_upper_margin.append((path.v_max.lower() - variance.upper()).lower())
        finite_amplitudes = finite_amplitudes and all(
            value.is_finite() for value in enclosed["physical_prototypes"]
        )

    def minimum_text(values: Sequence[arb]) -> str | None:
        if not values:
            return None
        return min(values, key=float).str(24, radius=False)

    return {
        "minimum_orbit_mass_lower": minimum_text(orbit_lower),
        "minimum_variance_lower": minimum_text(variance_lower),
        "minimum_variance_above_v_min_margin_lower": minimum_text(
            variance_lower_margin
        ),
        "minimum_v_max_above_variance_margin_lower": minimum_text(
            variance_upper_margin
        ),
        "minimum_raw_gs_gauge_energy_lower": minimum_text(raw_gauge_lower),
        "minimum_physical_normalization_energy_lower": minimum_text(
            physical_energy_lower
        ),
        "minimum_physical_scale_lower": minimum_text(physical_scale_lower),
        "all_coherent_state_amplitudes_finite": finite_amplitudes,
        "gs_gauge_identity": "mean_k |z_k|^2 = 1",
        "leaf_count": len(path_domain.get("certified_leaves", [])),
    }


def evaluate_node(
    taylor_path: TaylorTransmitterPath,
    direct_path: BallTransmitterPath,
    left: Fraction,
    right: Fraction,
    settings: dict[str, Any],
    *,
    elimination_callback: Any | None = None,
) -> dict[str, Any]:
    """Evaluate four exact C4 sectors without widening before congruence."""

    started = time.perf_counter()
    midpoint = (left + right) / 2
    threshold_float = float.fromhex(settings["candidate_threshold_float64_hex"])
    threshold_exact = _exact_threshold(settings)
    order = int(settings["taylor"]["order"])
    near_size = int(settings["eigencluster"]["true_near_size_per_sector"])
    block_sizes = settings["far_elimination"]["block_size_schedule"]
    precision_attempts: list[dict[str, Any]] = []

    for bits in settings["precision_bits"]:
        ctx.prec = int(bits)
        models = build_c4_sector_taylor_models(
            taylor_path, left, right, order=order,
        )
        midpoint_sectors = direct_path.sectors(exact_arb_from_fraction(midpoint))
        # Paired V2-style enclosure is diagnostic only and is computed on the
        # exact same node for a subset-independent tightening ratio.
        entrywise_sectors = taylor_path.c4_sector_enclosures(left, right, order=order)
        sector_rows: list[dict[str, Any]] = []
        for sector_index, (model, midpoint_sector, entrywise_sector) in enumerate(zip(
            models, midpoint_sectors, entrywise_sectors,
        )):
            eigenvalues, rounded_q = _midpoint_eigensystem(midpoint_sector)
            basis = certify_rounded_basis(rounded_q, precision_bits=int(bits))
            if basis["status"] != "CERTIFIED_NONSINGULAR":
                sector_rows.append({
                    "sector": sector_index,
                    "status": "UNCERTIFIED_BASIS",
                    "basis": basis,
                    "failure_reason": "ROUNDED_BASIS_NONSINGULARITY_UNCERTIFIED",
                })
                break
            transformed = shifted_rounded_congruence_taylor_model(
                model, rounded_q, threshold_exact,
            )
            enclosure = evaluate_taylor_model_enclosure(transformed)
            reduction = sequential_signed_schur_reduction(
                enclosure,
                midpoint_eigenvalues=eigenvalues,
                threshold=threshold_float,
                near_size=near_size,
                block_sizes=block_sizes,
                precision_bits=int(bits),
                sign_groups=tuple(settings["far_elimination"]["sign_groups"]),
                maximum_residual_dimension=None,
                elimination_callback=(
                    (lambda step, sector_index=sector_index, bits=int(bits):
                     elimination_callback(sector_index, bits, step))
                    if elimination_callback is not None else None
                ),
            )
            coefficient_norms = [
                _frobenius_upper(matrix).str(24, radius=False)
                for matrix in transformed.coefficients
            ]
            transformed_midpoint = transformed.coefficients[0]
            coefficient_radius = frobenius_perturbation_upper(
                enclosure, transformed_midpoint,
            )
            entrywise_shifted = shift_hermitian(
                entrywise_sector, threshold_exact,
            )
            entrywise_transformed = exact_congruence_enclosure(
                entrywise_shifted, rounded_q,
            )
            entrywise_radius = frobenius_perturbation_upper(
                entrywise_transformed, transformed_midpoint,
            )
            ratio = (
                float(coefficient_radius) / float(entrywise_radius)
                if float(entrywise_radius) > 0 else 0.0
            )
            successful_steps = [
                step for step in reduction["steps"] if step.get("accepted")
            ]
            unresolved_far = (
                len(reduction["unresolved_far_positive_indices"])
                + len(reduction["unresolved_far_negative_indices"])
            )
            sector_rows.append({
                "sector": sector_index,
                "status": reduction["status"],
                "basis": basis,
                "midpoint_shifted_spectrum_near_zero": sorted(
                    (value - threshold_float for value in eigenvalues), key=abs,
                )[:16],
                "true_near_indices": reduction["partition"]["near_indices"],
                "true_near_size": len(reduction["partition"]["near_indices"]),
                "positive_far_size": len(reduction["partition"]["far_positive_indices"]),
                "negative_far_size": len(reduction["partition"]["far_negative_indices"]),
                "unresolved_positive_far_size": len(
                    reduction["unresolved_far_positive_indices"]
                ),
                "unresolved_negative_far_size": len(
                    reduction["unresolved_far_negative_indices"]
                ),
                "unresolved_far_size": unresolved_far,
                "final_schur_reduced_dimension": len(reduction["residual_original_labels"]),
                "certified_positive_count": reduction.get("n_positive"),
                "certified_negative_count": reduction.get("n_negative"),
                "successful_schur_elimination_count": len(successful_steps),
                "successful_schur_eliminated_dimension": sum(
                    len(step["original_labels"]) for step in successful_steps
                ),
                "taylor_coefficient_frobenius_norms_upper": coefficient_norms,
                "rigorous_cubic_remainder_frobenius_norm_upper": (
                    _frobenius_upper(transformed.remainder_coefficient).str(
                        24, radius=False,
                    )
                ),
                "transformed_off_diagonal_coupling_norm_upper": (
                    _off_diagonal_upper(enclosure).str(24, radius=False)
                ),
                "coefficient_congruence_radius_upper": coefficient_radius.str(
                    24, radius=False,
                ),
                "entrywise_then_congruence_radius_upper": entrywise_radius.str(
                    24, radius=False,
                ),
                "paired_radius_ratio": ratio,
                "signed_midpoint_margins": _minimum_shifted_margins(
                    eigenvalues, threshold_float,
                ),
                "sequential_reduction": reduction,
                "failure_reason": reduction.get("failure_reason"),
            })
            if reduction["status"] != "CERTIFIED_SEQUENTIAL_INERTIA":
                break
        certified = len(sector_rows) == 4 and all(
            row["status"] == "CERTIFIED_SEQUENTIAL_INERTIA" for row in sector_rows
        )
        support = sum(
            int(row["certified_positive_count"])
            for row in sector_rows if row.get("certified_positive_count") is not None
        )
        attempt = {
            "precision_bits": int(bits),
            "status": "CERTIFIED_FIXED_INERTIA" if certified else "UNCERTIFIED",
            "certified_support_count": support if certified else None,
            "sector_rows": sector_rows,
        }
        precision_attempts.append(attempt)
        if certified:
            break

    last = precision_attempts[-1]
    return {
        "left": _fraction_text(left),
        "right": _fraction_text(right),
        "midpoint": _fraction_text(midpoint),
        "taylor_order": order,
        **last,
        "precision_attempts": precision_attempts,
        "runtime_seconds": time.perf_counter() - started,
    }


def _endpoint_ranks(settings: dict[str, Any], state_label: str, family: str) -> tuple[int, int]:
    artifact = json.loads(
        (ROOT / settings["endpoint_gate_artifact"]).read_text(encoding="utf-8")
    )
    rows = {
        (row["state_label"], row["family"], row["endpoint"]): int(row["n_positive"])
        for row in artifact["endpoint_rows"]
    }
    return rows[(state_label, family, "start")], rows[(state_label, family, "end")]


def run_segment(
    config_path: Path,
    bundle_path: Path,
    state_label: str,
    family: str,
    *,
    attempt_id: str,
    journal_directory: Path,
    journal_identity_path: Path,
    path_domain_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    settings = load_yaml(config_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    states = {row["label"]: row for row in bundle["states"]}
    segments = {row["family"]: row for row in bundle["segments"]}
    if state_label not in states or family not in segments:
        raise ValueError("Requested state/family is absent from the frozen bundle.")
    segment_id = f"{state_label}/{family}"
    identity = json.loads(journal_identity_path.read_text(encoding="utf-8"))
    direct = BallTransmitterPath(
        bundle["start_parameters"], segments[family]["end_parameters"],
        states[state_label], bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
    )
    taylor = TaylorTransmitterPath(
        bundle["start_parameters"], segments[family]["end_parameters"],
        states[state_label], bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
    )
    start_rank, end_rank = _endpoint_ranks(settings, state_label, family)
    run_started = time.perf_counter()
    nodes: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    with DurableJournal(
        journal_directory, attempt_id=attempt_id, segment_id=segment_id,
        identity=identity,
    ) as journal:
        journal.append("RUN_STARTED", {
            "state_label": state_label, "family": family,
            "started_perf_counter_ns": time.perf_counter_ns(),
        })
        path_started = time.perf_counter()
        path_domain = taylor.certify_path_domain(
            order=int(settings["taylor"]["order"]),
            maximum_depth=int(settings["path_domain"]["maximum_subdivision_depth"]),
        )
        critical_bounds = _critical_domain_bounds(
            taylor,
            path_domain,
            order=int(settings["taylor"]["order"]),
        ) if path_domain["status"] == "PATH_DOMAIN_CERTIFIED" else {}
        path_artifact = {
            "schema_version": "taylor-eigencluster-path-domain-v3",
            "status": path_domain["status"],
            "attempt_id": attempt_id,
            "segment_id": segment_id,
            "state_label": state_label,
            "family": family,
            "complete_interval": ["0/1", "1/1"],
            "continuity_certified": path_domain["status"] == "PATH_DOMAIN_CERTIFIED",
            "relu_transition_points": path_domain["relu_transition_points"],
            "certified_leaf_count": path_domain["certified_leaf_count"],
            "unresolved_leaf_count": path_domain["unresolved_leaf_count"],
            "certified_leaves": path_domain["certified_leaves"],
            "unresolved_leaves": path_domain["unresolved_leaves"],
            "critical_domain_bounds": critical_bounds,
            "path_domain": path_domain,
            "runtime_seconds": time.perf_counter() - path_started,
            "provenance": identity,
        }
        _durable_atomic_json(path_domain_path, path_artifact)
        path_artifact["artifact_sha256"] = __import__("hashlib").sha256(
            path_domain_path.read_bytes()
        ).hexdigest()
        journal.append("PATH_DOMAIN_COMMITTED", {"path_domain": path_artifact})

        if path_domain["status"] != "PATH_DOMAIN_CERTIFIED":
            artifact = {
                "schema_version": "taylor-eigencluster-segment-v3",
                "status": "UNCERTIFIED",
                "reason": "PATH_DOMAIN_UNCERTIFIED",
                "state_label": state_label, "family": family,
                "path_domain": path_artifact, "start_rank": start_rank,
                "end_rank": end_rank, "nodes": [], "unresolved_leaves": [],
            }
            journal.append("SEGMENT_COMPLETED", {"segment": artifact})
            _durable_atomic_json(output_path, artifact)
            return artifact

        if start_rank != end_rank:
            artifact = {
                "schema_version": "taylor-eigencluster-segment-v3",
                "status": "PROVEN_CROSSING",
                "reason": "CERTIFIED_ENDPOINT_INERTIA_CHANGE_ON_CERTIFIED_CONTINUOUS_PATH",
                "crossing_argument": {
                    "kind": "INERTIA_CHANGE_PLUS_CONTINUITY",
                    "zero_inclusion_alone_used": False,
                },
                "state_label": state_label, "family": family,
                "path_domain": path_artifact, "start_rank": start_rank,
                "end_rank": end_rank, "nodes": [], "unresolved_leaves": [],
            }
            journal.append("SEGMENT_COMPLETED", {"segment": artifact})
            _durable_atomic_json(output_path, artifact)
            return artifact

        pending = [(left, right, 0, None) for left, right in reversed(taylor.smooth_cells())]
        journal.append("WORK_QUEUE_INITIALIZED", {"pending": [
            [_fraction_text(a), _fraction_text(b), depth, parent]
            for a, b, depth, parent in pending
        ]})
        maximum_nodes = int(settings["subdivision"]["maximum_nodes_per_segment"])
        maximum_depth = int(settings["subdivision"]["maximum_depth"])
        next_node = 0
        while pending and next_node < maximum_nodes:
            left, right, depth, parent_id = pending.pop()
            node_id = f"node-{next_node:06d}"
            next_node += 1
            journal.append("NODE_STARTED", {
                "node_id": node_id, "parent_node_id": parent_id,
                "interval": [_fraction_text(left), _fraction_text(right)],
                "depth": depth, "taylor_order": int(settings["taylor"]["order"]),
                "path_domain_status": path_domain["status"],
                "path_domain_artifact_sha256": path_artifact["artifact_sha256"],
                "cumulative_runtime_seconds": time.perf_counter() - run_started,
            })
            def commit_elimination(
                sector_index: int, precision_bits: int, step: dict[str, Any]
            ) -> None:
                journal.append("SCHUR_ELIMINATION_COMMITTED", {
                    "node_id": node_id,
                    "sector": sector_index,
                    "precision_bits": precision_bits,
                    **step,
                    "cumulative_runtime_seconds": time.perf_counter() - run_started,
                })

            row = evaluate_node(
                taylor, direct, left, right, settings,
                elimination_callback=commit_elimination,
            )
            row.update({
                "node_id": node_id, "parent_node_id": parent_id, "depth": depth,
                "path_domain_status": path_domain["status"],
                "cumulative_runtime_seconds": time.perf_counter() - run_started,
            })
            nodes.append(row)
            if (row["status"] == "CERTIFIED_FIXED_INERTIA" and
                    int(row["certified_support_count"]) == start_rank):
                row["leaf_state"] = "CERTIFIED_FIXED_INERTIA"
                accepted.append(row)
                action = "ACCEPT"
            elif depth >= maximum_depth:
                row["leaf_state"] = "UNCERTIFIED"
                unresolved.append(row)
                action = "UNRESOLVED"
            else:
                middle = (left + right) / 2
                pending.append((middle, right, depth + 1, node_id))
                pending.append((left, middle, depth + 1, node_id))
                action = "SPLIT"
            journal.append("NODE_COMMITTED", {
                "node_id": node_id, "node": row, "action": action,
                "pending": [[_fraction_text(a), _fraction_text(b), d, parent]
                            for a, b, d, parent in pending],
            })

        if pending:
            unresolved.extend({
                "left": _fraction_text(left), "right": _fraction_text(right),
                "depth": depth, "parent_node_id": parent,
                "leaf_state": "UNCERTIFIED_RESOURCE_LIMIT",
            } for left, right, depth, parent in pending)
        status = "CERTIFIED_FIXED_INERTIA" if not unresolved else "UNCERTIFIED"
        artifact = {
            "schema_version": "taylor-eigencluster-segment-v3",
            "status": status, "reason": None if not unresolved else "INCOMPLETE_COVER",
            "state_label": state_label, "family": family,
            "path_domain": path_artifact, "start_rank": start_rank,
            "end_rank": end_rank, "accepted_leaf_count": len(accepted),
            "unresolved_leaf_count": len(unresolved), "nodes": nodes,
            "unresolved_leaves": unresolved, "exact_gap_free_cover_required": True,
            "runtime_seconds": time.perf_counter() - run_started,
        }
        journal.append("SEGMENT_COMPLETED", {"segment": artifact})
        _durable_atomic_json(output_path, artifact)
        return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--journal-directory", type=Path, required=True)
    parser.add_argument("--journal-identity", type=Path, required=True)
    parser.add_argument("--path-domain-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    row = run_segment(
        args.config.resolve(), args.bundle.resolve(), args.state, args.family,
        attempt_id=args.attempt_id,
        journal_directory=args.journal_directory.resolve(),
        journal_identity_path=args.journal_identity.resolve(),
        path_domain_path=args.path_domain_output.resolve(),
        output_path=args.output.resolve(),
    )
    print(json.dumps({
        "status": row["status"], "state": args.state, "family": args.family,
    }))


if __name__ == "__main__":
    main()
