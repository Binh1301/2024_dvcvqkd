"""Diagnose the preregistered near-coincident Fock fixture without selection.

This script is validation-only and does not alter the frozen estimator. It
compares the active full-matrix spectral construction with the algebraically
equivalent support-basis evaluation to isolate truncation, threshold/support,
and matrix-reconstruction cancellation effects.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import torch

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _numerical_validation import (
    provenance, representative_ensembles, validation_representative_states,
)
from src.cvqkd.holevo import (
    bosonic_entropy, coherent_state_vectors, holevo_information,
    support_restricted_source_moments,
)
from src.cvqkd.covariance import standard_form_covariance


# Frozen prospectively on 2026-08-28 before any result above cutoff 128 was
# inspected. Cutoff 256 is the nonselectable reference; tolerances are unchanged.
PREREGISTERED_EXTENSION_CUTOFFS = (144, 160, 192, 224, 256)


def _stable_suffix_against_last_reference(
    rows: list[dict[str, object]], config: dict[str, object], *, path: str
) -> dict[str, object]:
    settings = config["numerical_validation"]["fock"]
    tolerance_by_metric = {
        **{name: (float(settings["moment_absolute_tolerance"]),
                  float(settings["moment_relative_tolerance"]))
           for name in ("C", "w", "Z")},
        **{name: (float(settings["symplectic_absolute_tolerance"]),
                  float(settings["symplectic_relative_tolerance"]))
           for name in ("lambda1", "lambda2", "lambda3")},
        **{name: (float(settings["information_absolute_tolerance_bits"]),
                  float(settings["information_relative_tolerance"]))
           for name in ("chi_BE", "raw_K")},
    }
    def metrics(row: dict[str, object]) -> dict[str, list[float]]:
        if path == "support_restricted_residual":
            return row["support_basis_security"]
        return {
            "C": row["active_full_matrix_C"], "w": row["active_full_matrix_w"],
            **{name: row[name] for name in (
                "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K"
            )},
        }
    reference = metrics(rows[-1])
    comparisons = []
    passes = []
    for row in rows[:-1]:
        candidate = metrics(row)
        errors = {}
        allowances = {}
        metric_passes = []
        for name, (absolute, relative) in tolerance_by_metric.items():
            value = torch.as_tensor(candidate[name], dtype=torch.float64)
            reference_value = torch.as_tensor(reference[name], dtype=torch.float64)
            error = (value - reference_value).abs()
            allowance = absolute + relative * reference_value.abs()
            errors[name] = float(error.max())
            allowances[name] = float(allowance.max())
            metric_passes.append(bool(torch.all(error <= allowance)))
        trace_error = max(abs(float(value)) for value in row["tau_trace_deficit"])
        passed = all(metric_passes) and trace_error <= float(settings["density_trace_tolerance"])
        passes.append(passed)
        comparisons.append({
            "fock_cutoff": row["fock_cutoff"],
            "maximum_absolute_errors": errors,
            "maximum_allowed_errors": allowances,
            "maximum_density_trace_error": trace_error,
            "passes_reference_tolerance": passed,
        })
    selected = None
    for index, row in enumerate(rows[:-1]):
        if all(passes[index:]):
            selected = row["fock_cutoff"]
            break
    return {
        "path": path,
        "reference_fock_cutoff": rows[-1]["fock_cutoff"],
        "selected_fock_cutoff": selected,
        "converged": selected is not None,
        "comparisons": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--mi-evidence", type=Path, default=ROOT / "results" / "mi_convergence.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "near_coincident_fock_diagnostic.json")
    parser.add_argument("--include-preregistered-extension", action="store_true")
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    states, labels, t, epsilon = validation_representative_states(config)
    complete_ensembles = representative_ensembles(config, t, epsilon)
    fixture = complete_ensembles[
        "near_coincident_pseudoinverse_stress"
    ]
    mi_evidence = json.loads(args.mi_evidence.resolve().read_text(encoding="utf-8"))
    replications = mi_evidence["traces"]["near_coincident_pseudoinverse_stress"][
        "replications"
    ]
    selected_mi_count = int(mi_evidence["minimum_common_sample_count"])
    selected_rows = [
        next(
            row for row in replication["rows"]
            if int(row["sample_count"]) == selected_mi_count
        )
        for replication in replications
    ]
    mi = torch.as_tensor(
        [row["mi_bits"] for row in selected_rows], dtype=torch.float64
    ).mean(dim=0)
    active_threshold = float(config["cvqkd"]["holevo_numerics"][
        "density_eigenvalue_pseudoinverse_tolerance"
    ])
    threshold_grid = tuple(float(value) for value in config["numerical_validation"][
        "holevo_threshold_sensitivity"
    ]["density_eigenvalue_pseudoinverse_tolerances"])
    cutoffs = tuple(int(value) for value in config["numerical_validation"]["fock"]["cutoffs"])
    if args.include_preregistered_extension:
        cutoffs = cutoffs + PREREGISTERED_EXTENSION_CUTOFFS
    kwargs = holevo_numerical_kwargs(config)
    started = time.perf_counter()
    rows = []
    for cutoff in cutoffs:
        cutoff_started = time.perf_counter()
        print(f"diagnostic cutoff={cutoff}", flush=True)
        result = holevo_information(
            fixture, t, epsilon, fock_cutoff=cutoff, **kwargs
        )
        spectral_eigenvalues, spectral_eigenvectors = torch.linalg.eigh(result.tau)
        support_c, support_w, spectral = support_restricted_source_moments(
            result.tau,
            # Reconstructing the coherent vectors is deliberately separate
            # from the active Holevo path for this diagnosis.
            coherent_state_vectors(fixture.amplitudes, cutoff),
            fixture.probabilities,
            density_eigenvalue_tolerance=active_threshold,
            eigenvalues=spectral_eigenvalues,
            eigenvectors=spectral_eigenvectors,
        )
        support_z = (
            2.0 * torch.sqrt(t) * support_c
            - torch.sqrt(2.0 * t * epsilon * support_w)
        )
        support_covariance = standard_form_covariance(
            fixture, t, epsilon, support_z,
            require_supported_symmetry=True,
            symmetry_tolerance=float(config["cvqkd"]["holevo_numerics"][
                "symmetry_tolerance"
            ]),
            numerical_tolerance=float(config["cvqkd"]["holevo_numerics"][
                "physicality_tolerance"
            ]),
        )
        s1, s2, s3 = (
            torch.clamp_min(value, 1.0) for value in (
                support_covariance.lambda1,
                support_covariance.lambda2,
                support_covariance.lambda3,
            )
        )
        support_chi = (
            bosonic_entropy((s1 - 1.0) / 2.0)
            + bosonic_entropy((s2 - 1.0) / 2.0)
            - bosonic_entropy((s3 - 1.0) / 2.0)
        )
        threshold_rows = []
        for threshold in threshold_grid:
            _, threshold_w, threshold_spectral = support_restricted_source_moments(
                result.tau,
                coherent_state_vectors(fixture.amplitudes, cutoff),
                fixture.probabilities,
                density_eigenvalue_tolerance=threshold,
                eigenvalues=spectral_eigenvalues,
                eigenvectors=spectral_eigenvectors,
            )
            threshold_rows.append({
                "threshold": threshold,
                "support_size_by_state": [
                    state["support_size"] for state in threshold_spectral
                ],
                "support_basis_w": threshold_w.tolist(),
            })
        row = {
            "fock_cutoff": cutoff,
            "tau_trace": result.tau_trace.tolist(),
            "tau_trace_deficit": (1.0 - result.tau_trace).tolist(),
            "spectral": spectral,
            "active_full_matrix_C": result.coherent_correlation.tolist(),
            "support_basis_C": support_c.tolist(),
            "C_full_minus_support": (result.coherent_correlation - support_c).tolist(),
            "active_full_matrix_w": result.w.tolist(),
            "support_basis_w": support_w.tolist(),
            "w_full_minus_support": (result.w - support_w).tolist(),
            "support_basis_security": {
                "C": support_c.tolist(), "w": support_w.tolist(),
                "Z": support_z.tolist(),
                "lambda1": support_covariance.lambda1.tolist(),
                "lambda2": support_covariance.lambda2.tolist(),
                "lambda3": support_covariance.lambda3.tolist(),
                "chi_BE": support_chi.tolist(),
                "raw_K": (0.95 * mi - support_chi).tolist(),
            },
            "Z": result.z.tolist(),
            "lambda1": result.covariance.lambda1.tolist(),
            "lambda2": result.covariance.lambda2.tolist(),
            "lambda3": result.covariance.lambda3.tolist(),
            "chi_BE": result.chi_be.tolist(),
            "raw_K": (0.95 * mi - result.chi_be).tolist(),
            "threshold_diagnostic_only": threshold_rows,
        }
        row["runtime_seconds"] = time.perf_counter() - cutoff_started
        rows.append(row)
    payload = {
        "schema_version": "near-coincident-fock-diagnostic-v1",
        "status": "DIAGNOSTIC_ONLY_NOT_SELECTION",
        "test_set_used": False,
        "publication_training_performed": False,
        "fixture": "near_coincident_pseudoinverse_stress",
        "state_labels": labels,
        "validation_state_realization_sha256": states.realization_sha256,
        "active_density_eigenvalue_tolerance": active_threshold,
        "mutual_information_sample_count": selected_mi_count,
        "preregistered_extension_cutoffs": list(PREREGISTERED_EXTENSION_CUTOFFS),
        "extension_included": args.include_preregistered_extension,
        "nonselectable_reference_cutoff": cutoffs[-1],
        "runtime_seconds": time.perf_counter() - started,
        "provenance": provenance(args.config.resolve(), config, complete_ensembles),
        "rows": rows,
        "stable_suffix_results": {
            path: _stable_suffix_against_last_reference(rows, config, path=path)
            for path in ("active_full_matrix", "support_restricted_residual")
        },
        "interpretation_rule": {
            "truncation": "tau trace deficit or cutoff trend common to both algebraically equivalent paths",
            "threshold_inverse": "support-size or w change across the frozen diagnostic threshold grid",
            "matrix_cancellation": "active full-matrix minus support-basis value at identical cutoff and threshold"
        },
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
