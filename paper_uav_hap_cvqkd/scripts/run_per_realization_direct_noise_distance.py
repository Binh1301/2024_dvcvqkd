"""Per-realization direct-noise distance diagnostic using cached C,w moments."""

from __future__ import annotations

import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import tempfile
import time
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from src.channel.atmospheric_loss import atmospheric_transmittance
from src.channel.geometry import HAP_ALTITUDE_M, LinkGeometry, zenith_angle_rad_for_link_length_m
from src.channel.phase_noise import phase_excess_noise, phase_parameter_provenance, total_excess_noise
from src.channel.turbulence import UavMotion
from src.channel.fso_channel import sample_fso_channel
from src.cvqkd.holevo import _holevo_from_source_moments
import src.cvqkd.holevo as holevo_module
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.utils.random import torch_generator


VA = 2.0
BETA = 0.95
FADING_SAMPLES = 16
MI_SAMPLES_PER_SYMBOL = 64
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
CHANNEL_SEED_BASE = 202613
THETA_DIV_FULL_URAD = 50.0
APERTURE_RADIUS_M = 0.10
SIGMA_H_M = 0.20
RHO_M = math.hypot(0.30, 0.20)
SIGMA_HAP_ANG_RAD = 1.0e-6
CN2_GROUND = 5.0e-14
L_KM = tuple(19.0 + 0.5 * index for index in range(11))
MB_NUS = (0.02, 0.05, 0.075, 0.0875, 0.090625, 0.09375, 0.10, 0.125, 0.15, 0.20)
SOURCE_FILES = {
    "uniform": "cvqkd_uniform_va2_c4_checkpoint.json",
    "binomial": "cvqkd_binomial_va2_c4_checkpoint.json",
    "mb_0.02": "cvqkd_mb_nu_0p020000_va2_c4_checkpoint.json",
    "mb_0.05": "cvqkd_mb_nu_0p050000_va2_c4_checkpoint.json",
    "mb_0.075": "cvqkd_mb_nu_0p075000_va2_c4_checkpoint.json",
    "mb_0.0875": "cvqkd_mb_nu_0p087500_va2_c4_checkpoint.json",
    "mb_0.090625": "cvqkd_mb_nu_0p090625_va2_c4_checkpoint.json",
    "mb_0.09375": "cvqkd_mb_nu_0p093750_va2_c4_checkpoint.json",
    "mb_0.1": "cvqkd_fixed_mb_va2_c4_checkpoint.json",
    "mb_0.125": "cvqkd_mb_nu_0p125000_va2_c4_checkpoint.json",
    "mb_0.15": "cvqkd_mb_nu_0p150000_va2_c4_checkpoint.json",
    "mb_0.2": "cvqkd_mb_nu_0p200000_va2_c4_checkpoint.json",
}


def _load_sources() -> tuple[dict[str, tuple[str, str]], dict[str, dict]]:
    sources = {}
    metadata = {}
    for scheme, filename in SOURCE_FILES.items():
        path = Path(tempfile.gettempdir()) / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        final = payload["rows"][-1]
        if not final.get("resolved"):
            raise RuntimeError(f"Unresolved source checkpoint: {path}")
        sources[scheme] = (final["C"], final["w"])
        metadata[scheme] = {
            "checkpoint": str(path),
            "accepted_precision_pair": [payload["rows"][-2]["digits"], final["digits"]],
            "C": final["C"],
            "w": final["w"],
        }
    return sources, metadata


def _ensemble(config: dict, scheme: str, sample_count: int, nu: float | None):
    return reference_ensemble(
        "mb" if scheme.startswith("mb_") else scheme,
        batch_size=sample_count,
        modulation_variance=VA,
        nu_mb=nu,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )


def _sample_channel(config: dict, L_km: float, seed: int):
    channel = config["channel"]
    wavelength_m = float(channel["wavelength_m"])
    h_uav_m = float(channel["h_uav_m"])
    link_m = L_km * 1000.0
    zenith_angle_rad = zenith_angle_rad_for_link_length_m(link_m, h_uav_m)
    eta_atm = atmospheric_transmittance(
        link_m, float(channel["visibility_km"]), wavelength_m
    )
    geometry = LinkGeometry(HAP_ALTITUDE_M, h_uav_m, zenith_angle_rad)
    return sample_fso_channel(
        geometry=geometry,
        wavelength_m=wavelength_m,
        visibility_km=float(channel["visibility_km"]),
        beam_waist_m=2.0 * wavelength_m / (math.pi * THETA_DIV_FULL_URAD * 1.0e-6),
        aperture_radius_m=APERTURE_RADIUS_M,
        cn2_m_minus_two_thirds=float(channel["cn2_m_minus_two_thirds"]),
        sample_count=FADING_SAMPLES,
        rng=np.random.default_rng(seed),
        uav_motion=UavMotion(**channel["uav_motion"]),
        scintillation_log_variance=None,
        v_sc_override=None,
        aperture_averaging_model="hufnagel_valley_finite_aperture",
        turbulence_profile_model="hufnagel_valley",
        wind_speed_m_per_s=float(channel["turbulence_profile"]["wind_speed_m_per_s"]),
        ground_cn2_m_minus_two_thirds=CN2_GROUND,
        eta_atm=eta_atm,
        theta_div_rad=THETA_DIV_FULL_URAD * 1.0e-6,
        f0_m=float(channel["f0_m"]),
        sigma_h_m=SIGMA_H_M,
        boresight_x_m=RHO_M,
        boresight_y_m=0.0,
        sigma_hap_ang_rad=SIGMA_HAP_ANG_RAD,
        hap_angular_jitter_convention=channel["pointing"]["hap_angular_jitter_convention"],
        aoa_model=channel["aoa"]["model"],
        sigma_turb_AoA2=float(channel["aoa"]["sigma_turb_AoA2_rad2"]),
        turbulence_aoa_provenance=channel["aoa"]["provenance"],
        sigma_o_rad=float(channel["aoa"]["sigma_o_rad"]),
        theta_fov_rad=float(channel["aoa"]["theta_fov_rad"]),
    )


def _evaluate_distance(config, sources, ensembles, noises, phase, epsilon, L_km, seed):
    states = _sample_channel(config, L_km, seed)
    t_all = torch.as_tensor(states.transmittance, dtype=torch.float64)
    active = t_all > 0.0
    active_t = t_all[active]
    outage_rate = float((~active).double().mean())
    channel_rows = []
    rows = []
    for scheme, source in sources.items():
        i_full = torch.zeros_like(t_all)
        chi_full = torch.zeros_like(t_all)
        k_full = torch.zeros_like(t_all)
        if bool(torch.any(active)):
            n_active = int(active.sum())
            ensemble = _ensemble(
                config,
                scheme,
                n_active,
                float(scheme[3:]) if scheme.startswith("mb_") else None,
            )
            t = active_t
            eps = torch.full_like(t, epsilon)
            c = torch.full((n_active,), float(source[0]), dtype=torch.float64)
            w = torch.full((n_active,), float(source[1]), dtype=torch.float64)
            mi_reps = []
            for seed_i in MI_SEEDS:
                mi_reps.append(discrete_mutual_information(
                    ensemble,
                    t,
                    eps,
                    noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
                    standard_noise_samples=noises[seed_i][:n_active],
                ))
            mi_active = torch.stack(mi_reps).mean(dim=0)
            holevo = _holevo_from_source_moments(
                ensemble,
                t,
                eps,
                coherent_correlation=c,
                w_raw=w,
                tau=None,
                tau_trace=ensemble.probabilities.sum(dim=-1),
                require_supported_symmetry=True,
                symmetry_tolerance=1.0e-8,
                physicality_tolerance=1.0e-10,
                maximize_full_interval=False,
                diagnostics={
                    "backend": "per_realization_direct_noise_distance",
                    "T_is_per_realization_eta": True,
                    "effective_excess_noise_used": False,
                },
            )
            chi_active = holevo.chi_be
            k_active = BETA * mi_active - chi_active
            i_full[active] = mi_active
            chi_full[active] = chi_active
            k_full[active] = k_active
        rows.append({
            "L_km": L_km,
            "modulation": "Uniform" if scheme == "uniform" else "Binomial" if scheme == "binomial" else "MB",
            "nu_MB": None if not scheme.startswith("mb_") else float(scheme[3:]),
            "number_of_samples": FADING_SAMPLES,
            "outage_rate": outage_rate,
            "mean_eta": float(t_all.mean()),
            "mean_sqrt_eta": float(torch.sqrt(t_all).mean()),
            "epsilon": epsilon,
            "mean_I_AB": float(i_full.mean()),
            "mean_chi_BE": float(chi_full.mean()),
            "K_raw_bar": float(k_full.mean()),
            "K_raw_min": float(k_full.min()),
            "K_raw_max": float(k_full.max()),
            "physicality_pass": True,
            "source_C": source[0],
            "source_w": source[1],
        })
    channel_rows.append({
        "L_km": L_km,
        "number_of_samples": FADING_SAMPLES,
        "outage_rate": outage_rate,
        "mean_eta": float(t_all.mean()),
        "mean_sqrt_eta": float(torch.sqrt(t_all).mean()),
        "eta_min": float(t_all.min()),
        "eta_max": float(t_all.max()),
    })
    return channel_rows, rows


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    output_dir = ROOT / "results" / "per_realization_direct_noise_va2"
    output_dir.mkdir(parents=True, exist_ok=True)
    sources, source_metadata = _load_sources()
    epsilon_base = float(config["channel"]["excess_noise_distribution"]["value_snu"])
    noises = {
        seed: standard_complex_noise(
            (FADING_SAMPLES, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }
    original_maximizer = holevo_module._maximize_bounded_scalar
    holevo_module._maximize_bounded_scalar = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        RuntimeError("Per-realization diagnostic reached forbidden full-Z path.")
    )
    channel_rows = []
    rows = []
    try:
        for index, L_km in enumerate(L_KM, start=1):
            phase_config = config["channel"]["phase_noise"]
            h_uav_m = float(config["channel"]["h_uav_m"])
            link_m = L_km * 1000.0
            zenith_angle_rad = zenith_angle_rad_for_link_length_m(link_m, h_uav_m)
            phase = phase_parameter_provenance(
                phase_config["cn2_phase_m_minus_two_thirds"],
                config["channel"]["wavelength_m"],
                LinkGeometry(HAP_ALTITUDE_M, h_uav_m, zenith_angle_rad).link_length_m,
                mapping_status=phase_config.get("mapping_status", "configured"),
                author_approved=phase_config.get("author_approved", False),
            )
            xi_phase = float(phase_excess_noise(VA, phase["c_phi"]))
            epsilon = float(total_excess_noise(epsilon_base, VA, phase["c_phi"]))
            channel_part, row_part = _evaluate_distance(
                config, sources, None, noises, phase, epsilon, L_km,
                CHANNEL_SEED_BASE + index,
            )
            channel_rows.extend(channel_part)
            rows.extend(row_part)
            print(f"completed L={L_km:.1f} km ({index}/{len(L_KM)})", flush=True)
    finally:
        holevo_module._maximize_bounded_scalar = original_maximizer
    payload = {
        "artifact": "PER_REALIZATION_DIRECT_NOISE_DISTANCE_VA2",
        "status": "DIAGNOSTIC_ONLY",
        "scenario": {
            "VA": VA,
            "beta_rec": BETA,
            "fading_samples_per_distance": FADING_SAMPLES,
            "mi_samples_per_symbol": MI_SAMPLES_PER_SYMBOL,
            "mi_seeds": list(MI_SEEDS),
            "channel_seed_base": CHANNEL_SEED_BASE,
            "theta_div_full_urad": THETA_DIV_FULL_URAD,
            "aperture_radius_m": APERTURE_RADIUS_M,
            "sigma_h_m": SIGMA_H_M,
            "rho_m": RHO_M,
            "sigma_hap_ang_rad": SIGMA_HAP_ANG_RAD,
            "cn2_ground_m_minus_two_thirds": CN2_GROUND,
            "epsilon_base": epsilon_base,
            "cn2_phase_m_minus_two_thirds": phase["cn2_phase_m_minus_two_thirds"],
            "phase_distance_rule": "link_distance_m = (20000 - h_UAV_m) / cos(zenith_angle_rad)",
            "security_model": "T_n=eta_n; per-realization K_raw averaged afterward",
        },
        "source_moments_recomputed": False,
        "ap_worker_invoked": False,
        "full_z_optimization_invoked": False,
        "phase_provenance": phase,
        "source_moments": source_metadata,
        "channel_rows": channel_rows,
        "rows": rows,
        "runtime_seconds": time.perf_counter() - started,
    }
    (output_dir / "per_realization_direct_noise_va2.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    with (output_dir / "per_realization_direct_noise_va2.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "rows": len(rows),
        "channel_rows": len(channel_rows),
        "output_dir": str(output_dir),
        "runtime_seconds": payload["runtime_seconds"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
