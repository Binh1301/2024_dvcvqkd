"""Shared, read-only construction for bounded numerical validation scripts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from _common import missing_required
from _train import _channel
from src.modulation.joint_ps_gs import (
    Ensemble, JointTransmitter, enforce_peak_photon_constraint, reference_ensemble,
)
from src.modulation.qam256 import expand_c4_orbit_masses, expand_c4_orbit_values
from src.validation.physical_domain import (
    approved_peak_photon_limit, preconvergence_domain_report,
    peak_feasible_reference_va_grid, square_reference_papr,
    require_preconvergence_domain_ready,
)
from src.validation.convergence import select_representative_state_indices
from src.utils.random import derive_seed


COMMON_REQUIRED = [
    "channel.h_hap_m", "channel.h_uav_m", "channel.wavelength_m",
    "channel.visibility_km", "channel.beam_waist_m", "channel.aperture_radius_m",
    "channel.cn2_m_minus_two_thirds", "channel.excess_noise_distribution.kind",
    "channel.uav_motion.sigma_x_m", "channel.uav_motion.sigma_y_m",
    "channel.uav_motion.sigma_z_m", "channel.uav_motion.sigma_theta_rad",
    "channel.uav_motion.sigma_phi_rad", "channel.uav_motion.sigma_psi_rad",
    "channel.excess_noise_distribution.minimum_snu",
    "channel.excess_noise_distribution.maximum_snu", "cvqkd.v_min_snu",
    "cvqkd.v_max_snu", "cvqkd.v_a_budget_snu", "cvqkd.mb_nu",
    "cvqkd.n_peak_photons", "cvqkd.peak_domain_scope",
    "cvqkd.holevo_numerics.symmetry_tolerance",
    "cvqkd.holevo_numerics.density_trace_tolerance",
    "cvqkd.holevo_numerics.density_eigenvalue_pseudoinverse_tolerance",
    "cvqkd.holevo_numerics.physicality_tolerance",
    "training.validation_fading_samples", "training.seeds.validation_channel",
]


def require(config: dict[str, Any], extra: list[str]) -> None:
    missing = missing_required(config, COMMON_REQUIRED + extra)
    if missing:
        raise ValueError("Unresolved required configuration: " + ", ".join(missing))


def validation_representative_states(config: dict[str, Any]):
    training = config["training"]
    states = _channel(
        config,
        int(training["validation_fading_samples"]),
        derive_seed(int(training["seeds"]["validation_channel"]), "validation_channel"),
    )
    indices = select_representative_state_indices(
        states.transmittance, states.excess_noise_snu
    )
    order = (indices["bad"], indices["medium"], indices["good"])
    t = torch.as_tensor(states.transmittance[list(order)], dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu[list(order)], dtype=torch.float64)
    labels = ["bad", "medium", "good"]
    return states, labels, t, epsilon


def full_validation_states(config: dict[str, Any]):
    """Regenerate the complete preregistered validation realization."""

    training = config["training"]
    states = _channel(
        config,
        int(training["validation_fading_samples"]),
        derive_seed(int(training["seeds"]["validation_channel"]), "validation_channel"),
    )
    t = torch.as_tensor(states.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu, dtype=torch.float64)
    return states, t, epsilon


def representative_ensembles(
    config: dict[str, Any], t: torch.Tensor, epsilon: torch.Tensor
) -> dict[str, Ensemble]:
    """Finite representative set; not global learned-GS/PS coverage."""

    require_preconvergence_domain_ready(config)
    cvqkd = config["cvqkd"]
    n_peak = approved_peak_photon_limit(config)
    v_min = float(cvqkd["v_min_snu"])
    v_max = float(cvqkd["v_max_snu"])
    va_budget = float(cvqkd["v_a_budget_snu"])
    if va_budget < v_min:
        raise ValueError("V_A budget is infeasible because it is below V_min.")
    batch_size = int(t.numel())
    va_grid = tuple(float(value) for value in config["baseline_search"]["va_grid_snu"])

    def peak_feasible_extremes(
        kind: str, nu: float | None = None
    ) -> tuple[tuple[float, Ensemble], tuple[float, Ensemble]]:
        feasible_va = peak_feasible_reference_va_grid(
            kind, va_grid, n_peak_photons=n_peak, nu_mb=nu
        )
        if not feasible_va:
            raise ValueError(f"No peak-feasible preregistered V_A candidate for {kind}, nu={nu}.")
        def build(va: float) -> Ensemble:
            return reference_ensemble(
                kind, batch_size=batch_size, modulation_variance=va,
                nu_mb=nu, v_min=v_min, v_max=v_max,
                n_peak_photons=n_peak,
            )
        return (feasible_va[0], build(feasible_va[0])), (
            feasible_va[-1], build(feasible_va[-1])
        )

    result: dict[str, Ensemble] = {}
    for label, kind, nu in (
        ("uniform", "uniform", None),
        ("binomial", "binomial", None),
        ("fixed_mb", "mb", float(cvqkd["mb_nu"])),
    ):
        low, high = peak_feasible_extremes(kind, nu)
        result[f"{label}_low_va_{low[0]:g}"] = low[1]
        result[f"{label}_high_va_{high[0]:g}"] = high[1]

    # The optimized-MB roster is fixed algebraically before SKR/MI/Holevo
    # outcomes: nu-domain extrema plus the grid member with maximum PAPR.
    nu_grid = tuple(float(value) for value in config["baseline_search"][
        "optimized_mb_nu_grid"
    ])
    worst_nu = max(nu_grid, key=lambda value: square_reference_papr("mb", nu_mb=value))
    optimized_nus = tuple(dict.fromkeys((nu_grid[0], nu_grid[-1], worst_nu)))
    for nu in optimized_nus:
        low, high = peak_feasible_extremes("mb", nu)
        result[f"optimized_mb_nu_{nu:g}_low_va_{low[0]:g}"] = low[1]
        result[f"optimized_mb_nu_{nu:g}_high_va_{high[0]:g}"] = high[1]
    # The deterministic initialization and boundary are finite diagnostics;
    # neither certifies unenumerated learned outputs.
    learned = JointTransmitter("full", v_min=v_min, v_max=v_max,
                               n_peak_photons=n_peak)
    with torch.no_grad():
        result["untrained_full_initialization"] = learned(t, epsilon)
    # A deliberately synthetic, C4-symmetric boundary case probes the largest
    # coherent amplitude admitted by the common hard domain. It is a numerical
    # convergence fixture, not a transmitter baseline or performance result.
    photon_mean = v_min / 2.0
    if n_peak < photon_mean * (1.0 - 1e-12):
        raise ValueError("n_peak is incompatible with the mandatory V_min average energy.")
    if abs(n_peak - photon_mean) <= 1e-12 * max(1.0, n_peak):
        boundary_orbit_masses = torch.full((64,), 1.0 / 64.0, dtype=torch.float64)
        boundary_prototypes = torch.full((64,), n_peak ** 0.5, dtype=torch.complex128)
    else:
        secondary_energy = photon_mean / 2.0
        rare_mass = (photon_mean - secondary_energy) / (n_peak - secondary_energy)
        if not 0.0 < rare_mass < 1.0:
            raise ValueError("Unable to construct the preregistered peak-boundary fixture.")
        boundary_orbit_masses = torch.full(
            (64,), (1.0 - rare_mass) / 63.0, dtype=torch.float64
        )
        boundary_orbit_masses[0] = rare_mass
        boundary_prototypes = torch.full(
            (64,), secondary_energy ** 0.5, dtype=torch.complex128
        )
        boundary_prototypes[0] = n_peak ** 0.5
    boundary_probabilities = expand_c4_orbit_masses(boundary_orbit_masses)
    boundary_amplitudes = expand_c4_orbit_values(boundary_prototypes)
    boundary = Ensemble(
        boundary_probabilities.unsqueeze(0).expand(batch_size, -1),
        boundary_amplitudes.unsqueeze(0).expand(batch_size, -1),
        torch.full((batch_size,), v_min, dtype=torch.float64),
        boundary_amplitudes,
        exact_csi_oracle=True,
        c4_symmetric=True,
    )
    boundary.validate()
    enforce_peak_photon_constraint(boundary, n_peak)
    result["hard_peak_boundary_at_vmin"] = boundary
    return result


def ensemble_sha256(ensemble: Ensemble) -> str:
    digest = hashlib.sha256()
    for tensor in (
        ensemble.probabilities, ensemble.amplitudes.real, ensemble.amplitudes.imag,
        ensemble.declared_va, ensemble.relative_constellation.real,
        ensemble.relative_constellation.imag,
    ):
        value = tensor.detach().cpu().contiguous()
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def provenance(
    config_path: Path, config: dict[str, Any], ensembles: dict[str, Ensemble]
) -> dict[str, Any]:
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    domain = preconvergence_domain_report(config)
    if domain["status"] != "READY_FOR_CONVERGENCE_EXECUTION":
        raise ValueError("Physical amplitude domain is unresolved: " + "; ".join(domain["blockers"]))
    return {
        "config_path": str(config_path),
        "resolved_config_sha256": hashlib.sha256(encoded).hexdigest(),
        "precision": "torch.float64 / torch.complex128 on CPU",
        "test_set_used": False,
        "coverage_complete_over_learned_parameter_space": False,
        "coverage_scope": "finite_preregistered_fixture_suite_only",
        "physical_domain_rule": domain["physical_rule"],
        "n_peak_photons": domain["n_peak_photons"],
        "peak_domain_scope": domain["peak_domain_scope"],
        "boundary_fixture_included": "hard_peak_boundary_at_vmin",
        "publication_convergence_certification": False,
        "enumerated_fixture_sha256": {
            name: ensemble_sha256(ensemble) for name, ensemble in ensembles.items()
        },
        "coverage_limitation": (
            "Finite representative and boundary fixtures cannot certify the continuous learned "
            "parameter space or any selected checkpoint not explicitly enumerated and hash-bound."
        ),
    }
