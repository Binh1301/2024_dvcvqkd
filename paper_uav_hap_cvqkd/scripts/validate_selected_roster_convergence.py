"""Produce exact post-selection MI/Fock/Holevo-threshold convergence evidence.

This is a validation-only post-training tool.  It performs no optimization and
cannot construct a held-out test realization.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from _common import (
    holevo_numerical_kwargs,
    load_yaml,
    require_holevo_pseudoinverse_approval,
)
from _numerical_validation import full_validation_states, require
from src.utils.random import derive_seed
from src.validation.convergence import (
    ConvergenceTolerance,
    fock_convergence_trace,
    holevo_threshold_sensitivity_trace,
    mi_convergence_trace,
)
from src.validation.physical_domain import require_preconvergence_domain_ready
from src.validation.publication_manifest import (
    canonical_json_sha256,
)
from src.validation.selected_roster import (
    expected_evidence_settings,
    reconstruct_selected_roster,
    selection_roster_sha256,
)


def _resolve(manifest_path: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (manifest_path.parent / path).resolve()


def _entry(binding: dict[str, str], trace: dict[str, object]) -> dict[str, object]:
    return {**binding, "trace": trace}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--selection-manifest", type=Path)
    selection.add_argument("--selection-roster", type=Path)
    parser.add_argument("--mi-output", type=Path, required=True)
    parser.add_argument("--fock-output", type=Path, required=True)
    parser.add_argument("--holevo-threshold-output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = (args.selection_manifest or args.selection_roster).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config_path = _resolve(manifest_path, manifest["artifact_paths"]["resolved_config"])
    config = load_yaml(config_path)
    require(config, [
        "cvqkd.fock_cutoff",
        "numerical_validation.mi.sample_counts",
        "numerical_validation.mi.absolute_tolerance_bits",
        "numerical_validation.mi.relative_tolerance",
        "numerical_validation.mi.seeds",
        "numerical_validation.fock.cutoffs",
        "numerical_validation.fock.absolute_tolerance",
        "numerical_validation.fock.relative_tolerance",
        "numerical_validation.fock.density_trace_tolerance",
        "numerical_validation.holevo_threshold_sensitivity.density_eigenvalue_pseudoinverse_tolerances",
        "numerical_validation.holevo_threshold_sensitivity.absolute_tolerance",
        "numerical_validation.holevo_threshold_sensitivity.relative_tolerance",
    ])
    require_preconvergence_domain_ready(config)
    require_holevo_pseudoinverse_approval(config)
    states, t, epsilon = full_validation_states(config)
    config, baseline_hash, roster = reconstruct_selected_roster(
        manifest_path, manifest, t, epsilon, states.realization_sha256
    )
    config_hash = canonical_json_sha256(config)
    roster_hash = selection_roster_sha256(manifest)
    common = {
        "schema_version": "exact-selected-convergence-evidence-v1",
        "test_set_used": False,
        "coverage_scope": "exact_selected_roster_on_preregistered_validation_realization",
        "selection_roster_sha256": roster_hash,
        "resolved_config_sha256": config_hash,
        "baseline_selection_sha256": baseline_hash,
        "validation_state_realization_sha256": states.realization_sha256,
        "precision": "torch.float64 / torch.complex128 on CPU",
    }

    mi_settings = expected_evidence_settings(config, "mi")
    mi_tolerance = ConvergenceTolerance(
        mi_settings["absolute_tolerance_bits"], mi_settings["relative_tolerance"]
    )
    base_seeds = tuple(mi_settings["replication_base_seeds"])
    if len(base_seeds) < 2 or len(set(base_seeds)) != len(base_seeds):
        raise ValueError("MI exact-roster evidence needs distinct replication seeds.")
    replication_seeds = tuple(
        derive_seed(seed, "mi_convergence_common_replication") for seed in base_seeds
    )
    mi_entries = []
    mi_selected: list[int | None] = []
    mi_all_stable = True
    for item in roster:
        replications = [
            mi_convergence_trace(
                item.ensemble, t, epsilon,
                sample_counts=mi_settings["sample_counts"], seed=seed,
                tolerance=mi_tolerance,
            )
            for seed in replication_seeds
        ]
        mi_selected.extend(trace["selected_sample_count"] for trace in replications)
        references = np.asarray(
            [trace["rows"][-1]["mi_bits"] for trace in replications], dtype=np.float64
        )
        reference_mean = references.mean(axis=0)
        maximum_deviation = np.max(np.abs(references - reference_mean), axis=0)
        allowed = mi_tolerance.absolute + mi_tolerance.relative * np.abs(reference_mean)
        stable = bool(np.all(maximum_deviation <= allowed))
        mi_all_stable = mi_all_stable and stable
        trace = {
            "replications": replications,
            "all_replications_converged": all(row["converged"] for row in replications),
            "reference_replication_check": {
                "reference_mean_bits": reference_mean.tolist(),
                "maximum_replication_deviation_bits": maximum_deviation.tolist(),
                "maximum_allowed_deviation_bits": allowed.tolist(),
                "passes": stable,
            },
        }
        mi_entries.append(_entry(item.binding(), trace))
    mi_common = (
        None if any(value is None for value in mi_selected) or not mi_all_stable
        else max(int(value) for value in mi_selected)
    )
    mi_payload = {
        **common,
        "evidence_type": "mi",
        "status": "exact selected-roster validation evidence; not a publication result",
        "settings": mi_settings,
        "all_entries_pass": mi_common is not None,
        "minimum_common_sample_count": mi_common,
        "entries": mi_entries,
    }

    fock_settings = expected_evidence_settings(config, "fock")
    fock_tolerance = ConvergenceTolerance(
        fock_settings["absolute_tolerance"], fock_settings["relative_tolerance"]
    )
    if fock_settings["density_trace_tolerance"] != config["numerical_validation"][
        "fock"
    ]["density_trace_tolerance"]:
        raise ValueError("Fock and active Holevo density-trace tolerances differ.")
    holevo_kwargs = holevo_numerical_kwargs(config)
    fock_entries = []
    fock_selected = []
    for item in roster:
        trace = fock_convergence_trace(
            item.ensemble, t, epsilon,
            cutoffs=fock_settings["cutoffs"], tolerance=fock_tolerance,
            density_trace_tolerance=fock_settings["density_trace_tolerance"],
            **{key: value for key, value in holevo_kwargs.items()
               if key != "density_trace_tolerance"},
        )
        fock_selected.append(trace["selected_fock_cutoff"])
        fock_entries.append(_entry(item.binding(), trace))
    fock_common = (
        None if any(value is None for value in fock_selected)
        else max(int(value) for value in fock_selected)
    )
    fock_payload = {
        **common,
        "evidence_type": "fock",
        "status": "exact selected-roster validation evidence; not a publication result",
        "settings": fock_settings,
        "all_entries_pass": fock_common is not None,
        "minimum_common_fock_cutoff_for_listed_ensembles": fock_common,
        "entries": fock_entries,
    }

    threshold_settings = expected_evidence_settings(config, "holevo_threshold")
    threshold_tolerance = ConvergenceTolerance(
        threshold_settings["absolute_tolerance"], threshold_settings["relative_tolerance"]
    )
    threshold_entries = []
    for item in roster:
        trace = holevo_threshold_sensitivity_trace(
            item.ensemble, t, epsilon,
            fock_cutoff=threshold_settings["fock_cutoff"],
            density_eigenvalue_tolerances=threshold_settings[
                "density_eigenvalue_pseudoinverse_tolerances"
            ],
            selected_tolerance=threshold_settings[
                "density_eigenvalue_pseudoinverse_tolerance"
            ],
            tolerance=threshold_tolerance,
            symmetry_tolerance=threshold_settings["symmetry_tolerance"],
            density_trace_tolerance=threshold_settings["density_trace_tolerance"],
            physicality_tolerance=threshold_settings["physicality_tolerance"],
        )
        threshold_entries.append(_entry(item.binding(), trace))
    threshold_pass = all(
        entry["trace"]["selected_threshold_passes"] for entry in threshold_entries
    )
    threshold_payload = {
        **common,
        "evidence_type": "holevo_threshold",
        "status": "exact selected-roster validation evidence; not a publication result",
        "settings": threshold_settings,
        "all_entries_pass": threshold_pass,
        "entries": threshold_entries,
    }

    for path, payload in (
        (args.mi_output.resolve(), mi_payload),
        (args.fock_output.resolve(), fock_payload),
        (args.holevo_threshold_output.resolve(), threshold_payload),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if mi_payload["all_entries_pass"] and fock_payload[
        "all_entries_pass"
    ] and threshold_payload["all_entries_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
