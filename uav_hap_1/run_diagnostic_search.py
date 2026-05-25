"""
Improved diagnostic search: Investigate Z_raw > Zmax root cause.

Key changes:
1. Enhanced MB VA tuning (finer grid)
2. Comprehensive diagnostics: term_signal, term_noise, rho, margin
3. Clearer physical vs clipped distinction
4. Analysis of Z_raw distribution (histogram)
5. Top-N reports: by rho ratio, by SKR_raw
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
    """Classify point as physical, clipped, or invalid."""
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


def _write_csv(csv_path: Path, rows: list[dict]) -> None:
    """Write results to CSV."""
    if not rows:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _tune_nu_tilde_improved(
    target_va: float, alpha0: float, ncut: int, grid: np.ndarray
) -> tuple[float, float]:
    """
    Find nu_tilde that matches target VA.
    Two-stage search: coarse grid, then local refinement.
    """
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

    if len(grid) > 1:
        step = float(grid[1] - grid[0])
        lo = max(1e-6, best_nu - 2.0 * step)
        hi = best_nu + 2.0 * step
        fine_grid = np.linspace(lo, hi, 200)
        for nu in fine_grid:
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

    print("=" * 90)
    print("DIAGNOSTIC SEARCH: Root cause of Z_raw > Zmax")
    print("=" * 90)

    # ========================================================================
    # STAGE 1: Build states and converge
    # ========================================================================
    print("\nStage 1: Building baseline states...")
    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    uni_state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
    mb_state_fixed = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)

    print(f"\nState diagnostics:")
    print(f"  Binomial (Ncut={QAM_NCUT_BINOMIAL}): VA={bin_state.va:.10f}, TrC={bin_state.tr_c:.10f}, w={bin_state.w:.10f}")
    print(f"  Uniform  (Ncut={QAM_NCUT_UNIFORM}): VA={uni_state.va:.10f}, TrC={uni_state.tr_c:.10f}, w={uni_state.w:.10f}")
    print(f"  MB fixed (Ncut={QAM_NCUT_MB}, nu={QAM_NU_TILDE:.6f}): VA={mb_state_fixed.va:.10f}, TrC={mb_state_fixed.tr_c:.10f}, w={mb_state_fixed.w:.10f}")

    # Improved MB tuning
    print(f"\nImproved MB VA tuning:")
    nu_grid_fine = np.linspace(0.001, 2.0, 200)  # Finer grid
    nu_tuned_bin, va_tuned_bin = _tune_nu_tilde_improved(
        bin_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid_fine
    )
    mb_state_tuned = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_tuned_bin)
    va_error = abs(va_tuned_bin - bin_state.va)
    va_rel_error = va_error / bin_state.va if bin_state.va != 0 else float("nan")
    print(
        f"  Target VA (binomial) = {bin_state.va:.10f}"
        f" -> nu_tilde = {nu_tuned_bin:.10f}, VA_MB = {va_tuned_bin:.10f}"
        f" (abs error = {va_error:.2e}, rel error = {va_rel_error:.2e})"
    )

    # ========================================================================
    # STAGE 2: Diagnostic sweep at key channel values
    # ========================================================================
    print(f"\n" + "=" * 90)
    print("Stage 2: Diagnostic sweep at representative channel conditions")
    print("=" * 90)

    # Focus on range where problems appear
    T_grid = np.array([0.05, 0.3, 0.5, 0.7, 0.9, 0.95])
    eps_grid = np.array([0.0, 0.001, 0.005, 0.01])
    eta_vals = [0.6, 0.95, 0.99]
    v_el_vals = [0.0, 0.005, 0.01]

    rows: list[dict] = []
    rho_values = []  # Collect Z_raw/Z_max ratios for histogram
    physical_points = []
    clipped_points = []

    def evaluate(label, state, ncut, T, eps, eta, v_el, mode, nu_tilde):
        metrics = compute_metrics(state, T, eps, QAM_BETA, eta, v_el)
        status = _status(metrics)

        if label != "mb":
            key = label
        else:
            key = "mb_fixed" if mode == "fixed-parameter" else "mb_matched_VA"

        row = {
            "distribution": label,
            "mode": mode,
            "ncut": ncut,
            "T": float(T),
            "eps": float(eps),
            "eta": float(eta),
            "v_el": float(v_el),
            "nu_tilde": nu_tilde if nu_tilde is not None else "",
            "VA": state.va,
            "TrC": state.tr_c,
            "w": state.w,
            "term_signal": metrics.term_signal,
            "term_noise": metrics.term_noise,
            "signal_to_zmax": metrics.term_signal / metrics.z_star_max if metrics.z_star_max > 0 else float("nan"),
            "noise_fraction": metrics.term_noise / metrics.term_signal if metrics.term_signal > 0 else float("nan"),
            "z_star_raw": metrics.z_star_raw,
            "z_star_max": metrics.z_star_max,
            "z_star_used": metrics.z_star,
            "rho": metrics.z_raw_over_zmax,
            "margin": metrics.z_raw_margin,
            "z_star_clipped": metrics.z_star_clipped,
            "chi_be": metrics.chi_be,
            "i_ab": metrics.i_ab,
            "skr_raw": metrics.skr_raw,
            "skr": metrics.skr,
            "status": status,
        }
        rows.append(row)
        rho_values.append(metrics.z_raw_over_zmax)

        if status == "physical":
            physical_points.append(row)
        elif status == "clipped":
            clipped_points.append(row)

    # Evaluate all combinations
    for T in T_grid:
        for eps in eps_grid:
            for eta in eta_vals:
                for v_el in v_el_vals:
                    evaluate("binomial", bin_state, QAM_NCUT_BINOMIAL, T, eps, eta, v_el, "fixed-parameter", None)
                    evaluate("uniform", uni_state, QAM_NCUT_UNIFORM, T, eps, eta, v_el, "fixed-parameter", None)
                    evaluate("mb", mb_state_fixed, QAM_NCUT_MB, T, eps, eta, v_el, "fixed-parameter", QAM_NU_TILDE)
                    evaluate(
                        "mb",
                        mb_state_tuned,
                        QAM_NCUT_MB,
                        T,
                        eps,
                        eta,
                        v_el,
                        "matched-VA",
                        nu_tuned_bin,
                    )

    csv_path = out_dir / "qam_diagnostic_search.csv"
    _write_csv(csv_path, rows)
    print(f"\n  CSV saved: {csv_path} ({len(rows)} rows)")

    # ========================================================================
    # STAGE 3: Analysis
    # ========================================================================
    print(f"\n" + "=" * 90)
    print("DIAGNOSTIC ANALYSIS")
    print("=" * 90)

    # Count by status
    phys_count = sum(1 for r in rows if r["status"] == "physical")
    clip_count = sum(1 for r in rows if r["status"] == "clipped")
    unph_count = sum(1 for r in rows if r["status"] == "invalid")
    total_count = len(rows)

    print(f"\nStatus distribution across all {total_count} evaluations:")
    print(f"  Physical:     {phys_count:4d} ({100*phys_count/total_count:5.1f}%)")
    print(f"  Clipped:      {clip_count:4d} ({100*clip_count/total_count:5.1f}%)")
    print(f"  Invalid:      {unph_count:4d} ({100*unph_count/total_count:5.1f}%)")

    # Physical points with SKR_raw > 0
    phys_pos = [r for r in physical_points if r["skr_raw"] > 0]
    print(f"\nPhysical points with SKR_raw > 0: {len(phys_pos)}")
    if phys_pos:
        best_phys = max(phys_pos, key=lambda x: x["skr_raw"])
        print(f"  Best: SKR_raw={best_phys['skr_raw']:.6f} at T={best_phys['T']:.4f}, "
              f"eps={best_phys['eps']:.6f}, eta={best_phys['eta']:.4f}, v_el={best_phys['v_el']:.6f}")
    else:
        print("  *** NONE FOUND ***")

    # Clipped points with SKR_raw > 0 (for reference)
    clip_pos = [r for r in clipped_points if r["skr_raw"] > 0]
    print(f"\nClipped points with SKR_raw > 0 (reference only): {len(clip_pos)}")
    if clip_pos:
        best_clip = max(clip_pos, key=lambda x: x["skr_raw"])
        print(f"  Best: SKR_raw={best_clip['skr_raw']:.6f} at T={best_clip['T']:.4f}, "
              f"eps={best_clip['eps']:.6f}, eta={best_clip['eta']:.4f}, v_el={best_clip['v_el']:.6f}")
        print(f"  NOTE: These are NOT physically admissible (Z_raw > Z_max)")

    # Rho analysis (Z_raw/Z_max distribution)
    print(f"\nZ_raw/Z_max ratio (rho) statistics:")
    rho_array = np.array(rho_values)
    print(f"  Min:    {np.min(rho_array):.6f}")
    print(f"  Median: {np.median(rho_array):.6f}")
    print(f"  Mean:   {np.mean(rho_array):.6f}")
    print(f"  Max:    {np.max(rho_array):.6f}")
    print(f"  % > 1.0 (clipped): {100*np.sum(rho_array > 1.0)/len(rho_array):.1f}%")

    # Best physical/clipped points by SKR_raw (even if negative)
    best_phys_any = max(physical_points, key=lambda x: x["skr_raw"]) if physical_points else None
    best_clip_any = max(clipped_points, key=lambda x: x["skr_raw"]) if clipped_points else None
    print("\nBest physical point (by SKR_raw):")
    if best_phys_any:
        print(
            f"  SKR_raw={best_phys_any['skr_raw']:.6f} at T={best_phys_any['T']:.4f}, "
            f"eps={best_phys_any['eps']:.6f}, eta={best_phys_any['eta']:.4f}, v_el={best_phys_any['v_el']:.6f}"
        )
    else:
        print("  None (no physical points).")

    print("\nBest clipped point (by SKR_raw):")
    if best_clip_any:
        print(
            f"  SKR_raw={best_clip_any['skr_raw']:.6f} at T={best_clip_any['T']:.4f}, "
            f"eps={best_clip_any['eps']:.6f}, eta={best_clip_any['eta']:.4f}, v_el={best_clip_any['v_el']:.6f}"
        )
    else:
        print("  None (no clipped points).")

    # Top points by largest rho (most clipped)
    print(f"\nTop 10 points with largest rho (most severely clipped):")
    sorted_by_rho = sorted(rows, key=lambda x: x["rho"], reverse=True)
    for i, r in enumerate(sorted_by_rho[:10], 1):
        print(
            f"  {i}. {r['distribution']:10s} {r['mode']:12s}: "
            f"rho={r['rho']:.6f}, T={r['T']:.4f}, eps={r['eps']:.6f}, "
            f"SKR_raw={r['skr_raw']:.6f}, status={r['status']}"
        )

    # Term analysis: which term dominates?
    print(f"\nTerm magnitude analysis (signal vs noise in Z_raw):")
    avg_signal = np.mean([r["term_signal"] for r in rows])
    avg_noise = np.mean([r["term_noise"] for r in rows])
    avg_z = np.mean([r["z_star_raw"] for r in rows])
    avg_signal_to_zmax = np.mean([r["signal_to_zmax"] for r in rows])
    avg_noise_fraction = np.mean([r["noise_fraction"] for r in rows])
    print(f"  Avg term_signal (2*sqrt(T)*TrC): {avg_signal:.6f}")
    print(f"  Avg term_noise  (sqrt(2*T*eps*w)): {avg_noise:.6f}")
    print(f"  Avg Z_raw: {avg_z:.6f}")
    print(f"  Avg signal_to_zmax: {avg_signal_to_zmax:.6f}")
    print(f"  Avg noise_fraction: {avg_noise_fraction:.6f}")

    # Plot rho histogram
    try:
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

        # Histogram of rho
        ax1.hist(rho_array, bins=40, edgecolor="black", alpha=0.7)
        ax1.axvline(1.0, color="red", linestyle="--", linewidth=2, label="Clipping threshold (rho=1.0)")
        ax1.set_xlabel("Z_raw / Z_max")
        ax1.set_ylabel("Count")
        ax1.set_title("Distribution of Z_raw/Z_max (rho)")
        ax1.legend()
        ax1.grid(alpha=0.3)

        # Box plot by distribution
        dist_labels = ["binomial", "uniform", "mb"]
        rho_by_dist = {label: [] for label in dist_labels}
        for r in rows:
            if r["distribution"] in rho_by_dist:
                rho_by_dist[r["distribution"]].append(r["rho"])

        box_data = [rho_by_dist[label] for label in dist_labels]
        bp = ax2.boxplot(box_data, tick_labels=dist_labels, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor("lightblue")
        ax2.axhline(1.0, color="red", linestyle="--", linewidth=2, label="Clipping threshold")
        ax2.set_ylabel("Z_raw / Z_max")
        ax2.set_title("Z_raw/Z_max by distribution")
        ax2.legend()
        ax2.grid(alpha=0.3, axis="y")

        plot_path = out_dir / "diagnostic_zraw_distribution.png"
        fig.savefig(plot_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"\nPlot saved: {plot_path}")
    except ModuleNotFoundError:
        print("\nmatplotlib not available: skipping plot")

    # ========================================================================
    # STAGE 4: Root cause hypothesis
    # ========================================================================
    print(f"\n" + "=" * 90)
    print("ROOT CAUSE ANALYSIS (PHYSICAL INTERPRETATION)")
    print("=" * 90)

    avg_ratio = np.mean(rho_array)
    median_ratio = np.median(rho_array)
    clip_fraction = clip_count / total_count if total_count else 0.0

    print(
        f"\nSummary: clipped fraction = {100*clip_fraction:.1f}% | "
        f"mean rho = {avg_ratio:.3f} | median rho = {median_ratio:.3f} | max rho = {np.max(rho_array):.3f}"
    )
    print(
        "In the current covariance model, Z_raw > Zmax means the correlation term exceeds the admissible bound."
    )
    print("Therefore, clipped points are NOT physically admissible as-is and must not be used for physical conclusions.")

    if clip_fraction > 0.5 or avg_ratio > 1.1:
        print("\n✅ Interpretation: Z_raw systematically and frequently exceeds Zmax (not a boundary numerical issue).")
        print("   Most likely causes (in priority order):")
        print("   1. Convention/scale mismatch between TrC and the covariance correlation term")
        print("   2. Mapping from Z_raw to the covariance block correlation is inconsistent")
        print("   3. Numerical issues are a secondary possibility only if rho is near 1 (not the case here)")
    else:
        print("\n⚠️  Interpretation: Z_raw exceeds Zmax in a minority of cases; still non-physical when clipped.")
        print("   Investigate convention/mapping mismatch before attributing to numerical issues.")

    print("\nSignal vs Zmax diagnostics (by distribution):")
    for dist in ["binomial", "uniform", "mb"]:
        dist_rows = [r for r in rows if r["distribution"] == dist]
        if not dist_rows:
            continue
        avg_sig_to_zmax = np.mean([r["signal_to_zmax"] for r in dist_rows])
        avg_noise_frac = np.mean([r["noise_fraction"] for r in dist_rows])
        print(
            f"  {dist:8s}: avg(signal/Zmax)={avg_sig_to_zmax:.3f}, "
            f"avg(noise_fraction)={avg_noise_frac:.3f}"
        )

    # Further diagnostics at ideal channel
    print(f"\n" + "=" * 90)
    print("Detailed point at ideal channel (T=0.95, eps=0, eta=0.99, v_el=0):")
    metrics_ideal = compute_metrics(bin_state, 0.95, 0.0, QAM_BETA, 0.99, 0.0)
    print(f"  term_signal = {metrics_ideal.term_signal:.10f}")
    print(f"  term_noise  = {metrics_ideal.term_noise:.10f}")
    print(f"  Z_raw = {metrics_ideal.z_star_raw:.10f}")
    print(f"  Z_max = {metrics_ideal.z_star_max:.10f}")
    print(f"  rho = {metrics_ideal.z_raw_over_zmax:.10f}")
    print(f"  signal_to_zmax = {metrics_ideal.term_signal / metrics_ideal.z_star_max:.10f}")
    print(
        f"  noise_fraction = "
        f"{metrics_ideal.term_noise / metrics_ideal.term_signal if metrics_ideal.term_signal > 0 else float('nan'):.10f}"
    )
    print(f"  Status: {'PHYSICAL' if metrics_ideal.z_star_raw <= metrics_ideal.z_star_max else 'CLIPPED'}")

    print(f"\n" + "=" * 90)
    print("PHYSICAL INTERPRETATION SUMMARY")
    print("=" * 90)
    if not phys_pos:
        print("No physically admissible positive-SKR point found under the current model/convention.")
        print("All positive SKR_raw values observed so far are from clipped states (non-physical as-is).")
    print("Clipped states must NOT be used as physical evidence for protocol performance.")
    print("The dominant issue is Z_raw frequently exceeding Zmax, suggesting a convention/scale mismatch.")

    print(f"\n" + "=" * 90)
    print("DIAGNOSTIC SEARCH COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()
