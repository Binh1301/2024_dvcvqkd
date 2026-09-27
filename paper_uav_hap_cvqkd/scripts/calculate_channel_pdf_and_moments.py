"""Recompute the preliminary Case-D channel PDF from physical inputs.

This is a channel-only diagnostic.  It does not train or evaluate security.
The physical scenario is read from the active channel configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.special import log_ndtr, logsumexp, ndtri, roots_laguerre

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.channel.atmospheric_loss import atmospheric_transmittance_from_tau_zen
from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.channel.pointing_error import manuscript_pointing_parameters
from src.channel.scintillation import hufnagel_valley_cn2, hufnagel_valley_scintillation
from src.channel.turbulence import UavMotion
from scripts._common import load_yaml


# Historical exploratory comparison only; production uses the derived HV value.
OLD_V_SC = 0.25
EPSILON_CH = 0.0186
EPSILON_MEAN = EPSILON_CH
LAGUERRE_ORDER = 256
QUANTILE_Z = {float(q): float(ndtri(q)) for q in (0.05, 0.50, 0.95)}


def hv_cn2(h_m: float | np.ndarray, wind_m_per_s: float, cn2_ground: float):
    """Hufnagel--Valley profile used for the preliminary Case-D calculation."""

    return hufnagel_valley_cn2(h_m, wind_m_per_s, cn2_ground)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_physical_inputs(tau_zen_override: float | None = None) -> dict:
    channel = load_yaml(ROOT / "configs" / "default.yaml")["channel"]
    profile = channel["turbulence_profile"]
    if profile.get("model") != "hufnagel_valley":
        raise ValueError("The active diagnostic requires the configured Hufnagel-Valley profile.")
    if channel["scintillation"].get("aperture_averaging_model") != "hufnagel_valley_finite_aperture":
        raise ValueError("The active diagnostic requires the manuscript finite-aperture mapping.")
    pointing_config = channel["pointing"]
    aoa_config = channel["aoa"]
    wavelength_m = float(channel["wavelength_m"])
    h_hap_m = float(channel["h_hap_m"])
    h_uav_m = float(channel["h_uav_m"])
    zenith_angle_rad = float(channel.get("zenith_angle_rad", 0.0))
    link_length_m = (h_hap_m - h_uav_m) / math.cos(zenith_angle_rad)
    wind_m_per_s = float(profile["wind_speed_m_per_s"])
    cn2_ground = float(profile["cn2_ground_m_minus_two_thirds"])
    receiver_radius_m = float(channel["aperture_radius_m"])
    receiver_diameter_m = 2.0 * receiver_radius_m
    theta_div_rad = float(channel["theta_div_rad"])
    beam_waist_m = 2.0 * wavelength_m / (math.pi * theta_div_rad)
    tau_zen = channel.get("tau_zen") if tau_zen_override is None else tau_zen_override
    if tau_zen is None:
        raise ValueError(
            "Atmospheric scenario must be selected: provide an author-approved tau_zen."
        )
    tau_zen = float(tau_zen)
    sigma_hap_ang_rad = float(pointing_config["theta_jt_rad"])
    sigma_h_m = float(pointing_config["sigma_h_m"])
    sigma_o_rad = float(aoa_config["sigma_o_rad"])
    motion = UavMotion(
        sigma_x_m=sigma_h_m,
        sigma_y_m=sigma_h_m,
        sigma_z_m=0.0,
        sigma_theta_rad=sigma_o_rad,
        sigma_phi_rad=sigma_o_rad,
        sigma_psi_rad=0.0,
    )
    derivation = hufnagel_valley_scintillation(
        h_uav_m,
        h_hap_m,
        wavelength_m,
        zenith_angle_rad,
        wind_m_per_s,
        cn2_ground,
        receiver_diameter_m,
    )
    sigma_R0_squared = derivation["sigma_R0_squared"]
    v_sc = derivation["v_sc"]

    geometry = LinkGeometry(h_hap_m, h_uav_m, zenith_angle_rad)
    eta_atm = atmospheric_transmittance_from_tau_zen(
        link_length_m, tau_zen, zenith_angle_rad
    )
    pointing = manuscript_pointing_parameters(
        receiver_radius_m,
        beam_waist_m,
        wavelength_m,
        link_length_m,
        float(channel["radius_of_curvature_m"]),
        h_uav_m,
        h_hap_m,
        zenith_angle_rad,
        wind_m_per_s,
        cn2_ground,
    )
    sigma_uav_transverse_m2 = (motion.sigma_x_m**2 + motion.sigma_y_m**2) / 2.0
    sigma_hap_displacement_m2 = link_length_m**2 * sigma_hap_ang_rad**2
    sigma_m2 = sigma_uav_transverse_m2 + sigma_hap_displacement_m2
    sigma_m = math.sqrt(sigma_m2)
    sigma_o2 = sigma_o_rad**2
    theta_fov_rad = float(aoa_config["theta_fov_rad"])
    p_out = math.exp(-theta_fov_rad**2 / (2.0 * sigma_o2))

    return {
        "wavelength_m": wavelength_m,
        "h_hap_m": h_hap_m,
        "h_uav_m": h_uav_m,
        "link_length_m": link_length_m,
        "zenith_angle_rad": zenith_angle_rad,
        "wind_m_per_s": wind_m_per_s,
        "cn2_ground_m_minus_two_thirds": cn2_ground,
        "receiver_radius_m": receiver_radius_m,
        "receiver_diameter_m": receiver_diameter_m,
        "beam_waist_m": beam_waist_m,
        "tau_zen": tau_zen,
        "radius_of_curvature_m": float(channel["radius_of_curvature_m"]),
        "sigma_hap_ang_rad": sigma_hap_ang_rad,
        "uav_motion": {key: float(value) for key, value in motion.__dict__.items()},
        "wave_number_per_m": 2.0 * math.pi / wavelength_m,
        "rytov_integral": derivation["rytov_integral"],
        "rytov_integral_quad_error": derivation["rytov_integral_quad_error"],
        "sigma_R0_squared": float(sigma_R0_squared),
        "aperture_numerator": derivation["aperture_numerator"],
        "aperture_numerator_quad_error": derivation["aperture_numerator_quad_error"],
        "aperture_denominator": derivation["aperture_denominator"],
        "aperture_denominator_quad_error": derivation["aperture_denominator_quad_error"],
        "Phi_m": derivation["Phi_m"],
        "A_ap": derivation["A_ap"],
        "v_sc": float(v_sc),
        "eta_atm": float(eta_atm),
        "pointing": {
            "eta_p0": float(pointing.t0_power),
            "beam_radius_receiver_m": float(pointing.beam_radius_receiver_m),
            "rayleigh_range_m": float(pointing.rayleigh_range_m),
            "R_m": float(pointing.scale_radius_m),
            "Gamma": float(pointing.gamma),
            "omega_L_m": float(pointing.omega_l_m),
            "G_d": float(pointing.g_d),
            "omega_L_eq_m": float(pointing.omega_l_eq_m),
            "nu": float(pointing.nu),
            "A0": float(pointing.a0),
        },
        "sigma_uav_transverse_m2": float(sigma_uav_transverse_m2),
        "sigma_hap_displacement_m2": float(sigma_hap_displacement_m2),
        "sigma_m2": float(sigma_m2),
        "sigma_m": float(sigma_m),
        "rho_m": 0.0,
        "sigma_o2_rad2": float(sigma_o2),
        "sigma_o_rad": float(math.sqrt(sigma_o2)),
        "theta_fov_rad": theta_fov_rad,
        "p_out": float(p_out),
        "p_in": float(1.0 - p_out),
        "theta_div_rad": theta_div_rad,
        "omega_0_m": beam_waist_m,
        "sigma_h_m": sigma_h_m,
        "theta_jt_rad": sigma_hap_ang_rad,
        "sigma_o_rad": sigma_o_rad,
        "epsilon_ch_snu": EPSILON_CH,
        "epsilon_mean_snu": EPSILON_MEAN,
        "c_phi": 0.0,
        "geometry": geometry,
        "motion": motion,
    }


def hsc_statistics(v_sc: float) -> dict:
    mu = -v_sc / 2.0
    sigma = math.sqrt(v_sc)
    log_normalizer = math.log(sigma * math.sqrt(2.0 * math.pi))

    def log_normal_pdf(y: float) -> float:
        if not math.isfinite(y):
            return -math.inf
        return -0.5 * ((y - mu) / sigma) ** 2 - log_normalizer

    normalizing = quad(
        lambda y: math.exp(log_normal_pdf(y)),
        -math.inf,
        math.inf,
        epsabs=2.0e-13,
        epsrel=2.0e-13,
    )[0]
    mean_integral = quad(
        lambda y: math.exp(y + log_normal_pdf(y))
        if math.isfinite(y + log_normal_pdf(y))
        else 0.0,
        -math.inf,
        math.inf,
        epsabs=2.0e-13,
        epsrel=2.0e-13,
    )[0]
    return {
        "v_sc": float(v_sc),
        "log_mean": float(mu),
        "log_variance": float(v_sc),
        "pdf_formula": (
            "1/(h*sqrt(2*pi*v_sc))*exp(-(log(h)+v_sc/2)^2/(2*v_sc)), h>0"
        ),
        "pdf_normalization": float(normalizing),
        "mean_integral": float(mean_integral),
        "mean": 1.0,
        "variance": float(math.expm1(v_sc)),
        "standard_deviation": float(math.sqrt(math.expm1(v_sc))),
        "median": float(math.exp(mu)),
        "q05": float(math.exp(mu + QUANTILE_Z[0.05] * sigma)),
        "q50": float(math.exp(mu + QUANTILE_Z[0.50] * sigma)),
        "q95": float(math.exp(mu + QUANTILE_Z[0.95] * sigma)),
        "E_sqrt_H_sc": float(math.exp(-v_sc / 8.0)),
    }


def hsc_pdf(values: np.ndarray, v_sc: float) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    result = np.zeros_like(values)
    positive = values > 0.0
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        log_h = np.log(values[positive])
        result[positive] = np.exp(
            -log_h
            - 0.5 * math.log(2.0 * math.pi * v_sc)
            - (log_h + v_sc / 2.0) ** 2 / (2.0 * v_sc)
        )
    return result


def pointing_pdf(values, physical: dict):
    """Evaluate the independently transformed zero-boresight pointing PDF."""

    values = np.asarray(values, dtype=np.float64)
    result = np.zeros_like(values)
    eta_p0 = physical["pointing"]["eta_p0"]
    radius = physical["pointing"]["R_m"]
    gamma = physical["pointing"]["Gamma"]
    sigma_m = physical["sigma_m"]
    valid = (values > 0.0) & (values < eta_p0)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        z = -np.log(values[valid] / eta_p0)
        result[valid] = (
            radius**2
            / (gamma * sigma_m**2 * values[valid])
            * z ** (2.0 / gamma - 1.0)
            * np.exp(-radius**2 * z ** (2.0 / gamma) / (2.0 * sigma_m**2))
        )
    return result


def _product_kernel(v_sc: float, physical: dict, order: int = LAGUERRE_ORDER):
    nodes, weights = roots_laguerre(order)
    keep = weights > 0.0
    nodes = np.asarray(nodes[keep], dtype=np.float64)
    weights = np.asarray(weights[keep], dtype=np.float64)
    log_weights = np.log(weights)
    pointing = physical["pointing"]
    beta = (
        2.0 * physical["sigma_m"] ** 2 / pointing["R_m"] ** 2
    ) ** (pointing["Gamma"] / 2.0)
    power = pointing["Gamma"] / 2.0
    log_c = math.log(physical["eta_atm"] * pointing["eta_p0"])
    component_means = log_c - v_sc / 2.0 - beta * nodes**power
    return {
        "nodes": nodes,
        "weights": weights,
        "log_weights": log_weights,
        "beta": float(beta),
        "point_power": float(power),
        "log_c": float(log_c),
        "component_means": component_means,
        "sigma_log": math.sqrt(v_sc),
    }


def _log_product_pdf_log_coordinate(log_t, kernel: dict):
    log_t = np.asarray(log_t, dtype=np.float64)
    z = (log_t[..., None] - kernel["component_means"]) / kernel["sigma_log"]
    values = logsumexp(
        kernel["log_weights"]
        - 0.5 * math.log(2.0 * math.pi)
        - math.log(kernel["sigma_log"])
        - 0.5 * z**2,
        axis=-1,
    )
    return values


def product_pdf(values, kernel: dict):
    values = np.asarray(values, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.exp(
            _log_product_pdf_log_coordinate(np.log(values), kernel) - np.log(values)
        )
    return result


def product_cdf(values, kernel: dict):
    values = np.asarray(values, dtype=np.float64)
    log_t = np.log(values)[..., None]
    z = (log_t - kernel["component_means"]) / kernel["sigma_log"]
    return np.exp(logsumexp(kernel["log_weights"] + log_ndtr(z), axis=-1))


def _tail_probability(v_sc: float, physical: dict) -> float:
    log_c = math.log(physical["eta_atm"] * physical["pointing"]["eta_p0"])
    mu = -v_sc / 2.0
    sigma = math.sqrt(v_sc)
    beta = (
        2.0 * physical["sigma_m"] ** 2 / physical["pointing"]["R_m"] ** 2
    ) ** (physical["pointing"]["Gamma"] / 2.0)
    point_power = physical["pointing"]["Gamma"] / 2.0
    z0 = (-log_c - mu) / sigma
    log_sf0 = float(log_ndtr(-z0))

    def scaled_integrand(x: float) -> float:
        z = (-log_c + beta * x**point_power - mu) / sigma
        return math.exp(float(log_ndtr(-z)) - log_sf0 - x)

    scaled_integral = quad(
        scaled_integrand,
        0.0,
        math.inf,
        epsabs=2.0e-13,
        epsrel=2.0e-10,
        limit=300,
    )[0]
    return float(math.exp(log_sf0) * scaled_integral)


def _untruncated_moment(power: float, v_sc: float, physical: dict) -> float:
    c = physical["eta_atm"] * physical["pointing"]["eta_p0"]
    beta = (
        2.0 * physical["sigma_m"] ** 2 / physical["pointing"]["R_m"] ** 2
    ) ** (physical["pointing"]["Gamma"] / 2.0)
    point_power = physical["pointing"]["Gamma"] / 2.0
    pointing_moment = quad(
        lambda x: math.exp(-x - power * beta * x**point_power),
        0.0,
        math.inf,
        epsabs=2.0e-13,
        epsrel=2.0e-13,
        limit=300,
    )[0]
    scintillation_moment = math.exp((power**2 - power) * v_sc / 2.0)
    return float(c**power * scintillation_moment * pointing_moment)


def _truncated_moment(power: float, v_sc: float, physical: dict) -> float:
    c = physical["eta_atm"] * physical["pointing"]["eta_p0"]
    log_c = math.log(c)
    mu = -v_sc / 2.0
    sigma = math.sqrt(v_sc)
    beta = (
        2.0 * physical["sigma_m"] ** 2 / physical["pointing"]["R_m"] ** 2
    ) ** (physical["pointing"]["Gamma"] / 2.0)
    point_power = physical["pointing"]["Gamma"] / 2.0

    def integrand(x: float) -> float:
        log_hp = -beta * x**point_power
        log_h_max = -log_c - log_hp
        z = (log_h_max - mu - power * v_sc) / sigma
        log_cdf = float(log_ndtr(z))
        if log_cdf < -745.0:
            return 0.0
        return math.exp(
            -x
            + power * (log_c + log_hp)
            + power * mu
            + 0.5 * power**2 * v_sc
            + log_cdf
        )

    return float(
        quad(
            integrand,
            0.0,
            math.inf,
            epsabs=2.0e-13,
            epsrel=2.0e-12,
            limit=300,
        )[0]
    )


def _pdf_log_integral(power: float, kernel: dict, upper_log: float) -> float:
    def integrand(log_t: float) -> float:
        log_pdf = float(_log_product_pdf_log_coordinate(log_t, kernel))
        exponent = power * log_t + log_pdf
        return 0.0 if exponent < -745.0 else math.exp(exponent)

    return float(
        quad(
            integrand,
            -math.inf,
            upper_log,
            epsabs=2.0e-11,
            epsrel=2.0e-10,
            limit=300,
        )[0]
    )


def _product_quantile(probability: float, kernel: dict) -> float:
    lower = 1.0e-15
    upper = 1.0
    for _ in range(100):
        midpoint = math.sqrt(lower * upper)
        if float(product_cdf(midpoint, kernel)) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return float(math.sqrt(lower * upper))


def _mixed_quantiles(analysis: dict, physical: dict) -> dict:
    kernel = _product_kernel(analysis["v_sc"], physical)
    F1 = analysis["quadrature"]["F_X_1"]
    probabilities = (0.01, 0.05, 0.50, 0.95, 0.99)
    result = {}
    for probability in probabilities:
        if probability <= physical["p_out"]:
            value = 0.0
        else:
            conditional_target = (
                (probability - physical["p_out"]) / physical["p_in"] * F1
            )
            value = _product_quantile(conditional_target, kernel)
        result[f"q{int(round(100 * probability)):02d}"] = float(value)
    return result


def _pointing_pdf_normalization(physical: dict) -> float:
    radius = physical["pointing"]["R_m"]
    gamma = physical["pointing"]["Gamma"]
    sigma_m = physical["sigma_m"]
    exponent = 2.0 / gamma

    def integrand(s: float) -> float:
        if s <= 0.0:
            return 0.0
        return (
            radius**2
            / (gamma * sigma_m**2)
            * s ** (exponent - 1.0)
            * math.exp(-radius**2 * s**exponent / (2.0 * sigma_m**2))
        )

    return float(
        quad(
            integrand,
            0.0,
            math.inf,
            epsabs=2.0e-11,
            epsrel=2.0e-10,
            limit=300,
        )[0]
    )


def analyze_product(v_sc: float, physical: dict) -> dict:
    kernel = _product_kernel(v_sc, physical)
    tail = _tail_probability(v_sc, physical)
    F1 = float(1.0 - tail)
    pdf_normalization = _pdf_log_integral(0.0, kernel, math.inf)
    active_pdf_normalization = _pdf_log_integral(0.0, kernel, 0.0) / F1
    pdf_moments = {
        "mean": _pdf_log_integral(1.0, kernel, 0.0) / F1,
        "sqrt_mean": _pdf_log_integral(0.5, kernel, 0.0) / F1,
        "second_moment": _pdf_log_integral(2.0, kernel, 0.0) / F1,
    }
    truncated = {
        "mean": _truncated_moment(1.0, v_sc, physical),
        "sqrt_mean": _truncated_moment(0.5, v_sc, physical),
        "second_moment": _truncated_moment(2.0, v_sc, physical),
    }
    raw = {
        "mean": _untruncated_moment(1.0, v_sc, physical),
        "sqrt_mean": _untruncated_moment(0.5, v_sc, physical),
        "second_moment": _untruncated_moment(2.0, v_sc, physical),
    }
    quantile_probabilities = (0.0005, 0.001, 0.01, 0.05, 0.50, 0.95, 0.99, 0.999, 0.9995)
    raw_quantiles = {
        f"q{int(round(100000 * probability)):05d}": _product_quantile(
            probability, kernel
        )
        for probability in quantile_probabilities
    }
    active_mean = truncated["mean"] / F1
    active_sqrt_mean = truncated["sqrt_mean"] / F1
    return {
        "v_sc": float(v_sc),
        "quadrature": {
            "laguerre_order": LAGUERRE_ORDER,
            "retained_positive_nodes": int(kernel["nodes"].size),
            "f_X_formula": (
                "integral_0^eta_p0 [f_Hsc(t/(eta_atm*u))/(eta_atm*u)] "
                "f_Hp(u) du; evaluated as a lognormal mixture over x=r^2/(2*sigma_m^2)"
            ),
            "f_X_normalization": pdf_normalization,
            "active_pdf_normalization": active_pdf_normalization,
            "F_X_1": F1,
            "P_X_gt_1": tail,
            "f_X_at_1": float(product_pdf(1.0, kernel)),
            "raw_moments": raw,
            "truncated_moments_below_1": truncated,
            "pdf_moments_below_1": pdf_moments,
            "moment_crosscheck_abs_error": {
                key: abs(pdf_moments[key] - truncated[key] / F1)
                for key in pdf_moments
            },
        },
        "moments": {
            "active_mean_eta": float(active_mean),
            "active_mean_sqrt_eta": float(active_sqrt_mean),
            "active_second_moment_eta": float(truncated["second_moment"] / F1),
            "active_variance_eta": float(
                truncated["second_moment"] / F1 - active_mean**2
            ),
            "mean_eta": float(physical["p_in"] * active_mean),
            "mean_sqrt_eta": float(physical["p_in"] * active_sqrt_mean),
            "sqrt_mean_eta": float(math.sqrt(physical["p_in"] * active_mean)),
            "mean_eta_xi_eta": float(
                physical["p_in"] * active_mean * EPSILON_MEAN
            ),
        },
        "quantiles_X": raw_quantiles,
        "plot_quantile_bounds": {
            "lower_probability": 0.0005,
            "upper_probability": 0.9995,
            "lower": raw_quantiles["q00050"],
            "upper": raw_quantiles["q99950"],
        },
    }


def _stderr(values: np.ndarray) -> float:
    return float(np.std(values, ddof=1) / math.sqrt(values.size))


def primitive_monte_carlo(v_sc: float, physical: dict, sample_count: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    sigma = math.sqrt(v_sc)
    h_sc = np.exp(rng.normal(-v_sc / 2.0, sigma, sample_count))
    radial = np.hypot(
        rng.normal(0.0, physical["sigma_m"], sample_count),
        rng.normal(0.0, physical["sigma_m"], sample_count),
    )
    pointing = physical["pointing"]
    h_p = pointing["eta_p0"] * np.exp(
        -np.power(radial / pointing["R_m"], pointing["Gamma"])
    )
    raw = physical["eta_atm"] * h_sc * h_p
    angular_radius = np.hypot(
        rng.normal(0.0, physical["sigma_o_rad"], sample_count),
        rng.normal(0.0, physical["sigma_o_rad"], sample_count),
    )
    gate = angular_radius <= physical["theta_fov_rad"]
    above = raw > 1.0
    valid_active = gate & ~above
    t = np.zeros(sample_count, dtype=np.float64)
    t[valid_active] = raw[valid_active]
    epsilon = np.full(sample_count, physical["epsilon_ch_snu"], dtype=np.float64)
    sqrt_t = np.sqrt(t)
    t_xi = t * epsilon
    active_raw = raw[valid_active]
    return {
        "sample_count": sample_count,
        "seed": seed,
        "p_out": float(np.mean(~gate)),
        "p_in": float(np.mean(gate)),
        "p_X_gt_1": float(np.mean(above)),
        "p_X_gt_1_standard_error": float(
            math.sqrt(np.mean(above) * (1.0 - np.mean(above)) / sample_count)
        ),
        "p_X_gt_1_95_percent_upper_bound_if_zero": float(3.0 / sample_count),
        "above_one_count": int(np.count_nonzero(above)),
        "valid_active_count": int(active_raw.size),
        "mean_eta_active": float(np.mean(active_raw)),
        "mean_eta_active_standard_error": _stderr(active_raw),
        "mean_sqrt_eta_active": float(np.mean(np.sqrt(active_raw))),
        "mean_sqrt_eta_active_standard_error": _stderr(np.sqrt(active_raw)),
        "mean_eta": float(np.mean(t)),
        "mean_eta_standard_error": _stderr(t),
        "mean_sqrt_eta": float(np.mean(sqrt_t)),
        "mean_sqrt_eta_standard_error": _stderr(sqrt_t),
        "mean_eta_xi_eta": float(np.mean(t_xi)),
        "mean_eta_xi_eta_standard_error": _stderr(t_xi),
        "quantiles_T": {
            f"q{int(round(100 * probability)):02d}": float(np.quantile(t, probability))
            for probability in (0.01, 0.05, 0.50, 0.95, 0.99)
        },
    }


def production_sampler_check(
    v_sc: float, physical: dict, sample_count: int, seed: int
) -> dict:
    pointing = physical["pointing"]
    result = sample_fso_channel(
        geometry=physical["geometry"],
        wavelength_m=physical["wavelength_m"],
        tau_zen=physical["tau_zen"],
        beam_waist_m=physical["beam_waist_m"],
        radius_of_curvature_m=physical["radius_of_curvature_m"],
        theta_div_rad=physical["theta_div_rad"],
        pointing_model="manuscript_gaussian_equivalent",
        aperture_radius_m=physical["receiver_radius_m"],
        cn2_m_minus_two_thirds=physical["cn2_ground_m_minus_two_thirds"],
        sample_count=sample_count,
        rng=np.random.default_rng(seed),
        uav_motion=physical["motion"],
        scintillation_log_variance=None,
        v_sc_override=None,
        aperture_averaging_model="hufnagel_valley_finite_aperture",
        turbulence_profile_model="hufnagel_valley",
        wind_speed_m_per_s=physical["wind_m_per_s"],
        ground_cn2_m_minus_two_thirds=physical["cn2_ground_m_minus_two_thirds"],
        boresight_x_m=physical["rho_m"],
        boresight_y_m=0.0,
        sigma_hap_ang_rad=physical["sigma_hap_ang_rad"],
        hap_angular_jitter_convention="per_axis",
        aoa_model="external_validated",
        sigma_turb_AoA2=0.0,
        turbulence_aoa_provenance="preliminary Case-D zero turbulence-induced AoA fixture",
        theta_fov_rad=physical["theta_fov_rad"],
    )
    t = result.transmittance
    return {
        "sample_count": sample_count,
        "seed": seed,
        "mean_eta": float(np.mean(t)),
        "mean_eta_standard_error": _stderr(t),
        "mean_sqrt_eta": float(np.mean(np.sqrt(t))),
        "mean_sqrt_eta_standard_error": _stderr(np.sqrt(t)),
        "mean_eta_xi_eta": float(np.mean(t) * EPSILON_MEAN),
        "p_out": float(result.metadata["p_out"]),
        "p_in": float(result.metadata["p_in"]),
        "p_X_gt_1": float(result.metadata["p_above_one"]),
        "quantiles_T": {
            f"q{int(round(100 * probability)):02d}": float(np.quantile(t, probability))
            for probability in (0.01, 0.05, 0.50, 0.95, 0.99)
        },
        "channel_metadata": {
            "sigma_axis_m": float(result.sigma_axis_m),
            "physical_domain_rule": result.metadata["physical_domain_rule"],
            "scintillation": result.metadata["provenance"]["scintillation_model"],
            "profile_model": result.metadata["provenance"]["turbulence_profile"]["model"],
            "p_above_one_active": float(result.metadata["p_above_one_active"]),
        },
    }


def _comparison(reference: float, observed: float, standard_error: float | None = None) -> dict:
    result = {
        "reference": float(reference),
        "observed": float(observed),
        "absolute_difference": float(abs(observed - reference)),
        "relative_difference": float(abs(observed - reference) / abs(reference))
        if reference
        else None,
    }
    if standard_error is not None:
        result["standard_error"] = float(standard_error)
        result["difference_in_standard_errors"] = float(
            abs(observed - reference) / standard_error
        ) if standard_error else None
    return result


def _active_config_record() -> dict:
    config_path = ROOT / "configs" / "default.yaml"
    try:
        from _common import load_yaml

        channel = load_yaml(config_path)["channel"]
        return {
            "path": str(config_path.relative_to(ROOT)),
            "sha256": _sha256(config_path),
            "h_hap_m": channel.get("h_hap_m"),
            "h_uav_m": channel.get("h_uav_m"),
            "wavelength_m": channel.get("wavelength_m"),
            "scalar_cn2": channel.get("cn2_m_minus_two_thirds"),
            "tau_zen": channel.get("tau_zen"),
            "turbulence_profile_model": channel.get("turbulence_profile", {}).get("model"),
            "aperture_averaging_model": channel.get("scintillation", {}).get(
                "aperture_averaging_model"
            ),
            "v_sc_override": channel.get("scintillation", {}).get("v_sc_override"),
            "theta_jt_rad": channel.get("pointing", {}).get("theta_jt_rad"),
            "sigma_h_m": channel.get("pointing", {}).get("sigma_h_m"),
            "sigma_o_rad": channel.get("aoa", {}).get("sigma_o_rad"),
            "epsilon_noise_model": channel.get("excess_noise_distribution", {}).get("kind"),
            "aoa_model": channel.get("aoa", {}).get("model"),
        }
    except Exception as exc:  # pragma: no cover - provenance should not hide PDF output
        return {"path": str(config_path.relative_to(ROOT)), "read_error": str(exc)}


def _plot_single(physical: dict, analysis: dict, figure_path: Path) -> None:
    low = analysis["plot_quantile_bounds"]["lower"]
    high = analysis["plot_quantile_bounds"]["upper"]
    eta = np.geomspace(low, high, 1200)
    kernel = _product_kernel(analysis["v_sc"], physical)
    p_active = np.asarray(product_pdf(eta, kernel), dtype=float) / analysis["quadrature"]["F_X_1"]
    p_continuous = physical["p_in"] * p_active
    mean_eta = analysis["moments"]["mean_eta"]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.plot(eta, p_continuous, linewidth=2.0, label=r"$p_{\rm in}p_{\rm active}(\eta)$")
    ax.plot(eta, p_active, "--", linewidth=1.5, label=r"$p_{\rm active}(\eta)$")
    ax.axvline(
        mean_eta,
        linestyle=":",
        linewidth=1.5,
        label=rf"$\langle\eta\rangle={mean_eta:.5f}$",
    )
    ax.annotate(
        rf"AoA atom: $P(T=0)={physical['p_out']:.6f}$",
        xy=(eta[0], 0.0),
        xytext=(0.04, 0.90),
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="->"),
    )
    ax.set_xlabel(r"Channel transmittance $\eta=T$")
    ax.set_ylabel("Probability density")
    ax.set_title("Preliminary Case-D HAP--UAV transmittance PDF")
    ax.grid(alpha=0.25)
    ax.legend()
    ax.set_xlim(float(eta[0]), float(eta[-1]))
    fig.tight_layout()
    fig.savefig(figure_path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(figure_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def _plot_comparison(physical: dict, old: dict, new: dict, figure_path: Path) -> dict:
    low = min(old["plot_quantile_bounds"]["lower"], new["plot_quantile_bounds"]["lower"])
    high = max(old["plot_quantile_bounds"]["upper"], new["plot_quantile_bounds"]["upper"])
    eta = np.geomspace(low, high, 1200)
    old_kernel = _product_kernel(OLD_V_SC, physical)
    new_kernel = _product_kernel(new["v_sc"], physical)
    old_pdf = np.asarray(product_pdf(eta, old_kernel), dtype=float) / old["quadrature"]["F_X_1"]
    new_pdf = np.asarray(product_pdf(eta, new_kernel), dtype=float) / new["quadrature"]["F_X_1"]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.plot(eta, physical["p_in"] * old_pdf, linewidth=1.8, label=r"old $v_{sc}=0.25$")
    ax.plot(eta, physical["p_in"] * new_pdf, linewidth=1.8, label=rf"new $v_{{sc}}={new['v_sc']:.5f}$")
    ax.set_xlabel(r"Channel transmittance $\eta=T$")
    ax.set_ylabel("Continuous probability density")
    ax.set_title("Preliminary Case-D channel PDF: old versus derived scintillation")
    ax.text(
        0.98,
        0.95,
        rf"same $p_{{in}}={physical['p_in']:.6f}$; atom $P(T=0)={physical['p_out']:.6f}$",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
    )
    ax.grid(alpha=0.25)
    ax.legend()
    ax.set_xlim(float(eta[0]), float(eta[-1]))
    fig.tight_layout()
    fig.savefig(figure_path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(figure_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    return {
        "eta_grid": eta.tolist(),
        "old_p_continuous": (physical["p_in"] * old_pdf).tolist(),
        "new_p_continuous": (physical["p_in"] * new_pdf).tolist(),
        "lower": float(low),
        "upper": float(high),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-count", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument(
        "--tau-zen",
        type=float,
        default=None,
        help="Explicit atmospheric scenario for diagnostics; never selected implicitly.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "channel_pdf_and_moments.json",
    )
    args = parser.parse_args()
    if args.sample_count < 100_000:
        raise ValueError("Use at least 100,000 Monte Carlo samples for this diagnostic.")

    physical = derive_physical_inputs(args.tau_zen)
    old_hsc = hsc_statistics(OLD_V_SC)
    new_hsc = hsc_statistics(physical["v_sc"])
    old = analyze_product(OLD_V_SC, physical)
    new = analyze_product(physical["v_sc"], physical)
    pointing_pdf_normalization = _pointing_pdf_normalization(physical)
    old["quantiles_T"] = _mixed_quantiles(old, physical)
    new["quantiles_T"] = _mixed_quantiles(new, physical)

    if not math.isfinite(physical["v_sc"]) or physical["v_sc"] <= 0.0:
        raise FloatingPointError("Derived Hufnagel--Valley v_sc must be positive.")
    if abs(new["quadrature"]["f_X_normalization"] - 1.0) > 2.0e-9:
        raise FloatingPointError("Composite PDF normalization failed.")
    if abs(new["quadrature"]["active_pdf_normalization"] - 1.0) > 2.0e-9:
        raise FloatingPointError("Active PDF normalization failed.")
    if abs(new["quadrature"]["moment_crosscheck_abs_error"]["mean"]) > 2.0e-9:
        raise FloatingPointError("PDF and latent-variable mean disagree.")
    if abs(pointing_pdf_normalization - 1.0) > 2.0e-9:
        raise FloatingPointError("Pointing PDF normalization failed.")
    if new["moments"]["mean_sqrt_eta"] > new["moments"]["sqrt_mean_eta"] + 1.0e-12:
        raise FloatingPointError("sqrt(E[eta]) inequality failed.")
    if abs(physical["p_out"] + physical["p_in"] - 1.0) > 1.0e-15:
        raise FloatingPointError("AoA probability mass does not sum to one.")

    primitive = primitive_monte_carlo(
        physical["v_sc"], physical, args.sample_count, args.seed
    )
    production = production_sampler_check(
        physical["v_sc"], physical, args.sample_count, args.seed + 1
    )
    monte_carlo_comparison = {
        "mean_eta": _comparison(
            new["moments"]["mean_eta"],
            primitive["mean_eta"],
            primitive["mean_eta_standard_error"],
        ),
        "mean_sqrt_eta": _comparison(
            new["moments"]["mean_sqrt_eta"],
            primitive["mean_sqrt_eta"],
            primitive["mean_sqrt_eta_standard_error"],
        ),
        "mean_eta_xi_eta": _comparison(
            new["moments"]["mean_eta_xi_eta"],
            primitive["mean_eta_xi_eta"],
            primitive["mean_eta_xi_eta_standard_error"],
        ),
        "p_X_gt_1": _comparison(
            new["quadrature"]["P_X_gt_1"],
            primitive["p_X_gt_1"],
            primitive["p_X_gt_1_standard_error"],
        ),
        "p_out": _comparison(
            physical["p_out"], primitive["p_out"]
        ),
        "quantiles_T": {
            key: _comparison(
                new["quantiles_T"][key], primitive["quantiles_T"][key]
            )
            for key in new["quantiles_T"]
        },
        "production_quantiles_T": {
            key: _comparison(
                new["quantiles_T"][key], production["quantiles_T"][key]
            )
            for key in new["quantiles_T"]
        },
        "production_mean_eta": _comparison(
            new["moments"]["mean_eta"],
            production["mean_eta"],
            production["mean_eta_standard_error"],
        ),
        "production_mean_sqrt_eta": _comparison(
            new["moments"]["mean_sqrt_eta"],
            production["mean_sqrt_eta"],
            production["mean_sqrt_eta_standard_error"],
        ),
    }

    figures_dir = ROOT / "results" / "figures_preliminary"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _plot_single(physical, new, figures_dir / "channel_transmittance_pdf")
    comparison_plot = _plot_comparison(
        physical,
        old,
        new,
        figures_dir / "channel_transmittance_pdf_old_vs_new",
    )
    new_grid = np.geomspace(
        new["plot_quantile_bounds"]["lower"],
        new["plot_quantile_bounds"]["upper"],
        1200,
    )
    new_kernel = _product_kernel(new["v_sc"], physical)
    new_p_active = np.asarray(product_pdf(new_grid, new_kernel), dtype=float) / new["quadrature"]["F_X_1"]
    new_p_continuous = physical["p_in"] * new_p_active

    profile_grid = np.linspace(physical["h_uav_m"], physical["h_hap_m"], 100_001)
    profile_values = hv_cn2(
        profile_grid,
        physical["wind_m_per_s"],
        physical["cn2_ground_m_minus_two_thirds"],
    )
    hsc_grid = np.geomspace(
        max(1.0e-4, min(old_hsc["q05"], new_hsc["q05"]) * 0.5),
        max(old_hsc["q95"], new_hsc["q95"]) * 1.5,
        800,
    )
    pointing_grid = np.geomspace(
        physical["pointing"]["eta_p0"] * 1.0e-8,
        physical["pointing"]["eta_p0"] * (1.0 - 1.0e-10),
        800,
    )
    physical_json = {
        key: value
        for key, value in physical.items()
        if key not in {"geometry", "motion"}
    }
    if math.isinf(float(physical_json["radius_of_curvature_m"])):
        physical_json["radius_of_curvature_m"] = "inf"
    physical_json["profile"] = {
        "model": "Hufnagel-Valley",
        "height_interval_m": [physical["h_uav_m"], physical["h_hap_m"]],
        "formula": (
            "0.00594*(v_wind/27)^2*(1e-5*h)^10*exp(-h/1000) + "
            "2.7e-16*exp(-h/1500) + Cn2_ground*exp(-h/100)"
        ),
        "grid_point_count_for_sampler_provenance": int(profile_grid.size),
        "cn2_min_on_grid": float(np.min(profile_values)),
        "cn2_max_on_grid": float(np.max(profile_values)),
    }
    payload = {
        "schema": "preliminary-channel-pdf-and-moments-v1",
        "status": "PRELIMINARY_DIAGNOSTIC_ONLY",
        "physical_inputs_frozen": False,
        "lifecycle": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        "scope": "channel PDF, scintillation, pointing, AoA mixture, and moments only",
        "physical_derivation": physical_json,
        "repository_active_config": _active_config_record(),
        "repository_config_difference": {
            "note": "The physical configuration is manuscript-aligned; tau_zen remains author-unselected.",
            "requested_profile": "Hufnagel-Valley with v_wind=21 m/s and Cn2_ground=1e-14",
            "active_profile_model": "hufnagel_valley",
            "requested_v_sc": physical["v_sc"],
            "active_v_sc_override": None,
            "requested_sigma_hap_ang_rad": physical["sigma_hap_ang_rad"],
            "active_sigma_hap_ang_rad": physical["sigma_hap_ang_rad"],
            "requested_aoa_model": "external_validated with zero turbulence AoA variance",
            "active_aoa_model": "external_validated",
        },
        "scintillation": {
            "old": old_hsc,
            "new": new_hsc,
            "pdf_grid": hsc_grid.tolist(),
            "old_pdf": hsc_pdf(hsc_grid, OLD_V_SC).tolist(),
            "new_pdf": hsc_pdf(hsc_grid, physical["v_sc"]).tolist(),
        },
        "pointing": {
            "formula": "H_p(r)=eta_p0*exp(-(r/R)^Gamma)",
            "rho_m": physical["rho_m"],
            "parameters": physical["pointing"],
            "pdf_normalization": pointing_pdf_normalization,
            "normalization_method": "u=eta_p0*exp(-s), then integrate f_Hp(u)*u ds over s in [0,infinity]",
            "pdf_grid": pointing_grid.tolist(),
            "pdf": pointing_pdf(pointing_grid, physical).tolist(),
        },
        "aoa_mixture": {
            "p_out": physical["p_out"],
            "p_in": physical["p_in"],
            "atom": "p_out*delta_0",
            "continuous_component": "p_in*p_active(eta), eta in (0,1]",
        },
        "old": old,
        "new": new,
        "old_vs_new": {
            "rows": [
                {
                    "quantity": "v_sc",
                    "old": OLD_V_SC,
                    "new": physical["v_sc"],
                },
                {
                    "quantity": "sigma_R0_squared",
                    "old": None,
                    "new": physical["sigma_R0_squared"],
                },
                {"quantity": "A_ap", "old": None, "new": physical["A_ap"]},
                {
                    "quantity": "Var(H_sc)",
                    "old": old_hsc["variance"],
                    "new": new_hsc["variance"],
                },
                {
                    "quantity": "std(H_sc)",
                    "old": old_hsc["standard_deviation"],
                    "new": new_hsc["standard_deviation"],
                },
                {
                    "quantity": "median(H_sc)",
                    "old": old_hsc["median"],
                    "new": new_hsc["median"],
                },
                {
                    "quantity": "<eta>_active",
                    "old": old["moments"]["active_mean_eta"],
                    "new": new["moments"]["active_mean_eta"],
                },
                {
                    "quantity": "<eta>",
                    "old": old["moments"]["mean_eta"],
                    "new": new["moments"]["mean_eta"],
                },
                {
                    "quantity": "<sqrt(eta)>",
                    "old": old["moments"]["mean_sqrt_eta"],
                    "new": new["moments"]["mean_sqrt_eta"],
                },
                {
                    "quantity": "<eta xi_eta>",
                    "old": old["moments"]["mean_eta_xi_eta"],
                    "new": new["moments"]["mean_eta_xi_eta"],
                },
                {
                    "quantity": "P(X>1)",
                    "old": old["quadrature"]["P_X_gt_1"],
                    "new": new["quadrature"]["P_X_gt_1"],
                },
            ]
        },
        "monte_carlo": {
            "primitive": primitive,
            "production_sampler": production,
            "comparison": monte_carlo_comparison,
        },
        # These top-level fields keep the artifact consumable by the existing
        # root-level plotting helper without changing that user-owned script.
        "eta_grid": new_grid.tolist(),
        "p_active": new_p_active.tolist(),
        "p_continuous": new_p_continuous.tolist(),
        "p_out": physical["p_out"],
        "p_in": physical["p_in"],
        "mean_eta": new["moments"]["mean_eta"],
        "mean_sqrt_eta": new["moments"]["mean_sqrt_eta"],
        "mean_eta_xi_eta": new["moments"]["mean_eta_xi_eta"],
        "figures": {
            "single_pdf": {
                "png": "results/figures_preliminary/channel_transmittance_pdf.png",
                "pdf": "results/figures_preliminary/channel_transmittance_pdf.pdf",
                "eta_grid": new_grid.tolist(),
                "p_active": new_p_active.tolist(),
                "p_continuous": new_p_continuous.tolist(),
                "plot_lower": float(new_grid[0]),
                "plot_upper": float(new_grid[-1]),
            },
            "old_vs_new": {
                "png": "results/figures_preliminary/channel_transmittance_pdf_old_vs_new.png",
                "pdf": "results/figures_preliminary/channel_transmittance_pdf_old_vs_new.pdf",
                "eta_grid": comparison_plot["eta_grid"],
                "old_p_continuous": comparison_plot["old_p_continuous"],
                "new_p_continuous": comparison_plot["new_p_continuous"],
                "plot_lower": comparison_plot["lower"],
                "plot_upper": comparison_plot["upper"],
            },
        },
        "validation": {
            "f_Hsc_integral": new_hsc["pdf_normalization"],
            "E_Hsc": new_hsc["mean_integral"],
            "f_Hp_integral": pointing_pdf_normalization,
            "f_X_integral": new["quadrature"]["f_X_normalization"],
            "p_active_integral": new["quadrature"]["active_pdf_normalization"],
            "p_out_plus_p_in": physical["p_out"] + physical["p_in"],
            "sqrt_eta_le_sqrt_mean_eta": new["moments"]["mean_sqrt_eta"]
            <= new["moments"]["sqrt_mean_eta"],
            "E_X_vs_eta_atm_E_Hp": {
                "E_X_active_untruncated": new["quadrature"]["raw_moments"]["mean"],
                "eta_atm_E_Hp": _untruncated_moment(1.0, 0.0, physical),
                "new_active_mean_below_1": new["moments"]["active_mean_eta"],
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "output": str(args.output.resolve()),
                "v_sc": physical["v_sc"],
                "p_out": physical["p_out"],
                "mean_eta": new["moments"]["mean_eta"],
                "mean_sqrt_eta": new["moments"]["mean_sqrt_eta"],
                "primitive_mc_mean_eta": primitive["mean_eta"],
                "production_mean_eta": production["mean_eta"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
