"""Record the converged PS+V_A source moments and one exact median full-Z row."""

from __future__ import annotations

from decimal import Decimal, getcontext
import hashlib
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import diagnose_ps_va_ap_worker as localization  # noqa: E402
from scripts import run_analysis_figures as runner  # noqa: E402


INPUT_ARTIFACT = ROOT / "results" / "ps_va_ap_worker_localization_20260912.json"
DIAGNOSTIC_ARTIFACT = ROOT / "results" / "ps_va_source_moments_1050_20260912.json"
ACCEPTANCE_ARTIFACT = ROOT / "results" / "ps_va_source_moments_1250_1450_20260912.json"
REPAIRED_ANALYSIS = ROOT / "results" / "repaired_full_z_objective_analysis_20260911.json"
WORKER = ROOT / "scripts" / "full_support_c4_worker.py"
MODEL_SPEC = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
OUTPUT = ROOT / "results" / "PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json"
MEDIAN_INDEX = localization.MEDIAN_ANCHOR_INDEX


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _float(value: torch.Tensor | float) -> float:
    return float(value.detach()) if isinstance(value, torch.Tensor) else float(value)


def _scalar(values: torch.Tensor, index: int = 0) -> float:
    return float(values.reshape(-1)[index].detach())


def _relative_delta(left: Decimal, right: Decimal) -> Decimal:
    return abs(left - right) / max(abs(left), abs(right))


def _source_convergence(rows: list[dict[str, object]]) -> dict[str, object]:
    getcontext().prec = 200
    first, second = rows
    metrics: dict[str, object] = {}
    passed = True
    for name in ("C", "w"):
        left = Decimal(str(first[name]))
        right = Decimal(str(second[name]))
        absolute = abs(left - right)
        relative = _relative_delta(left, right)
        tolerance = Decimal("1e-7") + Decimal("1e-6") * max(abs(left), abs(right))
        metric = {
            "value_1250": str(left),
            "value_1450": str(right),
            "absolute_delta": str(absolute),
            "relative_delta": str(relative),
            "frozen_tolerance": str(tolerance),
            "pass": absolute <= tolerance,
            "stable_digits": "serialized_equal" if absolute == 0 else max(
                0, int(-relative.log10())
            ),
        }
        metrics[name] = metric
        passed = passed and bool(metric["pass"])
    return {
        "criteria": "absolute_delta <= 1e-7 + 1e-6 * max(abs(value_1250), abs(value_1450))",
        "pass": passed,
        "metrics": metrics,
    }


def _security_row(
    ensemble: runner.Ensemble,
    frozen: dict[str, object],
    exact_c: float,
    exact_w: float,
) -> dict[str, object]:
    transmittance = torch.tensor([float(frozen["T"])], dtype=torch.float64)
    epsilon_base = torch.tensor([float(frozen["epsilon_base"])], dtype=torch.float64)
    epsilon_total = epsilon_base + runner.PHASE_COEFFICIENT * ensemble.computed_va()
    standard_noise = runner.standard_complex_noise(
        (1, 256, runner.ANCHOR_NOISE_SAMPLES),
        generator=torch.Generator(device="cpu").manual_seed(
            runner.existing_case.AWGN_SEED + 1
        ),
        device=torch.device("cpu"),
    )
    correlations = torch.tensor([exact_c], dtype=torch.float64)
    w_raw = torch.tensor([exact_w], dtype=torch.float64)
    with torch.no_grad():
        mutual_information = runner.discrete_mutual_information(
            ensemble,
            transmittance,
            epsilon_total,
            noise_samples_per_symbol=standard_noise.shape[-1],
            standard_noise_samples=standard_noise,
            noise_sample_chunk_size=standard_noise.shape[-1],
        )
        holevo = runner._holevo_from_source_moments(
            ensemble,
            transmittance,
            epsilon_total,
            coherent_correlation=correlations,
            w_raw=w_raw,
            tau=None,
            tau_trace=ensemble.probabilities.sum(dim=-1),
            require_supported_symmetry=True,
            symmetry_tolerance=1.0e-8,
            physicality_tolerance=1.0e-10,
            diagnostics={
                "backend": "current_full_Z_exact_PS_VA_MEDIAN",
                "artifact_class": "PS_VA_SOURCE_MOMENTS_CONVERGED",
                "phase_disabled": True,
                "c_phi": runner.PHASE_COEFFICIENT,
                "epsilon_total_definition": runner.EPSILON_TOTAL_DEFINITION,
            },
            z_grid_size=runner.SECURITY_Z_GRID_SIZE,
            z_refinement_steps=runner.SECURITY_Z_REFINEMENT_STEPS,
        )
        raw_key = runner.BETA * mutual_information - holevo.chi_be

    lower = _scalar(holevo.diagnostics["Z_L"])
    upper = _scalar(holevo.diagnostics["Z_U"])
    selected = _scalar(holevo.z)
    result = {
        "T": float(frozen["T"]),
        "epsilon_base": float(frozen["epsilon_base"]),
        "epsilon_total": _scalar(epsilon_total),
        "V_A": _scalar(ensemble.computed_va()),
        "Z_minus": _scalar(holevo.diagnostics["Z_minus"]),
        "Z_plus": _scalar(holevo.diagnostics["Z_plus"]),
        "Z_phys": _scalar(holevo.diagnostics["Z_phys"]),
        "Z_L": lower,
        "Z_U": upper,
        "Z_star": selected,
        "I_AB": _scalar(mutual_information),
        "beta_I_AB": runner.BETA * _scalar(mutual_information),
        "beta": runner.BETA,
        "chi_BE": _scalar(holevo.chi_be),
        "raw_K": _scalar(raw_key),
        "interval_check": lower <= selected <= upper,
        "maximizing_location": holevo.diagnostics["maximizing_location"][0],
        "security_domain_valid": bool(holevo.diagnostics["security_domain_valid"][0]),
        "numerical_repairs": list(holevo.diagnostics["numerical_repairs"]),
        "solver": {
            "z_grid_size": runner.SECURITY_Z_GRID_SIZE,
            "z_refinement_steps": runner.SECURITY_Z_REFINEMENT_STEPS,
            "method": "fixed_grid_all_cells_golden_section",
        },
    }
    if not result["interval_check"]:
        raise RuntimeError("selected full-Z point escaped the declared interval")
    return result


def main() -> None:
    localization_artifact = json.loads(INPUT_ARTIFACT.read_text(encoding="utf-8"))
    diagnostic_artifact = json.loads(DIAGNOSTIC_ARTIFACT.read_text(encoding="utf-8"))
    acceptance_artifact = json.loads(ACCEPTANCE_ARTIFACT.read_text(encoding="utf-8"))
    repaired_analysis = json.loads(REPAIRED_ANALYSIS.read_text(encoding="utf-8"))
    frozen = localization_artifact["cases"]["ps_va"]["frozen_input"]
    if diagnostic_artifact["status"] != "DIAGNOSTIC_ONLY":
        raise RuntimeError("1050 artifact is not diagnostic-only")
    if acceptance_artifact["status"] != "FULL_SUPPORT_CONVERGED":
        raise RuntimeError("1250/1450 acceptance artifact did not converge")
    acceptance_rows = acceptance_artifact["rows"]
    if [row["digits"] for row in acceptance_rows] != [1250, 1450]:
        raise RuntimeError("acceptance artifact does not contain exactly 1250/1450 rows")
    diagnostic_rows = diagnostic_artifact["rows"]
    if [row["digits"] for row in diagnostic_rows] != [1050]:
        raise RuntimeError("diagnostic artifact does not contain exactly the 1050 row")

    source_convergence = _source_convergence(acceptance_rows)
    if not source_convergence["pass"]:
        raise RuntimeError("frozen source-moment convergence criteria failed")

    transmitter, loaded_frozen = localization._load_transmitter(
        "ps_va", ROOT / frozen["checkpoint"]
    )
    if loaded_frozen["direct_input_hash"] != frozen["direct_input_hash"]:
        raise RuntimeError("frozen input changed while reloading checkpoint")
    with torch.no_grad():
        ensemble = transmitter(
            torch.tensor([float(frozen["T"])], dtype=torch.float64),
            torch.tensor([float(frozen["epsilon_base"])], dtype=torch.float64),
        )
        surrogate_c, surrogate_w, _ = runner._surrogate_batch(ensemble)

    exact_row = acceptance_rows[-1]
    exact_c_text = str(exact_row["C"])
    exact_w_text = str(exact_row["w"])
    exact_c = float(exact_c_text)
    exact_w = float(exact_w_text)
    surrogate = {
        "C": _scalar(surrogate_c),
        "w": _scalar(surrogate_w),
    }
    source_comparison = {
        "exact": {"C": exact_c_text, "w": exact_w_text, "digits": 1450},
        "surrogate": surrogate,
        "C_absolute_delta": abs(surrogate["C"] - exact_c),
        "C_relative_delta": abs(surrogate["C"] - exact_c) / max(abs(exact_c), 1.0e-40),
        "w_absolute_delta": abs(surrogate["w"] - exact_w),
        "w_relative_delta": abs(surrogate["w"] - exact_w) / max(abs(exact_w), 1.0e-40),
    }
    security = _security_row(ensemble, frozen, exact_c, exact_w)

    reference_row = repaired_analysis["exact_three_state_check"]["rows"][MEDIAN_INDEX - 2]
    if reference_row["label"] != "median":
        raise RuntimeError("repaired-objective median reference row is not index 3")
    if reference_row["T"] != frozen["T"] or reference_row["epsilon_base"] != frozen["epsilon_base"]:
        raise RuntimeError("median ranking reference does not match frozen channel state")
    comparison_scores = {
        "ps_va": security["raw_K"],
        "full": float(reference_row["methods"]["full"]["raw_K"]),
        "mb": float(reference_row["methods"]["mb"]["raw_K"]),
    }
    ordered = sorted(comparison_scores, key=lambda key: (-comparison_scores[key], key))
    winner = {
        "ps_va": "PS_VA_MEDIAN_BEST",
        "full": "FULL_MEDIAN_BEST",
        "mb": "MB_MEDIAN_BEST",
    }[ordered[0]]
    if len({comparison_scores[key] for key in comparison_scores}) != 3:
        winner = "MEDIAN_RANKING_UNRESOLVED"

    payload = {
        "artifact_class": "PS_VA_SOURCE_MOMENTS_CONVERGED",
        "status": "PS_VA_SOURCE_MOMENTS_CONVERGED",
        "classification": winner,
        "scope": "one frozen repaired-objective PS+V_A median candidate and one median full-Z point",
        "frozen_ladder": {
            "decimal_digits": [1050, 1250, 1450],
            "diagnostic_only": [1050],
            "acceptance_pair": [1250, 1450],
            "forbidden_after_ladder": [1600, 2000, "adaptive mixed precision", "dense 256x256", "Arb", "retraining"],
        },
        "candidate_freeze": {
            "checkpoint": frozen["checkpoint"],
            "checkpoint_sha256": frozen["checkpoint_sha256"],
            "direct_input_hash": frozen["direct_input_hash"],
            "probability_hash": _canonical_hash(
                {"q_float64_hex": frozen["serialized"]["q_float64_hex"]}
            ),
            "constellation_hash": frozen["constellation_hash"],
            "full_constellation_hash": frozen["full_constellation_hash"],
            "T": frozen["T"],
            "T_float64_hex": frozen["T_float64_hex"],
            "epsilon_base": frozen["epsilon_base"],
            "epsilon_base_float64_hex": frozen["epsilon_base_float64_hex"],
            "epsilon_total": frozen["epsilon_base"],
            "epsilon_total_float64_hex": frozen["epsilon_base_float64_hex"],
            "epsilon_total_definition": runner.EPSILON_TOTAL_DEFINITION,
            "phase_disabled": True,
            "c_phi": runner.PHASE_COEFFICIENT,
            "V_A": frozen["V_A"],
            "V_A_float64_hex": frozen["V_A_float64_hex"],
            "q_float64_hex": frozen["serialized"]["q_float64_hex"],
            "full_amplitudes_float64_hex": frozen["serialized"]["full_amplitudes_float64_hex"],
            "q_count": len(frozen["serialized"]["q_float64_hex"]),
            "full_amplitude_count": len(frozen["serialized"]["full_amplitudes_float64_hex"]),
            "q_sum": frozen["q_sum"],
            "q_min": frozen["q_min"],
            "q_max": frozen["q_max"],
            "unique_amplitudes": frozen["unique_amplitudes"],
            "channel_state": {"T": frozen["T"], "epsilon_base": frozen["epsilon_base"], "phase_disabled": True},
        },
        "input_verification": {
            "localization_artifact": str(INPUT_ARTIFACT.relative_to(ROOT)),
            "localization_artifact_sha256": _sha256(INPUT_ARTIFACT),
            "reloaded_direct_input_hash_match": True,
            "q_positive": frozen["q_min"] > 0.0,
            "q_sum_error": abs(float(frozen["q_sum"]) - 1.0),
            "unique_256": frozen["unique_amplitudes"] == 256,
            "c4_probability_max_error": frozen["c4_probability_max_error"],
            "c4_amplitude_max_error": frozen["c4_amplitude_max_error"],
        },
        "provenance": {
            "worker": str(WORKER.relative_to(ROOT)),
            "worker_sha256": _sha256(WORKER),
            "model_spec": str(MODEL_SPEC.relative_to(ROOT)),
            "model_spec_sha256": _sha256(MODEL_SPEC),
            "diagnostic_artifact": str(DIAGNOSTIC_ARTIFACT.relative_to(ROOT)),
            "diagnostic_artifact_sha256": _sha256(DIAGNOSTIC_ARTIFACT),
            "acceptance_artifact": str(ACCEPTANCE_ARTIFACT.relative_to(ROOT)),
            "acceptance_artifact_sha256": _sha256(ACCEPTANCE_ARTIFACT),
            "median_ranking_reference": str(REPAIRED_ANALYSIS.relative_to(ROOT)),
            "median_ranking_reference_sha256": _sha256(REPAIRED_ANALYSIS),
            "full_Z_implementation": "src/cvqkd/holevo.py::_holevo_from_source_moments",
            "full_Z_grid_size": runner.SECURITY_Z_GRID_SIZE,
            "full_Z_refinement_steps": runner.SECURITY_Z_REFINEMENT_STEPS,
            "beta": runner.BETA,
            "anchor_noise_samples": runner.ANCHOR_NOISE_SAMPLES,
            "anchor_noise_seed": runner.existing_case.AWGN_SEED + 1,
        },
        "runtime": {
            "1050_wall_seconds": diagnostic_artifact["instrumentation_runtime_seconds"],
            "1250_1450_combined_wall_seconds": acceptance_artifact["instrumentation_runtime_seconds"],
            "1250_solve_only_seconds": sum(
                call["runtime_seconds"]
                for call in acceptance_artifact["instrumentation"]["rows"][0]["solve_calls"]
            ),
            "1450_solve_only_seconds": sum(
                call["runtime_seconds"]
                for call in acceptance_artifact["instrumentation"]["rows"][1]["solve_calls"]
            ),
            "per_precision_wall_time_status": (
                "1050 measured separately; 1250 and 1450 were executed as one "
                "acceptance process and only their combined wall time was captured"
            ),
        },
        "source_moment_rows": {
            "1050": diagnostic_artifact,
            "1250_1450": acceptance_artifact,
        },
        "source_moment_convergence": source_convergence,
        "authoritative_source_moments": {
            "C": exact_c_text,
            "w": exact_w_text,
            "digits": 1450,
            "rank": exact_row["rank"],
            "resolved": exact_row["resolved"],
        },
        "exact_vs_surrogate_source_moments": source_comparison,
        "median_full_Z_exact": security,
        "median_ranking": {
            "scores_raw_K": comparison_scores,
            "order_best_to_worst": ordered,
            "classification": winner,
            "full_and_mb_source": "existing exact median row in repaired_full_z_objective_analysis_20260911.json",
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUTPUT), "sha256": _sha256(OUTPUT)}))


if __name__ == "__main__":
    main()
