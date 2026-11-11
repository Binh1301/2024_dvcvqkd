"""Proposed Ibrahim-style stationary Gaussian clouds; no optical/QKD model.

The paper inspires the two-scale Gaussian construction, not the stationary AR(1)
law or the spectral interpolation/advection used here. Arrays are [y, x].
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.fft import fftfreq, rfftfreq, rfft2, irfft2


MODEL_NAME = "Ibrahim-style Multiscale Gaussian Cloud Model with Stationary Temporal Evolution and Wind Advection"


@dataclass(frozen=True)
class StationaryCloudConfig:
    nx: int = 50
    ny: int = 50
    dx_m: float = 40.0
    dy_m: float = 40.0
    dt_s: float = 1.0
    slots: int = 1000
    vx_m_s: float = -5.0
    vy_m_s: float = 0.0
    tau_c_s: float = 300.0
    seed: int = 20261111
    u: int = 5
    w_f: float = 0.35
    w_c: float = 1.0
    guard_m: float = 1000.0
    initial_fraction: float = 0.30
    intensity_transform: str = "softplus"
    intensity_scale: float = 1.0
    intensity_offset: float = 0.0

    def __post_init__(self):
        for name in ("nx", "ny", "slots", "u"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.u < 3 or self.u % 2 == 0:
            raise ValueError("u must be odd and >=3 (real, unitary Fourier shifts without Nyquist ambiguity)")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        for name in ("dx_m", "dy_m", "dt_s", "vx_m_s", "vy_m_s", "tau_c_s", "w_f", "w_c",
                     "guard_m", "initial_fraction", "intensity_scale", "intensity_offset"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"{name} must be finite numeric")
        if min(self.dx_m, self.dy_m, self.dt_s, self.tau_c_s, self.guard_m, self.intensity_scale) <= 0:
            raise ValueError("cell size, dt, tau, guard and intensity scale must be positive")
        if min(self.w_f, self.w_c) < 0 or self.w_f**2 + self.w_c**2 == 0:
            raise ValueError("nonnegative weights, at least one positive, required")
        if not 0 < self.initial_fraction < 1:
            raise ValueError("initial_fraction must be strictly between zero and one")
        if self.intensity_transform not in ("softplus", "positive_part"):
            raise ValueError("intensity_transform must be softplus or positive_part")

    @property
    def rho(self):
        return math.exp(-self.dt_s / self.tau_c_s)

    @property
    def innovation_scale(self):
        return math.sqrt(-math.expm1(-2 * self.dt_s / self.tau_c_s))

    @property
    def horizon_s(self):
        # One extra slot of padding beyond the last output, k=slots-1.
        return self.slots * self.dt_s


def _odd_multiple_at_least(n, u):
    coarse = max(3, math.ceil(n / u))
    return u * (coarse if coarse % 2 else coarse + 1)


class SpectralDomain:
    def __init__(self, config):
        self.c = c = config
        gx, gy = math.ceil(c.guard_m/c.dx_m), math.ceil(c.guard_m/c.dy_m)
        tx = math.ceil(abs(c.vx_m_s)*c.horizon_s/c.dx_m)
        ty = math.ceil(abs(c.vy_m_s)*c.horizon_s/c.dy_m)
        self.nx = _odd_multiple_at_least(c.nx + 2*gx + tx, c.u)
        self.ny = _odd_multiple_at_least(c.ny + 2*gy + ty, c.u)
        self.x0 = gx + (tx if c.vx_m_s > 0 else 0)
        self.y0 = gy + (ty if c.vy_m_s > 0 else 0)
        self.shape = self.ny, self.nx
        self.coarse_shape = self.ny//c.u, self.nx//c.u
        self.fy = fftfreq(self.ny)[:, None]
        self.fx = rfftfreq(self.nx)[None, :]
        self.coarse_iy = np.rint(fftfreq(self.coarse_shape[0])*self.coarse_shape[0]).astype(int) % self.ny
        self.phase = self.shift_phase(c.vx_m_s*c.dt_s/c.dx_m, c.vy_m_s*c.dt_s/c.dy_m)

    def shift_phase(self, dx_cells, dy_cells=0.0):
        if not np.isfinite([dx_cells, dy_cells]).all():
            raise ValueError("finite shifts required")
        return np.exp(-2j*np.pi*(self.fx*dx_cells + self.fy*dy_cells))

    def crop(self, full):
        if full.shape != self.shape:
            raise ValueError("full field shape differs from spectral domain")
        return full[self.y0:self.y0+self.c.ny, self.x0:self.x0+self.c.nx].copy()

    def draw(self, rng, *, components=False):
        """Fixed linear normalization preserves Gaussianity; no random sample-std divisor.

        Removing each scale's DC gives exact full-domain sample mean zero and
        deterministic variance factors give E[G_f(r)^2]=E[G_c(r)^2]=1.
        Coarse FFT coefficients are zero-padded: trigonometric interpolation.
        """
        n, nc = self.nx*self.ny, math.prod(self.coarse_shape)
        fine = rfft2(rng.standard_normal(self.shape)) / math.sqrt(1-1/n)
        fine[0, 0] = 0
        coarse_small = rfft2(rng.standard_normal(self.coarse_shape)) / math.sqrt(1-1/nc)
        coarse_small[0, 0] = 0
        coarse = np.zeros_like(fine)
        coarse[self.coarse_iy, :self.coarse_shape[1]//2+1] = coarse_small * (n/nc)
        combined = (self.c.w_f*fine + self.c.w_c*coarse) / math.hypot(self.c.w_f, self.c.w_c)
        return (combined, fine, coarse) if components else combined

    def to_real(self, coefficients):
        return irfft2(coefficients, s=self.shape)

    def covariance(self, scale="combined"):
        """Exact discrete target C(dy,dx) on the synthetic torus, C(0)=1."""
        n, nc = self.nx*self.ny, math.prod(self.coarse_shape)
        fine = np.full((self.ny, self.nx//2+1), n*n/(n-1))
        coarse = np.zeros_like(fine)
        coarse[self.coarse_iy, :self.coarse_shape[1]//2+1] = n*n/(nc-1)
        fine[0, 0] = coarse[0, 0] = 0
        if scale == "combined":
            power = (self.c.w_f**2*fine+self.c.w_c**2*coarse)/(self.c.w_f**2+self.c.w_c**2)
        elif scale == "fine":
            power = fine
        elif scale == "coarse":
            power = coarse
        else:
            raise ValueError("unknown covariance scale")
        return irfft2(power, s=self.shape)/n

    def empirical_covariance(self, coefficients):
        return irfft2(abs(coefficients)**2, s=self.shape)/(self.nx*self.ny)

    def expected_crop_variance(self):
        c = self.c
        covariance = self.covariance()
        variance_mean = 0.0
        for iy in range(-c.ny+1, c.ny):
            for ix in range(-c.nx+1, c.nx):
                variance_mean += (c.ny-abs(iy))*(c.nx-abs(ix))*covariance[iy % self.ny, ix % self.nx]
        return 1 - variance_mean/(c.nx*c.ny)**2

    def boundary_receipt(self):
        c = self.c
        rows = []
        for time in sorted(set([0.0, min(400., c.horizon_s), (c.slots-1)*c.dt_s, c.horizon_s])):
            row = {"time_s": time}
            for axis, origin, count, step, velocity, total in (
                ("x", self.x0, c.nx, c.dx_m, c.vx_m_s, self.nx),
                ("y", self.y0, c.ny, c.dy_m, c.vy_m_s, self.ny)):
                a, b = origin*step-velocity*time, (origin+count)*step-velocity*time
                row[f"{axis}_backtrace_interval_m"] = [a, b]
                row[f"{axis}_minimum_margin_m"] = min(a, total*step-b)
            rows.append(row)
        # Linear characteristics attain their extrema at the two horizon endpoints.
        margins = [r[f"{axis}_minimum_margin_m"] for r in rows for axis in ("x", "y")]
        return {"status": "CURRENTLY_VERIFIED_PASS" if min(margins) >= c.guard_m-1e-9 else "FAILED",
                "synthetic_shape_yx": list(self.shape), "coarse_shape_yx": list(self.coarse_shape),
                "synthetic_extent_xy_m": [self.nx*c.dx_m, self.ny*c.dy_m],
                "crop_index_origin_yx": [self.y0, self.x0], "guard_required_m": c.guard_m,
                "padding_horizon_s": c.horizon_s, "last_output_time_s": (c.slots-1)*c.dt_s,
                "backtraces": rows,
                "proof": "For any innovation birth time s<=t, age t-s lies in [0,horizon]. Backtraces r-v*(t-s) stay inside the unwrapped synthetic rectangle with this guard. No characteristic needs modulo reduction.",
                "limitation": "Fourier interpolation has global support; this is no geometric re-entry, not compact-support causal independence from periodic covariance images."}


def relative_intensity(latent, config):
    z = np.asarray(latent, dtype=float) - config.intensity_offset
    if not np.isfinite(z).all():
        raise ValueError("finite latent field required")
    result = config.intensity_scale*(np.logaddexp(0, z) if config.intensity_transform == "softplus" else np.maximum(z, 0))
    if not np.isfinite(result).all():
        raise ValueError("intensity overflow")
    return result


class StationaryCloudSimulator:
    def __init__(self, config):
        self.c = config
        self.domain = SpectralDomain(config)
        self.rng = np.random.Generator(np.random.PCG64(config.seed))
        self.coefficients, fine, coarse = self.domain.draw(self.rng, components=True)
        self.initial_fine = self.domain.crop(self.domain.to_real(fine))
        self.initial_coarse = self.domain.crop(self.domain.to_real(coarse))
        self.slot = 0
        self.initial = self.latent()
        self.gamma = float(np.quantile(self.initial, 1-config.initial_fraction, method="linear"))

    def latent(self):
        return self.domain.crop(self.domain.to_real(self.coefficients))

    def step(self):
        if self.slot >= self.c.slots-1:
            raise ValueError("configured slot horizon exhausted; enlarge domain before continuing")
        self.coefficients = (self.c.rho*self.domain.phase*self.coefficients
                             + self.c.innovation_scale*self.domain.draw(self.rng))
        self.slot += 1
        return self.latent()
