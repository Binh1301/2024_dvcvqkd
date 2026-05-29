"""
SKR = 0 boundary sensitivity analysis.

Baseline: T_eff = 0.132129, eps = 0.001, eta = 0.95, v_el = 0.001, beta = 0.95, alpha0 = 2.
Find T_eff_min(param) such that SKR = 0 for each parameter value.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1.channel.channel_model import channel
    from uav_hap_1.config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_NCUT_BINOMIAL,
        LAMBDA,
        kruse_xi_per_km,
    )
    from uav_hap_1.protocol.qam_protocol import build_state_binomial, compute_metrics
else:
    from .channel.channel_model import channel
    from .config import (
        ChannelParams,
        GeometryParams,
        QAM_ALPHA0_BINOMIAL,
        QAM_NCUT_BINOMIAL,
        LAMBDA,
        kruse_xi_per_km,
    )
    from .protocol.qam_protocol import build_state_binomial, compute_metrics


BASELINE = {
    "T_eff": 0.132129,
    "eps": 0.001,
    "eta": 0.95,
    "v_el": 0.001,
    "beta": 0.95,
    "alpha0": 2.0,
}

SKR_TARGET = 0.0
SKR_TOL = 1e-8
N_SAMPLES = 30_000
H_HAP_DEFAULT = 20_000.0
XI_FIXED = 0.09232


def _compute_skr(state, T_eff: float, eps: float, beta: float, eta: float, v_el: float) -> float:
    metrics = compute_metrics(state, float(T_eff), float(eps), float(beta), float(eta), float(v_el))
    return float(metrics.skr_raw)


def _channel_t_eff(
    geometry: GeometryParams,
    channel_params: ChannelParams,
    L_override_m: float | None = None,
    seed: int = 42,
) -> dict:
    rng = np.random.default_rng(seed)
    return channel(
        geometry=geometry,
        channel_params=channel_params,
        N=N_SAMPLES,
        rng=rng,
        L_override_m=L_override_m,
    )


def _bisect_t_eff(state, eps: float, beta: float, eta: float, v_el: float, t_min: float = 0.01, t_max: float = 0.5) -> float:
    """Find T_eff such that SKR = 0 using bisection."""
    s_min = _compute_skr(state, t_min, eps, beta, eta, v_el)
    s_max = _compute_skr(state, t_max, eps, beta, eta, v_el)
    if s_min > SKR_TARGET and s_max > SKR_TARGET:
        print(f"[WARN] SKR > 0 across T_eff in [{t_min}, {t_max}] for params; no root.")
        return float("nan")
    if s_min < SKR_TARGET and s_max < SKR_TARGET:
        print(f"[WARN] SKR < 0 across T_eff in [{t_min}, {t_max}] for params; no root.")
        return float("nan")
    for _ in range(100):
        t_mid = (t_min + t_max) / 2.0
        skr = _compute_skr(state, t_mid, eps, beta, eta, v_el)
        if abs(skr - SKR_TARGET) < SKR_TOL:
            return float(t_mid)
        if skr > SKR_TARGET:
            t_max = t_mid
        else:
            t_min = t_mid
        if t_max - t_min < 1e-10:
            break
    return float((t_min + t_max) / 2.0)


def _bisect_xi(geom: GeometryParams, ch_base: ChannelParams, T_eff_target: float, xi_min: float = 0.01, xi_max: float = 0.5) -> float:
    """Find xi_per_km such that T_eff = T_eff_target using bisection."""
    for _ in range(100):
        xi_mid = (xi_min + xi_max) / 2.0
        ch_params = replace(ch_base, xi_per_km=float(xi_mid))
        fading = _channel_t_eff(geometry=geom, channel_params=ch_params)
        t_eff = float(fading["T_eff"])
        if abs(t_eff - T_eff_target) < 1e-6:
            return float(xi_mid)
        if t_eff > T_eff_target:
            xi_min = xi_mid
        else:
            xi_max = xi_mid
        if xi_max - xi_min < 1e-10:
            break
    return float((xi_min + xi_max) / 2.0)


def _bisect_l_km(geom: GeometryParams, ch_base: ChannelParams, T_eff_target: float, l_min: float = 1.0, l_max: float = 200.0) -> float:
    """Find L(km) such that T_eff = T_eff_target using bisection."""
    for _ in range(100):
        l_mid = (l_min + l_max) / 2.0
        fading = _channel_t_eff(
            geometry=geom,
            channel_params=ch_base,
            L_override_m=float(l_mid) * 1000.0,
        )
        t_eff = float(fading["T_eff"])
        if abs(t_eff - T_eff_target) < 1e-6:
            return float(l_mid)
        if t_eff > T_eff_target:
            l_min = l_mid
        else:
            l_max = l_mid
        if l_max - l_min < 1e-10:
            break
    return float((l_min + l_max) / 2.0)


def _bisect_h_hap(ch_params: ChannelParams, T_eff_target: float, h_min: float = 5000.0, h_max: float = 50000.0) -> float:
    """Find H_HAP such that T_eff = T_eff_target using bisection."""
    for _ in range(100):
        h_mid = (h_min + h_max) / 2.0
        geom = GeometryParams(H_HAP_m=float(h_mid), H_UAV_m=0.0)
        fading = _channel_t_eff(geometry=geom, channel_params=ch_params)
        t_eff = float(fading["T_eff"])
        if abs(t_eff - T_eff_target) < 1e-6:
            return float(h_mid)
        if t_eff > T_eff_target:
            h_min = h_mid
        else:
            h_max = h_mid
        if h_max - h_min < 1e-10:
            break
    return float((h_min + h_max) / 2.0)


def _vis_from_xi(xi_per_km: float, v_min: float = 0.5, v_max: float = 100.0) -> float:
    """Invert Kruse model to get visibility from xi."""
    xi_low = kruse_xi_per_km(v_max, wavelength_m=LAMBDA)
    xi_high = kruse_xi_per_km(v_min, wavelength_m=LAMBDA)
    if not (xi_low <= xi_per_km <= xi_high):
        return np.nan
    for _ in range(100):
        v_mid = 0.5 * (v_min + v_max)
        xi_mid = kruse_xi_per_km(v_mid, wavelength_m=LAMBDA)
        if abs(xi_mid - xi_per_km) < 1e-5:
            return float(v_mid)
        if xi_mid > xi_per_km:
            v_min = v_mid
        else:
            v_max = v_mid
        if v_max - v_min < 1e-6:
            break
    return float(0.5 * (v_min + v_max))


def _format_float(value: float, fmt: str = "{:.6f}") -> str:
    if value != value or np.isinf(value):
        return "n/a"
    return fmt.format(value)


def _print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        return
    widths = [max(len(h), max(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    print(f"\n{title}")
    print("  ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers)))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(f"{row[i]:<{widths[i]}}" for i in range(len(row))))


def _sensitivity_1d() -> dict[str, list[float]]:
    geom = GeometryParams(H_HAP_m=H_HAP_DEFAULT, H_UAV_m=0.0)
    ch_base = ChannelParams(visibility_km=10.0, xi_per_km=None)
    ch_fixed_xi = ChannelParams(visibility_km=10.0, xi_per_km=XI_FIXED)

    state_baseline = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    sensitivity = {}

    print("\n" + "=" * 100)
    print("1D Sensitivity: T_eff_min for SKR = 0")
    print("=" * 100)

    # a) eps sweep
    eps_values = [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.05]
    rows = []
    t_values = []
    for eps in eps_values:
        t_min = _bisect_t_eff(state_baseline, eps, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
        if not np.isnan(t_min):
            xi_max = _bisect_xi(geom, ch_base, t_min)
            h_hap_max = _bisect_h_hap(ch_fixed_xi, t_min) / 1000.0
            vis_min = _vis_from_xi(xi_max)
            t_values.append(t_min)
        else:
            xi_max = float("nan")
            h_hap_max = float("nan")
            vis_min = float("nan")
        rows.append(
            [
                "eps",
                f"{eps:.4g}",
                f"{t_min:.6f}",
                f"{xi_max:.6f}",
                _format_float(h_hap_max, "{:.1f}"),
                _format_float(vis_min, "{:.1f}"),
            ]
        )
    sensitivity["eps"] = t_values
    _print_table("a) eps sweep", ["Param", "Value", "T_min", "xi_max(/km)", "H_HAP_max(km)", "Vis_min(km)"], rows)

    # b) eta sweep
    eta_values = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
    rows = []
    t_values = []
    for eta in eta_values:
        t_min = _bisect_t_eff(state_baseline, BASELINE["eps"], BASELINE["beta"], eta, BASELINE["v_el"])
        if not np.isnan(t_min):
            xi_max = _bisect_xi(geom, ch_base, t_min)
            h_hap_max = _bisect_h_hap(ch_fixed_xi, t_min) / 1000.0
            vis_min = _vis_from_xi(xi_max)
            t_values.append(t_min)
        else:
            xi_max = float("nan")
            h_hap_max = float("nan")
            vis_min = float("nan")
        rows.append(
            [
                "eta",
                f"{eta:.2f}",
                f"{t_min:.6f}",
                f"{xi_max:.6f}",
                _format_float(h_hap_max, "{:.1f}"),
                _format_float(vis_min, "{:.1f}"),
            ]
        )
    sensitivity["eta"] = t_values
    _print_table("b) eta sweep", ["Param", "Value", "T_min", "xi_max(/km)", "H_HAP_max(km)", "Vis_min(km)"], rows)

    # c) v_el sweep
    v_el_values = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]
    rows = []
    t_values = []
    for v_el in v_el_values:
        t_min = _bisect_t_eff(state_baseline, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], v_el)
        if not np.isnan(t_min):
            xi_max = _bisect_xi(geom, ch_base, t_min)
            h_hap_max = _bisect_h_hap(ch_fixed_xi, t_min) / 1000.0
            vis_min = _vis_from_xi(xi_max)
            t_values.append(t_min)
        else:
            xi_max = float("nan")
            h_hap_max = float("nan")
            vis_min = float("nan")
        rows.append(
            [
                "v_el",
                f"{v_el:.4g}",
                f"{t_min:.6f}",
                f"{xi_max:.6f}",
                _format_float(h_hap_max, "{:.1f}"),
                _format_float(vis_min, "{:.1f}"),
            ]
        )
    sensitivity["v_el"] = t_values
    _print_table("c) v_el sweep", ["Param", "Value", "T_min", "xi_max(/km)", "H_HAP_max(km)", "Vis_min(km)"], rows)

    # d) alpha0 sweep
    alpha0_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    rows = []
    t_values = []
    for alpha0 in alpha0_values:
        ncut = max(45, int(3.0 * float(alpha0) ** 2) + 10)
        state = build_state_binomial(float(alpha0), ncut)
        t_min = _bisect_t_eff(state, BASELINE["eps"], BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"])
        if not np.isnan(t_min):
            xi_max = _bisect_xi(geom, ch_base, t_min)
            h_hap_max = _bisect_h_hap(ch_fixed_xi, t_min) / 1000.0
            vis_min = _vis_from_xi(xi_max)
            t_values.append(t_min)
        else:
            xi_max = float("nan")
            h_hap_max = float("nan")
            vis_min = float("nan")
        rows.append(
            [
                "alpha0",
                f"{alpha0:.1f}",
                f"{t_min:.6f}",
                f"{xi_max:.6f}",
                _format_float(h_hap_max, "{:.1f}"),
                _format_float(vis_min, "{:.1f}"),
            ]
        )
    sensitivity["alpha0"] = t_values
    _print_table("d) alpha0 sweep", ["Param", "Value", "T_min", "xi_max(/km)", "H_HAP_max(km)", "Vis_min(km)"], rows)

    # e) beta sweep
    beta_values = [0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
    rows = []
    t_values = []
    for beta in beta_values:
        t_min = _bisect_t_eff(state_baseline, BASELINE["eps"], beta, BASELINE["eta"], BASELINE["v_el"])
        if not np.isnan(t_min):
            xi_max = _bisect_xi(geom, ch_base, t_min)
            h_hap_max = _bisect_h_hap(ch_fixed_xi, t_min) / 1000.0
            vis_min = _vis_from_xi(xi_max)
            t_values.append(t_min)
        else:
            xi_max = float("nan")
            h_hap_max = float("nan")
            vis_min = float("nan")
        rows.append(
            [
                "beta",
                f"{beta:.2f}",
                f"{t_min:.6f}",
                f"{xi_max:.6f}",
                _format_float(h_hap_max, "{:.1f}"),
                _format_float(vis_min, "{:.1f}"),
            ]
        )
    sensitivity["beta"] = t_values
    _print_table("e) beta sweep", ["Param", "Value", "T_min", "xi_max(/km)", "H_HAP_max(km)", "Vis_min(km)"], rows)
    return sensitivity


def _print_sign_grid(title: str, x_label: str, x_values: list[float], y_label: str, y_values: list[float], func) -> None:
    print("\n" + title)
    print(f"\n{y_label}\\{x_label}", end="")
    for x in x_values:
        print(f"  {x:.3g}", end="")
    print()
    print("-" * (12 + 8 * len(x_values)))
    for y in y_values:
        print(f"{y:.3g}    ", end="")
        for x in x_values:
            marker = "+" if func(x, y) > 0 else "-"
            print(f"  {marker:>6s}", end="")
        print()


def _sensitivity_2d() -> None:
    state_baseline = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)

    print("\n" + "=" * 100)
    print("2D Sensitivity: Sign of SKR_raw")
    print("=" * 100)

    eps_values = np.logspace(np.log10(1e-4), np.log10(0.1), 8)
    eta_values = np.linspace(0.5, 0.99, 8)
    t_values = np.linspace(0.05, 0.35, 8)

    _print_sign_grid(
        title="T_eff vs eps (+ = SKR > 0, - = SKR < 0)",
        x_label="eps",
        x_values=list(eps_values),
        y_label="T_eff",
        y_values=list(t_values),
        func=lambda eps, t: _compute_skr(state_baseline, t, eps, BASELINE["beta"], BASELINE["eta"], BASELINE["v_el"]),
    )

    _print_sign_grid(
        title="T_eff vs eta (+ = SKR > 0, - = SKR < 0)",
        x_label="eta",
        x_values=list(eta_values),
        y_label="T_eff",
        y_values=list(t_values),
        func=lambda eta, t: _compute_skr(state_baseline, t, BASELINE["eps"], BASELINE["beta"], eta, BASELINE["v_el"]),
    )

    _print_sign_grid(
        title="eps vs eta @ T_eff=0.132 (+ = SKR > 0, - = SKR < 0)",
        x_label="eps",
        x_values=list(eps_values),
        y_label="eta",
        y_values=list(eta_values),
        func=lambda eps, eta: _compute_skr(state_baseline, BASELINE["T_eff"], eps, BASELINE["beta"], eta, BASELINE["v_el"]),
    )


def _sensitivity_conclusion(sensitivity: dict[str, list[float]]) -> None:
    print("\n" + "=" * 100)
    print("Summary and Conclusions")
    print("=" * 100)

    geom = GeometryParams(H_HAP_m=H_HAP_DEFAULT, H_UAV_m=0.0)
    ch_base = ChannelParams(visibility_km=10.0, xi_per_km=None)
    ch_fixed_xi = ChannelParams(visibility_km=10.0, xi_per_km=XI_FIXED)
    state_baseline = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)

    t_baseline = _bisect_t_eff(
        state_baseline,
        BASELINE["eps"],
        BASELINE["beta"],
        BASELINE["eta"],
        BASELINE["v_el"],
    )

    xi_baseline = _bisect_xi(geom, ch_base, t_baseline)
    h_hap_baseline = _bisect_h_hap(ch_fixed_xi, t_baseline) / 1000.0
    vis_baseline = _vis_from_xi(xi_baseline)

    print(f"\nBaseline (H_HAP={H_HAP_DEFAULT/1000:.0f}km):")
    print(f"  T_eff_min = {t_baseline:.6f}")
    print(f"  xi_max = {xi_baseline:.6f} /km")
    print(f"  H_HAP_max (xi={XI_FIXED:.5f}/km) = {h_hap_baseline:.1f} km")
    print(f"  Vis_min = {_format_float(vis_baseline, '{:.1f}')} km")

    deltas = {k: (max(v) - min(v)) if v else 0.0 for k, v in sensitivity.items()}
    most_sensitive = max(deltas, key=deltas.get)
    least_sensitive = min(deltas, key=deltas.get)

    print("\nSensitivity ranking (by ΔT_eff_min across sweep):")
    print(f"  Most sensitive: {most_sensitive} (ΔT_eff_min={deltas[most_sensitive]:.6f})")
    print(f"  Least sensitive: {least_sensitive} (ΔT_eff_min={deltas[least_sensitive]:.6f})")

    print("\nRecommended configs:")
    print("  Realistic: eta <= 0.95, eps >= 0.001, v_el >= 0.001")
    print("  Ideal: eta = 0.99, eps = 0.0001, v_el = 0")

    print("\nĐể SKR > 0 tại H_HAP = 20km, cần:")
    print(f"1. T_eff >= {t_baseline:.6f}")
    print(f"2. xi_per_km <= {xi_baseline:.6f}")
    print(f"3. visibility >= {_format_float(vis_baseline, '{:.1f}')} km")
    print(f"4. eps <= {BASELINE['eps']:.4g} (giữ như baseline)")
    print(f"5. eta >= {BASELINE['eta']:.2f} (giữ như baseline)")


def main() -> None:
    sensitivity = _sensitivity_1d()
    _sensitivity_2d()
    _sensitivity_conclusion(sensitivity)


if __name__ == "__main__":
    main()
