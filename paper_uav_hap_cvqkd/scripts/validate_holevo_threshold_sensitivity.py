"""Validation-only sensitivity audit for the Holevo density pseudoinverse threshold."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _numerical_validation import (
    provenance, representative_ensembles, require, unique_ensemble_roster,
    validation_representative_states,
)
from src.validation.convergence import (
    ConvergenceTolerance, holevo_threshold_sensitivity_trace,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "holevo_threshold_sensitivity.json",
    )
    parser.add_argument("--mi-evidence", type=Path,
                        default=ROOT / "results" / "mi_convergence.json")
    parser.add_argument("--fock-evidence", type=Path,
                        default=ROOT / "results" / "fock_convergence.json")
    args = parser.parse_args()
    path = args.config.resolve()
    config = load_yaml(path)
    require(config, [
        "numerical_validation.holevo_threshold_sensitivity.density_eigenvalue_pseudoinverse_tolerances",
        "numerical_validation.holevo_threshold_sensitivity.absolute_tolerance",
        "numerical_validation.holevo_threshold_sensitivity.relative_tolerance",
    ])
    settings = config["numerical_validation"]["holevo_threshold_sensitivity"]
    thresholds = holevo_numerical_kwargs(config)
    states, labels, t, epsilon = validation_representative_states(config)
    complete_ensembles = representative_ensembles(config, t, epsilon)
    ensembles, aliases = unique_ensemble_roster(complete_ensembles)
    mi_path = args.mi_evidence.resolve()
    mi_evidence = json.loads(mi_path.read_text(encoding="utf-8"))
    if mi_evidence.get("minimum_common_sample_count") is None:
        raise ValueError("Threshold sensitivity requires passed MI convergence evidence.")
    fock_path = args.fock_evidence.resolve()
    fock_evidence = json.loads(fock_path.read_text(encoding="utf-8"))
    selected_fock_cutoff = fock_evidence.get(
        "minimum_common_fock_cutoff_for_listed_ensembles"
    )
    if selected_fock_cutoff is None:
        payload = {
            "schema_version": "holevo-threshold-dependency-blocker-v1",
            "status": "NOT_RUN_FOCK_DEPENDENCY",
            "test_set_used": False,
            "validation_state_realization_sha256": states.realization_sha256,
            "state_labels": labels,
            "all_listed_fixtures_pass": False,
            "selected_ensemble_certification": None,
            "traces": {},
            "exact_duplicate_aliases": {},
            "mi_evidence_sha256": hashlib.sha256(mi_path.read_bytes()).hexdigest(),
            "fock_evidence_sha256": hashlib.sha256(fock_path.read_bytes()).hexdigest(),
            "convergence_selected_fock_cutoff": None,
            "provenance": provenance(path, config, complete_ensembles),
            "blocker": "Threshold sensitivity requires passed Fock convergence evidence.",
        }
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        return 2
    mi_by_ensemble = {}
    for name in ensembles:
        replications = mi_evidence["traces"][name]["replications"]
        mi_by_ensemble[name] = __import__("torch").as_tensor(
            [replication["rows"][-1]["mi_bits"] for replication in replications],
            dtype=__import__("torch").float64,
        ).mean(dim=0)
    comparison = ConvergenceTolerance(
        float(settings["absolute_tolerance"]), float(settings["relative_tolerance"])
    )
    traces = {
        name: holevo_threshold_sensitivity_trace(
            ensemble, t, epsilon, fock_cutoff=int(selected_fock_cutoff),
            density_eigenvalue_tolerances=settings[
                "density_eigenvalue_pseudoinverse_tolerances"
            ],
            selected_tolerance=thresholds["density_eigenvalue_tolerance"],
            tolerance=comparison,
            symmetry_tolerance=thresholds["symmetry_tolerance"],
            density_trace_tolerance=thresholds["density_trace_tolerance"],
            physicality_tolerance=thresholds["physicality_tolerance"],
            mutual_information_bits=mi_by_ensemble[name],
            beta_reconciliation=float(config["cvqkd"]["beta_reconciliation"]),
        )
        for name, ensemble in ensembles.items()
    }
    for alias, canonical in aliases.items():
        traces[alias] = {"exact_duplicate_of": canonical,
                          "selected_threshold_passes": traces[canonical]["selected_threshold_passes"]}
    payload = {
        "status": "validation-only threshold sensitivity; not publication certification",
        "test_set_used": False,
        "validation_state_realization_sha256": states.realization_sha256,
        "state_labels": labels,
        "all_listed_fixtures_pass": all(
            trace["selected_threshold_passes"] for trace in traces.values()
        ),
        "selected_ensemble_certification": None,
        "traces": traces,
        "exact_duplicate_aliases": aliases,
        "mi_evidence_sha256": hashlib.sha256(mi_path.read_bytes()).hexdigest(),
        "fock_evidence_sha256": hashlib.sha256(fock_path.read_bytes()).hexdigest(),
        "convergence_selected_fock_cutoff": int(selected_fock_cutoff),
        "provenance": provenance(path, config, complete_ensembles),
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if payload["all_listed_fixtures_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
