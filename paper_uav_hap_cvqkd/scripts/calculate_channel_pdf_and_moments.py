"""Calculate the exploratory Case-D channel PDF and its three requested moments."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import quad
from scipy.special import i0e, ndtr, roots_laguerre


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml  # noqa: E402
from src.channel.aoa import aoa_outage_probability, aoa_variance_rad2  # noqa: E402
from src.channel.atmospheric_loss import atmospheric_transmittance  # noqa: E402
from src.channel.fso_channel import sample_fso_channel  # noqa: E402
from src.channel.geometry import LinkGeometry  # noqa: E402
from src.channel.pointing_error import pointing_parameters  # noqa: E402
from src.channel.turbulence import (  # noqa: E402
    UavMotion,
    pointing_displacement_variance_m2,
)
from src.utils.random import array_sha256  # noqa: E402


SCENARIO_ARTIFACT = ROOT / "results" / "analysis_channel_grid_20260911.json"
DEFAULT_CONFIG = ROOT / "configs" / "default.yaml"
OUTPUT_JSON = ROOT / "results" / "channel_pdf_and_moments.json"
OUTPUT_PNG = ROOT / "results" / "figures_preliminary" / "channel_transmittance_pdf.png"
OUTPUT_PDF = ROOT / "results" / "figures_preliminary" / "channel_transmittance_pdf.pdf"
MC_SAMPLE_COUNT = 100_000


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _comparison(quadrature: float, monte_carlo: float) -> dict[str, float]:
    difference = abs(monte_carlo - quadrature)
    return {
        "quadrature": quadrature,
        "monte_carlo": monte_carlo,
        "absolute_difference": difference,
        "relative_difference": difference / max(abs(quadrature), np.finfo(float).tiny),
    }


def main() -> None:
    scenario = json.loads(SCENARIO_ARTIFACT.read_text(encoding="utf-8"))
    config = load_yaml(DEFAULT_CONFIG)
    source = scenario["source"]
    case = source["channel_config"]
    provenance = source["channel_metadata"]["provenance"]
    if source["case"] != "D" or not scenario["phase_disabled"] or scenario["c_phi"] != 0.0:
        raise ValueError("The selected analysis artifact is not phase-disabled Case D.")
    if provenance["physical_domain_rule"] != "truncated_renormalized_active_law":
        raise ValueError("Case D does not use the required physical active-law treatment.")

    geometry_data = provenance["geometry"]
    geometry = LinkGeometry(
        geometry_data["h_hap_m"],
        geometry_data["h_uav_m"],
        geometry_data["zenith_angle_rad"],
    )
    motion = UavMotion(**case["uav_motion"])
    wavelength_m = float(provenance["wavelength_m"])
    visibility_km = float(provenance["visibility_km"])
    beam_waist_m = float(provenance["beam_waist_m"])
    aperture_radius_m = float(provenance["aperture_radius_m"])
    v_sc = float(case["v_sc_override"])
    sigma_hap_ang_rad = float(case["sigma_hap_ang_rad"])
    rho = math.hypot(*map(float, provenance["boresight_m"]))
    theta_fov_rad = float(case["theta_fov_rad"])

    eta_atm = atmospheric_transmittance(
        geometry.link_length_m, visibility_km, wavelength_m
    )
    pointing = pointing_parameters(
        aperture_radius_m, beam_waist_m, wavelength_m, geometry.link_length_m
    )
    sigma_m2 = pointing_displacement_variance_m2(
        motion,
        geometry.link_length_m,
        sigma_hap_ang_rad,
        "per_axis",
    )
    sigma_m = math.sqrt(sigma_m2)
    sigma_o2 = aoa_variance_rad2(
        motion,
        sigma_turb_AoA2=case["sigma_turb_AoA2"],
        model=case["aoa_model"],
        provenance=case["turbulence_aoa_provenance"],
    )
    sigma_o = math.sqrt(sigma_o2)
    p_out = aoa_outage_probability(theta_fov_rad, sigma_o2)
    p_in = 1.0 - p_out

    # Case D has zero boresight, so y=r^2/(2 sigma_m^2) is unit exponential.
    if rho != 0.0:
        raise ValueError("This bounded implementation expects Case D's zero boresight.")
    laguerre_nodes, laguerre_weights = roots_laguerre(256)
    radial = np.sqrt(2.0 * sigma_m2 * laguerre_nodes)
    pointing_log_loss = np.power(radial / pointing.scale_radius_m, pointing.gamma)
    log_a = math.log(eta_atm * pointing.t0_power) - pointing_log_loss
    log_x_mean = log_a - 0.5 * v_sc
    sqrt_v_sc = math.sqrt(v_sc)
    normalizer = math.sqrt(2.0 * math.pi * v_sc)

    def log_x_pdf(log_t: float | np.ndarray) -> float | np.ndarray:
        values = np.asarray(log_t, dtype=np.float64)
        z = (values[..., None] - log_x_mean) / sqrt_v_sc
        density = np.sum(laguerre_weights * np.exp(-0.5 * z * z), axis=-1) / normalizer
        return float(density) if density.ndim == 0 else density

    def pointing_q_pdf(q: float) -> float:
        if q <= 0.0:
            return 0.0
        power = q ** (1.0 / pointing.gamma)
        argument = rho * pointing.scale_radius_m * power / sigma_m2
        exponent = (
            2.0 / pointing.gamma - 1.0
        ) * math.log(q) - (
            pointing.scale_radius_m**2 * q ** (2.0 / pointing.gamma) + rho**2
        ) / (
            2.0 * sigma_m2
        ) + abs(argument)
        return (
            pointing.scale_radius_m**2
            / (pointing.gamma * sigma_m2)
            * math.exp(exponent)
            * float(i0e(argument))
        )

    # Every improper integral is evaluated after a log/support transformation.
    hsc_normalization, hsc_norm_error = quad(
        lambda y: math.exp(-0.5 * ((y + 0.5 * v_sc) / sqrt_v_sc) ** 2)
        / normalizer,
        -np.inf,
        np.inf,
        epsabs=1e-12,
        epsrel=1e-12,
    )
    hsc_mean, hsc_mean_error = quad(
        lambda y: math.exp(y - 0.5 * ((y + 0.5 * v_sc) / sqrt_v_sc) ** 2)
        / normalizer,
        -np.inf,
        np.inf,
        epsabs=1e-12,
        epsrel=1e-12,
    )
    hp_normalization, hp_norm_error = quad(
        pointing_q_pdf, 0.0, np.inf, epsabs=1e-12, epsrel=1e-12, limit=300
    )
    fx_normalization, fx_norm_error = quad(
        log_x_pdf, -np.inf, np.inf, epsabs=1e-11, epsrel=1e-11, limit=300
    )
    f_x_1, f_x_1_error = quad(
        log_x_pdf, -np.inf, 0.0, epsabs=1e-12, epsrel=1e-12, limit=300
    )

    def truncated_raw_moment(power: float) -> tuple[float, float]:
        return quad(
            lambda log_t: math.exp(power * log_t) * float(log_x_pdf(log_t)),
            -np.inf,
            0.0,
            epsabs=1e-12,
            epsrel=1e-12,
            limit=300,
        )

    eta_numerator, eta_error = truncated_raw_moment(1.0)
    sqrt_eta_numerator, sqrt_eta_error = truncated_raw_moment(0.5)
    mean_eta_active = eta_numerator / f_x_1
    mean_eta = p_in * mean_eta_active
    mean_sqrt_eta_active = sqrt_eta_numerator / f_x_1
    mean_sqrt_eta = p_in * mean_sqrt_eta_active
    sqrt_mean_eta = math.sqrt(mean_eta)
    p_x_gt_1 = 1.0 - f_x_1

    noise = config["channel"]["excess_noise_distribution"]
    if noise["kind"] != "independent_uniform" or noise["dependence_on_transmittance"] != "independent":
        raise ValueError("Case D requires the current independent-uniform epsilon_base law.")
    epsilon_min = float(noise["minimum_snu"])
    epsilon_max = float(noise["maximum_snu"])
    mean_epsilon = 0.5 * (epsilon_min + epsilon_max)
    mean_eta_xi = mean_eta * mean_epsilon

    channel = sample_fso_channel(
        geometry=geometry,
        wavelength_m=wavelength_m,
        visibility_km=visibility_km,
        beam_waist_m=beam_waist_m,
        aperture_radius_m=aperture_radius_m,
        cn2_m_minus_two_thirds=provenance["legacy_scalar_cn2_m_minus_two_thirds"],
        sample_count=MC_SAMPLE_COUNT,
        rng=np.random.default_rng(int(source["channel_seed"])),
        uav_motion=motion,
        scintillation_log_variance=None,
        v_sc_override=v_sc,
        aperture_averaging_model="explicit_v_sc_override",
        boresight_x_m=provenance["boresight_m"][0],
        boresight_y_m=provenance["boresight_m"][1],
        sigma_hap_ang_rad=sigma_hap_ang_rad,
        hap_angular_jitter_convention="per_axis",
        aoa_model=case["aoa_model"],
        sigma_turb_AoA2=case["sigma_turb_AoA2"],
        turbulence_aoa_provenance=case["turbulence_aoa_provenance"],
        theta_fov_rad=theta_fov_rad,
    )
    epsilon_base = np.random.default_rng(int(source["epsilon_base_seed"])).uniform(
        epsilon_min, epsilon_max, MC_SAMPLE_COUNT
    )
    t_mc = channel.transmittance
    mc_values = {
        "mean_eta": float(np.mean(t_mc)),
        "mean_sqrt_eta": float(np.mean(np.sqrt(t_mc))),
        "mean_eta_xi": float(np.mean(t_mc * epsilon_base)),
    }
    comparisons = {
        "mean_eta": _comparison(mean_eta, mc_values["mean_eta"]),
        "mean_sqrt_eta": _comparison(mean_sqrt_eta, mc_values["mean_sqrt_eta"]),
        "mean_eta_xi": _comparison(mean_eta_xi, mc_values["mean_eta_xi"]),
    }
    for name, samples, expected in (
        ("mean_eta", t_mc, mean_eta),
        ("mean_sqrt_eta", np.sqrt(t_mc), mean_sqrt_eta),
        ("mean_eta_xi", t_mc * epsilon_base, mean_eta_xi),
    ):
        standard_error = float(np.std(samples, ddof=1) / math.sqrt(MC_SAMPLE_COUNT))
        comparisons[name]["monte_carlo_standard_error"] = standard_error
        comparisons[name]["difference_in_standard_errors"] = abs(
            float(np.mean(samples)) - expected
        ) / standard_error

    eta_grid = np.geomspace(1e-12, 1.0, 1200)
    p_active = np.asarray(log_x_pdf(np.log(eta_grid))) / eta_grid / f_x_1
    p_continuous = p_in * p_active
    sampled_active_integral = float(
        np.trapezoid(p_active * eta_grid, np.log(eta_grid))
    )

    checks = {
        "integral_f_Hsc": hsc_normalization,
        "integral_f_Hsc_quadrature_error": hsc_norm_error,
        "mean_Hsc": hsc_mean,
        "mean_Hsc_quadrature_error": hsc_mean_error,
        "integral_f_Hp": hp_normalization,
        "integral_f_Hp_quadrature_error": hp_norm_error,
        "integral_f_X": fx_normalization,
        "integral_f_X_quadrature_error": fx_norm_error,
        "integral_p_active": f_x_1 / f_x_1,
        "sampled_grid_integral_p_active": sampled_active_integral,
        "p_out_plus_p_in": p_out + p_in,
        "jensen_outage_inclusive": mean_sqrt_eta <= sqrt_mean_eta + 1e-13,
        "mean_eta_quadrature_error": eta_error / f_x_1,
        "mean_sqrt_eta_quadrature_error": sqrt_eta_error / f_x_1,
        "laguerre_weight_sum": float(np.sum(laguerre_weights)),
    }
    if not (
        abs(hsc_normalization - 1.0) < 1e-10
        and abs(hsc_mean - 1.0) < 1e-10
        and abs(hp_normalization - 1.0) < 1e-9
        and abs(fx_normalization - 1.0) < 1e-9
        and abs(sampled_active_integral - 1.0) < 5e-4
        and checks["jensen_outage_inclusive"]
        and all(row["difference_in_standard_errors"] < 6.0 for row in comparisons.values())
    ):
        raise FloatingPointError("A channel PDF/moment verification check failed.")

    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.0, 5.2), constrained_layout=True)
    ax.plot(eta_grid, p_active, label=r"$p_{active}(\eta)$", linewidth=2.0)
    ax.plot(eta_grid, p_continuous, "--", label=r"$p_{in}p_{active}(\eta)$", linewidth=1.8)
    ax.axvline(mean_eta, color="black", linestyle=":", linewidth=1.4, label=r"$\langle\eta\rangle$")
    ax.set_xscale("log")
    ax.set_xlim(1e-5, 1.0)
    ax.set_xlabel(r"Power transmittance $\eta=T$")
    ax.set_ylabel("Probability density")
    ax.set_title("Physical HAP-UAV Channel Transmittance Distribution")
    ax.grid(True, which="both", alpha=0.22)
    ax.legend()
    ax.text(
        0.98,
        0.97,
        "\n".join(
            (
                f"AoA outage mass = {p_out:.6g}",
                rf"$\langle\sqrt{{\eta}}\rangle$ = {mean_sqrt_eta:.6g}",
                rf"$P(X>1)$ = {p_x_gt_1:.3e}",
            )
        ),
        transform=ax.transAxes,
        ha="right",
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
    )
    fig.savefig(OUTPUT_PNG, dpi=300)
    fig.savefig(OUTPUT_PDF)
    plt.close(fig)

    payload: dict[str, Any] = {
        "schema": "channel-pdf-and-moments-v1",
        "status": "CURRENTLY_VERIFIED_PASS",
        "artifact_class": "ANALYSIS_ESTIMATE_NOT_PUBLICATION_CERTIFIED",
        "scenario": {
            "name": "exploratory_case_D_20260911",
            "source_artifact": str(SCENARIO_ARTIFACT.relative_to(ROOT)),
            "source_artifact_sha256": _sha256(SCENARIO_ARTIFACT),
            "default_config_epsilon_source": str(DEFAULT_CONFIG.relative_to(ROOT)),
            "default_config_sha256": _sha256(DEFAULT_CONFIG),
            "source_case_config": case,
            "phase_disabled": True,
            "c_phi": 0.0,
            "limitations": [
                "Exploratory analysis scenario; not publication-approved channel evidence.",
                "v_sc=0.25 and the external AoA fixture are explicit analysis choices.",
                "No training, SKR, security optimization, final-test access, or publication-scale run.",
            ],
        },
        "repository": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("branch", "--show-current"),
            "dirty_at_artifact_write": bool(_git("status", "--porcelain")),
            "producer": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": _sha256(Path(__file__)),
            "source_hashes": {
                str(path.relative_to(ROOT)): _sha256(path)
                for path in (
                    ROOT / "src/channel/fso_channel.py",
                    ROOT / "src/channel/pointing_error.py",
                    ROOT / "src/channel/scintillation.py",
                    ROOT / "src/channel/aoa.py",
                    ROOT / "src/channel/atmospheric_loss.py",
                    ROOT / "src/channel/turbulence.py",
                )
            },
        },
        "physical_parameters": {
            "h_hap_m": geometry.h_hap_m,
            "h_uav_m": geometry.h_uav_m,
            "zenith_angle_rad": geometry.zenith_angle_rad,
            "link_length_m": geometry.link_length_m,
            "wavelength_m": wavelength_m,
            "visibility_km": visibility_km,
            "beam_waist_m": beam_waist_m,
            "aperture_radius_m": aperture_radius_m,
            "uav_motion": case["uav_motion"],
            "sigma_hap_ang_rad": sigma_hap_ang_rad,
            "theta_fov_rad": theta_fov_rad,
            "epsilon_base_distribution": {
                "kind": "independent_uniform",
                "minimum_snu": epsilon_min,
                "maximum_snu": epsilon_max,
            },
        },
        "derived_parameters": {
            "eta_atm": eta_atm,
            "v_sc": v_sc,
            "eta_p0": pointing.t0_power,
            "R_m": pointing.scale_radius_m,
            "Gamma": pointing.gamma,
            "sigma_m": sigma_m,
            "rho": rho,
            "sigma_o": sigma_o,
        },
        "distribution": {
            "p_out": p_out,
            "p_in": p_in,
            "F_X_1": f_x_1,
            "F_X_1_quadrature_error": f_x_1_error,
            "P_X_gt_1": p_x_gt_1,
            "eta_grid": eta_grid.tolist(),
            "p_active": p_active.tolist(),
            "p_continuous": p_continuous.tolist(),
        },
        "moments": {
            "mean_eta": mean_eta,
            "mean_eta_active": mean_eta_active,
            "mean_sqrt_eta": mean_sqrt_eta,
            "mean_sqrt_eta_active": mean_sqrt_eta_active,
            "sqrt_mean_eta": sqrt_mean_eta,
            "mean_eta_xi": mean_eta_xi,
            "xi_definition": "xi_eta = epsilon_total = epsilon_base because c_phi=0; epsilon_base is independent Uniform[0.001, 0.04] SNU",
        },
        "normalization_checks": checks,
        "monte_carlo": {
            "sample_count": MC_SAMPLE_COUNT,
            "channel_seed": int(source["channel_seed"]),
            "epsilon_base_seed": int(source["epsilon_base_seed"]),
            "empirical_p_out": float(np.mean(channel.aoa_gate == 0)),
            "empirical_P_X_gt_1": channel.metadata["p_above_one_active"],
            "transmittance_sha256": array_sha256(t_mc),
            "epsilon_base_sha256": array_sha256(epsilon_base),
            "comparisons": comparisons,
        },
        "figures": {
            "png": str(OUTPUT_PNG.relative_to(ROOT)),
            "pdf": str(OUTPUT_PDF.relative_to(ROOT)),
        },
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": payload["status"],
        "scenario": payload["scenario"]["name"],
        **payload["moments"],
        "p_out": p_out,
        "P_X_gt_1": p_x_gt_1,
        "output": str(OUTPUT_JSON),
    }, indent=2))


if __name__ == "__main__":
    main()
