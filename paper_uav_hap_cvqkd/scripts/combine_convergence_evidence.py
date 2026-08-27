"""Create the fail-closed exact-selected-roster convergence gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import load_yaml, require_holevo_pseudoinverse_approval
from _numerical_validation import full_validation_states
from src.utils.random import derive_seed
from src.validation.publication_manifest import (
    canonical_json_sha256,
    file_sha256,
)
from src.validation.physical_domain import approved_peak_photon_limit
from src.validation.selected_roster import (
    expected_evidence_settings,
    reconstruct_selected_roster,
    selection_roster_sha256,
    validate_exact_evidence,
)


def _resolve(manifest_path: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (manifest_path.parent / path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--selection-manifest", type=Path)
    selection.add_argument("--selection-roster", type=Path)
    parser.add_argument("--mi-evidence", type=Path, required=True)
    parser.add_argument("--fock-evidence", type=Path, required=True)
    parser.add_argument("--holevo-threshold-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = (args.selection_manifest or args.selection_roster).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config_path = _resolve(manifest_path, manifest["artifact_paths"]["resolved_config"])
    preliminary_config = load_yaml(config_path)
    require_holevo_pseudoinverse_approval(preliminary_config)
    states, t, epsilon = full_validation_states(preliminary_config)
    config, baseline_hash, roster = reconstruct_selected_roster(
        manifest_path, manifest, t, epsilon, states.realization_sha256
    )
    n_peak = approved_peak_photon_limit(config)
    roster_hash = selection_roster_sha256(manifest)
    mi = json.loads(args.mi_evidence.read_text(encoding="utf-8"))
    fock = json.loads(args.fock_evidence.read_text(encoding="utf-8"))
    threshold = json.loads(args.holevo_threshold_evidence.read_text(encoding="utf-8"))
    mi_entries = validate_exact_evidence(
        mi, evidence_type="mi", config=config,
        baseline_selection_sha256=baseline_hash,
        validation_state_realization_sha256=states.realization_sha256,
        selection_roster_hash=roster_hash, roster=roster,
    )
    fock_entries = validate_exact_evidence(
        fock, evidence_type="fock", config=config,
        baseline_selection_sha256=baseline_hash,
        validation_state_realization_sha256=states.realization_sha256,
        selection_roster_hash=roster_hash, roster=roster,
    )
    threshold_entries = validate_exact_evidence(
        threshold, evidence_type="holevo_threshold", config=config,
        baseline_selection_sha256=baseline_hash,
        validation_state_realization_sha256=states.realization_sha256,
        selection_roster_hash=roster_hash, roster=roster,
    )

    mi_selected: list[int] = []
    all_mi = mi.get("all_entries_pass") is True
    mi_settings = expected_evidence_settings(config, "mi")
    expected_replication_seeds = [
        derive_seed(seed, "mi_convergence_common_replication")
        for seed in mi_settings["replication_base_seeds"]
    ]
    for entry in mi_entries.values():
        trace = entry["trace"]
        replications = trace.get("replications")
        stable = trace.get("reference_replication_check", {}).get("passes") is True
        if not isinstance(replications, list) or not replications or not stable or trace.get(
            "all_replications_converged"
        ) is not True:
            all_mi = False
            continue
        if len(replications) != len(expected_replication_seeds):
            raise ValueError("MI trace replication roster differs from configured seeds.")
        for replication, expected_seed in zip(replications, expected_replication_seeds):
            if (
                replication.get("seed") != expected_seed
                or replication.get("reference_sample_count") != mi_settings["sample_counts"][-1]
                or replication.get("absolute_tolerance_bits")
                != mi_settings["absolute_tolerance_bits"]
                or replication.get("relative_tolerance") != mi_settings["relative_tolerance"]
                or [row.get("sample_count") for row in replication.get("rows", [])]
                != mi_settings["sample_counts"]
            ):
                raise ValueError("MI trace settings differ from the resolved configuration.")
            selected = replication.get("selected_sample_count")
            if replication.get("converged") is not True or not isinstance(selected, int):
                all_mi = False
            else:
                mi_selected.append(selected)
    selected_mi = max(mi_selected) if all_mi and mi_selected else None
    if selected_mi != mi.get("minimum_common_sample_count"):
        raise ValueError("MI common sample count is not derived from every exact roster trace.")

    fock_selected: list[int] = []
    all_fock = fock.get("all_entries_pass") is True
    fock_settings = expected_evidence_settings(config, "fock")
    for entry in fock_entries.values():
        trace = entry["trace"]
        for key in (
            "absolute_tolerance", "relative_tolerance", "density_trace_tolerance",
            "symmetry_tolerance", "density_eigenvalue_pseudoinverse_tolerance",
            "physicality_tolerance",
        ):
            if trace.get(key) != fock_settings[key]:
                raise ValueError("Fock trace tolerances differ from resolved configuration.")
        if trace.get("reference_fock_cutoff") != fock_settings["cutoffs"][-1] or [
            row.get("fock_cutoff") for row in trace.get("rows", [])
        ] != fock_settings["cutoffs"]:
            raise ValueError("Fock trace cutoff grid differs from resolved configuration.")
        selected = trace.get("selected_fock_cutoff")
        if trace.get("converged") is not True or not isinstance(selected, int):
            all_fock = False
        else:
            fock_selected.append(selected)
    selected_fock = max(fock_selected) if all_fock and fock_selected else None
    if selected_fock != fock.get("minimum_common_fock_cutoff_for_listed_ensembles"):
        raise ValueError("Fock cutoff is not derived from every exact roster trace.")

    threshold_settings = expected_evidence_settings(config, "holevo_threshold")
    all_threshold = threshold.get("all_entries_pass") is True
    for entry in threshold_entries.values():
        trace = entry["trace"]
        if (
            trace.get("selected_threshold_passes") is not True
            or trace.get("absolute_tolerance") != threshold_settings["absolute_tolerance"]
            or trace.get("relative_tolerance") != threshold_settings["relative_tolerance"]
            or trace.get("selected_density_eigenvalue_pseudoinverse_tolerance")
            != threshold_settings["density_eigenvalue_pseudoinverse_tolerance"]
            or trace.get("reference_density_eigenvalue_pseudoinverse_tolerance")
            != threshold_settings["density_eigenvalue_pseudoinverse_tolerances"][0]
            or [row.get("density_eigenvalue_pseudoinverse_tolerance")
                for row in trace.get("rows", [])]
            != threshold_settings["density_eigenvalue_pseudoinverse_tolerances"]
        ):
            all_threshold = False
    if selected_mi is None or selected_fock is None or not all_threshold:
        raise ValueError("Exact selected-roster convergence evidence is incomplete or failed.")
    if int(config["cvqkd"]["fock_cutoff"]) != selected_fock:
        raise ValueError("Resolved Fock cutoff differs from exact-roster convergence selection.")
    if any(int(config["training"][key]) < selected_mi for key in (
        "validation_awgn_samples_per_symbol", "test_awgn_samples_per_symbol"
    )):
        raise ValueError("Resolved validation/test MI counts are below convergence selection.")

    checkpoint_hashes = [
        entry.source_artifact_sha256 for entry in roster if entry.kind == "checkpoint"
    ]
    payload = {
        "schema_version": "combined-convergence-evidence-v2",
        "status": "exact-selected-roster-convergence-gates-passed",
        "test_set_used": False,
        "validation_state_realization_sha256": states.realization_sha256,
        "coverage_scope": "exact_selected_roster_on_preregistered_validation_realization",
        "coverage_complete_over_enumerated_selected_ensembles": True,
        "selection_roster_sha256": roster_hash,
        "certified_roster": [entry.binding() for entry in roster],
        "certified_checkpoint_sha256": checkpoint_hashes,
        "certified_baseline_selection_sha256": baseline_hash,
        "selected_mi_samples_per_symbol": selected_mi,
        "selected_fock_cutoff": selected_fock,
        "mi_replications_stable": True,
        "all_mi_cases_converged": True,
        "all_fock_cases_converged": True,
        "all_holevo_threshold_sensitivity_cases_passed": True,
        "mi_artifact_sha256": file_sha256(args.mi_evidence.resolve()),
        "fock_artifact_sha256": file_sha256(args.fock_evidence.resolve()),
        "holevo_threshold_artifact_sha256": file_sha256(
            args.holevo_threshold_evidence.resolve()
        ),
        "resolved_config_sha256": canonical_json_sha256(config),
        "n_peak_photons": n_peak,
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
