"""Fail-closed diagnostics for an explicitly resolved FSO channel scenario."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np
from scipy.integrate import quad
from scipy.special import i0

from .atmospheric_loss import extinction_coefficient_per_km
from .geometry import LinkGeometry
from .pointing_error import PointingParameters, pointing_pdf
from .scintillation import lognormal_pdf
from .state_distribution import (
    IndependentUniformExcessNoise,
    sample_channel_state_distribution,
)
from .turbulence import UavMotion


def composite_transmittance_diagnostics(
    raw_transmittance: Iterable[float],
    physical_transmittance: Iterable[float],
    *,
    aoa_gate: Iterable[int] | None = None,
) -> dict[str, float | None]:
    """Summarize raw/physical moments without hiding domain violations."""

    raw = np.asarray(tuple(raw_transmittance), dtype=np.float64)
    physical = np.asarray(tuple(physical_transmittance), dtype=np.float64)
    if raw.ndim != 1 or physical.shape != raw.shape or raw.size == 0:
        raise ValueError("Raw and physical transmittance arrays must be nonempty and equally shaped.")
    if not np.all(np.isfinite(raw)) or not np.all(np.isfinite(physical)):
        raise ValueError("Raw and physical transmittances must be finite.")
    if np.any(raw < 0.0) or np.any(physical < 0.0) or np.any(physical > 1.0):
        raise ValueError("Transmittances must be nonnegative and physical T must be at most one.")
    if aoa_gate is None:
        gate = (raw > 0.0).astype(np.int8)
    else:
        gate = np.asarray(tuple(aoa_gate), dtype=np.int8)
        if gate.shape != raw.shape or not np.all(np.isin(gate, (0, 1))):
            raise ValueError("aoa_gate must be a zero/one array matching transmittances.")
    raw_mean = float(np.mean(raw))
    physical_mean = float(np.mean(physical))
    mean_difference = raw_mean - physical_mean
    return {
        "p_out": float(np.mean(gate == 0)),
        "p_in": float(np.mean(gate == 1)),
        "p_above_one": float(np.mean(raw > 1.0)),
        "raw_mean_T": raw_mean,
        "physical_mean_T": physical_mean,
        "mean_difference_T": mean_difference,
        "delta_T": (
            None
            if physical_mean == 0.0
            else float(abs(raw_mean - physical_mean) / physical_mean)
        ),
    }


def active_transmittance_pdf_eq49(
    t: float,
    *,
    eta_atm: float,
    v_sc: float,
    pointing: PointingParameters,
    sigma_jt_m: float,
    rho_m: float = 0.0,
) -> float:
    """Evaluate the active-link PDF by directly integrating PDF Eq. (49)."""

    t = _positive_finite("t", t)
    eta_atm = _positive_finite("eta_atm", eta_atm)
    v_sc = _positive_finite("v_sc", v_sc)
    sigma_jt_m = _positive_finite("sigma_jt_m", sigma_jt_m)
    rho_m = float(rho_m)
    if not math.isfinite(rho_m) or rho_m < 0.0:
        raise ValueError("rho_m must be finite and nonnegative.")

    # Eq. (49) is evaluated with h_p=A0*exp(-s), retaining its Jacobian:
    # du=-h_p ds, so [f_Hsc/(eta_atm*h_p)]*f_Hp*du=f_Hsc*f_Hp/eta_atm ds.
    log_eta_a0 = math.log(eta_atm * pointing.t0_power)
    chi_squared = (pointing.omega_L_eq_m / (2.0 * sigma_jt_m)) ** 2
    s_peak = max(0.0, -math.log(t) + log_eta_a0 - v_sc / 2.0)

    def integrand(s: float) -> float:
        h_p = pointing.t0_power * math.exp(-s)
        f_hsc = float(lognormal_pdf(np.asarray([t / (eta_atm * h_p)]), v_sc)[0])
        f_hp = float(pointing_pdf(np.asarray([h_p]), pointing, sigma_jt_m, rho_m)[0])
        return f_hsc / eta_atm * f_hp

    integral, _ = quad(
        integrand,
        0.0,
        max(80.0, s_peak + 20.0 * math.sqrt(v_sc) + 5.0),
        points=[s_peak] if s_peak > 0.0 else None,
        epsabs=1.0e-12,
        epsrel=1.0e-9,
        limit=300,
    )
    return float(integral)


def active_transmittance_pdf_eq50(
    t: float,
    *,
    eta_atm: float,
    v_sc: float,
    pointing: PointingParameters,
    sigma_jt_m: float,
    rho_m: float = 0.0,
) -> float:
    """Evaluate the explicit analytical active-link PDF from PDF Eq. (50)."""

    t = _positive_finite("t", t)
    eta_atm = _positive_finite("eta_atm", eta_atm)
    v_sc = _positive_finite("v_sc", v_sc)
    sigma_jt_m = _positive_finite("sigma_jt_m", sigma_jt_m)
    rho_m = float(rho_m)
    if not math.isfinite(rho_m) or rho_m < 0.0:
        raise ValueError("rho_m must be finite and nonnegative.")
    sigma_squared = sigma_jt_m**2
    a0 = float(pointing.t0_power)
    chi_squared = (pointing.omega_L_eq_m / (2.0 * sigma_jt_m)) ** 2

    def log_integrand(h_p: float) -> float:
        if h_p <= 0.0:
            return -math.inf
        radial_squared = -0.5 * pointing.omega_L_eq_m**2 * math.log(h_p / a0)
        bessel_argument = rho_m * math.sqrt(radial_squared) / sigma_squared
        return (
            (chi_squared - 1.0) * math.log(h_p)
            - (
                math.log(t / (eta_atm * h_p)) + v_sc / 2.0
            )
            ** 2
            / (2.0 * v_sc)
            + math.log(float(i0(bessel_argument)))
        )

    # For the baseline rho=0 case, split at the exact peak of the Eq. (50)
    # integrand so small-t log-normal mass is not missed by quad.
    h_p_peak = t * math.exp(v_sc * (chi_squared - 0.5)) / eta_atm
    h_p_scale = min(a0, max(np.nextafter(0.0, 1.0), h_p_peak))
    log_scale = log_integrand(h_p_scale)
    integration_points = sorted(
        {
            point
            for point in (h_p_peak / 2.0, h_p_peak, 2.0 * h_p_peak)
            if 0.0 < point < a0
        }
    )

    def integrand(h_p: float) -> float:
        return math.exp(log_integrand(h_p) - log_scale)

    integral, _ = quad(
        integrand,
        0.0,
        a0,
        points=integration_points or None,
        epsabs=1.0e-14,
        epsrel=1.0e-10,
        limit=300,
    )
    prefactor = (
        chi_squared
        * math.exp(-rho_m**2 / (2.0 * sigma_squared))
        / (a0**chi_squared * t * math.sqrt(2.0 * math.pi * v_sc))
    )
    return float(math.exp(math.log(prefactor) + log_scale) * integral)


def active_channel_moments(
    *,
    eta_atm: float,
    v_sc: float,
    pointing: PointingParameters,
    sigma_jt_m: float,
    p_in: float = 1.0,
    rho_m: float = 0.0,
) -> dict[str, float]:
    """Numerically evaluate PDF Eqs. (53), (56), and (57)."""

    p_in = float(p_in)
    if not math.isfinite(p_in) or not 0.0 <= p_in <= 1.0:
        raise ValueError("p_in must lie in [0,1].")
    pdf = lambda t: active_transmittance_pdf_eq49(
        t,
        eta_atm=eta_atm,
        v_sc=v_sc,
        pointing=pointing,
        sigma_jt_m=sigma_jt_m,
        rho_m=rho_m,
    )
    # Integrate in log(t) so the narrow low-transmittance density is not
    # skipped by the outer adaptive quadrature.
    log_lower = -40.0
    log_upper = 0.0
    log_center = math.log(eta_atm * pointing.t0_power)
    log_points = sorted(
        {
            point
            for point in (
                log_center - 4.0 * math.sqrt(v_sc),
                log_center - 2.0 * math.sqrt(v_sc),
                log_center,
                log_center + 2.0 * math.sqrt(v_sc),
                log_center + 4.0 * math.sqrt(v_sc),
            )
            if log_lower < point < log_upper
        }
    )

    def integrate_power(power: float) -> float:
        return float(
            quad(
                lambda log_t: math.exp((power + 1.0) * log_t) * pdf(math.exp(log_t)),
                log_lower,
                log_upper,
                points=log_points or None,
                epsabs=1.0e-9,
                epsrel=1.0e-7,
                limit=300,
            )[0]
        )

    f_x_1 = integrate_power(0.0)
    mean_t = integrate_power(1.0)
    mean_sqrt_t = integrate_power(0.5)
    return {
        "F_X_1": float(f_x_1),
        "mean_T": float(p_in * mean_t / f_x_1),
        "mean_sqrt_T": float(p_in * mean_sqrt_t / f_x_1),
    }


def _positive_finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and positive.")
    return value


def _quantile_probabilities(values: Iterable[float]) -> np.ndarray:
    probabilities = np.asarray(tuple(values), dtype=np.float64)
    if probabilities.ndim != 1 or probabilities.size == 0:
        raise ValueError("At least one quantile probability is required.")
    if np.any(~np.isfinite(probabilities)) or np.any(probabilities <= 0.0) or np.any(
        probabilities >= 1.0
    ):
        raise ValueError("Quantile probabilities must be finite and strictly inside (0,1).")
    if np.any(np.diff(probabilities) <= 0.0):
        raise ValueError("Quantile probabilities must be strictly increasing.")
    return probabilities


def transformed_rayleigh_transmittance_quantile(
    probability: float,
    *,
    upper_transmittance: float,
    sigma_axis_m: float,
    scale_radius_m: float,
    gamma: float,
) -> float:
    """Analytic quantile of ``T=upper*exp[-(r/R)^gamma]`` for Rayleigh ``r``."""

    probability = float(probability)
    upper_transmittance = _positive_finite("upper_transmittance", upper_transmittance)
    sigma_axis_m = _positive_finite("sigma_axis_m", sigma_axis_m)
    scale_radius_m = _positive_finite("scale_radius_m", scale_radius_m)
    gamma = _positive_finite("gamma", gamma)
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly inside (0,1).")
    coefficient = scale_radius_m**2 / (2.0 * sigma_axis_m**2)
    exponent = ((-math.log(probability)) / coefficient) ** (gamma / 2.0)
    return float(upper_transmittance * math.exp(-exponent))


def transformed_rayleigh_mean_transmittance(
    *,
    upper_transmittance: float,
    sigma_axis_m: float,
    scale_radius_m: float,
    gamma: float,
    quadrature_order: int = 64,
) -> float:
    """Deterministic Gauss--Laguerre mean of the transformed Rayleigh law."""

    upper_transmittance = _positive_finite("upper_transmittance", upper_transmittance)
    sigma_axis_m = _positive_finite("sigma_axis_m", sigma_axis_m)
    scale_radius_m = _positive_finite("scale_radius_m", scale_radius_m)
    gamma = _positive_finite("gamma", gamma)
    if not isinstance(quadrature_order, int) or quadrature_order < 16:
        raise ValueError("quadrature_order must be an integer of at least 16.")
    # x=r^2/(2 sigma^2) is Exp(1), matching the Laguerre weight exp(-x).
    nodes, weights = np.polynomial.laguerre.laggauss(quadrature_order)
    pointing_loss = np.exp(
        -np.power(sigma_axis_m * np.sqrt(2.0 * nodes) / scale_radius_m, gamma)
    )
    result = upper_transmittance * float(np.sum(weights * pointing_loss))
    if not 0.0 < result <= upper_transmittance:
        raise FloatingPointError("Computed mean transmittance violates physical support.")
    return result


def frozen_channel_diagnostics(
    *,
    geometry: LinkGeometry,
    wavelength_m: float,
    visibility_km: float,
    beam_waist_m: float,
    aperture_radius_m: float,
    cn2_m_minus_two_thirds: float,
    eta_atm: float | None = None,
    theta_div_rad: float | None = None,
    f0_m: float = math.inf,
    sigma_h_m: float | None = None,
    sigma_hap_ang_rad: float = 0.0,
    sigma_o_rad: float | None = None,
    motion: UavMotion,
    epsilon_minimum_snu: float,
    epsilon_maximum_snu: float,
    sample_count: int,
    seed: int,
    quantile_probabilities: Iterable[float],
) -> dict[str, Any]:
    """Compute a reproducible physical/channel diagnostic artifact payload.

    ``sample_count`` and ``seed`` are diagnostic software choices, not physical
    parameters or train/validation/test seeds. They must be fixed before the
    artifact is generated.
    """

    if not isinstance(sample_count, int) or sample_count < 2:
        raise ValueError("sample_count must be an integer of at least two.")
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer.")
    probabilities = _quantile_probabilities(quantile_probabilities)
    wavelength_m = _positive_finite("wavelength_m", wavelength_m)
    visibility_km = _positive_finite("visibility_km", visibility_km)
    beam_waist_m = _positive_finite("beam_waist_m", beam_waist_m)
    aperture_radius_m = _positive_finite("aperture_radius_m", aperture_radius_m)
    cn2_m_minus_two_thirds = _positive_finite(
        "cn2_m_minus_two_thirds", cn2_m_minus_two_thirds
    )
    geometry.validate()
    motion.validate()
    states = sample_channel_state_distribution(
        geometry=geometry,
        wavelength_m=wavelength_m,
        visibility_km=visibility_km,
        beam_waist_m=beam_waist_m,
        aperture_radius_m=aperture_radius_m,
        cn2_m_minus_two_thirds=cn2_m_minus_two_thirds,
        excess_noise=IndependentUniformExcessNoise(
            epsilon_minimum_snu, epsilon_maximum_snu
        ),
        sample_count=sample_count,
        seed=seed,
        uav_motion=motion,
        scintillation_log_variance=0.0,
        eta_atm=eta_atm,
        theta_div_rad=theta_div_rad,
        f0_m=f0_m,
        sigma_h_m=sigma_h_m,
        sigma_hap_ang_rad=sigma_hap_ang_rad,
        sigma_o_rad=sigma_o_rad,
    )
    fso = states.fso
    pointing = fso.pointing
    metadata = fso.metadata
    sigma_turbulence_m = math.sqrt(float(metadata["sigma2_turbulence_m2"]))
    sigma_uav_m = math.sqrt(float(metadata["sigma2_uav_m2"]))
    sigma_axis_m = fso.sigma_axis_m
    upper_transmittance = fso.atmospheric_transmittance * pointing.t0_power
    extinction_per_km = extinction_coefficient_per_km(
        visibility_km, wavelength_m * 1.0e9
    )
    analytic_quantiles = np.asarray(
        [
            transformed_rayleigh_transmittance_quantile(
                probability,
                upper_transmittance=upper_transmittance,
                sigma_axis_m=sigma_axis_m,
                scale_radius_m=pointing.scale_radius_m,
                gamma=pointing.gamma,
            )
            for probability in probabilities
        ],
        dtype=np.float64,
    )
    analytic_mean = transformed_rayleigh_mean_transmittance(
        upper_transmittance=upper_transmittance,
        sigma_axis_m=sigma_axis_m,
        scale_radius_m=pointing.scale_radius_m,
        gamma=pointing.gamma,
    )
    empirical_quantiles = np.quantile(states.transmittance, probabilities)
    empirical_mean = float(np.mean(states.transmittance))
    mean_standard_error = float(
        np.std(states.transmittance, ddof=1) / math.sqrt(sample_count)
    )
    mean_z_score = abs(empirical_mean - analytic_mean) / mean_standard_error
    if mean_z_score > 6.0:
        raise FloatingPointError(
            "Monte Carlo T mean disagrees with deterministic quadrature by more than 6 SE."
        )
    if np.any(states.transmittance <= 0.0) or np.any(
        states.transmittance > upper_transmittance * (1.0 + 1e-12)
    ):
        raise FloatingPointError("Generated T violates its physical support.")
    if not 0.0 < fso.atmospheric_transmittance <= 1.0:
        raise FloatingPointError("Atmospheric power transmittance must lie in (0,1].")
    if not 0.0 < pointing.t0_power < 1.0 or upper_transmittance > 1.0:
        raise FloatingPointError("Aperture or composite on-axis power exceeds unity.")
    if pointing.beam_radius_receiver_m < beam_waist_m:
        raise FloatingPointError("Gaussian beam radius contracted in free propagation.")
    if not states.metadata["statistical_dependence"].startswith(
        "T and epsilon_base independent"
    ):
        raise FloatingPointError("The approved independent T-epsilon_base law was not used.")

    wave_number_per_m = 2.0 * math.pi / wavelength_m
    rytov_variance_plane_wave = (
        1.23
        * cn2_m_minus_two_thirds
        * wave_number_per_m ** (7.0 / 6.0)
        * geometry.link_length_m ** (11.0 / 6.0)
    )
    quantile_records = {
        f"p{int(round(100.0 * probability)):02d}": {
            "probability": float(probability),
            "analytic_transmittance": float(analytic),
            "empirical_transmittance": float(empirical),
        }
        for probability, analytic, empirical in zip(
            probabilities, analytic_quantiles, empirical_quantiles
        )
    }
    return {
        "schema": "frozen-channel-diagnostics-v2-composite-compatible",
        "status": "PASS",
        "scenario": {
            "name": "nominal_good_weather_homogeneous_kruse_sensitivity_scenario",
            "interpretation": (
                "Author-approved nominal good-weather sensitivity scenario; not a "
                "universal atmosphere or measured HAP-UAV joint distribution."
            ),
            "temporal_model": "iid Monte Carlo states; no time correlation",
            "boresight_model": "zero deterministic boresight; centered Rayleigh jitter",
        },
        "classifications": {
            "physical_inputs": "AUTHOR_APPROVED",
            "derived_channel_quantities": "DERIVED",
            "diagnostic_seed_and_count": "SOFTWARE_PREREGISTERED",
            "convergence_selected_values": [],
        },
        "physical_inputs": {
            "h_hap_m": float(geometry.h_hap_m),
            "h_uav_m": float(geometry.h_uav_m),
            "zenith_angle_rad": float(geometry.zenith_angle_rad),
            "wavelength_m": wavelength_m,
            "visibility_km": visibility_km,
            "beam_waist_m": beam_waist_m,
            "aperture_radius_m": aperture_radius_m,
            "cn2_m_minus_two_thirds": cn2_m_minus_two_thirds,
            "uav_motion_standard_deviations": {
                key: float(value) for key, value in motion.__dict__.items()
            },
            "epsilon_minimum_snu": float(epsilon_minimum_snu),
            "epsilon_maximum_snu": float(epsilon_maximum_snu),
            "epsilon_distribution": (
                f"independent Uniform[{float(epsilon_minimum_snu):g},"
                f"{float(epsilon_maximum_snu):g}] input-referred SNU"
            ),
            "beam_wander_status": metadata["beam_wander_status"],
            "aoa_model": metadata["provenance"]["aoa_model"],
            "scintillation_model": metadata["provenance"]["scintillation_model"],
            "physical_domain_rule": metadata["physical_domain_rule"],
        },
        "derived": {
            "vertical_separation_m": float(geometry.vertical_separation_m),
            "link_length_m": float(geometry.link_length_m),
            "extinction_coefficient_per_km_napier": float(extinction_per_km),
            "extinction_db_per_km": float(10.0 * extinction_per_km / math.log(10.0)),
            "atmospheric_power_transmittance": float(fso.atmospheric_transmittance),
            "rayleigh_range_m": float(pointing.rayleigh_range_m),
            "beam_radius_receiver_m": float(pointing.beam_radius_receiver_m),
            "centered_aperture_power_coupling_t0_squared": float(pointing.t0_power),
            "sigma_turbulence_m": float(sigma_turbulence_m),
            "sigma_uav_m": float(sigma_uav_m),
            "sigma_r_rayleigh_scale_m": float(sigma_axis_m),
            "radial_rms_displacement_m": float(math.sqrt(2.0) * sigma_axis_m),
            "pointing_shape_gamma": float(pointing.gamma),
            "pointing_scale_radius_m": float(pointing.scale_radius_m),
            "transmittance_support": {
                "lower": 0.0,
                "lower_inclusive": False,
                "upper": float(upper_transmittance),
                "upper_inclusive": True,
            },
            "analytic_mean_transmittance": float(analytic_mean),
            "plane_wave_rytov_variance_diagnostic": float(rytov_variance_plane_wave),
            "p_out": float(metadata["p_out"]),
            "p_in": float(metadata["p_in"]),
            "p_above_one": float(metadata["p_above_one"]),
            "raw_mean_T": float(metadata["raw_mean_T"]),
            "physical_mean_T": float(metadata["physical_mean_T"]),
            "delta_T": metadata["delta_T"],
        },
        "monte_carlo_diagnostic": {
            "sample_count": sample_count,
            "base_seed": seed,
            "transmittance_seed": states.transmittance_seed,
            "epsilon_base_seed": states.epsilon_base_seed,
            "excess_noise_seed": states.excess_noise_seed,
            "empirical_mean_transmittance": empirical_mean,
            "mean_standard_error": mean_standard_error,
            "analytic_mean_difference_in_standard_errors": float(mean_z_score),
            "empirical_transmittance_variance": float(np.var(states.transmittance)),
            "empirical_epsilon_base_mean_snu": float(np.mean(states.epsilon_base_snu)),
            "empirical_epsilon_base_variance_snu2": float(
                np.var(states.epsilon_base_snu)
            ),
            "empirical_epsilon_mean_snu": float(np.mean(states.epsilon_base_snu)),
            "empirical_epsilon_variance_snu2": float(np.var(states.epsilon_base_snu)),
            "empirical_t_epsilon_correlation": float(
                np.corrcoef(states.transmittance, states.epsilon_base_snu)[0, 1]
            ),
            "transmittance_sha256": states.metadata["transmittance_sha256"],
            "epsilon_base_sha256": states.metadata["epsilon_base_sha256"],
            "excess_noise_sha256": states.metadata["excess_noise_sha256"],
            "joint_realization_sha256": states.realization_sha256,
            "quantiles": quantile_records,
            "raw_mean_T": float(metadata["raw_mean_T"]),
            "physical_mean_T": float(metadata["physical_mean_T"]),
            "p_out": float(metadata["p_out"]),
            "p_in": float(metadata["p_in"]),
            "p_above_one": float(metadata["p_above_one"]),
            "delta_T": metadata["delta_T"],
        },
        "validity_and_limitations": [
            "Vertical 19 km path with homogeneous 200 km Kruse visibility.",
            "The legacy scalar Cn2 is not used for active pointing beam wander; no validated altitude-profile or aperture mapping is frozen.",
            "Plane-wave Rytov variance is an applicability diagnostic only and is not an added fading term.",
            "Independent zero-mean Gaussian UAV components and zero boresight produce Rayleigh radial jitter.",
            "States are iid, not a time-correlated UAV trajectory.",
            "No additional optical-throughput or detector-efficiency loss is included in T.",
            "Epsilon_base is an assumed independent operating-domain distribution, not measured atmospheric coupling.",
            "AoA turbulence is explicitly disabled because no validated C_n^2(h)->AoA mapping is available.",
        ],
        "downstream_channel_outputs": {
            "qam_adaptation": ["instantaneous power transmittance T", "input-referred epsilon_base in SNU"],
            "cvqkd": ["the identical instantaneous power transmittance T", "epsilon_base input and evaluator-derived epsilon_total in SNU"],
            "do_not_substitute": ["field amplitude sqrt(T)", "received-power SNR", "detector-output noise"],
        },
    }
