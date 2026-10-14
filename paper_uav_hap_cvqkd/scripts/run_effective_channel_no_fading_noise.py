"""Exactly one effective-Gaussian reference, with existing source moments only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MODEL = "effective_channel_no_fading_noise"
OUTPUT = ROOT / "results" / MODEL / "reference_20261013"
CONFIG = ROOT / "configs" / (MODEL + ".json")
SOURCE = ROOT / "results/exact_mb_test2/exact_source_cache/77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c.json"
IDEAL = ROOT / "results/manuscript_corrected_3moments/ideal_heterodyne_reference_20261013/reference_result.json"
DIAGNOSTIC = ROOT / "results/manuscript_corrected_3moments/negative_skr_diagnostic_20261013/diagnostic_result.json"
STATE = ["docs/EVIDENCE.md", "docs/DECISION_LOG.md", "docs/PROJECT_STATE.md",
         "docs/NEXT_ACTIONS.md", ".agent/SESSION_HANDOFF.md"]
NEW = ["scripts/run_effective_channel_no_fading_noise.py", "src/effective_channel_no_fading_noise.py",
       "configs/effective_channel_no_fading_noise.json", "tests/test_effective_channel_no_fading_noise.py",
       "docs/EFFECTIVE_CHANNEL_NO_FADING_NOISE_REPORT_VI.md"]
EXPECTED = dict(scientific_model=MODEL, distance_km=21.9393102292, nu_raw=.165, VA=5.5,
    xi_ch=.0186, beta_rec=.95, R=1., xi_det=0., chi_het=1., phase_noise="OFF", AO="OFF",
    noise_model="xi_eff=xi_ch;N_eff=T_eff*xi_ch", MI_GH_orders=[8, 16, 32],
    holevo_target="direct_Z_star_diagnostic",
    interpretation="effective Gaussian approximation ignoring fading-induced variance")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def verify_hashes(expected):
    changed = [p for p, digest in expected.items()
               if not (ROOT / p).is_file() or sha256(ROOT / p) != digest]
    if changed:
        raise ValueError(f"Protected input/producer changed: {changed}")
    return changed


def prepare():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    paths = [p for folder in ["src", "scripts", "configs", "tests", "results", "docs", ".agent"]
             for p in (ROOT / folder).rglob("*") if p.is_file()
             and "__pycache__" not in p.parts and OUTPUT not in p.parents
             and p.relative_to(ROOT).as_posix() not in STATE + NEW]
    snapshot = dict(captured_utc=datetime.now(timezone.utc).isoformat(),
        branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        initial_git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        initial_git_diff=subprocess.check_output(["git", "diff"], cwd=ROOT).decode("utf-8"),
        protected_hashes={p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(paths)},
        state_baseline={p: (ROOT / p).read_text(encoding="utf-8") for p in STATE},
        authority="Explicit user decision: remove fading variance in a separate one-point Gaussian diagnostic",
        reference=EXPECTED, frozen_sha256=sha256(ROOT / "docs/FINAL_MODEL_SPEC.md"))
    write_new(OUTPUT / "startup_manifest.json", snapshot)
    print("Prepared protected files:", len(paths))


def evaluate_reference(settings):
    if settings != EXPECTED:
        raise ValueError("This entry permits only the user-authorized reference configuration")
    from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
    from scripts.run_manuscript_literal_3moments import verified_candidate
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    from src.manuscript_corrected_3moments import PhysicalFadingDistribution
    from src.manuscript_corrected_evaluator import validate_cached_candidate
    from src.manuscript_literal_3moments import LiteralChannel
    from src.effective_channel_no_fading_noise import evaluate_candidate

    previous = json.loads(IDEAL.read_text(encoding="utf-8"))
    prior = previous["identity"]
    verify_hashes(dict(prior["implementations"],
        **{"configs/default.yaml": prior["default_config_sha256"],
           "scripts/run_manuscript_corrected_ideal_reference.py": prior["ideal_reference_runner_sha256"]}))
    if json_hash(prior) != previous["record"]["scientific_context_hash"]:
        raise ValueError("Stored corrected scientific context mismatch")
    if sha256(SOURCE) != prior["source_payload_sha256"]:
        raise ValueError("Source cache bytes mismatch")
    config = unconstrained_config()
    candidate = verified_candidate(SOURCE, config)
    ensemble = validate_cached_candidate(candidate)
    if candidate["nu_raw"] != settings["nu_raw"] or candidate["V_A"] != settings["VA"]:
        raise ValueError("Source parameter mismatch")
    if candidate["ensemble_hash"] != prior["ensemble_hash"]:
        raise ValueError("Prior/current ensemble mismatch")
    vertical = config["channel"]["h_hap_m"] - config["channel"]["h_uav_m"]
    physical = derive_physical_inputs(.92,
        zenith_angle_rad_override=math.acos(vertical/(1000*settings["distance_km"])),
        aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
    raw = LiteralChannel.from_physical(physical)
    if raw.__dict__ != prior["raw_channel"]:
        raise ValueError("Raw Equation (10) physical inputs changed")
    fading = PhysicalFadingDistribution(raw)
    moments = fading.moments(R=1., xi_det=0., xi_ch=settings["xi_ch"])
    retained = ["mean_eta", "mean_sqrt_eta", "mean_eta_xi_total",
                "physical_probability_mass", "raw_probability_mass", "outage_atom"]
    residuals = {p: moments[p]-previous["record"][p] for p in retained}
    if any(value != 0 for value in residuals.values()):
        raise ValueError(f"Preserved channel moments changed: {residuals}")
    record = evaluate_candidate(candidate, moments, config)
    record.update(distance_km=settings["distance_km"], nu_raw=candidate["nu_raw"],
                  C=candidate["C"], w=candidate["w"], ensemble_hash=candidate["ensemble_hash"],
                  source_cache_key=candidate["source_cache_key"],
                  channel_moment_preservation_residuals=residuals, raw_channel=raw.__dict__)
    p = ensemble.probabilities.detach().cpu().numpy().reshape(-1)
    alpha = ensemble.amplitudes.detach().cpu().numpy().reshape(-1)
    identities = dict(mode=MODEL, settings=settings, raw_channel=raw.__dict__,
        source_payload_sha256=sha256(SOURCE), ensemble_hash=candidate["ensemble_hash"],
        source_C_hex=candidate["C"].hex(), source_w_hex=candidate["w"].hex(),
        PMF_sha256=hashlib.sha256(p.tobytes()).hexdigest(),
        amplitudes_sha256=hashlib.sha256(alpha.tobytes()).hexdigest(),
        previous_corrected_context=previous["record"]["scientific_context_hash"],
        implementations={**prior["implementations"], **{name: sha256(ROOT / name) for name in NEW[:3]}},
        new_config_sha256=sha256(CONFIG), default_config_sha256=sha256(ROOT/"configs/default.yaml"))
    record["scientific_context_hash"] = json_hash(identities)
    audit = json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))
    corrected = previous["record"]
    if audit["provenance"]["ensemble_hash"] != candidate["ensemble_hash"]:
        raise ValueError("Comparison source mismatch")
    comparisons = [
        dict(mode="historical", interpretation="Stored original untruncated scalar effective channel",
             **{key: audit["covariance"]["historical"][key] for key in ["a", "b"]},
             T_eff=audit["pdf_and_moments"]["historical"]["T_eff"], xi_eff=.0186,
             Z_star=audit["covariance"]["historical"]["Z"],
             lambda_1=audit["covariance"]["historical"]["lambda_1"],
             lambda_2=audit["covariance"]["historical"]["lambda_2"],
             lambda_3=audit["covariance"]["historical"]["lambda_3"],
             I_AB=audit["mutual_information"]["historical"]["I_AB"],
             chi_BE=audit["covariance"]["historical"]["chi_BE"],
             SKR=audit["skr_decomposition"]["historical_K"], MI_standard_error=None),
    ]
    for kind, mi, skr, se in [
        ("effective_Gaussian", corrected["effective_Gaussian_approximation"]["I_AB"],
         corrected["effective_Gaussian_approximation"]["K_at_Z_star"], None),
        ("actual_fading_mixture", corrected["I_AB"], corrected["K_at_Z_star"],
         corrected["MI_diagnostics"]["stderr"])]:
        comparisons.append(dict(mode="manuscript_corrected_3moments_"+kind,
            interpretation="Stored comparison; Gaussian surrogate/MC mixture distinguished",
            **{key: corrected[key] for key in ["T_eff", "xi_eff", "a", "b", "Z_star",
                                               "lambda_1", "lambda_2", "lambda_3"]},
            I_AB=mi, chi_BE=corrected["chi_BE_at_Z_star"], SKR=skr, MI_standard_error=se))
    comparisons.append(dict(mode=MODEL, interpretation=settings["interpretation"],
        **{key:record[key] for key in ["T_eff","xi_eff","a","b","Z_star",
                                      "lambda_1","lambda_2","lambda_3","I_AB","chi_BE","SKR"]},
        MI_standard_error=None))
    return dict(identity=identities, record=record, comparisons=comparisons,
                input_hashes={path.relative_to(ROOT).as_posix(): sha256(path)
                              for path in (SOURCE, IDEAL, DIAGNOSTIC, CONFIG)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if args.prepare_only:
        prepare()
        return 0
    baseline = json.loads((OUTPUT/"startup_manifest.json").read_text(encoding="utf-8"))
    verify_hashes(baseline["protected_hashes"])
    import torch
    torch.set_num_threads(1)
    settings = json.loads(CONFIG.read_text(encoding="utf-8"))
    write_new(OUTPUT/"execution_started.json", dict(scope="ONE_REFERENCE_ONLY",
                                                   config_sha256=sha256(CONFIG)))
    result = evaluate_reference(settings)
    write_new(OUTPUT/"reference_result.json", result)
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName("tests.test_effective_channel_no_fading_noise"))
    with (OUTPUT/"test_output.txt").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(log.getvalue())
    changes = verify_hashes(baseline["protected_hashes"])
    if not tests.wasSuccessful():
        raise ValueError(log.getvalue())
    outputs = [p for p in OUTPUT.iterdir() if p.is_file()]
    receipt = dict(status="CURRENTLY_VERIFIED_PASS", model=MODEL, tests_run=tests.testsRun,
        failures=len(tests.failures), errors=len(tests.errors),
        protected_files=len(baseline["protected_hashes"]), protected_changes=changes,
        output_sha256={p.relative_to(ROOT).as_posix(): sha256(p) for p in outputs},
        producer_sha256={name:sha256(ROOT/name) for name in NEW[:4]},
        input_hashes=result["input_hashes"], reference_candidates_evaluated=1,
        AP_AO_new_MC_sweep_restart_commit_push="NOT_RUN",
        validated_fading_security_lower_bound="NOT_ESTABLISHED",
        frozen_sha256=sha256(ROOT/"docs/FINAL_MODEL_SPEC.md"),
        frozen_historical_discrepancy="PREEXISTING_UNCHANGED")
    write_new(OUTPUT/"validation_receipt.json", receipt)
    print(log.getvalue())
    record = result["record"]
    for name in ["T_eff","xi_eff","a","b","Z_star","lambda_1","lambda_2","lambda_3","I_AB","chi_BE","SKR"]:
        print(name, "=", record[name])
    print("Interpretation:", settings["interpretation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
