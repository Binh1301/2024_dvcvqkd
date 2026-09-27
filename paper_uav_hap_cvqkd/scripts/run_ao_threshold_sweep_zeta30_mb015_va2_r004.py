"""Sweep AO efficiency for fixed MB=0.15, V_A=2, zeta=30 deg, r_ap=0.04 m."""

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
    VA,
    ZETA_DEG,
    _evaluate_mb,
    _load_source,
    _make_ensemble,
)
from scripts.run_mb_skr_sweep_zeta30_va2_ao09 import _finite_physical
from src.channel.geometry import LinkGeometry
from src.channel.phase_noise import (
    phase_distortion_variance,
    phase_noise_coefficient,
)


MB_NU = 0.15
APERTURE_RADIUS_M = 0.04
AO_VALUES = (0.95, 0.96, 0.97, 0.98, 0.99)
OUTPUT_DIR = ROOT / "results" / "ao_threshold_sweep_zeta30_mb015_va2_r004"
AO095_CSV = ROOT / "results" / "mb_skr_sweep_zeta30_va2_ao095_aperture_r004" / "mb_skr_sweep_ao095_aperture_r004.csv"
CSV_FIELDS = (
    "eta_ao", "point_kind", "status", "error", "mb_parameter", "va_snu",
    "zeta_deg", "aperture_radius_m", "aperture_diameter_m", "link_distance_m",
    "cn2_phase_m_minus_two_thirds", "wavelength_m", "tau_phi_raw_squared",
    "tau_phi_ao_squared", "xi_phase", "epsilon_base", "epsilon_total",
    "mean_transmittance", "effective_transmittance", "aoa_outage_probability",
    "I_AB", "I_AB_stderr", "chi_BE", "beta_I_AB", "raw_SKR",
    "delta_I_AB_vs_eta095", "delta_chi_BE_vs_eta095", "delta_SKR_vs_eta095",
    "physical_energy_VA", "peak_photons", "pmf_normalization",
    "minimum_symplectic_lambda", "non_physical", "source_rank", "source_checkpoint",
    "holevo_mode",
)


def _prior_ao095() -> dict[str, float] | None:
    if not AO095_CSV.is_file():
        return None
    with AO095_CSV.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["status"] == "PASS" and math.isclose(float(row["mb_parameter"]), MB_NU):
                return {
                    "mean_transmittance": float(row["mean_transmittance"]),
                    "effective_transmittance": float(row["effective_transmittance"]),
                }
    return None


def _evaluate_eta(
    eta_ao: float,
    *,
    config: dict,
    physical: dict,
    moments: dict,
    tau_raw: float,
    cn2_phase: float,
    numerical: dict[str, float],
    reference: dict[str, float] | None,
    point_kind: str,
) -> dict:
    tau_ao = (1.0 - eta_ao) * tau_raw
    c_phi_ao = phase_noise_coefficient(tau_ao)
    security = physical_channel_parameters(
        moments["mean_sqrt_eta"],
        float(physical["epsilon_base_snu"]),
        c_phi_ao,
        VA,
    )
    row = {
        "eta_ao": eta_ao,
        "point_kind": point_kind,
        "status": "FAILED",
        "error": None,
        "mb_parameter": MB_NU,
        "va_snu": VA,
        "zeta_deg": ZETA_DEG,
        "aperture_radius_m": physical["receiver_radius_m"],
        "aperture_diameter_m": physical["receiver_diameter_m"],
        "link_distance_m": physical["link_length_m"],
        "cn2_phase_m_minus_two_thirds": cn2_phase,
        "wavelength_m": physical["wavelength_m"],
        "tau_phi_raw_squared": tau_raw,
        "tau_phi_ao_squared": tau_ao,
        "xi_phase": security["xi_phase"],
        "epsilon_base": security["epsilon_base"],
        "epsilon_total": security["epsilon"],
        "mean_transmittance": moments["mean_eta"],
        "effective_transmittance": security["T"],
        "aoa_outage_probability": physical["p_out"],
        "holevo_mode": "zstar",
    }
    try:
        _finite_physical(tau_ao, "tau_phi_ao_squared")
        _finite_physical(security["epsilon"], "epsilon_total")
        ensemble = _make_ensemble(config, MB_NU)
        result = _evaluate_mb(
            config,
            ensemble,
            _load_source(ensemble, MB_NU),
            security["T"],
            security["epsilon"],
            numerical,
            MB_NU,
        )
        row.update({
            **result,
            "beta_I_AB": float(config["cvqkd"]["beta_reconciliation"]) * result["I_AB"],
            "raw_SKR": result["SKR"],
            "peak_photons": float(ensemble.amplitudes.abs().square().amax()),
            "holevo_mode": "zstar",
        })
        if reference is not None:
            row.update({
                "delta_I_AB_vs_eta095": row["I_AB"] - reference["I_AB"],
                "delta_chi_BE_vs_eta095": row["chi_BE"] - reference["chi_BE"],
                "delta_SKR_vs_eta095": row["raw_SKR"] - reference["raw_SKR"],
            })
    except Exception as error:
        row["error"] = f"{type(error).__name__}: {error}"
    return row


def _crossing(rows: list[dict]) -> dict[str, float] | None:
    passed = sorted((row for row in rows if row["status"] == "PASS"), key=lambda row: row["eta_ao"])
    for left, right in zip(passed, passed[1:]):
        if left["raw_SKR"] < 0.0 < right["raw_SKR"]:
            estimate = left["eta_ao"] + (
                -left["raw_SKR"] / (right["raw_SKR"] - left["raw_SKR"])
            ) * (right["eta_ao"] - left["eta_ao"])
            return {"eta_left": left["eta_ao"], "K_left": left["raw_SKR"], "eta_right": right["eta_ao"], "K_right": right["raw_SKR"], "linear_eta_estimate": estimate}
    return None


def main() -> int:
    config = load_yaml(ROOT / "configs" / "default.yaml")
    zeta_rad = math.radians(ZETA_DEG)
    geometry = LinkGeometry(
        float(config["channel"]["h_hap_m"]),
        float(config["channel"]["h_uav_m"]),
        zeta_rad,
    )
    physical = derive_physical_inputs(
        zenith_angle_rad_override=zeta_rad,
        aperture_radius_m_override=APERTURE_RADIUS_M,
    )
    if not math.isclose(physical["link_length_m"], geometry.link_length_m, rel_tol=0.0, abs_tol=1.0e-9):
        raise RuntimeError("The requested zeta was not propagated into link geometry.")
    if physical["receiver_radius_m"] != APERTURE_RADIUS_M:
        raise RuntimeError("The receiver-aperture override was not retained by the channel.")
    phase_config = config["channel"]["phase_noise"]
    cn2_phase = float(phase_config["cn2_phase_m_minus_two_thirds"])
    tau_raw = phase_distortion_variance(cn2_phase, physical["wavelength_m"], physical["link_length_m"])
    analysis = analyze_product(physical["v_sc"], physical)
    moments = analysis["moments"]
    _finite_physical(moments["mean_eta"], "mean_transmittance", upper=1.0)
    prior = _prior_ao095()
    if prior is not None:
        if not math.isclose(moments["mean_eta"], prior["mean_transmittance"], rel_tol=0.0, abs_tol=1.0e-15):
            raise RuntimeError("Matched AO runs produced different mean transmittance.")
        expected_t = float(moments["mean_sqrt_eta"]) ** 2
        if not math.isclose(expected_t, prior["effective_transmittance"], rel_tol=0.0, abs_tol=1.0e-15):
            raise RuntimeError("Matched AO runs produced different effective transmittance.")

    preflight = {
        "zeta_deg": ZETA_DEG,
        "link_distance_m": physical["link_length_m"],
        "MB": MB_NU,
        "VA": VA,
        "aperture_radius_m": physical["receiver_radius_m"],
        "aperture_diameter_m": physical["receiver_diameter_m"],
        "cn2_phase_m_minus_two_thirds": cn2_phase,
        "wavelength_m": physical["wavelength_m"],
        "tau_phi_raw_squared": tau_raw,
        "epsilon_base": physical["epsilon_base_snu"],
        "mean_transmittance": moments["mean_eta"],
        "effective_transmittance": float(moments["mean_sqrt_eta"]) ** 2,
        "aoa_outage_probability": physical["p_out"],
    }
    print(json.dumps({"ao_threshold_preflight": preflight}, indent=2), flush=True)

    numerical = holevo_numerical_kwargs(config)
    rows = []
    reference = None
    for eta_ao in AO_VALUES:
        row = _evaluate_eta(
            eta_ao,
            config=config,
            physical=physical,
            moments=moments,
            tau_raw=tau_raw,
            cn2_phase=cn2_phase,
            numerical=numerical,
            reference=reference,
            point_kind="requested_grid",
        )
        rows.append(row)
        if eta_ao == AO_VALUES[0] and row["status"] == "PASS":
            reference = row
            row.update({
                "delta_I_AB_vs_eta095": 0.0,
                "delta_chi_BE_vs_eta095": 0.0,
                "delta_SKR_vs_eta095": 0.0,
            })
    if reference is None:
        raise RuntimeError("The eta_AO=0.95 reference point failed.")
    if any(right["tau_phi_ao_squared"] >= left["tau_phi_ao_squared"] for left, right in zip(rows, rows[1:])):
        raise RuntimeError("AO phase variance did not decrease monotonically.")
    if any(right["xi_phase"] >= left["xi_phase"] for left, right in zip(rows, rows[1:])):
        raise RuntimeError("AO phase excess noise did not decrease monotonically.")
    if any(right["epsilon_total"] >= left["epsilon_total"] for left, right in zip(rows, rows[1:])):
        raise RuntimeError("AO total excess noise did not decrease monotonically.")

    crossing = _crossing(rows)
    if crossing is not None:
        estimate = crossing["linear_eta_estimate"]
        if all(not math.isclose(estimate, value, rel_tol=0.0, abs_tol=1.0e-12) for value in AO_VALUES):
            rows.append(_evaluate_eta(
                estimate,
                config=config,
                physical=physical,
                moments=moments,
                tau_raw=tau_raw,
                cn2_phase=cn2_phase,
                numerical=numerical,
                reference=reference,
                point_kind="linear_threshold_probe",
            ))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "ao_threshold_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    passed = [row for row in rows if row["status"] == "PASS"]
    if not passed:
        raise RuntimeError("No AO threshold point passed the physicality check.")
    figure_path = OUTPUT_DIR / "SKR_vs_eta_AO.png"
    requested = [row for row in rows if row["point_kind"] == "requested_grid" and row["status"] == "PASS"]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot([row["eta_ao"] for row in requested], [row["raw_SKR"] for row in requested], marker="o", linewidth=1.5)
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("AO efficiency")
    ax.set_ylabel("Raw SKR (bits/use)")
    ax.set_title("AO sensitivity: zeta = 30 deg, MB = 0.15, V_A = 2, r_ap = 0.04 m")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    print(json.dumps({
        "csv_path": str(csv_path.resolve()),
        "figure_path": str(figure_path.resolve()),
        "preflight": preflight,
        "zero_crossing_bracket": crossing,
        "pass_count": len(passed),
        "failed_points": [row for row in rows if row["status"] == "FAILED"],
        "non_physical_points": [row["eta_ao"] for row in rows if row["status"] == "NON_PHYSICAL"],
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
