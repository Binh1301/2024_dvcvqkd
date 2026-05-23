"""
Improved parameter search with better coverage and clear physical vs clipped distinction.

Features:
- Expanded parameter grids to systematically search for SKR_raw > 0
- Two-stage search: coarse grid then refined around best physical points
- Clear separation of physical/clipped/unphysical states in output
- Comprehensive CSV with all diagnostics (Ncut, convergence flags, etc.)
- Better summary reporting
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
    """Classify point as physical, clipped, or unphysical."""
    if metrics.z_star_clipped:
        return "clipped"
    if metrics.z_star_raw < 0 or metrics.z_star_raw > metrics.z_star_max:
        return "unphysical"
    return "physical"


def _write_csv(csv_path: Path, rows: list[dict]) -> None:
    """Write results to CSV."""
    if not rows:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _tune_nu_tilde(target_va: float, alpha0: float, ncut: int, grid: np.ndarray) -> tuple[float, float]:
    """Find nu_tilde that matches target VA (for fair MB comparison)."""
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


def _plot_summary(x_values, series, xlabel, out_path: Path, title: str) -> None:
    """Plot SKR vs parameter with physical/clipped distinction."""
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print(f"matplotlib not available: skipping plot {out_path}")
        return

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    for item in series:
        # Plot main line (use SKR_raw to show true value)
        ax.plot(x_values, item["skr_raw"], lw=2.0, label=item["label"], marker="o", markersize=4)

        # Mark clipped points with X
        clipped_mask = item["status"] == "clipped"
        unphys_mask = item["status"] == "unphysical"
        if np.any(clipped_mask):
            ax.scatter(
                x_values[clipped_mask],
                item["skr_raw"][clipped_mask],
                marker="x",
                s=100,
                color="orange",
                linewidths=2,
                zorder=5,
            )
        if np.any(unphys_mask):
            ax.scatter(
                x_values[unphys_mask],
                item["skr_raw"][unphys_mask],
                marker="x",
                s=100,
                color="red",
                linewidths=2,
                zorder=5,
            )

    # Add legend for markers
    from matplotlib.lines import Line2D

    legend_elements = [
        Line2D([0], [0], marker="x", color="w", markerfacecolor="orange", markersize=8, label="clipped"),
        Line2D([0], [0], marker="x", color="w", markerfacecolor="red", markersize=8, label="unphysical"),
    ]
    ax.legend(handles=ax.get_legend_handles_labels()[0] + legend_elements, frameon=False, loc="best")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("SKR_raw (bits/use)")
    ax.axhline(0, color="k", linestyle="--", alpha=0.3)
    ax.grid(alpha=0.3)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("IMPROVED PARAMETER SEARCH: Finding SKR_raw > 0 regions with physical validity")
    print("=" * 80)

    # ============================================================================
    # STAGE 1: Expanded coarse grid
    # ============================================================================
    print("\nStage 1: Building baseline states...")
    T_grid = np.array([0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95])
    eps_grid = np.array([0.0, 0.001, 0.002, 0.005, 0.01, 0.015, 0.02])
    eta_grid = np.array([0.6, 0.75, 0.9, 0.95, 0.99])
    v_el_grid = np.array([0.0, 0.001, 0.002, 0.005, 0.01, 0.015, 0.02])
    nu_grid = np.linspace(0.01, 1.0, 50)

    # Build states with updated Ncut values
    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    uni_state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
    mb_state_fixed = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)

    # Convergence diagnostics
    print(f"\nNcut convergence check (at T=0.5, eps=0.01, eta=0.95, v_el=0.005):")
    bin_state_hi = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL + 15)
    uni_state_hi = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM + 30)
    mb_state_hi = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB + 30, QAM_NU_TILDE)

    print(
        f"  Binomial: Ncut {QAM_NCUT_BINOMIAL} -> {QAM_NCUT_BINOMIAL + 15}"
        f" | VA: {bin_state.va:.6f} -> {bin_state_hi.va:.6f} (Δ={abs(bin_state.va - bin_state_hi.va):.2e})"
        f" | w: {bin_state.w:.6f} -> {bin_state_hi.w:.6f} (Δ={abs(bin_state.w - bin_state_hi.w):.2e})"
    )
    print(
        f"  Uniform : Ncut {QAM_NCUT_UNIFORM} -> {QAM_NCUT_UNIFORM + 30}"
        f" | VA: {uni_state.va:.6f} -> {uni_state_hi.va:.6f} (Δ={abs(uni_state.va - uni_state_hi.va):.2e})"
        f" | w: {uni_state.w:.6f} -> {uni_state_hi.w:.6f} (Δ={abs(uni_state.w - uni_state_hi.w):.2e})"
    )
    print(
        f"  MB      : Ncut {QAM_NCUT_MB} -> {QAM_NCUT_MB + 30}"
        f" | VA: {mb_state_fixed.va:.6f} -> {mb_state_hi.va:.6f} (Δ={abs(mb_state_fixed.va - mb_state_hi.va):.2e})"
        f" | w: {mb_state_fixed.w:.6f} -> {mb_state_hi.w:.6f} (Δ={abs(mb_state_fixed.w - mb_state_hi.w):.2e})"
    )

    # Tune MB to match binomial VA
    print(f"\nTuning MB nu_tilde to match binomial VA={bin_state.va:.6f}...")
    nu_tuned_bin, va_tuned_bin = _tune_nu_tilde(bin_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid)
    mb_state_tuned = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_tuned_bin)
    print(f"  Found: nu_tilde={nu_tuned_bin:.6f}, VA={va_tuned_bin:.6f}")

    # ============================================================================
    # STAGE 2: Grid sweep
    # ============================================================================
    print(f"\nStage 2: Sweeping expanded grid ({len(T_grid)}×{len(eps_grid)}×{len(eta_grid)}×{len(v_el_grid)} points)...")
    rows: list[dict] = []
    best = {
        "binomial_phys": None,
        "uniform_phys": None,
        "mb_fixed_phys": None,
        "mb_tuned_phys": None,
        "binomial_clipped": None,
        "uniform_clipped": None,
        "mb_fixed_clipped": None,
        "mb_tuned_clipped": None,
    }
    counts = {
        "binomial": {"physical": 0, "clipped": 0, "unphysical": 0},
        "uniform": {"physical": 0, "clipped": 0, "unphysical": 0},
        "mb_fixed": {"physical": 0, "clipped": 0, "unphysical": 0},
        "mb_tuned": {"physical": 0, "clipped": 0, "unphysical": 0},
    }

    def evaluate(label, state, ncut, T, eps, eta, v_el, mode, nu_tilde):
        metrics = compute_metrics(state, T, eps, QAM_BETA, eta, v_el)
        status = _status(metrics)
        if label != "mb":
            key = label
        else:
            key = "mb_fixed" if mode == "fixed" else "mb_tuned"

        row = {
            "distribution": label,
            "mode": mode,
            "ncut": ncut,
            "T": float(T),
            "eps": float(eps),
            "eta": float(eta),
            "v_el": float(v_el),
            "nu_tilde": nu_tilde if nu_tilde is not None else "",
            "va": state.va,
            "tr_c": state.tr_c,
            "w": state.w,
            "z_star_raw": metrics.z_star_raw,
            "z_star_max": metrics.z_star_max,
            "z_star_used": metrics.z_star,
            "z_star_clipped": metrics.z_star_clipped,
            "chi_be": metrics.chi_be,
            "i_ab": metrics.i_ab,
            "skr_raw": metrics.skr_raw,
            "skr": metrics.skr,
            "status": status,
        }
        rows.append(row)
        counts[key][status] += 1

        # Track best points (physical and clipped separately)
        if status == "physical" and metrics.skr_raw > 0:
            best_key = f"{key}_phys"
            prev = best.get(best_key)
            if prev is None or metrics.skr_raw > prev["skr_raw"]:
                best[best_key] = row
        elif status == "clipped" and metrics.skr_raw > 0:
            best_key = f"{key}_clipped"
            prev = best.get(best_key)
            if prev is None or metrics.skr_raw > prev["skr_raw"]:
                best[best_key] = row

    # Evaluate all combinations
    for T in T_grid:
        for eps in eps_grid:
            for eta in eta_grid:
                for v_el in v_el_grid:
                    evaluate("binomial", bin_state, QAM_NCUT_BINOMIAL, T, eps, eta, v_el, "fixed", None)
                    evaluate("uniform", uni_state, QAM_NCUT_UNIFORM, T, eps, eta, v_el, "fixed", None)
                    evaluate("mb", mb_state_fixed, QAM_NCUT_MB, T, eps, eta, v_el, "fixed", QAM_NU_TILDE)
                    evaluate("mb", mb_state_tuned, QAM_NCUT_MB, T, eps, eta, v_el, "tuned_va", nu_tuned_bin)

    csv_path = out_dir / "qam_search_improved.csv"
    _write_csv(csv_path, rows)
    print(f"  CSV saved: {csv_path} ({len(rows)} rows)")

    # ============================================================================
    # STAGE 3: Summary statistics
    # ============================================================================
    print("\n" + "=" * 80)
    print("SEARCH SUMMARY")
    print("=" * 80)
    print("\nStatus counts by distribution:")
    for key in ["binomial", "uniform", "mb_fixed", "mb_tuned"]:
        stats = counts[key]
        total = stats["physical"] + stats["clipped"] + stats["unphysical"]
        print(
            f"  {key:12s}: physical={stats['physical']:4d}, clipped={stats['clipped']:4d}, "
            f"unphysical={stats['unphysical']:4d}, total={total:4d}"
        )

    print("\nBest points with SKR_raw > 0 (physical only):")
    found_any = False
    for key in ["binomial_phys", "uniform_phys", "mb_fixed_phys", "mb_tuned_phys"]:
        if best[key] is not None:
            found_any = True
            row = best[key]
            print(
                f"  {key:18s}: SKR_raw={row['skr_raw']:.6f} at "
                f"T={row['T']:.4f}, eps={row['eps']:.4f}, eta={row['eta']:.4f}, v_el={row['v_el']:.4f}"
            )
            if "mb" in key and row["nu_tilde"]:
                print(f"                         nu_tilde={row['nu_tilde']:.6f}")

    if not found_any:
        print("  *** NO PHYSICAL POINTS WITH SKR_raw > 0 FOUND ***")
        print("\nBest clipped points (for reference, but NOT physical):")
        for key in ["binomial_clipped", "uniform_clipped", "mb_fixed_clipped", "mb_tuned_clipped"]:
            if best[key] is not None:
                row = best[key]
                print(
                    f"  {key:18s}: SKR_raw={row['skr_raw']:.6f} at "
                    f"T={row['T']:.4f}, eps={row['eps']:.4f}, eta={row['eta']:.4f}, v_el={row['v_el']:.4f}"
                )

    # ============================================================================
    # STAGE 4: Plots
    # ============================================================================
    print("\n" + "=" * 80)
    print("Generating summary plots...")
    print("=" * 80)

    def build_sweep_series(label, state, ncut, mode, nu_tilde, fixed_eps, fixed_eta, fixed_v_el):
        """Sweep over one parameter, build SKR curves for all three distributions."""
        T_vals = np.linspace(0.05, 0.95, 30)
        eps_vals = np.linspace(0.0, 0.03, 30)
        v_vals = np.linspace(0.0, 0.05, 31)

        def sweep_x(x_vals, sweep_name):
            skr_raw = []
            status = []
            for x in x_vals:
                fixed_T = 0.5
                if sweep_name == "T":
                    metrics = compute_metrics(state, float(x), fixed_eps, QAM_BETA, fixed_eta, fixed_v_el)
                elif sweep_name == "eps":
                    metrics = compute_metrics(state, fixed_T, float(x), QAM_BETA, fixed_eta, fixed_v_el)
                else:
                    metrics = compute_metrics(state, fixed_T, fixed_eps, QAM_BETA, fixed_eta, float(x))
                skr_raw.append(metrics.skr_raw)
                status.append(_status(metrics))
            return np.array(skr_raw), np.array(status, dtype=object)

        skr_T, status_T = sweep_x(T_vals, "T")
        skr_eps, status_eps = sweep_x(eps_vals, "eps")
        skr_v, status_v = sweep_x(v_vals, "v_el")
        return (T_vals, skr_T, status_T), (eps_vals, skr_eps, status_eps), (v_vals, skr_v, status_v)

    bin_T, bin_eps, bin_v = build_sweep_series(
        "binomial", bin_state, QAM_NCUT_BINOMIAL, "fixed", None, QAM_EPS, QAM_ETA, QAM_V_EL
    )
    uni_T, uni_eps, uni_v = build_sweep_series(
        "uniform", uni_state, QAM_NCUT_UNIFORM, "fixed", None, QAM_EPS, QAM_ETA, QAM_V_EL
    )
    mb_T, mb_eps, mb_v = build_sweep_series(
        "mb", mb_state_tuned, QAM_NCUT_MB, "tuned_va", nu_tuned_bin, QAM_EPS, QAM_ETA, QAM_V_EL
    )

    series_T = [
        {"label": "binomial", "skr_raw": bin_T[1], "status": bin_T[2]},
        {"label": "uniform", "skr_raw": uni_T[1], "status": uni_T[2]},
        {"label": f"mb (nu={nu_tuned_bin:.3f})", "skr_raw": mb_T[1], "status": mb_T[2]},
    ]
    series_eps = [
        {"label": "binomial", "skr_raw": bin_eps[1], "status": bin_eps[2]},
        {"label": "uniform", "skr_raw": uni_eps[1], "status": uni_eps[2]},
        {"label": f"mb (nu={nu_tuned_bin:.3f})", "skr_raw": mb_eps[1], "status": mb_eps[2]},
    ]
    series_v = [
        {"label": "binomial", "skr_raw": bin_v[1], "status": bin_v[2]},
        {"label": "uniform", "skr_raw": uni_v[1], "status": uni_v[2]},
        {"label": f"mb (nu={nu_tuned_bin:.3f})", "skr_raw": mb_v[1], "status": mb_v[2]},
    ]

    _plot_summary(bin_T[0], series_T, "T_eff", out_dir / "search_improved_skr_vs_T.png", "SKR_raw vs T_eff")
    _plot_summary(bin_eps[0], series_eps, "eps", out_dir / "search_improved_skr_vs_eps.png", "SKR_raw vs eps")
    _plot_summary(bin_v[0], series_v, "v_el", out_dir / "search_improved_skr_vs_v_el.png", "SKR_raw vs v_el")

    print("\n" + "=" * 80)
    print("SEARCH COMPLETE")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  CSV:   {csv_path}")
    print(f"  Plots: {out_dir / 'search_improved_skr_vs_T.png'}")
    print(f"         {out_dir / 'search_improved_skr_vs_eps.png'}")
    print(f"         {out_dir / 'search_improved_skr_vs_v_el.png'}")


if __name__ == "__main__":
    main()
