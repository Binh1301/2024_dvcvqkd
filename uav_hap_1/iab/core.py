from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

from ..channel.channel_model import channel
from ..config import (
    ChannelParams,
    GeometryParams,
    QAM_ALPHA0_BINOMIAL,
    QAM_ALPHA0_MB,
    QAM_ALPHA0_UNIFORM,
    QAM_NCUT_BINOMIAL,
    QAM_NCUT_MB,
    QAM_NCUT_UNIFORM,
)
from ..zstar.base import build_constellation, build_probs_binomial, build_probs_mb, build_probs_uniform

EPS = 1e-15
DEFAULT_ALPHA0 = np.sqrt(12.0 / 17.0)
DEFAULT_SNR_DB = -8.0


@dataclass(frozen=True)
class IABResult:
    label: str
    h_x: float
    i_ab: float
    mean_conditional_term: float
    sample_count: int
    eta_mean: float
    eta_std: float
    sigma2_used: float
    snr_db_used: float
    avg_symbol_energy: float
    snr_linear_used: float
    effective_snr_mean: float
    mean_posterior_probability: float
    posterior_histogram_counts: tuple[int, ...]
    posterior_histogram_edges: tuple[float, ...]


@dataclass(frozen=True)
class IABMonteCarloResult:
    label: str
    va: float
    t_eff: float
    i_ab_mc: float
    i_ab_ref: float
    sample_count: int
    eta_mean: float
    eta_std: float


def _complex_awgn(rng: np.random.Generator, n: int, sigma2: float) -> np.ndarray:
    if sigma2 <= 0.0:
        raise ValueError("sigma2 must be positive.")
    scale = np.sqrt(float(sigma2) / 2.0)
    return scale * (rng.standard_normal(n) + 1j * rng.standard_normal(n))


def _entropy_bits(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    if np.any(p < 0.0):
        raise ValueError("Probabilities must be non-negative.")
    total = float(p.sum())
    if not np.isclose(total, 1.0):
        if total <= 0.0:
            raise ValueError("Probability mass must be positive.")
        p = p / total
    mask = p > 0.0
    return float(-np.sum(p[mask] * np.log2(p[mask])))


def _average_symbol_energy(constellation: np.ndarray, probs: np.ndarray) -> float:
    energy = np.sum(np.asarray(probs, dtype=float) * np.abs(np.asarray(constellation, dtype=complex)) ** 2)
    return float(energy)


def _sigma2_from_snr_db(constellation: np.ndarray, probs: np.ndarray, snr_db: float) -> float:
    snr_linear = 10.0 ** (float(snr_db) / 10.0)
    if snr_linear <= 0.0:
        raise ValueError("snr_db must be finite.")
    signal_power = _average_symbol_energy(constellation, probs)
    if signal_power <= 0.0:
        raise ValueError("Average symbol energy must be positive.")
    return float(signal_power / snr_linear)


def _posterior_term(
    y: np.ndarray,
    eta: np.ndarray,
    transmitted_indices: np.ndarray,
    constellation: np.ndarray,
    probs: np.ndarray,
    sigma2: float,
    chunk_size: int = 2048,
) -> tuple[float, np.ndarray]:
    """Monte-Carlo estimator of E[log2 Q(X|Y)] from Qu & Djordjevic."""
    log_prior = np.log(np.maximum(probs, EPS))
    total = 0.0
    n = int(y.shape[0])
    sqrt_eta = np.sqrt(np.maximum(eta, 0.0))
    q_true_chunks: list[np.ndarray] = []
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        y_chunk = y[start:stop][:, None]
        eta_chunk = sqrt_eta[start:stop][:, None]
        idx_chunk = transmitted_indices[start:stop]
        d2 = np.abs(y_chunk - eta_chunk * constellation[None, :]) ** 2
        logw = log_prior[None, :] - d2 / float(sigma2)
        logw = logw - np.max(logw, axis=1, keepdims=True)
        w = np.exp(logw)
        w_sum = np.sum(w, axis=1, keepdims=True)
        q = w / np.maximum(w_sum, EPS)
        q_true = q[np.arange(stop - start), idx_chunk]
        q_true_chunks.append(q_true)
        total += float(np.sum(np.log2(np.maximum(q_true, EPS))))
    return total / float(n), np.concatenate(q_true_chunks)


def _build_distribution(
    label: Literal["uniform", "binomial", "mb"],
    alpha0: float,
    nu_tilde: Optional[float] = None,
) -> tuple[np.ndarray, np.ndarray]:
    constellation = np.asarray(build_constellation(float(alpha0)), dtype=complex)
    if label == "uniform":
        probs = build_probs_uniform()
    elif label == "binomial":
        probs = build_probs_binomial()
    elif label == "mb":
        if nu_tilde is None:
            raise ValueError("nu_tilde is required for Maxwell-Boltzmann.")
        probs = build_probs_mb(float(nu_tilde))
    else:
        raise ValueError(f"Unsupported distribution: {label}")
    return constellation, np.asarray(probs, dtype=float)


def simulate_iab(
    label: Literal["uniform", "binomial", "mb"],
    eta_samples: np.ndarray,
    sigma2: Optional[float] = None,
    snr_db: float = DEFAULT_SNR_DB,
    seed: int = 42,
    alpha0: float = DEFAULT_ALPHA0,
    nu_tilde: Optional[float] = None,
    noise_samples: Optional[np.ndarray] = None,
    chunk_size: int = 2048,
) -> IABResult:
    constellation, probs = _build_distribution(label, alpha0=alpha0, nu_tilde=nu_tilde)
    avg_symbol_energy = _average_symbol_energy(constellation, probs)
    sigma2_used = float(sigma2) if sigma2 is not None else _sigma2_from_snr_db(constellation, probs, snr_db)
    snr_linear_used = float(avg_symbol_energy / sigma2_used)
    n = int(len(eta_samples))
    if n <= 0:
        raise ValueError("eta_samples must contain at least one element.")

    rng = np.random.default_rng(seed)
    indices = rng.choice(len(constellation), size=n, p=probs)
    x = constellation[indices]
    if noise_samples is None:
        noise_samples = _complex_awgn(rng, n, sigma2_used)
    else:
        noise_samples = np.asarray(noise_samples, dtype=complex)
        if noise_samples.shape[0] != n:
            raise ValueError("noise_samples must match eta_samples length.")

    y = np.sqrt(np.maximum(eta_samples, 0.0)) * x + noise_samples
    h_x = _entropy_bits(probs)
    mean_term, q_true_samples = _posterior_term(
        y=y,
        eta=eta_samples,
        transmitted_indices=indices,
        constellation=constellation,
        probs=probs,
        sigma2=sigma2_used,
        chunk_size=chunk_size,
    )
    i_ab = h_x + mean_term
    hist_counts, hist_edges = np.histogram(q_true_samples, bins=np.linspace(0.0, 1.0, 11))
    return IABResult(
        label=label,
        h_x=h_x,
        i_ab=float(i_ab),
        mean_conditional_term=float(mean_term),
        sample_count=n,
        eta_mean=float(np.mean(eta_samples)),
        eta_std=float(np.std(eta_samples, ddof=0)),
        sigma2_used=sigma2_used,
        snr_db_used=float(snr_db),
        avg_symbol_energy=float(avg_symbol_energy),
        snr_linear_used=snr_linear_used,
        effective_snr_mean=float(np.mean(eta_samples) * snr_linear_used),
        mean_posterior_probability=float(np.mean(q_true_samples)),
        posterior_histogram_counts=tuple(int(x) for x in hist_counts.tolist()),
        posterior_histogram_edges=tuple(float(x) for x in hist_edges.tolist()),
    )


def simulate_three_distributions(
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    n_fading_samples: int = 30_000,
    sigma2: Optional[float] = None,
    snr_db: float = DEFAULT_SNR_DB,
    seed: int = 42,
    alpha0: float = DEFAULT_ALPHA0,
    nu_tilde: float = 0.1,
    chunk_size: int = 2048,
) -> dict[str, IABResult]:
    geom = GeometryParams() if geometry is None else geometry
    params = ChannelParams() if channel_params is None else channel_params
    fading = channel(geometry=geom, channel_params=params, N=n_fading_samples, rng=np.random.default_rng(seed))
    eta_samples = np.asarray(fading["T_samples"], dtype=float)

    results = {
        "uniform": simulate_iab(
            "uniform",
            eta_samples=eta_samples,
            sigma2=sigma2,
            snr_db=snr_db,
            seed=seed,
            alpha0=alpha0,
            chunk_size=chunk_size,
        ),
        "binomial": simulate_iab(
            "binomial",
            eta_samples=eta_samples,
            sigma2=sigma2,
            snr_db=snr_db,
            seed=seed,
            alpha0=alpha0,
            chunk_size=chunk_size,
        ),
        "mb": simulate_iab(
            "mb",
            eta_samples=eta_samples,
            sigma2=sigma2,
            snr_db=snr_db,
            seed=seed,
            alpha0=alpha0,
            nu_tilde=nu_tilde,
            chunk_size=chunk_size,
        ),
    }
    return results


def simulate_three_distributions_mc(
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    n_fading_samples: int = 30_000,
    seed: int = 42,
    nu_tilde: float = 0.1,
    eps: float = 0.001,
    beta: float = 0.95,
    eta_det: float = 0.95,
    v_el: float = 0.001,
) -> dict[str, IABMonteCarloResult]:
    from ..protocol.qam_protocol import build_state_binomial, build_state_mb, build_state_uniform
    from ..zstar.base import compute_IAB, compute_chi_tot

    geom = GeometryParams() if geometry is None else geometry
    params = ChannelParams() if channel_params is None else channel_params
    fading = channel(geometry=geom, channel_params=params, N=n_fading_samples, rng=np.random.default_rng(seed))
    t_samples = np.asarray(fading["T_samples"], dtype=float)
    t_eff = float(fading["T_eff"])

    states = {
        "uniform": build_state_uniform(float(QAM_ALPHA0_UNIFORM), int(QAM_NCUT_UNIFORM)),
        "binomial": build_state_binomial(float(QAM_ALPHA0_BINOMIAL), int(QAM_NCUT_BINOMIAL)),
        "mb": build_state_mb(float(QAM_ALPHA0_MB), int(QAM_NCUT_MB), nu_tilde),
    }

    results: dict[str, IABMonteCarloResult] = {}
    for label, state in states.items():
        iab_samples = []
        for t in t_samples:
            chi_tot, _, _ = compute_chi_tot(float(t), float(eps), float(eta_det), float(v_el))
            iab_samples.append(compute_IAB(float(state.va), float(t), chi_tot))
        iab_mc = float(np.mean(iab_samples))
        iab_ref = float(
            compute_IAB(
                float(state.va),
                t_eff,
                compute_chi_tot(float(t_eff), float(eps), float(eta_det), float(v_el))[0],
            )
        )
        results[label] = IABMonteCarloResult(
            label=label,
            va=float(state.va),
            t_eff=t_eff,
            i_ab_mc=iab_mc,
            i_ab_ref=iab_ref,
            sample_count=int(len(t_samples)),
            eta_mean=float(np.mean(t_samples)),
            eta_std=float(np.std(t_samples, ddof=0)),
        )

    return results
