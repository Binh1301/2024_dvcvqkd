"""
Investigative comparison: Why Binomial negative, MB/Uniform positive?

Compares binomial, uniform, and MB at identical channel parameters.
Two modes:
  1. fixed-parameter: Use each distribution's default Ncut and nu_tilde
  2. matched-VA: Tune MB/Uniform to match binomial VA

Outputs:
  - Detailed comparison table
  - CSV with all diagnostics
  - Root cause analysis
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1_sample.config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
    )
    from uav_hap_1_sample.protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from uav_hap_1_sample.zstar import mb as zmb
else:
    from .config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
    )
    from .protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
    from .zstar import mb as zmb


def _tune_nu_tilde_matched(
    target_va: float, alpha0: float, ncut: int, grid: np.ndarray
) -> tuple[float, float]:
    """Find nu_tilde that matches target VA."""
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


def _status(metrics) -> str:
    """Classify as physical, clipped, or invalid."""
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


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 100)
    print("INVESTIGATIVE COMPARISON: Why Binomial Negative, MB/Uniform Positive?")
    print("=" * 100)

    # ========================================================================
    # PHASE 1: Build states
    # ========================================================================
    print("\nPHASE 1: Building QAM states\n")

    # Binomial
    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    print(f"Binomial  (α0={QAM_ALPHA0_BINOMIAL:.6f}, Ncut={QAM_NCUT_BINOMIAL}):")
    print(f"  VA={bin_state.va:.10f}, TrC={bin_state.tr_c:.10f}, w={bin_state.w:.10f}")

    # Uniform
    uni_state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
    print(f"Uniform   (α0={QAM_ALPHA0_UNIFORM:.6f}, Ncut={QAM_NCUT_UNIFORM}):")
    print(f"  VA={uni_state.va:.10f}, TrC={uni_state.tr_c:.10f}, w={uni_state.w:.10f}")

    # MB fixed
    mb_state_fixed = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)
    print(
        f"MB fixed  (α0={QAM_ALPHA0_MB:.6f}, Ncut={QAM_NCUT_MB}, ν_tilde={QAM_NU_TILDE:.6f}):"
    )
    print(f"  VA={mb_state_fixed.va:.10f}, TrC={mb_state_fixed.tr_c:.10f}, w={mb_state_fixed.w:.10f}")

    # MB matched to binomial VA
    nu_grid = np.linspace(0.001, 2.0, 200)
    nu_matched, va_matched = _tune_nu_tilde_matched(
        bin_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid
    )
    mb_state_matched = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_matched)
    print(
        f"MB matched (α0={QAM_ALPHA0_MB:.6f}, Ncut={QAM_NCUT_MB}, ν_tilde={nu_matched:.6f} [tuned]):"
    )
    va_error = abs(mb_state_matched.va - bin_state.va)
    va_rel = va_error / bin_state.va if bin_state.va != 0 else float("nan")
    print(f"  VA={mb_state_matched.va:.10f}, TrC={mb_state_matched.tr_c:.10f}, w={mb_state_matched.w:.10f}")
    print(
        f"  VA_target={bin_state.va:.10f}, VA_MB={mb_state_matched.va:.10f}, "
        f"abs error={va_error:.2e}, rel error={va_rel:.2e}"
    )

    # ========================================================================
    # PHASE 2: Evaluate at multiple representative channel conditions
    # ========================================================================
    # Test at a few representative points
    test_cases = [
        {"T": 0.5, "eps": 0.01, "eta": 0.95, "v_el": 0.01, "name": "Baseline (T=0.5)"},
        {"T": 0.95, "eps": 0.0, "eta": 0.99, "v_el": 0.0, "name": "Near-ideal (T=0.95)"},
        {"T": 0.3, "eps": 0.01, "eta": 0.6, "v_el": 0.01, "name": "Conservative (T=0.3)"},
    ]

    all_results = []

    for test_case in test_cases:
        T = test_case["T"]
        eps = test_case["eps"]
        eta = test_case["eta"]
        v_el = test_case["v_el"]
        case_name = test_case["name"]

        print("\n" + "=" * 100)
        print(f"TEST CASE: {case_name}")
        print(f"  T={T}, eps={eps}, eta={eta}, v_el={v_el}")
        print("=" * 100)

        # ====================================================================
        # MODE 1: Fixed parameters
        # ====================================================================
        print(f"\nMODE 1: Fixed-parameter (Each distribution uses default Ncut, ν_tilde)")
        print("-" * 100)

        metrics_bin_fixed = compute_metrics(bin_state, T, eps, QAM_BETA, eta, v_el)
        metrics_uni_fixed = compute_metrics(uni_state, T, eps, QAM_BETA, eta, v_el)
        metrics_mb_fixed = compute_metrics(mb_state_fixed, T, eps, QAM_BETA, eta, v_el)

        # Build comparison table for fixed mode
        fixed_rows = [
            {
                "test_case": case_name,
                "mode": "fixed-parameter",
                "distribution": "Binomial",
                "alpha0": QAM_ALPHA0_BINOMIAL,
                "ncut": QAM_NCUT_BINOMIAL,
                "nu_tilde": "",
                "VA": bin_state.va,
                "TrC": bin_state.tr_c,
                "w": bin_state.w,
                "term_signal": metrics_bin_fixed.term_signal,
                "term_noise": metrics_bin_fixed.term_noise,
                "signal_to_zmax": metrics_bin_fixed.term_signal / metrics_bin_fixed.z_star_max if metrics_bin_fixed.z_star_max > 0 else float("nan"),
                "noise_fraction": metrics_bin_fixed.term_noise / metrics_bin_fixed.term_signal if metrics_bin_fixed.term_signal > 0 else float("nan"),
                "Z_raw": metrics_bin_fixed.z_star_raw,
                "Z_used": metrics_bin_fixed.z_star,
                "Zmax": metrics_bin_fixed.z_star_max,
                "Z_raw/Zmax": metrics_bin_fixed.z_raw_over_zmax,
                "margin": metrics_bin_fixed.z_raw_margin,
                "status": _status(metrics_bin_fixed),
                "chi_BE": metrics_bin_fixed.chi_be,
                "I_AB": metrics_bin_fixed.i_ab,
                "SKR_raw": metrics_bin_fixed.skr_raw,
                "SKR": metrics_bin_fixed.skr,
            },
            {
                "test_case": case_name,
                "mode": "fixed-parameter",
                "distribution": "Uniform",
                "alpha0": QAM_ALPHA0_UNIFORM,
                "ncut": QAM_NCUT_UNIFORM,
                "nu_tilde": "",
                "VA": uni_state.va,
                "TrC": uni_state.tr_c,
                "w": uni_state.w,
                "term_signal": metrics_uni_fixed.term_signal,
                "term_noise": metrics_uni_fixed.term_noise,
                "signal_to_zmax": metrics_uni_fixed.term_signal / metrics_uni_fixed.z_star_max if metrics_uni_fixed.z_star_max > 0 else float("nan"),
                "noise_fraction": metrics_uni_fixed.term_noise / metrics_uni_fixed.term_signal if metrics_uni_fixed.term_signal > 0 else float("nan"),
                "Z_raw": metrics_uni_fixed.z_star_raw,
                "Z_used": metrics_uni_fixed.z_star,
                "Zmax": metrics_uni_fixed.z_star_max,
                "Z_raw/Zmax": metrics_uni_fixed.z_raw_over_zmax,
                "margin": metrics_uni_fixed.z_raw_margin,
                "status": _status(metrics_uni_fixed),
                "chi_BE": metrics_uni_fixed.chi_be,
                "I_AB": metrics_uni_fixed.i_ab,
                "SKR_raw": metrics_uni_fixed.skr_raw,
                "SKR": metrics_uni_fixed.skr,
            },
            {
                "test_case": case_name,
                "mode": "fixed-parameter",
                "distribution": "MB (fixed ν)",
                "alpha0": QAM_ALPHA0_MB,
                "ncut": QAM_NCUT_MB,
                "nu_tilde": QAM_NU_TILDE,
                "VA": mb_state_fixed.va,
                "TrC": mb_state_fixed.tr_c,
                "w": mb_state_fixed.w,
                "term_signal": metrics_mb_fixed.term_signal,
                "term_noise": metrics_mb_fixed.term_noise,
                "signal_to_zmax": metrics_mb_fixed.term_signal / metrics_mb_fixed.z_star_max if metrics_mb_fixed.z_star_max > 0 else float("nan"),
                "noise_fraction": metrics_mb_fixed.term_noise / metrics_mb_fixed.term_signal if metrics_mb_fixed.term_signal > 0 else float("nan"),
                "Z_raw": metrics_mb_fixed.z_star_raw,
                "Z_used": metrics_mb_fixed.z_star,
                "Zmax": metrics_mb_fixed.z_star_max,
                "Z_raw/Zmax": metrics_mb_fixed.z_raw_over_zmax,
                "margin": metrics_mb_fixed.z_raw_margin,
                "status": _status(metrics_mb_fixed),
                "chi_BE": metrics_mb_fixed.chi_be,
                "I_AB": metrics_mb_fixed.i_ab,
                "SKR_raw": metrics_mb_fixed.skr_raw,
                "SKR": metrics_mb_fixed.skr,
            },
        ]

        # Print fixed mode table
        print(
            f"\n{'Dist':<12} {'Mode':<7} {'alpha0':<7} {'Ncut':<5} {'nu':<8} {'VA':<8} "
            f"{'TrC':<8} {'w':<8} {'term_sig':<9} {'term_noise':<10} {'sig/Zmax':<9} "
            f"{'noise_frac':<10} {'Z_raw':<9} {'Z_used':<9} {'Zmax':<9} {'rho':<7} "
            f"{'Status':<9} {'chi_BE':<9} {'I_AB':<9} {'SKR_raw':<9} {'SKR':<8}"
        )
        print("-" * 190)
        for row in fixed_rows:
            print(
                f"{row['distribution']:<12} "
                f"{row['mode']:<7} "
                f"{row['alpha0']:<7.3f} "
                f"{row['ncut']:<5d} "
                f"{str(row['nu_tilde']):<8} "
                f"{row['VA']:<8.4f} "
                f"{row['TrC']:<8.4f} "
                f"{row['w']:<8.4f} "
                f"{row['term_signal']:<9.4f} "
                f"{row['term_noise']:<10.4f} "
                f"{row['signal_to_zmax']:<9.4f} "
                f"{row['noise_fraction']:<10.4f} "
                f"{row['Z_raw']:<9.4f} "
                f"{row['Z_used']:<9.4f} "
                f"{row['Zmax']:<9.4f} "
                f"{row['Z_raw/Zmax']:<7.3f} "
                f"{row['status']:<9} "
                f"{row['chi_BE']:<9.4f} "
                f"{row['I_AB']:<9.4f} "
                f"{row['SKR_raw']:<9.5f} "
                f"{row['SKR']:<8.5f}"
            )

        print("\nPhysical interpretation (fixed mode):")
        for row in fixed_rows:
            status = row["status"]
            if status == "physical":
                note = "physical; SKR_raw can be used for physical conclusions"
            elif status == "clipped":
                note = "clipped; SKR_raw is post-clipping and NOT physically admissible"
            else:
                note = "invalid; numeric/constraint issue, do not interpret physically"
            print(f"  {row['distribution']}: {note}")

        # ====================================================================
        # MODE 2: Matched VA
        # ====================================================================
        print(f"\nMODE 2: Matched-VA (Tune MB ν_tilde to match binomial VA)")
        print("-" * 100)

        metrics_bin_matched = compute_metrics(bin_state, T, eps, QAM_BETA, eta, v_el)
        metrics_uni_matched = compute_metrics(uni_state, T, eps, QAM_BETA, eta, v_el)
        metrics_mb_matched = compute_metrics(mb_state_matched, T, eps, QAM_BETA, eta, v_el)

        matched_rows = [
            {
                "test_case": case_name,
                "mode": "matched-VA",
                "distribution": "Binomial",
                "alpha0": QAM_ALPHA0_BINOMIAL,
                "ncut": QAM_NCUT_BINOMIAL,
                "nu_tilde": "",
                "VA": bin_state.va,
                "TrC": bin_state.tr_c,
                "w": bin_state.w,
                "term_signal": metrics_bin_matched.term_signal,
                "term_noise": metrics_bin_matched.term_noise,
                "signal_to_zmax": metrics_bin_matched.term_signal / metrics_bin_matched.z_star_max if metrics_bin_matched.z_star_max > 0 else float("nan"),
                "noise_fraction": metrics_bin_matched.term_noise / metrics_bin_matched.term_signal if metrics_bin_matched.term_signal > 0 else float("nan"),
                "Z_raw": metrics_bin_matched.z_star_raw,
                "Z_used": metrics_bin_matched.z_star,
                "Zmax": metrics_bin_matched.z_star_max,
                "Z_raw/Zmax": metrics_bin_matched.z_raw_over_zmax,
                "margin": metrics_bin_matched.z_raw_margin,
                "status": _status(metrics_bin_matched),
                "chi_BE": metrics_bin_matched.chi_be,
                "I_AB": metrics_bin_matched.i_ab,
                "SKR_raw": metrics_bin_matched.skr_raw,
                "SKR": metrics_bin_matched.skr,
            },
            {
                "test_case": case_name,
                "mode": "matched-VA",
                "distribution": "Uniform",
                "alpha0": QAM_ALPHA0_UNIFORM,
                "ncut": QAM_NCUT_UNIFORM,
                "nu_tilde": "",
                "VA": uni_state.va,
                "TrC": uni_state.tr_c,
                "w": uni_state.w,
                "term_signal": metrics_uni_matched.term_signal,
                "term_noise": metrics_uni_matched.term_noise,
                "signal_to_zmax": metrics_uni_matched.term_signal / metrics_uni_matched.z_star_max if metrics_uni_matched.z_star_max > 0 else float("nan"),
                "noise_fraction": metrics_uni_matched.term_noise / metrics_uni_matched.term_signal if metrics_uni_matched.term_signal > 0 else float("nan"),
                "Z_raw": metrics_uni_matched.z_star_raw,
                "Z_used": metrics_uni_matched.z_star,
                "Zmax": metrics_uni_matched.z_star_max,
                "Z_raw/Zmax": metrics_uni_matched.z_raw_over_zmax,
                "margin": metrics_uni_matched.z_raw_margin,
                "status": _status(metrics_uni_matched),
                "chi_BE": metrics_uni_matched.chi_be,
                "I_AB": metrics_uni_matched.i_ab,
                "SKR_raw": metrics_uni_matched.skr_raw,
                "SKR": metrics_uni_matched.skr,
            },
            {
                "test_case": case_name,
                "mode": "matched-VA",
                "distribution": "MB (matched VA)",
                "alpha0": QAM_ALPHA0_MB,
                "ncut": QAM_NCUT_MB,
                "nu_tilde": nu_matched,
                "VA": mb_state_matched.va,
                "TrC": mb_state_matched.tr_c,
                "w": mb_state_matched.w,
                "term_signal": metrics_mb_matched.term_signal,
                "term_noise": metrics_mb_matched.term_noise,
                "signal_to_zmax": metrics_mb_matched.term_signal / metrics_mb_matched.z_star_max if metrics_mb_matched.z_star_max > 0 else float("nan"),
                "noise_fraction": metrics_mb_matched.term_noise / metrics_mb_matched.term_signal if metrics_mb_matched.term_signal > 0 else float("nan"),
                "Z_raw": metrics_mb_matched.z_star_raw,
                "Z_used": metrics_mb_matched.z_star,
                "Zmax": metrics_mb_matched.z_star_max,
                "Z_raw/Zmax": metrics_mb_matched.z_raw_over_zmax,
                "margin": metrics_mb_matched.z_raw_margin,
                "status": _status(metrics_mb_matched),
                "chi_BE": metrics_mb_matched.chi_be,
                "I_AB": metrics_mb_matched.i_ab,
                "SKR_raw": metrics_mb_matched.skr_raw,
                "SKR": metrics_mb_matched.skr,
            },
        ]

        # Print matched mode table
        print(
            f"\n{'Dist':<20} {'Mode':<7} {'alpha0':<7} {'Ncut':<5} {'nu':<8} {'VA':<8} "
            f"{'TrC':<8} {'w':<8} {'term_sig':<9} {'term_noise':<10} {'sig/Zmax':<9} "
            f"{'noise_frac':<10} {'Z_raw':<9} {'Z_used':<9} {'Zmax':<9} {'rho':<7} "
            f"{'Status':<9} {'chi_BE':<9} {'I_AB':<9} {'SKR_raw':<9} {'SKR':<8}"
        )
        print("-" * 200)
        for row in matched_rows:
            print(
                f"{row['distribution']:<20} "
                f"{row['mode']:<7} "
                f"{row['alpha0']:<7.3f} "
                f"{row['ncut']:<5d} "
                f"{str(row['nu_tilde']):<8} "
                f"{row['VA']:<8.4f} "
                f"{row['TrC']:<8.4f} "
                f"{row['w']:<8.4f} "
                f"{row['term_signal']:<9.4f} "
                f"{row['term_noise']:<10.4f} "
                f"{row['signal_to_zmax']:<9.4f} "
                f"{row['noise_fraction']:<10.4f} "
                f"{row['Z_raw']:<9.4f} "
                f"{row['Z_used']:<9.4f} "
                f"{row['Zmax']:<9.4f} "
                f"{row['Z_raw/Zmax']:<7.3f} "
                f"{row['status']:<9} "
                f"{row['chi_BE']:<9.4f} "
                f"{row['I_AB']:<9.4f} "
                f"{row['SKR_raw']:<9.5f} "
                f"{row['SKR']:<8.5f}"
            )

        print("\nPhysical interpretation (matched-VA mode):")
        for row in matched_rows:
            status = row["status"]
            if status == "physical":
                note = "physical; SKR_raw can be used for physical conclusions"
            elif status == "clipped":
                note = "clipped; SKR_raw is post-clipping and NOT physically admissible"
            else:
                note = "invalid; numeric/constraint issue, do not interpret physically"
            print(f"  {row['distribution']}: {note}")

        # Add to all results
        all_results.extend(fixed_rows)
        all_results.extend(matched_rows)

        # ====================================================================
        # ANALYSIS for this test case
        # ====================================================================
        print(f"\nANALYSIS for {case_name}:")
        print("-" * 100)

        bin_skr = metrics_bin_fixed.skr_raw
        uni_skr = metrics_uni_fixed.skr_raw
        mb_skr = metrics_mb_fixed.skr_raw

        print(f"\nFixed mode SKR_raw:")
        print(f"  Binomial: {bin_skr:>10.6f} {'(POSITIVE ✓)' if bin_skr > 0 else '(NEGATIVE ✗)'}")
        print(f"  Uniform:  {uni_skr:>10.6f} {'(POSITIVE ✓)' if uni_skr > 0 else '(NEGATIVE ✗)'}")
        print(f"  MB:       {mb_skr:>10.6f} {'(POSITIVE ✓)' if mb_skr > 0 else '(NEGATIVE ✗)'}")

        # Identify main difference
        if bin_skr < 0 < uni_skr:
            print(
                f"\n  ⚠️  Binomial is NEGATIVE while Uniform is POSITIVE"
            )
            print(
                f"      Difference: {uni_skr - bin_skr:.6f}"
            )

            # Factor analysis
            chi_be_diff = metrics_uni_fixed.chi_be - metrics_bin_fixed.chi_be
            i_ab_diff = metrics_uni_fixed.i_ab - metrics_bin_fixed.i_ab
            print(
                f"\n  Δ(χ_BE) = {chi_be_diff:>10.6f} (Uniform less χ_BE)"
                f" {'←HELPS' if chi_be_diff < 0 else '← HURTS'}"
            )
            print(
                f"  Δ(I_AB) = {i_ab_diff:>10.6f} (Uniform more I_AB)"
                f" {'←HELPS' if i_ab_diff > 0 else '← HURTS'}"
            )

            z_diff = metrics_uni_fixed.z_star_raw - metrics_bin_fixed.z_star_raw
            print(f"  Δ(Z_raw) = {z_diff:>10.6f} (Uniform has {'larger' if z_diff > 0 else 'smaller'} Z_raw)")

        if bin_skr < 0 < mb_skr:
            print(
                f"\n  ⚠️  Binomial is NEGATIVE while MB is POSITIVE"
            )
            print(
                f"      Difference: {mb_skr - bin_skr:.6f}"
            )

            chi_be_diff = metrics_mb_fixed.chi_be - metrics_bin_fixed.chi_be
            i_ab_diff = metrics_mb_fixed.i_ab - metrics_bin_fixed.i_ab
            print(
                f"\n  Δ(χ_BE) = {chi_be_diff:>10.6f} (MB less χ_BE)"
                f" {'←HELPS' if chi_be_diff < 0 else '← HURTS'}"
            )
            print(
                f"  Δ(I_AB) = {i_ab_diff:>10.6f} (MB more I_AB)"
                f" {'←HELPS' if i_ab_diff > 0 else '← HURTS'}"
            )

            z_diff = metrics_mb_fixed.z_star_raw - metrics_bin_fixed.z_star_raw
            print(f"  Δ(Z_raw) = {z_diff:>10.6f} (MB has {'larger' if z_diff > 0 else 'smaller'} Z_raw)")

            print(f"\n  VA difference: Bin={bin_state.va:.6f} vs MB={mb_state_fixed.va:.6f} (Δ={mb_state_fixed.va - bin_state.va:.6f})")

        if bin_skr < 0 and uni_skr < 0 and mb_skr < 0:
            print("\n  ⚠️  All distributions NEGATIVE")

    # Save CSV
    csv_path = out_dir / "investigate_skr_difference.csv"
    if all_results:
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(all_results[0].keys()))
            writer.writeheader()
            writer.writerows(all_results)
    print(f"\nCSV saved: {csv_path}")

    # ========================================================================
    # FINAL CONCLUSION
    # ========================================================================
    print("\n" + "=" * 100)
    print("FINAL CONCLUSION")
    print("=" * 100)

    print(f"\nBinomial (fixed):       SKR_raw = {metrics_bin_fixed.skr_raw:.6f}")
    print(f"Uniform (fixed):        SKR_raw = {metrics_uni_fixed.skr_raw:.6f}")
    print(f"MB (fixed ν={QAM_NU_TILDE:.6f}):  SKR_raw = {metrics_mb_fixed.skr_raw:.6f}")

    print(
        f"\nBinomial SKR is negative chiefly because:"
    )
    print(
        f"  - chi_BE = {metrics_bin_fixed.chi_be:.6f}"
    )
    print(
        f"  - I_AB = {metrics_bin_fixed.i_ab:.6f}"
    )
    print(
        f"  - SKR_raw = β·I_AB - χ_BE = {QAM_BETA}·{metrics_bin_fixed.i_ab:.6f} - {metrics_bin_fixed.chi_be:.6f} = {metrics_bin_fixed.skr_raw:.6f}"
    )

    if metrics_uni_fixed.skr_raw > 0:
        print(
            f"\nUniform SKR is positive because:"
        )
        print(
            f"  - chi_BE = {metrics_uni_fixed.chi_be:.6f} ({'lower' if metrics_uni_fixed.chi_be < metrics_bin_fixed.chi_be else 'higher'} than binomial by {metrics_uni_fixed.chi_be - metrics_bin_fixed.chi_be:.6f})"
        )
        print(
            f"  - I_AB = {metrics_uni_fixed.i_ab:.6f} ({'higher' if metrics_uni_fixed.i_ab > metrics_bin_fixed.i_ab else 'lower'} than binomial by {metrics_uni_fixed.i_ab - metrics_bin_fixed.i_ab:.6f})"
        )
        print(
            f"  - SKR_raw = β·I_AB - χ_BE = {QAM_BETA}·{metrics_uni_fixed.i_ab:.6f} - {metrics_uni_fixed.chi_be:.6f} = {metrics_uni_fixed.skr_raw:.6f}"
        )
        print(
            f"  - Status: {_status(metrics_uni_fixed)} {'(PHYSICAL ✓)' if _status(metrics_uni_fixed) == 'physical' else '(NOT PHYSICAL ✗)'}"
        )

    if metrics_mb_fixed.skr_raw > 0:
        print(
            f"\nMB SKR is positive because:"
        )
        print(
            f"  - chi_BE = {metrics_mb_fixed.chi_be:.6f} ({'lower' if metrics_mb_fixed.chi_be < metrics_bin_fixed.chi_be else 'higher'} than binomial by {metrics_mb_fixed.chi_be - metrics_bin_fixed.chi_be:.6f})"
        )
        print(
            f"  - I_AB = {metrics_mb_fixed.i_ab:.6f} ({'higher' if metrics_mb_fixed.i_ab > metrics_bin_fixed.i_ab else 'lower'} than binomial by {metrics_mb_fixed.i_ab - metrics_bin_fixed.i_ab:.6f})"
        )
        print(
            f"  - SKR_raw = β·I_AB - χ_BE = {QAM_BETA}·{metrics_mb_fixed.i_ab:.6f} - {metrics_mb_fixed.chi_be:.6f} = {metrics_mb_fixed.skr_raw:.6f}"
        )
        print(
            f"  - Status: {_status(metrics_mb_fixed)} {'(PHYSICAL ✓)' if _status(metrics_mb_fixed) == 'physical' else '(NOT PHYSICAL ✗)'}"
        )

    print(f"\n" + "=" * 100)
    print("INVESTIGATION COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
