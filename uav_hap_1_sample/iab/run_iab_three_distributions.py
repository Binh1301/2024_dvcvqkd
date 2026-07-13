from __future__ import annotations

import os
import sys

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1_sample.config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from uav_hap_1_sample.iab.core import simulate_three_distributions
    from uav_hap_1_sample.protocol.qam_protocol import build_state_binomial, build_state_mb, build_state_uniform, compute_metrics
    from uav_hap_1_sample.zstar.base import build_constellation, build_probs_binomial, build_probs_mb, build_probs_uniform
else:
    from ..config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from .core import simulate_three_distributions
    from ..protocol.qam_protocol import build_state_binomial, build_state_mb, build_state_uniform, compute_metrics
    from ..zstar.base import build_constellation, build_probs_binomial, build_probs_mb, build_probs_uniform


MB_ALPHA0_DISPLAY = float(QAM_ALPHA0_MB)


def _average_symbol_energy(constellation: np.ndarray, probs: np.ndarray) -> float:
    return float(np.sum(np.asarray(probs, dtype=float) * np.abs(np.asarray(constellation, dtype=complex)) ** 2))


def _qam_distribution(label: str, alpha0: float) -> tuple[np.ndarray, np.ndarray]:
    constellation = np.asarray(build_constellation(float(alpha0)), dtype=complex)
    if label == "uniform":
        probs = build_probs_uniform()
    elif label == "binomial":
        probs = build_probs_binomial()
    elif label == "mb":
        probs = build_probs_mb(QAM_NU_TILDE)
    else:
        raise ValueError(f"Unsupported label: {label}")
    return constellation, probs


def main() -> None:
    geom = GeometryParams()
    params = ChannelParams(W0_m=0.10, a_m=0.20, visibility_km=13.6, Cn2=1e-15)
    fading = simulate_three_distributions(
        geometry=geom,
        channel_params=params,
        n_fading_samples=30_000,
        seed=42,
    )

    # Reuse the same physical channel realization for all label-specific estimates.
    channel_result = fading
    eta_samples = None
    # The helper above returns only IAB results, so rebuild the channel once for diagnostics.
    from uav_hap_1_sample.iab.core import channel as _channel  # local import keeps script entry simple
    channel_data = _channel(geometry=geom, channel_params=params, N=30_000, rng=np.random.default_rng(42))
    eta_samples = np.asarray(channel_data["T_samples"], dtype=float)
    t_eff = float(channel_data["T_eff"])

    states = {
        "uniform": build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM),
        "binomial": build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL),
        "mb": build_state_mb(MB_ALPHA0_DISPLAY, QAM_NCUT_MB, QAM_NU_TILDE),
    }

    results = {}
    diagnostics = {}
    for label, state in states.items():
        metrics = compute_metrics(state, t_eff, QAM_EPS, 0.95, QAM_ETA, QAM_V_EL)
        constellation, probs = _qam_distribution(label, state.alpha0)
        avg_symbol_energy = _average_symbol_energy(constellation, probs)
        snr_cvqkd = float((t_eff * state.va) / (2.0 + t_eff * metrics.chi_tot))
        sigma2 = float(avg_symbol_energy / max(snr_cvqkd, 1e-15))
        result = simulate_three_distributions(
            geometry=geom,
            channel_params=params,
            n_fading_samples=30_000,
            sigma2=sigma2,
            snr_db=10.0 * np.log10(snr_cvqkd),
            seed=42,
            alpha0=state.alpha0,
            nu_tilde=QAM_NU_TILDE if label == "mb" else None,
        )[label]
        results[label] = result
        diagnostics[label] = {
            "state_va": state.va,
            "chi_tot": metrics.chi_tot,
            "snr_cvqkd": snr_cvqkd,
            "sigma2": sigma2,
            "avg_symbol_energy": avg_symbol_energy,
        }

    print("=" * 72)
    print("I_AB Monte Carlo estimator from Qu & Djordjevic")
    print("=" * 72)
    for label in ("uniform", "binomial", "mb"):
        result = results[label]
        diag = diagnostics[label]
        eff_snr_db = 10.0 * np.log10(result.effective_snr_mean) if result.effective_snr_mean > 0.0 else float("-inf")
        print(
            f"{label:<8} | H(X)={result.h_x:.6f}  I_AB={result.i_ab:.6f}  "
            f"E[log2 Q(X|Y)]={result.mean_conditional_term:.6f}"
        )
        print(
            f"          VA={diag['state_va']:.6f}  chi_tot={diag['chi_tot']:.6f}  "
            f"SNR_CVQKD={diag['snr_cvqkd']:.6f}  Es={diag['avg_symbol_energy']:.6f}"
        )
        print(
            f"          sigma2={result.sigma2_used:.6f}  snr_lin={result.snr_linear_used:.6f}  "
            f"eff_snr_mean={result.effective_snr_mean:.6f} "
            f"({eff_snr_db:.2f} dB)"
        )
        print(
            f"          eta_mean={result.eta_mean:.6f}  eta_std={result.eta_std:.6f}  "
            f"mean_Q(x_i|y_i)={result.mean_posterior_probability:.6f}"
        )
        bins = list(zip(result.posterior_histogram_edges[:-1], result.posterior_histogram_edges[1:], result.posterior_histogram_counts))
        hist_text = " ".join([f"[{lo:.1f},{hi:.1f}):{cnt}" for lo, hi, cnt in bins if cnt > 0])
        print(f"          posterior_hist={hist_text}")


if __name__ == "__main__":
    main()
