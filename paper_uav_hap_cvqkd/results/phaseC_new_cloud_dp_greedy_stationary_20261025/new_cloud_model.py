"""Index-covariance Gaussian blockage; independently resampled means and slots."""
from functools import lru_cache
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import ndtr

J = 100


@lru_cache(maxsize=1)
def covariance():
    index=np.arange(J)
    gamma=9.*.9**np.abs(index[:,None]-index[None,:])
    factor=np.linalg.cholesky(gamma)
    assert np.array_equal(gamma,gamma.T) and np.array_equal(np.diag(gamma),np.full(J,9.))
    assert np.max(abs(factor@factor.T-gamma))<2e-13
    gamma.setflags(write=False);factor.setflags(write=False)
    return gamma,factor


def blockage_probability(threshold):
    return quad(lambda mu:ndtr((mu-threshold)/3)/2,-1,1,epsabs=1e-13,epsrel=1e-13)[0]


@lru_cache(maxsize=16)
def calibrated_threshold(probability):
    p=float(probability)
    if not np.isfinite(p) or not .1<=p<=.8:raise ValueError('Approved calibrated domain is p in [0.1,0.8]')
    t=float(brentq(lambda x:blockage_probability(x)-p,-30.,30.,xtol=1e-13))
    if abs(blockage_probability(t)-p)>1e-12:raise ValueError('Threshold calibration residual')
    return t


def latent(slots,seed,mission_id):
    if type(slots) is not int or slots<2 or type(seed) is not int or seed<0 or type(mission_id) is not int or mission_id<0:
        raise ValueError('Require slots>=2 and nonnegative integer seed/mission ID')
    normal_rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,mission_id])))
    mean_rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,mission_id,1])))
    mu=mean_rng.uniform(-1.,1.,size=(slots,J))
    # Sign reversal aligns upper-threshold new masks with the old lower-threshold CRN coupling.
    epsilon=-normal_rng.standard_normal((slots,J))@covariance()[1].T
    return (mu+epsilon).T,mu.T,epsilon.T


def threshold(latent_values,*,mode,probability=None):
    values=np.asarray(latent_values,dtype=float)
    if values.ndim!=2 or values.shape[0]!=J or not np.isfinite(values).all():
        raise ValueError('Finite J=100 by Nt Gaussian values required')
    if mode=='zero':
        if probability is not None:raise ValueError('Zero threshold has no arbitrary p parameter')
        t=0.
    elif mode=='calibrated':t=calibrated_threshold(probability)
    else:raise ValueError('Use separate zero or calibrated threshold mode')
    return values>t,t


def generate(slots,seed,mission_id,*,mode='zero',probability=None):
    g,mu,epsilon=latent(slots,seed,mission_id)
    blocked,t=threshold(g,mode=mode,probability=probability)
    return dict(G=g,mu=mu,epsilon=epsilon,C=blocked,threshold=t,mode=mode)
