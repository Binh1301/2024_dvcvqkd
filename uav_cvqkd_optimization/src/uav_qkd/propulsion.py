"""Manuscript Eq. (6)-(7): speed mixing with a numerical lower convex hull."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class PropulsionParams:
    P0: float
    Pi: float
    U_tip: float
    v0: float
    d0: float
    rho: float
    s: float
    A: float
    v_max: float

    def __post_init__(self):
        for name, value in vars(self).items():
            if not np.isfinite(value) or value < 0 or (name != 'd0' and value == 0):
                raise ValueError(f'Propulsion parameter {name} must be finite and positive (d0 may be zero)')


def propulsion_power(v, params: PropulsionParams):
    """Watts at nonnegative speed (m/s); rationalized induced-power expression."""
    v = np.asarray(v, dtype=float)
    if not np.isfinite(v).all() or (v < 0).any() or (v > params.v_max).any():
        raise ValueError('Speed must lie in [0, v_max] m/s')
    a = v**2 / (2*params.v0**2)
    induced = 1 / np.sqrt(np.hypot(1., a) + a)
    return (params.P0*(1+3*v**2/params.U_tip**2) + params.Pi*induced
            + .5*params.d0*params.rho*params.s*params.A*v**3)


def lower_convex_envelope(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Increasing abscissae and the lower hull of their numerical function values."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or x.shape != y.shape or len(x) < 2 or not np.isfinite([x, y]).all() or (np.diff(x) <= 0).any():
        raise ValueError('Convex envelope requires finite, strictly increasing x and matching y')
    hull = []
    for k in range(len(x)):
        while len(hull) >= 2:
            i, j = hull[-2:]
            if (y[j]-y[i])*(x[k]-x[j]) < (y[k]-y[j])*(x[j]-x[i]):
                break
            hull.pop()
        hull.append(k)
    return x[hull], y[hull]


class EnergyModel:
    def __init__(self, params: PropulsionParams, samples: int = 2001):
        if isinstance(samples, bool) or int(samples) != samples or samples < 3:
            raise ValueError('Velocity grid samples must be an integer >=3')
        self.params, self.samples = params, int(samples)
        self.grid = np.linspace(0, params.v_max, self.samples)

    def energy(self, distance, duration: float):
        """Joules; infeasible distances return inf, invalid arguments raise.

        Query means are inserted into the hull: constant speed is always a
        candidate. This is a sampled speed-mixing approximation, not an oracle.
        """
        d = np.asarray(distance, float)
        if not np.isfinite(duration) or duration <= 0 or not np.isfinite(d).all() or (d < 0).any():
            raise ValueError('Distance must be nonnegative and duration positive, both finite')
        feasible = d <= self.params.v_max * duration
        means = np.atleast_1d(d / duration)[np.atleast_1d(feasible)]
        grid = np.unique(np.r_[self.grid, means])
        hx, hy = lower_convex_envelope(grid, propulsion_power(grid, self.params))
        result = np.where(feasible, duration*np.interp(d/duration, hx, hy), np.inf)
        return float(result) if result.ndim == 0 else result


def minimum_propulsion_energy(distance: float, duration: float, params: PropulsionParams,
                              samples: int = 2001) -> float:
    return EnergyModel(params, samples).energy(distance, duration)
