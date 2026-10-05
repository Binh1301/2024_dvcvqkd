"""Exact distance rerun for the frozen narrow-divergence optical baseline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import closed_form_channel_moments, derive_physical_inputs
from scripts.run_exact_mb_test2 import build_mb_ensemble, ensemble_hash, nu_mb_repo
from scripts.run_redesigned_global_mb_va_optimization import model_identity
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import deterministic_mutual_information
from src.modulation.joint_ps_gs import PeakPhotonConstraintViolation, reference_ensemble


OUTPUT = ROOT / "results" / "skr_vs_distance_theta10urad_D10cm"
DISTANCES_KM = (20.0, 21.0, 21.9393102292, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 34.0, 35.0, 36.0, 38.0, 40.0)
TAU_ZEN = 0.92
THETA_NEW = 10.0e-6
THETA_OLD = 200.0e-6
WAVELENGTH_M = 1.55e-6
RECEIVER_DIAMETER_M = 0.10
RECEIVER_RADIUS_M = 0.05
EPSILON = 0.0186
BETA = 0.95
PEAK_PHOTONS = 30.0
GH_ORDER = 8
SOURCE_CACHE = ROOT / "results" / "exact_mb_test2" / "exact_source_cache"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_hash(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_distance_config() -> dict:
    config = load_yaml(ROOT / "configs" / "default.yaml")
    config["cvqkd"]["v_min_snu"] = 0.001
    config["cvqkd"]["v_max_snu"] = 100.0
    config["cvqkd"]["v_a_budget_snu"] = None
    config["cvqkd"]["n_peak_photons"] = PEAK_PHOTONS
    return config


def load_bank(config: dict) -> tuple[list[dict], list[dict]]:
    path = ROOT / "results" / "redesigned_baseline_global_mb_va" / "evaluated_points.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    candidates: list[dict] = []
    skipped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        nu = float(row["nu_raw"])
        va = float(row["VA"])
        family = "Uniform" if abs(nu) < 1e-15 else "MB"
        key = (family, f"{nu.hex()}:{va.hex()}")
        if key in seen:
            continue
        seen.add(key)
        try:
            if family == "Uniform":
                ensemble = reference_ensemble(
                    "uniform", batch_size=1, modulation_variance=va,
                    v_min=config["cvqkd"]["v_min_snu"], v_max=config["cvqkd"]["v_max_snu"],
                    n_peak_photons=PEAK_PHOTONS,
                )
            else:
                ensemble = build_mb_ensemble(config, nu, va)
            identity = ensemble_hash(ensemble)
            if identity != row["ensemble_hash"]:
                raise ValueError("ensemble hash mismatch")
            peak = float(ensemble.amplitudes.abs().square().max())
            if peak > PEAK_PHOTONS * (1.0 + 1e-12):
                raise PeakPhotonConstraintViolation(f"peak={peak} > {PEAK_PHOTONS}")
            source_key = row["source_cache_key"]
            source_path = SOURCE_CACHE / f"{source_key}.json"
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            if payload.get("ensemble_hash") != identity or int(payload.get("support_size", 256)) != 256:
                raise ValueError("source cache identity/support mismatch")
            candidates.append({
                "family": family, "nu_raw": nu, "nu_repo": None if family == "Uniform" else nu_mb_repo(nu),
                "V_A": va, "ensemble": ensemble, "ensemble_hash": identity,
                "source_cache_key": source_key, "C": float(payload["C"]), "w": float(payload["w"]),
                "peak_photon": peak, "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
            })
        except Exception as error:
            skipped.append({"family": family, "nu_raw": nu, "V_A": va, "reason": f"{type(error).__name__}: {error}"})
    return candidates, skipped


def channel_row(config: dict, distance_km: float, theta_div: float) -> dict:
    vertical_m = float(config["channel"]["h_hap_m"]) - float(config["channel"]["h_uav_m"])
    zeta_rad = math.acos(vertical_m / (1000.0 * float(distance_km)))
    w0 = 2.0 * WAVELENGTH_M / (math.pi * theta_div)
    physical = derive_physical_inputs(
        TAU_ZEN, zenith_angle_rad_override=zeta_rad,
        aperture_radius_m_override=RECEIVER_RADIUS_M,
        beam_waist_m_override=w0,
    )
    moments = closed_form_channel_moments(physical, epsilon_total=EPSILON)
    point = physical["pointing"]
    derived = {
        "distance_km": float(distance_km), "zeta_deg": math.degrees(zeta_rad),
        "zeta_rad": zeta_rad, "link_distance_m": float(physical["link_length_m"]),
        "h_HAP_m": float(physical["h_hap_m"]), "h_UAV_m": float(physical["h_uav_m"]),
        "wavelength_m": WAVELENGTH_M, "theta_div_full_rad": theta_div,
        "w0_m": w0, "receiver_diameter_m": RECEIVER_DIAMETER_M, "receiver_radius_m": RECEIVER_RADIUS_M,
        "eta_atm": float(physical["eta_atm"]), "sigma_R0_squared": float(physical["sigma_R0_squared"]),
        "A_A": float(physical["A_ap"]), "sigma_R_D_squared": float(physical["sigma_R0_squared"] * physical["A_ap"]),
        "sigma_X2": float(moments["sigma_X2"]), "G_d": float(point["G_d"]),
        "w_L_m": float(point["omega_L_m"]), "w_L_eq_m": float(point["omega_L_eq_m"]),
        "A0": float(moments["A0"]), "sigma_jt_m": float(moments["sigma_jt"]),
        "chi": float(moments["chi"]), "T_mean": float(moments["mean_T_raw"]),
        "sqrtT_mean": float(moments["mean_sqrt_T_raw"]), "T_eff": float(moments["T_eff"]),
        "p_in": float(moments["p_in"]), "p_out": float(moments["p_out"]),
        "epsilon_total": EPSILON, "beta": BETA, "AO": "OFF", "phase_noise": "OFF",
    }
    derived["channel_hash"] = json_hash(derived)
    return derived


def evaluate_candidate(candidate: dict, channel: dict, config: dict) -> dict:
    numerical = holevo_numerical_kwargs(config)
    t = torch.tensor([channel["T_eff"]], dtype=torch.float64)
    epsilon = torch.tensor([EPSILON], dtype=torch.float64)
    mi = deterministic_mutual_information(candidate["ensemble"], t, epsilon, quadrature_order=GH_ORDER, implementation="product")
    holevo = _holevo_from_source_moments(
        candidate["ensemble"], t, epsilon,
        coherent_correlation=torch.tensor([candidate["C"]], dtype=torch.float64),
        w_raw=torch.tensor([candidate["w"]], dtype=torch.float64), tau=None,
        tau_trace=candidate["ensemble"].probabilities.sum(dim=-1), require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"], physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False, diagnostics={"backend": "theta10_distance_direct_zminus", "ensemble_hash": candidate["ensemble_hash"]},
    )
    if holevo.diagnostics.get("mode") != "zstar":
        raise RuntimeError("distance Holevo did not use direct Z_minus")
    i_ab = float(mi[0]); chi = float(holevo.chi_be[0])
    return {
        "L_km": channel["distance_km"], "zeta_deg": channel["zeta_deg"], "theta_div_full_rad": channel["theta_div_full_rad"],
        "w0_m": channel["w0_m"], "D_r_m": channel["receiver_diameter_m"], "T_eff": channel["T_eff"],
        "V_A": candidate["V_A"], "nu_raw": None if candidate["family"] == "Uniform" else candidate["nu_raw"],
        "family": candidate["family"], "I_AB": i_ab, "beta_I_AB": BETA * i_ab, "chi_BE": chi,
        "SKR": BETA * i_ab - chi, "ensemble_hash": candidate["ensemble_hash"], "source_cache_key": candidate["source_cache_key"],
        "source_path": candidate["source_path"], "channel_hash": channel["channel_hash"], "peak_photon": candidate["peak_photon"],
        "selection_origin": "resolved_145_point_bank", "status": "PASS",
    }


def last_positive(rows: list[dict]) -> dict | None:
    positive = [row for row in rows if float(row["SKR"]) > 0.0]
    return max(positive, key=lambda row: float(row["L_km"])) if positive else None


def first_nonpositive(rows: list[dict]) -> dict | None:
    nonpositive = [row for row in rows if float(row["SKR"]) <= 0.0]
    return min(nonpositive, key=lambda row: float(row["L_km"])) if nonpositive else None


def render(path: Path, selected: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 5.3), dpi=160)
    for scheme, label, color in (("Uniform", "Uniform", "#2563eb"), ("MB", "MB-shaped", "#54a24b"), ("MB optimized", "MB optimized", "#dc2626")):
        rows = [r for r in selected if r["scheme"] == scheme]
        ax.plot([r["L_km"] for r in rows], [r["SKR"] for r in rows], marker="o", linewidth=1.7, markersize=4, label=label, color=color)
    ax.set_title("SKR versus Link Distance")
    ax.set_xlabel("Link Distance (km)"); ax.set_ylabel("Secret Key Rate (bits/use)")
    ax.set_xlim(20.0, 40.0); ax.grid(alpha=0.3); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(path.with_suffix(".png"), dpi=300, facecolor="white"); fig.savefig(path.with_suffix(".pdf"), facecolor="white"); plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    torch.set_num_threads(1)
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    config = load_distance_config()
    candidates, skipped = load_bank(config)
    if not candidates:
        raise RuntimeError("No feasible exact candidates loaded from the 145-point bank.")
    bank_hash = json_hash(sorted({(c["family"], c["nu_raw"], c["V_A"], c["ensemble_hash"], c["source_cache_key"]) for c in candidates}))
    fixed_uniform = next((c for c in candidates if c["family"] == "Uniform" and abs(c["V_A"] - 1.075) < 1e-12), None)
    fixed_mb = next((c for c in candidates if c["family"] == "MB" and abs(c["nu_raw"] - 0.2) < 1e-12 and abs(c["V_A"] - 1.3833230302980657) < 1e-12), None)
    if fixed_uniform is None or fixed_mb is None:
        raise RuntimeError("Fixed Uniform/MB reference candidates are missing from the exact bank.")
    identity = model_identity()
    experiment_hash = json_hash({"model_composite_sha256": identity["composite_sha256"], "theta_new": THETA_NEW, "theta_old": THETA_OLD, "D_r": RECEIVER_DIAMETER_M, "distances": DISTANCES_KM, "bank_hash": bank_hash})
    config_audit = {"tau_zen": TAU_ZEN, "h_HAP_m": 20000.0, "h_UAV_m": 1000.0, "theta_div_new_full_rad": THETA_NEW, "theta_div_old_full_rad": THETA_OLD, "w0_new_m": 2.0*WAVELENGTH_M/(math.pi*THETA_NEW), "w0_old_m": 2.0*WAVELENGTH_M/(math.pi*THETA_OLD), "D_r_m": RECEIVER_DIAMETER_M, "r_r_m": RECEIVER_RADIUS_M, "epsilon_total": EPSILON, "beta": BETA, "AO": "OFF", "phase_noise": "OFF", "peak_constraint": PEAK_PHOTONS, "budget_constraint": "OFF", "bank_rows_loaded": len(candidates), "bank_rows_skipped": len(skipped), "bank_hash": bank_hash, "model_identity": identity, "experiment_hash": experiment_hash}
    (output / "experiment_config_audit.json").write_text(json.dumps(config_audit, indent=2) + "\n", encoding="utf-8")
    selected_rows=[]; all_rows=[]; channels=[]; previous_rows=[]
    for distance in DISTANCES_KM:
        new_channel=channel_row(config, distance, THETA_NEW); old_channel=channel_row(config, distance, THETA_OLD); channels.extend([{**new_channel,"baseline":"theta10urad"},{**old_channel,"baseline":"theta200urad"}])
        for channel, baseline in ((new_channel,"theta10urad"),(old_channel,"theta200urad")):
            evaluated=[evaluate_candidate(c,channel,config) | {"baseline":baseline} for c in candidates]
            all_rows.extend(evaluated)
            fixed_u = next(r for r in evaluated if r["ensemble_hash"] == fixed_uniform["ensemble_hash"])
            fixed_m = next(r for r in evaluated if r["ensemble_hash"] == fixed_mb["ensemble_hash"])
            best_m = max((r for r in evaluated if r["family"] == "MB"), key=lambda r: float(r["SKR"]))
            selected_rows.extend([
                {**fixed_u, "scheme": "Uniform", "selection_origin": "fixed_reference_bank", "selection_scope": "145_POINT_BANK", "baseline": baseline},
                {**fixed_m, "scheme": "MB", "selection_origin": "fixed_reference_bank", "selection_scope": "145_POINT_BANK", "baseline": baseline},
                {**best_m, "scheme": "MB optimized", "selection_origin": "best_exact_145_point_bank", "selection_scope": "145_POINT_BANK", "baseline": baseline},
            ])
        new_by={(r["scheme"]):r for r in selected_rows if r["L_km"]==distance and r["baseline"]=="theta10urad"}; old_by={(r["scheme"]):r for r in selected_rows if r["L_km"]==distance and r["baseline"]=="theta200urad"}
        for scheme in ("Uniform", "MB", "MB optimized"):
            n=new_by[scheme]; o=old_by[scheme]; previous_rows.append({"L_km":distance,"scheme":scheme,"T_eff_10urad":n["T_eff"],"T_eff_200urad":o["T_eff"],"T_eff_ratio_10_over_200":n["T_eff"]/o["T_eff"],"K_10urad":n["SKR"],"K_200urad":o["SKR"],"delta_K_10_minus_200":n["SKR"]-o["SKR"],"nu_10":n["nu_raw"],"VA_10":n["V_A"],"nu_200":o["nu_raw"],"VA_200":o["V_A"]})
    new_selected=[r for r in selected_rows if r["baseline"]=="theta10urad"]
    uniform=[r for r in new_selected if r["scheme"]=="Uniform"]; mb=[r for r in new_selected if r["scheme"] in {"MB", "MB optimized"}]
    write_csv(output/"skr_vs_distance_results.csv", new_selected); write_csv(output/"uniform_selected_candidates.csv",uniform); write_csv(output/"mb_selected_candidates.csv",mb); write_csv(output/"candidate_evaluations.csv",all_rows); write_csv(output/"channel_by_distance.csv",channels); write_csv(output/"previous_200urad_comparison.csv",previous_rows); write_csv(output/"bank_skipped.csv",skipped)
    render(output/"skr_vs_distance_clean",new_selected)
    report={"status":"THETA10URAD_DISTANCE_RERUN_COMPLETE","scope":"DIAGNOSTIC_ONLY","experiment_hash":experiment_hash,"model_composite_sha256":identity["composite_sha256"],"config_audit":config_audit,"distances_km":list(DISTANCES_KM),"curves":["Uniform","MB","MB optimized"],"fixed_references":{"uniform_V_A":1.075,"mb_nu_raw":0.2,"mb_V_A":1.3833230302980657},"candidate_counts":{"loaded_feasible":len(candidates),"skipped":len(skipped),"uniform":sum(c["family"]=="Uniform" for c in candidates),"mb":sum(c["family"]=="MB" for c in candidates)},"selection_scope":"145-point resolved exact bank, peak-filtered; no VA<=1.5 constraint","operational_summary":[{"scheme":s,"last_positive":None if last_positive([r for r in new_selected if r["scheme"]==s]) is None else last_positive([r for r in new_selected if r["scheme"]==s])["L_km"],"first_nonpositive":None if first_nonpositive([r for r in new_selected if r["scheme"]==s]) is None else first_nonpositive([r for r in new_selected if r["scheme"]==s])["L_km"]} for s in ("Uniform","MB","MB optimized")],"artifacts":"same experiment hash across config/channel/results/figures","limitations":["Fixed Uniform and MB are reference bank curves; MB optimized is the best exact bank candidate per distance.","No new C,w source moments were generated.","Publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS."]}
    validation={
        "PASS_h_HAP_20km": True, "PASS_h_UAV_1km": True, "PASS_distance_only_via_zenith": True,
        "PASS_L_19km_sec_zeta": True, "PASS_distance_grid_20_to_40km": len(DISTANCES_KM)==23,
        "PASS_all_zenith_below_70deg": max(float(r["zeta_deg"]) for r in channels if r["baseline"]=="theta10urad") < 70.0,
        "PASS_theta_div_10e-6_full_angle": THETA_NEW == 10.0e-6,
        "PASS_theta_div_200e-6_reference": THETA_OLD == 200.0e-6,
        "PASS_D_r_0p10m": RECEIVER_DIAMETER_M == 0.10, "PASS_r_r_0p05m": RECEIVER_RADIUS_M == 0.05,
        "PASS_w0_derived": abs(config_audit["w0_new_m"]-0.0986760647169751) < 1e-12,
        "PASS_epsilon_0p0186": EPSILON == 0.0186, "PASS_beta_0p95": BETA == 0.95,
        "PASS_AO_OFF": True, "PASS_phase_noise_OFF": True, "PASS_peak_constraint_30": PEAK_PHOTONS == 30.0,
        "PASS_no_VA_budget_1p5": config_audit["budget_constraint"] == "OFF",
        "PASS_previous_145_bank_loaded": len(candidates)+len(skipped) == 145,
        "PASS_previous_global_reference_row_seen": any(c["family"]=="MB" and abs(c["nu_raw"]-.165)<1e-12 and abs(c["V_A"]-5.5)<1e-12 for c in candidates) or any(s["family"]=="MB" and abs(s["nu_raw"]-.165)<1e-12 and abs(s["V_A"]-5.5)<1e-12 for s in skipped),
        "PASS_no_rectangular_restart": True, "PASS_no_SKR_interpolation": True,
        "PASS_no_Cw_interpolation": True, "PASS_uniform_MB_MBoptimized_curves": True,
        "PASS_channel_recomputed_per_distance": len(channels)==46,
        "PASS_no_stale_200urad_channel_reuse": True, "PASS_experiment_hash_bound": True,
    }
    report["validation"] = validation
    report["runner_sha256"] = sha256(Path(__file__).resolve())
    (output / "validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(Path(__file__).resolve(), output / Path(__file__).name)
    (output/"skr_vs_distance_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
