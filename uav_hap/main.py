from dataclasses import replace
from typing import Optional
import os
import sys
import argparse

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap.channel.channel_model import channel
    from uav_hap.config import (
        ChannelParams,
        FiniteSizeParams,
        GeometryParams,
        MonteCarloParams,
        NoiseParams,
        SecurityParams,
    )
    from uav_hap.protocols.gm import noise, skr
    from uav_hap.reconciliation.finite_size import finite_size_key_rate
else:
    from .channel.channel_model import channel
    from .config import (
        ChannelParams,
        FiniteSizeParams,
        GeometryParams,
        MonteCarloParams,
        NoiseParams,
        SecurityParams,
    )
    from .protocols.gm import noise, skr
    from .reconciliation.finite_size import finite_size_key_rate


def simulate_uav_hap_cvqkd(
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    L_m: Optional[float] = None,
    sigma_r_m: Optional[float] = None,
    xi_phase: Optional[float] = None,
    N: Optional[int] = None,
    n: Optional[int] = None,
    histogram_bins: Optional[int] = 50,
) -> dict:
    geom = GeometryParams() if geometry is None else geometry
    ch_cfg = ChannelParams() if channel_params is None else channel_params
    nz_cfg = NoiseParams() if noise_params is None else noise_params
    sec_cfg = SecurityParams() if security_params is None else security_params
    mc_cfg = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs_cfg = FiniteSizeParams() if finite_size is None else finite_size

    if L_m is not None:
        geom = replace(geom, H_HAP_m=float(geom.H_UAV_m) + float(L_m), tilt_deg=0.0)
    if sigma_r_m is not None:
        ch_cfg = replace(ch_cfg, sigma_r_m=float(sigma_r_m))
    if xi_phase is not None:
        nz_cfg = replace(nz_cfg, xi_phase=float(xi_phase))
    if N is not None:
        mc_cfg = replace(mc_cfg, N=int(N))
    if n is not None:
        fs_cfg = replace(fs_cfg, n=int(n))

    rng = np.random.default_rng(mc_cfg.seed)
    fading = channel(
        geometry=geom,
        channel_params=ch_cfg,
        N=int(mc_cfg.N),
        rng=rng,
        L_override_m=L_m,
    )
    T_samples = np.asarray(fading["T_samples"], dtype=float)

    noise_terms = noise(T_samples=T_samples, noise_params=nz_cfg)
    K_samples = np.asarray(
        skr(
            T_samples=T_samples,
            noise_terms=noise_terms,
            security_params=sec_cfg,
            detection=nz_cfg.detection,
        ),
        dtype=float,
    )

    K_eff = float(np.mean(K_samples))
    K_finite = float(finite_size_key_rate(K_eff=K_eff, n=fs_cfg.n, delta_c=fs_cfg.delta_c))
    P_out = float(np.mean(K_samples < 0.0))

    result = {
        "K_eff": K_eff,
        "K_finite": K_finite,
        "P_out": P_out,
        "T_samples": T_samples,
        "K_samples": K_samples,
        "X_tot_samples": noise_terms["X_tot"],
        "X_line_samples": noise_terms["X_line"],
        "X_D": noise_terms["X_D"],
        "xi_tot": noise_terms["xi_tot"],
        "L_m": fading["L_m"],
        "sigma_r_m": fading["sigma_r_m"],
        "channel_factors": {
            "eta_atm": fading["eta_atm"],
            "eta_geo": fading["eta_geo"],
            "eta_SMF": fading["eta_SMF"],
            "eta_sys": fading["eta_sys"],
        },
    }

    if histogram_bins is not None and int(histogram_bins) > 0:
        counts, edges = np.histogram(T_samples, bins=int(histogram_bins), range=(0.0, 1.0), density=False)
        result["T_histogram"] = {"counts": counts, "bin_edges": edges}

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="UAV-HAP CV-QKD simulation")
    parser.add_argument("--no-plots", action="store_true", help="Run simulation without opening plots")
    args = parser.parse_args()

    out = simulate_uav_hap_cvqkd()
    print(f"K_eff    = {out['K_eff']:.6f} bits/use")
    print(f"K_finite = {out['K_finite']:.6f} bits/use")
    print(f"P_out    = {out['P_out']:.6f}")

    if not args.no_plots:
        if __package__ in (None, ""):
            from uav_hap.plots.performance_plots import example_usage
        else:
            from .plots.performance_plots import example_usage
        example_usage(show=True)


if __name__ == "__main__":
    main()
