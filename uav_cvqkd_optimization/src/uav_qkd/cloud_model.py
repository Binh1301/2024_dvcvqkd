"""Analytic Gaussian CLWC sum at arbitrary coordinates and continuous time."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class GaussianCluster:
    amplitude: float
    center: tuple[float, float]
    sigma: tuple[float, float]
    covariance: tuple | None = None
    velocity: tuple[float, float] | None = None

    def __post_init__(self):
        if not np.isfinite(self.amplitude) or self.amplitude < 0:
            raise ValueError('Gaussian amplitude must be nonnegative and finite')
        if np.shape(self.center) != (2,) or np.shape(self.sigma) != (2,) or not np.isfinite([self.center, self.sigma]).all() or np.min(self.sigma) <= 0:
            raise ValueError('Gaussian center/sigma must be finite pairs and sigma positive')
        covariance = np.diag(np.square(self.sigma)) if self.covariance is None else np.asarray(self.covariance, float)
        if covariance.shape != (2, 2) or not np.isfinite(covariance).all() or not np.allclose(covariance, covariance.T) or np.linalg.eigvalsh(covariance).min() <= 0:
            raise ValueError('Cloud covariance must be symmetric positive definite')
        if self.velocity is not None and (np.shape(self.velocity) != (2,) or not np.isfinite(self.velocity).all()):
            raise ValueError('Cloud velocity must be a finite pair in m/s')


class CloudField:
    def __init__(self, clusters: list[GaussianCluster], velocity=(-5., 0.), clip_max=None):
        if np.shape(velocity) != (2,) or not np.isfinite(velocity).all():
            raise ValueError('Cloud velocity must be a finite pair in m/s')
        if clip_max is not None and (not np.isfinite(clip_max) or clip_max <= 0):
            raise ValueError('CLWC clipping maximum must be positive')
        self.clusters, self.velocity, self.clip_max = clusters, np.asarray(velocity), clip_max

    def evaluate(self, positions, time: float) -> np.ndarray:
        """CLWC in mg/m^3. Empty clusters explicitly represent clear skies."""
        q = np.asarray(positions, float)
        if q.ndim < 1 or q.shape[-1] != 2 or not np.isfinite(q).all() or not np.isfinite(time) or time < 0:
            raise ValueError('Cloud query needs finite (...,2) coordinates and nonnegative time')
        out = np.zeros(q.shape[:-1])
        for c in self.clusters:
            velocity = self.velocity if c.velocity is None else np.asarray(c.velocity)
            delta = q - (np.asarray(c.center) + time*velocity)
            covariance = np.diag(np.square(c.sigma)) if c.covariance is None else np.asarray(c.covariance)
            exponent = np.einsum('...i,ij,...j->...', delta, np.linalg.inv(covariance), delta)
            out += c.amplitude * np.exp(-.5*exponent)
        return np.minimum(out, self.clip_max) if self.clip_max is not None else out

    def grid(self, width: float, height: float, time: float, shape=(50, 50)):
        ny, nx = shape
        x = (np.arange(nx)+.5)*width/nx
        y = (np.arange(ny)+.5)*height/ny
        X, Y = np.meshgrid(x, y)
        return x, y, self.evaluate(np.stack([X, Y], axis=-1), time)
