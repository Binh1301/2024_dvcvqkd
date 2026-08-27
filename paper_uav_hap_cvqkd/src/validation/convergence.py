"""Nested-sample MI and Fock-cutoff convergence diagnostics.

These functions select a numerical setting only relative to the largest
explicitly evaluated reference setting.  They do not claim coverage outside
the supplied states and ensembles; publication scripts must record that
scope in their output artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable

import numpy as np
import torch

from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import (
    discrete_mutual_information,
    standard_complex_noise,
)
from src.modulation.joint_ps_gs import Ensemble
from src.utils.random import torch_generator


@dataclass(frozen=True)
class ConvergenceTolerance:
    """Absolute-plus-relative comparison tolerance."""

    absolute: float
    relative: float

    def validate(self) -> None:
        if not math.isfinite(self.absolute) or self.absolute <= 0.0:
            raise ValueError("absolute convergence tolerance must be finite and positive.")
        if not math.isfinite(self.relative) or self.relative < 0.0:
            raise ValueError("relative convergence tolerance must be finite and nonnegative.")

    def bound(self, reference: torch.Tensor) -> torch.Tensor:
        self.validate()
        return self.absolute + self.relative * reference.abs()


def _strict_grid(values: Iterable[int], *, name: str, minimum: int) -> tuple[int, ...]:
    grid = tuple(values)
    if len(grid) < 2 or any(not isinstance(value, int) or value < minimum for value in grid):
        raise ValueError(f"{name} must contain at least two integers >= {minimum}.")
    if any(right <= left for left, right in zip(grid, grid[1:])):
        raise ValueError(f"{name} must be strictly increasing.")
    return grid


def _first_suffix_converged(
    errors: list[torch.Tensor], bounds: list[torch.Tensor], settings: tuple[int, ...]
) -> int | None:
    # The last setting is the explicit numerical reference, not a candidate.
    passed = [bool(torch.all(error <= bound)) for error, bound in zip(errors, bounds)]
    for index in range(len(settings) - 1):
        if all(passed[index : len(settings) - 1]):
            return settings[index]
    return None


def mi_convergence_trace(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    sample_counts: Iterable[int],
    seed: int,
    tolerance: ConvergenceTolerance,
    noise_sample_chunk_size: int | None = None,
) -> dict[str, Any]:
    """Evaluate nested common-random-number MI convergence.

    The largest count is the reference.  A candidate is accepted only when it
    and every larger evaluated candidate satisfy the declared tolerance against
    that same reference, preventing an isolated lucky crossing.
    """

    counts = _strict_grid(sample_counts, name="sample_counts", minimum=1)
    tolerance.validate()
    ensemble.validate()
    max_count = counts[-1]
    noise = standard_complex_noise(
        (ensemble.probabilities.shape[0], ensemble.probabilities.shape[1], max_count),
        generator=torch_generator(seed, ensemble.probabilities.device),
        device=ensemble.probabilities.device,
    )
    # Evaluate each newly added CRN segment exactly once. Because the estimator
    # is an arithmetic mean over noise samples, the count-prefix estimate is
    # the sample-count-weighted mean of segment estimates. This is algebraically
    # identical to recomputing every prefix and reduces the preregistered grid
    # workload from sum(counts) to max(counts).
    estimates: list[torch.Tensor] = []
    cumulative: torch.Tensor | None = None
    previous = 0
    for count in counts:
        segment_count = count - previous
        segment = discrete_mutual_information(
            ensemble,
            transmittance,
            epsilon,
            noise_samples_per_symbol=segment_count,
            standard_noise_samples=noise[..., previous:count],
            noise_sample_chunk_size=noise_sample_chunk_size,
        ).detach()
        cumulative = (
            segment if cumulative is None
            else (previous * cumulative + segment_count * segment) / count
        )
        estimates.append(cumulative)
        previous = count
    reference = estimates[-1]
    errors = [(value - reference).abs() for value in estimates]
    bounds = [tolerance.bound(reference) for _ in estimates]
    selected = _first_suffix_converged(errors, bounds, counts)
    return {
        "reference_sample_count": max_count,
        "selected_sample_count": selected,
        "converged": selected is not None,
        "absolute_tolerance_bits": tolerance.absolute,
        "relative_tolerance": tolerance.relative,
        "seed": seed,
        "noise_sample_chunk_size": noise_sample_chunk_size,
        "rows": [
            {
                "sample_count": count,
                "mi_bits": value.tolist(),
                "absolute_error_bits_by_state": error.tolist(),
                "maximum_allowed_error_bits_by_state": bound.tolist(),
                "maximum_absolute_error_bits": float(error.max()),
                "maximum_allowed_error_bits": float(bound.max()),
                "passes_reference_tolerance": bool(torch.all(error <= bound)),
            }
            for count, value, error, bound in zip(counts, estimates, errors, bounds)
        ],
    }


def summarize_mi_replications(
    traces: dict[str, dict[str, Any]],
    *,
    state_labels: list[str] | tuple[str, ...],
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    replication_base_seeds: tuple[int, ...],
    derived_replication_seeds: tuple[int, ...],
    selected_common_sample_count: int | None,
) -> dict[str, Any]:
    """Report reference variance and the limiting certified fixture/state.

    A blocked/incomplete run has no traces and must report both fields as
    unavailable rather than synthesizing a variance or worst case.
    """

    if not traces:
        return {
            "repeated_run_variance_bits_squared": None,
            "worst_certified_state_fixture": None,
        }
    if len(replication_base_seeds) != len(derived_replication_seeds):
        raise ValueError("Base and derived MI replication seed lists must match.")
    t = transmittance.detach().reshape(-1)
    e = epsilon.detach().reshape(-1)
    if not (len(state_labels) == t.numel() == e.numel()):
        raise ValueError("MI reporting state labels and tensors must have matching lengths.")
    repeated_variance: dict[str, list[float]] = {}
    for fixture_name, fixture in traces.items():
        replications = fixture.get("replications", [])
        if len(replications) != len(replication_base_seeds) or len(replications) < 2:
            raise ValueError("Every MI fixture needs the complete preregistered replications.")
        references = np.asarray(
            [replication["rows"][-1]["mi_bits"] for replication in replications],
            dtype=np.float64,
        )
        repeated_variance[fixture_name] = np.var(references, axis=0, ddof=1).tolist()
    worst: dict[str, Any] | None = None
    if selected_common_sample_count is not None:
        worst_ratio = -1.0
        for fixture_name, fixture in traces.items():
            for replication_index, replication in enumerate(fixture["replications"]):
                rows = [
                    row for row in replication["rows"]
                    if row["sample_count"] == selected_common_sample_count
                ]
                if len(rows) != 1:
                    raise ValueError("Selected MI count must occur exactly once in every trace.")
                row = rows[0]
                for state_index, (error, allowed) in enumerate(zip(
                    row["absolute_error_bits_by_state"],
                    row["maximum_allowed_error_bits_by_state"],
                )):
                    ratio = float(error) / float(allowed)
                    if ratio > worst_ratio:
                        worst_ratio = ratio
                        worst = {
                            "fixture": fixture_name,
                            "state_label": state_labels[state_index],
                            "state_index_within_fixture": state_index,
                            "transmittance": float(t[state_index]),
                            "epsilon_snu": float(e[state_index]),
                            "replication_index": replication_index,
                            "replication_base_seed": int(
                                replication_base_seeds[replication_index]
                            ),
                            "derived_crn_seed": int(
                                derived_replication_seeds[replication_index]
                            ),
                            "selected_common_sample_count": int(
                                selected_common_sample_count
                            ),
                            "absolute_error_bits": float(error),
                            "maximum_allowed_error_bits": float(allowed),
                            "error_to_tolerance_ratio": ratio,
                        }
    return {
        "repeated_run_variance_bits_squared": repeated_variance,
        "worst_certified_state_fixture": worst,
    }


def fock_convergence_trace(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    cutoffs: Iterable[int],
    tolerance: ConvergenceTolerance,
    symplectic_tolerance: ConvergenceTolerance | None = None,
    information_tolerance: ConvergenceTolerance | None = None,
    mutual_information_bits: torch.Tensor | None = None,
    beta_reconciliation: float | None = None,
    density_trace_tolerance: float,
    symmetry_tolerance: float = 1e-8,
    density_eigenvalue_tolerance: float = 1e-12,
    physicality_tolerance: float = 1e-10,
) -> dict[str, Any]:
    """Evaluate convergence of C, w, Z, and chi_BE against the largest cutoff."""

    grid = _strict_grid(cutoffs, name="cutoffs", minimum=2)
    tolerance.validate()
    symplectic_tolerance = symplectic_tolerance or tolerance
    information_tolerance = information_tolerance or tolerance
    symplectic_tolerance.validate()
    information_tolerance.validate()
    if (mutual_information_bits is None) != (beta_reconciliation is None):
        raise ValueError("MI and beta must either both be supplied or both omitted.")
    if beta_reconciliation is not None and (
        not math.isfinite(beta_reconciliation) or not 0.0 < beta_reconciliation <= 1.0
    ):
        raise ValueError("beta_reconciliation must lie in (0,1].")
    if mutual_information_bits is not None:
        mutual_information_bits = mutual_information_bits.detach().reshape(-1)
        if mutual_information_bits.shape[0] != ensemble.probabilities.shape[0]:
            raise ValueError("MI must have one value per Fock convergence state.")
        if not bool(torch.all(torch.isfinite(mutual_information_bits))):
            raise ValueError("MI values used for SKR convergence must be finite.")
    if not math.isfinite(density_trace_tolerance) or density_trace_tolerance <= 0.0:
        raise ValueError("density_trace_tolerance must be finite and positive.")
    values: list[dict[str, torch.Tensor]] = []
    failures: list[dict[str, Any]] = []
    for cutoff in grid:
        try:
            result = holevo_information(
                ensemble,
                transmittance,
                epsilon,
                fock_cutoff=cutoff,
                density_trace_tolerance=density_trace_tolerance,
                symmetry_tolerance=symmetry_tolerance,
                density_eigenvalue_tolerance=density_eigenvalue_tolerance,
                physicality_tolerance=physicality_tolerance,
            )
        except (ValueError, RuntimeError) as error:
            failures.append({"fock_cutoff": cutoff, "error": str(error)})
            values.append({})
            continue
        values.append(
            {
                "C": result.coherent_correlation.detach(),
                "w": result.w.detach(),
                "Z": result.z.detach(),
                "chi_BE": result.chi_be.detach(),
                "lambda1": result.covariance.lambda1.detach(),
                "lambda2": result.covariance.lambda2.detach(),
                "lambda3": result.covariance.lambda3.detach(),
                "trace_error": (result.tau_trace.detach() - 1.0).abs(),
            }
        )
        if mutual_information_bits is not None:
            values[-1]["raw_K"] = (
                float(beta_reconciliation) * mutual_information_bits - result.chi_be.detach()
            )
    if not values[-1]:
        return {
            "reference_fock_cutoff": grid[-1],
            "selected_fock_cutoff": None,
            "converged": False,
            "failures": failures,
            "rows": [],
        }
    reference = values[-1]
    rows: list[dict[str, Any]] = []
    candidate_passes: list[bool] = []
    for cutoff, value in zip(grid, values):
        if not value:
            rows.append({"fock_cutoff": cutoff, "passes_reference_tolerance": False})
            candidate_passes.append(False)
            continue
        metric_errors: dict[str, float] = {}
        metric_bounds: dict[str, float] = {}
        metric_passes: list[bool] = []
        metric_tolerances = {
            "C": tolerance, "w": tolerance, "Z": tolerance,
            "lambda1": symplectic_tolerance, "lambda2": symplectic_tolerance,
            "lambda3": symplectic_tolerance, "chi_BE": information_tolerance,
        }
        if mutual_information_bits is not None:
            metric_tolerances["raw_K"] = information_tolerance
        for name, metric_tolerance in metric_tolerances.items():
            error = (value[name] - reference[name]).abs()
            bound = metric_tolerance.bound(reference[name])
            metric_errors[name] = float(error.max())
            metric_bounds[name] = float(bound.max())
            metric_passes.append(bool(torch.all(error <= bound)))
        trace_error = float(value["trace_error"].max())
        passed = all(metric_passes) and trace_error <= density_trace_tolerance
        candidate_passes.append(passed)
        rows.append(
            {
                "fock_cutoff": cutoff,
                "maximum_absolute_errors": metric_errors,
                "maximum_allowed_errors": metric_bounds,
                "maximum_density_trace_error": trace_error,
                "passes_reference_tolerance": passed,
                "values": {name: value[name].tolist() for name in metric_tolerances},
            }
        )
    selected: int | None = None
    for index in range(len(grid) - 1):
        if all(candidate_passes[index : len(grid) - 1]):
            selected = grid[index]
            break
    return {
        "reference_fock_cutoff": grid[-1],
        "selected_fock_cutoff": selected,
        "converged": selected is not None,
        "absolute_tolerance": tolerance.absolute,
        "relative_tolerance": tolerance.relative,
        "symplectic_absolute_tolerance": symplectic_tolerance.absolute,
        "symplectic_relative_tolerance": symplectic_tolerance.relative,
        "information_absolute_tolerance_bits": information_tolerance.absolute,
        "information_relative_tolerance": information_tolerance.relative,
        "instantaneous_raw_skr_included": mutual_information_bits is not None,
        "density_trace_tolerance": density_trace_tolerance,
        "symmetry_tolerance": symmetry_tolerance,
        "density_eigenvalue_pseudoinverse_tolerance": density_eigenvalue_tolerance,
        "physicality_tolerance": physicality_tolerance,
        "failures": failures,
        "rows": rows,
    }


def holevo_threshold_sensitivity_trace(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    *,
    fock_cutoff: int,
    density_eigenvalue_tolerances: Iterable[float],
    selected_tolerance: float,
    tolerance: ConvergenceTolerance,
    symmetry_tolerance: float,
    density_trace_tolerance: float,
    physicality_tolerance: float,
) -> dict[str, Any]:
    """Measure C/w/Z/chi sensitivity to the density pseudoinverse threshold."""

    grid = tuple(float(value) for value in density_eigenvalue_tolerances)
    if len(grid) < 2 or any(not math.isfinite(value) or value <= 0.0 for value in grid):
        raise ValueError("Pseudoinverse threshold grid needs at least two positive finite values.")
    if any(right <= left for left, right in zip(grid, grid[1:])):
        raise ValueError("Pseudoinverse threshold grid must be strictly increasing.")
    if selected_tolerance not in grid:
        raise ValueError("The active pseudoinverse threshold must be on the sensitivity grid.")
    tolerance.validate()
    rows: list[dict[str, Any]] = []
    results = []
    for value in grid:
        result = holevo_information(
            ensemble, transmittance, epsilon, fock_cutoff=fock_cutoff,
            symmetry_tolerance=symmetry_tolerance,
            density_trace_tolerance=density_trace_tolerance,
            density_eigenvalue_tolerance=value,
            physicality_tolerance=physicality_tolerance,
        )
        results.append(result)
    reference = results[0]
    for threshold, result in zip(grid, results):
        errors: dict[str, float] = {}
        bounds: dict[str, float] = {}
        passed = True
        for name, candidate, reference_value in (
            ("C", result.coherent_correlation, reference.coherent_correlation),
            ("w", result.w, reference.w), ("Z", result.z, reference.z),
            ("chi_BE", result.chi_be, reference.chi_be),
        ):
            error = (candidate.detach() - reference_value.detach()).abs()
            bound = tolerance.bound(reference_value.detach())
            errors[name] = float(error.max())
            bounds[name] = float(bound.max())
            passed = passed and bool(torch.all(error <= bound))
        rows.append({
            "density_eigenvalue_pseudoinverse_tolerance": threshold,
            "maximum_absolute_errors": errors,
            "maximum_allowed_errors": bounds,
            "passes": passed,
            "suppressed_density_eigenvalues": result.diagnostics[
                "suppressed_density_eigenvalues"
            ],
        })
    selected_row = rows[grid.index(selected_tolerance)]
    return {
        "reference_density_eigenvalue_pseudoinverse_tolerance": grid[0],
        "selected_density_eigenvalue_pseudoinverse_tolerance": selected_tolerance,
        "selected_threshold_passes": selected_row["passes"],
        "absolute_tolerance": tolerance.absolute,
        "relative_tolerance": tolerance.relative,
        "rows": rows,
    }


def select_representative_state_indices(
    transmittance: np.ndarray, epsilon: np.ndarray
) -> dict[str, int]:
    """Select outcome-independent bad/medium/good validation states.

    Targets are the componentwise (T, epsilon) quantiles (10%,90%),
    (50%,50%), and (90%,10%).  Nearest-state distance is calculated after
    scaling each coordinate by its validation interdecile range.  Ties use the
    original realization order.
    """

    t = np.asarray(transmittance, dtype=np.float64).reshape(-1)
    e = np.asarray(epsilon, dtype=np.float64).reshape(-1)
    if t.shape != e.shape or t.size < 3:
        raise ValueError("Representative-state selection requires matching arrays of size >= 3.")
    if np.any(~np.isfinite(t)) or np.any(t <= 0.0) or np.any(~np.isfinite(e)) or np.any(e < 0.0):
        raise ValueError("Representative states must be finite and physical.")
    t_scale = float(np.quantile(t, 0.9) - np.quantile(t, 0.1))
    e_scale = float(np.quantile(e, 0.9) - np.quantile(e, 0.1))
    if t_scale <= 0.0 or e_scale <= 0.0:
        raise ValueError("Both channel-state coordinates must vary.")
    definitions = {"bad": (0.1, 0.9), "medium": (0.5, 0.5), "good": (0.9, 0.1)}
    chosen: dict[str, int] = {}
    for name, (t_quantile, e_quantile) in definitions.items():
        target_t = float(np.quantile(t, t_quantile))
        target_e = float(np.quantile(e, e_quantile))
        distance = ((t - target_t) / t_scale) ** 2 + ((e - target_e) / e_scale) ** 2
        chosen[name] = int(np.argmin(distance))
    if len(set(chosen.values())) != 3:
        raise ValueError("Validation realization does not yield three distinct representative states.")
    return chosen
