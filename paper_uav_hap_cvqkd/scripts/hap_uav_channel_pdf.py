"""Standalone TCP-style HAP--UAV FSO channel PDF diagnostic.

This script implements the numerical scenario supplied with this task exactly.
It is intentionally separate from ``configs/default.yaml`` and the production
channel sampler because those bind a different manuscript scenario and a
different generalized pointing law.  It is a channel-only diagnostic: it does
not train a model, evaluate SKR/security, or modify any active configuration.

The baseline has zero deterministic boresight error.  In that case the stated
Rician pointing model makes ``log(X)`` a normal-minus-exponential variable;
the resulting closed-form active PDF is algebraically identical to the
specified one-dimensional convolution.  The script also evaluates the
transformed convolution by adaptive quadrature at representative points as an
independent check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.channel.atmospheric_loss import atmospheric_transmittance

try:
    import scipy as _scipy
    from scipy.integrate import quad as _scipy_quad
    from scipy.optimize import brentq as _scipy_brentq
    from scipy.special import i0e as _scipy_i0e
    from scipy.special import log_ndtr as _scipy_log_ndtr
    from scipy.special import ndtri as _scipy_ndtri

    SCIPY_VERSION = _scipy.__version__
except Exception:  # pragma: no cover - depends on local application control.
    _scipy_quad = _scipy_brentq = _scipy_i0e = _scipy_log_ndtr = _scipy_ndtri = None
    SCIPY_VERSION = "unavailable; in-script adaptive Gauss--Legendre fallback"


@dataclass(frozen=True)
class Scenario:
    lambda_m: float = 1.55e-6
    h_hap_m: float = 2.0e4
    h_uav_m: float = 1.0e3
    zeta_rad: float = math.pi / 6.0
    wind_m_per_s: float = 21.0
    cn2_ground_m_minus_two_thirds: float = 5.0e-14
    visibility_km: float = 20.0
    aperture_radius_m: float = 0.04
    theta_div_rad: float = 223e-6
    sigma_h_m: float = 1.0
    theta_jt_rad: float = 15.61e-6
    rho_m: float = 0.0
    sigma_o_rad: float = 1.5e-3
    theta_fov_rad: float = 6.25e-3
    epsilon_ch_snu: float = 0.0186

    @property
    def link_length_m(self) -> float:
        return (self.h_hap_m - self.h_uav_m) / math.cos(self.zeta_rad)

    @property
    def receiver_diameter_m(self) -> float:
        return 2.0 * self.aperture_radius_m

    @property
    def omega_0_m(self) -> float:
        return 2.0 * self.lambda_m / (math.pi * self.theta_div_rad)

    @property
    def eta_atm(self) -> float:
        return atmospheric_transmittance(
            self.link_length_m, self.visibility_km, self.lambda_m
        )


SCENARIO = Scenario()
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "results" / "tcp_style_hap_uav_channel_pdf"
LOG_TINY = math.log(np.finfo(float).tiny)
_NORMAL = NormalDist()
_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(24)


def _fallback_log_ndtr(value: float | np.ndarray) -> float | np.ndarray:
    """Stable log Phi(x), including the far tail needed for P(X>1)."""

    x = np.asarray(value, dtype=float)
    result = np.empty_like(x)
    lower = x < -8.0
    if np.any(lower):
        y = -x[lower]
        inverse_square = 1.0 / y**2
        series = 1.0 - inverse_square + 3.0 * inverse_square**2 - 15.0 * inverse_square**3 + 105.0 * inverse_square**4
        result[lower] = -0.5 * y**2 - np.log(y) - 0.5 * math.log(2.0 * math.pi) + np.log(series)
    if np.any(~lower):
        erfc_values = np.vectorize(math.erfc)(-x[~lower] / math.sqrt(2.0))
        result[~lower] = np.log(0.5 * erfc_values)
    return float(result) if np.ndim(value) == 0 else result


def log_ndtr(value: float | np.ndarray) -> float | np.ndarray:
    return _scipy_log_ndtr(value) if _scipy_log_ndtr is not None else _fallback_log_ndtr(value)


def i0e(value: float | np.ndarray) -> float | np.ndarray:
    if _scipy_i0e is not None:
        return _scipy_i0e(value)
    values = np.asarray(value, dtype=float)
    result = np.i0(values) * np.exp(-np.abs(values))
    return float(result) if np.ndim(value) == 0 else result


def ndtri(probability: float) -> float:
    return float(_scipy_ndtri(probability)) if _scipy_ndtri is not None else _NORMAL.inv_cdf(probability)


def _fallback_finite_quad(
    fn: Callable[[float], float], lower: float, upper: float, epsabs: float, epsrel: float, depth: int = 18
) -> tuple[float, float]:
    def panel(a: float, b: float) -> float:
        center = (a + b) / 2.0
        half = (b - a) / 2.0
        return half * float(sum(weight * float(fn(center + half * node)) for node, weight in zip(_GL_NODES, _GL_WEIGHTS)))

    def recurse(a: float, b: float, whole: float, absolute: float, remaining: int) -> tuple[float, float]:
        middle = (a + b) / 2.0
        split = panel(a, middle) + panel(middle, b)
        error = abs(split - whole)
        if remaining == 0 or error <= max(absolute, epsrel * abs(split)):
            return split, error
        left, left_error = recurse(a, middle, panel(a, middle), absolute / 2.0, remaining - 1)
        right, right_error = recurse(middle, b, panel(middle, b), absolute / 2.0, remaining - 1)
        return left + right, left_error + right_error

    whole = panel(lower, upper)
    return recurse(lower, upper, whole, epsabs, depth)


def _fallback_quad(
    fn: Callable[[float], float], lower: float, upper: float, epsabs: float, epsrel: float
) -> tuple[float, float]:
    if math.isfinite(lower) and math.isfinite(upper):
        return _fallback_finite_quad(fn, lower, upper, epsabs, epsrel)
    if math.isfinite(lower) and math.isinf(upper):
        return _fallback_finite_quad(
            lambda t: float(fn(lower + t / (1.0 - t))) / (1.0 - t) ** 2,
            0.0,
            1.0,
            epsabs,
            epsrel,
        )
    if math.isinf(lower) and math.isfinite(upper):
        return _fallback_finite_quad(
            lambda t: float(fn(upper - t / (1.0 - t))) / (1.0 - t) ** 2,
            0.0,
            1.0,
            epsabs,
            epsrel,
        )
    return _fallback_finite_quad(
        lambda t: float(fn(math.tan(math.pi * (t - 0.5)))) * math.pi / math.cos(math.pi * (t - 0.5)) ** 2,
        0.0,
        1.0,
        epsabs,
        epsrel,
    )


def brentq(fn: Callable[[float], float], lower: float, upper: float, xtol: float, rtol: float) -> float:
    if _scipy_brentq is not None:
        return float(_scipy_brentq(fn, lower, upper, xtol=xtol, rtol=rtol))
    f_lower, f_upper = fn(lower), fn(upper)
    if f_lower == 0.0:
        return lower
    if f_upper == 0.0:
        return upper
    if f_lower * f_upper > 0.0:
        raise ValueError("Bisection interval does not bracket a root.")
    for _ in range(250):
        middle = (lower + upper) / 2.0
        f_middle = fn(middle)
        if f_middle == 0.0 or abs(upper - lower) <= xtol + rtol * abs(middle):
            return middle
        if f_lower * f_middle < 0.0:
            upper, f_upper = middle, f_middle
        else:
            lower, f_lower = middle, f_middle
    return (lower + upper) / 2.0


def _quad(fn: Callable[[float], float], lower: float, upper: float) -> tuple[float, float]:
    """Adaptive quadrature with tolerances suitable for diagnostic checks."""

    if _scipy_quad is not None:
        return _scipy_quad(fn, lower, upper, epsabs=1.0e-11, epsrel=1.0e-10, limit=300)
    return _fallback_quad(fn, lower, upper, epsabs=1.0e-11, epsrel=1.0e-10)


def _finite_quad(fn: Callable[[float], float], lower: float, upper: float) -> tuple[float, float]:
    if _scipy_quad is not None:
        return _scipy_quad(fn, lower, upper, epsabs=1.0e-20, epsrel=2.0e-12, limit=300)
    return _fallback_quad(fn, lower, upper, epsabs=1.0e-20, epsrel=2.0e-12)


def _safe_exp(value: np.ndarray | float) -> np.ndarray | float:
    array = np.asarray(value, dtype=float)
    with np.errstate(under="ignore", over="ignore", invalid="ignore"):
        result = np.exp(array)
    if np.ndim(value) == 0:
        return float(result)
    return result


def _log1mexp(log_x: float) -> float:
    """Return log(1-exp(log_x)) for log_x <= 0 without cancellation."""

    if log_x > 1.0e-13:
        raise ValueError(f"Expected log_x <= 0, received {log_x!r}.")
    log_x = min(log_x, 0.0)
    if log_x > -math.log(2.0):
        return math.log(-math.expm1(log_x))
    return math.log1p(-math.exp(log_x))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cn2_hufnagel_valley(h_m: float | np.ndarray, p: Scenario = SCENARIO) -> float | np.ndarray:
    """The Hufnagel--Valley profile specified in the task."""

    h = np.asarray(h_m, dtype=float)
    value = (
        0.00594
        * (p.wind_m_per_s / 27.0) ** 2
        * (1.0e-5 * h) ** 10
        * np.exp(-h / 1000.0)
        + 2.7e-16 * np.exp(-h / 1500.0)
        + p.cn2_ground_m_minus_two_thirds * np.exp(-h / 100.0)
    )
    return float(value) if np.ndim(h_m) == 0 else value


def derive_parameters(p: Scenario = SCENARIO) -> dict[str, float]:
    sec_zeta = 1.0 / math.cos(p.zeta_rad)
    link_from_geometry = (p.h_hap_m - p.h_uav_m) * sec_zeta

    wave_number = 2.0 * math.pi / p.lambda_m
    h_low, h_high = p.h_uav_m, p.h_hap_m
    vertical_span = h_high - h_low
    rytov_integral, rytov_quad_error = _finite_quad(
        lambda h: cn2_hufnagel_valley(h, p) * (h - h_low) ** (5.0 / 6.0),
        h_low,
        h_high,
    )
    sigma_r0_sq = (
        2.25
        * wave_number ** (7.0 / 6.0)
        * sec_zeta ** (11.0 / 6.0)
        * rytov_integral
    )
    aperture_numerator, aperture_numerator_error = _finite_quad(
        lambda h: cn2_hufnagel_valley(h, p) * h**2,
        h_low,
        h_high,
    )
    aperture_denominator, aperture_denominator_error = _finite_quad(
        lambda h: cn2_hufnagel_valley(h, p) * h ** (5.0 / 6.0),
        h_low,
        h_high,
    )
    phi = (aperture_numerator / aperture_denominator) ** (6.0 / 7.0)
    aperture_factor = (
        1.0
        + 1.11
        * (p.receiver_diameter_m**2 / (p.lambda_m * phi * sec_zeta)) ** (7.0 / 6.0)
    ) ** -1.0
    sigma_rd_sq = aperture_factor * sigma_r0_sq
    v_sc = sigma_rd_sq

    omega_0_check = 2.0 * p.lambda_m / (math.pi * p.theta_div_rad)
    omega_0_relative_difference = (omega_0_check - p.omega_0_m) / p.omega_0_m
    # F_0=infinity: the focusing term is exactly zero.
    omega_l = p.omega_0_m * math.sqrt(
        1.0 + (2.0 * p.link_length_m / (wave_number * p.omega_0_m**2)) ** 2
    )
    lambda_beam = 2.0 * p.link_length_m / (wave_number * omega_l**2)
    mu2, mu2_quad_error = _finite_quad(
        lambda h: cn2_hufnagel_valley(h, p) * ((h - h_low) / vertical_span) ** (5.0 / 3.0),
        h_low,
        h_high,
    )
    g_d = (
        4.35
        * lambda_beam ** (5.0 / 6.0)
        * wave_number ** (7.0 / 6.0)
        * vertical_span ** (5.0 / 6.0)
        * sec_zeta ** (11.0 / 6.0)
        * mu2
    )
    if g_d < 0.0:
        raise ValueError(f"G_d must be nonnegative, got {g_d}.")
    omega_le = omega_l * math.sqrt(1.0 + g_d)

    # Literal task specification: nu uses omega_L, not omega_L,e.
    nu = math.sqrt(math.pi) * p.receiver_diameter_m / (2.0 * math.sqrt(2.0) * omega_l)
    a0 = math.erf(nu) ** 2
    omega_leq_sq = (
        omega_le**2
        * math.sqrt(math.pi)
        * math.erf(nu)
        / (2.0 * nu * math.exp(-nu**2))
    )
    omega_leq = math.sqrt(omega_leq_sq)

    hap_jitter_displacement = p.link_length_m * p.theta_jt_rad
    sigma_jt_sq = p.sigma_h_m**2 + hap_jitter_displacement**2
    sigma_jt = math.sqrt(sigma_jt_sq)
    chi = omega_leq / (2.0 * sigma_jt)
    chi_sq = chi**2
    if not (a0 > 0.0 and chi_sq > 0.0 and v_sc > 0.0):
        raise ValueError("The supplied scenario gives a singular continuous PDF.")

    p_out = math.exp(-p.theta_fov_rad**2 / (2.0 * p.sigma_o_rad**2))
    p_in = 1.0 - p_out
    return {
        "sec_zeta": sec_zeta,
        "link_from_geometry_m": link_from_geometry,
        "wave_number_per_m": wave_number,
        "rytov_integral": rytov_integral,
        "rytov_integral_quad_error": rytov_quad_error,
        "sigma_r0_sq": sigma_r0_sq,
        "aperture_numerator": aperture_numerator,
        "aperture_numerator_quad_error": aperture_numerator_error,
        "aperture_denominator": aperture_denominator,
        "aperture_denominator_quad_error": aperture_denominator_error,
        "phi_m": phi,
        "aperture_averaging_factor": aperture_factor,
        "sigma_rd_sq": sigma_rd_sq,
        "v_sc": v_sc,
        "omega_0_check_m": omega_0_check,
        "omega_0_relative_difference": omega_0_relative_difference,
        "omega_l_m": omega_l,
        "lambda_beam": lambda_beam,
        "mu2": mu2,
        "mu2_quad_error": mu2_quad_error,
        "g_d": g_d,
        "omega_le_m": omega_le,
        "nu": nu,
        "a0": a0,
        "omega_leq_sq_m2": omega_leq_sq,
        "omega_leq_m": omega_leq,
        "hap_jitter_displacement_m": hap_jitter_displacement,
        "sigma_jt_sq_m2": sigma_jt_sq,
        "sigma_jt_m": sigma_jt,
        "chi": chi,
        "chi_sq": chi_sq,
        "p_out": p_out,
        "p_in": p_in,
    }


def log_hsc_pdf_from_log_h(log_h: float | np.ndarray, d: dict[str, float]) -> float | np.ndarray:
    v = d["v_sc"]
    return -np.asarray(log_h) - 0.5 * math.log(2.0 * math.pi * v) - (
        np.asarray(log_h) + v / 2.0
    ) ** 2 / (2.0 * v)


def f_hsc(h: float | np.ndarray, d: dict[str, float]) -> float | np.ndarray:
    values = np.asarray(h, dtype=float)
    result = np.zeros_like(values)
    valid = values > 0.0
    result[valid] = _safe_exp(log_hsc_pdf_from_log_h(np.log(values[valid]), d))
    return float(result) if np.ndim(h) == 0 else result


def f_rmis(r: float | np.ndarray, d: dict[str, float], p: Scenario = SCENARIO) -> float | np.ndarray:
    values = np.asarray(r, dtype=float)
    result = np.zeros_like(values)
    valid = values >= 0.0
    sigma_sq = d["sigma_jt_sq_m2"]
    rho = p.rho_m
    if rho == 0.0:
        result[valid] = values[valid] / sigma_sq * np.exp(-values[valid] ** 2 / (2.0 * sigma_sq))
    else:
        argument = rho * values[valid] / sigma_sq
        log_pdf = (
            np.log(values[valid])
            - math.log(sigma_sq)
            - (values[valid] ** 2 + rho**2) / (2.0 * sigma_sq)
            + np.abs(argument)
            + np.log(i0e(argument))
        )
        nonzero = values[valid] > 0.0
        result_indices = np.flatnonzero(valid)
        result[result_indices[nonzero]] = _safe_exp(log_pdf[nonzero])
    return float(result) if np.ndim(r) == 0 else result


def f_rayleigh(r: float | np.ndarray, d: dict[str, float]) -> float | np.ndarray:
    values = np.asarray(r, dtype=float)
    sigma_sq = d["sigma_jt_sq_m2"]
    result = np.where(values >= 0.0, values / sigma_sq * np.exp(-values**2 / (2.0 * sigma_sq)), 0.0)
    return float(result) if np.ndim(r) == 0 else result


def f_hp(u: float | np.ndarray, d: dict[str, float], p: Scenario = SCENARIO) -> float | np.ndarray:
    values = np.asarray(u, dtype=float)
    result = np.zeros_like(values)
    valid = (values > 0.0) & (values <= d["a0"])
    a = d["chi_sq"]
    if p.rho_m == 0.0:
        result[valid] = a / d["a0"] ** a * values[valid] ** (a - 1.0)
    else:
        root = np.sqrt(-d["omega_leq_sq_m2"] / 2.0 * np.log(values[valid] / d["a0"]))
        argument = p.rho_m * root / d["sigma_jt_sq_m2"]
        log_pdf = (
            math.log(a)
            - a * math.log(d["a0"])
            - p.rho_m**2 / (2.0 * d["sigma_jt_sq_m2"])
            + (a - 1.0) * np.log(values[valid])
            + np.abs(argument)
            + np.log(i0e(argument))
        )
        result[valid] = _safe_exp(log_pdf)
    return float(result) if np.ndim(u) == 0 else result


def f_theta(theta: float | np.ndarray, p: Scenario = SCENARIO) -> float | np.ndarray:
    values = np.asarray(theta, dtype=float)
    result = np.where(
        values >= 0.0,
        values / p.sigma_o_rad**2 * np.exp(-values**2 / (2.0 * p.sigma_o_rad**2)),
        0.0,
    )
    return float(result) if np.ndim(theta) == 0 else result


def _log_pdf_log_x(log_x: float | np.ndarray, m: float, v: float, rate: float) -> float | np.ndarray:
    """Log density of log(X)=m+Normal(0,v)-Exp(rate)."""

    y = np.asarray(log_x, dtype=float)
    sigma = math.sqrt(v)
    return (
        math.log(rate)
        + rate * (y - m)
        + 0.5 * rate**2 * v
        + log_ndtr((m - y) / sigma - rate * sigma)
    )


def _log_survival_log_x(log_x: float, m: float, v: float, rate: float) -> float:
    """Stable log P(log(X)>log_x) for the normal-minus-exponential law."""

    sigma = math.sqrt(v)
    z = (log_x - m) / sigma
    log_q = float(log_ndtr(-z))
    log_a = rate * (log_x - m) + 0.5 * rate**2 * v + float(log_ndtr(-z - rate * sigma))
    difference = log_a - log_q
    if difference > 1.0e-11:
        raise ArithmeticError("Normal-minus-exponential survival lost its required ordering.")
    return log_q + _log1mexp(difference)


def _cdf_log_x(log_x: float, m: float, v: float, rate: float) -> float:
    return -math.expm1(_log_survival_log_x(log_x, m, v, rate))


def f_x(t: float | np.ndarray, d: dict[str, float], p: Scenario = SCENARIO) -> float | np.ndarray:
    """Active raw density f_X for the rho=0 scenario."""

    if p.rho_m != 0.0:
        raise ValueError("The closed f_X expression is used only for the supplied rho=0 baseline.")
    values = np.asarray(t, dtype=float)
    result = np.zeros_like(values)
    valid = values > 0.0
    m = math.log(p.eta_atm * d["a0"]) - d["v_sc"] / 2.0
    log_density = _log_pdf_log_x(np.log(values[valid]), m, d["v_sc"], d["chi_sq"]) - np.log(values[valid])
    result[valid] = _safe_exp(log_density)
    return float(result) if np.ndim(t) == 0 else result


def f_x_direct_quadrature(t: float, d: dict[str, float], p: Scenario = SCENARIO) -> float:
    """Specified f_X convolution after the stable s=r^2/(2 sigma_jt^2) change."""

    if not (t > 0.0 and p.rho_m == 0.0):
        raise ValueError("Direct convolution check requires t>0 and the supplied rho=0 baseline.")
    v, a = d["v_sc"], d["chi_sq"]
    sigma = math.sqrt(v)
    m = math.log(p.eta_atm * d["a0"]) - v / 2.0
    log_t = math.log(t)
    normalizer = math.log(t * sigma * math.sqrt(2.0 * math.pi))

    def integrand(s: float) -> float:
        log_value = -s - normalizer - 0.5 * ((log_t - (m - s / a)) / sigma) ** 2
        return 0.0 if log_value < LOG_TINY else math.exp(log_value)

    return _quad(integrand, 0.0, math.inf)[0]


def _raw_moment(q: float, d: dict[str, float], p: Scenario = SCENARIO) -> float:
    c = p.eta_atm * d["a0"]
    a, v = d["chi_sq"], d["v_sc"]
    return c**q * math.exp((q**2 - q) * v / 2.0) * a / (a + q)


def _truncated_moment(q: float, d: dict[str, float], p: Scenario = SCENARIO) -> float:
    """E[X^q 1(X<=1)] via exponential tilting of the exact log-X law."""

    a, v = d["chi_sq"], d["v_sc"]
    m = math.log(p.eta_atm * d["a0"]) - v / 2.0
    tilted_cdf = _cdf_log_x(0.0, m + q * v, v, a + q)
    return _raw_moment(q, d, p) * tilted_cdf


def _log_density_integral(q: float, upper_log_x: float, d: dict[str, float], p: Scenario = SCENARIO) -> float:
    """Numerical log-coordinate integral used to validate analytic moments."""

    m = math.log(p.eta_atm * d["a0"]) - d["v_sc"] / 2.0

    def integrand(y: float) -> float:
        log_value = q * y + float(_log_pdf_log_x(y, m, d["v_sc"], d["chi_sq"]))
        return 0.0 if log_value < LOG_TINY else math.exp(log_value)

    return _quad(integrand, -math.inf, upper_log_x)[0]


def _raw_quantile(probability: float, d: dict[str, float], p: Scenario = SCENARIO) -> float:
    if not 0.0 < probability < 1.0:
        raise ValueError("Quantile probability must be strictly between zero and one.")
    m = math.log(p.eta_atm * d["a0"]) - d["v_sc"] / 2.0
    sigma = math.sqrt(d["v_sc"])
    rate = d["chi_sq"]
    lower = m - 50.0 * (sigma + 1.0 / rate)
    upper = m + 50.0 * sigma + 10.0
    root = brentq(
        lambda y: _cdf_log_x(y, m, d["v_sc"], rate) - probability,
        lower,
        upper,
        xtol=1.0e-13,
        rtol=1.0e-14,
    )
    return math.exp(root)


def component_and_channel_analysis(d: dict[str, float], p: Scenario = SCENARIO) -> dict[str, float | dict]:
    v, a = d["v_sc"], d["chi_sq"]
    m = math.log(p.eta_atm * d["a0"]) - v / 2.0
    log_tail = _log_survival_log_x(0.0, m, v, a)
    tail = math.exp(log_tail) if log_tail >= LOG_TINY else 0.0
    f_x_1 = _cdf_log_x(0.0, m, v, a)
    truncated_q0 = _truncated_moment(0.0, d, p)
    truncated_q_half = _truncated_moment(0.5, d, p)
    truncated_q1 = _truncated_moment(1.0, d, p)
    active_q_half = truncated_q_half / f_x_1
    active_q1 = truncated_q1 / f_x_1
    mean_t = d["p_in"] * active_q1
    mean_sqrt_t = d["p_in"] * active_q_half
    epsilon_mean = p.epsilon_ch_snu
    direct_points = [_raw_quantile(q, d, p) for q in (0.01, 0.5, 0.99)]
    direct_errors = []
    for point in direct_points:
        analytic = float(f_x(point, d, p))
        numerical = f_x_direct_quadrature(point, d, p)
        direct_errors.append(abs(analytic - numerical) / max(abs(analytic), 1.0e-300))

    return {
        "log_x_location": m,
        "log_p_x_gt_1": log_tail,
        "p_x_gt_1_float64": tail,
        "f_x_1_float64": f_x_1,
        "truncated_q0": truncated_q0,
        "truncated_q_half": truncated_q_half,
        "truncated_q1": truncated_q1,
        "raw_q_half": _raw_moment(0.5, d, p),
        "raw_q1": _raw_moment(1.0, d, p),
        "active_mean_t": active_q1,
        "active_mean_sqrt_t": active_q_half,
        "mean_t": mean_t,
        "mean_sqrt_t": mean_sqrt_t,
        "epsilon_base_mean": epsilon_mean,
        "mean_t_epsilon_base": mean_t * epsilon_mean,
        "direct_convolution_points": direct_points,
        "direct_convolution_relative_errors": direct_errors,
    }


def _normalization_checks(d: dict[str, float], analysis: dict, p: Scenario = SCENARIO) -> dict[str, dict[str, float | str]]:
    v = d["v_sc"]
    hsc_norm, _ = _quad(
        lambda y: math.exp(-0.5 * ((y + v / 2.0) ** 2 / v)) / math.sqrt(2.0 * math.pi * v),
        -math.inf,
        math.inf,
    )
    # Combining the exponents first avoids overflow at QUADPACK's extreme
    # transformed abscissae: exp(y) f_logH(y) is exactly N(v/2, v).
    hsc_mean, _ = _quad(
        lambda y: math.exp(-0.5 * ((y - v / 2.0) ** 2 / v)) / math.sqrt(2.0 * math.pi * v),
        -math.inf,
        math.inf,
    )
    r_norm, _ = _quad(lambda r: float(f_rmis(r, d, p)), 0.0, math.inf)
    hp_norm, _ = _quad(lambda x: d["chi_sq"] * x ** (d["chi_sq"] - 1.0), 0.0, 1.0)
    theta_norm, _ = _quad(lambda theta: float(f_theta(theta, p)), 0.0, math.inf)
    fx_norm = _log_density_integral(0.0, math.inf, d, p)
    pactive_norm = _log_density_integral(0.0, 0.0, d, p) / float(analysis["f_x_1_float64"])
    continuous_mass = d["p_in"] * pactive_norm
    checks = {
        "integral_f_Hsc": hsc_norm,
        "E_Hsc": hsc_mean,
        "integral_f_rmis": r_norm,
        "integral_f_Hp": hp_norm,
        "integral_f_theta": theta_norm,
        "integral_f_X": fx_norm,
        "integral_p_active": pactive_norm,
        "p_out_plus_integral_p_cont": d["p_out"] + continuous_mass,
    }
    result: dict[str, dict[str, float | str]] = {}
    for name, value in checks.items():
        error = abs(value - 1.0)
        result[name] = {
            "value": value,
            "absolute_error": error,
            "status": "PASS" if error <= 2.0e-8 else "FAIL",
        }
    rayleigh_grid = np.linspace(0.0, 8.0 * d["sigma_jt_m"], 500)
    rayleigh_error = float(np.max(np.abs(f_rmis(rayleigh_grid, d, p) - f_rayleigh(rayleigh_grid, d))))
    result["rho_zero_is_rayleigh"] = {
        "value": rayleigh_error,
        "absolute_error": rayleigh_error,
        "status": "PASS" if rayleigh_error <= 1.0e-14 else "FAIL",
    }
    direct_error = max(float(x) for x in analysis["direct_convolution_relative_errors"])
    result["f_X_direct_convolution_crosscheck"] = {
        "value": direct_error,
        "absolute_error": direct_error,
        "status": "PASS" if direct_error <= 2.0e-8 else "FAIL",
    }
    result["G_d_nonnegative"] = {
        "value": d["g_d"],
        "absolute_error": 0.0,
        "status": "PASS" if d["g_d"] >= 0.0 else "FAIL",
    }
    return result


def _histogram(samples: np.ndarray, edges: np.ndarray, scale: float = 1.0) -> dict[str, list[float]]:
    counts, edges = np.histogram(samples, bins=edges)
    density = scale * counts / (samples.size * np.diff(edges))
    return {
        "edges": edges.tolist(),
        "counts": counts.astype(int).tolist(),
        "centers": ((edges[:-1] + edges[1:]) / 2.0).tolist(),
        "density": density.tolist(),
    }


def _sample_physical_active(rng: np.random.Generator, n: int, d: dict[str, float], p: Scenario) -> tuple[np.ndarray, int]:
    """Rejection-sample X|X<=1; rejected overflows are never converted to outages."""

    accepted: list[np.ndarray] = []
    accepted_count = 0
    proposed = 0
    while accepted_count < n:
        batch = max(n - accepted_count, 10_000)
        h_sc = np.exp(rng.normal(-d["v_sc"] / 2.0, math.sqrt(d["v_sc"]), batch))
        rx = rng.normal(0.0, d["sigma_jt_m"], batch)
        ry = rng.normal(0.0, d["sigma_jt_m"], batch)
        r_mis = np.hypot(rx, ry)
        hp = d["a0"] * np.exp(-2.0 * r_mis**2 / d["omega_leq_sq_m2"])
        x = p.eta_atm * h_sc * hp
        keep = x <= 1.0
        accepted.append(x[keep])
        accepted_count += int(np.count_nonzero(keep))
        proposed += batch
    return np.concatenate(accepted)[:n], proposed


def monte_carlo(d: dict[str, float], sample_count: int, seed: int, p: Scenario = SCENARIO) -> dict[str, object]:
    streams = np.random.SeedSequence(seed).spawn(3)
    component_rng = np.random.default_rng(streams[0])
    gate_rng = np.random.default_rng(streams[1])
    physical_rng = np.random.default_rng(streams[2])
    h_sc = np.exp(component_rng.normal(-d["v_sc"] / 2.0, math.sqrt(d["v_sc"]), sample_count))
    rx = component_rng.normal(0.0, d["sigma_jt_m"], sample_count)
    ry = component_rng.normal(0.0, d["sigma_jt_m"], sample_count)
    r_mis = np.hypot(rx, ry)
    h_p = d["a0"] * np.exp(-2.0 * r_mis**2 / d["omega_leq_sq_m2"])
    x = p.eta_atm * h_sc * h_p
    theta_rx = gate_rng.normal(0.0, p.sigma_o_rad, sample_count)
    theta_ry = gate_rng.normal(0.0, p.sigma_o_rad, sample_count)
    theta_a = np.hypot(theta_rx, theta_ry)
    b_aoa = theta_a <= p.theta_fov_rad
    active_x, physical_proposed = _sample_physical_active(physical_rng, sample_count, d, p)
    physical_gate = gate_rng.random(sample_count) >= d["p_out"]
    physical_t = active_x * physical_gate
    outage_count = int(np.count_nonzero(~b_aoa))
    p_out_hat = outage_count / sample_count
    p_out_se = math.sqrt(d["p_out"] * (1.0 - d["p_out"]) / sample_count)
    return {
        "seed": seed,
        "sample_count": sample_count,
        "child_spawn_keys": [list(child.spawn_key) for child in streams],
        "h_sc": h_sc,
        "r_mis": r_mis,
        "h_p": h_p,
        "x": x,
        "theta_a": theta_a,
        "b_aoa": b_aoa,
        "active_x": active_x,
        "physical_t": physical_t,
        "physical_proposed_count": physical_proposed,
        "p_out_hat": p_out_hat,
        "p_out_standard_error": p_out_se,
        "p_out_z_score": (p_out_hat - d["p_out"]) / p_out_se if p_out_se else 0.0,
        "mean_h_sc": float(np.mean(h_sc)),
        "mean_t": float(np.mean(physical_t)),
        "mean_sqrt_t": float(np.mean(np.sqrt(physical_t))),
    }


def _style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def _save(fig: plt.Figure, output_dir: Path, basename: str) -> None:
    fig.tight_layout()
    fig.savefig(output_dir / f"{basename}.pdf", bbox_inches="tight")
    fig.savefig(output_dir / f"{basename}.png", dpi=350, bbox_inches="tight")
    plt.close(fig)


def make_figures(d: dict[str, float], analysis: dict, mc: dict[str, object], output_dir: Path, p: Scenario = SCENARIO) -> dict[str, object]:
    _style()
    figure_data: dict[str, object] = {}
    v = d["v_sc"]
    h_low = math.exp(-v / 2.0 + math.sqrt(v) * float(ndtri(1.0e-5)))
    h_high = math.exp(-v / 2.0 + math.sqrt(v) * float(ndtri(1.0 - 1.0e-5)))
    h_grid = np.linspace(h_low, h_high, 1600)
    h_hist = _histogram(np.asarray(mc["h_sc"]), np.linspace(h_low, h_high, 65))
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.bar(h_hist["centers"], h_hist["density"], width=np.diff(np.asarray(h_hist["edges"])), alpha=0.28, color="tab:gray", label="Monte Carlo")
    ax.plot(h_grid, f_hsc(h_grid, d), color="tab:blue", linewidth=1.8, label=r"Analytical $f_{H_{\rm sc}}$")
    ax.set(xlabel=r"Scintillation gain $H_{\rm sc}$", ylabel="Probability density", title="Scintillation Gain PDF")
    ax.grid(alpha=0.22)
    ax.legend()
    _save(fig, output_dir, "fig_01_scintillation_pdf")
    figure_data["fig_01"] = {"grid": h_grid.tolist(), "pdf": f_hsc(h_grid, d).tolist(), "histogram": h_hist}

    r_high = d["sigma_jt_m"] * math.sqrt(-2.0 * math.log(1.0 - 0.99999))
    r_grid = np.linspace(0.0, r_high, 1600)
    r_hist = _histogram(np.asarray(mc["r_mis"]), np.linspace(0.0, r_high, 65))
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.bar(r_hist["centers"], r_hist["density"], width=np.diff(np.asarray(r_hist["edges"])), alpha=0.28, color="tab:gray", label="Monte Carlo")
    ax.plot(r_grid, f_rmis(r_grid, d, p), color="tab:blue", linewidth=1.8, label=r"Rician $f_{r_{\rm mis}}$")
    ax.set(xlabel=r"Radial misalignment $r_{\rm mis}$ (m)", ylabel="Probability density", title="Radial Beam--Receiver Misalignment PDF")
    ax.grid(alpha=0.22)
    ax.legend()
    _save(fig, output_dir, "fig_02_radial_misalignment_pdf")
    figure_data["fig_02"] = {"grid": r_grid.tolist(), "pdf": f_rmis(r_grid, d, p).tolist(), "histogram": r_hist}

    hp_grid = np.geomspace(d["a0"] * 1.0e-9, d["a0"], 1800)
    hp_hist = _histogram(np.asarray(mc["h_p"]), np.linspace(0.0, d["a0"], 70))
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.bar(hp_hist["centers"], hp_hist["density"], width=np.diff(np.asarray(hp_hist["edges"])), alpha=0.28, color="tab:gray", label="Monte Carlo")
    ax.plot(hp_grid, f_hp(hp_grid, d, p), color="tab:blue", linewidth=1.8, label=r"Analytical $f_{H_p}$")
    ax.set_xlim(0.0, d["a0"])
    ax.set(xlabel=r"Pointing coefficient $H_p$", ylabel="Probability density", title="Pointing-Coefficient PDF")
    ax.grid(alpha=0.22)
    ax.legend()
    _save(fig, output_dir, "fig_03_pointing_pdf")
    figure_data["fig_03"] = {"grid": hp_grid.tolist(), "pdf": f_hp(hp_grid, d, p).tolist(), "histogram": hp_hist}

    theta_high = max(
        p.theta_fov_rad * 1.05,
        p.sigma_o_rad * math.sqrt(-2.0 * math.log(1.0 - 0.99999)),
    )
    theta_grid = np.linspace(0.0, theta_high, 1600)
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.plot(theta_grid * 1.0e3, f_theta(theta_grid, p) / 1.0e3, color="tab:blue", linewidth=1.8)
    ax.axvline(p.theta_fov_rad * 1.0e3, color="tab:red", linestyle="--", linewidth=1.4, label=r"$\theta_{\rm FOV}$")
    ax.set(xlabel=r"AoA magnitude $\theta_a$ (mrad)", ylabel="Probability density (mrad$^{-1}$)", title="Angle-of-Arrival PDF")
    ax.grid(alpha=0.22)
    ax.legend()
    _save(fig, output_dir, "fig_04_aoa_pdf")
    figure_data["fig_04"] = {"grid_mrad": (theta_grid * 1.0e3).tolist(), "pdf_per_mrad": (f_theta(theta_grid, p) / 1.0e3).tolist()}

    b_values = np.array([d["p_out"], d["p_in"]])
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    bars = ax.bar([0, 1], b_values, color=["tab:red", "tab:blue"], width=0.48)
    for bar, value in zip(bars, b_values):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.025, f"{value:.8g}", ha="center", va="bottom")
    ax.set(xticks=[0, 1], xticklabels=[r"$B_{\rm AoA}=0$", r"$B_{\rm AoA}=1$"], ylim=(0.0, 1.12), ylabel="Probability mass", title="AoA Acquisition PMF")
    ax.grid(axis="y", alpha=0.22)
    _save(fig, output_dir, "fig_05_aoa_pmf")
    figure_data["fig_05"] = {"support": [0, 1], "probability_mass": b_values.tolist(), "monte_carlo_p_out": float(mc["p_out_hat"])}

    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.vlines(p.eta_atm, 0.0, 1.0, color="tab:blue", linewidth=2.3)
    ax.scatter([p.eta_atm], [1.0], color="tab:blue", zorder=3)
    ax.set(xlim=(p.eta_atm - 0.08, p.eta_atm + 0.08), ylim=(0.0, 1.12), xlabel=r"Atmospheric transmittance $\eta_{\rm atm}$", ylabel="Probability mass", title="Deterministic Atmospheric Transmittance")
    ax.grid(alpha=0.22)
    _save(fig, output_dir, "fig_06_atmospheric_mass")
    figure_data["fig_06"] = {"support": [p.eta_atm], "probability_mass": [1.0]}

    x_low = _raw_quantile(1.0e-6, d, p)
    x_high = max(1.05, _raw_quantile(1.0 - 1.0e-6, d, p))
    x_grid = np.geomspace(x_low, x_high, 2200)
    x_hist = _histogram(np.asarray(mc["x"]), np.geomspace(x_low, x_high, 70))
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ax.bar(x_hist["centers"], x_hist["density"], width=np.diff(np.asarray(x_hist["edges"])), alpha=0.28, color="tab:gray", label="Monte Carlo")
    ax.plot(x_grid, f_x(x_grid, d, p), color="tab:blue", linewidth=1.8, label=r"Analytical $f_X$")
    ax.axvline(1.0, color="tab:red", linestyle="--", linewidth=1.25, label=r"Physical boundary $X=1$")
    ax.set_xscale("log")
    ax.set(xlabel=r"Raw active transmittance $X=\eta_{\rm atm}H_{\rm sc}H_p$", ylabel="Probability density", title="Raw Active Composite PDF")
    ax.grid(alpha=0.22, which="both")
    ax.legend()
    _save(fig, output_dir, "fig_07_raw_active_pdf")
    figure_data["fig_07"] = {"grid": x_grid.tolist(), "pdf": f_x(x_grid, d, p).tolist(), "histogram": x_hist}

    physical_low = _raw_quantile(max(1.0e-8, float(analysis["f_x_1_float64"]) * 1.0e-8), d, p)
    t_grid = np.geomspace(physical_low, 1.0, 2400)
    p_active = f_x(t_grid, d, p) / float(analysis["f_x_1_float64"])
    p_cont = d["p_in"] * p_active
    active_hist = _histogram(np.asarray(mc["active_x"]), np.geomspace(physical_low, 1.0, 70), scale=d["p_in"])
    fig, ax = plt.subplots(figsize=(7.0, 4.3))
    ax.bar(active_hist["centers"], active_hist["density"], width=np.diff(np.asarray(active_hist["edges"])), alpha=0.28, color="tab:gray", label="Monte Carlo active component")
    ax.plot(t_grid, p_cont, color="tab:blue", linewidth=1.8, label="Continuous active density")
    # Symlog retains the physical endpoint T=0 while resolving the compact active law.
    ax.set_xscale("symlog", linthresh=max(5.0 * physical_low, 1.0e-11))
    ax.set(xlim=(0.0, 1.0), ylim=(0.0, 1.08 * max(float(np.max(p_cont)), max(active_hist["density"]))), xlabel=r"Physical power transmittance $T$", ylabel="Continuous probability density", title="Physical HAP--UAV Power-Transmittance Distribution")
    ax.grid(alpha=0.22)
    ax_mass = ax.twinx()
    ax_mass.vlines(0.0, 0.0, d["p_out"], color="tab:red", linewidth=2.8, label=rf"Outage mass $P(T=0)={d['p_out']:.3g}$")
    ax_mass.scatter([0.0], [d["p_out"]], color="tab:red", s=30, zorder=4)
    ax_mass.set(ylim=(0.0, 1.25 * d["p_out"]), ylabel="Discrete probability mass")
    lines_a, labels_a = ax.get_legend_handles_labels()
    lines_b, labels_b = ax_mass.get_legend_handles_labels()
    ax.legend(lines_a + lines_b, labels_a + labels_b, loc="upper right", framealpha=0.9)
    _save(fig, output_dir, "fig_08_total_channel_distribution")
    figure_data["fig_08"] = {"grid": t_grid.tolist(), "p_active": p_active.tolist(), "p_continuous": p_cont.tolist(), "histogram": active_hist, "outage_mass": d["p_out"]}
    return figure_data


def _print_value(label: str, value: float) -> None:
    print(f"  {label:<34} = {value:.12g}")


def print_summary(d: dict[str, float], analysis: dict, checks: dict[str, dict[str, float | str]], mc: dict[str, object], p: Scenario = SCENARIO) -> None:
    print("\nHAP--UAV TCP-style channel-only diagnostic")
    print("(Standalone supplied scenario; not the active project configuration.)")
    print("\nGeometry")
    _print_value("L (m)", p.link_length_m)
    _print_value("k (m^-1)", d["wave_number_per_m"])
    _print_value("omega_0 check (m)", d["omega_0_check_m"])
    _print_value("relative omega_0 difference", d["omega_0_relative_difference"])
    print("\nTurbulence")
    for key, label in (("sigma_r0_sq", "sigma_R0_sq"), ("phi_m", "Phi (m)"), ("aperture_averaging_factor", "A_A"), ("sigma_rd_sq", "sigma_RD_sq"), ("v_sc", "v_sc")):
        _print_value(label, d[key])
    print("\nBeam")
    for key, label in (("omega_l_m", "omega_L (m)"), ("lambda_beam", "Lambda"), ("g_d", "G_d"), ("omega_le_m", "omega_L,e (m)"), ("nu", "nu"), ("a0", "A0"), ("omega_leq_m", "omega_L,eq (m)")):
        _print_value(label, d[key])
    print("\nMisalignment")
    _print_value("sigma_h (m)", p.sigma_h_m)
    _print_value("L theta_jt (m)", d["hap_jitter_displacement_m"])
    _print_value("sigma_jt (m)", d["sigma_jt_m"])
    _print_value("rho (m)", p.rho_m)
    _print_value("chi", d["chi"])
    print("\nAoA")
    _print_value("sigma_o (rad)", p.sigma_o_rad)
    _print_value("theta_FOV (rad)", p.theta_fov_rad)
    _print_value("p_in", d["p_in"])
    _print_value("p_out", d["p_out"])
    print("\nComposite")
    _print_value("F_X_1 (float64)", float(analysis["f_x_1_float64"]))
    log_tail = float(analysis["log_p_x_gt_1"])
    print(f"  P(X>1)                              = exp({log_tail:.12g}) = 10^({log_tail / math.log(10.0):.12g})")
    _print_value("<T>", float(analysis["mean_t"]))
    _print_value("<sqrt(T)>", float(analysis["mean_sqrt_t"]))
    _print_value("<T epsilon_base> (independent only)", float(analysis["mean_t_epsilon_base"]))
    _print_value("epsilon_ch (SNU)", p.epsilon_ch_snu)
    print("  excess-noise interpretation          = deterministic baseline input")
    print("\nMonte Carlo")
    _print_value("N", float(mc["sample_count"]))
    _print_value("MC p_out", float(mc["p_out_hat"]))
    _print_value("MC p_out z-score", float(mc["p_out_z_score"]))
    _print_value("MC <T>", float(mc["mean_t"]))
    _print_value("MC <sqrt(T)>", float(mc["mean_sqrt_t"]))
    print("\nChecks")
    for name, check in checks.items():
        print(f"  {str(check['status']):<4} {name:<40} value={float(check['value']):.12g} error={float(check['absolute_error']):.3g}")


def _json_ready_mc(mc: dict[str, object]) -> dict[str, object]:
    """Persist figure-reconstructible diagnostics without 300k raw samples."""

    return {
        key: value
        for key, value in mc.items()
        if key not in {"h_sc", "r_mis", "h_p", "x", "theta_a", "b_aoa", "active_x", "physical_t"}
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for the eight PDF/PNG pairs and raw summary JSON.")
    parser.add_argument("--samples", type=int, default=300_000, help="Monte Carlo samples (minimum 300000).")
    parser.add_argument("--seed", type=int, default=20260917, help="Base seed for named Monte Carlo streams.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.samples < 300_000:
        raise ValueError("The requested validation requires at least 300,000 Monte Carlo samples.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    d = derive_parameters()
    analysis = component_and_channel_analysis(d)
    checks = _normalization_checks(d, analysis)
    mc = monte_carlo(d, args.samples, args.seed)
    figure_data = make_figures(d, analysis, mc, args.output_dir)
    print_summary(d, analysis, checks, mc)
    if any(check["status"] != "PASS" for check in checks.values()):
        raise RuntimeError("One or more analytical normalization/cross-checks failed.")

    payload = {
        "status": "CHANNEL_ONLY_DIAGNOSTIC_NOT_ACTIVE_CONFIG",
        "scope": "Exact supplied TCP-style HAP--UAV parameter scenario; no CV-QKD security/SKR evaluation.",
        "independence_assumption": "H_sc, H_p, and B_AoA are mutually independent as required by the mixed-law construction.",
        "literal_specification_note": "nu is computed with omega_L, as supplied in the request; the active TeX draft uses a different radius.",
        "scenario": asdict(SCENARIO),
        "derived": d,
        "analysis": analysis,
        "checks": checks,
        "monte_carlo": _json_ready_mc(mc),
        "figure_data": figure_data,
        "provenance": {
            "script": str(Path(__file__).resolve()),
            "script_sha256": _sha256(Path(__file__)),
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": SCIPY_VERSION,
            "matplotlib": matplotlib.__version__,
        },
    }
    summary_path = args.output_dir / "hap_uav_channel_pdf_summary.json"
    summary_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"\nSaved figures and raw plotted data to: {args.output_dir.resolve()}")
    print(f"Saved numerical summary: {summary_path.resolve()}")


if __name__ == "__main__":
    main()
