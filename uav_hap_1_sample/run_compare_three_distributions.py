"""
Compare binomial, uniform, and Maxwell–Boltzmann QAM-256 at the same channel T_eff.

Assumptions:
- Use Z* formula aligned with compute_Zstar_qam256.py (sqrt(2*T*eps*w)).
- Use chi_tot in I_AB (consistent with qam_count helpers).
"""

from __future__ import annotations

import os
import sys

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1_sample.channel.channel_model import channel
    from uav_hap_1_sample.config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from uav_hap_1_sample.protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from uav_hap_1_sample.zstar import mb as zmb
else:
    from .channel.channel_model import channel
    from .config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from .protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from .zstar import mb as zmb


def _print_result(label, state, metrics):
    nu_info = f", nu_tilde={state.nu_tilde}" if state.nu_tilde is not None else ""
    print(f"{label:<10} | alpha0={state.alpha0:.6f}, Ncut={state.ncut}{nu_info}")
    print(f"  VA={state.va:.10f}, TrC={state.tr_c:.10f}, w={state.w:.10f}")
    print(
        f"  term_signal={metrics.term_signal:.10f}, term_noise={metrics.term_noise:.10f}"
    )
    print(
        f"  Z*_raw={metrics.z_star_raw:.10f}, Z*={metrics.z_star:.10f}, "
        f"chi_BE={metrics.chi_be:.10f}, I_AB[{metrics.mi_mode}]={metrics.i_ab:.10f}"
    )
    print(f"  rho=Z_raw/Zmax={metrics.z_raw_over_zmax:.10f}, margin={metrics.z_raw_margin:.10f}")
    status = _status(metrics)
    if status == "clipped":
        print(f"  ⚠️  Z* clipped to Z*_max = {metrics.z_star_max:.10f} (not physically admissible)")
    elif status == "invalid":
        print("  ⚠️  invalid numeric state (do not interpret physically)")
    print(f"  SKR_raw={metrics.skr_raw:.10f}, SKR={metrics.skr:.10f}")


def _status(metrics) -> str:
    values = [
        metrics.z_star_raw,
        metrics.z_star_max,
        metrics.chi_be,
        metrics.i_ab,
        metrics.skr_raw,
        metrics.term_signal,
        metrics.term_noise,
    ]
    if not np.all(np.isfinite(values)) or metrics.z_star_max <= 0:
        return "invalid"
    if metrics.z_star_raw > metrics.z_star_max:
        return "clipped"
    return "physical"


def _tune_nu_tilde(target_va: float, alpha0: float, ncut: int, grid: np.ndarray) -> tuple[float, float]:
    best_nu = float(grid[0])
    best_err = float("inf")
    best_va = float("nan")
    for nu in grid:
        state = zmb.compute_state(alpha0=alpha0, ncut=ncut, nu_tilde=float(nu))
        err = abs(state["va"] - target_va)
        if err < best_err:
            best_err = err
            best_nu = float(nu)
            best_va = float(state["va"])
    return best_nu, best_va


def main() -> None:
    geom = GeometryParams()
    ch_params = ChannelParams()
    fading = channel(geometry=geom, channel_params=ch_params, N=30_000, rng=np.random.default_rng(42))
    T_eff = float(fading["T_eff"])

    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    uni_state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
    mb_state = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)

    nu_grid = np.linspace(0.02, 0.6, 40)
    nu_bin, va_bin = _tune_nu_tilde(bin_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid)
    nu_uni, va_uni = _tune_nu_tilde(uni_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid)
    mb_state_tuned_bin = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_bin)
    mb_state_tuned_uni = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_uni)

    bin_metrics = compute_metrics(bin_state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    uni_metrics = compute_metrics(uni_state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    mb_metrics = compute_metrics(mb_state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    mb_metrics_bin = compute_metrics(mb_state_tuned_bin, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    mb_metrics_uni = compute_metrics(mb_state_tuned_uni, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)

    print("=" * 70)
    print("Binomial vs Uniform vs Maxwell–Boltzmann (QAM-256)")
    print("=" * 70)
    print(
        f"T_eff = {T_eff:.6f}, eps = {QAM_EPS}, beta = {QAM_BETA}, "
        f"eta = {QAM_ETA}, v_el = {QAM_V_EL}, nu_tilde = {QAM_NU_TILDE}"
    )
    print("-" * 70)
    _print_result("Binomial", bin_state, bin_metrics)
    print("-" * 70)
    _print_result("Uniform", uni_state, uni_metrics)
    print("-" * 70)
    _print_result("MB", mb_state, mb_metrics)
    print("-" * 70)
    print("MB tuning for fixed-VA comparison:")
    print(f"  target VA (binomial) = {bin_state.va:.10f} -> nu_tilde = {nu_bin:.4f}, VA_MB = {va_bin:.10f}")
    _print_result("MB@VA(bin)", mb_state_tuned_bin, mb_metrics_bin)
    print(f"  target VA (uniform)  = {uni_state.va:.10f} -> nu_tilde = {nu_uni:.4f}, VA_MB = {va_uni:.10f}")
    _print_result("MB@VA(uni)", mb_state_tuned_uni, mb_metrics_uni)


if __name__ == "__main__":
    main()
