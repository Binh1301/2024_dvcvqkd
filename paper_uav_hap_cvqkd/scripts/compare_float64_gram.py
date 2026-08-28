"""Compare exact float64 C4-Gram moments with dense Fock and HP diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import torch

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _numerical_validation import (
    representative_ensembles, unique_ensemble_roster, validation_representative_states,
)
from src.cvqkd.covariance import standard_form_covariance
from src.cvqkd.gram_moments import c4_gram_source_moments
from src.cvqkd.holevo import bosonic_entropy, holevo_information


THRESHOLDS = (1e-14, 1e-13, 1e-12)
MOMENT_ABSOLUTE_TOLERANCE = 1e-7
MOMENT_RELATIVE_TOLERANCE = 1e-6
INFORMATION_ABSOLUTE_TOLERANCE = 1e-6
INFORMATION_RELATIVE_TOLERANCE = 1e-5


def _security(ensemble, t, epsilon, correlation):
    covariance = standard_form_covariance(
        ensemble, t, epsilon, correlation,
        symmetry_tolerance=1e-8, numerical_tolerance=1e-10,
    )
    l1, l2, l3 = (
        torch.clamp_min(value, 1.0) for value in (
            covariance.lambda1, covariance.lambda2, covariance.lambda3
        )
    )
    chi = (
        bosonic_entropy((l1 - 1.0) / 2.0)
        + bosonic_entropy((l2 - 1.0) / 2.0)
        - bosonic_entropy((l3 - 1.0) / 2.0)
    )
    return covariance, chi


def _frozen_bound(metric: str, reference: float) -> float:
    if metric in {"chi_BE", "raw_K"}:
        return INFORMATION_ABSOLUTE_TOLERANCE + INFORMATION_RELATIVE_TOLERANCE * abs(reference)
    return MOMENT_ABSOLUTE_TOLERANCE + MOMENT_RELATIVE_TOLERANCE * abs(reference)


def _maximum_errors(candidate: dict, reference: dict) -> dict:
    return {
        metric: max(abs(float(left) - float(right)) for left, right in zip(
            candidate[metric], reference[metric]
        ))
        for metric in ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
    }


def _conservative_bounds(reference: dict) -> dict:
    return {
        metric: min(_frozen_bound(metric, float(value)) for value in reference[metric])
        for metric in ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--hp-oracle", type=Path, default=ROOT / "results" / "near_coincident_gram_oracle.json")
    parser.add_argument(
        "--dense-diagnostic", type=Path,
        default=ROOT / "results" / "near_coincident_fock_diagnostic.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "float64_gram_comparison.json")
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    _, labels, t, epsilon = validation_representative_states(config)
    complete = representative_ensembles(config, t, epsilon)
    ensembles, aliases = unique_ensemble_roster(complete)
    hp = json.loads(args.hp_oracle.resolve().read_text(encoding="utf-8"))
    dense_diagnostic = json.loads(
        args.dense_diagnostic.resolve().read_text(encoding="utf-8")
    )
    dense_diagnostic_128 = next(
        row for row in dense_diagnostic["rows"] if row["fock_cutoff"] == 128
    )
    hp160 = next(row for row in hp["precision_rows"] if row["decimal_digits"] == 160)
    hp_full = hp["selected_full_support_oracle"]
    hp_by_threshold = {
        float(row["threshold"]): row
        for row in hp160["threshold_sensitivity_diagnostic_only"]
    }
    stress_mi = torch.tensor(
        hp["states"]["mutual_information_bits"], dtype=torch.float64
    )
    beta_reconciliation = float(config["cvqkd"]["beta_reconciliation"])
    reconciled_stress_mi = beta_reconciliation * stress_mi
    started = time.perf_counter()
    rows = []
    holevo_kwargs = holevo_numerical_kwargs(config)
    for fixture_name, ensemble in ensembles.items():
        print(f"float64 Gram fixture={fixture_name}", flush=True)
        for threshold in THRESHOLDS:
            gram = c4_gram_source_moments(
                ensemble, density_eigenvalue_tolerance=threshold
            )
            gram_z = (
                2.0 * torch.sqrt(t) * gram.coherent_correlation
                - torch.sqrt(2.0 * t * epsilon * gram.w)
            )
            gram_covariance, gram_chi = _security(ensemble, t, epsilon, gram_z)
            dense = holevo_information(
                ensemble, t, epsilon, fock_cutoff=128,
                density_eigenvalue_tolerance=threshold,
                **{key: value for key, value in holevo_kwargs.items()
                   if key != "density_eigenvalue_tolerance"},
            )
            metric_pairs = {
                "C": (gram.coherent_correlation, dense.coherent_correlation),
                "w": (gram.w, dense.w), "Z": (gram_z, dense.z),
                "lambda1": (gram_covariance.lambda1, dense.covariance.lambda1),
                "lambda2": (gram_covariance.lambda2, dense.covariance.lambda2),
                "lambda3": (gram_covariance.lambda3, dense.covariance.lambda3),
                "chi_BE": (gram_chi, dense.chi_be),
            }
            row = {
                "fixture": fixture_name, "threshold": threshold,
                "gram_diagnostics": gram.diagnostics,
                "gram": {
                    "C": gram.coherent_correlation.tolist(), "w": gram.w.tolist(),
                    "Z": gram_z.tolist(),
                    "lambda1": gram_covariance.lambda1.tolist(),
                    "lambda2": gram_covariance.lambda2.tolist(),
                    "lambda3": gram_covariance.lambda3.tolist(),
                    "chi_BE": gram_chi.tolist(),
                },
                "dense_fock_cutoff_128": {
                    "C": dense.coherent_correlation.tolist(), "w": dense.w.tolist(),
                    "Z": dense.z.tolist(),
                    "lambda1": dense.covariance.lambda1.tolist(),
                    "lambda2": dense.covariance.lambda2.tolist(),
                    "lambda3": dense.covariance.lambda3.tolist(),
                    "chi_BE": dense.chi_be.tolist(),
                },
                "maximum_absolute_gram_minus_dense": {
                    name: float((left - right).abs().max())
                    for name, (left, right) in metric_pairs.items()
                },
            }
            if fixture_name == "near_coincident_pseudoinverse_stress":
                gram_raw_k = reconciled_stress_mi - gram_chi
                dense_raw_k = reconciled_stress_mi - dense.chi_be
                row["gram"]["raw_K"] = gram_raw_k.tolist()
                row["dense_fock_cutoff_128"]["raw_K"] = dense_raw_k.tolist()
                row["maximum_absolute_gram_minus_dense"]["raw_K"] = float(
                    (gram_raw_k - dense_raw_k).abs().max()
                )
                hp_row = hp_by_threshold[threshold]
                hp_c = float(hp_row["C"])
                hp_w = float(hp_row["w"])
                row["high_precision_160_digit_reference"] = {
                    "C": hp_row["C"], "w": hp_row["w"],
                    "support_size": hp_row["support_size"],
                    "maximum_absolute_gram_minus_hp": {
                        "C": float((gram.coherent_correlation - hp_c).abs().max()),
                        "w": float((gram.w - hp_w).abs().max()),
                    },
                }
                gram_minus_hp_full = {
                    "C": float((gram.coherent_correlation - float(hp_full["C"])).abs().max()),
                    "w": float((gram.w - float(hp_full["w"])).abs().max()),
                    "Z": max(abs(float(value) - float(reference["Z"]))
                             for value, reference in zip(gram_z, hp_full["states"])),
                    "lambda1": max(abs(float(value) - float(reference["lambda1"]))
                                   for value, reference in zip(
                                       gram_covariance.lambda1, hp_full["states"]
                                   )),
                    "lambda2": max(abs(float(value) - float(reference["lambda2"]))
                                   for value, reference in zip(
                                       gram_covariance.lambda2, hp_full["states"]
                                   )),
                    "lambda3": max(abs(float(value) - float(reference["lambda3"]))
                                   for value, reference in zip(
                                       gram_covariance.lambda3, hp_full["states"]
                                   )),
                    "chi_BE": max(abs(float(value) - float(reference["chi_BE"]))
                                  for value, reference in zip(
                                      gram_chi, hp_full["states"]
                                  )),
                    "raw_K": max(abs(float(value) - float(reference["raw_K"]))
                                 for value, reference in zip(
                                     gram_raw_k, hp_full["states"]
                                 )),
                }
                hp_full_bounds = {
                    metric: min(
                        _frozen_bound(
                            metric,
                            float(hp_full["C"] if metric == "C" else
                                  hp_full["w"] if metric == "w" else
                                  reference[metric]),
                        )
                        for reference in hp_full["states"]
                    )
                    for metric in gram_minus_hp_full
                }
                row["high_precision_full_support_1250_digit_reference"] = {
                    "C": hp_full["C"], "w": hp_full["w"],
                    "support_size": hp_full["support_size"],
                    "maximum_absolute_gram_minus_hp": gram_minus_hp_full,
                    "conservative_minimum_allowed_error": hp_full_bounds,
                    "passes_all_frozen_tolerances": all(
                        gram_minus_hp_full[metric] <= hp_full_bounds[metric]
                        for metric in gram_minus_hp_full
                    ),
                }
            rows.append(row)

    stress_rows = {
        float(row["threshold"]): row for row in rows
        if row["fixture"] == "near_coincident_pseudoinverse_stress"
    }
    hp_full_values = {
        "C": [hp_full["C"]] * len(labels),
        "w": [hp_full["w"]] * len(labels),
        **{
            metric: [state[metric] for state in hp_full["states"]]
            for metric in ("Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
        },
    }
    active_gram = stress_rows[1e-12]["gram"]
    active_dense = stress_rows[1e-12]["dense_fock_cutoff_128"]
    active_support = {
        metric: dense_diagnostic_128["support_basis_security"][metric]
        for metric in ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
    }
    three_formulations = {}
    for name, values in (
        ("complex128_c4_gram", active_gram),
        ("dense_fock_full_matrix_cutoff_128", active_dense),
        ("dense_fock_support_restricted_residual_cutoff_128", active_support),
    ):
        errors = _maximum_errors(values, hp_full_values)
        bounds = _conservative_bounds(hp_full_values)
        three_formulations[name] = {
            "values": values,
            "maximum_absolute_error_to_hp_full_support": errors,
            "conservative_minimum_allowed_error": bounds,
            "passes_all_frozen_tolerances": all(
                errors[metric] <= bounds[metric] for metric in errors
            ),
        }

    well_conditioned_rows = [
        row for row in rows
        if row["fixture"] != "near_coincident_pseudoinverse_stress"
    ]
    well_conditioned_summary = {}
    for threshold in THRESHOLDS:
        threshold_rows = [
            row for row in well_conditioned_rows if row["threshold"] == threshold
        ]
        worst_errors = {
            metric: max(
                row["maximum_absolute_gram_minus_dense"][metric]
                for row in threshold_rows
            )
            for metric in ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE")
        }
        worst_allowed = {
            metric: min(
                min(
                    _frozen_bound(metric, float(value))
                    for value in row["dense_fock_cutoff_128"][metric]
                )
                for row in threshold_rows
            )
            for metric in worst_errors
        }
        well_conditioned_summary[str(threshold)] = {
            "maximum_absolute_gram_minus_dense": worst_errors,
            "conservative_minimum_allowed_error": worst_allowed,
            "passes_all_frozen_tolerances": all(
                worst_errors[metric] <= worst_allowed[metric]
                for metric in worst_errors
            ),
        }

    stress_1e14 = stress_rows[1e-14]
    stress_1e13 = stress_rows[1e-13]
    plateau_metrics = ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
    plateau_deltas = {
        metric: max(abs(float(left) - float(right)) for left, right in zip(
            stress_1e14["gram"][metric], stress_1e13["gram"][metric]
        ))
        for metric in plateau_metrics
    }
    payload = {
        "schema_version": "float64-c4-gram-comparison-v1",
        "status": "DIAGNOSTIC_ONLY_NO_ACTIVE_RULE_CHANGE",
        "test_set_used": False, "publication_training_performed": False,
        "precision": "torch.float64/complex128",
        "thresholds": list(THRESHOLDS),
        "active_threshold": 1e-12,
        "prospective_thresholds_not_frozen": [1e-14, 1e-13],
        "state_labels": labels, "fixture_count": len(ensembles),
        "exact_duplicate_aliases": aliases,
        "frozen_tolerances": {
            "moment_and_symplectic": {
                "absolute": MOMENT_ABSOLUTE_TOLERANCE,
                "relative": MOMENT_RELATIVE_TOLERANCE,
            },
            "information_bits": {
                "absolute": INFORMATION_ABSOLUTE_TOLERANCE,
                "relative": INFORMATION_RELATIVE_TOLERANCE,
            },
        },
        "well_conditioned_roster_excluding_declared_stress": {
            "fixture_count": len(ensembles) - 1,
            "exclusion": (
                "The declared near-coincident stress fixture has analytic rank 256, "
                "smallest eigenvalue about 1.72e-1099, and cannot be a float64 dense-Fock reference."
            ),
            "by_threshold": well_conditioned_summary,
        },
        "stress_threshold_plateau_1e_minus_14_vs_1e_minus_13": {
            "support_sizes": [
                stress_1e14["gram_diagnostics"][0]["support_size"],
                stress_1e13["gram_diagnostics"][0]["support_size"],
            ],
            "maximum_absolute_differences": plateau_deltas,
            "identical_support_and_passes_frozen_tolerances": (
                stress_1e14["gram_diagnostics"][0]["support_size"]
                == stress_1e13["gram_diagnostics"][0]["support_size"]
                and all(
                    plateau_deltas[metric]
                    <= _frozen_bound(
                        metric, max(abs(float(value)) for value in stress_1e13["gram"][metric])
                    )
                    for metric in plateau_metrics
                )
            ),
        },
        "stress_active_threshold_three_float64_formulations": {
            "threshold": 1e-12,
            "mutual_information_sample_count": hp["mutual_information_sample_count_for_raw_K"],
            "reconciled_mutual_information_bits": reconciled_stress_mi.tolist(),
            "high_precision_full_support_reference": hp_full_values,
            "formulations": three_formulations,
            "conditioning": {
                "analytic_physical_rank": 256,
                "smallest_physical_eigenvalue": hp["precision_rows"][-1]["minimum_resolved_positive_eigenvalue"],
                "active_dense_support_size": dense_diagnostic_128["spectral"][0]["support_size"],
                "active_dense_minimum_retained_eigenvalue": dense_diagnostic_128["spectral"][0]["minimum_retained_density_eigenvalue"],
                "active_dense_retained_condition_number": dense_diagnostic_128["spectral"][0]["retained_density_condition_number"],
                "full_physical_spectral_condition_number": hp["precision_rows"][-1]["resolved_spectral_condition_number"],
                "complex128_1e_minus_13_support_size": stress_1e13["gram_diagnostics"][0]["support_size"],
                "complex128_1e_minus_13_minimum_retained_eigenvalue": stress_1e13["gram_diagnostics"][0]["minimum_retained_eigenvalue"],
                "complex128_1e_minus_13_retained_condition_number": stress_1e13["gram_diagnostics"][0]["retained_condition_number"],
            },
        },
        "runtime_seconds": time.perf_counter() - started,
        "rows": rows,
        "provenance": {
            "config_sha256": hashlib.sha256(args.config.resolve().read_bytes()).hexdigest(),
            "hp_oracle_sha256": hashlib.sha256(args.hp_oracle.resolve().read_bytes()).hexdigest(),
            "dense_diagnostic_sha256": hashlib.sha256(
                args.dense_diagnostic.resolve().read_bytes()
            ).hexdigest(),
            "comparison_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "gram_module_sha256": hashlib.sha256(
                (ROOT / "src" / "cvqkd" / "gram_moments.py").read_bytes()
            ).hexdigest(),
        },
    }
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
