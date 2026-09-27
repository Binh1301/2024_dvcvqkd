"""Evaluate the existing zeta=30 deg MB sweep with AO phase compensation."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    analyze_product,
    derive_physical_inputs,
)
from scripts.run_effective_channel_va2 import physical_channel_parameters
from scripts.run_mb_skr_sweep_zeta30_va2 import (
    MB_VALUES,
    VA,
    ZETA_DEG,
    _evaluate_mb,
    _load_source,
    _make_ensemble,
)
from src.channel.geometry import LinkGeometry
from src.channel.phase_noise import (
    phase_distortion_variance,
    phase_noise_coefficient,
)


ETA_AO = 0.9
OUTPUT_DIR = ROOT / "results" / "mb_skr_sweep_zeta30_va2_ao09"
PREVIOUS_CSV = ROOT / "results" / "mb_skr_sweep_zeta30_va2" / "mb_skr_sweep.csv"
CSV_FIELDS = (
    "mb_parameter", "status", "error", "zeta_deg", "zeta_rad", "h_HAP_m",
    "h_UAV_m", "link_distance_m", "va_snu", "eta_ao",
    "cn2_phase_m_minus_two_thirds", "wavelength_m", "tau_phi_raw_squared",
    "tau_phi_ao_squared", "c_phi_ao", "xi_phase", "epsilon_base",
    "mean_epsilon_total", "effective_total_excess_noise", "mean_transmittance",
    "mean_sqrt_transmittance", "effective_transmittance", "I_AB", "I_AB_stderr",
    "chi_BE", "raw_SKR", "delta_I_AB_from_no_ao", "delta_chi_BE_from_no_ao",
    "delta_SKR_from_no_ao", "physical_energy_VA", "pmf_normalization",
    "minimum_symplectic_lambda", "non_physical", "source_rank", "source_checkpoint",
    "holevo_mode",
)


def _previous_rows() -> dict[float, dict[str, float]]:
    if not PREVIOUS_CSV.is_file():
        return {}
    with PREVIOUS_CSV.open(newline="", encoding="utf-8") as stream:
        return {
            float(row["mb_parameter"]): {
                "I_AB": float(row["I_AB"]),
                "chi_BE": float(row["chi_BE"]),
                "SKR": float(row["SKR"]),
            }
            for row in csv.DictReader(stream)
            if row["status"] == "PASS"
        }


def _finite_physical(value: float, name: str, *, upper: float | None = None) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0.0 or (upper is not None and value > upper):
        raise ValueError(f"{name} must be finite and physical.")
    return value


def main() -> int:
    config = load_yaml(ROOT / "configs" / "default.yaml")
    zeta_rad = math.radians(ZETA_DEG)
    geometry = LinkGeometry(
        float(config["channel"]["h_hap_m"]),
        float(config["channel"]["h_uav_m"]),
        zeta_rad,
    )
    physical = derive_physical_inputs(zenith_angle_rad_override=zeta_rad)
    if not math.isclose(physical["link_length_m"], geometry.link_length_m, rel_tol=0.0, abs_tol=1.0e-9):
        raise RuntimeError("The requested zeta was not propagated into link geometry.")

    phase_config = config["channel"]["phase_noise"]
    cn2_phase = float(phase_config["cn2_phase_m_minus_two_thirds"])
    tau_raw = phase_distortion_variance(cn2_phase, physical["wavelength_m"], physical["link_length_m"])
    tau_ao = (1.0 - ETA_AO) * tau_raw
    c_phi_ao = phase_noise_coefficient(tau_ao)

    analysis = analyze_product(physical["v_sc"], physical)
    moments = analysis["moments"]
    security = physical_channel_parameters(
        moments["mean_sqrt_eta"],
        float(physical["epsilon_base_snu"]),
        c_phi_ao,
        VA,
    )
    _finite_physical(moments["mean_eta"], "mean_transmittance", upper=1.0)
    _finite_physical(security["T"], "effective_transmittance", upper=1.0)
    _finite_physical(security["epsilon"], "epsilon_total")
    preflight = {
        "zeta_deg": ZETA_DEG,
        "link_distance_m": physical["link_length_m"],
        "VA": VA,
        "eta_ao": ETA_AO,
        "cn2_phase_m_minus_two_thirds": cn2_phase,
        "wavelength_m": physical["wavelength_m"],
        "tau_phi_raw_squared": tau_raw,
        "tau_phi_ao_squared": tau_ao,
        "c_phi_ao": c_phi_ao,
        "xi_phase": security["xi_phase"],
        "epsilon_base": security["epsilon_base"],
        "epsilon_total": security["epsilon"],
        "mean_transmittance": moments["mean_eta"],
        "effective_transmittance": security["T"],
    }
    print(json.dumps({"phase_preflight": preflight}, indent=2), flush=True)

    previous = _previous_rows()
    numerical = holevo_numerical_kwargs(config)
    rows = []
    for nu_mb in MB_VALUES:
        row = {
            "mb_parameter": nu_mb,
            "status": "FAILED",
            "error": None,
            "zeta_deg": ZETA_DEG,
            "zeta_rad": zeta_rad,
            "h_HAP_m": physical["h_hap_m"],
            "h_UAV_m": physical["h_uav_m"],
            "link_distance_m": physical["link_length_m"],
            "va_snu": VA,
            "eta_ao": ETA_AO,
            "cn2_phase_m_minus_two_thirds": cn2_phase,
            "wavelength_m": physical["wavelength_m"],
            "tau_phi_raw_squared": tau_raw,
            "tau_phi_ao_squared": tau_ao,
            "c_phi_ao": c_phi_ao,
            "xi_phase": security["xi_phase"],
            "epsilon_base": security["epsilon_base"],
            "mean_epsilon_total": security["epsilon"],
            "effective_total_excess_noise": security["epsilon"],
            "mean_transmittance": moments["mean_eta"],
            "mean_sqrt_transmittance": moments["mean_sqrt_eta"],
            "effective_transmittance": security["T"],
            "holevo_mode": "zstar",
        }
        try:
            ensemble = _make_ensemble(config, nu_mb)
            result = _evaluate_mb(
                config,
                ensemble,
                _load_source(ensemble, nu_mb),
                security["T"],
                security["epsilon"],
                numerical,
                nu_mb,
            )
            row.update({
                **result,
                "raw_SKR": result["SKR"],
                "holevo_mode": "zstar",
            })
            prior = previous.get(nu_mb)
            if prior is not None:
                row.update({
                    "delta_I_AB_from_no_ao": row["I_AB"] - prior["I_AB"],
                    "delta_chi_BE_from_no_ao": row["chi_BE"] - prior["chi_BE"],
                    "delta_SKR_from_no_ao": row["raw_SKR"] - prior["SKR"],
                })
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "mb_skr_sweep_ao09.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    passed = [row for row in rows if row["status"] == "PASS"]
    if not passed:
        raise RuntimeError("No AO-compensated MB sweep point passed the physicality check.")
    best = max(passed, key=lambda row: float(row["raw_SKR"]))
    figure_path = OUTPUT_DIR / "SKR_vs_MB_AO09.png"
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(
        [row["mb_parameter"] for row in passed],
        [row["raw_SKR"] for row in passed],
        marker="o",
        linewidth=1.5,
    )
    ax.set_xlabel("Maxwell-Boltzmann parameter")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("SKR vs MB: zeta = 30 deg, V_A = 2, eta_AO = 0.9")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)

    previous_best = max(previous.items(), key=lambda item: item[1]["SKR"], default=None)
    print(json.dumps({
        "csv_path": str(csv_path.resolve()),
        "figure_path": str(figure_path.resolve()),
        "phase_preflight": preflight,
        "best_mb": best["mb_parameter"],
        "best_raw_SKR": best["raw_SKR"],
        "best_I_AB": best["I_AB"],
        "best_chi_BE": best["chi_BE"],
        "previous_best": None if previous_best is None else {
            "mb": previous_best[0], "SKR": previous_best[1]["SKR"],
        },
        "best_SKR_improvement": None if previous_best is None else best["raw_SKR"] - previous_best[1]["SKR"],
        "pass_count": len(passed),
        "failed_points": [row for row in rows if row["status"] == "FAILED"],
        "non_physical_points": [row["mb_parameter"] for row in rows if row["status"] == "NON_PHYSICAL"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
