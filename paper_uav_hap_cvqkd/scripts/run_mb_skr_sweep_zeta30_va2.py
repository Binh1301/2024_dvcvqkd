"""Evaluate the existing effective-channel SKR pipeline over MB at zeta=30 deg."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import (
    analyze_product,
    derive_physical_inputs,
)
from scripts.run_effective_channel_va2 import (
    MI_SAMPLES_PER_SYMBOL,
    MI_SEEDS,
    physical_channel_parameters,
)
from src.channel.geometry import LinkGeometry
from src.channel.phase_noise import phase_parameter_provenance
from src.cvqkd.gram_moments import _hash_payload, _hex
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import (
    discrete_mutual_information,
    standard_complex_noise,
)
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import reference_ensemble
from src.modulation.qam256 import c4_orbit_indices
from src.utils.random import torch_generator


VA = 2.0
ZETA_DEG = 30.0
MB_VALUES = (0.05, 0.075, 0.10, 0.125, 0.15, 0.20)
SOURCE_FILES = {
    0.05: "cvqkd_mb_nu_0p050000_va2_c4_checkpoint.json",
    0.075: "cvqkd_mb_nu_0p075000_va2_c4_checkpoint.json",
    0.10: "cvqkd_fixed_mb_va2_c4_checkpoint.json",
    0.125: "cvqkd_mb_nu_0p125000_va2_c4_checkpoint.json",
    0.15: "cvqkd_mb_nu_0p150000_va2_c4_checkpoint.json",
    0.20: "cvqkd_mb_nu_0p200000_va2_c4_checkpoint.json",
}
OUTPUT_DIR = ROOT / "results" / "mb_skr_sweep_zeta30_va2"


def _load_source(ensemble, nu_mb: float) -> dict:
    path = Path(tempfile.gettempdir()) / SOURCE_FILES[nu_mb]
    payload = json.loads(path.read_text(encoding="utf-8"))
    final = payload["rows"][-1]
    if final.get("resolved") is not True or final.get("rank") != 256:
        raise RuntimeError(f"Unresolved full-support source checkpoint: {path}")
    expected = payload.get("input_hashes", {})
    representatives = c4_orbit_indices(device=ensemble.probabilities.device)[:, 0]
    probabilities_hex = [
        _hex(x) for x in ensemble.probabilities[0, representatives].detach().tolist()
    ]
    amplitudes_hex = [
        [_hex(complex(x).real), _hex(complex(x).imag)]
        for x in ensemble.amplitudes[0, representatives].detach().tolist()
    ]
    actual_pmf = _hash_payload(probabilities_hex)
    actual_amplitudes = _hash_payload(amplitudes_hex)
    if expected.get("pmf_sha256") != actual_pmf or expected.get("amplitude_sha256") != actual_amplitudes:
        raise RuntimeError(f"Source checkpoint input hash mismatch: {path}")
    return {
        "C": float(final["C"]),
        "w": float(final["w"]),
        "rank": int(final["rank"]),
        "route": "cached_resolved_ap_checkpoint",
        "checkpoint": str(path),
        "digits": int(final["digits"]),
        "pmf_sha256": actual_pmf,
        "amplitude_sha256": actual_amplitudes,
    }


def _make_ensemble(config: dict, nu_mb: float):
    ensemble = reference_ensemble(
        "mb",
        batch_size=1,
        modulation_variance=VA,
        nu_mb=nu_mb,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    physical_energy = float(ensemble.computed_va()[0])
    if not math.isclose(physical_energy, VA, rel_tol=0.0, abs_tol=1.0e-12):
        raise RuntimeError(f"V_A changed at MB={nu_mb}: {physical_energy}")
    if not math.isclose(float(ensemble.probabilities.sum()), 1.0, rel_tol=0.0, abs_tol=1.0e-12):
        raise RuntimeError(f"MB PMF is not normalized at MB={nu_mb}")
    return ensemble


def _evaluate_mb(
    config: dict,
    ensemble,
    source: dict,
    transmittance: float,
    epsilon: float,
    numerical: dict[str, float],
    nu_mb: float,
) -> dict:
    t = torch.tensor([transmittance], dtype=torch.float64)
    e = torch.tensor([epsilon], dtype=torch.float64)
    c = torch.tensor([source["C"]], dtype=torch.float64)
    w = torch.tensor([source["w"]], dtype=torch.float64)
    mi_values = []
    for seed in MI_SEEDS:
        mi_values.append(float(discrete_mutual_information(
            ensemble,
            t,
            e,
            noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
            standard_noise_samples=standard_complex_noise(
                (1, 256, MI_SAMPLES_PER_SYMBOL),
                generator=torch_generator(seed),
                device=t.device,
            ),
        )[0]))
    mi_mean = float(np.mean(mi_values))
    mi_stderr = float(np.std(mi_values, ddof=1) / math.sqrt(len(mi_values)))
    holevo = _holevo_from_source_moments(
        ensemble,
        t,
        e,
        coherent_correlation=c,
        w_raw=w,
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False,
        diagnostics={
            "backend": "mb_skr_sweep_zeta30_va2",
            "source_moment_route": source["route"],
            "phase_noise_already_in_epsilon": True,
        },
    )
    chi_be = float(holevo.chi_be[0])
    key_rate = fading_secret_key_rate(
        torch.tensor([mi_mean], dtype=torch.float64),
        torch.tensor([chi_be], dtype=torch.float64),
        float(config["cvqkd"]["beta_reconciliation"]),
    )
    minimum_lambda = min(
        float(holevo.covariance.lambda1[0]),
        float(holevo.covariance.lambda2[0]),
        float(holevo.covariance.lambda3[0]),
    )
    return {
        "mb_parameter": nu_mb,
        "SKR": float(key_rate.fading_average_raw),
        "I_AB": mi_mean,
        "I_AB_stderr": mi_stderr,
        "chi_BE": chi_be,
        "effective_transmittance": transmittance,
        "physical_energy_VA": float(ensemble.computed_va()[0]),
        "pmf_normalization": float(ensemble.probabilities.sum()),
        "minimum_symplectic_lambda": minimum_lambda,
        "non_physical": minimum_lambda < 1.0 - 1.0e-10,
        "status": "PASS" if minimum_lambda >= 1.0 - 1.0e-10 else "NON_PHYSICAL",
        "source_rank": source["rank"],
        "source_checkpoint": source["checkpoint"],
    }


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
    if not math.isclose(physical["zenith_angle_rad"], zeta_rad, rel_tol=0.0, abs_tol=1.0e-15):
        raise RuntimeError("The requested zeta was not retained by the physical channel.")

    analysis = analyze_product(physical["v_sc"], physical)
    moments = analysis["moments"]
    phase_config = config["channel"]["phase_noise"]
    phase = phase_parameter_provenance(
        phase_config["cn2_phase_m_minus_two_thirds"],
        physical["wavelength_m"],
        physical["link_length_m"],
        mapping_status=phase_config.get("mapping_status", "configured"),
        author_approved=phase_config.get("author_approved", False),
    )
    security = physical_channel_parameters(
        moments["mean_sqrt_eta"],
        float(physical["epsilon_base_snu"]),
        phase["c_phi"],
        VA,
    )
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
            "VA_requested": VA,
            "mean_transmittance": moments["mean_eta"],
            "mean_sqrt_transmittance": moments["mean_sqrt_eta"],
            "effective_excess_noise": security["epsilon"],
            "mean_excess_noise": physical["epsilon_base_snu"],
            "phase_excess_noise": security["xi_phase"],
            "effective_transmittance": security["T"],
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
            row.update(result)
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "mb_skr_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    passed = [row for row in rows if row["status"] == "PASS"]
    if not passed:
        raise RuntimeError("No MB sweep point passed the physicality check.")
    figure_path = OUTPUT_DIR / "SKR_vs_MB.png"
    best = max(passed, key=lambda row: float(row["SKR"]))
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(
        [row["mb_parameter"] for row in passed],
        [row["SKR"] for row in passed],
        marker="o",
        linewidth=1.5,
    )
    ax.set_xlabel("Maxwell–Boltzmann parameter")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("SKR vs MB: zeta = 30 deg, V_A = 2")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    print(json.dumps({
        "csv_path": str(csv_path.resolve()),
        "figure_path": str(figure_path.resolve()),
        "zeta_deg": ZETA_DEG,
        "VA": VA,
        "link_distance_m": physical["link_length_m"],
        "mean_transmittance": moments["mean_eta"],
        "effective_transmittance": security["T"],
        "best_mb": best["mb_parameter"],
        "best_SKR": best["SKR"],
        "failed_points": [row for row in rows if row["status"] == "FAILED"],
        "non_physical_points": [row["mb_parameter"] for row in rows if row["status"] == "NON_PHYSICAL"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
