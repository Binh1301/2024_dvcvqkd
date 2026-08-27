"""Validation-only sensitivity audit for the Holevo density pseudoinverse threshold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _numerical_validation import (
    provenance, representative_ensembles, require, validation_representative_states,
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
    args = parser.parse_args()
    path = args.config.resolve()
    config = load_yaml(path)
    require(config, [
        "cvqkd.fock_cutoff",
        "numerical_validation.holevo_threshold_sensitivity.density_eigenvalue_pseudoinverse_tolerances",
        "numerical_validation.holevo_threshold_sensitivity.absolute_tolerance",
        "numerical_validation.holevo_threshold_sensitivity.relative_tolerance",
    ])
    settings = config["numerical_validation"]["holevo_threshold_sensitivity"]
    thresholds = holevo_numerical_kwargs(config)
    states, labels, t, epsilon = validation_representative_states(config)
    ensembles = representative_ensembles(config, t, epsilon)
    comparison = ConvergenceTolerance(
        float(settings["absolute_tolerance"]), float(settings["relative_tolerance"])
    )
    traces = {
        name: holevo_threshold_sensitivity_trace(
            ensemble, t, epsilon, fock_cutoff=int(config["cvqkd"]["fock_cutoff"]),
            density_eigenvalue_tolerances=settings[
                "density_eigenvalue_pseudoinverse_tolerances"
            ],
            selected_tolerance=thresholds["density_eigenvalue_tolerance"],
            tolerance=comparison,
            symmetry_tolerance=thresholds["symmetry_tolerance"],
            density_trace_tolerance=thresholds["density_trace_tolerance"],
            physicality_tolerance=thresholds["physicality_tolerance"],
        )
        for name, ensemble in ensembles.items()
    }
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
        "provenance": provenance(path, config, ensembles),
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if payload["all_listed_fixtures_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
