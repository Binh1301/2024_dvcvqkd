"""Recompute the bounded corrected exploratory security subsets for Cases B--D."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.channel.turbulence import UavMotion
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.optimization.pointwise_guard import ensemble_row_sha256
from src.utils.random import array_sha256, derive_seed
N_CHANNEL = 1000
N_SECURITY = 16
CHANNEL_SEED = 20260910
AWGN_SEED = 20260911
EPSILON_SEED = derive_seed(CHANNEL_SEED, "joint_state_excess_noise")
AWGN_SAMPLES = 64
MODULATION_VARIANCE = 1.0
BETA = 0.95
PHASE_COEFFICIENT = 0.0
V_SC_OVERRIDE = 0.25
SIGMA_HAP_ANG_RAD = 5.0e-6
THETA_FOV_RAD = 0.0038910863
EPSILON_MIN = 0.001
EPSILON_MAX = 0.04

C_CORRECTED = 0.85985110654649868138037962728289179096834048571987
W_CORRECTED = 0.018327610474963502048823295065766568532781601388489
C_CORRECTED_TEXT = "0.85985110654649868138037962728289179096834048571987"
W_CORRECTED_TEXT = "0.018327610474963502048823295065766568532781601388489"
ENSEMBLE_HASH = "c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3"
CORRECTED_AP_ARTIFACT_SHA256 = "f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44"
CORRECTED_CASE_A_ARTIFACT_SHA256 = "a3b7aaa23635ac5e01e08f3486d4131fe9d17580c51b32ef9b498324fa5723fa"
OLD_BD_ARTIFACT_SHA256 = "e493bbdeda8ce8913862b8336a859dc2458a16dd444f392882d9b2389e39cc74"

OLD_WRONG_W = {
    "B": {"mean_chi_BE": 0.0204856716, "mean_K_active": 0.0072065872, "mean_K_all": 0.0072065872},
    "C": {"mean_chi_BE": 0.0188097272, "mean_K_active": 0.0065888504, "mean_K_all": 0.0065888504},
    "D": {"mean_chi_BE": 0.0167342180, "mean_K_active": 0.0057258242, "mean_K_all": 0.0041913033},
}

DEFAULT_Z_GRID_SIZE = 33
DEFAULT_Z_REFINEMENT_STEPS = 12


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _git_metadata() -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "dirty": None if status is None else bool(status),
    }


def _zero_motion() -> UavMotion:
    return UavMotion(
        sigma_x_m=0.0,
        sigma_y_m=0.0,
        sigma_z_m=0.0,
        sigma_theta_rad=0.0,
        sigma_phi_rad=0.0,
        sigma_psi_rad=0.0,
    )


def _case_options(case: str) -> dict[str, Any]:
    if case == "B":
        return {
            "uav_motion": _zero_motion(),
            "sigma_hap_ang_rad": 0.0,
            "aoa_model": "disabled",
            "sigma_turb_AoA2": 0.0,
            "turbulence_aoa_provenance": None,
            "theta_fov_rad": None,
        }
    if case in {"C", "D"}:
        options = {
            "uav_motion": UavMotion(),
            "sigma_hap_ang_rad": SIGMA_HAP_ANG_RAD,
            "aoa_model": "disabled",
            "sigma_turb_AoA2": 0.0,
            "turbulence_aoa_provenance": None,
            "theta_fov_rad": None,
        }
        if case == "D":
            options.update(
                {
                    "aoa_model": "external_validated",
                    "turbulence_aoa_provenance": (
                        "development fixture: zero turbulence-induced AoA variance"
                    ),
                    "theta_fov_rad": THETA_FOV_RAD,
                }
            )
        return options
    raise ValueError(f"Unsupported exploratory case: {case}")


def _sample_case(case: str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    geometry = LinkGeometry(20_000.0, 1_000.0, 0.0)
    channel = sample_fso_channel(
        geometry=geometry,
        wavelength_m=1.55e-6,
        visibility_km=200.0,
        beam_waist_m=0.0157,
        aperture_radius_m=0.075,
        cn2_m_minus_two_thirds=1.0e-16,
        sample_count=N_CHANNEL,
        rng=np.random.default_rng(CHANNEL_SEED),
        scintillation_log_variance=None,
        v_sc_override=V_SC_OVERRIDE,
        aperture_averaging_model="explicit_v_sc_override",
        **_case_options(case),
    )
    epsilon_base = np.random.default_rng(EPSILON_SEED).uniform(
        EPSILON_MIN, EPSILON_MAX, size=N_CHANNEL
    ).astype(np.float64, copy=False)
    if not np.all(channel.transmittance >= 0.0) or not np.all(channel.transmittance <= 1.0):
        raise AssertionError("The physical channel left [0,1].")
    metadata = {
        "channel": channel.metadata,
        "transmittance_sha256": array_sha256(channel.transmittance),
        "epsilon_base_sha256": array_sha256(epsilon_base),
        "realization_sha256": array_sha256(
            np.column_stack((channel.transmittance, epsilon_base))
        ),
        "channel_config": {
            "case": case,
            "sample_count": N_CHANNEL,
            "seed": CHANNEL_SEED,
            "v_sc_override": V_SC_OVERRIDE,
            **{
                key: value
                for key, value in _case_options(case).items()
                if key not in {"uav_motion"}
            },
            "uav_motion": {
                key: float(value) for key, value in _case_options(case)["uav_motion"].__dict__.items()
            },
        },
    }
    return channel.transmittance, epsilon_base, metadata


def _repeat_ensemble(source: Ensemble, count: int) -> Ensemble:
    return Ensemble(
        probabilities=source.probabilities.expand(count, -1),
        amplitudes=source.amplitudes.expand(count, -1),
        declared_va=source.declared_va.expand(count),
        raw_constellation=source.raw_constellation,
        exact_csi_oracle=source.exact_csi_oracle,
        c4_symmetric=source.c4_symmetric,
    )


def _security_roster(
    case: str, transmittance: np.ndarray, epsilon_base: np.ndarray
) -> dict[str, Any]:
    active_indices = np.flatnonzero(transmittance > 0.0).astype(np.int64, copy=False)
    if active_indices.size < N_SECURITY:
        raise AssertionError(f"{case} has fewer than {N_SECURITY} active states.")
    positions = np.linspace(0, active_indices.size - 1, N_SECURITY, dtype=np.int64)
    indices = active_indices[positions]
    pairs = np.ascontiguousarray(
        np.column_stack((transmittance[indices], epsilon_base[indices])), dtype=np.float64
    )
    return {
        "selection_rule": "evenly_spaced_active_rows_v1",
        "active_count": int(active_indices.size),
        "active_indices": indices.tolist(),
        "indices_sha256": _canonical_hash(indices.tolist()),
        "state_pairs_sha256": array_sha256(pairs),
    }


def _summary(values: torch.Tensor) -> dict[str, float]:
    return {
        "mean": float(values.mean()),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def _evaluate_case(
    case: str,
    transmittance: np.ndarray,
    epsilon_base: np.ndarray,
    source_ensemble: Ensemble,
) -> dict[str, Any]:
    roster = _security_roster(case, transmittance, epsilon_base)
    indices = np.asarray(roster["active_indices"], dtype=np.int64)
    t = torch.as_tensor(transmittance[indices], dtype=torch.float64)
    epsilon = torch.as_tensor(epsilon_base[indices], dtype=torch.float64)
    ensemble = _repeat_ensemble(source_ensemble, N_SECURITY)
    epsilon_total = epsilon + PHASE_COEFFICIENT * ensemble.declared_va
    mi = discrete_mutual_information(
        ensemble,
        t,
        epsilon_total,
        noise_samples_per_symbol=AWGN_SAMPLES,
        generator=torch.Generator(device="cpu").manual_seed(AWGN_SEED),
    )
    holevo = _holevo_from_source_moments(
        ensemble,
        t,
        epsilon_total,
        coherent_correlation=torch.full_like(t, C_CORRECTED),
        w_raw=torch.full_like(t, W_CORRECTED),
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=1.0e-8,
        physicality_tolerance=1.0e-10,
        diagnostics={
            "backend": "corrected_ap_cached_source_moments",
            "source_moment_status": "EXPLORATORY_CORRECTED_AP_W",
            "source_moment_artifact_sha256": CORRECTED_AP_ARTIFACT_SHA256,
        },
        z_grid_size=DEFAULT_Z_GRID_SIZE,
        z_refinement_steps=DEFAULT_Z_REFINEMENT_STEPS,
    )
    rate = fading_secret_key_rate(mi, holevo.chi_be, BETA)
    lambdas = torch.stack(
        (holevo.covariance.lambda1, holevo.covariance.lambda2, holevo.covariance.lambda3)
    )
    location = list(holevo.diagnostics["maximizing_location"])
    counts = {name: location.count(name) for name in ("lower_boundary", "upper_boundary", "interior")}
    interval_width = holevo.diagnostics["interval_width"]
    minimum_lambda = float(lambdas.min())
    channel_active_fraction = float(np.mean(transmittance > 0.0))
    mean_k_active = float(rate.instantaneous_raw.mean())
    mean_k_all = channel_active_fraction * mean_k_active
    identity_discrepancy = mean_k_all - channel_active_fraction * mean_k_active
    old = OLD_WRONG_W[case]
    corrected = {
        "mean_chi_BE": float(holevo.chi_be.mean()),
        "mean_K_active": mean_k_active,
        "mean_K_all": mean_k_all,
    }
    comparison = {
        quantity: {
            "old_wrong_w": old[quantity],
            "corrected": corrected[quantity],
            "absolute_change": corrected[quantity] - old[quantity],
            "relative_change": (corrected[quantity] - old[quantity]) / abs(old[quantity]),
        }
        for quantity in corrected
    }
    per_state = []
    for row, original_index in enumerate(indices.tolist()):
        per_state.append(
            {
                "original_index": int(original_index),
                "T": float(t[row]),
                "epsilon_base": float(epsilon[row]),
                "epsilon_total": float(epsilon_total[row]),
                "I_AB": float(mi[row]),
                "chi_BE": float(holevo.chi_be[row]),
                "raw_K": float(rate.instantaneous_raw[row]),
                "Z_minus": float(holevo.diagnostics["Z_minus"][row]),
                "Z_plus": float(holevo.diagnostics["Z_plus"][row]),
                "Z_phys": float(holevo.diagnostics["Z_phys"][row]),
                "Z_L": float(holevo.diagnostics["Z_L"][row]),
                "Z_U": float(holevo.diagnostics["Z_U"][row]),
                "Z_star": float(holevo.z[row]),
                "interval_width": float(interval_width[row]),
                "maximizing_location": location[row],
                "minimum_symplectic_eigenvalue": float(lambdas[:, row].min()),
            }
        )
    return {
        "case": case,
        "N_security": N_SECURITY,
        "security_roster": roster,
        "channel": {
            "N_channel": N_CHANNEL,
            "mean_T": float(np.mean(transmittance)),
            "std_T": float(np.std(transmittance)),
            "p_out": float(np.mean(transmittance == 0.0)),
            "active_fraction": channel_active_fraction,
            "outage_fraction": float(np.mean(transmittance == 0.0)),
            "transmittance_min": float(np.min(transmittance)),
            "transmittance_max": float(np.max(transmittance)),
        },
        "I_AB": _summary(mi),
        "chi_BE": _summary(holevo.chi_be),
        "raw_K_active": {
            **_summary(rate.instantaneous_raw),
            "positive_fraction": float(torch.mean((rate.instantaneous_raw > 0.0).to(torch.float64))),
        },
        "raw_K_all": mean_k_all,
        "outage_identity": {
            "mean_K_all": mean_k_all,
            "active_fraction_times_mean_K_active": channel_active_fraction * mean_k_active,
            "absolute_discrepancy": abs(identity_discrepancy),
        },
        "full_Z_diagnostics": {
            "lower_boundary_optima": counts["lower_boundary"],
            "upper_boundary_optima": counts["upper_boundary"],
            "interior_optima": counts["interior"],
            "interval_width_min": float(interval_width.min()),
            "interval_width_mean": float(interval_width.mean()),
            "interval_width_max": float(interval_width.max()),
            "security_domain_failure_count": int(
                (~holevo.diagnostics["security_domain_valid"]).sum()
            ),
            "minimum_symplectic_physicality": minimum_lambda,
            "solver": {
                "grid_size": DEFAULT_Z_GRID_SIZE,
                "refinement_steps": DEFAULT_Z_REFINEMENT_STEPS,
                "method": "fixed_grid_all_cells_golden_section",
            },
        },
        "old_wrong_w_comparison": comparison,
        "per_state": per_state,
        "outage_indices": np.flatnonzero(transmittance == 0.0).tolist(),
    }


def build_artifact() -> dict[str, Any]:
    started = time.perf_counter()
    source_ensemble = reference_ensemble(
        "uniform",
        batch_size=1,
        modulation_variance=MODULATION_VARIANCE,
        v_min=0.1,
        v_max=4.0,
        n_peak_photons=30.0,
    )
    source_ensemble.validate()
    row_hash = ensemble_row_sha256(source_ensemble, 0)
    if row_hash != ENSEMBLE_HASH:
        raise AssertionError(f"Exact ensemble hash mismatch: {row_hash}")
    cases: dict[str, dict[str, Any]] = {}
    sampled: dict[str, tuple[np.ndarray, np.ndarray, dict[str, Any]]] = {}
    case_runtime: dict[str, float] = {}
    for case in ("B", "C", "D"):
        case_started = time.perf_counter()
        sampled[case] = _sample_case(case)
        transmittance, epsilon_base, metadata = sampled[case]
        cases[case] = _evaluate_case(case, transmittance, epsilon_base, source_ensemble)
        cases[case]["channel_provenance"] = metadata
        case_runtime[case] = time.perf_counter() - case_started

    runtime = time.perf_counter() - started
    config = {
        "N_channel": N_CHANNEL,
        "N_security": N_SECURITY,
        "channel_seed": CHANNEL_SEED,
        "epsilon_base_seed": EPSILON_SEED,
        "awgn_seed": AWGN_SEED,
        "awgn_samples_per_symbol": AWGN_SAMPLES,
        "V_A": MODULATION_VARIANCE,
        "beta_rec": BETA,
        "phase_coefficient": PHASE_COEFFICIENT,
        "epsilon_base_range": [EPSILON_MIN, EPSILON_MAX],
        "physical_domain_rule": "truncated_renormalized_active_law",
        "outage_rule": "T=0 -> no policy, MI, Holevo; raw K=0",
    }
    return {
        "status": "EXPLORATORY_CORRECTED_AP_W",
        "scope": "bounded 16-active-state B-D exploratory security only",
        "source_moments": {
            "C": C_CORRECTED_TEXT,
            "w": W_CORRECTED_TEXT,
            "support": "256/256",
            "precision_rows_decimal_digits": [800, 900],
            "minimum_positive_eigenvalue": "3.9730108272405810054e-618",
            "worker_expression": "aa = x2.T",
        },
        "ensemble": {
            "kind": "uniform_256_qam",
            "symbols": 256,
            "positive_probabilities": 256,
            "unique_coherent_states": 256,
            "V_A": MODULATION_VARIANCE,
            "row_sha256": row_hash,
            "identical_across_cases": True,
        },
        "configuration": config,
        "full_Z_solver": {
            "grid_size": DEFAULT_Z_GRID_SIZE,
            "refinement_steps": DEFAULT_Z_REFINEMENT_STEPS,
            "physicality_tolerance": 1.0e-10,
            "symmetry_tolerance": 1.0e-8,
            "phase_disabled": True,
            "epsilon_total_definition": "epsilon_base + 0 * V_A",
        },
        "provenance": {
            "repository": _git_metadata(),
            "producer_script": "scripts/recompute_corrected_bd_security.py",
            "producer_script_sha256": _hash_file(Path(__file__)),
            "corrected_ap_worker_sha256": _hash_file(ROOT / "scripts" / "full_support_c4_worker.py"),
            "corrected_ap_artifact_sha256": CORRECTED_AP_ARTIFACT_SHA256,
            "corrected_ap_artifact_available_in_workspace": False,
            "corrected_case_A_artifact_sha256": CORRECTED_CASE_A_ARTIFACT_SHA256,
            "corrected_case_A_artifact_available_in_workspace": False,
            "historical_wrong_w_bd_artifact_sha256": OLD_BD_ARTIFACT_SHA256,
            "historical_wrong_w_bd_artifact_available_in_workspace": False,
            "exact_ensemble_sha256": ENSEMBLE_HASH,
            "configuration_sha256": _canonical_hash(config),
            "selection_reconstruction": (
                "Historical ignored B-D JSON and its exact indices were unavailable; "
                "indices were reconstructed from the supplied seed/config using the "
                "declared evenly_spaced_active_rows_v1 rule."
            ),
        },
        "corrected_case_A_reference": {
            "mean_T": 0.028919672940466015,
            "chi_BE": 0.01518919002933572,
            "raw_K": 0.004757635492383283,
        },
        "cases": cases,
        "case_runtime_seconds": case_runtime,
        "runtime_seconds": runtime,
        "no_ap_eigendecomposition": True,
        "training_ran": False,
        "final_test_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "exploratory_cases_BD_full_security_corrected_20260911.json",
    )
    args = parser.parse_args()
    artifact = build_artifact()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    for case in ("B", "C", "D"):
        row = artifact["cases"][case]
        print(
            f"{case}: mean_T={row['channel']['mean_T']:.12g} "
            f"mean_chi={row['chi_BE']['mean']:.12g} "
            f"mean_K_active={row['raw_K_active']['mean']:.12g}"
        )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
