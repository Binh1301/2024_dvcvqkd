"""Plot and validate the manuscript Eq. (62) raw HAP--UAV channel PDF.

This is an isolated channel-only diagnostic.  It deliberately keeps the raw
product ``T_raw = eta_atm * H_sc * H_p * B_AoA``: no clipping, ``T <= 1``
conditioning, physical-domain renormalization, CV-QKD, or security code is
used here.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
import math
from pathlib import Path
import sys
import types

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml


CONFIG_DEFAULT = ROOT / "configs" / "channel.yaml"
OUTPUT_DEFAULT = ROOT / "diagnostics"
_BACKEND_NOTES: list[str] = []


def _load_repository_modules() -> dict[str, object]:
    """Load pure repository channel modules without executing scipy-heavy __init__."""

    # ``src.channel.__init__`` imports the production sampler, which imports
    # optional SciPy extensions.  The diagnostic only needs the pure channel
    # helpers below, so keep the import boundary isolated.
    channel_path = ROOT / "src" / "channel"
    channel_package = types.ModuleType("src.channel")
    channel_package.__path__ = [str(channel_path)]
    sys.modules.setdefault("src.channel", channel_package)

    modules: dict[str, object] = {}
    for name in ("geometry", "atmospheric_loss", "turbulence", "aoa"):
        try:
            modules[name] = importlib.import_module(f"src.channel.{name}")
        except Exception as error:  # pragma: no cover - environment dependent.
            _BACKEND_NOTES.append(f"repository {name} import unavailable: {error}")
    for name in ("scintillation", "pointing_error"):
        try:
            modules[name] = importlib.import_module(f"src.channel.{name}")
        except Exception as error:  # pragma: no cover - environment dependent.
            _BACKEND_NOTES.append(f"repository {name} import unavailable: {error}")
            sys.modules.pop(f"src.channel.{name}", None)
    return modules


_REPOSITORY = _load_repository_modules()


def _repo_or_local(name: str, fallback):
    module_name, attribute = name.split(":")
    module = _REPOSITORY.get(module_name)
    if module is not None and hasattr(module, attribute):
        return getattr(module, attribute), True
    return fallback, False


@dataclass(frozen=True)
class LocalMotion:
    sigma_x_m: float
    sigma_y_m: float
    sigma_z_m: float
    sigma_theta_rad: float
    sigma_phi_rad: float
    sigma_psi_rad: float


@dataclass(frozen=True)
class LocalGeometry:
    h_hap_m: float
    h_uav_m: float
    zenith_angle_rad: float

    @property
    def link_length_m(self) -> float:
        return _local_link_length(self.h_hap_m, self.h_uav_m, self.zenith_angle_rad)


def _local_link_length(h_hap_m: float, h_uav_m: float, zenith_angle_rad: float) -> float:
    return (h_hap_m - h_uav_m) / math.cos(zenith_angle_rad)


def _local_atmospheric_transmittance(
    link_length_m: float, tau_zen: float, zenith_angle_rad: float
) -> float:
    return float(tau_zen ** (1.0 / math.cos(zenith_angle_rad)))


def _local_uav_translational_variance(motion: LocalMotion) -> float:
    return (motion.sigma_x_m**2 + motion.sigma_y_m**2) / 2.0


def _local_hap_displacement_variance(link_length_m: float, sigma_hap_ang_rad: float) -> float:
    return link_length_m**2 * sigma_hap_ang_rad**2


def _local_aoa_variance(motion: LocalMotion, sigma_turbulence2: float) -> float:
    return (motion.sigma_theta_rad**2 + motion.sigma_phi_rad**2) / 2.0 + sigma_turbulence2


def _local_outage_probability(theta_fov_rad: float, sigma_o2: float) -> float:
    return math.exp(-theta_fov_rad**2 / (2.0 * sigma_o2)) if sigma_o2 else 0.0


def _local_beam_radius(
    beam_waist_m: float,
    wavelength_m: float,
    link_length_m: float,
    radius_of_curvature_m: float = math.inf,
) -> tuple[float, float]:
    rayleigh_range_m = math.pi * beam_waist_m**2 / wavelength_m
    wave_number = 2.0 * math.pi / wavelength_m
    focusing = (
        1.0
        if math.isinf(radius_of_curvature_m)
        else 1.0 - link_length_m / radius_of_curvature_m
    )
    return (
        beam_waist_m
        * math.sqrt(
            focusing**2
            + (2.0 * link_length_m / (wave_number * beam_waist_m**2)) ** 2
        ),
        rayleigh_range_m,
    )


def _hv_profile(height_m: float | np.ndarray, wind_m_per_s: float, ground_cn2: float):
    height = np.asarray(height_m, dtype=float)
    return (
        0.00594 * (wind_m_per_s / 27.0) ** 2 * (1.0e-5 * height) ** 10 * np.exp(-height / 1000.0)
        + 2.7e-16 * np.exp(-height / 1500.0)
        + ground_cn2 * np.exp(-height / 100.0)
    )


def _gauss_integral(fn, lower: float, upper: float, order: int = 256) -> float:
    nodes, weights = np.polynomial.legendre.leggauss(order)
    center = (lower + upper) / 2.0
    half = (upper - lower) / 2.0
    values = np.asarray(fn(center + half * nodes), dtype=float)
    return float(half * np.dot(weights, values))


def _local_scintillation(
    h_uav_m: float,
    h_hap_m: float,
    wavelength_m: float,
    zenith_angle_rad: float,
    wind_m_per_s: float,
    ground_cn2: float,
    receiver_diameter_m: float,
) -> dict[str, float]:
    """NumPy-only equivalent of the repository HV finite-aperture helper."""

    secant = 1.0 / math.cos(zenith_angle_rad)
    wave_number = 2.0 * math.pi / wavelength_m
    profile = lambda h: _hv_profile(h, wind_m_per_s, ground_cn2)
    rytov = _gauss_integral(
        lambda h: profile(h) * (h - h_uav_m) ** (5.0 / 6.0), h_uav_m, h_hap_m
    )
    numerator = _gauss_integral(lambda h: profile(h) * h**2, h_uav_m, h_hap_m)
    denominator = _gauss_integral(
        lambda h: profile(h) * h ** (5.0 / 6.0), h_uav_m, h_hap_m
    )
    sigma_r0_squared = 2.25 * wave_number ** (7.0 / 6.0) * secant ** (11.0 / 6.0) * rytov
    phi_m = (numerator / denominator) ** (6.0 / 7.0)
    aperture_factor = (
        1.0
        + 1.11
        * (receiver_diameter_m**2 / (wavelength_m * phi_m * secant)) ** (7.0 / 6.0)
    ) ** -1.0
    return {
        "sigma_R0_squared": sigma_r0_squared,
        "Phi_m": phi_m,
        "A_ap": aperture_factor,
        "v_sc": aperture_factor * sigma_r0_squared,
    }


def _derive(
    config: dict, tau_zen_override: float | None = None
) -> tuple[dict[str, float], dict[str, object]]:
    geometry_cfg = config["geometry"]
    optics = config["optics"]
    turbulence = config["turbulence_profile"]
    pointing_cfg = config["pointing"]
    aoa_cfg = config["aoa"]

    Geometry, geometry_repo = _repo_or_local(
        "geometry:LinkGeometry",
        LocalGeometry,
    )
    geometry = Geometry(
        float(geometry_cfg["h_hap_m"]),
        float(geometry_cfg["h_uav_m"]),
        float(geometry_cfg["zenith_angle_rad"]),
    )
    link_length_m = float(geometry.link_length_m)
    expected_length = (
        float(geometry_cfg["h_hap_m"]) - float(geometry_cfg["h_uav_m"])
    ) / math.cos(float(geometry_cfg["zenith_angle_rad"]))
    if not math.isclose(link_length_m, expected_length, rel_tol=0.0, abs_tol=1.0e-9):
        raise ValueError(f"Derived L={link_length_m} disagrees with expected {expected_length}.")

    tau_zen = optics.get("tau_zen") if tau_zen_override is None else tau_zen_override
    if tau_zen is None:
        raise ValueError(
            "Atmospheric scenario must be selected: provide --tau-zen explicitly "
            "or set an author-approved optics.tau_zen."
        )
    atmospheric, atmospheric_repo = _repo_or_local(
        "atmospheric_loss:atmospheric_transmittance_from_tau_zen",
        _local_atmospheric_transmittance,
    )
    eta_atm = float(
        atmospheric(
            link_length_m,
            float(tau_zen),
            float(geometry_cfg["zenith_angle_rad"]),
        )
    )

    wavelength_m = float(optics["wavelength_m"])
    theta_div_rad = float(optics["theta_div_rad"])
    beam_waist_m = 2.0 * wavelength_m / (math.pi * theta_div_rad)
    receiver_diameter_m = 2.0 * float(optics["aperture_radius_m"])
    hv_repo = _REPOSITORY.get("scintillation")
    hv_function = getattr(hv_repo, "hufnagel_valley_scintillation", None)
    hv_profile_function = getattr(hv_repo, "hufnagel_valley_cn2", _hv_profile)
    if hv_function is not None:
        scintillation = hv_function(
            float(geometry_cfg["h_uav_m"]),
            float(geometry_cfg["h_hap_m"]),
            wavelength_m,
            float(geometry_cfg["zenith_angle_rad"]),
            float(turbulence["wind_speed_m_per_s"]),
            float(turbulence["cn2_ground_m_minus_two_thirds"]),
            receiver_diameter_m,
        )
        scintillation_repo = True
    else:
        scintillation = _local_scintillation(
            float(geometry_cfg["h_uav_m"]),
            float(geometry_cfg["h_hap_m"]),
            wavelength_m,
            float(geometry_cfg["zenith_angle_rad"]),
            float(turbulence["wind_speed_m_per_s"]),
            float(turbulence["cn2_ground_m_minus_two_thirds"]),
            receiver_diameter_m,
        )
        scintillation_repo = False

    beam_radius, rayleigh_range = _repo_or_local(
        "pointing_error:gaussian_beam_radius", _local_beam_radius
    )[0](
        beam_waist_m,
        wavelength_m,
        link_length_m,
        float(optics["radius_of_curvature_m"]),
    )
    beam_repo = _REPOSITORY.get("pointing_error") is not None

    h_low = float(geometry_cfg["h_uav_m"])
    h_high = float(geometry_cfg["h_hap_m"])
    span = h_high - h_low
    cn2 = lambda h: hv_profile_function(
        h,
        float(turbulence["wind_speed_m_per_s"]),
        float(turbulence["cn2_ground_m_minus_two_thirds"]),
    )
    wave_number = 2.0 * math.pi / wavelength_m
    secant = 1.0 / math.cos(float(geometry_cfg["zenith_angle_rad"]))
    lambda_beam = 2.0 * link_length_m / (wave_number * beam_radius**2)
    gd_integral = _gauss_integral(
        lambda h: cn2(h) * ((h - h_low) / span) ** (5.0 / 3.0), h_low, h_high
    )
    g_d = (
        4.35
        * lambda_beam ** (5.0 / 6.0)
        * wave_number ** (7.0 / 6.0)
        * span ** (5.0 / 6.0)
        * secant ** (11.0 / 6.0)
        * gd_integral
    )
    beam_radius_turbulent = beam_radius * math.sqrt(1.0 + g_d)

    # Eq. (32) uses receiver diameter; the configuration stores radius.
    nu = math.sqrt(math.pi) * receiver_diameter_m / (2.0 * math.sqrt(2.0) * beam_radius)
    a0 = math.erf(nu) ** 2
    omega_leq_squared = (
        beam_radius_turbulent**2
        * math.sqrt(math.pi)
        * math.erf(nu)
        / (2.0 * nu * math.exp(-nu**2))
    )
    omega_leq = math.sqrt(omega_leq_squared)

    Motion, motion_repo = _repo_or_local("turbulence:UavMotion", LocalMotion)
    sigma_h_m = float(pointing_cfg["sigma_h_m"])
    sigma_o_rad = float(aoa_cfg["sigma_o_rad"])
    motion = Motion(
        sigma_x_m=sigma_h_m,
        sigma_y_m=sigma_h_m,
        sigma_z_m=0.0,
        sigma_theta_rad=sigma_o_rad,
        sigma_phi_rad=sigma_o_rad,
        sigma_psi_rad=0.0,
    )
    uav_variance, uav_repo = _repo_or_local(
        "turbulence:uav_translational_variance_m2", _local_uav_translational_variance
    )
    hap_variance, hap_repo = _repo_or_local(
        "turbulence:hap_angular_displacement_variance_m2", _local_hap_displacement_variance
    )
    sigma_h_squared = float(uav_variance(motion))
    sigma_hap_displacement_squared = float(
        hap_variance(
            link_length_m,
            float(pointing_cfg["theta_jt_rad"]),
            str(pointing_cfg["hap_angular_jitter_convention"]),
        )
        if hap_repo
        else hap_variance(link_length_m, float(pointing_cfg["theta_jt_rad"]))
    )
    sigma_jt_squared = sigma_h_squared + sigma_hap_displacement_squared
    sigma_jt = math.sqrt(sigma_jt_squared)
    rho_x = float(pointing_cfg["boresight_x_m"])
    rho_y = float(pointing_cfg["boresight_y_m"])
    rho = math.hypot(rho_x, rho_y)
    chi = omega_leq / (2.0 * sigma_jt)
    chi_squared = chi**2

    aoa_variance, aoa_repo = _repo_or_local("aoa:aoa_variance_rad2", _local_aoa_variance)
    if aoa_repo:
        sigma_o_squared = float(
            aoa_variance(
                motion,
                sigma_turb_AoA2=float(aoa_cfg["sigma_turb_AoA2_rad2"]),
                model=str(aoa_cfg["model"]),
                provenance=str(aoa_cfg["provenance"]),
            )
        )
    else:
        sigma_o_squared = float(aoa_variance(motion, float(aoa_cfg["sigma_turb_AoA2_rad2"])))
    if not math.isclose(sigma_o_squared, sigma_o_rad**2, rel_tol=0.0, abs_tol=1.0e-18):
        raise ValueError("Derived AoA variance disagrees with the approved sigma_o input.")
    outage, outage_repo = _repo_or_local(
        "aoa:aoa_outage_probability", _local_outage_probability
    )
    p_out = float(outage(float(aoa_cfg["theta_fov_rad"]), sigma_o_squared))
    p_in = 1.0 - p_out

    sigma_x_squared = float(scintillation["v_sc"]) / 4.0
    log_c1 = rho**2 / sigma_jt_squared + 2.0 * sigma_x_squared * chi_squared * (1.0 + chi_squared)
    c2 = (
        32.0 * rho**2 * sigma_jt_squared / omega_leq**4 + 8.0 * sigma_x_squared
    ) ** -0.5
    mu = 6.0 * rho**2 / omega_leq**2 + 2.0 * sigma_x_squared * (1.0 + 2.0 * chi_squared)
    scale = a0 * eta_atm

    params = {
        "h_HAP_m": float(geometry_cfg["h_hap_m"]),
        "h_UAV_m": float(geometry_cfg["h_uav_m"]),
        "zeta_rad": float(geometry_cfg["zenith_angle_rad"]),
        "lambda_m": wavelength_m,
        "F0_m": float(optics["radius_of_curvature_m"]),
        "v_wind_m_per_s": float(turbulence["wind_speed_m_per_s"]),
        "cn2_ground_m_minus_two_thirds": float(
            turbulence["cn2_ground_m_minus_two_thirds"]
        ),
        "sigma_h_m": sigma_h_m,
        "theta_jt_rad": float(pointing_cfg["theta_jt_rad"]),
        "rho_m": rho,
        "epsilon_ch_snu": float(
            config.get("excess_noise_distribution", {}).get("epsilon_ch_snu", 0.0186)
        ),
        "L": link_length_m,
        "D_r": receiver_diameter_m,
        "theta_div_rad": theta_div_rad,
        "omega_0": beam_waist_m,
        "eta_atm": eta_atm,
        "tau_zen": float(tau_zen),
        "radius_of_curvature_m": float(optics["radius_of_curvature_m"]),
        "sigma_R0_squared": float(scintillation["sigma_R0_squared"]),
        "AA": float(scintillation["A_ap"]),
        "sigma_R_squared": float(scintillation["v_sc"]),
        "sigma_X_squared": sigma_x_squared,
        "v_sc": float(scintillation["v_sc"]),
        "omega_L": float(beam_radius),
        "rayleigh_range_m": float(rayleigh_range),
        "G_d": float(g_d),
        "omega_L_e": float(beam_radius_turbulent),
        "A0": float(a0),
        "omega_L_eq": float(omega_leq),
        "rho_x": rho_x,
        "rho_y": rho_y,
        "rho": rho,
        "sigma_h": math.sqrt(sigma_h_squared),
        "L_sigma_hap": link_length_m * float(pointing_cfg["theta_jt_rad"]),
        "sigma_jt": sigma_jt,
        "chi": chi,
        "chi_squared": chi_squared,
        "log_C1": log_c1,
        "C1": math.exp(log_c1),
        "C2": c2,
        "mu": mu,
        "sigma_o": math.sqrt(sigma_o_squared),
        "sigma_o_squared": sigma_o_squared,
        "theta_FOV": float(aoa_cfg["theta_fov_rad"]),
        "p_out": p_out,
        "p_in": p_in,
        "A0_eta_atm": scale,
        "gd_integral": gd_integral,
    }
    backends = {
        "geometry": geometry_repo,
        "atmospheric_loss": atmospheric_repo,
        "scintillation": scintillation_repo,
        "beam_radius": beam_repo,
        "uav_motion": motion_repo,
        "uav_variance": uav_repo,
        "hap_variance": hap_repo,
        "aoa_variance": aoa_repo,
        "aoa_outage": outage_repo,
    }
    return params, backends


def _log_erfc_scalar(value: float) -> float:
    if value < 8.0:
        return math.log(math.erfc(value))
    inverse_square = 1.0 / (value * value)
    correction = (
        1.0
        - 0.5 * inverse_square
        + 0.75 * inverse_square**2
        - 1.875 * inverse_square**3
        + 6.5625 * inverse_square**4
    )
    return -value**2 - math.log(value) - 0.5 * math.log(math.pi) + math.log(correction)


def _log_erfc(values: float | np.ndarray) -> float | np.ndarray:
    array = np.asarray(values, dtype=float)
    result = np.fromiter(
        (_log_erfc_scalar(float(value)) for value in array.reshape(-1)),
        dtype=float,
        count=array.size,
    ).reshape(array.shape)
    return float(result) if array.ndim == 0 else result


def make_active_pdf(params: dict[str, float]):
    q = params["chi_squared"]
    log_scale = math.log(params["A0_eta_atm"])
    log_prefactor = math.log(q / 2.0) + params["log_C1"] - q * log_scale
    c2 = params["C2"]
    mu = params["mu"]

    def log_pdf_from_log_t(log_t: float | np.ndarray) -> float | np.ndarray:
        log_t_array = np.asarray(log_t, dtype=float)
        z = c2 * (log_t_array - log_scale + mu)
        result = log_prefactor + (q - 1.0) * log_t_array + _log_erfc(z)
        return float(result) if log_t_array.ndim == 0 else result

    def log_pdf(t: float | np.ndarray) -> float | np.ndarray:
        values = np.asarray(t, dtype=float)
        if np.any(values <= 0.0) or np.any(~np.isfinite(values)):
            raise ValueError("Eq. (51) requires finite t > 0.")
        return log_pdf_from_log_t(np.log(values))

    def pdf(t: float | np.ndarray) -> float | np.ndarray:
        values = np.exp(log_pdf(t))
        if np.any(~np.isfinite(values)) or np.any(values < 0.0):
            raise FloatingPointError("Eq. (51) produced a non-finite or negative density.")
        return values

    return log_pdf_from_log_t, log_pdf, pdf


def _integrate_log_density(log_pdf_from_log_t, lower: float, upper: float) -> float:
    """Convergence-controlled Gauss--Legendre integration in log(t)."""

    # ponytail: fixed-panel refinement is the small dependency-free fallback;
    # increase panels before adding a new numerical-integration dependency.
    previous = None
    nodes, weights = np.polynomial.legendre.leggauss(128)
    for panel_count in (16, 32, 64, 128):
        edges = np.linspace(lower, upper, panel_count + 1)
        total = 0.0
        for left, right in zip(edges[:-1], edges[1:]):
            center = (left + right) / 2.0
            half = (right - left) / 2.0
            log_t = center + half * nodes
            log_integrand = np.asarray(log_pdf_from_log_t(log_t), dtype=float) + log_t
            if np.any(~np.isfinite(log_integrand)):
                raise FloatingPointError("Non-finite log-integrand during normalization.")
            total += half * float(np.dot(weights, np.exp(log_integrand)))
        if previous is not None and abs(total - previous) <= 1.0e-8 * max(1.0, abs(total)):
            return total
        previous = total
    raise RuntimeError(f"Log-domain quadrature did not converge: last values {previous}, {total}.")


def _print_table(params: dict[str, float]) -> None:
    units = {
        "L": "m",
        "D_r": "m",
        "theta_div_rad": "rad",
        "omega_0": "m",
        "eta_atm": "dimensionless",
        "sigma_R0_squared": "dimensionless",
        "AA": "dimensionless",
        "sigma_R_squared": "dimensionless",
        "sigma_X_squared": "dimensionless",
        "v_sc": "dimensionless",
        "omega_L": "m",
        "rayleigh_range_m": "m",
        "G_d": "dimensionless",
        "omega_L_e": "m",
        "A0": "dimensionless",
        "omega_L_eq": "m",
        "rho_x": "m",
        "rho_y": "m",
        "rho": "m",
        "sigma_h": "m",
        "L_sigma_hap": "m",
        "sigma_jt": "m",
        "chi": "dimensionless",
        "chi_squared": "dimensionless",
        "C1": "dimensionless",
        "C2": "dimensionless",
        "mu": "dimensionless",
        "sigma_o": "rad",
        "sigma_o_squared": "rad^2",
        "theta_FOV": "rad",
        "p_out": "dimensionless",
        "p_in": "dimensionless",
        "A0_eta_atm": "dimensionless",
    }
    print("\nDerived Eq. (62) parameters")
    for name, unit in units.items():
        print(f"{name:22s} = {params[name]:.16g}  [{unit}]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--sample-count", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--tau-zen", type=float, default=None)
    args = parser.parse_args()

    config = load_yaml(args.config)
    params, backends = _derive(config, args.tau_zen)
    _print_table(params)
    print("\nRepository helper reuse")
    for name, reused in backends.items():
        print(f"{name:22s}: {'reused' if reused else 'local Eq. (62) fallback'}")
    for note in _BACKEND_NOTES:
        print(f"NOTE: {note}")

    checks = {
        "L > 0": params["L"] > 0.0,
        "0 < eta_atm <= 1": 0.0 < params["eta_atm"] <= 1.0,
        "sigma_X_squared > 0": params["sigma_X_squared"] > 0.0,
        "0 < A0 <= 1": 0.0 < params["A0"] <= 1.0,
        "omega_L_eq > 0": params["omega_L_eq"] > 0.0,
        "sigma_jt > 0": params["sigma_jt"] > 0.0,
        "chi > 0": params["chi"] > 0.0,
        "C2 > 0": params["C2"] > 0.0,
        "0 <= p_out <= 1": 0.0 <= params["p_out"] <= 1.0,
        "p_in + p_out = 1": abs(params["p_in"] + params["p_out"] - 1.0) < 1.0e-12,
        "L matches slant geometry": abs(
            params["L"]
            - (float(config["geometry"]["h_hap_m"])
               - float(config["geometry"]["h_uav_m"]))
            / math.cos(float(config["geometry"]["zenith_angle_rad"]))
        ) < 1.0e-9,
    }
    if not all(checks.values()):
        raise AssertionError(f"Sanity checks failed: {[name for name, ok in checks.items() if not ok]}")

    log_pdf_from_log_t, log_pdf, active_pdf = make_active_pdf(params)
    active_integral = _integrate_log_density(log_pdf_from_log_t, -80.0, 20.0)
    inner_integral = _integrate_log_density(log_pdf_from_log_t, -60.0, 10.0)
    normalization_error = abs(active_integral - 1.0)
    if abs(active_integral - inner_integral) > 1.0e-6:
        raise AssertionError(
            f"Normalization bounds disagree: wide={active_integral}, inner={inner_integral}"
        )
    raw_log_pdf_from_log_t = lambda log_t: math.log(params["p_in"]) + log_pdf_from_log_t(log_t)
    continuous_raw_mass = _integrate_log_density(raw_log_pdf_from_log_t, -80.0, 20.0)
    total_raw_mass = params["p_out"] + continuous_raw_mass
    total_mass_error = abs(total_raw_mass - 1.0)
    if normalization_error > 1.0e-5 or abs(continuous_raw_mass - params["p_in"]) > 1.0e-5 or total_mass_error > 1.0e-5:
        raise AssertionError(
            f"Eq. (62) mass check failed: active={active_integral}, "
            f"continuous={continuous_raw_mass}, total={total_raw_mass}"
        )

    sample_count = int(config["diagnostics"]["sample_count"] if args.sample_count is None else args.sample_count)
    seed = int(config["diagnostics"]["seed"] if args.seed is None else args.seed)
    if sample_count <= 0:
        raise ValueError("sample_count must be positive.")
    rng = np.random.default_rng(seed)
    variance = params["v_sc"]
    h_sc = np.exp(rng.normal(-0.5 * variance, math.sqrt(variance), sample_count))
    x_jitter = params["rho_x"] + rng.normal(0.0, params["sigma_jt"], sample_count)
    y_jitter = params["rho_y"] + rng.normal(0.0, params["sigma_jt"], sample_count)
    h_p = params["A0"] * np.exp(
        -2.0 * (x_jitter**2 + y_jitter**2) / params["omega_L_eq"] ** 2
    )
    x_mc = params["eta_atm"] * h_sc * h_p
    aoa_x = rng.normal(0.0, params["sigma_o"], sample_count)
    aoa_y = rng.normal(0.0, params["sigma_o"], sample_count)
    aoa_gate = (np.hypot(aoa_x, aoa_y) <= params["theta_FOV"]).astype(np.int8)
    t_raw_mc = aoa_gate * x_mc
    empirical_outage = float(np.mean(aoa_gate == 0))
    empirical_active = float(np.mean(aoa_gate == 1))
    outage_error = abs(empirical_outage - params["p_out"])
    active_error = abs(empirical_active - params["p_in"])
    standard_error = math.sqrt(params["p_out"] * params["p_in"] / sample_count)
    mc_tolerance = max(5.0e-3, 6.0 * standard_error)
    if outage_error > mc_tolerance or active_error > mc_tolerance:
        raise AssertionError(
            f"Monte Carlo AoA check failed: outage_error={outage_error}, active_error={active_error}"
        )

    plot_low = max(float(np.quantile(x_mc, 1.0e-4)) * 0.5, params["A0_eta_atm"] * 1.0e-8)
    plot_high = max(float(np.quantile(x_mc, 0.999)) * 1.05, params["A0_eta_atm"] * 1.1)
    t_grid = np.geomspace(plot_low, plot_high, 2400)
    active_values = np.asarray(active_pdf(t_grid), dtype=float)
    raw_values = params["p_in"] * active_values
    if np.any(~np.isfinite(active_values)) or np.any(active_values < 0.0):
        raise FloatingPointError("Plotted Eq. (51) curve is not finite and nonnegative.")

    mode_grid = np.geomspace(params["A0_eta_atm"] * 1.0e-10, plot_high, 12000)
    mode_active_values = np.asarray(active_pdf(mode_grid), dtype=float)
    active_mode_index = int(np.argmax(mode_active_values))
    raw_mode_index = int(np.argmax(params["p_in"] * mode_active_values))
    if active_mode_index != raw_mode_index:
        raise AssertionError("AoA scaling shifted the analytical PDF mode.")
    active_mode = float(mode_grid[active_mode_index])
    raw_mode = float(mode_grid[raw_mode_index])

    histogram_edges = np.geomspace(plot_low, plot_high, 80)
    active_hist, _ = np.histogram(x_mc, bins=histogram_edges, density=True)
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    ax.stairs(active_hist, histogram_edges, color="0.45", linewidth=1.0, alpha=0.75, label="MC $X$ (conditional density)")
    ax.stairs(params["p_in"] * active_hist, histogram_edges, color="0.25", linewidth=1.0, alpha=0.75, linestyle="--", label="MC positive $T_{raw}$ (mass $p_{in}$)")
    ax.plot(t_grid, active_values, color="tab:blue", linewidth=2.0, label=r"Analytical $f_X(t)$")
    ax.plot(t_grid, raw_values, color="tab:orange", linewidth=2.0, linestyle="--", label=r"Analytical $p_{in}f_X(t)$")
    ax.axvline(params["A0_eta_atm"], color="tab:green", linestyle=":", linewidth=1.5, label=r"reference $A_0\eta_{atm}$")
    ax.set_xlim(0.0, plot_high)
    ax.set_xlabel(r"Raw power transmittance $t=T_{raw}$")
    ax.set_ylabel("Continuous probability density")
    ax.set_title("Manuscript Eq. (62): raw HAP--UAV transmittance PDF")
    ax.grid(alpha=0.25)

    ax_mass = ax.twinx()
    ax_mass.vlines(0.0, 0.0, params["p_out"], color="tab:red", linewidth=3.0, label=r"outage mass $P(T_{raw}=0)=p_{out}$")
    ax_mass.scatter([0.0], [params["p_out"]], color="tab:red", s=42, zorder=4)
    ax_mass.set_ylim(0.0, 1.0)
    ax_mass.set_ylabel("Discrete probability mass")
    handles, labels = ax.get_legend_handles_labels()
    mass_handles, mass_labels = ax_mass.get_legend_handles_labels()
    ax.legend(handles + mass_handles, labels + mass_labels, loc="upper right", fontsize=8)
    ax.text(
        0.02,
        0.98,
        f"wide integral f_X={active_integral:.9f}\n"
        f"p_out={params['p_out']:.6f}; q_0.999={np.quantile(x_mc, 0.999):.6g}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox={"boxstyle": "round", "alpha": 0.12},
    )
    fig.tight_layout()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    png_path = args.output_dir / "eq62_raw_transmittance_pdf.png"
    pdf_path = args.output_dir / "eq62_raw_transmittance_pdf.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print("\nNumerical validation")
    print(f"active_integral       = {active_integral:.12f}")
    print(f"active_abs_error      = {normalization_error:.3e}")
    print(f"continuous_raw_mass   = {continuous_raw_mass:.12f}")
    print(f"outage_mass           = {params['p_out']:.12f}")
    print(f"total_raw_mass        = {total_raw_mass:.12f}")
    print(f"total_mass_error      = {total_mass_error:.3e}")
    print(f"MC empirical outage   = {empirical_outage:.12f} (error {outage_error:.3e})")
    print(f"MC empirical active   = {empirical_active:.12f} (error {active_error:.3e})")
    print(f"MC max X (no clipping)= {float(np.max(x_mc)):.12g}")
    print(f"active mode           = {active_mode:.12g}")
    print(f"raw-continuous mode   = {raw_mode:.12g}")
    print(f"same mode index       = {active_mode_index == raw_mode_index}")
    print(f"saved PNG             = {png_path.resolve()}")
    print(f"saved PDF             = {pdf_path.resolve()}")
    print("physical conditioning = NOT RUN")
    print("security/SKR          = NOT RUN")


if __name__ == "__main__":
    main()
