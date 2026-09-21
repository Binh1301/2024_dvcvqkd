"""Fixed-VA=2 weak-PE HAP-UAV beam-divergence diagnostic search."""

from __future__ import annotations

import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import tempfile
import time
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    _untruncated_moment,
    analyze_product,
    derive_physical_inputs,
)
from scripts.run_effective_channel_va2 import physical_channel_parameters
from src.channel.atmospheric_loss import atmospheric_transmittance
from src.channel.geometry import HAP_ALTITUDE_M, zenith_angle_rad_for_link_length_m
from src.channel.phase_noise import phase_parameter_provenance
import src.cvqkd.holevo as holevo_module
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import (
    discrete_mutual_information,
    standard_complex_noise,
)
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator


VA = 2.0
BETA = 0.95
NU_MB = 0.20
THETA_DIV_FULL_URAD = (50, 75, 100, 125, 150, 175, 200, 223, 250, 300, 350, 400)
L_KM = tuple(19.0 + 0.5 * index for index in range(11))
H_UAV_M = 1000.0
RHO_M = math.hypot(0.30, 0.20)
SIGMA_H_M = 0.20
SIGMA_HAP_ANG_RAD = 1.0e-6
APERTURE_RADIUS_M = 0.10
CN2_GROUND = 1.7e-14
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
SCHEMES = ("uniform", "binomial", "mb")
SOURCE_CHECKPOINTS = {
    "uniform": (
        "cvqkd_uniform_va2_c4_checkpoint.json",
        "1.4019995788968011700681192152159252514555640211395",
        "0.026543338228713932540445642845440478987301227896247",
    ),
    "binomial": (
        "cvqkd_binomial_va2_c4_checkpoint.json",
        "1.4141475013110644521324597287161515649836725146279",
        "0.00011333136696344303286474027293141848604047270638207",
    ),
    "mb": (
        "cvqkd_mb_nu_0p200000_va2_c4_checkpoint.json",
        "1.4142135560377151402791686003423073594184222417457",
        "0.000000016265500905208522184947686319809889290461827831953",
    ),
}


def _forbidden(*_args, **_kwargs):
    raise RuntimeError("Beam search reached a forbidden AP/full-Z path.")


def _load_sources() -> tuple[dict[str, tuple[str, str]], dict[str, dict]]:
    sources = {}
    metadata = {}
    for scheme, (filename, expected_c, expected_w) in SOURCE_CHECKPOINTS.items():
        path = Path(tempfile.gettempdir()) / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        final = payload["rows"][-1]
        if (
            not final["resolved"]
            or Decimal(final["C"]) != Decimal(expected_c)
            or Decimal(final["w"]) != Decimal(expected_w)
        ):
            raise RuntimeError(f"Validated source checkpoint mismatch for {scheme}.")
        sources[scheme] = (expected_c, expected_w)
        metadata[scheme] = {
            "checkpoint": str(path),
            "accepted_precision_pair": [
                payload["rows"][-2]["digits"], payload["rows"][-1]["digits"]
            ],
            "C": expected_c,
            "w": expected_w,
        }
    return sources, metadata


def _scintillation_moment(power: float, v_sc: float) -> float:
    return math.exp((power**2 - power) * v_sc / 2.0)


def _channel(
    config: dict,
    link_m: float,
    theta_div_full_urad: float,
    *,
    aperture_radius_m: float = APERTURE_RADIUS_M,
    sigma_h_m: float = SIGMA_H_M,
    rho_m: float = RHO_M,
    sigma_hap_ang_rad: float = SIGMA_HAP_ANG_RAD,
    cn2_ground: float | None = CN2_GROUND,
) -> tuple[dict, dict, dict]:
    wavelength = float(config["channel"]["wavelength_m"])
    visibility = float(config["channel"]["visibility_km"])
    theta_div = theta_div_full_urad * 1.0e-6
    zenith_angle_rad = zenith_angle_rad_for_link_length_m(link_m, H_UAV_M)
    eta_atm = atmospheric_transmittance(link_m, visibility, wavelength)
    physical = derive_physical_inputs(
        h_uav_m_override=H_UAV_M,
        zenith_angle_rad_override=zenith_angle_rad,
        eta_atm_override=eta_atm,
        beam_waist_m_override=2.0 * wavelength / (math.pi * theta_div),
        theta_div_rad_override=theta_div,
        aperture_radius_m_override=aperture_radius_m,
        sigma_h_m_override=sigma_h_m,
        sigma_hap_ang_rad_override=sigma_hap_ang_rad,
        cn2_ground_m_minus_two_thirds_override=cn2_ground,
        rho_m_override=rho_m,
    )
    analysis = analyze_product(physical["v_sc"], physical)
    phase_config = config["channel"]["phase_noise"]
    phase = phase_parameter_provenance(
        phase_config["cn2_phase_m_minus_two_thirds"],
        physical["wavelength_m"],
        physical["link_length_m"],
    )
    moments = analysis["moments"]
    security = physical_channel_parameters(
        moments["mean_sqrt_eta"],
        float(physical["epsilon_base_snu"]),
        phase["c_phi"],
        VA,
    )
    return physical, phase, {
        "analysis": analysis,
        "security": security,
    }


def _channel_row(theta_div_full_urad: float, L_km: float, physical: dict, phase: dict, channel: dict) -> dict:
    moments = channel["analysis"]["moments"]
    security = channel["security"]
    v_sc = physical["v_sc"]
    mean_eta = moments["mean_eta"]
    transmittance = security["T"]
    epsilon = security["epsilon"]
    e_hp = _untruncated_moment(1.0, v_sc, physical) / physical["eta_atm"]
    e_sqrt_hp = _untruncated_moment(0.5, v_sc, physical) / (
        physical["eta_atm"] ** 0.5 * _scintillation_moment(0.5, v_sc)
    )
    if not (
        physical["eta_atm"] > 0.0
        and physical["pointing"]["eta_p0"] > 0.0
        and physical["sigma_m"] > 0.0
        and channel["analysis"]["quadrature"]["F_X_1"] > 0.0
    ):
        raise RuntimeError("Active transmittance positivity check failed.")
    return {
        "theta_div_full_urad": theta_div_full_urad,
        "theta_div_full_rad": theta_div_full_urad * 1.0e-6,
        "L_km": L_km,
        "zenith_angle_rad": physical["zenith_angle_rad"],
        "h_HAP_m": physical["h_hap_m"],
        "h_UAV_m": physical["h_uav_m"],
        "eta_atm": physical["eta_atm"],
        "w0_m": physical["pointing"]["omega_0_m"],
        "wL_m": physical["pointing"]["beam_radius_receiver_m"],
        "wL_eq_m": physical["pointing"]["omega_L_eq_m"],
        "rho_m": physical["rho_m"],
        "sigma_h_m": physical["sigma_h_m"],
        "L_theta_jt_m": physical["link_length_m"] * physical["sigma_hap_ang_rad"],
        "sigma_jt_m": physical["sigma_m"],
        "A0": physical["pointing"]["eta_p0"],
        "E_Hp": e_hp,
        "E_sqrt_Hp": e_sqrt_hp,
        "v_sc": v_sc,
        "mean_eta": mean_eta,
        "mean_sqrt_eta": moments["mean_sqrt_eta"],
        "T": transmittance,
        "epsilon_base": security["epsilon_base"],
        "xi_phase": security["xi_phase"],
        "epsilon": epsilon,
        "c_phi": phase["c_phi"],
        "tau_phi_squared": phase["tau_phi2"],
        "p_in": physical["p_in"],
        "p_out": physical["p_out"],
        "P_X_gt_1_raw": channel["analysis"]["quadrature"]["P_X_gt_1"],
        "active_T_support": "(0, 1]",
        "active_T_strictly_positive": True,
        "zero_T_source": "AoA outage only",
    }


def _evaluate_scheme(
    ensemble,
    source: tuple[str, str],
    security: dict,
    noises: dict[int, torch.Tensor],
    scheme: str,
    theta_div_full_urad: float,
    L_km: float,
) -> dict:
    t = torch.tensor([security["T"]], dtype=torch.float64)
    epsilon = torch.tensor([security["epsilon"]], dtype=torch.float64)
    c = torch.tensor([float(source[0])], dtype=torch.float64)
    w = torch.tensor([float(source[1])], dtype=torch.float64)
    mi_values = [
        float(
            discrete_mutual_information(
                ensemble,
                t,
                epsilon,
                noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
                standard_noise_samples=noises[seed],
            )[0]
        )
        for seed in MI_SEEDS
    ]
    mi = sum(mi_values) / len(mi_values)
    holevo = _holevo_from_source_moments(
        ensemble,
        t,
        epsilon,
        coherent_correlation=c,
        w_raw=w,
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=1.0e-8,
        physicality_tolerance=1.0e-10,
        maximize_full_interval=False,
        diagnostics={
            "backend": "optimistic_hapuav_beam_search",
            "source_moment_recomputed": False,
            "phase_noise_already_in_epsilon": True,
        },
    )
    chi = float(holevo.chi_be[0])
    return {
        "theta_div_full_urad": theta_div_full_urad,
        "L_km": L_km,
        "scheme": scheme,
        "C": source[0],
        "w": source[1],
        "I_AB": mi,
        "beta_I_AB": BETA * mi,
        "Z_star": float(holevo.z[0]),
        "chi_BE": chi,
        "K_raw": BETA * mi - chi,
        "physicality_pass": min(
            float(holevo.covariance.lambda1[0]),
            float(holevo.covariance.lambda2[0]),
            float(holevo.covariance.lambda3[0]),
        ) >= 1.0 - 1.0e-10,
        "holevo_mode": holevo.diagnostics["mode"],
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _json_default(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    raise TypeError(type(value).__name__)


def _reference_case(
    config: dict,
    sources: dict[str, tuple[str, str]],
    ensembles: dict,
    noises: dict[int, torch.Tensor],
    *,
    name: str,
    theta_div_full_urad: float,
    aperture_radius_m: float,
    sigma_h_m: float,
    rho_m: float,
    sigma_hap_ang_rad: float,
    cn2_ground: float | None,
) -> dict:
    physical, phase, channel = _channel(
        config,
        19000.0,
        theta_div_full_urad,
        aperture_radius_m=aperture_radius_m,
        sigma_h_m=sigma_h_m,
        rho_m=rho_m,
        sigma_hap_ang_rad=sigma_hap_ang_rad,
        cn2_ground=cn2_ground,
    )
    channel_row = _channel_row(theta_div_full_urad, 19.0, physical, phase, channel)
    security = [
        _evaluate_scheme(
            ensembles[scheme], sources[scheme], channel["security"], noises,
            scheme, theta_div_full_urad, 19.0,
        )
        for scheme in SCHEMES
    ]
    return {"name": name, "channel": channel_row, "security": security}


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    output_dir = ROOT / "results" / "optimistic_hapuav_beam_search"
    output_dir.mkdir(parents=True, exist_ok=True)
    sources, source_metadata = _load_sources()
    ensembles = {
        scheme: reference_ensemble(
            scheme,
            batch_size=1,
            modulation_variance=VA,
            nu_mb=NU_MB if scheme == "mb" else None,
            v_min=float(config["cvqkd"]["v_min_snu"]),
            v_max=float(config["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
        )
        for scheme in SCHEMES
    }
    noises = {
        seed: standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }
    channel_rows = []
    security_rows = []
    original_maximizer = holevo_module._maximize_bounded_scalar
    holevo_module._maximize_bounded_scalar = _forbidden
    try:
        for theta_div_full_urad in THETA_DIV_FULL_URAD:
            for L_km in L_KM:
                physical, phase, channel = _channel(
                    config, L_km * 1000.0, theta_div_full_urad
                )
                channel_rows.append(
                    _channel_row(theta_div_full_urad, L_km, physical, phase, channel)
                )
                for scheme in SCHEMES:
                    security_rows.append(
                        _evaluate_scheme(
                            ensembles[scheme], sources[scheme], channel["security"],
                            noises, scheme, theta_div_full_urad, L_km,
                        )
                    )
    finally:
        holevo_module._maximize_bounded_scalar = original_maximizer

    summaries = []
    for theta in THETA_DIV_FULL_URAD:
        channels = [row for row in channel_rows if row["theta_div_full_urad"] == theta]
        security = [row for row in security_rows if row["theta_div_full_urad"] == theta]
        by_scheme = {
            scheme: [row["K_raw"] for row in security if row["scheme"] == scheme]
            for scheme in SCHEMES
        }
        summaries.append({
            "theta_div_full_urad": theta,
            "min_T": min(row["T"] for row in channels),
            "mean_T": sum(row["T"] for row in channels) / len(channels),
            "max_T": max(row["T"] for row in channels),
            "min_epsilon": min(row["epsilon"] for row in channels),
            "max_epsilon": max(row["epsilon"] for row in channels),
            "min_K_Uniform": min(by_scheme["uniform"]),
            "min_K_Binomial": min(by_scheme["binomial"]),
            "min_K_MB": min(by_scheme["mb"]),
            "min_K_raw": min(row["K_raw"] for row in security),
            "positive_rows": sum(row["K_raw"] > 0.0 for row in security),
            "positive_rows_total": len(security),
            "T_19_km": next(row["T"] for row in channels if row["L_km"] == 19.0),
            "T_24_km": next(row["T"] for row in channels if row["L_km"] == 24.0),
            "epsilon_19_km": next(row["epsilon"] for row in channels if row["L_km"] == 19.0),
            "epsilon_24_km": next(row["epsilon"] for row in channels if row["L_km"] == 24.0),
        })

    by_t = sorted(summaries, key=lambda row: row["min_T"], reverse=True)
    by_k = sorted(summaries, key=lambda row: row["min_K_raw"], reverse=True)
    theta_t_star = by_t[0]["theta_div_full_urad"]
    theta_tmean_star = max(summaries, key=lambda row: row["mean_T"])["theta_div_full_urad"]
    theta_k_star = by_k[0]["theta_div_full_urad"]
    reference = {
        "old_baseline_223urad": _reference_case(
            config, sources, ensembles, noises,
            name="old baseline",
            theta_div_full_urad=223.0,
            aperture_radius_m=0.04,
            sigma_h_m=1.0,
            rho_m=0.0,
            sigma_hap_ang_rad=15.61e-6,
            cn2_ground=None,
        ),
        "previous_overoptimistic_33urad": _reference_case(
            config, sources, ensembles, noises,
            name="previous over-optimistic case",
            theta_div_full_urad=33.0,
            aperture_radius_m=0.10,
            sigma_h_m=0.10,
            rho_m=0.0,
            sigma_hap_ang_rad=1.0e-6,
            cn2_ground=None,
        ),
        "corrected_weak_pe_theta_T_star": _reference_case(
            config, sources, ensembles, noises,
            name="corrected weak-PE case at theta_T_star",
            theta_div_full_urad=float(theta_t_star),
            aperture_radius_m=APERTURE_RADIUS_M,
            sigma_h_m=SIGMA_H_M,
            rho_m=RHO_M,
            sigma_hap_ang_rad=SIGMA_HAP_ANG_RAD,
            cn2_ground=CN2_GROUND,
        ),
    }
    payload = {
        "artifact": "OPTIMISTIC_WEAK_PE_HAP_UAV_BEAM_DIVERGENCE_SEARCH_VA2",
        "status": "DIAGNOSTIC_ONLY",
        "scenario": {
            "VA": VA,
            "beta_rec": BETA,
            "nu_MB": NU_MB,
            "h_UAV_m": H_UAV_M,
            "h_HAP_m": HAP_ALTITUDE_M,
            "geometry_rule": "L_m = (20000 - h_UAV_m) / cos(zenith_angle_rad)",
            "wavelength_nm": 1550,
            "visibility_km": 200.0,
            "kruse_beer_lambert": True,
            "theta_div_full_urad": list(THETA_DIV_FULL_URAD),
            "rho_m": RHO_M,
            "sigma_h_m": SIGMA_H_M,
            "sigma_hap_ang_rad": SIGMA_HAP_ANG_RAD,
            "receiver_aperture_radius_m": APERTURE_RADIUS_M,
            "cn2_ground_m_minus_two_thirds": CN2_GROUND,
            "wind_m_per_s": float(config["channel"]["turbulence_profile"]["wind_speed_m_per_s"]),
        },
        "source_moments_recomputed": False,
        "ap_worker_invoked": False,
        "full_z_optimization_invoked": False,
        "active_T_claim": "T_raw>0 for active states; T=0 only for AoA outage; active physical support is (0,1]",
        "source_moments": source_metadata,
        "channel_rows": channel_rows,
        "security_rows": security_rows,
        "summary_by_theta_sorted_min_T": by_t,
        "summary_by_theta_sorted_min_K": by_k,
        "theta_T_star_full_urad": theta_t_star,
        "theta_Tmean_star_full_urad": theta_tmean_star,
        "theta_K_star_full_urad": theta_k_star,
        "reference_cases_L19": reference,
        "runtime_seconds": time.perf_counter() - started,
    }
    (output_dir / "optimistic_hapuav_beam_search.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False, default=_json_default) + "\n",
        encoding="utf-8",
    )
    _write_csv(output_dir / "channel_rows.csv", channel_rows)
    _write_csv(output_dir / "security_rows.csv", security_rows)
    _write_csv(output_dir / "summary_by_theta_min_T.csv", by_t)
    _write_csv(output_dir / "summary_by_theta_min_K.csv", by_k)
    print(json.dumps({
        "runtime_seconds": payload["runtime_seconds"],
        "channel_rows": len(channel_rows),
        "security_rows": len(security_rows),
        "theta_T_star_full_urad": theta_t_star,
        "theta_Tmean_star_full_urad": theta_tmean_star,
        "theta_K_star_full_urad": theta_k_star,
        "positive_rows_total": sum(row["K_raw"] > 0.0 for row in security_rows),
        "output_dir": str(output_dir),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
