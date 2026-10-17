"""Synthetic stationary Gaussian-copula cloud states, not measured weather."""
from __future__ import annotations

import math
from functools import lru_cache
import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr, ndtri
from src.uav_mobility import scalar, transition_distances


def positive_integer(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def cloud_parameters(probability, correlation_length_m, temporal_rho):
    p = scalar(probability, "blockage probability")
    ell = scalar(correlation_length_m, "latent correlation length", positive=True)
    rho = scalar(temporal_rho, "latent temporal correlation")
    if not 0 <= p <= 1 or not 0 <= rho < 1:
        raise ValueError("Require 0<=p<=1 and 0<=rho<1")
    return p, ell, rho


@lru_cache(maxsize=32)
def _spatial_factor(coordinates, ell):
    covariance = np.exp(-transition_distances(np.asarray(coordinates)) / ell)
    # Duplicate positions/singular kernels fail; no jitter changes the model.
    factor = np.linalg.cholesky(covariance)
    if not np.allclose(factor @ factor.T, covariance, atol=1e-12, rtol=1e-12):
        raise ValueError("Spatial factorization residual")
    covariance.setflags(write=False); factor.setflags(write=False)
    return covariance, factor


def spatial_covariance(positions, correlation_length_m):
    ell = scalar(correlation_length_m, "latent correlation length", positive=True)
    points = np.asarray(positions, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not len(points) or not np.isfinite(points).all():
        raise ValueError("Positions must be a nonempty finite Jx2 array")
    return _spatial_factor(tuple(map(tuple, points)), ell)


def generate_cloud(positions, slots, probability, correlation_length_m, temporal_rho,
                   seed=20261015, realization_id=0, *, return_latent=False):
    """Return JxN booleans; the same seed/ID supplies common innovations."""
    slots = positive_integer(slots, "slots")
    p, ell, rho = cloud_parameters(probability, correlation_length_m, temporal_rho)
    if type(seed) is not int or seed < 0 or type(realization_id) is not int or realization_id < 0:
        raise ValueError("Seed and realization ID must be nonnegative integers")
    _, factor = spatial_covariance(positions, ell)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, realization_id])))
    innovations = rng.standard_normal((slots, len(factor))) @ factor.T
    latent = np.empty_like(innovations)
    latent[0] = innovations[0]
    for n in range(1, slots):
        latent[n] = rho * latent[n-1] + math.sqrt(1-rho*rho) * innovations[n]
    if p in (0., 1.):
        blocked = np.full((len(factor), slots), bool(p), dtype=bool)
    else:
        blocked = (latent < ndtri(p)).T
    return (blocked, latent.T) if return_latent else blocked


def bernoulli_correlation(probability, latent_correlation):
    p = scalar(probability, "probability")
    r = scalar(latent_correlation, "latent correlation")
    if not 0 <= p <= 1 or not -1 <= r <= 1:
        raise ValueError("Invalid Bernoulli correlation parameters")
    if p in (0., 1.):
        return None
    if r == 1.:
        return 1.
    if r == -1.:
        joint = max(0., 2*p-1)
    else:
        a = float(ndtri(p))
        joint = quad(lambda x: math.exp(-x*x/2)/math.sqrt(2*math.pi)
                     * ndtr((a-r*x)/math.sqrt(1-r*r)), -np.inf, a,
                     epsabs=1e-11, epsrel=1e-11)[0]
    return float((joint-p*p)/(p*(1-p)))


def mean_statistics(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Statistics require at least two finite independent mission values")
    from scipy.stats import t
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    se = sd / math.sqrt(len(values))
    half = float(t.ppf(.975, len(values)-1)) * se
    return dict(mean=mean, sd=sd, se=se, ci95_low=mean-half, ci95_high=mean+half,
                realizations=len(values), uncertainty_scope="independent_missions_not_cells_or_slots")


def correlation_audit(positions, *, probability=.4, correlation_length_m=250., temporal_rho=.9,
                      missions=512, slots=64, seed=20261016):
    """Cluster-SE checks; every per-mission statistic can contain correlated cells."""
    positive_integer(missions, "audit missions")
    if missions < 2 or slots < 2 or len(positions) < 3:
        raise ValueError("Correlation audit requires >=2 missions, >=2 slots, >=3 positions")
    p, ell, rho = cloud_parameters(probability, correlation_length_m, temporal_rho)
    if p in (0.,1.):
        raise ValueError("Binary correlation is undefined for a deterministic cloud law")
    distance = transition_distances(positions)
    near = int(np.argsort(distance[0])[1]); far = int(np.argmax(distance[0]))
    targets = dict(blockage_probability=p,
        latent_spatial_near=math.exp(-distance[0,near]/ell),
        latent_spatial_far=math.exp(-distance[0,far]/ell), latent_temporal=rho)
    for name in ("spatial_near", "spatial_far", "temporal"):
        targets["binary_"+name] = bernoulli_correlation(p, targets["latent_"+name])
    values = {k:[] for k in targets}
    for realization in range(missions):
        c,z = generate_cloud(positions, slots, p, ell, rho, seed, realization, return_latent=True)
        b = (c.astype(float)-p)/math.sqrt(p*(1-p))
        values["blockage_probability"].append(float(c.mean()))
        for name, data in (("latent",z),("binary",b)):
            values[name+"_spatial_near"].append(float(np.mean(data[0]*data[near])))
            values[name+"_spatial_far"].append(float(np.mean(data[0]*data[far])))
            values[name+"_temporal"].append(float(np.mean(data[:,:-1]*data[:,1:])))
    rows=[]
    for name, target in targets.items():
        stats=mean_statistics(values[name])
        tolerance=5*stats["se"] + 1e-10
        rows.append(dict(metric=name,target=target,**stats,tolerance=tolerance,
                         passed=abs(stats["mean"]-target)<=tolerance))
    return dict(status="CURRENTLY_VERIFIED_PASS" if all(r["passed"] for r in rows) else "FAILED",
                missions=missions,slots=slots,seed=seed,near_index=near,far_index=far,
                probability=p,correlation_length_m=ell,temporal_rho=rho,checks=rows,
                interpretation="Gaussian latent parameters; binary covariance computed by threshold integral")
