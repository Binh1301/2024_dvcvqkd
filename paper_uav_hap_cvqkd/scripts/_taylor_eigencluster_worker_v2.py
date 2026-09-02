"""One externally-watched V2 whole-segment certification worker."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
import os
from pathlib import Path
import time
from typing import Any

import numpy as np
from flint import acb, ctx

from _common import ROOT, load_yaml
from src.validation.rigorous_flint_support import (
    BallTransmitterPath,
    exact_arb_from_fraction,
)
from src.validation.rigorous_shifted_inertia_segment import frobenius_perturbation_upper
from src.validation.rigorous_taylor_eigencluster_v2 import certify_fixed_basis_eigencluster
from src.validation.validated_scalar_taylor_v2 import TaylorTransmitterPath


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _complex_midpoint(value: acb) -> complex:
    return complex(float(value.real.mid()), float(value.imag.mid()))


def _midpoint_eigensystem(sector: list[list[acb]]) -> tuple[list[float], list[list[complex]]]:
    values = np.asarray(
        [[_complex_midpoint(value) for value in row] for row in sector],
        dtype=np.complex128,
    )
    values = (values + values.conj().T) / 2
    eigenvalues, eigenvectors = np.linalg.eigh(values)
    return eigenvalues.tolist(), eigenvectors.tolist()


def _compact_sector(result: dict[str, Any], rho: str, sector: int) -> dict[str, Any]:
    attempts = result.get("attempts", [])
    accepted = attempts[-1] if attempts else None
    return {
        "sector": sector,
        "status": result["status"],
        "certified_support_count": result.get("certified_support_count"),
        "taylor_frobenius_radius_upper": rho,
        "basis": result.get("basis"),
        "cluster_schedule": result.get("cluster_schedule"),
        "accepted_cluster_size": result.get("accepted_cluster_size"),
        "attempt_count": len(attempts),
        "last_partition": accepted.get("partition") if accepted else None,
        "last_reduction": accepted.get("reduction") if accepted else None,
        "last_cluster_inertia": accepted.get("cluster_inertia") if accepted else None,
        "failure_reason": result.get("failure_reason"),
        "runtime_seconds": result.get("runtime_seconds"),
    }


def evaluate_node(
    taylor_path: TaylorTransmitterPath,
    direct_path: BallTransmitterPath,
    left: Fraction,
    right: Fraction,
    settings: dict[str, Any],
) -> dict[str, Any]:
    started = time.perf_counter()
    midpoint = (left + right) / 2
    threshold = float.fromhex(settings["candidate_threshold_float64_hex"])
    cluster = settings["eigencluster"]
    taylor = settings["taylor"]
    attempts = []
    for bits in settings["precision_bits"]:
        ctx.prec = int(bits)
        interval_sectors = taylor_path.c4_sector_enclosures(
            left, right, order=int(taylor["order"])
        )
        midpoint_sectors = direct_path.sectors(exact_arb_from_fraction(midpoint))
        sector_rows = []
        for sector_index, (interval_sector, midpoint_sector) in enumerate(
            zip(interval_sectors, midpoint_sectors)
        ):
            eigenvalues, rounded_q = _midpoint_eigensystem(midpoint_sector)
            rho = frobenius_perturbation_upper(interval_sector, midpoint_sector)
            result = certify_fixed_basis_eigencluster(
                interval_sector,
                rounded_q=rounded_q,
                midpoint_eigenvalues=eigenvalues,
                threshold=threshold,
                precision_bits=int(bits),
                seed_size=int(cluster["seed_size"]),
                expansion_step=int(cluster["expansion_step"]),
                maximum_cluster_size=int(cluster["maximum_size_per_sector"]),
                maximum_seconds=float(settings["resources"]["cooperative_maximum_seconds_per_node"]),
            )
            sector_rows.append(_compact_sector(
                result, rho.str(24, radius=False), sector_index
            ))
            if result["status"] != "CERTIFIED_FIXED_BASIS_INERTIA":
                break
        fixed = len(sector_rows) == 4 and all(
            row["status"] == "CERTIFIED_FIXED_BASIS_INERTIA" for row in sector_rows
        )
        support = sum(int(row["certified_support_count"]) for row in sector_rows
                      if row["certified_support_count"] is not None)
        attempt = {
            "precision_bits": int(bits),
            "status": "CERTIFIED_FIXED_INERTIA" if fixed else "UNCERTIFIED",
            "certified_support_count": support if fixed else None,
            "sector_rows": sector_rows,
        }
        attempts.append(attempt)
        if fixed:
            break
    last = attempts[-1]
    return {
        "left": _fraction_text(left),
        "right": _fraction_text(right),
        "midpoint": _fraction_text(midpoint),
        **last,
        "attempts": attempts,
        "runtime_seconds": time.perf_counter() - started,
    }


def run_segment(
    config_path: Path,
    bundle_path: Path,
    state_label: str,
    family: str,
    checkpoint_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    settings = load_yaml(config_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    states = {row["label"]: row for row in bundle["states"]}
    segments = {row["family"]: row for row in bundle["segments"]}
    if state_label not in states or family not in segments:
        raise ValueError("Requested state/family is absent from the frozen bundle.")
    state, segment = states[state_label], segments[family]
    direct = BallTransmitterPath(
        bundle["start_parameters"], segment["end_parameters"], state,
        bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
    )
    taylor = TaylorTransmitterPath(
        bundle["start_parameters"], segment["end_parameters"], state,
        bundle["v_min_float64_hex"], bundle["v_max_float64_hex"],
    )
    endpoint_artifact = json.loads(
        (ROOT / settings["endpoint_gate_artifact"]).read_text(encoding="utf-8")
    )
    endpoint_map = {
        (row["state_label"], row["family"], row["endpoint"]): int(row["n_positive"])
        for row in endpoint_artifact["endpoint_rows"]
    }
    start_rank = endpoint_map[(state_label, family, "start")]
    end_rank = endpoint_map[(state_label, family, "end")]

    path_domain = taylor.certify_path_domain(
        order=int(settings["taylor"]["order"]),
        maximum_depth=int(settings["path_domain"]["maximum_subdivision_depth"]),
    )
    if path_domain["status"] != "PATH_DOMAIN_CERTIFIED":
        artifact = {
            "status": "UNCERTIFIED_PATH_DOMAIN", "state_label": state_label,
            "family": family, "path_domain": path_domain, "nodes": [],
            "start_rank": start_rank, "end_rank": end_rank,
        }
        _atomic_json(output_path, artifact)
        return artifact
    if start_rank != end_rank:
        artifact = {
            "status": "PROVEN_CROSSING_BY_INERTIA_CHANGE_AND_CONTINUITY",
            "state_label": state_label, "family": family,
            "path_domain": path_domain, "nodes": [],
            "start_rank": start_rank, "end_rank": end_rank,
        }
        _atomic_json(output_path, artifact)
        return artifact

    subdivision = settings["subdivision"]
    pending = [(left, right, 0) for left, right in reversed(taylor.smooth_cells())]
    nodes: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    max_nodes = int(subdivision["maximum_nodes_per_segment"])
    max_depth = int(subdivision["maximum_depth"])
    while pending and len(nodes) < max_nodes:
        left, right, depth = pending.pop()
        row = evaluate_node(taylor, direct, left, right, settings)
        row["depth"] = depth
        nodes.append(row)
        if row["status"] == "CERTIFIED_FIXED_INERTIA" and int(
            row["certified_support_count"]
        ) == start_rank:
            row["leaf_state"] = "CERTIFIED_FIXED_INERTIA"
            accepted.append(row)
        elif depth >= max_depth:
            row["leaf_state"] = "UNCERTIFIED"
            unresolved.append(row)
        else:
            middle = (left + right) / 2
            pending.append((middle, right, depth + 1))
            pending.append((left, middle, depth + 1))
        _atomic_json(checkpoint_path, {
            "schema_version": "taylor-eigencluster-checkpoint-v2",
            "state_label": state_label, "family": family,
            "last_completed_node": row,
            "completed_node_count": len(nodes),
            "pending": [[_fraction_text(a), _fraction_text(b), d] for a, b, d in pending],
        })
    if pending:
        unresolved.extend({
            "left": _fraction_text(left), "right": _fraction_text(right),
            "depth": depth, "leaf_state": "UNCERTIFIED_RESOURCE_LIMIT",
        } for left, right, depth in pending)
    status = "CERTIFIED_FIXED_INERTIA" if not unresolved else "UNCERTIFIED"
    artifact = {
        "status": status, "state_label": state_label, "family": family,
        "path_domain": path_domain, "start_rank": start_rank, "end_rank": end_rank,
        "accepted_leaf_count": len(accepted),
        "unresolved_leaf_count": len(unresolved),
        "nodes": nodes, "unresolved_leaves": unresolved,
        "exact_gap_free_cover_required": True,
    }
    _atomic_json(output_path, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    row = run_segment(
        args.config.resolve(), args.bundle.resolve(), args.state, args.family,
        args.checkpoint.resolve(), args.output.resolve(),
    )
    print(json.dumps({"status": row["status"], "state": args.state, "family": args.family}))


if __name__ == "__main__":
    main()
