"""Shared, read-only construction for bounded numerical validation scripts."""

from __future__ import annotations

import hashlib
import json
import math
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
    fixture_seed = int(config["numerical_validation"]["fixture_initialization_seed"])
    # Construct the diagnostic initialization reproducibly without perturbing
    # caller/global RNG state. It is a fixed numerical fixture, not training.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(fixture_seed)
        learned = JointTransmitter("full", v_min=v_min, v_max=v_max,
                                   n_peak_photons=n_peak)
    with torch.no_grad():
        result["untrained_full_initialization"] = learned(t, epsilon)

    def deterministically_deform(model: JointTransmitter, *, ps: bool, gs: bool,
                                 va: bool) -> None:
        with torch.no_grad():
            if ps:
                final = model.ps_network.network[-1]
                rows = torch.linspace(-1.0, 1.0, 64, dtype=torch.float64)
                columns = torch.linspace(-1.0, 1.0, 128, dtype=torch.float64)
                final.weight.copy_(0.015 * torch.outer(rows, columns))
                final.bias.add_(0.12 * torch.cos(torch.arange(64, dtype=torch.float64)))
            if gs:
                prototypes = model.gs_model.raw_prototypes()
                index = torch.arange(64, dtype=torch.float64)
                scale = 0.8 + 0.4 * (index / 63.0)
                phase = 0.08 * torch.sin(index)
                deformed = prototypes * scale * torch.exp(1j * phase)
                model.gs_model.raw_coordinates.copy_(torch.view_as_real(deformed))
            if va:
                final = model.va_network.network[-1]
                final.weight.copy_(torch.linspace(
                    -0.08, 0.08, 64, dtype=torch.float64
                ).unsqueeze(0))
                final.bias.fill_(-0.2)

    # Outcome-independent learned-family fixtures. These are deterministic
    # parameter vectors, never optimized checkpoints.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(fixture_seed + 1)
        ps_fixture = JointTransmitter(
            "ps", fixed_va=va_budget, v_min=v_min, v_max=v_max,
            n_peak_photons=n_peak,
        )
        deterministically_deform(ps_fixture, ps=True, gs=False, va=False)
        torch.manual_seed(fixture_seed + 2)
        gs_fixture = JointTransmitter(
            "gs", fixed_va=va_budget, v_min=v_min, v_max=v_max,
            n_peak_photons=n_peak,
        )
        deterministically_deform(gs_fixture, ps=False, gs=True, va=False)
        torch.manual_seed(fixture_seed + 3)
        va_fixture = JointTransmitter(
            "va", v_min=v_min, v_max=v_max, n_peak_photons=n_peak,
        )
        deterministically_deform(va_fixture, ps=False, gs=False, va=True)
        torch.manual_seed(fixture_seed + 4)
        full_fixture = JointTransmitter(
            "full", v_min=v_min, v_max=v_max, n_peak_photons=n_peak,
        )
        deterministically_deform(full_fixture, ps=True, gs=True, va=True)
    with torch.no_grad():
        result["deterministic_ps_only"] = ps_fixture(t, epsilon)
        result["deterministic_gs_only"] = gs_fixture(t, epsilon)
        result["deterministic_va_only"] = va_fixture(t, epsilon)
        result["deterministic_deformed_full"] = full_fixture(t, epsilon)

    # Near-coincident C4 prototypes stress the low-rank density-operator
    # pseudoinverse without violating any physical invariant.
    stress_orbit_masses = torch.full((64,), 1.0 / 64.0, dtype=torch.float64)
    stress_index = torch.arange(64, dtype=torch.float64)
    stress_prototypes = math.sqrt(v_max / 2.0) * torch.exp(1j * 1e-7 * stress_index)
    stress_probabilities = expand_c4_orbit_masses(stress_orbit_masses)
    stress_amplitudes = expand_c4_orbit_values(stress_prototypes)
    stress = Ensemble(
        stress_probabilities.unsqueeze(0).expand(batch_size, -1),
        stress_amplitudes.unsqueeze(0).expand(batch_size, -1),
        torch.full((batch_size,), v_max, dtype=torch.float64), stress_amplitudes,
        exact_csi_oracle=True, c4_symmetric=True,
    )
    stress.validate()
    enforce_peak_photon_constraint(stress, n_peak)
    result["near_coincident_pseudoinverse_stress"] = stress
    # Deliberately synthetic C4 boundary cases probe the largest coherent
    # amplitude at both V_A box endpoints. They are convergence fixtures, not
    # transmitter baselines or performance results.
    def build_peak_boundary(declared_va: float, secondary_energy: float) -> Ensemble:
        photon_mean = declared_va / 2.0
        if not 0.0 <= secondary_energy < photon_mean <= n_peak:
            raise ValueError("Invalid peak-boundary mean/secondary energy.")
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
            torch.full((batch_size,), declared_va, dtype=torch.float64),
            boundary_amplitudes,
            exact_csi_oracle=True,
            c4_symmetric=True,
        )
        boundary.validate()
        enforce_peak_photon_constraint(boundary, n_peak)
        return boundary

    result["hard_peak_boundary_at_vmin"] = build_peak_boundary(v_min, v_min / 4.0)
    # Author-approved adaptive-domain extremum: mean photon number=V_A/2=2,
    # secondary orbit energy=1, hence q_peak=(2-1)/(30-1)=1/29 exactly.
    result["hard_peak_boundary_at_vmax"] = build_peak_boundary(v_max, 1.0)
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


def unique_ensemble_roster(
    ensembles: dict[str, Ensemble],
) -> tuple[dict[str, Ensemble], dict[str, str]]:
    """Remove only byte-identical fixtures and report alias -> canonical name.

    This is not a numerical-similarity reduction.  Equal hashes are confirmed
    by exact tensor equality so the removed unit would execute the same
    estimator on the same state batch and CRN tensor.
    """

    canonical_by_hash: dict[str, str] = {}
    unique: dict[str, Ensemble] = {}
    aliases: dict[str, str] = {}
    for name, ensemble in ensembles.items():
        digest = ensemble_sha256(ensemble)
        canonical = canonical_by_hash.get(digest)
        if canonical is None:
            canonical_by_hash[digest] = name
            unique[name] = ensemble
            continue
        reference = unique[canonical]
        left = (
            ensemble.probabilities, ensemble.amplitudes, ensemble.declared_va,
            ensemble.relative_constellation,
        )
        right = (
            reference.probabilities, reference.amplitudes, reference.declared_va,
            reference.relative_constellation,
        )
        if not all(torch.equal(a, b) for a, b in zip(left, right)):
            raise RuntimeError("SHA-256 collision in certification ensemble roster.")
        aliases[name] = canonical
    return unique, aliases


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
        "boundary_fixtures_included": [
            "hard_peak_boundary_at_vmin", "hard_peak_boundary_at_vmax",
        ],
        "publication_convergence_certification": False,
        "enumerated_fixture_sha256": {
            name: ensemble_sha256(ensemble) for name, ensemble in ensembles.items()
        },
        "coverage_limitation": (
            "Finite representative and boundary fixtures cannot certify the continuous learned "
            "parameter space or any selected checkpoint not explicitly enumerated and hash-bound."
        ),
    }
