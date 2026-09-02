"""Sequential, validation-only MI convergence certification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch

from _common import ROOT, load_yaml
from _numerical_validation import (
    ensemble_sha256, provenance, representative_ensembles, require,
    unique_ensemble_roster, validation_representative_states,
)
from src.cvqkd.mutual_information import (
    discrete_mutual_information, is_product_qam_ensemble, standard_complex_noise,
)
from src.validation.convergence import ConvergenceTolerance
from src.utils.random import derive_seed, torch_generator


def _canonical_hash(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "mi_convergence.json")
    args = parser.parse_args()
    path = args.config.resolve()
    config = load_yaml(path)
    require(config, [
        "numerical_validation.mi.sample_counts",
        "numerical_validation.mi.required_consecutive_refinement_passes",
        "numerical_validation.mi.absolute_tolerance_bits",
        "numerical_validation.mi.relative_tolerance",
        "numerical_validation.mi.seeds",
    ])
    settings = config["numerical_validation"]["mi"]
    counts = tuple(int(value) for value in settings["sample_counts"])
    required_passes = int(settings["required_consecutive_refinement_passes"])
    if len(counts) < 3 or counts != tuple(sorted(set(counts))):
        raise ValueError("Sequential sample counts need at least three increasing values.")
    if required_passes < 2 or required_passes >= len(counts):
        raise ValueError("Required refinement passes must be in [2,len(grid)-1].")
    tolerance = ConvergenceTolerance(
        float(settings["absolute_tolerance_bits"]), float(settings["relative_tolerance"])
    )
    tolerance.validate()
    base_seeds = tuple(int(value) for value in settings["seeds"])
    if len(base_seeds) < 2 or len(set(base_seeds)) != len(base_seeds):
        raise ValueError("MI certification needs at least two distinct replication seeds.")
    replication_seeds = tuple(
        derive_seed(seed, "mi_convergence_common_replication") for seed in base_seeds
    )
    states, state_labels, transmittance, epsilon = validation_representative_states(config)
    complete = representative_ensembles(config, transmittance, epsilon)
    ensembles, aliases = unique_ensemble_roster(complete)
    roster = {
        "validation_state_realization_sha256": states.realization_sha256,
        "state_labels": state_labels,
        "transmittance": transmittance.tolist(),
        "epsilon_snu": epsilon.tolist(),
        "canonical_fixtures": {name: ensemble_sha256(value) for name, value in ensembles.items()},
        "exact_duplicate_aliases": aliases,
        "replication_base_seeds": list(base_seeds),
        "derived_crn_seeds": list(replication_seeds),
        "sample_count_sequence": list(counts),
        "required_consecutive_refinement_passes": required_passes,
        "absolute_tolerance_bits": tolerance.absolute,
        "relative_tolerance": tolerance.relative,
    }
    roster_sha256 = _canonical_hash(roster)
    cumulative = {name: [None] * len(replication_seeds) for name in ensembles}
    traces = {
        name: {"replications": [{"rows": []} for _ in replication_seeds]}
        for name in ensembles
    }
    stage_rows: list[dict[str, object]] = []
    previous_count = 0
    consecutive = 0
    selected_count: int | None = None
    total_runtime = 0.0
    chunk_size = int(settings["noise_sample_chunk_size"])

    for stage_index, count in enumerate(counts):
        started = time.perf_counter()
        segment_count = count - previous_count
        print(
            f"MI stage {stage_index + 1}/{len(counts)} N_MC={count} increment={segment_count} "
            f"canonical_units={len(ensembles) * len(replication_seeds)}", flush=True,
        )
        refinement_passes: list[bool] = []
        for replication_index, seed in enumerate(replication_seeds):
            # One fixed maximum-length tensor is shared by every fixture in a
            # replication. This both enforces cross-configuration CRN and
            # avoids ten identical RNG calls.
            noise = standard_complex_noise(
                # A stage-dependent shape would move the imaginary stream
                # because all real values are drawn before all imaginary ones.
                (transmittance.shape[0], 256, counts[-1]),
                generator=torch_generator(seed, transmittance.device),
                device=transmittance.device,
            )
            for fixture_name, ensemble in ensembles.items():
                segment = discrete_mutual_information(
                    ensemble, transmittance, epsilon,
                    noise_samples_per_symbol=segment_count,
                    standard_noise_samples=noise[..., previous_count:count],
                    noise_sample_chunk_size=chunk_size,
                    implementation=(
                        "product" if is_product_qam_ensemble(ensemble) else "optimized"
                    ),
                ).detach()
                prior = cumulative[fixture_name][replication_index]
                estimate = segment if prior is None else (
                    previous_count * prior + segment_count * segment
                ) / count
                cumulative[fixture_name][replication_index] = estimate
                row: dict[str, object] = {"sample_count": count, "mi_bits": estimate.tolist()}
                if prior is not None:
                    error = (estimate - prior).abs()
                    bound = tolerance.bound(estimate)
                    passed = bool(torch.all(error <= bound))
                    refinement_passes.append(passed)
                    row.update({
                        "absolute_refinement_difference_bits_by_state": error.tolist(),
                        "maximum_allowed_error_bits_by_state": bound.tolist(),
                        "passes_refinement_tolerance": passed,
                    })
                traces[fixture_name]["replications"][replication_index]["rows"].append(row)
        replication_checks: dict[str, object] = {}
        for name, values in cumulative.items():
            stack = torch.stack(values)
            mean = stack.mean(dim=0)
            deviation = (stack - mean).abs().max(dim=0).values
            bound = tolerance.bound(mean)
            replication_checks[name] = {
                "mean_bits": mean.tolist(),
                "sample_variance_bits_squared": stack.var(dim=0, unbiased=True).tolist(),
                "maximum_deviation_bits": deviation.tolist(),
                "maximum_allowed_deviation_bits": bound.tolist(),
                "passes": bool(torch.all(deviation <= bound)),
            }
        refinements_ok = bool(refinement_passes) and all(refinement_passes)
        replications_ok = all(bool(value["passes"]) for value in replication_checks.values())
        consecutive = consecutive + 1 if refinements_ok and replications_ok else 0
        elapsed = time.perf_counter() - started
        total_runtime += elapsed
        stage_rows.append({
            "sample_count": count,
            "incremental_sample_count": segment_count,
            "stage_runtime_seconds": elapsed,
            "cumulative_runtime_seconds": total_runtime,
            "all_refinements_pass": refinements_ok,
            "all_reference_replications_stable": replications_ok,
            "consecutive_global_passes": consecutive,
            "replication_checks": replication_checks,
        })
        print(
            f"MI stage complete N_MC={count} seconds={elapsed:.3f} refinement={refinements_ok} "
            f"replication={replications_ok} consecutive={consecutive}/{required_passes}",
            flush=True,
        )
        previous_count = count
        if consecutive >= required_passes:
            selected_count = count
            break

    repeated_variance = {
        name: torch.stack(values).var(dim=0, unbiased=True).tolist()
        for name, values in cumulative.items()
    }
    for alias, canonical in aliases.items():
        traces[alias] = {"exact_duplicate_of": canonical,
                          "canonical_fixture_sha256": ensemble_sha256(ensembles[canonical])}
        repeated_variance[alias] = repeated_variance[canonical]
    worst = None
    if selected_count is not None:
        candidates = []
        for name, fixture in traces.items():
            if "replications" not in fixture:
                continue
            for replication_index, replication in enumerate(fixture["replications"]):
                row = replication["rows"][-1]
                for state_index, (error, bound) in enumerate(zip(
                    row["absolute_refinement_difference_bits_by_state"],
                    row["maximum_allowed_error_bits_by_state"],
                )):
                    candidates.append((error / bound, name, replication_index, state_index, error, bound))
        ratio, name, replication_index, state_index, error, bound = max(candidates)
        worst = {
            "fixture": name, "state_label": state_labels[state_index],
            "transmittance": float(transmittance[state_index]),
            "epsilon_snu": float(epsilon[state_index]),
            "replication_index": replication_index,
            "replication_base_seed": base_seeds[replication_index],
            "derived_crn_seed": replication_seeds[replication_index],
            "selected_common_sample_count": selected_count,
            "absolute_error_bits": float(error), "maximum_allowed_error_bits": float(bound),
            "error_to_tolerance_ratio": float(ratio),
        }
    scaling = None
    if len(stage_rows) >= 2:
        x = np.log([row["sample_count"] for row in stage_rows])
        y = np.log([row["cumulative_runtime_seconds"] for row in stage_rows])
        scaling = float(np.polyfit(x, y, 1)[0])
    payload = {
        "schema_version": "mi-sequential-convergence-v2",
        "status": "CONVERGENCE_SELECTED" if selected_count else "FAILED_PREREGISTERED_SEQUENCE",
        "is_convergence_certification": selected_count is not None,
        "publication_training_performed": False, "test_set_used": False,
        "state_split": "validation", "state_labels": state_labels,
        "states": {"transmittance": transmittance.tolist(), "epsilon_snu": epsilon.tolist()},
        "validation_state_realization_sha256": states.realization_sha256,
        "sequential_rule": {
            "sample_count_sequence": list(counts),
            "required_consecutive_refinement_passes": required_passes,
            "absolute_tolerance_bits": tolerance.absolute,
            "relative_tolerance": tolerance.relative,
            "replication_stability_required_at_each_passing_stage": True,
            "early_stop_only_by_frozen_rule": True,
        },
        "certification_roster": roster, "certification_roster_sha256": roster_sha256,
        "canonical_numerical_unit_count": len(ensembles) * len(replication_seeds),
        "avoided_exact_duplicate_unit_count": len(aliases) * len(replication_seeds),
        "traces": traces, "stages": stage_rows,
        "minimum_common_sample_count": selected_count,
        "convergence_selected_sample_count": selected_count,
        "repeated_run_variance_bits_squared": repeated_variance if selected_count else None,
        "worst_certified_state_fixture": worst,
        "runtime": {"total_seconds": total_runtime,
                    "empirical_cumulative_runtime_scaling_exponent": scaling,
                    "cuda_available": torch.cuda.is_available(),
                    "precision": "torch.float64 / torch.complex128"},
        "common_random_numbers_across_configurations": True,
        "selected_ensemble_certification": None,
        "provenance": provenance(path, config, complete),
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.resolve()}")
    return 0 if selected_count is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
