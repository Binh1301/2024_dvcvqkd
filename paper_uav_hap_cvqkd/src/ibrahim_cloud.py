"""Isolated synthetic cloud emulator: Ibrahim et al. (2024), Algorithm 1.

Arrays are [y, x], with x increasing right and y increasing up. No QKD imports.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates, shift


@dataclass(frozen=True)
class CloudConfig:
    # Required explicitly: the paper does not specify a reproducible p/P pair.
    p: float
    P: float
    nx: int = 50
    ny: int = 50
    width_m: float = 2000.0
    height_m: float = 2000.0
    u: int = 5
    dt_s: float = 1.0
    vx_m_s: float = -5.0
    vy_m_s: float = 0.0
    duration_s: float = 1000.0
    seed: int = 20261111
    threshold_mode: str = "coverage"
    gamma: float | None = None
    target_coverage: float = 0.30
    blur_sigma_cells: float = 1.0
    blur_radius_cells: int = 4
    normalization: str = "reference_minmax"

    def __post_init__(self):
        for name in ("nx", "ny", "u", "blur_radius_cells"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.nx % self.u or self.ny % self.u:
            raise ValueError("u must divide nx and ny")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        for name in ("p", "P", "width_m", "height_m", "dt_s", "vx_m_s",
                     "vy_m_s", "duration_s", "target_coverage", "blur_sigma_cells"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be finite numeric")
        if min(self.width_m, self.height_m, self.dt_s, self.blur_sigma_cells) <= 0:
            raise ValueError("domain, time step and blur sigma must be positive")
        if not 0 <= self.p <= 1 or self.P < 0 or not 0 <= self.target_coverage <= 1:
            raise ValueError("Require 0<=p<=1, P>=0, 0<=target_coverage<=1")
        if self.duration_s < 0 or not np.isclose(self.duration_s / self.dt_s,
                                                round(self.duration_s / self.dt_s), atol=1e-9, rtol=0):
            raise ValueError("duration_s must be a nonnegative multiple of dt_s")
        if self.threshold_mode not in ("fixed", "coverage"):
            raise ValueError("threshold_mode must be fixed or coverage")
        if self.threshold_mode == "fixed" and (self.gamma is None or not math.isfinite(self.gamma)):
            raise ValueError("fixed threshold requires finite gamma")
        if self.normalization not in ("none", "reference_minmax"):
            raise ValueError("normalization must be none or reference_minmax")

    @property
    def shape(self):
        return self.ny, self.nx

    @property
    def displacement_cells(self):
        return (self.vy_m_s * self.dt_s / (self.height_m / self.ny),
                self.vx_m_s * self.dt_s / (self.width_m / self.nx))


def multiscale_noise(rng, config):
    """Lines 1-2: independent unit Gaussian fine/coarse fields; periodic bilinear interp."""
    fine = rng.standard_normal(config.shape)
    coarse = rng.standard_normal((config.ny // config.u, config.nx // config.u))
    y, x = np.indices(config.shape, dtype=float) / config.u
    upsampled = map_coordinates(coarse, [y, x], order=1, mode="grid-wrap", prefilter=False)
    return fine, upsampled


def _field(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or min(values.shape) < 1 or not np.isfinite(values).all():
        raise ValueError("field must be a finite nonempty 2D array")
    return values


def advect_periodic(field, *, vx_m_s, vy_m_s, dt_s, dx_m, dy_m):
    """Physical pullback G(x-vx*dt,y-vy*dt), using periodic linear interpolation.

    Repeated fractional steps introduce numerical diffusion; this is a numerical
    choice, not an extra physical cloud-evolution term in Algorithm 1.
    """
    field = _field(field)
    parameters = (vx_m_s, vy_m_s, dt_s, dx_m, dy_m)
    if not all(math.isfinite(v) for v in parameters) or min(dt_s, dx_m, dy_m) <= 0:
        raise ValueError("advection requires finite velocities and positive dt/dx/dy")
    return shift(field, (vy_m_s * dt_s / dy_m, vx_m_s * dt_s / dx_m),
                 order=1, mode="grid-wrap", prefilter=False)


def coverage_threshold(reference, coverage):
    reference = _field(reference)
    if not math.isfinite(coverage) or not 0 <= coverage <= 1:
        raise ValueError("coverage must be in [0,1]")
    if coverage == 1:
        return float(np.nextafter(reference.min(), -np.inf))
    return float(np.quantile(reference, 1 - coverage, method="linear"))


def blur_noise(field, sigma_cells, radius_cells):
    """Lines 16-21: separable, unit-sum Gaussian convolution of continuous G."""
    if not math.isfinite(sigma_cells) or sigma_cells <= 0 or type(radius_cells) is not int or radius_cells <= 0:
        raise ValueError("positive Gaussian sigma and integer radius required")
    return gaussian_filter(_field(field), sigma_cells, radius=radius_cells, mode="wrap")


@dataclass(frozen=True)
class CloudFrame:
    time_s: float
    raw_noise: np.ndarray
    mask: np.ndarray
    blurred_noise: np.ndarray
    intensity: np.ndarray
    normalization_clipped_fraction: float


class CloudSimulator:
    """Only raw Gaussian noise is recursive; mask and blur never feed back."""

    def __init__(self, config: CloudConfig, *, initial_field=None, reference_field=None):
        self.config = config
        self.rng = np.random.Generator(np.random.PCG64(config.seed))
        self.initial_fine, self.initial_coarse = multiscale_noise(self.rng, config)
        initial = self.initial_fine + self.initial_coarse if initial_field is None else _field(initial_field)
        reference = initial if reference_field is None else _field(reference_field)
        if initial.shape != config.shape or reference.shape != config.shape:
            raise ValueError("initial and reference fields must match configured grid")
        self._raw = initial.copy()
        self.reference_field = reference.copy()
        self.reference_field.setflags(write=False)
        self._gamma = (float(config.gamma) if config.threshold_mode == "fixed" else
                       coverage_threshold(reference, config.target_coverage))
        reference_bn = blur_noise(reference, config.blur_sigma_cells, config.blur_radius_cells)
        self.normalization_bounds = float(reference_bn.min()), float(reference_bn.max())
        self.slot = 0

    @property
    def gamma(self):
        return self._gamma

    def frame(self):
        c = self.config
        raw = self._raw.copy()
        mask = (raw > self.gamma).astype(np.uint8)
        blurred = blur_noise(raw, c.blur_sigma_cells, c.blur_radius_cells)
        intensity = blurred.copy()
        clipped = 0.0
        if c.normalization == "reference_minmax":
            lo, hi = self.normalization_bounds
            if hi == lo:
                # A constant reference has no intensity scale; fail rather than invent one.
                raise ValueError("reference_minmax requires nonconstant blurred reference")
            intensity = (blurred - lo) / (hi - lo)
            clipped = float(np.mean((intensity < 0) | (intensity > 1)))
            intensity = np.clip(intensity, 0, 1)
        for array in (raw, mask, blurred, intensity):
            array.setflags(write=False)
        return CloudFrame(self.slot * c.dt_s, raw, mask, blurred, intensity, clipped)

    def step(self):
        c = self.config
        advected = advect_periodic(self._raw, vx_m_s=c.vx_m_s, vy_m_s=c.vy_m_s,
                                  dt_s=c.dt_s, dx_m=c.width_m / c.nx, dy_m=c.height_m / c.ny)
        fine, coarse = multiscale_noise(self.rng, c)
        self._raw = (1 - c.p) * advected + c.P * fine + c.P * coarse
        self.slot += 1
        return self.frame()


def motion_diagnostic(config):
    """Noise-free isolated pulse: verify subpixel sign and 8-second centroid motion."""
    from dataclasses import replace
    test = replace(config, p=0.0, P=0.0, dt_s=1.0, duration_s=8.0,
                   threshold_mode="fixed", gamma=0.5, normalization="none")
    initial = np.zeros(test.shape)
    iy, ix = test.ny // 2, test.nx // 2
    initial[iy, ix] = 1.0
    sim = CloudSimulator(test, initial_field=initial)
    one = sim.step()
    for _ in range(7):
        last = sim.step()
    x = np.arange(test.nx) * test.width_m / test.nx
    measured = float((last.raw_noise.sum(axis=0) @ x) / last.raw_noise.sum() - x[ix])
    expected = test.vx_m_s * 8
    # The configured scenario stays away from the periodic seam for this probe.
    return {"status": "CURRENTLY_VERIFIED_PASS" if np.isclose(measured, expected, atol=1e-10, rtol=0) else "FAILED",
            "probe_dt_s": 1.0, "probe_p": 0.0, "probe_P": 0.0,
            "configured_dx_m": test.width_m / test.nx,
            "configured_one_second_shift_x_cells": test.displacement_cells[1],
            "pulse_value_after_1s_at_initial_cell": float(one.raw_noise[iy, ix]),
            "measured_x_displacement_after_8s_m": measured,
            "expected_x_displacement_after_8s_m": expected,
            "metric": "centroid, not peak; linear interpolation broadens the pulse"}
