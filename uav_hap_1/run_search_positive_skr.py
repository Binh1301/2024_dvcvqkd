"""
Search parameter regions where SKR_raw > 0 and physical constraints hold.

Outputs:
- CSV of sweep results
- Summary plots for SKR vs T, eps, v_el at best-physical configurations
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1.config import (
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
    from uav_hap_1.protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from uav_hap_1.zstar import mb as zmb
else:
    from .config import (
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


def _status(metrics) -> str:
    if metrics.z_star_clipped:
        return "clipped"
    if metrics.z_star_raw < 0 or metrics.z_star_raw > metrics.z_star_max:
        return "unphysical"
    return "physical"


def _write_csv(csv_path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _plot_summary(x_values, series, xlabel, out_path: Path, title: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("matplotlib not available: skipping plot", out_path)
        return

    fig, ax = plt.subplots(figsize=(8.4, 5.0), constrained_layout=True)
    for item in series:
        ax.plot(x_values, item["skr"], lw=2.0, label=item["label"])
        clipped_mask = item["status"] == "clipped"
        unphys_mask = item["status"] == "unphysical"
        if np.any(clipped_mask):
            ax.scatter(x_values[clipped_mask], item["skr"][clipped_mask], marker="x", s=50, color="orange")
        if np.any(unphys_mask):
            ax.scatter(x_values[unphys_mask], item["skr"][unphys_mask], marker="x", s=50, color="red")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("SKR (bits/use)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


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
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Parameter grids (coarse search)
    T_grid = np.array([0.05, 0.08, 0.12, 0.2, 0.3, 0.5, 0.7, 0.9])
    eps_grid = np.array([0.0, 0.002, 0.005, 0.01, 0.02])
    eta_grid = np.array([0.6, 0.8, 0.95, 0.99])
    v_el_grid = np.array([0.0, 0.002, 0.005, 0.01, 0.02])
    nu_grid = np.linspace(0.02, 0.6, 40)

    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    uni_state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
    mb_state_fixed = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)

    # Quick convergence checks (print-only diagnostics)
    bin_state_hi = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL + 10)
    uni_state_hi = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM + 30)
    mb_state_hi = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB + 30, QAM_NU_TILDE)
    print("=" * 70)
    print("Ncut convergence check (VA, TrC, w):")
    print(
        f"  Binomial: Ncut {QAM_NCUT_BINOMIAL} -> {QAM_NCUT_BINOMIAL + 10} | "
        f"VA {bin_state.va:.6f} -> {bin_state_hi.va:.6f}, "
        f"TrC {bin_state.tr_c:.6f} -> {bin_state_hi.tr_c:.6f}, "
        f"w {bin_state.w:.6f} -> {bin_state_hi.w:.6f}"
    )
    print(
        f"  Uniform : Ncut {QAM_NCUT_UNIFORM} -> {QAM_NCUT_UNIFORM + 30} | "
        f"VA {uni_state.va:.6f} -> {uni_state_hi.va:.6f}, "
        f"TrC {uni_state.tr_c:.6f} -> {uni_state_hi.tr_c:.6f}, "
        f"w {uni_state.w:.6f} -> {uni_state_hi.w:.6f}"
    )
    print(
        f"  MB      : Ncut {QAM_NCUT_MB} -> {QAM_NCUT_MB + 30} | "
        f"VA {mb_state_fixed.va:.6f} -> {mb_state_hi.va:.6f}, "
        f"TrC {mb_state_fixed.tr_c:.6f} -> {mb_state_hi.tr_c:.6f}, "
        f"w {mb_state_fixed.w:.6f} -> {mb_state_hi.w:.6f}"
    )
    print("=" * 70)

    nu_tuned_bin, va_tuned_bin = _tune_nu_tilde(bin_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid)
    mb_state_tuned = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_tuned_bin)

    rows: list[dict] = []
    best = {
        "binomial": None,
        "uniform": None,
        "mb_fixed": None,
        "mb_tuned": None,
    }
    counts = {
        "binomial": {"physical": 0, "clipped": 0, "unphysical": 0},
        "uniform": {"physical": 0, "clipped": 0, "unphysical": 0},
        "mb_fixed": {"physical": 0, "clipped": 0, "unphysical": 0},
        "mb_tuned": {"physical": 0, "clipped": 0, "unphysical": 0},
    }

    def evaluate(label, state, T, eps, eta, v_el, mode, nu_tilde):
        metrics = compute_metrics(state, T, eps, QAM_BETA, eta, v_el)
        status = _status(metrics)
        if label != "mb":
            key = label
        else:
            key = "mb_fixed" if mode == "fixed" else "mb_tuned"
        row = {
            "mode": mode,
            "distribution": label,
            "T": float(T),
            "eps": float(eps),
            "eta": float(eta),
            "v_el": float(v_el),
            "nu_tilde": nu_tilde,
            "va": state.va,
            "z_star_raw": metrics.z_star_raw,
            "z_star": metrics.z_star,
            "z_star_max": metrics.z_star_max,
            "z_star_clipped": metrics.z_star_clipped,
            "chi_be": metrics.chi_be,
            "i_ab": metrics.i_ab,
            "skr_raw": metrics.skr_raw,
            "skr": metrics.skr,
            "status": status,
        }
        rows.append(row)
        counts[key][status] += 1
        if status == "physical" and metrics.skr_raw > 0:
            prev = best.get(key)
            if prev is None or metrics.skr_raw > prev["skr_raw"]:
                best[key] = row

    for T in T_grid:
        for eps in eps_grid:
            for eta in eta_grid:
                for v_el in v_el_grid:
                    evaluate("binomial", bin_state, T, eps, eta, v_el, "fixed", None)
                    evaluate("uniform", uni_state, T, eps, eta, v_el, "fixed", None)
                    evaluate("mb", mb_state_fixed, T, eps, eta, v_el, "fixed", QAM_NU_TILDE)
                    evaluate("mb", mb_state_tuned, T, eps, eta, v_el, "fixed_va", nu_tuned_bin)

    csv_path = out_dir / "qam_search_positive_skr.csv"
    _write_csv(csv_path, rows)

    # Build summary plots around best-physical configs (if found)
    def build_sweep_series(label, state, mode, nu_tilde, fixed_eps, fixed_eta, fixed_v_el):
        T_vals = np.linspace(0.05, 0.95, 30)
        eps_vals = np.linspace(0.0, 0.03, 30)
        v_vals = np.linspace(0.0, 0.05, 31)

        def sweep_x(x_vals, sweep_name):
            skr = []
            status = []
            for x in x_vals:
                if sweep_name == "T":
                    metrics = compute_metrics(state, float(x), fixed_eps, QAM_BETA, fixed_eta, fixed_v_el)
                elif sweep_name == "eps":
                    metrics = compute_metrics(state, fixed_T, float(x), QAM_BETA, fixed_eta, fixed_v_el)
                else:
                    metrics = compute_metrics(state, fixed_T, fixed_eps, QAM_BETA, fixed_eta, float(x))
                skr.append(metrics.skr)
                status.append(_status(metrics))
            return np.array(skr), np.array(status, dtype=object)

        fixed_T = 0.5
        skr_T, status_T = sweep_x(T_vals, "T")
        skr_eps, status_eps = sweep_x(eps_vals, "eps")
        skr_v, status_v = sweep_x(v_vals, "v_el")
        return (T_vals, skr_T, status_T), (eps_vals, skr_eps, status_eps), (v_vals, skr_v, status_v)

    # Use default comparison baseline for plotting
    series_T = []
    series_eps = []
    series_v = []

    bin_T, bin_eps, bin_v = build_sweep_series(
        "binomial", bin_state, "fixed", None, QAM_EPS, QAM_ETA, QAM_V_EL
    )
    uni_T, uni_eps, uni_v = build_sweep_series(
        "uniform", uni_state, "fixed", None, QAM_EPS, QAM_ETA, QAM_V_EL
    )
    mb_T, mb_eps, mb_v = build_sweep_series(
        "mb", mb_state_tuned, "fixed_va", nu_tuned_bin, QAM_EPS, QAM_ETA, QAM_V_EL
    )

    series_T = [
        {"label": "binomial", "skr": bin_T[1], "status": bin_T[2]},
        {"label": "uniform", "skr": uni_T[1], "status": uni_T[2]},
        {"label": f"mb (nu={nu_tuned_bin:.3f})", "skr": mb_T[1], "status": mb_T[2]},
    ]
    series_eps = [
        {"label": "binomial", "skr": bin_eps[1], "status": bin_eps[2]},
        {"label": "uniform", "skr": uni_eps[1], "status": uni_eps[2]},
        {"label": f"mb (nu={nu_tuned_bin:.3f})", "skr": mb_eps[1], "status": mb_eps[2]},
    ]
    series_v = [
        {"label": "binomial", "skr": bin_v[1], "status": bin_v[2]},
        {"label": "uniform", "skr": uni_v[1], "status": uni_v[2]},
        {"label": f"mb (nu={nu_tuned_bin:.3f})", "skr": mb_v[1], "status": mb_v[2]},
    ]

    _plot_summary(bin_T[0], series_T, "T_eff", out_dir / "search_skr_vs_T.png", "SKR vs T_eff")
    _plot_summary(bin_eps[0], series_eps, "eps", out_dir / "search_skr_vs_eps.png", "SKR vs eps")
    _plot_summary(bin_v[0], series_v, "v_el", out_dir / "search_skr_vs_v_el.png", "SKR vs v_el")

    print("=" * 70)
    print("Search summary")
    print("=" * 70)
    print(f"CSV saved: {csv_path}")
    print(f"Plots saved: {out_dir / 'search_skr_vs_T.png'}, {out_dir / 'search_skr_vs_eps.png'}, {out_dir / 'search_skr_vs_v_el.png'}")
    print("Status counts:")
    for key, stats in counts.items():
        print(f"  {key}: physical={stats['physical']}, clipped={stats['clipped']}, unphysical={stats['unphysical']}")
    if best["binomial"]:
        print(f"Best binomial (physical, SKR_raw>0): {best['binomial']}")
    else:
        print("No physical binomial point with SKR_raw>0 in grid.")
    if best["uniform"]:
        print(f"Best uniform (physical, SKR_raw>0): {best['uniform']}")
    else:
        print("No physical uniform point with SKR_raw>0 in grid.")
    if best["mb_fixed"]:
        print(f"Best MB fixed nu_tilde (physical, SKR_raw>0): {best['mb_fixed']}")
    else:
        print("No physical MB fixed-nu point with SKR_raw>0 in grid.")
    if best["mb_tuned"]:
        print(f"Best MB tuned (physical, SKR_raw>0): {best['mb_tuned']}")
    else:
        print("No physical MB tuned point with SKR_raw>0 in grid.")


if __name__ == "__main__":
    main()
