"""One-point, cache-only diagnosis of the historical/corrected SKR change.

Reuses cached C,w and stored mixture MI. Rechecks one physical channel and
its algebra with unchanged producers; no AP, optimization or new Monte Carlo.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DISTANCE_KM = 21.9393102292
NU_RAW = 0.165
VA = 5.5
EPSILON_CH = 0.0186
BETA = 0.95
HISTORICAL_CSV = ROOT / "results" / "theta10_D55_alt_opt_distance_sweep" / "three_scheme_alt_opt.csv"
SNAPSHOT_JSON = ROOT / "results" / "skr_pipeline_documentation" / "documentation_snapshot.json"
CORRECTED_JSON = ROOT / "results" / "manuscript_corrected_3moments" / "ideal_heterodyne_reference_20261013" / "reference_result.json"
OLD_INTEGRITY_JSON = ROOT / "results" / "manuscript_corrected_3moments" / "ideal_heterodyne_reference_20261013" / "integrity_receipt.json"
OUTPUT_DIR = ROOT / "results" / "manuscript_corrected_3moments" / "negative_skr_diagnostic_20261013"


def _sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _entropy(lam: float) -> float:
    x = (lam - 1.0) / 2.0
    if x < 0.0:
        raise ValueError(f"invalid bosonic occupation {x!r}")
    if x == 0.0:
        return 0.0
    return (x + 1.0) * math.log2(x + 1.0) - x * math.log2(x)


def _covariance(t: float, epsilon: float, z: float) -> dict[str, object]:
    a = VA + 1.0
    b = 1.0 + t * VA + t * epsilon
    delta = a * a + b * b - 2.0 * z * z
    determinant = (a * b - z * z) ** 2
    discriminant = delta * delta - 4.0 * determinant
    if discriminant < 0.0:
        raise ValueError("negative symplectic discriminant")
    root = math.sqrt(discriminant)
    lambda_1 = math.sqrt((delta + root) / 2.0)
    lambda_2 = math.sqrt((delta - root) / 2.0)
    lambda_3 = a - z * z / (b + 1.0)
    ordinary_min = (a + b - math.sqrt((a - b) ** 2 + 4.0 * z * z)) / 2.0
    g1, g2, g3 = (_entropy(lambda_1), _entropy(lambda_2), _entropy(lambda_3))
    matrix = [[a, 0.0, z, 0.0], [0.0, a, 0.0, -z],
              [z, 0.0, b, 0.0], [0.0, -z, 0.0, b]]
    return {
        "a": a, "b": b, "Z": z, "Delta": delta, "D": determinant,
        "discriminant": discriminant, "Gamma_AB": matrix,
        "lambda_1": lambda_1, "lambda_2": lambda_2, "lambda_3": lambda_3,
        "ordinary_covariance_min_eigenvalue": ordinary_min,
        "g_lambda_1": g1, "g_lambda_2": g2, "g_lambda_3": g3,
        "S_AB": g1 + g2, "S_conditional": g3, "chi_BE": g1 + g2 - g3,
        "physicality": min(lambda_1, lambda_2, lambda_3) >= 1.0 and ordinary_min > 0.0,
    }


def _historical_row() -> dict[str, str]:
    with HISTORICAL_CSV.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    matches = [
        row for row in rows
        if abs(float(row["L_km"]) - DISTANCE_KM) <= 1e-12
        and row["family"] == "MB"
        and abs(float(row["nu_raw"]) - NU_RAW) <= 1e-12
        and abs(float(row["V_A"]) - VA) <= 1e-12
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one historical reference row, found {len(matches)}")
    return matches[0]


def _relative_change(new: float, old: float) -> float | None:
    return None if old == 0.0 else (new - old) / old


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_hashes(expected: dict[str, str]) -> list[str]:
    changed = [rel for rel, digest in expected.items()
               if not (ROOT / rel).is_file() or _sha256(ROOT / rel) != digest]
    if changed:
        raise ValueError(f"Protected input or producer changed: {changed}")
    return changed


def _audit_current_point(corrected_root, historical, snapshot):
    """Audit the one source/channel point using unchanged producers; no oracle."""
    from scripts.run_manuscript_literal_3moments import verified_candidate
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config, W0_M
    from scripts.run_uniform_beam_waist_diagnostic import _channel_row
    from scripts.run_skr_vs_link_distance_theta10urad import evaluate_candidate
    from src.manuscript_literal_3moments import LiteralChannel
    from src.manuscript_corrected_evaluator import validate_cached_candidate
    from src.manuscript_corrected_3moments import (
        PhysicalFadingDistribution, effective_fading_channel,
        corrected_covariance, corrected_z_star, holevo_interval_maximizer,
    )
    import torch
    from scripts._common import holevo_numerical_kwargs
    from src.cvqkd.holevo import _holevo_from_source_moments

    identity, stored = corrected_root["identity"], corrected_root["record"]
    for key, expected in dict(R=1., xi_det=0., chi_het=1., xi_ch=EPSILON_CH,
                              VA=VA, nu_raw=NU_RAW, distance_km=DISTANCE_KM,
                              phase_noise="OFF", AO="OFF").items():
        if stored[key] != expected:
            raise ValueError(f"Corrected stored reference configuration mismatch: {key}")
    prior = json.loads(OLD_INTEGRITY_JSON.read_text(encoding="utf-8"))
    baseline = json.loads((CORRECTED_JSON.parent / "startup_manifest.json").read_text(encoding="utf-8"))
    _verify_hashes(baseline["protected_hashes"])
    mutable_state = {"docs/EVIDENCE.md", "docs/DECISION_LOG.md", "docs/PROJECT_STATE.md",
                     "docs/NEXT_ACTIONS.md", ".agent/SESSION_HANDOFF.md"}
    previous_outputs = {rel: digest for rel, digest in prior["output_hashes"].items()
                        if rel not in mutable_state}
    _verify_hashes(previous_outputs)
    producers = dict(identity["implementations"])
    producers["configs/default.yaml"] = identity["default_config_sha256"]
    producers["scripts/run_manuscript_corrected_ideal_reference.py"] = identity["ideal_reference_runner_sha256"]
    _verify_hashes(producers)
    if _sha256_json(identity) != stored["scientific_context_hash"]:
        raise ValueError("Corrected scientific context hash mismatch")

    source_path = ROOT / historical["source_path"]
    if _sha256(source_path) != identity["source_payload_sha256"]:
        raise ValueError("Source payload bytes changed")
    config = unconstrained_config()
    candidate = verified_candidate(source_path, config)
    ensemble = validate_cached_candidate(candidate)
    if candidate["ensemble_hash"] != stored["ensemble_hash"]:
        raise ValueError("Rebuilt transmitted ensemble differs from stored MI/security source")
    p = ensemble.probabilities.detach().cpu().numpy().reshape(-1)
    alpha = ensemble.amplitudes.detach().cpu().numpy().reshape(-1)
    row, physical = _channel_row(config, w0_m=W0_M, receiver_diameter_m=.55,
                                 distance_km=DISTANCE_KM)
    channel_hash = _sha256_json(row)
    if channel_hash != historical["channel_hash"]:
        raise ValueError("Recomputed historical optical channel hash differs")
    row = dict(row, theta_div_full_rad=1e-5, channel_hash=channel_hash)
    old_result = evaluate_candidate(candidate, row, config)
    numerical = holevo_numerical_kwargs(config)
    old_security = _holevo_from_source_moments(
        ensemble, torch.tensor([row["T_eff"]], dtype=torch.float64),
        torch.tensor([EPSILON_CH], dtype=torch.float64),
        coherent_correlation=torch.tensor([candidate["C"]], dtype=torch.float64),
        w_raw=torch.tensor([candidate["w"]], dtype=torch.float64), tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1), require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False, diagnostics={"backend": "negative_skr_diagnostic"})
    old_residuals = {name: old_result[name] - float(historical[name])
                     for name in ("I_AB", "beta_I_AB", "chi_BE", "SKR", "T_eff")}
    if any(abs(value) > 1e-13 for value in old_residuals.values()):
        raise ValueError(f"Historical evaluator regression failed: {old_residuals}")
    raw = LiteralChannel.from_physical(physical)
    if raw.__dict__ != identity["raw_channel"]:
        raise ValueError("Corrected raw channel differs from stored physics")
    fading = PhysicalFadingDistribution(raw)
    moments = fading.moments(R=1., xi_det=0., xi_ch=EPSILON_CH)
    effective = effective_fading_channel(moments, VA)
    z = corrected_z_star(effective, candidate["C"], candidate["w"])
    cov = corrected_covariance(effective, VA, z)
    maximum = holevo_interval_maximizer(effective, VA, candidate["C"], candidate["w"])
    corrected_residuals = {name: effective[name] - stored[name]
                          for name in ("mean_eta", "mean_sqrt_eta", "mean_eta_xi_total",
                                       "T_eff", "b", "xi_eff", "output_excess_noise")}
    corrected_residuals["Z_star"] = z - stored["Z_star"]
    corrected_residuals["chi_BE_worst_case"] = maximum["chi_BE"] - stored["chi_BE_worst_case"]
    if any(abs(value) > 1e-13 for value in corrected_residuals.values()):
        raise ValueError(f"Corrected one-point algebra regression failed: {corrected_residuals}")

    # These are sensitivity stages of one law, not separate evaluated protocols.
    def full_moments(label, a0, w_eq, variance):
        d = (w_eq / (2 * raw.sigma_s)) ** 2
        base = a0 * raw.eta_atm
        m1 = raw.P1 * base * d / (d + 1)
        mh = raw.P1 * math.sqrt(base) * d / (d + .5) * math.exp(-variance / 8)
        return dict(stage=label, A0=a0, w_eq=w_eq, lognormal_variance=variance,
                    mean_eta=m1, mean_sqrt_eta=mh, T_eff=mh * mh)

    point = physical["pointing"]
    stages = [
        full_moments("historical_full_support", point["A0"], point["omega_L_eq_m"], physical["v_sc"]),
        full_moments("change_aperture_convention_only", raw.A0, raw.w_eq, physical["v_sc"]),
        full_moments("then_change_to_raw_Rytov", raw.A0, raw.w_eq, raw.sigma_R2),
        dict(stage="then_cut_at_eta_one_without_renormalization",
             mean_eta=moments["raw_mean_eta"], mean_sqrt_eta=moments["raw_mean_sqrt_eta"],
             T_eff=moments["raw_mean_sqrt_eta"] ** 2),
        dict(stage="then_condition_active_preserve_atom",
             mean_eta=moments["mean_eta"], mean_sqrt_eta=moments["mean_sqrt_eta"],
             T_eff=effective["T_eff"]),
    ]
    for index, stage in enumerate(stages):
        stage["delta_Teff_from_previous"] = 0. if index == 0 else stage["T_eff"] - stages[index - 1]["T_eff"]
    full_quad = {}
    for q, name in ((0., "mass"), (.5, "mean_sqrt_eta"), (1., "mean_eta")):
        integral, error = fading._integrate_raw(q, upper=math.inf)
        value = raw.P0 + raw.P1 * integral if q == 0 else raw.P1 * integral
        expected = 1. if q == 0 else stages[2][name]
        full_quad[name] = dict(value=value, error_estimate=error,
                               residual_against_full_support_formula=value - expected)
    from scripts.calculate_channel_pdf_and_moments import _tail_probability
    old_tail_active = _tail_probability(physical["v_sc"], physical)

    physical_inputs = {key: physical[key] for key in (
        "wavelength_m", "h_hap_m", "h_uav_m", "link_length_m", "zenith_angle_rad",
        "wind_m_per_s", "cn2_ground_m_minus_two_thirds", "receiver_diameter_m",
        "beam_waist_m", "tau_zen", "sigma_h_m", "theta_jt_rad", "sigma_o_rad",
        "theta_fov_rad", "rho_m", "theta_div_rad",
    )}
    scientific_inputs = {
        "physical_inputs": physical_inputs,
        "common_physics_input_hash": _sha256_json(physical_inputs),
        "default_config_sha256": _sha256(ROOT / "configs/default.yaml"),
        "historical_pdf_coefficients": dict(
            B=point["A0"] * raw.eta_atm, chi2=(point["omega_L_eq_m"] / (2*raw.sigma_s))**2,
            lognormal_mean=-physical["v_sc"]/2, lognormal_variance=physical["v_sc"],
            A_ap=physical["A_ap"], sigma_X2=physical["v_sc"]/4,
            aperture_nu=point["nu"], w_L=point["omega_L_m"],
        ),
        "corrected_pdf_coefficients": raw.coefficients(),
        "mapping_trace": {
            "historical": "pointing_error.manuscript_pointing_parameters: nu uses w_L; scintillation uses v_sc=A_ap*sigma_R0^2",
            "corrected": "LiteralChannel.from_physical: nu uses w_L*sqrt(1+G_d); Eq10 uses sigma_R0^2",
        },
        "geometry_identity": "L=(h_H-h_U)/cos(zeta); same inputs and exact overrides in both producers",
        "rebuilt_source": dict(C=candidate["C"], w=candidate["w"], nu_raw=candidate["nu_raw"],
            VA=candidate["V_A"], computed_VA=float(ensemble.computed_va()[0]),
            ensemble_hash=candidate["ensemble_hash"], sum_probabilities=float(p.sum()),
            probabilities_sha256=hashlib.sha256(p.tobytes()).hexdigest(),
            complex_amplitudes_sha256=hashlib.sha256(alpha.tobytes()).hexdigest()),
        "producer_hashes": {rel: _sha256(ROOT / rel) for rel in producers},
        "input_hashes": {path.relative_to(ROOT).as_posix(): _sha256(path)
                        for path in (source_path, CORRECTED_JSON, SNAPSHOT_JSON, HISTORICAL_CSV)},
        "protection": dict(protected_files_verified=len(baseline["protected_hashes"]),
                           previous_ideal_outputs_verified=len(previous_outputs), changed=[]),
        "historical_evaluator_residuals": old_residuals,
        "historical_actual_covariance_output": old_security.covariance.matrix[0].tolist(),
        "historical_actual_symplectic_output": [
            float(value[0]) for value in (old_security.covariance.lambda1,
                                         old_security.covariance.lambda2,
                                         old_security.covariance.lambda3)],
        "historical_actual_numerical_repairs": old_security.diagnostics["numerical_repairs"],
        "corrected_current_producer_residuals": corrected_residuals,
        "corrected_covariance": cov,
        "correlation_interval_verification": maximum,
        "PDF_moment_stages_order_dependent": stages,
        "corrected_full_support_quadrature": full_quad,
        "historical_tail_independent_diagnostic": dict(
            active_tail_above_one=old_tail_active,
            mixed_tail_above_one=raw.P1*old_tail_active,
            retained_active_mass=1-old_tail_active,
            note="New read-only diagnostic of historical law; not used by historical objective",
        ),
    }
    scientific_inputs["historical_pdf_parameters_sha256"] = _sha256_json(scientific_inputs["historical_pdf_coefficients"])
    scientific_inputs["corrected_pdf_parameters_sha256"] = _sha256_json(scientific_inputs["corrected_pdf_coefficients"])
    return scientific_inputs


def evaluate() -> dict[str, object]:
    historical = _historical_row()
    snapshot = json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))
    corrected_root = json.loads(CORRECTED_JSON.read_text(encoding="utf-8"))
    corrected = corrected_root["record"]
    corrected_identity = corrected_root["identity"]
    old_channel = snapshot["reference_channel"]
    raw_channel = corrected_identity["raw_channel"]
    current_audit = _audit_current_point(corrected_root, historical, snapshot)

    for name, actual, expected in (
        ("source cache key", historical["source_cache_key"], corrected["source_cache_key"]),
        ("ensemble hash", historical["ensemble_hash"], corrected["ensemble_hash"]),
    ):
        if actual != expected:
            raise ValueError(f"{name} mismatch: {actual!r} != {expected!r}")
    for name, actual, expected in (
        ("nu_raw", float(historical["nu_raw"]), NU_RAW),
        ("V_A", float(historical["V_A"]), VA),
        ("C", float(historical["C"]), float(corrected["C"])),
        ("w", float(historical["w"]), float(corrected["w"])),
    ):
        if actual != expected:
            raise ValueError(f"{name} mismatch: {actual!r} != {expected!r}")

    old_t = float(historical["T_eff"])
    old_m1 = float(old_channel["mean_T_raw"])
    old_mh = float(old_channel["mean_sqrt_T_raw"])
    old_z_signal = 2.0 * math.sqrt(old_t) * float(corrected["C"])
    old_z_penalty = math.sqrt(2.0 * old_t * EPSILON_CH * float(corrected["w"]))
    old_z = old_z_signal - old_z_penalty
    old_cov = _covariance(old_t, EPSILON_CH, old_z)

    new_m1 = float(corrected["mean_eta"])
    new_mh = float(corrected["mean_sqrt_eta"])
    new_t = float(corrected["T_eff"])
    new_mn = float(corrected["mean_eta_xi_total"])
    new_noise = float(corrected["N_eff"])
    new_xi = float(corrected["xi_eff"])
    new_z = float(corrected["Z_star"])
    new_z_signal = 2.0 * new_mh * float(corrected["C"])
    new_z_penalty = math.sqrt(2.0 * new_noise * float(corrected["w"]))
    new_cov = _covariance(new_t, new_xi, new_z)

    old_fixed_noise = old_t * EPSILON_CH
    fading_noise = (new_m1 - new_t) * VA
    channel_noise = new_m1 * EPSILON_CH
    noise_from_three = (new_m1 - new_t) * VA + new_mn + new_m1 - 1.0 - float(corrected["chi_het"])
    raw_mh = float(corrected["raw_mean_sqrt_eta"])
    raw_m1 = float(corrected["raw_mean_eta"])
    raw_t = raw_mh * raw_mh
    raw_active_mass = float(corrected["active_retained_mass"])
    raw_total_mass = float(corrected["raw_probability_mass"])
    raw_tail_active = float(corrected["active_tail_probability"])
    raw_tail_total = float(corrected["discarded_raw_mass_quadrature"])

    old_i = float(historical["I_AB"])
    old_beta_i = float(historical["beta_I_AB"])
    old_chi = float(historical["chi_BE"])
    old_k = float(historical["SKR"])
    new_mix_i = float(corrected["I_AB"])
    new_mix_se = float(corrected["MI_diagnostics"]["stderr"])
    new_gauss = corrected["effective_Gaussian_approximation"]
    new_gauss_i = float(new_gauss["I_AB"])
    new_chi = float(corrected["chi_BE_at_Z_star"])
    mixture_delta_i = new_mix_i - old_i
    mixture_delta_beta_i = BETA * mixture_delta_i
    delta_chi = new_chi - old_chi
    gaussian_delta_i = new_gauss_i - old_i
    gaussian_delta_beta_i = BETA * gaussian_delta_i

    common_geometry = {
        "distance_km": DISTANCE_KM,
        "zeta_deg": float(old_channel["zeta_deg"]),
        "h_HAP_m": 20000.0,
        "h_UAV_m": 1000.0,
        "wavelength_m": 1.55e-6,
        "tau_zen": 0.92,
        "theta_div_full_rad": float(historical["theta_div_full_rad"]),
        "w0_m": float(historical["w0_m"]),
        "receiver_diameter_m": float(historical["D_r_m"]),
        "wind_m_per_s": 21.0,
        "cn2_ground_m_minus_two_thirds": 1e-14,
        "theta_jt_rad": 15.61e-6,
        "sigma_h_m": 1.0,
        "sigma_o_rad": 1.5e-3,
        "theta_fov_rad": 6.25e-3,
        "rho": 0.0,
        "phase_noise": "OFF",
        "AO": "OFF",
        "xi_ch": EPSILON_CH,
        "beta": BETA,
    }
    corrected_channel_parameter_hash = _sha256_json(raw_channel)
    prior_integrity = json.loads(OLD_INTEGRITY_JSON.read_text(encoding="utf-8"))
    checks = {
        "source_hash_identical": historical["source_cache_key"] == corrected["source_cache_key"],
        "ensemble_hash_identical": historical["ensemble_hash"] == corrected["ensemble_hash"],
        "source_C_exact_match": float(historical["C"]) == float(corrected["C"]),
        "source_w_exact_match": float(historical["w"]) == float(corrected["w"]),
        "common_base_geometry_recorded": abs(current_audit["physical_inputs"]["link_length_m"] - DISTANCE_KM * 1000) <= 1e-9,
        "raw_equation_10_unchanged": corrected["raw_equation_10_changed"] is False,
        "corrected_raw_full_mass_residual": float(corrected["raw_full_support_probability_mass"]) - 1.0,
        "corrected_physical_mass_residual": float(corrected["physical_pdf_mass"]) - 1.0,
        "corrected_third_moment_residual": float(corrected["third_moment_identity_residual"]),
        "corrected_Teff_residual": new_t - new_mh * new_mh,
        "corrected_moment_ordering": 0.0 <= new_t <= new_m1 <= 1.0,
        "corrected_noise_identity_residual": float(corrected["noise_consistency_residual"]),
        "corrected_eq20_residual": new_z - (new_z_signal - new_z_penalty),
        "historical_regression_residual": old_k - 0.07798099387393764,
        "historical_entropy_residual": old_cov["chi_BE"] - old_chi,
        "corrected_entropy_residual": new_cov["chi_BE"] - new_chi,
        "historical_covariance_physical": old_cov["physicality"],
        "corrected_covariance_physical": new_cov["physicality"],
        "historical_symplectic_min": min(old_cov["lambda_1"], old_cov["lambda_2"], old_cov["lambda_3"]),
        "corrected_symplectic_min": min(new_cov["lambda_1"], new_cov["lambda_2"], new_cov["lambda_3"]),
        "prior_ideal_integrity_receipt": prior_integrity.get("protected_changes") == []
        and prior_integrity.get("corrected_core_changed") is False
        and prior_integrity.get("historical_literal_cache_results_changed") is False,
    }
    numeric_residuals = {
        key: value for key, value in checks.items()
        if key.endswith("residual") or key.endswith("_min")
    }

    result = {
        "status": "CONFIGURATION_MISMATCH",
        "scope": "ONE_REFERENCE_CACHE_ONLY_ALGEBRAIC_DIAGNOSTIC",
        "reference": {"distance_km": DISTANCE_KM, "nu_raw": NU_RAW, "VA": VA,
                      "beta": BETA, "xi_ch": EPSILON_CH, "detector": "ideal_heterodyne",
                      "R": 1.0, "xi_det": 0.0, "chi_het": 1.0, "phase_noise": "OFF", "AO": "OFF"},
        "provenance": {
            "historical_channel_hash": historical["channel_hash"],
            "corrected_scientific_context_hash": corrected["scientific_context_hash"],
            "corrected_raw_channel_parameter_sha256": corrected_channel_parameter_hash,
            "source_cache_key": corrected["source_cache_key"],
            "ensemble_hash": corrected["ensemble_hash"],
            "source_payload_sha256": corrected_identity["source_payload_sha256"],
            "historical_csv": str(HISTORICAL_CSV.relative_to(ROOT)).replace("\\", "/"),
            "corrected_result": str(CORRECTED_JSON.relative_to(ROOT)).replace("\\", "/"),
        },
        "configuration_audit": {
            "current_producer_audit": current_audit,
            "common_base_geometry": common_geometry,
            "historical_pdf_parameters": {
                "eta_atm": float(old_channel["eta_atm"]), "A0": float(old_channel["A0"]),
                "w_eq": float(old_channel["omega_L_eq_m"]), "sigma_jt": float(old_channel["sigma_jt_m"]),
                "sigma_X2": float(old_channel["sigma_X2"]), "p_in": float(old_channel["p_in"]),
                "p_out": float(old_channel["p_out"]), "rho": 0.0,
                "convention": "closed_form_channel_moments_untruncated_raw_moments",
            },
            "corrected_pdf_parameters": {
                **raw_channel,
                "convention": "literal_Eq10_raw_Rytov_then_active_conditioning",
            },
            "discrepancy": [
                "Base geometry and exogenous jitter/AoA settings match.",
                "Derived PDF coefficients do not match: A0, w_eq and scintillation parameterization differ.",
                "Historical evaluator uses untruncated closed-form moments; corrected mode conditions active eta to (0,1].",
                "This is a model/convention mismatch, not evidence of floating-point failure.",
            ],
        },
        "pdf_and_moments": {
            "historical": {
                "mean_eta": old_m1, "mean_sqrt_eta": old_mh, "T_eff": old_t,
                "mean_eta_epsilon_ch_only": old_m1 * EPSILON_CH,
                "mean_eta_xi_total": None,
                "mean_eta_xi_total_note": "NOT USED BY HISTORICAL EVALUATOR; its covariance uses fixed epsilon=.0186.",
                "mean_eta_xi_total_if_corrected_ideal_identity_only": 2.0 + (EPSILON_CH - 1.0) * old_m1,
                "raw_active_mass_0_to_1": None,
                "raw_total_mass_0_to_1": None,
                "raw_tail_above_1": None,
                "physical_mass": None,
                "support_note": "Untruncated positive-support raw moments; cutoff/tail was not recorded by the historical caller.",
            },
            "corrected": {
                "P0": float(corrected["outage_atom"]), "P1": float(corrected["active_probability"]),
                "raw_active_mass_0_to_1": raw_active_mass,
                "raw_total_mass_0_to_1": raw_total_mass,
                "raw_probability_tail_above_1": raw_tail_total,
                "raw_active_tail_above_1": raw_tail_active,
                "raw_full_support_mass": float(corrected["raw_full_support_probability_mass"]),
                "physical_active_normalization": float(corrected["independent_normalized_active_mass"]),
                "physical_total_mass": float(corrected["physical_pdf_mass"]),
                "raw_mean_eta": raw_m1, "raw_mean_sqrt_eta": raw_mh,
                "raw_T_eff_before_conditioning": raw_t,
                "physical_mean_eta": new_m1, "physical_mean_sqrt_eta": new_mh,
                "physical_T_eff": new_t,
                "raw_missing_mass_identity_residual": (1.0 - raw_total_mass) - raw_tail_total,
                "conditioning_Teff_ratio": new_t / raw_t,
            },
            "comparison": {
                "mean_eta_difference": new_m1 - old_m1,
                "mean_sqrt_eta_difference": new_mh - old_mh,
                "T_eff_difference": new_t - old_t,
                "T_eff_relative_change": _relative_change(new_t, old_t),
                "conditioning_only_Teff_change_from_corrected_raw": new_t - raw_t,
                "conditioning_only_Teff_relative_change": _relative_change(new_t, raw_t),
            },
        },
        "noise": {
            "historical_fixed_objective_output_noise": old_fixed_noise,
            "N_fading": fading_noise,
            "N_channel": channel_noise,
            "N_eff": new_noise,
            "xi_eff": new_xi,
            "N_eff_from_three_moments": noise_from_three,
            "consistency_error": new_noise - noise_from_three,
            "fading_fraction_of_N_eff": fading_noise / new_noise,
            "fading_to_channel_ratio": fading_noise / channel_noise,
            "xi_ch_physical": EPSILON_CH,
        },
        "covariance": {
            "historical": {**old_cov, "Z_signal": old_z_signal, "Z_penalty": old_z_penalty},
            "corrected": {**new_cov, "Z_signal": new_z_signal, "Z_penalty": new_z_penalty},
            "differences": {
                key: new_cov[key] - old_cov[key]
                for key in ("a", "b", "Delta", "D", "lambda_1", "lambda_2", "lambda_3", "g_lambda_1", "g_lambda_2", "g_lambda_3", "S_AB", "S_conditional", "chi_BE")
            } | {"Z_signal": new_z_signal - old_z_signal, "Z_penalty": new_z_penalty - old_z_penalty,
               "Z_star": new_z - old_z, "b_minus_1": (new_cov["b"] - 1.0) - (old_cov["b"] - 1.0),
               "Z_star_squared": new_z * new_z - old_z * old_z},
        },
        "mutual_information": {
            "historical": {"I_AB": old_i, "standard_error": None, "beta_I_AB": old_beta_i,
                            "noise_variance_complex": 1.0 + old_fixed_noise / 2.0,
                            "method": "discrete_QAM_deterministic_GH8_product"},
            "corrected_effective_gaussian": {"I_AB": new_gauss_i, "standard_error": None,
                                              "beta_I_AB": BETA * new_gauss_i,
                                              "noise_variance_complex": float(new_gauss["sigma2_complex"]),
                                              "method": new_gauss["MI_method"],
                                              "quadrature_refinement": float(new_gauss["last_refinement_difference"])},
            "corrected_fading_mixture": {"I_AB": new_mix_i, "standard_error": new_mix_se,
                                          "beta_I_AB": BETA * new_mix_i,
                                          "method": corrected["MI_method"],
                                          "outage_atom_in_likelihood": True,
                                          "sampling_status": corrected["MI_diagnostics"]["status"]},
            "mixture_minus_effective_gaussian": new_mix_i - new_gauss_i,
            "mixture_difference_in_standard_errors": (new_mix_i - new_gauss_i) / new_mix_se,
        },
        "skr_decomposition": {
            "historical_K": old_k,
            "corrected_mixture_K": BETA * new_mix_i - new_chi,
            "corrected_effective_gaussian_K": BETA * new_gauss_i - new_chi,
            "mixture_delta_I_AB": mixture_delta_i,
            "mixture_delta_beta_I_AB": mixture_delta_beta_i,
            "delta_chi_BE": delta_chi,
            "mixture_delta_K": mixture_delta_beta_i - delta_chi,
            "mixture_sampling_SE_in_beta_I": BETA * new_mix_se,
            "mixture_decline_fraction_from_MI": (-mixture_delta_beta_i) / (-(mixture_delta_beta_i - delta_chi)),
            "mixture_decline_fraction_from_Holevo": delta_chi / (-(mixture_delta_beta_i - delta_chi)),
            "gaussian_delta_I_AB": gaussian_delta_i,
            "gaussian_delta_beta_I_AB": gaussian_delta_beta_i,
            "gaussian_delta_K": gaussian_delta_beta_i - delta_chi,
            "gaussian_decline_fraction_from_MI": (-gaussian_delta_beta_i) / (-(gaussian_delta_beta_i - delta_chi)),
            "gaussian_decline_fraction_from_Holevo": delta_chi / (-(gaussian_delta_beta_i - delta_chi)),
        },
        "validation": {"checks": checks, "numeric_residuals": numeric_residuals,
                        "all_boolean_checks_pass": all(value for key, value in checks.items() if isinstance(value, bool)),
                        "corrected_MI_precision_status": corrected["MI_diagnostics"]["status"],
                        "corrected_security_bound_status": corrected["validated_security_lower_bound"],
                        "protected_science_modified": False},
        "final_status": {
            "status": "CONFIGURATION_MISMATCH",
            "basis": [
                "The common geometric/channel inputs and source identity match.",
                "The two evaluators use different derived PDF coefficients and support/moment conventions.",
                "No numerical inconsistency was found in the stored algebraic reproduction.",
                "Corrected actual-mixture MI precision and rigorous continuous Holevo error enclosure remain unestablished.",
            ],
            "negative_corrected_K_interpretation": "Mathematically consistent signed diagnostic for the corrected one-point model; not a certified operational/security lower bound.",
        },
    }
    # Mathematical covariance sensitivities only; each is checked for physicality.
    channel_only_noise = new_m1 * EPSILON_CH
    channel_only_z = new_z_signal - math.sqrt(2 * channel_only_noise * float(corrected["w"]))
    controls = []
    for label, t, noise, fixed_z in (
        ("historical", old_t, old_fixed_noise, None),
        ("change_Teff_keep_historical_fixed_epsilon", new_t, new_t * EPSILON_CH, None),
        ("then_use_m1_xi_ch_without_fading", new_t, channel_only_noise, None),
        ("then_add_fading_to_b_keep_previous_Z", new_t, new_noise, channel_only_z),
        ("then_change_Z_penalty_to_corrected", new_t, new_noise, new_z),
    ):
        z_control = fixed_z if fixed_z is not None else 2 * math.sqrt(t)*float(corrected["C"]) - math.sqrt(2*noise*float(corrected["w"]))
        control = _covariance(t, noise/t, z_control)
        if not control["physicality"]:
            raise ValueError(f"Nonphysical sensitivity covariance: {label}")
        controls.append(dict(label=label, T_eff=t, noise_output=noise, **control))
    result["covariance_sensitivities"] = dict(
        interpretation="Order-dependent mathematical sensitivities; not protocols, SKRs, or security claims",
        rows=controls)
    pdf = result["pdf_and_moments"]
    pdf["historical"].update(
        raw_active_mass_0_to_1=current_audit["historical_tail_independent_diagnostic"]["retained_active_mass"],
        raw_total_mass_0_to_1=1-current_audit["historical_tail_independent_diagnostic"]["mixed_tail_above_one"],
        raw_tail_above_1=current_audit["historical_tail_independent_diagnostic"]["mixed_tail_above_one"],
        raw_full_support_mass=1.,
        support_note="Tail newly calculated from unchanged historical raw law; historical objective still uses full-support moments",
    )
    pdf["corrected"].update(
        raw_mean_definition="Unnormalized RETAINED integrals over 0<eta<=1, not full-support moments",
        raw_full_support_mean_eta=current_audit["PDF_moment_stages_order_dependent"][2]["mean_eta"],
        raw_full_support_mean_sqrt_eta=current_audit["PDF_moment_stages_order_dependent"][2]["mean_sqrt_eta"],
        raw_full_support_T_eff=current_audit["PDF_moment_stages_order_dependent"][2]["T_eff"],
        conditioning_divisor=raw_active_mass,
        raw_retained_mean_eta=raw_m1, raw_retained_mean_sqrt_eta=raw_mh,
        raw_retained_T_eff=raw_t,
    )
    result["covariance"]["relative_changes"] = {
        "a": _relative_change(new_cov["a"], old_cov["a"]),
        "b": _relative_change(new_cov["b"], old_cov["b"]),
        "Z_signal": _relative_change(new_z_signal, old_z_signal),
        "Z_penalty": _relative_change(new_z_penalty, old_z_penalty),
        "Z_star": _relative_change(new_z, old_z),
        "b_minus_1": _relative_change(new_cov["b"]-1, old_cov["b"]-1),
        "Z_star_squared": _relative_change(new_z*new_z, old_z*old_z),
    }
    result["covariance"]["historical"]["Z_star_squared"] = old_z*old_z
    result["covariance"]["corrected"]["Z_star_squared"] = new_z*new_z
    result["validation"]["checks"]["current_protection_hashes_match"] = not current_audit["protection"]["changed"]
    result["validation"]["checks"]["historical_actual_covariance_max_residual"] = max(
        abs(first - second) for actual, derived in zip(
            current_audit["historical_actual_covariance_output"], old_cov["Gamma_AB"])
        for first, second in zip(actual, derived))
    result["validation"]["checks"]["SKR_delta_identity_residual"] = (
        (result["skr_decomposition"]["corrected_mixture_K"] - old_k)
        - result["skr_decomposition"]["mixture_delta_K"])
    result["validation"]["all_boolean_checks_pass"] = all(
        value for value in result["validation"]["checks"].values() if isinstance(value, bool))
    result["validation"]["numeric_residuals"].update({
        key: value for key, value in result["validation"]["checks"].items()
        if key.endswith("residual")})
    result["provenance"]["diagnostic_producer_sha256"] = _sha256(Path(__file__))
    result["provenance"]["diagnostic_request_sha256"] = _sha256(Path(
        r"C:\Users\HP\.codex\attachments\f386aec4-dfab-449a-85f6-be325a3dfac3\Pasted text.txt"))
    return result


def main() -> int:
    import io
    import subprocess
    import unittest
    from datetime import datetime, timezone

    result = evaluate()
    if not result["validation"]["all_boolean_checks_pass"]:
        raise ValueError("One-point validation failed")
    residuals = result["validation"]["checks"]
    if any(abs(value) > 1e-13 for key, value in residuals.items() if key.endswith("residual")):
        raise ValueError("Algebraic residual exceeds diagnostic tolerance")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "diagnostic_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_negative_skr_diagnostic")
    test_result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (OUTPUT_DIR / "test_output.txt").write_text(stream.getvalue(), encoding="utf-8", newline="\n")
    audit = result["configuration_audit"]["current_producer_audit"]
    if not test_result.wasSuccessful():
        raise ValueError("Independent diagnostic tests failed")
    _verify_hashes(audit["input_hashes"])
    _verify_hashes(audit["producer_hashes"])
    protected = json.loads((CORRECTED_JSON.parent / "startup_manifest.json").read_text(encoding="utf-8"))
    _verify_hashes(protected["protected_hashes"])
    report_path = ROOT / "docs/NEGATIVE_SKR_DIAGNOSTIC_REPORT_VI.md"
    files = [Path(__file__), ROOT / "tests/test_negative_skr_diagnostic.py", report_path,
             OUTPUT_DIR / "diagnostic_result.json", OUTPUT_DIR / "test_output.txt"]
    receipt = dict(
        captured_utc=datetime.now(timezone.utc).isoformat(),
        scope=result["scope"], status=result["status"], candidate=result["reference"],
        branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        producer_and_output_sha256={path.relative_to(ROOT).as_posix(): _sha256(path) for path in files},
        input_sha256=audit["input_hashes"], protected_files_verified=audit["protection"],
        tests=dict(command="in-process unittest: tests.test_negative_skr_diagnostic",
                   count=test_result.testsRun, failures=len(test_result.failures),
                   errors=len(test_result.errors), status="CURRENTLY_VERIFIED_PASS"),
        algebraic_residuals=result["validation"]["numeric_residuals"],
        preserved=["historical/literal/corrected evaluators and configs", "Eq10/Eq20",
                   "existing source/objective caches and results", "frozen specification"],
        NOT_RUN=["AP/source moment recomputation", "AO", "ObjectiveC restart",
                 "182-candidate evaluation", "26-distance sweep", "new Monte Carlo",
                 "training/heldout/final-test/publication", "commit/push"],
        unresolved=result["validation"]["corrected_security_bound_status"],
        frozen_sha256=_sha256(ROOT / "docs/FINAL_MODEL_SPEC.md"),
        frozen_historical_hash_discrepancy="PREEXISTING_UNCHANGED",
    )
    (OUTPUT_DIR / "diagnostic_receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False)+"\n",
        encoding="utf-8", newline="\n")
    print(stream.getvalue())
    print(OUTPUT_DIR / "diagnostic_result.json")
    print("status =", result["status"])
    print("delta_K_mixture =", result["skr_decomposition"]["mixture_delta_K"])
    print("fading_fraction_of_N_eff =", result["noise"]["fading_fraction_of_N_eff"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
