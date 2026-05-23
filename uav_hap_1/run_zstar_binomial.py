"""
Compute Z* and key metrics for QAM-256 (binomial).

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
    from uav_hap_1.channel.channel_model import channel
    from uav_hap_1.config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_V_EL,
    )
    from uav_hap_1.protocol.qam_protocol import build_state_binomial, compute_metrics
else:
    from .channel.channel_model import channel
    from .config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_V_EL,
    )
    from .protocol.qam_protocol import build_state_binomial, compute_metrics


def main() -> None:
    geom = GeometryParams()
    ch_params = ChannelParams()
    fading = channel(geometry=geom, channel_params=ch_params, N=30_000, rng=np.random.default_rng(42))
    T_eff = float(fading["T_eff"])

    state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    metrics = compute_metrics(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)

    print("=" * 70)
    print("QAM-256 Binomial")
    print("=" * 70)
    print(f"T_eff   = {T_eff:.6f}")
    print(f"alpha0  = {state.alpha0:.6f}, Ncut = {state.ncut}")
    print(f"VA      = {state.va:.10f}")
    print(f"Tr(tau) = {state.tr_tau:.10f}, rank = {state.rank}")
    print(f"Tr(C)   = {state.tr_c:.10f}")
    print(f"w       = {state.w:.10f}")
    print("-" * 70)
    print(f"Z*_raw  = {metrics.z_star_raw:.10f}")
    print(f"Z*      = {metrics.z_star:.10f}")
    if metrics.z_star_clipped:
        print(f"Z* clipped to Z*_max = {metrics.z_star_max:.10f}")
    print(f"chi_BE  = {metrics.chi_be:.10f}")
    print(f"I_AB    = {metrics.i_ab:.10f}")
    print(f"SKR_raw = {metrics.skr_raw:.10f}")
    print(f"SKR     = {metrics.skr:.10f}")


if __name__ == "__main__":
    main()
