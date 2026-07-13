"""
Visualize SKR sweeps for QAM-256 (uniform, binomial, Maxwell–Boltzmann).

Assumptions:
- v_el is the sweep variable for electronic noise.
- nu_tilde is the Maxwell–Boltzmann shaping parameter.
- Z* uses sqrt(2*T*eps*w), consistent with qam_count logic.
- I_AB uses chi_tot (consistent with qam_count helpers).
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

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
    from uav_hap_1_sample.visualization.v_sweep import SweepSeries, plot_nu_sweep
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
    from .visualization.v_sweep import SweepSeries, plot_nu_sweep
    from .zstar import mb as zmb


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


def _write_csv(csv_path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


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


def _plot_skr_sweep(x_values, series, xlabel, out_path: Path, title: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("matplotlib not available: skipping plot", out_path)
        return

    fig, ax = plt.subplots(figsize=(8.2, 5.2), constrained_layout=True)

    for item in series:
        status = item["status"]
        skr_raw = item["skr_raw"]
        physical_mask = status == "physical"
        clipped_mask = status == "clipped"
        invalid_mask = status == "invalid"

        # Plot only physical points as the main line
        skr_physical = np.where(physical_mask, skr_raw, np.nan)
        ax.plot(x_values, skr_physical, lw=2.0, label=item["label"])

        # Overlay clipped/invalid points as markers
        if np.any(clipped_mask):
            ax.scatter(x_values[clipped_mask], skr_raw[clipped_mask], marker="x", s=55, color="orange")
        if np.any(invalid_mask):
            ax.scatter(x_values[invalid_mask], skr_raw[invalid_mask], marker="x", s=55, color="red")

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("SKR_raw (bits/use)")
    ax.grid(alpha=0.3)
    from matplotlib.lines import Line2D

    legend_extra = [
        Line2D([0], [0], marker="x", color="orange", linestyle="None", label="clipped (non-physical)"),
        Line2D([0], [0], marker="x", color="red", linestyle="None", label="invalid"),
    ]
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles + legend_extra, labels + [h.get_label() for h in legend_extra], frameon=False)

    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _plot_rho_sweep(x_values, series, xlabel, out_path: Path, title: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print("matplotlib not available: skipping plot", out_path)
        return

    fig, ax = plt.subplots(figsize=(8.2, 5.2), constrained_layout=True)
    for item in series:
        ax.plot(x_values, item["rho"], lw=2.0, label=item["label"])
    ax.axhline(1.0, color="red", linestyle="--", linewidth=1.5, label="rho=1 (clipping)")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("rho = Z_raw / Zmax")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    geom = GeometryParams()
    ch_params = ChannelParams()
    fading = channel(geometry=geom, channel_params=ch_params, N=30_000, rng=np.random.default_rng(42))
    T_eff = float(fading["T_eff"])

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    bin_state = build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL)
    uni_state = build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM)
    # MB mode: "fixed-parameter" uses QAM_NU_TILDE, "matched-VA" matches VA to binomial
    mb_mode = "matched-VA"
    nu_grid = np.linspace(0.02, 0.6, 40)
    if mb_mode == "matched-VA":
        nu_tuned, va_tuned = _tune_nu_tilde(bin_state.va, QAM_ALPHA0_MB, QAM_NCUT_MB, nu_grid)
        mb_state_fixed = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, nu_tuned)
        va_err = abs(va_tuned - bin_state.va)
        mb_label = f"mb (nu={nu_tuned:.3f}, VA~{va_tuned:.3f}, err={va_err:.2e})"
    else:
        mb_state_fixed = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE)
        mb_label = f"mb (nu={QAM_NU_TILDE})"

    # Sweep grids
    T_values = np.linspace(0.05, 0.95, 30)
    eps_values = np.linspace(0.0, 0.03, 30)
    v_el_values = np.linspace(0.0, 0.05, 31)
    nu_values = np.linspace(0.02, 0.6, 30)

    rows = []

    def sweep_one(state, label, sweep_name, sweep_values):
        skr_raw_vals = []
        status_vals = []
        rho_vals = []
        for val in sweep_values:
            if sweep_name == "T":
                metrics = compute_metrics(state, float(val), QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
                eps = QAM_EPS
                eta = QAM_ETA
                v_el = QAM_V_EL
            elif sweep_name == "eps":
                metrics = compute_metrics(state, T_eff, float(val), QAM_BETA, QAM_ETA, QAM_V_EL)
                eps = float(val)
                eta = QAM_ETA
                v_el = QAM_V_EL
            elif sweep_name == "v_el":
                metrics = compute_metrics(state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, float(val))
                eps = QAM_EPS
                eta = QAM_ETA
                v_el = float(val)
            else:
                raise ValueError("Unsupported sweep")

            status = _status(metrics)
            skr_raw_vals.append(metrics.skr_raw)
            status_vals.append(status)
            rho_vals.append(metrics.z_raw_over_zmax)
            rows.append(
                {
                    "sweep": sweep_name,
                    "distribution": label,
                    "T": float(val) if sweep_name == "T" else T_eff,
                    "eps": eps,
                    "eta": eta,
                    "v_el": v_el,
                    "nu_tilde": state.nu_tilde,
                    "term_signal": metrics.term_signal,
                    "term_noise": metrics.term_noise,
                    "signal_to_zmax": metrics.term_signal / metrics.z_star_max if metrics.z_star_max > 0 else float("nan"),
                    "noise_fraction": metrics.term_noise / metrics.term_signal if metrics.term_signal > 0 else float("nan"),
                    "z_star_raw": metrics.z_star_raw,
                    "z_star_used": metrics.z_star,
                    "z_star_max": metrics.z_star_max,
                    "rho": metrics.z_raw_over_zmax,
                    "margin": metrics.z_raw_margin,
                    "status": status,
                    "chi_be": metrics.chi_be,
                    "i_ab": metrics.i_ab,
                    "skr_raw": metrics.skr_raw,
                    "skr": metrics.skr,
                }
            )

        return (
            np.array(skr_raw_vals, dtype=float),
            np.array(status_vals, dtype=object),
            np.array(rho_vals, dtype=float),
        )

    # SKR vs T
    bin_skr_T, bin_status_T, bin_rho_T = sweep_one(bin_state, "binomial", "T", T_values)
    uni_skr_T, uni_status_T, uni_rho_T = sweep_one(uni_state, "uniform", "T", T_values)
    mb_skr_T, mb_status_T, mb_rho_T = sweep_one(mb_state_fixed, "mb", "T", T_values)

    _plot_skr_sweep(
        T_values,
        [
            {"label": "binomial", "skr_raw": bin_skr_T, "status": bin_status_T},
            {"label": "uniform", "skr_raw": uni_skr_T, "status": uni_status_T},
            {"label": mb_label, "skr_raw": mb_skr_T, "status": mb_status_T},
        ],
        xlabel="T_eff",
        out_path=out_dir / "skr_vs_T.png",
        title="SKR vs T_eff (eps, eta, v_el fixed)",
    )

    # SKR vs eps
    bin_skr_eps, bin_status_eps, bin_rho_eps = sweep_one(bin_state, "binomial", "eps", eps_values)
    uni_skr_eps, uni_status_eps, uni_rho_eps = sweep_one(uni_state, "uniform", "eps", eps_values)
    mb_skr_eps, mb_status_eps, mb_rho_eps = sweep_one(mb_state_fixed, "mb", "eps", eps_values)

    _plot_skr_sweep(
        eps_values,
        [
            {"label": "binomial", "skr_raw": bin_skr_eps, "status": bin_status_eps},
            {"label": "uniform", "skr_raw": uni_skr_eps, "status": uni_status_eps},
            {"label": mb_label, "skr_raw": mb_skr_eps, "status": mb_status_eps},
        ],
        xlabel="eps",
        out_path=out_dir / "skr_vs_eps.png",
        title="SKR vs eps (T_eff, eta, v_el fixed)",
    )

    # SKR vs v_el
    bin_skr_v, bin_status_v, bin_rho_v = sweep_one(bin_state, "binomial", "v_el", v_el_values)
    uni_skr_v, uni_status_v, uni_rho_v = sweep_one(uni_state, "uniform", "v_el", v_el_values)
    mb_skr_v, mb_status_v, mb_rho_v = sweep_one(mb_state_fixed, "mb", "v_el", v_el_values)

    _plot_skr_sweep(
        v_el_values,
        [
            {"label": "binomial", "skr_raw": bin_skr_v, "status": bin_status_v},
            {"label": "uniform", "skr_raw": uni_skr_v, "status": uni_status_v},
            {"label": mb_label, "skr_raw": mb_skr_v, "status": mb_status_v},
        ],
        xlabel="v_el",
        out_path=out_dir / "skr_vs_v_el.png",
        title=f"SKR vs v_el (T_eff={T_eff:.3f}, eps fixed)",
    )

    _plot_rho_sweep(
        v_el_values,
        [
            {"label": "binomial", "rho": bin_rho_v},
            {"label": "uniform", "rho": uni_rho_v},
            {"label": mb_label, "rho": mb_rho_v},
        ],
        xlabel="v_el",
        out_path=out_dir / "rho_vs_v_el.png",
        title=f"rho = Z_raw/Zmax vs v_el (T_eff={T_eff:.3f})",
    )

    # Sweep nu_tilde (MB only; binomial/uniform drawn as flat baselines)
    mb_z, mb_chi, mb_iab, mb_skr = [], [], [], []
    mb_rows_nu = []
    mb_status_nu = []
    for nu in nu_values:
        mb_state = build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, float(nu))
        metrics = compute_metrics(mb_state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
        mb_z.append(metrics.z_star)
        mb_chi.append(metrics.chi_be)
        mb_iab.append(metrics.i_ab)
        mb_skr.append(metrics.skr_raw)
        status = _status(metrics)
        mb_status_nu.append(status)
        mb_rows_nu.append(
            {
                "sweep": "nu_tilde",
                "distribution": "mb",
                "T": T_eff,
                "eps": QAM_EPS,
                "eta": QAM_ETA,
                "v_el": QAM_V_EL,
                "nu_tilde": float(nu),
            "term_signal": metrics.term_signal,
            "term_noise": metrics.term_noise,
            "signal_to_zmax": metrics.term_signal / metrics.z_star_max if metrics.z_star_max > 0 else float("nan"),
            "noise_fraction": metrics.term_noise / metrics.term_signal if metrics.term_signal > 0 else float("nan"),
            "z_star_raw": metrics.z_star_raw,
                "z_star_used": metrics.z_star,
                "z_star_max": metrics.z_star_max,
                "rho": metrics.z_raw_over_zmax,
                "margin": metrics.z_raw_margin,
                "chi_be": metrics.chi_be,
                "i_ab": metrics.i_ab,
                "skr_raw": metrics.skr_raw,
                "skr": metrics.skr,
                "status": status,
            }
        )
    rows.extend(mb_rows_nu)

    bin_metrics_fixed = compute_metrics(bin_state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    uni_metrics_fixed = compute_metrics(uni_state, T_eff, QAM_EPS, QAM_BETA, QAM_ETA, QAM_V_EL)
    bin_status_fixed = _status(bin_metrics_fixed)
    uni_status_fixed = _status(uni_metrics_fixed)

    nu_series = [
        SweepSeries(
            "binomial",
            nu_values,
            np.full_like(nu_values, bin_metrics_fixed.z_star, dtype=float),
            np.full_like(nu_values, bin_metrics_fixed.chi_be, dtype=float),
            np.full_like(nu_values, bin_metrics_fixed.i_ab, dtype=float),
            np.full_like(nu_values, bin_metrics_fixed.skr_raw, dtype=float),
            status=np.full_like(nu_values, bin_status_fixed, dtype=object),
        ),
        SweepSeries(
            "uniform",
            nu_values,
            np.full_like(nu_values, uni_metrics_fixed.z_star, dtype=float),
            np.full_like(nu_values, uni_metrics_fixed.chi_be, dtype=float),
            np.full_like(nu_values, uni_metrics_fixed.i_ab, dtype=float),
            np.full_like(nu_values, uni_metrics_fixed.skr_raw, dtype=float),
            status=np.full_like(nu_values, uni_status_fixed, dtype=object),
        ),
        SweepSeries("mb", nu_values, np.array(mb_z), np.array(mb_chi), np.array(mb_iab), np.array(mb_skr), status=np.array(mb_status_nu, dtype=object)),
    ]
    try:
        nu_plot_path = plot_nu_sweep(nu_series, out_dir)
    except ModuleNotFoundError:
        nu_plot_path = None
        print("matplotlib not available: skipping nu_tilde plot")

    csv_path = out_dir / "qam_skr_sweeps.csv"
    _write_csv(csv_path, rows)

    print("=" * 70)
    print("Visualization completed")
    print("=" * 70)
    print(f"T_eff = {T_eff:.6f}, eps = {QAM_EPS}, beta = {QAM_BETA}, eta = {QAM_ETA}")
    print(f"MB mode: {mb_mode}, label: {mb_label}")
    print(
        "Saved plots: "
        f"{out_dir / 'skr_vs_T.png'}, "
        f"{out_dir / 'skr_vs_eps.png'}, "
        f"{out_dir / 'skr_vs_v_el.png'}, "
        f"{out_dir / 'rho_vs_v_el.png'}"
    )
    if nu_plot_path is not None:
        print(f"Saved plot: {nu_plot_path}")
    print(f"Saved CSV:  {csv_path}")


if __name__ == "__main__":
    main()
