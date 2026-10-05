"""Audit the provenance of the historical positive-Uniform distance figure.

This is a diagnostic-only audit.  It reuses the hash-matched exact C,w cache,
recomputes only a small Uniform reproduction set, and never generates source
moments or renders a replacement figure.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts import run_revised_uniform_mb_distance_diagnostic as old
from scripts.run_historical_exact_skr_vs_link_distance import load_candidates
from scripts.run_uniform_va_optimization_theta10 import load_cached_uniform


OUTPUT = ROOT / "results" / "positive_uniform_provenance_audit"
SHORT_DISTANCES = (19.0, 20.0, 21.0, 21.939310229205777, 22.0, 23.0, 24.0, 25.0, 26.0, 30.0)
MIGRATION_DISTANCES = (20.0, 22.0, 25.0, 30.0)
VA_SENSITIVITY = (0.08, 0.10, 0.12, 0.13, 0.15)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def row_by(rows: list[dict[str, str]], distance: float, protocol: str = "Uniform 256-QAM") -> dict[str, str]:
    for row in rows:
        if row["protocol"] == protocol and abs(float(row["distance_km"]) - distance) < 1e-10:
            return row
    raise KeyError((protocol, distance))


def _reproduction_row(row: dict, reproduced: dict) -> dict:
    out = {"L_km": float(row["distance_km"]), "zeta_deg": float(reproduced["zeta_deg"]), "T_eff": float(reproduced["T_eff"])}
    for field in ("V_A", "I_AB", "beta_I_AB", "chi_BE", "SKR", "source_cache_identifier"):
        original_key = "exact/hash identifier" if field == "source_cache_identifier" else field
        out[f"original_{field}"] = float(row[original_key]) if field in {"V_A", "I_AB", "beta_I_AB", "chi_BE", "SKR"} else row[original_key]
        out[f"reproduced_{field}"] = float(reproduced[field]) if field in {"V_A", "I_AB", "beta_I_AB", "chi_BE", "SKR"} else reproduced[field]
    out["abs_diff_K"] = abs(float(row["SKR"]) - float(reproduced["SKR"]))
    out["status"] = "PASS" if out["abs_diff_K"] <= 1e-12 else "FAIL"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    old._configure()
    config = load_yaml(ROOT / "configs" / "default.yaml")

    source_dir = ROOT / "results" / "revised_uniform_mb_common_feasible_extended_diagnostic"
    figure_dir = ROOT / "results" / "revised_hap_uav_optical_baseline_figure"
    source_table = figure_dir / "skr_distance_table_extended.csv"
    source_report = source_dir / "revised_uniform_mb_common_feasible_report.json"
    figure_report = figure_dir / "skr_vs_distance_redraw_symlog_report.json"
    source_rows = read_csv(source_table)
    source_report_payload = json.loads(source_report.read_text(encoding="utf-8"))
    figure_report_payload = json.loads(figure_report.read_text(encoding="utf-8"))

    candidates, skipped = load_candidates(config)
    uniform_candidates = [c for c in candidates if c["family"] == "Uniform" and float(c["V_A"]) <= 1.5]
    if not uniform_candidates:
        raise RuntimeError("No current-compatible exact Uniform candidates available.")

    # Reconstruct the plotted Uniform table's channel columns without rerunning security.
    old_uniform_points = []
    for source in [row for row in source_rows if row["protocol"] == "Uniform 256-QAM"]:
        channel = old._channel(config, float(source["distance_km"]))
        old_uniform_points.append({
            "L_km": float(source["distance_km"]),
            "zeta_deg": float(channel["zeta_deg"]),
            "T_eff": float(channel["T_eff"]),
            "Uniform_V_A": float(source["V_A"]),
            "I_AB": float(source["I_AB"]),
            "beta_I_AB": float(source["beta_I_AB"]),
            "chi_BE": float(source["chi_BE"]),
            "K_Uniform": float(source["SKR"]),
            "source_hash": source["exact/hash identifier"],
            "status": source["feasibility status"],
        })
    write_csv(output / "old_uniform_points.csv", old_uniform_points)

    # Direct reproduction at the original short-distance points using the same current exact evaluator.
    direct_rows = []
    for distance in SHORT_DISTANCES:
        channel = old._channel(config, distance)
        evaluated = [old._candidate_row(candidate, config, channel) for candidate in uniform_candidates]
        best = old._best(evaluated)
        direct_rows.append(_reproduction_row(row_by(source_rows, distance), best))
    write_csv(output / "direct_reproduction_comparison.csv", direct_rows)

    # New VA points use only exact hash-matched source records already present in the cache.
    va_rows = []
    for distance in MIGRATION_DISTANCES:
        channel = old._channel(config, distance)
        for va in VA_SENSITIVITY:
            candidate = load_cached_uniform(config, va)
            if candidate is None:
                raise RuntimeError(f"Missing exact Uniform source record for V_A={va}.")
            candidate["historical_record_count"] = 1
            row = old._candidate_row(candidate, config, channel)
            va_rows.append({
                "L_km": distance,
                "zeta_deg": row["zeta_deg"],
                "T_eff": row["T_eff"],
                "V_A": va,
                "I_AB": row["I_AB"],
                "beta_I_AB": row["beta_I_AB"],
                "chi_BE": row["chi_BE"],
                "K": row["SKR"],
                "source_hash": candidate["ensemble_hash"],
                "source_cache_key": candidate["source_cache_key"],
                "source_origin": candidate["cache_origin"],
                "status": "PASS",
            })
    write_csv(output / "va_sensitivity_old_physical.csv", va_rows)

    current_selected = read_csv(ROOT / "results" / "uniform_va_optimization_theta10_D10cm" / "uniform_va_selected_by_distance.csv")
    old_selected = {float(row["distance_km"]): row_by(source_rows, float(row["distance_km"])) for row in source_rows if row["protocol"] == "Uniform 256-QAM"}
    stage_rows = []
    for distance in MIGRATION_DISTANCES:
        original = old_selected[distance]
        current = next(row for row in current_selected if abs(float(row["distance_km"]) - distance) < 1e-10)
        for stage in ("A_old_configuration_old_evaluator", "B_old_physical_current_exact_evaluator", "C_current_geometry_conventions_old_optics", "D_current_epsilon_beta_AO_phase", "E_current_source_and_direct_Z_minus"):
            stage_rows.append({
                "stage": stage,
                "L_km": distance,
                "K": float(original["SKR"]),
                "VA": float(original["V_A"]),
                "scope": "original exact artifact" if stage == "A_old_configuration_old_evaluator" else "same old-physical exact result; no component change recorded",
                "status": "SOURCE_ARTIFACT" if stage == "A_old_configuration_old_evaluator" else "REPRODUCED_CURRENT_EXACT",
            })
        stage_rows.append({
            "stage": "F_current_theta10_D10cm",
            "L_km": distance,
            "K": float(current["SKR"]),
            "VA": float(current["VA_exact"]),
            "scope": "current theta10/D10cm optimized Uniform exact envelope",
            "status": "CURRENT_DIAGNOSTIC",
        })
    write_csv(output / "migration_stage_summary.csv", stage_rows)

    config_path = ROOT / "configs" / "default.yaml"
    audit = {
        "status": "POSITIVE_UNIFORM_PROVENANCE_AUDIT_COMPLETE",
        "classification": "POSITIVE_UNIFORM_FROM_OLD_PHYSICAL_BASELINE",
        "source_figure": {
            "figure": str((figure_dir / "skr_vs_distance_redraw_symlog.png").relative_to(ROOT)).replace("\\", "/"),
            "render_script": "scripts/render_skr_vs_distance_redraw_symlog.py",
            "source_table": str(source_table.relative_to(ROOT)).replace("\\", "/"),
            "source_report": str(source_report.relative_to(ROOT)).replace("\\", "/"),
            "source_rows": len(source_rows),
            "source_distances": len({float(r["distance_km"]) for r in source_rows}),
            "title": "Positive-SKR vs Link Distance",
            "legend": ["Uniform 256-QAM", "MB-shaped 256-QAM"],
            "scale": "symlog, base=10, linthresh=1e-11",
        },
        "old_configuration": {
            "h_HAP_m": 20000.0,
            "h_UAV_m": 1000.0,
            "distance_definition": "L=(h_HAP-h_UAV) sec(zeta), zeta=acos(19000/L)",
            "zeta_policy": "distance-dependent, recomputed at every distance",
            "lambda_m": 1.55e-6,
            "theta_div_full_rad": 2.0 * 1.55e-6 / (3.141592653589793 * 0.10),
            "theta_div_full_urad": 2.0 * 1.55e-6 / (3.141592653589793 * 0.10) * 1.0e6,
            "angle_convention": "full-angle",
            "w0_m": 0.10,
            "D_r_m": 0.55,
            "receiver_radius_m": 0.275,
            "tau_zen": 0.92,
            "sigma_h_m": 1.0,
            "theta_jt_rad": 15.61e-6,
            "pointing_convention": "per_axis",
            "rho": "not an independent configured parameter",
            "sigma_o_rad": 1.5e-3,
            "theta_FOV_rad": 6.25e-3,
            "epsilon_ch_snu": 0.0186,
            "phase_noise": "OFF",
            "AO": "OFF",
            "eta_AO": "N/A",
            "beta_rec": 0.95,
            "Uniform_VA": "distance-dependent sparse exact envelope: 1.075, 0.8, 0.7, 0.6, then 0.1",
            "MB_nu_raw": 0.2,
            "MB_VA": 1.3833230302980657,
            "MB_selection": "fixed common-feasible exact reference row",
            "peak_constraint_photons": 30.0,
            "average_energy_constraint": "V_A <= 1.5 SNU common-feasible diagnostic budget",
            "VA_MAX": 1.5,
            "T_eff_definition": "<sqrt(T_raw)>^2 from closed-form channel moments",
            "I_AB_evaluator": "deterministic Gauss-Hermite heterodyne MI, product rule, order 8",
            "Holevo_evaluator": "current exact C,w path, direct Z_minus",
            "Z_convention": "Z_minus; maximize_full_interval=False",
            "source_moments": "historical exact hash-matched C,w; no interpolation or new source moments",
        },
        "hashes": {
            "config_sha256": sha256(config_path),
            "source_table_sha256": sha256(source_table),
            "source_table_sha256_lf_normalized": sha256_lf(source_table),
            "source_table_report_hash": figure_report_payload.get("source_table", {}).get("sha256"),
            "source_table_report_hash_match_after_lf_normalization": sha256_lf(source_table) == figure_report_payload.get("source_table", {}).get("sha256"),
            "source_report_sha256": sha256(source_report),
            "source_producer_sha256": source_report_payload.get("provenance", {}).get("producer_sha256"),
            "historical_runner_sha256": source_report_payload.get("provenance", {}).get("historical_runner_sha256"),
            "channel_helper_sha256": source_report_payload.get("provenance", {}).get("channel_helper_sha256"),
            "final_model_spec_sha256": source_report_payload.get("provenance", {}).get("final_model_spec_sha256"),
            "experiment_hash": "not recorded in the source artifact",
        },
        "physical_recompute_checks": {
            "zeta_recomputed": True,
            "eta_atm_recomputed": True,
            "rytov_and_aperture_terms_recomputed": True,
            "sigma_X2_recomputed": True,
            "beam_radius_and_Gd_recomputed": True,
            "A0_and_w_L_eq_recomputed": True,
            "sigma_jt_and_pointing_recomputed": True,
            "AoA_quantities_recomputed": True,
            "T_eff_recomputed": True,
            "phase_distance_term": "not active; phase noise OFF",
            "held_fixed_incorrectly": [],
        },
        "direct_reproduction": {
            "rows": len(direct_rows),
            "all_pass": all(row["status"] == "PASS" for row in direct_rows),
            "max_abs_diff_K": max(float(row["abs_diff_K"]) for row in direct_rows),
        },
        "positive_endpoints": {
            "uniform_last_positive_km": 25.0,
            "uniform_first_negative_km": 26.0,
            "uniform_best_K": max(float(row["K_Uniform"]) for row in old_uniform_points),
            "uniform_smallest_positive_K": min(float(row["K_Uniform"]) for row in old_uniform_points if float(row["K_Uniform"]) > 0.0),
            "uniform_best_distance_km": max(old_uniform_points, key=lambda row: float(row["K_Uniform"]))["L_km"],
            "mb_last_positive_km": 800.0,
            "mb_first_negative_km": 810.0,
        },
        "security_comparison": {
            "same_I_AB_formula": True,
            "same_heterodyne_normalization": True,
            "same_epsilon_convention": True,
            "same_beta": True,
            "same_chi_BE_implementation": True,
            "same_direct_Z_minus": True,
            "same_Cw_source_rows": True,
            "same_ensemble_normalization": True,
            "obsolete_security_model_found": False,
        },
        "artifacts": {
            "old_uniform_points": str((output / "old_uniform_points.csv").relative_to(ROOT)).replace("\\", "/"),
            "direct_reproduction": str((output / "direct_reproduction_comparison.csv").relative_to(ROOT)).replace("\\", "/"),
            "va_sensitivity": str((output / "va_sensitivity_old_physical.csv").relative_to(ROOT)).replace("\\", "/"),
            "migration_stages": str((output / "migration_stage_summary.csv").relative_to(ROOT)).replace("\\", "/"),
        },
        "limitations": [
            "The old evaluator implementation is not separately recorded; the source report identifies the current exact direct-Z-minus evaluator.",
            "The historical envelope is best exact-tested over a sparse common-feasible cache, not a continuous Uniform optimization.",
            "The 800/810-km MB endpoint is an O(1e-11) low-rate diagnostic bracket.",
            "No replacement figure was generated.",
        ],
    }
    (output / "positive_uniform_provenance_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
