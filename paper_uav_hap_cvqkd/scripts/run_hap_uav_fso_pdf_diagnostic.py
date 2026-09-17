"""Generate a bounded HAP--UAV channel PDF/Monte Carlo diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad

from _common import ROOT, load_yaml
from src.channel.aoa import aoa_outage_probability, sample_aoa_gate
from src.channel.diagnostics import (
    active_channel_moments,
    active_transmittance_pdf_eq49,
    active_transmittance_pdf_eq50,
)
from src.channel.fso_channel import sample_fso_channel
from src.channel.geometry import LinkGeometry
from src.channel.pointing_error import pointing_pdf, pointing_power_transmittance, rician_pdf
from src.channel.scintillation import lognormal_pdf
from src.channel.turbulence import UavMotion


def _plot(
    values: np.ndarray,
    x: np.ndarray,
    pdf: np.ndarray,
    path: Path,
    *,
    xlabel: str,
    title: str,
    pdf_label: str,
    second_pdf: np.ndarray | None = None,
    second_pdf_label: str | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.hist(values, bins=60, density=True, alpha=0.68, label="Monte Carlo")
    ax.plot(x, pdf, color="black", linewidth=2.0, label=pdf_label)
    if second_pdf is not None:
        ax.plot(x, second_pdf, color="tab:red", linestyle="--", linewidth=1.5, label=second_pdf_label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density")
    ax.set_title(title)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _stats(values: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean(values)),
        "variance": float(np.var(values)),
        "standard_deviation": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def _pdf_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--sample-count", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "hap_uav_fso_pdf_diagnostic",
    )
    args = parser.parse_args()
    if args.sample_count < 10_000:
        raise ValueError("Use at least 10,000 diagnostic realizations.")
    if args.seed < 0:
        raise ValueError("seed must be nonnegative.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = load_yaml(args.config.resolve())
    channel = config["channel"]
    profile = channel["turbulence_profile"]
    pointing_config = channel["pointing"]
    aoa_config = channel["aoa"]
    geometry = LinkGeometry(
        float(channel["h_hap_m"]),
        float(channel["h_uav_m"]),
        float(channel["zenith_angle_rad"]),
    )
    motion = UavMotion(**channel["uav_motion"])

    # The X diagnostic intentionally excludes AoA.  AoA is sampled separately
    # below so the plot remains the conditional active optical distribution.
    fso = sample_fso_channel(
        geometry=geometry,
        wavelength_m=float(channel["wavelength_m"]),
        visibility_km=float(channel["visibility_km"]),
        beam_waist_m=float(channel["beam_waist_m"]),
        aperture_radius_m=float(channel["aperture_radius_m"]),
        cn2_m_minus_two_thirds=float(channel["cn2_m_minus_two_thirds"]),
        sample_count=args.sample_count,
        rng=np.random.default_rng(args.seed),
        uav_motion=motion,
        scintillation_log_variance=None,
        v_sc_override=channel["scintillation"].get("v_sc_override"),
        aperture_averaging_model=channel["scintillation"]["aperture_averaging_model"],
        turbulence_profile_model=profile["model"],
        wind_speed_m_per_s=float(profile["wind_speed_m_per_s"]),
        ground_cn2_m_minus_two_thirds=float(profile["cn2_ground_m_minus_two_thirds"]),
        eta_atm=float(channel["eta_atm"]),
        theta_div_rad=float(channel["theta_div_rad"]),
        f0_m=float(channel["f0_m"]),
        sigma_h_m=float(pointing_config["sigma_h_m"]),
        boresight_x_m=float(pointing_config["boresight_x_m"]),
        boresight_y_m=float(pointing_config["boresight_y_m"]),
        sigma_hap_ang_rad=float(pointing_config["sigma_hap_ang_rad"]),
        hap_angular_jitter_convention=pointing_config["hap_angular_jitter_convention"],
        aoa_model="disabled",
    )
    h_sc = np.asarray(fso.scintillation_factor, dtype=np.float64)
    r_mis = np.asarray(fso.radial_displacement_m, dtype=np.float64)
    h_p = np.asarray(pointing_power_transmittance(r_mis, fso.pointing), dtype=np.float64)
    x_active = float(channel["eta_atm"]) * h_sc * h_p

    aoa_sigma_o2 = float(aoa_config["sigma_o_rad"]) ** 2
    aoa_gate = sample_aoa_gate(
        sample_count=args.sample_count,
        rng=np.random.default_rng(args.seed + 1),
        sigma_o2=aoa_sigma_o2,
        theta_fov_rad=float(aoa_config["theta_fov_rad"]),
    )
    p_out_analytic = aoa_outage_probability(
        float(aoa_config["theta_fov_rad"]), aoa_sigma_o2
    )

    v_sc = float(fso.metadata["provenance"]["scintillation_model"]["v_sc"])
    sigma_jt_m = float(fso.sigma_axis_m)
    rho_m = math.hypot(
        float(pointing_config["boresight_x_m"]),
        float(pointing_config["boresight_y_m"]),
    )
    hsc_x = np.linspace(max(1.0e-6, float(np.min(h_sc)) * 0.8), float(np.max(h_sc)) * 1.2, 800)
    r_x = np.linspace(0.0, float(np.max(r_mis)) * 1.1, 800)
    hp_x = np.linspace(float(np.min(h_p)) * 0.8, fso.pointing.t0_power, 800)
    x_x = np.linspace(1.0e-8, max(0.0015, float(np.max(x_active)) * 1.2), 800)
    _plot(
        h_sc,
        hsc_x,
        lognormal_pdf(hsc_x, v_sc),
        args.output_dir / "H_sc_monte_carlo_vs_pdf.png",
        xlabel=r"Scintillation gain $H_{\rm sc}$ (dimensionless)",
        title=r"$H_{\rm sc}$: Monte Carlo and analytical PDF (Eq. 12)",
        pdf_label="Analytical Eq. (12)",
    )
    _plot(
        r_mis,
        r_x,
        rician_pdf(r_x, sigma_jt_m, rho_m),
        args.output_dir / "r_mis_monte_carlo_vs_pdf.png",
        xlabel=r"Radial displacement $r_{\rm mis}$ (m)",
        title=r"$r_{\rm mis}$: Monte Carlo and analytical PDF (Eq. 26)",
        pdf_label="Analytical Eq. (26)",
    )
    _plot(
        h_p,
        hp_x,
        pointing_pdf(hp_x, fso.pointing, sigma_jt_m, rho_m),
        args.output_dir / "H_p_monte_carlo_vs_pdf.png",
        xlabel=r"Pointing coefficient $H_p$ (dimensionless)",
        title=r"$H_p$: Monte Carlo and analytical PDF (Eq. 37)",
        pdf_label="Analytical Eq. (37)",
    )
    x_pdf_eq50 = np.asarray(
        [
            active_transmittance_pdf_eq50(
                float(t),
                eta_atm=float(channel["eta_atm"]),
                v_sc=v_sc,
                pointing=fso.pointing,
                sigma_jt_m=sigma_jt_m,
                rho_m=rho_m,
            )
            for t in x_x
        ],
        dtype=np.float64,
    )
    x_pdf_eq49 = np.asarray(
        [
            active_transmittance_pdf_eq49(
                float(t),
                eta_atm=float(channel["eta_atm"]),
                v_sc=v_sc,
                pointing=fso.pointing,
                sigma_jt_m=sigma_jt_m,
                rho_m=rho_m,
            )
            for t in x_x
        ],
        dtype=np.float64,
    )
    _plot(
        x_active,
        x_x,
        x_pdf_eq50,
        args.output_dir / "X_active_monte_carlo_vs_pdf.png",
        xlabel=r"Active channel $X=\eta_{\rm atm}H_{\rm sc}H_p$ (dimensionless)",
        title=r"$X$: Monte Carlo and analytical PDF (Eq. 50), no AoA",
        pdf_label="Analytical Eq. (50)",
        second_pdf=x_pdf_eq49,
        second_pdf_label="Analytical Eq. (49)",
    )

    np.savez_compressed(
        args.output_dir / "samples.npz",
        H_sc=h_sc,
        r_mis=r_mis,
        H_p=h_p,
        X_active=x_active,
        B_AoA=aoa_gate,
    )
    hsc_mass = quad(
        lambda h: float(lognormal_pdf(np.asarray([h]), v_sc)[0]),
        0.0,
        math.inf,
    )[0]
    hp_mass = quad(
        lambda u: float(pointing_pdf(np.asarray([u]), fso.pointing, sigma_jt_m, rho_m)[0]),
        0.0,
        fso.pointing.t0_power,
    )[0]
    x_mass = quad(
        lambda log_t: active_transmittance_pdf_eq50(
            math.exp(log_t),
            eta_atm=float(channel["eta_atm"]),
            v_sc=v_sc,
            pointing=fso.pointing,
            sigma_jt_m=sigma_jt_m,
            rho_m=rho_m,
        )
        * math.exp(log_t),
        -40.0,
        0.0,
        limit=200,
    )[0]
    moments = active_channel_moments(
        eta_atm=float(channel["eta_atm"]),
        v_sc=v_sc,
        pointing=fso.pointing,
        sigma_jt_m=sigma_jt_m,
        p_in=1.0 - p_out_analytic,
        rho_m=rho_m,
    )
    result = {
        "status": "CHANNEL_ONLY_DIAGNOSTIC_NOT_PUBLICATION_CERTIFIED",
        "source_pdf": r"C:\Users\admin\Downloads\2026__Binh_s_work__Copy___Copy_ (5).pdf",
        "source_pdf_sha256": _pdf_sha256(Path(r"C:\Users\admin\Downloads\2026__Binh_s_work__Copy___Copy_ (5).pdf")),
        "config": str(args.config.resolve()),
        "config_sha256": _pdf_sha256(args.config.resolve()),
        "sample_count": args.sample_count,
        "seed": args.seed,
        "monte_carlo_used": True,
        "security_or_training_used": False,
        "x_active_excludes_aoa": True,
        "baseline": {
            "eta_atm": float(channel["eta_atm"]),
            "v_sc": v_sc,
            "sigma_jt_m": sigma_jt_m,
            "rho_m": rho_m,
            "sigma_o_rad": float(aoa_config["sigma_o_rad"]),
            "theta_fov_rad": float(aoa_config["theta_fov_rad"]),
            "A0": float(fso.pointing.t0_power),
            "omega_0_m": float(fso.pointing.omega_0_m),
            "omega_L_m": float(fso.pointing.beam_radius_receiver_m),
            "G_d": float(fso.pointing.g_d),
            "omega_L_e_m": float(fso.pointing.omega_L_e_m),
            "nu": float(fso.pointing.nu),
            "omega_L_eq_m": float(fso.pointing.omega_L_eq_m),
        },
        "statistics": {
            "H_sc": _stats(h_sc),
            "r_mis": _stats(r_mis),
            "H_p": _stats(h_p),
            "X_active": _stats(x_active),
        },
        "validation": {
            "integral_f_Hsc": float(hsc_mass),
            "integral_f_Hp": float(hp_mass),
            "integral_f_X_log_t_minus_40_to_0": float(x_mass),
            "F_X_1": moments["F_X_1"],
            "mean_T": moments["mean_T"],
            "mean_sqrt_T": moments["mean_sqrt_T"],
            "eq49_eq50_max_relative_difference": float(
                np.max(np.abs(x_pdf_eq49 - x_pdf_eq50) / np.maximum(x_pdf_eq50, 1.0e-300))
            ),
            "H_p_support": bool(np.all((h_p > 0.0) & (h_p <= fso.pointing.t0_power))),
            "p_out_empirical": float(np.mean(aoa_gate == 0)),
            "p_out_analytic": float(p_out_analytic),
            "p_in_empirical": float(np.mean(aoa_gate == 1)),
            "raw_transmittance_above_one_count": int(np.count_nonzero(x_active > 1.0)),
            "raw_transmittance_above_one_probability": float(np.mean(x_active > 1.0)),
        },
        "figures": [
            "H_sc_monte_carlo_vs_pdf.png",
            "r_mis_monte_carlo_vs_pdf.png",
            "H_p_monte_carlo_vs_pdf.png",
            "X_active_monte_carlo_vs_pdf.png",
        ],
        "arrays_file": "samples.npz",
    }
    (args.output_dir / "diagnostic_results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
