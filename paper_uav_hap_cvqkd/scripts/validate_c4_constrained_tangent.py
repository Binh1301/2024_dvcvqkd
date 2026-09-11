"""Validate the isolated C4 constrained-solve forward tangent.

This runner deliberately calls no custom reverse and performs no training.
The target AP finite-difference reference is the already-recorded corrected
Case-A PS artifact, whose direction and worker hashes are checked before use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import mpmath as mp

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_corrected_ap_custom_backward import (  # noqa: E402
    COMBINED_A,
    COMBINED_B,
    ENSEMBLE_HASH,
    _fixture_inputs,
    _generic_ap_row,
    _target_directional_inputs,
    _target_structure_record,
)
from src.cvqkd.c4_constrained_tangent import (  # noqa: E402
    FullSupportUnresolved,
    forward_tangent,
)


CHEAP_DIGITS = 70
CHEAP_H_VALUES = ("1e-3", "3e-4", "1e-4", "3e-5", "1e-5")
TARGET_DIGITS = (200, 400, 600, 800)
TARGET_ATTEMPT = ROOT / "results" / "ap_custom_backward_ps_target_attempt_20260911.json"
DEFAULT_OUTPUT = ROOT / "results" / "c4_constrained_forward_tangent_20260911.json"
EXPECTED_DIRECTION_SHA256 = "e274073c5038308b521bd1a348c932a4a249cd5fc59a006b7611911e2be6dd87"


def _relative(observed: mp.mpf, reference: mp.mpf) -> mp.mpf:
    return abs(observed - reference) / max(abs(reference), mp.mpf("1e-40"))


def _string(value: Any, digits: int = 50) -> str:
    return mp.nstr(value, digits)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cheap_fixture(name: str, instrument_explicit: bool) -> dict[str, Any]:
    p, z, dp, dz = _fixture_inputs()[name]
    with mp.workdps(CHEAP_DIGITS + 30):
        tangent = forward_tangent(
            p,
            z,
            dp,
            dz,
            digits=CHEAP_DIGITS,
            instrument_explicit=instrument_explicit,
        )
        oracle = _generic_ap_row(p, z, CHEAP_DIGITS)
        oracle_c = mp.mpf(oracle["C"])
        oracle_w = mp.mpf(oracle["w"])
        h_rows = []
        for h_text in CHEAP_H_VALUES:
            h = mp.mpf(h_text)
            plus = _generic_ap_row(
                [p[i] + float(h) * dp[i] for i in range(len(p))],
                [z[i] + complex(h) * dz[i] for i in range(len(z))],
                CHEAP_DIGITS,
            )
            minus = _generic_ap_row(
                [p[i] - float(h) * dp[i] for i in range(len(p))],
                [z[i] - complex(h) * dz[i] for i in range(len(z))],
                CHEAP_DIGITS,
            )
            ap_dC = (mp.mpf(plus["C"]) - mp.mpf(minus["C"])) / (2 * h)
            ap_dw = (mp.mpf(plus["w"]) - mp.mpf(minus["w"])) / (2 * h)
            ap_dJ = COMBINED_A * ap_dC + COMBINED_B * ap_dw
            h_rows.append(
                {
                    "h": h_text,
                    "AP_dC": _string(ap_dC),
                    "AP_dw": _string(ap_dw),
                    "AP_dJ": _string(ap_dJ),
                    "dC_relative_error": _string(_relative(tangent.dC, ap_dC), 30),
                    "dw_relative_error": _string(_relative(tangent.dw, ap_dw), 30),
                    "dJ_relative_error": _string(
                        _relative(COMBINED_A * tangent.dC + COMBINED_B * tangent.dw, ap_dJ),
                        30,
                    ),
                }
            )
        selected = h_rows[-1]
        adjacent = [
            abs(mp.mpf(h_rows[i]["AP_dJ"]) - mp.mpf(h_rows[i + 1]["AP_dJ"]))
            for i in range(len(h_rows) - 1)
        ]
        comparison = tangent.diagnostics.get("constrained_vs_explicit", {})
        tangent_pass = all(
            mp.mpf(selected[key]) <= mp.mpf("1e-8")
            for key in ("dC_relative_error", "dw_relative_error", "dJ_relative_error")
        )
        explicit_pass = not comparison or all(
            mp.mpf(comparison[key]["relative"]) <= mp.mpf("1e-40")
            for key in ("B", "dB", "A", "dA", "C", "w", "dC", "dw")
        )
        return {
            "fixture": name,
            "digits": CHEAP_DIGITS,
            "support": tangent.diagnostics["support"],
            "forward_relative_error": {
                "C": _string(_relative(tangent.C, oracle_c), 30),
                "w": _string(_relative(tangent.w, oracle_w), 30),
            },
            "tangent": {
                "C": _string(tangent.C),
                "w": _string(tangent.w),
                "dC": _string(tangent.dC),
                "dw": _string(tangent.dw),
                "dJ": _string(COMBINED_A * tangent.dC + COMBINED_B * tangent.dw),
            },
            "h_rows": h_rows,
            "adjacent_AP_dJ_errors": [_string(value, 30) for value in adjacent],
            "explicit_comparison": comparison,
            "solve_residuals": tangent.diagnostics["solve_residuals"],
            "diagnostics": tangent.diagnostics,
            "passes": bool(
                _relative(tangent.C, oracle_c) <= mp.mpf("1e-40")
                and _relative(tangent.w, oracle_w) <= mp.mpf("1e-40")
                and tangent_pass
                and explicit_pass
            ),
        }


def build_cheap_artifact(instrument_explicit: bool = True) -> dict[str, Any]:
    fixtures = [_cheap_fixture(name, instrument_explicit) for name in _fixture_inputs()]
    return {
        "status": "CHEAP_CONSTRAINED_TANGENT_PASS" if all(row["passes"] for row in fixtures) else "CHEAP_CONSTRAINED_TANGENT_FAIL",
        "fixtures": fixtures,
    }


def _load_target_reference() -> tuple[dict[str, Any], str]:
    if not TARGET_ATTEMPT.exists():
        raise FileNotFoundError(f"required prior target artifact is missing: {TARGET_ATTEMPT}")
    prior = json.loads(TARGET_ATTEMPT.read_text(encoding="utf-8"))
    worker_hash = _hash(ROOT / "scripts" / "full_support_c4_worker.py")
    if prior["provenance"]["corrected_worker_sha256"] != worker_hash:
        raise RuntimeError("prior target artifact was produced by a different corrected AP worker")
    if prior["provenance"]["exact_ensemble_sha256"] != ENSEMBLE_HASH:
        raise RuntimeError("prior target artifact ensemble hash mismatch")
    if prior["structure"]["direction_sha256"] != EXPECTED_DIRECTION_SHA256:
        raise RuntimeError("prior Case-A PS direction hash mismatch")
    return prior, worker_hash


def _target_row(
    p: list[float],
    z: list[complex],
    dp: list[float],
    dz: list[complex],
    digits: int,
    reference: dict[str, mp.mpf],
    instrument_explicit: bool,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        tangent = forward_tangent(
            p,
            z,
            dp,
            dz,
            digits=digits,
            instrument_explicit=instrument_explicit,
        )
    except FullSupportUnresolved as error:
        return {
            "digits": digits,
            "resolved": False,
            "rank": error.rank,
            "minimum_eigenvalue": _string(error.minimum_eigenvalue),
            "runtime_seconds": time.perf_counter() - started,
            "passes": False,
        }
    dJ = COMBINED_A * tangent.dC + COMBINED_B * tangent.dw
    errors = {
        "C": _relative(tangent.C, reference["C"]),
        "w": _relative(tangent.w, reference["w"]),
        "dC": _relative(tangent.dC, reference["dC"]),
        "dw": _relative(tangent.dw, reference["dw"]),
        "dJ": _relative(dJ, reference["dJ"]),
    }
    return {
        "digits": digits,
        "resolved": True,
        "rank": tangent.diagnostics["support"]["rank"],
        "minimum_eigenvalue": tangent.diagnostics["support"]["minimum_eigenvalue"],
        "C": _string(tangent.C),
        "w": _string(tangent.w),
        "dC": _string(tangent.dC),
        "dw": _string(tangent.dw),
        "dJ": _string(dJ),
        "relative_error_to_prior_AP": {key: _string(value, 30) for key, value in errors.items()},
        "runtime_seconds": time.perf_counter() - started,
        "solve_residuals": tangent.diagnostics["solve_residuals"],
        "magnitude": tangent.diagnostics["magnitude"],
        "constrained_vs_explicit": tangent.diagnostics.get("constrained_vs_explicit"),
        "explicit_values": tangent.diagnostics.get("explicit_values"),
        "passes": bool(all(value <= mp.mpf("1e-8") for value in errors.values())),
    }


def build_target_artifact(
    target_digits: tuple[int, ...],
    instrument_explicit: bool,
    precomputed_rows: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    prior, worker_hash = _load_target_reference()
    structure = _target_structure_record("ps")
    if structure["direction_sha256"] != prior["structure"]["direction_sha256"]:
        raise RuntimeError("deterministic Case-A PS direction no longer matches the prior artifact")
    p, z, dp, dz = _target_directional_inputs("ps")
    with mp.workdps(max(target_digits) + 40):
        reference = {
            key: mp.mpf(prior["reference"][f"AP_{key}"])
            for key in ("dC", "dw", "dJ")
        }
        reference.update(
            {
                "C": mp.mpf(prior["provenance"]["corrected_C"]),
                "w": mp.mpf(prior["provenance"]["corrected_w"]),
            }
        )
        rows = (
            [precomputed_rows[digits] for digits in target_digits]
            if precomputed_rows is not None
            else [
                _target_row(p, z, dp, dz, digits, reference, instrument_explicit)
                for digits in target_digits
            ]
        )
    resolved = [row for row in rows if row["resolved"]]
    if rows and rows[-1].get("passes", False):
        classification = "CONSTRAINED_TANGENT_VALIDATED"
    elif len(resolved) >= 2:
        last_errors = [
            max(mp.mpf(value) for value in row["relative_error_to_prior_AP"].values())
            for row in resolved
        ]
        improving = len(last_errors) >= 2 and last_errors[-1] < last_errors[-2] / 10
        classification = (
            "CONSTRAINED_TANGENT_NUMERICALLY_UNSTABLE"
            if improving
            else "CONSTRAINED_TANGENT_DERIVATION_ERROR"
        )
    elif len(resolved) == 1:
        classification = "CONSTRAINED_TANGENT_NUMERICALLY_UNSTABLE"
    else:
        classification = "CONSTRAINED_TANGENT_INCONCLUSIVE"
    return {
        "status": classification,
        "classification": classification,
        "adaptive_readiness": "NOT_READY_FOR_ADAPTIVE_TRAINING",
        "scope": "one exact full-support C4 constrained-solve forward tangent; Case-A PS only",
        "prior_target_artifact": str(TARGET_ATTEMPT.relative_to(ROOT)),
        "prior_target_artifact_sha256": _hash(TARGET_ATTEMPT),
        "corrected_worker_sha256": worker_hash,
        "exact_ensemble_sha256": ENSEMBLE_HASH,
        "direction": structure,
        "reference": {
            "source": "prior corrected AP central-difference artifact",
            "selected_h": prior["selected_h"],
            "C": _string(reference["C"]),
            "w": _string(reference["w"]),
            "dC": _string(reference["dC"]),
            "dw": _string(reference["dw"]),
            "dJ": _string(reference["dJ"]),
        },
        "prior_case_a_comparison": {
            "prior_custom_dJ": prior["custom"]["custom_dJ"],
            "prior_AP_dJ": prior["reference"]["AP_dJ"],
            "prior_custom_relative_error": prior["custom"]["relative_error"],
            "prior_custom_runtime_seconds": prior["runtime_seconds"]["custom_vjp"],
        },
        "precision_rows": rows,
        "precision_row_sources": (
            "precomputed bounded rows; target explicit-intermediate attempt did not complete"
            if precomputed_rows is not None
            else "live target rows"
        ),
        "target_explicit_intermediate_comparison": (
            {
                "status": "NOT_COMPLETED_WITHIN_BOUNDED_RUNTIME",
                "runtime_window": "approximately 16 minutes",
                "completed_target_row": False,
                "constrained_only_row_used_for_validation": True,
            }
            if precomputed_rows is not None
            else {
                "status": "COMPLETED" if instrument_explicit else "NOT_REQUESTED",
                "completed_target_row": instrument_explicit,
            }
        ),
        "target_passes": bool(rows and rows[-1].get("passes", False)),
        "reverse_or_training": {
            "custom_reverse_called": False,
            "optimizer_step": False,
            "training_ran": False,
            "full_z_backward": False,
        },
        "next_task": "Do not implement reverse yet; if tangent is validated, benchmark a compiled multiprecision forward/reverse boundary separately.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("cheap", "target", "all"), default="all")
    parser.add_argument("--target-digits", default=",".join(str(value) for value in TARGET_DIGITS))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--without-explicit", action="store_true")
    parser.add_argument("--reuse-target-rows", action="store_true")
    args = parser.parse_args()
    target_digits = tuple(int(value) for value in args.target_digits.split(",") if value)
    instrument_explicit = not args.without_explicit
    artifact: dict[str, Any] = {
        "runner": "scripts/validate_c4_constrained_tangent.py",
        "instrument_explicit_for_live_rows": instrument_explicit,
    }
    if args.phase in {"cheap", "all"}:
        artifact["cheap"] = build_cheap_artifact(instrument_explicit)
    if args.phase in {"target", "all"}:
        precomputed_rows = None
        if args.reuse_target_rows:
            precomputed_rows = {}
            for digits in target_digits:
                candidates = [
                    ROOT / "results" / f"c4_constrained_forward_tangent_target_{digits}_20260911.json",
                ]
                if digits == 800:
                    candidates.append(
                        ROOT / "results" / "c4_constrained_forward_tangent_target_800_no_explicit_20260911.json"
                    )
                source = next((path for path in candidates if path.exists()), None)
                if source is None:
                    raise FileNotFoundError(f"no precomputed target row for {digits} digits")
                payload = json.loads(source.read_text(encoding="utf-8"))
                precomputed_rows[digits] = payload["target"]["precision_rows"][0]
        artifact["target"] = build_target_artifact(
            target_digits,
            instrument_explicit,
            precomputed_rows,
        )
    if "target" not in artifact:
        artifact["target"] = {
            "status": "CONSTRAINED_TANGENT_INCONCLUSIVE",
            "classification": "CONSTRAINED_TANGENT_INCONCLUSIVE",
            "adaptive_readiness": "NOT_READY_FOR_ADAPTIVE_TRAINING",
            "reason": "target phase was not run",
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "target": artifact["target"]}, indent=2))


if __name__ == "__main__":
    main()
