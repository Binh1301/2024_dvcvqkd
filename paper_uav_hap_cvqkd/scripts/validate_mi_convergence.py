"""Bounded validation of mutual-information Monte Carlo convergence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from _common import ROOT, load_yaml
from _numerical_validation import (
    provenance,
    representative_ensembles,
    require,
    validation_representative_states,
)
from src.validation.convergence import (
    ConvergenceTolerance, mi_convergence_trace, summarize_mi_replications,
)
from src.utils.random import derive_seed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "mi_convergence.json")
    args = parser.parse_args()
    path = args.config.resolve()
    config = load_yaml(path)
    require(
        config,
        [
            "numerical_validation.mi.sample_counts",
            "numerical_validation.mi.absolute_tolerance_bits",
            "numerical_validation.mi.relative_tolerance",
            "numerical_validation.mi.seeds",
        ],
    )
    values = config["numerical_validation"]["mi"]
    states, state_labels, t, epsilon = validation_representative_states(config)
    ensembles = representative_ensembles(config, t, epsilon)
    tolerance = ConvergenceTolerance(
        float(values["absolute_tolerance_bits"]), float(values["relative_tolerance"])
    )
    base_seeds = tuple(values["seeds"])
    if len(base_seeds) < 2 or any(not isinstance(seed, int) or seed < 0 for seed in base_seeds):
        raise ValueError("MI convergence requires at least two nonnegative replication seeds.")
    if len(set(base_seeds)) != len(base_seeds):
        raise ValueError("MI convergence replication seeds must be distinct.")
    # Each ensemble gets the same nested standard-noise realization for a
    # replication, so comparisons also use cross-configuration common randomness.
    replication_seeds = tuple(
        derive_seed(seed, "mi_convergence_common_replication") for seed in base_seeds
    )
    traces: dict[str, dict[str, object]] = {}
    selected: list[int | None] = []
    reference_replication_checks: dict[str, dict[str, object]] = {}
    for name, ensemble in ensembles.items():
        ensemble_traces = []
        for replication_index, seed in enumerate(replication_seeds):
            started = time.perf_counter()
            print(
                f"MI fixture={name} replication={replication_index + 1}/{len(replication_seeds)} "
                f"reference_count={max(int(value) for value in values['sample_counts'])}",
                flush=True,
            )
            ensemble_traces.append(mi_convergence_trace(
                ensemble,
                t,
                epsilon,
                sample_counts=tuple(int(value) for value in values["sample_counts"]),
                seed=seed,
                tolerance=tolerance,
                noise_sample_chunk_size=int(values["noise_sample_chunk_size"]),
            ))
            print(
                f"MI completed fixture={name} replication={replication_index + 1} "
                f"elapsed_seconds={time.perf_counter() - started:.3f}",
                flush=True,
            )
        traces[name] = {
            "replications": ensemble_traces,
            "all_replications_converged": all(trace["converged"] for trace in ensemble_traces),
        }
        selected.extend(trace["selected_sample_count"] for trace in ensemble_traces)
        references = np.asarray(
            [trace["rows"][-1]["mi_bits"] for trace in ensemble_traces], dtype=np.float64
        )
        reference_mean = references.mean(axis=0)
        maximum_deviation = np.max(np.abs(references - reference_mean), axis=0)
        allowed = tolerance.absolute + tolerance.relative * np.abs(reference_mean)
        reference_replication_checks[name] = {
            "reference_mean_bits": reference_mean.tolist(),
            "reference_repeated_run_variance_bits_squared": np.var(
                references, axis=0, ddof=1
            ).tolist(),
            "maximum_replication_deviation_bits": maximum_deviation.tolist(),
            "maximum_allowed_deviation_bits": allowed.tolist(),
            "passes": bool(np.all(maximum_deviation <= allowed)),
        }
    references_stable = all(value["passes"] for value in reference_replication_checks.values())
    minimum_common = (
        None
        if any(value is None for value in selected) or not references_stable
        else max(int(value) for value in selected)
    )
    reporting = summarize_mi_replications(
        traces,
        state_labels=state_labels,
        transmittance=t,
        epsilon=epsilon,
        replication_base_seeds=base_seeds,
        derived_replication_seeds=replication_seeds,
        selected_common_sample_count=minimum_common,
    )
    payload = {
        "status": "bounded numerical validation; not a publication result",
        "state_split": "validation",
        "state_labels": state_labels,
        "states": {"transmittance": t.tolist(), "epsilon_snu": epsilon.tolist()},
        "validation_state_realization_sha256": states.realization_sha256,
        "traces": traces,
        "replication_base_seeds": list(base_seeds),
        "common_random_numbers_across_configurations": True,
        "reference_replication_checks": reference_replication_checks,
        "reference_replications_stable": references_stable,
        **reporting,
        "minimum_common_sample_count": minimum_common,
        # Finite bad/medium/good fixtures cannot attest the selected publication
        # roster. The separate exact-roster producer emits a different evidence
        # schema; this finite-fixture field must remain null.
        "selected_ensemble_certification": None,
        "provenance": provenance(path, config, ensembles),
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote bounded MI convergence evidence to {args.output.resolve()}")
    return 0 if payload["minimum_common_sample_count"] is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
