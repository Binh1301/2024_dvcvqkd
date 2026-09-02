"""Hash-bound validation-only numerical pre-certification of every MB grid candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import torch

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _numerical_validation import (
    ensemble_sha256, provenance, representative_ensembles,
    validation_representative_states,
)
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import PeakPhotonConstraintViolation, reference_ensemble
from src.utils.random import derive_seed, torch_generator
from src.validation.convergence import (
    ConvergenceTolerance, fock_convergence_trace, holevo_threshold_sensitivity_trace,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results" / "mb_grid_numerical_precertification.json")
    args = parser.parse_args()
    path = args.config.resolve()
    config = load_yaml(path)
    states, labels, t, epsilon = validation_representative_states(config)
    cvqkd = config["cvqkd"]
    mi_settings = config["numerical_validation"]["mi"]
    selected_count = int(config["training"]["validation_awgn_samples_per_symbol"])
    if selected_count != 2048 or 1024 not in mi_settings["sample_counts"]:
        raise ValueError("MB pre-certification is frozen to the selected 1024->2048 refinement.")
    mi_tolerance = ConvergenceTolerance(
        float(mi_settings["absolute_tolerance_bits"]),
        float(mi_settings["relative_tolerance"]),
    )
    fock_settings = config["numerical_validation"]["fock"]
    moment_tolerance = ConvergenceTolerance(
        float(fock_settings["moment_absolute_tolerance"]),
        float(fock_settings["moment_relative_tolerance"]),
    )
    symplectic_tolerance = ConvergenceTolerance(
        float(fock_settings["symplectic_absolute_tolerance"]),
        float(fock_settings["symplectic_relative_tolerance"]),
    )
    information_tolerance = ConvergenceTolerance(
        float(fock_settings["information_absolute_tolerance_bits"]),
        float(fock_settings["information_relative_tolerance"]),
    )
    threshold_settings = config["numerical_validation"]["holevo_threshold_sensitivity"]
    threshold_tolerance = ConvergenceTolerance(
        float(threshold_settings["absolute_tolerance"]),
        float(threshold_settings["relative_tolerance"]),
    )
    nu_grid = tuple(float(value) for value in config["baseline_search"]["optimized_mb_nu_grid"])
    va_grid = tuple(float(value) for value in config["baseline_search"]["va_grid_snu"])
    seed = derive_seed(
        int(mi_settings["seeds"][0]), "mb_full_grid_numerical_precertification"
    )
    noise = standard_complex_noise(
        (3, 256, selected_count), generator=torch_generator(seed, t.device), device=t.device
    )
    rows = []
    started = time.perf_counter()
    holevo_kwargs = holevo_numerical_kwargs(config)
    selected_cutoff = int(cvqkd["fock_cutoff"])
    for nu_index, nu in enumerate(nu_grid):
        print(f"MB pre-cert nu={nu:g} ({nu_index + 1}/{len(nu_grid)})", flush=True)
        for va in va_grid:
            try:
                ensemble = reference_ensemble(
                    "mb", batch_size=3, modulation_variance=va, nu_mb=nu,
                    v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
                    n_peak_photons=float(cvqkd["n_peak_photons"]),
                )
            except PeakPhotonConstraintViolation as error:
                rows.append({"nu_mb": nu, "va_snu": va, "physical_admissible": False,
                             "error": str(error)})
                continue
            first = discrete_mutual_information(
                ensemble, t, epsilon, noise_samples_per_symbol=1024,
                standard_noise_samples=noise[..., :1024], noise_sample_chunk_size=64,
                implementation="product",
            ).detach()
            second = discrete_mutual_information(
                ensemble, t, epsilon, noise_samples_per_symbol=1024,
                standard_noise_samples=noise[..., 1024:2048], noise_sample_chunk_size=64,
                implementation="product",
            ).detach()
            current = 0.5 * (first + second)
            mi_error = (current - first).abs()
            mi_bound = mi_tolerance.bound(current)
            fock = fock_convergence_trace(
                ensemble, t, epsilon, cutoffs=(selected_cutoff, 128),
                tolerance=moment_tolerance, symplectic_tolerance=symplectic_tolerance,
                information_tolerance=information_tolerance,
                mutual_information_bits=current,
                beta_reconciliation=float(cvqkd["beta_reconciliation"]),
                density_trace_tolerance=float(fock_settings["density_trace_tolerance"]),
                **{key: value for key, value in holevo_kwargs.items()
                   if key != "density_trace_tolerance"},
            )
            threshold = holevo_threshold_sensitivity_trace(
                ensemble, t, epsilon, fock_cutoff=selected_cutoff,
                density_eigenvalue_tolerances=threshold_settings[
                    "density_eigenvalue_pseudoinverse_tolerances"
                ],
                selected_tolerance=holevo_kwargs["density_eigenvalue_tolerance"],
                tolerance=threshold_tolerance,
                symmetry_tolerance=holevo_kwargs["symmetry_tolerance"],
                density_trace_tolerance=holevo_kwargs["density_trace_tolerance"],
                physicality_tolerance=holevo_kwargs["physicality_tolerance"],
                mutual_information_bits=current,
                beta_reconciliation=float(cvqkd["beta_reconciliation"]),
            )
            rows.append({
                "nu_mb": nu, "va_snu": va, "physical_admissible": True,
                "ensemble_sha256": ensemble_sha256(ensemble),
                "maximum_peak_photons": float(ensemble.amplitudes.abs().square().max()),
                "mi_1024_to_2048_maximum_difference_bits": float(mi_error.max()),
                "mi_maximum_allowed_difference_bits": float(mi_bound.max()),
                "mi_refinement_passes": bool(torch.all(mi_error <= mi_bound)),
                "fock_72_vs_128_passes": fock["selected_fock_cutoff"] == selected_cutoff,
                "threshold_selected_passes": threshold["selected_threshold_passes"],
                "threshold_plateau_passes": threshold[
                    "stable_three_point_plateau_around_selected_threshold"
                ],
            })
    all_pass = len(rows) == len(nu_grid) * len(va_grid) and all(
        row.get("physical_admissible") is True
        and row.get("mi_refinement_passes") is True
        and row.get("fock_72_vs_128_passes") is True
        and row.get("threshold_selected_passes") is True
        and row.get("threshold_plateau_passes") is True
        for row in rows
    )
    roster = [{"nu_mb": row["nu_mb"], "va_snu": row["va_snu"],
               "ensemble_sha256": row.get("ensemble_sha256")} for row in rows]
    roster_sha = hashlib.sha256(json.dumps(
        roster, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    reference_fixtures = representative_ensembles(config, t, epsilon)
    payload = {
        "schema_version": "mb-grid-numerical-precertification-v1",
        "status": "PASS" if all_pass else "FAIL",
        "is_baseline_selection": False, "test_set_used": False,
        "publication_training_performed": False,
        "scope": "all 31 nu x 15 VA candidates on representative validation states",
        "state_labels": labels,
        "validation_state_realization_sha256": states.realization_sha256,
        "candidate_count": len(rows), "nu_count": len(nu_grid), "va_count": len(va_grid),
        "selected_mi_sample_count": selected_count,
        "selected_fock_cutoff": selected_cutoff,
        "selected_pseudoinverse_threshold": holevo_kwargs["density_eigenvalue_tolerance"],
        "crn_seed": seed, "candidate_roster_sha256": roster_sha,
        "runtime_seconds": time.perf_counter() - started,
        "rows": rows,
        "provenance": provenance(path, config, reference_fixtures),
        "limitation": (
            "This is a finite representative-state numerical pre-certification, not "
            "baseline ranking and not a substitute for exact selected-roster replay."
        ),
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.resolve()} status={payload['status']}")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
