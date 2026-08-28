"""Bounded validation of Fock convergence for C, w, Z, and chi_BE."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _common import (
    ROOT, holevo_numerical_kwargs, load_yaml,
)
from _numerical_validation import (
    provenance,
    representative_ensembles,
    require,
    unique_ensemble_roster,
    validation_representative_states,
)
from src.validation.convergence import ConvergenceTolerance, fock_convergence_trace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--mi-evidence", type=Path,
        default=ROOT / "results" / "mi_convergence.json",
        help="Preregistered MI evidence used only to report raw K at every cutoff.",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "fock_convergence.json")
    args = parser.parse_args()
    path = args.config.resolve()
    config = load_yaml(path)
    require(
        config,
        [
            "numerical_validation.fock.cutoffs",
            "numerical_validation.fock.moment_absolute_tolerance",
            "numerical_validation.fock.moment_relative_tolerance",
            "numerical_validation.fock.symplectic_absolute_tolerance",
            "numerical_validation.fock.symplectic_relative_tolerance",
            "numerical_validation.fock.information_absolute_tolerance_bits",
            "numerical_validation.fock.information_relative_tolerance",
            "numerical_validation.fock.density_trace_tolerance",
            "cvqkd.beta_reconciliation",
        ],
    )
    values = config["numerical_validation"]["fock"]
    holevo_thresholds = holevo_numerical_kwargs(config)
    if float(values["density_trace_tolerance"]) != holevo_thresholds[
        "density_trace_tolerance"
    ]:
        raise ValueError("Fock convergence and active Holevo trace tolerances must match.")
    states, state_labels, t, epsilon = validation_representative_states(config)
    complete_ensembles = representative_ensembles(config, t, epsilon)
    ensembles, aliases = unique_ensemble_roster(complete_ensembles)
    moment_tolerance = ConvergenceTolerance(
        float(values["moment_absolute_tolerance"]),
        float(values["moment_relative_tolerance"]),
    )
    symplectic_tolerance = ConvergenceTolerance(
        float(values["symplectic_absolute_tolerance"]),
        float(values["symplectic_relative_tolerance"]),
    )
    information_tolerance = ConvergenceTolerance(
        float(values["information_absolute_tolerance_bits"]),
        float(values["information_relative_tolerance"]),
    )
    mi_path = args.mi_evidence.resolve()
    mi_evidence = json.loads(mi_path.read_text(encoding="utf-8"))
    expected_provenance = provenance(path, config, complete_ensembles)
    if mi_evidence.get("validation_state_realization_sha256") != states.realization_sha256:
        raise ValueError("MI evidence is not bound to the same validation realization.")
    if mi_evidence.get("provenance", {}).get("resolved_config_sha256") != expected_provenance[
        "resolved_config_sha256"
    ]:
        raise ValueError("MI evidence is not bound to the same resolved configuration.")
    mi_by_ensemble = {}
    selected_mi_count = int(mi_evidence["minimum_common_sample_count"])
    for name in ensembles:
        replications = mi_evidence.get("traces", {}).get(name, {}).get("replications", [])
        if not replications:
            raise ValueError(f"MI evidence is missing fixture {name}.")
        selected_rows = [
            next(
                row for row in replication["rows"]
                if int(row["sample_count"]) == selected_mi_count
            )
            for replication in replications
        ]
        references = torch.as_tensor(
            [row["mi_bits"] for row in selected_rows],
            dtype=torch.float64,
        )
        mi_by_ensemble[name] = references.mean(dim=0)
    traces = {
        name: fock_convergence_trace(
            ensemble,
            t,
            epsilon,
            cutoffs=tuple(int(value) for value in values["cutoffs"]),
            tolerance=moment_tolerance,
            symplectic_tolerance=symplectic_tolerance,
            information_tolerance=information_tolerance,
            mutual_information_bits=mi_by_ensemble[name],
            beta_reconciliation=float(config["cvqkd"]["beta_reconciliation"]),
            density_trace_tolerance=float(values["density_trace_tolerance"]),
            **{
                key: value for key, value in holevo_thresholds.items()
                if key != "density_trace_tolerance"
            },
        )
        for name, ensemble in ensembles.items()
    }
    for alias, canonical in aliases.items():
        traces[alias] = {
            "exact_duplicate_of": canonical,
            "selected_fock_cutoff": traces[canonical]["selected_fock_cutoff"],
            "converged": traces[canonical]["converged"],
        }
    selected = [trace["selected_fock_cutoff"] for trace in traces.values()]
    all_listed_fixtures_pass = not any(value is None for value in selected)
    failed_fixtures = sorted(
        name for name, trace in traces.items()
        if trace.get("selected_fock_cutoff") is None
    )
    payload = {
        "schema_version": "fock-convergence-evidence-v2",
        "status": (
            "CONVERGENCE_SELECTED"
            if all_listed_fixtures_pass
            else "FAILED_FROZEN_TOLERANCE"
        ),
        "is_convergence_certification": all_listed_fixtures_pass,
        "publication_training_performed": False,
        "test_set_used": False,
        "state_split": "validation",
        "state_labels": state_labels,
        "states": {"transmittance": t.tolist(), "epsilon_snu": epsilon.tolist()},
        "validation_state_realization_sha256": states.realization_sha256,
        "traces": traces,
        "exact_duplicate_aliases": aliases,
        "minimum_common_fock_cutoff_for_listed_ensembles": (
            None if not all_listed_fixtures_pass
            else max(int(value) for value in selected)
        ),
        "failed_fixtures": failed_fixtures,
        "blocker": (
            None
            if all_listed_fixtures_pass
            else "No selectable Fock cutoff satisfies every frozen metric tolerance "
                 "for the complete preregistered fixture roster."
        ),
        "selected_ensemble_certification": None,
        "mi_evidence_path": str(mi_path),
        "mi_evidence_sha256": __import__("hashlib").sha256(mi_path.read_bytes()).hexdigest(),
        "provenance": expected_provenance,
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote bounded Fock convergence evidence to {args.output.resolve()}")
    # This script supplies validation evidence only; the combined gate verifies
    # the approved domain/config hashes before publication execution.
    return 0 if payload["minimum_common_fock_cutoff_for_listed_ensembles"] is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
