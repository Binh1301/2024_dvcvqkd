"""Run the bounded GS-real, GS-imaginary, and V_A C4 tangent study.

This runner is deliberately forward-only.  It reuses the existing production
transmitter map for target points and the corrected AP worker for the central
finite-difference reference.  Each target direction is checkpointed before
the next direction is allowed to start.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import mpmath as mp
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# These helpers own the already validated production map and corrected worker.
# Importing this module does not call its reverse path; this runner never calls
# source_moments_vjp, a full-Z backward, or an optimizer.
from scripts.validate_corrected_ap_custom_backward import (  # noqa: E402
    COMBINED_A,
    COMBINED_B,
    ENSEMBLE_HASH,
    _fixture_inputs,
    _generic_ap_row,
    _target_direction,
    _target_directional_inputs,
    _target_structure_record,
    _worker_row,
)
from src.cvqkd.c4_constrained_tangent import (  # noqa: E402
    FullSupportUnresolved,
    forward_tangent,
)
from src.modulation.qam256 import (  # noqa: E402
    expand_c4_orbit_masses,
    expand_c4_orbit_values,
)


DIRECTIONS = ("gs_real", "gs_imag", "va")
CHEAP_DIGITS = 70
CHEAP_H = mp.mpf("1e-5")
TARGET_DIGITS = 800
TARGET_H = mp.mpf("1e-4")
CHEAP_RELATIVE_TOLERANCE = mp.mpf("1e-8")
TARGET_RELATIVE_TOLERANCE = mp.mpf("1e-6")
NEAR_ZERO_SCALE = mp.mpf("1e-40")
EXPECTED_PS_ARTIFACT = ROOT / "results" / "c4_constrained_forward_tangent_20260911.json"
DEFAULT_OUTPUT = ROOT / "results" / "c4_remaining_forward_tangents_20260911.json"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string(value: Any, digits: int = 50) -> str:
    return mp.nstr(value if isinstance(value, (mp.mpf, mp.mpc)) else mp.mpf(value), digits)


def _relative(observed: mp.mpf, reference: mp.mpf) -> mp.mpf:
    return abs(observed - reference) / max(abs(reference), NEAR_ZERO_SCALE)


def _comparison(observed: mp.mpf, reference: mp.mpf, tolerance: mp.mpf) -> dict[str, Any]:
    absolute = abs(observed - reference)
    near_zero = abs(reference) < NEAR_ZERO_SCALE
    relative = _relative(observed, reference)
    return {
        "observed": _string(observed),
        "reference": _string(reference),
        "absolute_error": _string(absolute, 30),
        "relative_error": _string(relative, 30),
        "near_zero_reference": near_zero,
        "tolerance": _string(tolerance, 10),
        "passes": bool(absolute <= tolerance if near_zero else relative <= tolerance),
    }


def _git_metadata() -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "dirty": bool(run("status", "--porcelain")),
    }


def _ps_reference() -> dict[str, Any]:
    if not EXPECTED_PS_ARTIFACT.exists():
        raise FileNotFoundError(f"validated PS tangent artifact is missing: {EXPECTED_PS_ARTIFACT}")
    payload = json.loads(EXPECTED_PS_ARTIFACT.read_text(encoding="utf-8"))
    target = payload["target"]
    rows = {int(row["digits"]): row for row in target["precision_rows"]}
    row = rows[TARGET_DIGITS]
    return {
        "artifact": str(EXPECTED_PS_ARTIFACT.relative_to(ROOT)),
        "artifact_sha256": _hash(EXPECTED_PS_ARTIFACT),
        "classification": target["classification"],
        "target_passes": bool(target["target_passes"]),
        "direction": target["direction"],
        "precision_800": {
            key: row[key]
            for key in (
                "digits",
                "resolved",
                "rank",
                "minimum_eigenvalue",
                "C",
                "w",
                "dC",
                "dw",
                "dJ",
                "relative_error_to_prior_AP",
                "runtime_seconds",
                "solve_residuals",
                "magnitude",
                "passes",
            )
        },
    }


def _provenance() -> dict[str, Any]:
    model = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
    mapping = ROOT / "scripts" / "validate_corrected_ap_custom_backward.py"
    worker = ROOT / "scripts" / "full_support_c4_worker.py"
    tangent = ROOT / "src" / "cvqkd" / "c4_constrained_tangent.py"
    return {
        "git": _git_metadata(),
        "final_model_spec_sha256": _hash(model),
        "exact_ensemble_sha256": ENSEMBLE_HASH,
        "production_mapping_source": str(mapping.relative_to(ROOT)),
        "production_mapping_source_sha256": _hash(mapping),
        "corrected_worker_source": str(worker.relative_to(ROOT)),
        "corrected_worker_sha256": _hash(worker),
        "tangent_source": str(tangent.relative_to(ROOT)),
        "tangent_source_sha256": _hash(tangent),
    }


def _mapping_definition(family: str) -> dict[str, Any]:
    common = {
        "parameter": "scalar theta",
        "endpoint_rule": "evaluate the existing transmitter map at theta=+/-h",
        "physical_normalization": "E_z=sum q|z|^2; s=sqrt(V_A/(2 E_z)); alpha=s*i^r*z",
        "phase": "disabled; c_phi=0",
        "manual_256_alpha_perturbation": False,
    }
    if family == "gs_real":
        return {
            **common,
            "family": family,
            "raw_parameterization": "coordinates[0,0] += theta in the existing 64-prototype GS representation",
            "fixed_values": "V_A=1 and the uniform reference PMF",
            "independent_from": "gs_imaginary is evaluated through its own mapping call",
        }
    if family == "gs_imag":
        return {
            **common,
            "family": family,
            "raw_parameterization": "coordinates[0,1] += theta in the existing 64-prototype GS representation",
            "fixed_values": "V_A=1 and the uniform reference PMF",
            "independent_from": "gs_real is evaluated through its own mapping call",
        }
    if family == "va":
        return {
            **common,
            "family": family,
            "raw_parameterization": "relative constellation and uniform reference PMF fixed",
            "variance_parameterization": "V_A=1+theta; only physical amplitudes change before alpha is formed",
        }
    raise ValueError(f"unsupported direction family: {family}")


def _target_at(family: str, theta: float | mp.mpf) -> tuple[list[float], list[complex]]:
    value = torch.tensor(float(theta), dtype=torch.float64)
    probabilities, amplitudes = _target_direction(family, value)
    return (
        [float(item) for item in probabilities.detach().cpu().tolist()],
        [complex(item) for item in amplitudes.detach().cpu().tolist()],
    )


def _physical_structure(
    family: str,
    theta: float | mp.mpf,
    probabilities: list[float],
    amplitudes: list[complex],
) -> dict[str, Any]:
    p_tensor = torch.tensor(probabilities, dtype=torch.float64)
    z_tensor = torch.tensor(amplitudes, dtype=torch.complex128)
    full_p = expand_c4_orbit_masses((4.0 * p_tensor).unsqueeze(0))[0]
    full_z = expand_c4_orbit_values(z_tensor)
    expected_variance = 1.0 + float(theta) if family == "va" else 1.0
    physical_energy = float(torch.sum(full_p * full_z.abs().square()).item())
    expected_energy = expected_variance / 2.0
    unique_state_count = len(
        {(complex(value).real.hex(), complex(value).imag.hex()) for value in full_z.tolist()}
    )
    probability_sum = float(full_p.sum().item())
    energy_error = abs(physical_energy - expected_energy)
    return {
        "theta": _string(mp.mpf(theta), 20),
        "positive_probabilities": bool(torch.all(full_p > 0)),
        "probability_sum": probability_sum,
        "probability_sum_error": abs(probability_sum - 1.0),
        "unique_state_count": unique_state_count,
        "physical_energy": physical_energy,
        "expected_variance": expected_variance,
        "expected_physical_energy": expected_energy,
        "physical_energy_abs_error": energy_error,
        "passes": bool(
            torch.all(full_p > 0)
            and abs(probability_sum - 1.0) <= 1e-12
            and unique_state_count == 256
            and energy_error <= 1e-12
        ),
    }


def _cheap_direction_inputs(
    family: str,
    probabilities: list[float],
    amplitudes: list[complex],
) -> tuple[list[float], list[complex], list[float], list[complex]]:
    """Build independent, well-conditioned physical paths for the small oracle."""

    dp = [0.0 for _ in probabilities]
    if family == "gs_real":
        dz = [complex(value.real, 0.0) for value in amplitudes]
    elif family == "gs_imag":
        dz = [complex(0.0, value.imag) for value in amplitudes]
    elif family == "va":
        dz = [0.5 * value for value in amplitudes]
    else:
        raise ValueError(f"unsupported direction family: {family}")
    return probabilities, amplitudes, dp, dz


def _cheap_row(family: str, fixture: str) -> dict[str, Any]:
    probabilities, amplitudes, _, _ = _fixture_inputs()[fixture]
    p, z, dp, dz = _cheap_direction_inputs(family, probabilities, amplitudes)
    started = time.perf_counter()
    with mp.workdps(CHEAP_DIGITS + 30):
        tangent = forward_tangent(
            p,
            z,
            dp,
            dz,
            digits=CHEAP_DIGITS,
            instrument_explicit=False,
        )
        plus = _generic_ap_row(
            [p[i] + float(CHEAP_H) * dp[i] for i in range(len(p))],
            [z[i] + complex(CHEAP_H) * dz[i] for i in range(len(z))],
            CHEAP_DIGITS,
        )
        minus = _generic_ap_row(
            [p[i] - float(CHEAP_H) * dp[i] for i in range(len(p))],
            [z[i] - complex(CHEAP_H) * dz[i] for i in range(len(z))],
            CHEAP_DIGITS,
        )
        ap_d_c = (mp.mpf(plus["C"]) - mp.mpf(minus["C"])) / (2 * CHEAP_H)
        ap_d_w = (mp.mpf(plus["w"]) - mp.mpf(minus["w"])) / (2 * CHEAP_H)
        ap_d_j = COMBINED_A * ap_d_c + COMBINED_B * ap_d_w
        tangent_d_j = COMBINED_A * tangent.dC + COMBINED_B * tangent.dw
        comparisons = {
            "dC": _comparison(tangent.dC, ap_d_c, CHEAP_RELATIVE_TOLERANCE),
            "dw": _comparison(tangent.dw, ap_d_w, CHEAP_RELATIVE_TOLERANCE),
            "dJ": _comparison(tangent_d_j, ap_d_j, CHEAP_RELATIVE_TOLERANCE),
        }
    return {
        "family": family,
        "fixture": fixture,
        "digits": CHEAP_DIGITS,
        "h": _string(CHEAP_H, 20),
        "support": tangent.diagnostics["support"],
        "central_fd": {
            "dC": _string(ap_d_c),
            "dw": _string(ap_d_w),
            "dJ": _string(ap_d_j),
        },
        "constrained_tangent": {
            "dC": _string(tangent.dC),
            "dw": _string(tangent.dw),
            "dJ": _string(tangent_d_j),
        },
        "comparisons": comparisons,
        "passes": bool(
            tangent.diagnostics["support"]["rank"] == tangent.diagnostics["support"]["expected_rank"]
            and all(row["passes"] for row in comparisons.values())
        ),
        "runtime_seconds": time.perf_counter() - started,
    }


def build_cheap_preflight() -> dict[str, Any]:
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    failure: dict[str, Any] | None = None
    for family in DIRECTIONS:
        for fixture in _fixture_inputs():
            row = _cheap_row(family, fixture)
            rows.append(row)
            if not row["passes"]:
                failure = {"family": family, "fixture": fixture}
                return {
                    "status": "CHEAP_DIRECTIONAL_PREFLIGHT_FAIL",
                    "directions_order": list(DIRECTIONS),
                    "rows": rows,
                    "failure": failure,
                    "passes": False,
                    "runtime_seconds": time.perf_counter() - started,
                }
    return {
        "status": "CHEAP_DIRECTIONAL_PREFLIGHT_PASS",
        "directions_order": list(DIRECTIONS),
        "rows": rows,
        "failure": failure,
        "passes": True,
        "runtime_seconds": time.perf_counter() - started,
    }


def _magnitude_summary(magnitude: dict[str, Any]) -> dict[str, Any]:
    return {
        name: {
            "max_abs": values["max_abs"],
            "log10_max_abs": values["log10_max_abs"],
        }
        for name, values in magnitude.items()
        if isinstance(values, dict) and "max_abs" in values and "log10_max_abs" in values
    }


def _failed_target_result(
    family: str,
    message: str,
    started: float,
    *,
    structure: dict[str, Any] | None = None,
    endpoints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "family": family,
        "mapping": _mapping_definition(family),
        "digits": TARGET_DIGITS,
        "h": _string(TARGET_H, 20),
        "structure": structure,
        "endpoints": endpoints or {},
        "failure": message,
        "passes": False,
        "runtime": {
            "endpoint_minus_seconds": None,
            "endpoint_plus_seconds": None,
            "constrained_tangent_seconds": None,
            "total_seconds": time.perf_counter() - started,
        },
    }


def _target_endpoint(family: str, theta: mp.mpf) -> dict[str, Any]:
    probabilities, amplitudes = _target_at(family, theta)
    structure = _physical_structure(family, theta, probabilities, amplitudes)
    if not structure["passes"]:
        return {
            "theta": _string(theta, 20),
            "structure": structure,
            "resolved": False,
            "passes": False,
            "failure": "physical endpoint structure check failed",
            "runtime_seconds": 0.0,
        }
    started = time.perf_counter()
    try:
        row = _worker_row(probabilities, amplitudes, TARGET_DIGITS)
    except RuntimeError as error:
        return {
            "theta": _string(theta, 20),
            "structure": structure,
            "resolved": False,
            "passes": False,
            "failure": str(error),
            "runtime_seconds": time.perf_counter() - started,
        }
    return {
        "theta": _string(theta, 20),
        "structure": structure,
        "resolved": bool(row["resolved"]),
        "rank": row["rank"],
        "minimum_eigenvalue": row["minimum_eigenvalue"],
        "C": row["C"],
        "w": row["w"],
        "passes": bool(row["resolved"] and row["rank"] == 256),
        "runtime_seconds": time.perf_counter() - started,
    }


def run_target_direction(family: str) -> dict[str, Any]:
    started_total = time.perf_counter()
    print(f"{family}: constructing central production-mapping direction", flush=True)
    probabilities, amplitudes, dp, dz = _target_directional_inputs(family)
    central_structure = _target_structure_record(family)
    central_structure.update(_physical_structure(family, 0.0, probabilities, amplitudes))
    if not central_structure["positive_probabilities"] or central_structure["unique_state_count"] != 256:
        return _failed_target_result(
            family,
            "central production mapping failed positivity or uniqueness checks",
            started_total,
            structure=central_structure,
        )
    if not central_structure["passes"]:
        return _failed_target_result(
            family,
            "central physical normalization or probability-sum check failed",
            started_total,
            structure=central_structure,
        )

    print(f"{family}: constrained tangent at {TARGET_DIGITS} digits", flush=True)
    started_tangent = time.perf_counter()
    try:
        tangent = forward_tangent(
            probabilities,
            amplitudes,
            dp,
            dz,
            digits=TARGET_DIGITS,
            instrument_explicit=False,
        )
    except FullSupportUnresolved as error:
        result = _failed_target_result(
            family,
            f"central constrained tangent support unresolved: rank={error.rank} lambda_min={_string(error.minimum_eigenvalue)}",
            started_total,
            structure=central_structure,
        )
        result["runtime"]["constrained_tangent_seconds"] = time.perf_counter() - started_tangent
        return result
    tangent_runtime = time.perf_counter() - started_tangent

    print(f"{family}: corrected AP endpoint theta=-h", flush=True)
    minus = _target_endpoint(family, -TARGET_H)
    if not minus["passes"]:
        return _failed_target_result(
            family,
            f"minus endpoint failed: {minus.get('failure', 'unresolved support')}",
            started_total,
            structure=central_structure,
            endpoints={"minus": minus},
        ) | {"runtime": {"endpoint_minus_seconds": minus["runtime_seconds"], "endpoint_plus_seconds": None, "constrained_tangent_seconds": tangent_runtime, "total_seconds": time.perf_counter() - started_total}}

    print(f"{family}: corrected AP endpoint theta=+h", flush=True)
    plus = _target_endpoint(family, TARGET_H)
    if not plus["passes"]:
        return _failed_target_result(
            family,
            f"plus endpoint failed: {plus.get('failure', 'unresolved support')}",
            started_total,
            structure=central_structure,
            endpoints={"minus": minus, "plus": plus},
        ) | {"runtime": {"endpoint_minus_seconds": minus["runtime_seconds"], "endpoint_plus_seconds": plus["runtime_seconds"], "constrained_tangent_seconds": tangent_runtime, "total_seconds": time.perf_counter() - started_total}}

    with mp.workdps(TARGET_DIGITS + 40):
        ap_d_c = (mp.mpf(plus["C"]) - mp.mpf(minus["C"])) / (2 * TARGET_H)
        ap_d_w = (mp.mpf(plus["w"]) - mp.mpf(minus["w"])) / (2 * TARGET_H)
        ap_d_j = COMBINED_A * ap_d_c + COMBINED_B * ap_d_w
        tangent_d_j = COMBINED_A * tangent.dC + COMBINED_B * tangent.dw
        comparisons = {
            "dC": _comparison(tangent.dC, ap_d_c, TARGET_RELATIVE_TOLERANCE),
            "dw": _comparison(tangent.dw, ap_d_w, TARGET_RELATIVE_TOLERANCE),
            "dJ": _comparison(tangent_d_j, ap_d_j, TARGET_RELATIVE_TOLERANCE),
        }

    magnitude = tangent.diagnostics["magnitude"]["constrained"]
    passes = bool(
        tangent.diagnostics["support"]["rank"] == 256
        and all(row["passes"] for row in comparisons.values())
        and minus["passes"]
        and plus["passes"]
    )
    return {
        "family": family,
        "mapping": _mapping_definition(family),
        "digits": TARGET_DIGITS,
        "h": _string(TARGET_H, 20),
        "structure": central_structure,
        "endpoints": {"minus": minus, "plus": plus},
        "central": {
            "C": _string(tangent.C),
            "w": _string(tangent.w),
            "dC": _string(tangent.dC),
            "dw": _string(tangent.dw),
            "dJ": _string(tangent_d_j),
            "support": tangent.diagnostics["support"],
            "solve_residuals": tangent.diagnostics["solve_residuals"],
            "magnitude": _magnitude_summary(magnitude),
            "diagnostic_marker": tangent.diagnostics["marker"],
            "reverse": tangent.diagnostics["reverse"],
        },
        "central_finite_difference": {
            "dC": _string(ap_d_c),
            "dw": _string(ap_d_w),
            "dJ": _string(ap_d_j),
        },
        "comparisons": comparisons,
        "acceptance": {
            "relative_tolerance": _string(TARGET_RELATIVE_TOLERANCE, 10),
            "near_zero_scale": _string(NEAR_ZERO_SCALE, 10),
            "rule": "relative error for non-near-zero references; absolute tolerance for near-zero references",
        },
        "passes": passes,
        "runtime": {
            "endpoint_minus_seconds": minus["runtime_seconds"],
            "endpoint_plus_seconds": plus["runtime_seconds"],
            "constrained_tangent_seconds": tangent_runtime,
            "total_seconds": time.perf_counter() - started_total,
        },
    }


def _base_artifact() -> dict[str, Any]:
    return {
        "runner": "scripts/validate_remaining_c4_forward_tangents.py",
        "status": "BOUNDED_STUDY_IN_PROGRESS",
        "classification": "SOURCE_FORWARD_TANGENT_PARTIALLY_VALIDATED",
        "adaptive_readiness": "NOT_READY_FOR_ADAPTIVE_TRAINING",
        "scope": "bounded full-support C4 constrained-solve forward tangent for PS, GS-real, GS-imaginary, and V_A; no reverse or training",
        "directions_order": list(DIRECTIONS),
        "target_digits": TARGET_DIGITS,
        "target_h": _string(TARGET_H, 20),
        "provenance": _provenance(),
        "ps_reference": _ps_reference(),
        "mapping_definitions": {family: _mapping_definition(family) for family in DIRECTIONS},
        "cheap_preflight": None,
        "directions": {},
        "reverse_or_training": {
            "custom_reverse_called": False,
            "full_z_backward": False,
            "optimizer_step": False,
            "training_ran": False,
            "holevo_or_final_test_ran": False,
        },
        "checkpoint": {
            "last_completed_direction": None,
            "completed_directions": [],
            "stopped_on_failure": False,
        },
    }


def _refresh_artifact(artifact: dict[str, Any]) -> None:
    directions = artifact.get("directions", {})
    completed = [family for family in DIRECTIONS if family in directions and directions[family].get("passes")]
    cheap_pass = bool(artifact.get("cheap_preflight", {}).get("passes"))
    ps_pass = bool(artifact.get("ps_reference", {}).get("target_passes"))
    all_pass = cheap_pass and ps_pass and len(completed) == len(DIRECTIONS)
    classification = (
        "FULL_SOURCE_FORWARD_TANGENT_VALIDATED"
        if all_pass
        else "SOURCE_FORWARD_TANGENT_PARTIALLY_VALIDATED"
    )
    artifact["classification"] = classification
    artifact["status"] = classification
    artifact["adaptive_readiness"] = "NOT_READY_FOR_ADAPTIVE_TRAINING"
    artifact["checkpoint"]["completed_directions"] = completed
    runtime = {
        "cheap_preflight_seconds": artifact.get("cheap_preflight", {}).get("runtime_seconds"),
        "direction_seconds": {
            family: directions[family].get("runtime", {}).get("total_seconds")
            for family in DIRECTIONS
            if family in directions
        },
    }
    runtime["target_directions_total_seconds"] = sum(
        value for value in runtime["direction_seconds"].values() if value is not None
    )
    runtime["study_total_seconds"] = sum(
        value for value in (
            runtime["cheap_preflight_seconds"],
            runtime["target_directions_total_seconds"],
        )
        if value is not None
    )
    artifact["runtime"] = runtime
    if all_pass:
        artifact["blocker"] = "a validated and computationally practical reverse/adjoint of the constrained C4 source-moment system"
        artifact["recommended_next_task"] = "Assess that reverse/adjoint boundary separately; do not execute reverse, full-Z backward, or training in this study."
    elif artifact["checkpoint"].get("stopped_on_failure"):
        family = artifact["checkpoint"].get("last_completed_direction")
        artifact["blocker"] = f"{family} direction failed bounded forward-tangent validation"
        artifact["recommended_next_task"] = "Investigate the failed direction without starting reverse, full-Z backward, or training."
    else:
        artifact["blocker"] = "remaining GS-real, GS-imaginary, and V_A forward directions are not yet validated"
        artifact["recommended_next_task"] = "Continue the remaining directions in the recorded order only."


def _save(path: Path, artifact: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _base_artifact()
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("runner") != "scripts/validate_remaining_c4_forward_tangents.py":
        raise RuntimeError(f"checkpoint belongs to another runner: {path}")
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("cheap", "target"), default="target")
    parser.add_argument("--direction", choices=DIRECTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.phase == "cheap":
        artifact = _base_artifact()
        artifact["cheap_preflight"] = build_cheap_preflight()
        _refresh_artifact(artifact)
        _save(args.output, artifact)
        print(json.dumps({"output": str(args.output), "cheap": artifact["cheap_preflight"]}, indent=2))
        return 0 if artifact["cheap_preflight"]["passes"] else 1

    if args.direction is None:
        parser.error("--direction is required for --phase target")
    artifact = _load(args.output)
    if artifact.get("cheap_preflight", {}).get("passes") is not True:
        print("running cheap directional preflight before any target computation", flush=True)
        artifact["cheap_preflight"] = build_cheap_preflight()
        _refresh_artifact(artifact)
        _save(args.output, artifact)
        if not artifact["cheap_preflight"]["passes"]:
            print(json.dumps({"output": str(args.output), "status": artifact["status"]}, indent=2))
            return 1

    if args.direction in artifact.get("directions", {}):
        existing = artifact["directions"][args.direction]
        if existing.get("passes"):
            print(json.dumps({"output": str(args.output), "direction": args.direction, "status": "already_checkpointed"}, indent=2))
            return 0
        artifact["checkpoint"]["stopped_on_failure"] = True
        _refresh_artifact(artifact)
        _save(args.output, artifact)
        return 1

    result = run_target_direction(args.direction)
    artifact["directions"][args.direction] = result
    artifact["checkpoint"]["last_completed_direction"] = args.direction
    if not result["passes"]:
        artifact["checkpoint"]["stopped_on_failure"] = True
    _refresh_artifact(artifact)
    _save(args.output, artifact)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "direction": args.direction,
                "passes": result["passes"],
                "classification": artifact["classification"],
                "runtime": result.get("runtime"),
            },
            indent=2,
        )
    )
    return 0 if result["passes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
