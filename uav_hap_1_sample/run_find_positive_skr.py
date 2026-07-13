"""
Search parameter regions for SKR_raw > 0 in QAM-256 (binomial/uniform/MB).

Workflow:
1) Recompute baseline at T_eff=0.082151 (expected SKR_raw < 0).
2) Coarse sweep over T_eff, eps, eta, v_el (fixed alpha0, ncut).
3) Optional extension: alpha0 and ncut grids; MB nu_tilde tuning.
4) Determine minimal T_eff where SKR_raw > 0 (physical only).

Notes:
- Does NOT change any core formulas; only uses compute_metrics.
- Physical points are strictly Z_raw <= Zmax and finite diagnostics.
"""

from __future__ import annotations

import csv
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1_sample.config import (
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


@dataclass(frozen=True)
class EvalResult:
    distribution: str
    mode: str
    T_eff: float
    eps: float
    eta: float
    v_el: float
    alpha0: float
    ncut: int
    nu_tilde: float | None
    va: float
    tr_c: float
    w: float
    term_signal: float
    term_noise: float
    signal_to_zmax: float
    noise_fraction: float
    z_raw: float
    z_used: float
    z_max: float
    rho: float
    margin: float
    status: str
    chi_be: float
    i_ab: float
    skr_raw: float
    skr: float
    lambda1: float
    lambda2: float
    lambda3: float


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


def _tune_nu_tilde(target_va: float, alpha0: float, ncut: int) -> tuple[float, float]:
    grid = np.linspace(0.001, 2.0, 200)
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

    step = float(grid[1] - grid[0])
    fine_grid = np.linspace(max(1e-6, best_nu - 2 * step), best_nu + 2 * step, 200)
    for nu in fine_grid:
        state = zmb.compute_state(alpha0=alpha0, ncut=ncut, nu_tilde=float(nu))
        err = abs(state["va"] - target_va)
        if err < best_err:
            best_err = err
            best_nu = float(nu)
            best_va = float(state["va"])
    return best_nu, best_va


def _evaluate(
    distribution: str,
    mode: str,
    state,
    T_eff: float,
    eps: float,
    eta: float,
    v_el: float,
) -> EvalResult:
    metrics = compute_metrics(state, T_eff, eps, QAM_BETA, eta, v_el)
    status = _status(metrics)
    signal_to_zmax = metrics.term_signal / metrics.z_star_max if metrics.z_star_max > 0 else float("nan")
    noise_fraction = metrics.term_noise / metrics.term_signal if metrics.term_signal > 0 else float("nan")
    return EvalResult(
        distribution=distribution,
        mode=mode,
        T_eff=float(T_eff),
        eps=float(eps),
        eta=float(eta),
        v_el=float(v_el),
        alpha0=float(state.alpha0),
        ncut=int(state.ncut),
        nu_tilde=getattr(state, "nu_tilde", None),
        va=float(state.va),
        tr_c=float(state.tr_c),
        w=float(state.w),
        term_signal=float(metrics.term_signal),
        term_noise=float(metrics.term_noise),
        signal_to_zmax=float(signal_to_zmax),
        noise_fraction=float(noise_fraction),
        z_raw=float(metrics.z_star_raw),
        z_used=float(metrics.z_star),
        z_max=float(metrics.z_star_max),
        rho=float(metrics.z_raw_over_zmax),
        margin=float(metrics.z_raw_margin),
        status=status,
        chi_be=float(metrics.chi_be),
        i_ab=float(metrics.i_ab),
        skr_raw=float(metrics.skr_raw),
        skr=float(metrics.skr),
        lambda1=float(metrics.lambda1),
        lambda2=float(metrics.lambda2),
        lambda3=float(metrics.lambda3),
    )


def _write_csv(path: Path, rows: list[EvalResult]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].__dict__.keys()))
        writer.writeheader()
        writer.writerows([r.__dict__ for r in rows])


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Baseline (given in prompt)
    T_eff_baseline = 0.082151

    print("=" * 80)
    print("Baseline check (binomial @ T_eff=0.082151)")
    print("=" * 80)
    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    base_metrics = compute_metrics(bin_state, T_eff_baseline, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    print(f"T_eff   = {T_eff_baseline:.6f}")
    print(f"alpha0  = {bin_state.alpha0:.6f}, Ncut = {bin_state.ncut}")
    print(f"VA      = {bin_state.va:.10f}")
    print(f"Tr(C)   = {bin_state.tr_c:.10f}")
    print(f"w       = {bin_state.w:.10f}")
    print(f"Z_raw   = {base_metrics.z_star_raw:.10f}")
    print(f"chi_BE  = {base_metrics.chi_be:.10f}")
    print(f"I_AB    = {base_metrics.i_ab:.10f}")
    print(f"SKR_raw = {base_metrics.skr_raw:.10f}")

    # Parameter grids (coarse)
    T_grid = np.linspace(0.05, 0.95, 19)
    eps_grid = np.array([0.0, 0.002, 0.005, 0.01, 0.02])
    eta_grid = np.array([0.6, 0.8, 0.9, 0.95, 0.99])
    v_el_grid = np.array([0.0, 0.002, 0.005, 0.01])

    alpha_scales = np.array([0.8, 1.0, 1.2])
    ncut_grid_bin = [QAM_NCUT_BINOMIAL, QAM_NCUT_BINOMIAL + 15]
    ncut_grid_uni = [QAM_NCUT_UNIFORM]
    ncut_grid_mb = [QAM_NCUT_MB]

    results: list[EvalResult] = []

    def search_distribution(distribution: str, mode: str):
        best_phys = None
        best_clip = None
        best_any = None

        for T_eff in T_grid:
            for eps in eps_grid:
                for eta in eta_grid:
                    for v_el in v_el_grid:
                        if distribution == "binomial":
                            for a_scale in alpha_scales:
                                for ncut in ncut_grid_bin:
                                    state = build_state_binomial(QAM_ALPHA0_BINOMIAL * a_scale, ncut)
                                    res = _evaluate("binomial", mode, state, T_eff, eps, eta, v_el)
                                    results.append(res)
                                    if best_any is None or res.skr_raw > best_any.skr_raw:
                                        best_any = res
                                    if res.status == "physical":
                                        if best_phys is None or res.skr_raw > best_phys.skr_raw:
                                            best_phys = res
                                    elif res.status == "clipped":
                                        if best_clip is None or res.skr_raw > best_clip.skr_raw:
                                            best_clip = res
                        elif distribution == "uniform":
                            for a_scale in alpha_scales:
                                for ncut in ncut_grid_uni:
                                    state = build_state_uniform(QAM_ALPHA0_UNIFORM * a_scale, ncut)
                                    res = _evaluate("uniform", mode, state, T_eff, eps, eta, v_el)
                                    results.append(res)
                                    if best_any is None or res.skr_raw > best_any.skr_raw:
                                        best_any = res
                                    if res.status == "physical":
                                        if best_phys is None or res.skr_raw > best_phys.skr_raw:
                                            best_phys = res
                                    elif res.status == "clipped":
                                        if best_clip is None or res.skr_raw > best_clip.skr_raw:
                                            best_clip = res
                        else:  # MB
                            for a_scale in alpha_scales:
                                for ncut in ncut_grid_mb:
                                    if mode == "fixed-parameter":
                                        state = build_state_mb(QAM_ALPHA0_MB * a_scale, ncut, QAM_NU_TILDE)
                                    else:
                                        # match VA to binomial baseline state (same alpha scaling)
                                        target_state = build_state_binomial(QAM_ALPHA0_BINOMIAL * a_scale, QAM_NCUT_BINOMIAL)
                                        nu_tuned, _ = _tune_nu_tilde(target_state.va, QAM_ALPHA0_MB * a_scale, ncut)
                                        state = build_state_mb(QAM_ALPHA0_MB * a_scale, ncut, nu_tuned)
                                    res = _evaluate("mb", mode, state, T_eff, eps, eta, v_el)
                                    results.append(res)
                                    if best_any is None or res.skr_raw > best_any.skr_raw:
                                        best_any = res
                                    if res.status == "physical":
                                        if best_phys is None or res.skr_raw > best_phys.skr_raw:
                                            best_phys = res
                                    elif res.status == "clipped":
                                        if best_clip is None or res.skr_raw > best_clip.skr_raw:
                                            best_clip = res

        return best_phys, best_clip, best_any

    print("\nSearching (coarse) across T_eff, eps, eta, v_el, alpha0, ncut...")
    best_bin_phys, best_bin_clip, best_bin_any = search_distribution("binomial", "fixed-parameter")
    best_uni_phys, best_uni_clip, best_uni_any = search_distribution("uniform", "fixed-parameter")
    best_mb_phys, best_mb_clip, best_mb_any = search_distribution("mb", "matched-VA")

    def print_best(label: str, res: EvalResult | None, title: str):
        print(f"\n{title} - {label}")
        if res is None:
            print("  None found.")
            return
        print(
            f"  T_eff={res.T_eff:.4f}, eps={res.eps:.4f}, eta={res.eta:.3f}, v_el={res.v_el:.4f}, "
            f"alpha0={res.alpha0:.4f}, ncut={res.ncut}, nu_tilde={res.nu_tilde}"
        )
        print(
            f"  status={res.status}, Z_raw={res.z_raw:.6f}, Zmax={res.z_max:.6f}, "
            f"chi_BE={res.chi_be:.6f}, I_AB={res.i_ab:.6f}, SKR_raw={res.skr_raw:.6f}"
        )

    print_best("Binomial", best_bin_phys, "Best physical")
    print_best("Binomial", best_bin_clip, "Best clipped (non-physical)")
    print_best("Uniform", best_uni_phys, "Best physical")
    print_best("Uniform", best_uni_clip, "Best clipped (non-physical)")
    print_best("MB (matched-VA)", best_mb_phys, "Best physical")
    print_best("MB (matched-VA)", best_mb_clip, "Best clipped (non-physical)")

    # Minimal T_eff threshold (coarse)
    def threshold_T_for_positive(distribution: str, mode: str):
        best_by_T = []
        for T_eff in T_grid:
            best_phys = None
            for eps in eps_grid:
                for eta in eta_grid:
                    for v_el in v_el_grid:
                        if distribution == "binomial":
                            state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
                        elif distribution == "uniform":
                            state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
                        else:
                            if mode == "fixed-parameter":
                                state = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)
                            else:
                                target_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
                                nu_tuned, _ = _tune_nu_tilde(target_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB)
                                state = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_tuned)

                        res = _evaluate(distribution, mode, state, T_eff, eps, eta, v_el)
                        if res.status == "physical":
                            if best_phys is None or res.skr_raw > best_phys.skr_raw:
                                best_phys = res
            best_by_T.append((T_eff, best_phys))

        min_T = None
        best_at_min = None
        for T_eff, res in best_by_T:
            if res is not None and res.skr_raw > 0:
                min_T = T_eff
                best_at_min = res
                break
        return min_T, best_at_min

    print("\nMinimal T_eff thresholds (coarse, physical only):")
    for label, mode in [
        ("binomial", "fixed-parameter"),
        ("uniform", "fixed-parameter"),
        ("mb", "matched-VA"),
    ]:
        min_T, res = threshold_T_for_positive(label, mode)
        if min_T is None:
            print(f"  {label:8s}: No physical SKR_raw > 0 found on coarse grid.")
        else:
            print(
                f"  {label:8s}: min T_eff ≈ {min_T:.4f} "
                f"(SKR_raw={res.skr_raw:.6f}, eps={res.eps:.4f}, eta={res.eta:.3f}, v_el={res.v_el:.4f})"
            )

    csv_path = out_dir / "skr_positive_search.csv"
    _write_csv(csv_path, results)
    print(f"\nCSV saved: {csv_path} ({len(results)} rows)")


if __name__ == "__main__":
    main()
