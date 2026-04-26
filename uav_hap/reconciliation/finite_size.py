import numpy as np

from ..config import NoiseParams, SecurityParams
from ..protocols.gm import noise, skr


def delta_n(n: int, c: float) -> float:
    if int(n) <= 0:
        raise ValueError("n must be positive.")
    return float(c) / np.sqrt(float(n))


def finite_size_key_rate(K_eff: float, n: int, delta_c: float) -> float:
    return float(K_eff) - delta_n(n=int(n), c=float(delta_c))


def finite_size_skr(VA, T, eps, mode="MD", N=100_000_000, f_rep=50_000_000):
    del mode
    T_arr = np.array([float(T)], dtype=float)
    noise_terms = noise(
        T_samples=T_arr,
        noise_params=NoiseParams(xi_ch=float(eps), xi_det=0.0, xi_phase=0.0, detection="hom"),
    )
    k_arr = skr(
        T_samples=T_arr,
        noise_terms=noise_terms,
        security_params=SecurityParams(VA=float(VA), beta=0.90),
        detection="hom",
    )
    k_finite = finite_size_key_rate(K_eff=float(k_arr[0]), n=int(N), delta_c=5.0)
    return float(f_rep) * k_finite


def plob_upper_bound(T):
    T_val = float(T)
    if T_val <= 0.0 or T_val >= 1.0:
        return 0.0
    return -np.log2(1.0 - T_val)
