"""
Compute and report T_eff for the channel model.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import replace

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1_sample.channel.channel_model import channel
    from uav_hap_1_sample.config import ChannelParams, GeometryParams
else:
    from .channel.channel_model import channel
    from .config import ChannelParams, GeometryParams


N_SAMPLES = 30_000
SKR_T_EFF_THRESHOLD = 0.317


def _build_channel_params(args) -> ChannelParams:
    base = ChannelParams(
        a_m=float(args.a_m),
        W0_m=float(args.W0),
        visibility_km=float(args.visibility),
        xi_per_km=None,
    )
    scale = max(float(args.sigma_scale), 0.0)
    return replace(
        base,
        sigma_theta_rad=float(base.sigma_theta_rad) * scale,
        sigma_phi_rad=float(base.sigma_phi_rad) * scale,
        sigma_psi_rad=float(base.sigma_psi_rad) * scale,
    )


def _build_geometry(args) -> GeometryParams:
    return GeometryParams(H_HAP_m=float(args.H_HAP), H_UAV_m=float(args.H_UAV))


def _compute_channel(geom: GeometryParams, ch_params: ChannelParams, rng, L_override_m=None) -> dict:
    return channel(
        geometry=geom,
        channel_params=ch_params,
        N=N_SAMPLES,
        rng=rng,
        L_override_m=L_override_m,
    )


def _print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    line = "  ".join(h.ljust(widths[idx]) for idx, h in enumerate(headers))
    sep = "  ".join("-" * widths[idx] for idx in range(len(headers)))
    print(f"\n{title}")
    print(line)
    print(sep)
    for row in rows:
        print("  ".join(row[idx].rjust(widths[idx]) for idx in range(len(headers))))


def _sweep_tables(args) -> None:
    rng = np.random.default_rng(42)
    geom = _build_geometry(args)
    ch_params = _build_channel_params(args)

    # a) T_eff vs L
    L_km_values = np.arange(1.0, 50.1, 5.0)
    rows = []
    for L_km in L_km_values:
        fading = _compute_channel(geom, ch_params, rng, L_override_m=float(L_km) * 1000.0)
        rows.append([f"{L_km:6.1f}", f"{fading['T_eff']:.6f}"])
    _print_table("T_eff vs L (km)", ["L_km", "T_eff"], rows)

    # b) T_eff vs aperture radius
    a_values = np.arange(0.10, 0.51, 0.05)
    rows = []
    for a_m in a_values:
        ch_params_a = replace(ch_params, a_m=float(a_m))
        fading = _compute_channel(geom, ch_params_a, rng)
        rows.append([f"{a_m:6.2f}", f"{fading['T_eff']:.6f}"])
    _print_table("T_eff vs aperture radius", ["a_m", "T_eff"], rows)

    # c) T_eff vs H_HAP
    H_values = np.arange(5000.0, 30000.1, 5000.0)
    rows = []
    for H_HAP in H_values:
        geom_h = replace(geom, H_HAP_m=float(H_HAP))
        fading = _compute_channel(geom_h, ch_params, rng)
        rows.append([f"{H_HAP:7.0f}", f"{fading['L_km']:.3f}", f"{fading['T_eff']:.6f}"])
    _print_table("T_eff vs H_HAP", ["H_HAP_m", "L_km", "T_eff"], rows)


def _print_detailed(args) -> None:
    rng = np.random.default_rng(42)
    geom = _build_geometry(args)
    ch_params = _build_channel_params(args)

    L_override_m = float(args.L) if args.L is not None else None
    fading = _compute_channel(geom, ch_params, rng, L_override_m=L_override_m)

    print("Channel summary:")
    print(f"L_m: {fading['L_m']:.2f} m (L_km: {fading['L_km']:.3f} km)")
    print(f"eta_atm: {fading['eta_atm']:.6f}")
    print(f"W_L (beam radius): {fading['W_L_m']:.6f} m")
    print(f"sigma_r: {fading['sigma_r_m']:.6e} m")
    print(f"T0 (peak coupling): {fading['T0_amp']:.6f}")
    print(f"Gamma: {fading['Gamma']:.6f}")
    print(f"R_m: {fading['R_m']:.6f} m")
    print(f"mean_T2: {fading['mean_T2']:.6f}")
    print(f"T_eff: {fading['T_eff']:.6f}")

    ok = "YES" if float(fading["T_eff"]) >= SKR_T_EFF_THRESHOLD else "NO"
    print(f"SKR viability (T_eff >= {SKR_T_EFF_THRESHOLD:.3f}): {ok}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute T_eff from the channel model.")
    parser.add_argument("--H_HAP", type=float, default=20000.0, help="HAP altitude (m).")
    parser.add_argument("--H_UAV", type=float, default=0.0, help="UAV altitude (m).")
    parser.add_argument("--a_m", type=float, default=0.20, help="Aperture radius (m).")
    parser.add_argument("--W0", type=float, default=0.0626, help="Beam waist (m).")
    parser.add_argument("--visibility", type=float, default=10.0, help="Visibility (km).")
    parser.add_argument("--sigma_scale", type=float, default=1.0, help="Scale factor for pointing error.")
    parser.add_argument("--L", type=float, default=None, help="Override link distance (m).")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if len(sys.argv) == 1:
        _sweep_tables(args)
    else:
        _print_detailed(args)


if __name__ == "__main__":
    main()
