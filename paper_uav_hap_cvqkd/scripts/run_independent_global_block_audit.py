"""Run the bounded independent low-precision global C4 audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT_ARTIFACT = ROOT / "results" / "ps_va_ap_worker_localization_20260912.json"
DEFAULT_OUTPUT = ROOT / "results" / "independent_global_block_audit_20260912.json"
DEFAULT_DIGITS = (80, 120, 200)
TOTAL_BUDGET_SECONDS = 15 * 60

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import diagnose_ps_va_ap_worker as diagnostic  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_summary(frozen: dict[str, Any]) -> dict[str, Any]:
    return {
        key: frozen[key]
        for key in (
            "mode",
            "state_label",
            "anchor_index",
            "T",
            "epsilon_base",
            "V_A",
            "checkpoint",
            "checkpoint_sha256",
            "constellation_hash",
            "full_constellation_hash",
            "direct_input_hash",
            "q_min",
            "q_max",
            "p_min",
            "p_max",
            "normalization_scale",
            "minimum_pair_distance",
            "unique_amplitudes",
        )
    }


def _child(input_artifact: Path, mode: str, digits: int) -> None:
    artifact = json.loads(input_artifact.read_text(encoding="utf-8"))
    frozen = artifact["cases"][mode]["frozen_input"]
    request = frozen["request"]
    result = diagnostic._independent_full(
        request["probabilities_float64_hex"],
        request["prototypes_float64_hex"],
        digits,
        True,
    )
    result["frozen_input"] = _frozen_summary(frozen)
    print(json.dumps(result, separators=(",", ":"), allow_nan=False))


def _save(path: Path, artifact: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _run(args: argparse.Namespace) -> None:
    started = time.perf_counter()
    source = json.loads(args.input_artifact.read_text(encoding="utf-8"))
    artifact: dict[str, Any] = {
        "artifact_class": "INDEPENDENT_LOW_PRECISION_GLOBAL_BLOCK_AUDIT",
        "status": "RUNNING",
        "scope": "frozen median PS+V_A and Full candidates",
        "model_and_security_changes": False,
        "budget_seconds": args.budget_seconds,
        "requested_digits": args.digits,
        "cases": {},
        "provenance": {
            "input_artifact": str(args.input_artifact.relative_to(ROOT)),
            "input_artifact_sha256": _sha256(args.input_artifact),
            "worker": source["provenance"]["worker"],
            "worker_sha256": source["provenance"]["worker_sha256"],
            "analysis_runner": source["provenance"]["analysis_runner"],
            "analysis_runner_sha256": source["provenance"]["analysis_runner_sha256"],
            "final_model_spec_sha256": source["provenance"]["final_model_spec_sha256"],
            "audit_script": str(Path(__file__).relative_to(ROOT)),
            "audit_script_sha256": _sha256(Path(__file__)),
        },
    }
    timed_out = False
    stop_reason = None

    for mode in ("ps_va", "full"):
        artifact["cases"][mode] = {
            "frozen_input": _frozen_summary(source["cases"][mode]["frozen_input"]),
            "rows": [],
        }
        for digits in args.digits:
            remaining = args.budget_seconds - (time.perf_counter() - started)
            if remaining <= 1:
                timed_out = True
                stop_reason = "DENSE_LOW_PRECISION_COST_BOUNDED_SKIP"
                break
            row_started = time.perf_counter()
            command = [
                sys.executable,
                str(Path(__file__)),
                "--child",
                "--input-artifact",
                str(args.input_artifact),
                "--mode",
                mode,
                "--child-digits",
                str(digits),
            ]
            try:
                completed = subprocess.run(
                    command,
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=max(0.1, remaining - 1.0),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                artifact["cases"][mode]["rows"].append(
                    {
                        "digits": digits,
                        "status": "TIMEOUT",
                        "runtime_seconds": time.perf_counter() - row_started,
                    }
                )
                timed_out = True
                stop_reason = "DENSE_LOW_PRECISION_COST_BOUNDED_SKIP"
                break

            row: dict[str, Any] = {
                "digits": digits,
                "runtime_seconds": time.perf_counter() - row_started,
                "returncode": completed.returncode,
            }
            if completed.returncode != 0:
                row["status"] = "EXIT_NONZERO"
                row["stderr_tail"] = completed.stderr[-4000:]
                row["stdout_tail"] = completed.stdout[-4000:]
                artifact["cases"][mode]["rows"].append(row)
                timed_out = True
                stop_reason = "DENSE_LOW_PRECISION_COST_BOUNDED_SKIP"
                break
            try:
                row = json.loads(completed.stdout)
            except json.JSONDecodeError:
                row["status"] = "INVALID_JSON"
                row["stderr_tail"] = completed.stderr[-4000:]
                row["stdout_tail"] = completed.stdout[-4000:]
                artifact["cases"][mode]["rows"].append(row)
                timed_out = True
                stop_reason = "DENSE_LOW_PRECISION_COST_BOUNDED_SKIP"
                break
            row["orchestration_runtime_seconds"] = time.perf_counter() - row_started
            artifact["cases"][mode]["rows"].append(row)
            _save(args.output, artifact)
        if timed_out:
            break

    artifact["runtime_seconds"] = time.perf_counter() - started
    artifact["recorded_rows"] = sum(
        len(case["rows"]) for case in artifact["cases"].values()
    )
    artifact["completed_rows"] = sum(
        row.get("global_spectrum_status") == "COMPLETED"
        for case in artifact["cases"].values()
        for row in case["rows"]
    )
    artifact["status"] = (
        stop_reason
        if timed_out
        else "COMPLETED_WITHIN_BUDGET"
    )
    artifact["budget_compliance"] = artifact["runtime_seconds"] <= args.budget_seconds
    if stop_reason is not None:
        artifact["stop_reason"] = stop_reason
    _save(args.output, artifact)
    print(json.dumps({
        "status": artifact["status"],
        "runtime_seconds": artifact["runtime_seconds"],
        "output": str(args.output),
        "recorded_rows": sum(
            len(case["rows"]) for case in artifact["cases"].values()
        ),
        "completed_rows": artifact["completed_rows"],
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-artifact", type=Path, default=INPUT_ARTIFACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--digits", nargs="+", type=int, default=list(DEFAULT_DIGITS))
    parser.add_argument("--budget-seconds", type=float, default=TOTAL_BUDGET_SECONDS)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", choices=("ps_va", "full"))
    parser.add_argument("--child-digits", type=int)
    args = parser.parse_args()
    if args.child:
        if args.mode is None or args.child_digits is None:
            parser.error("--child requires --mode and --child-digits")
        _child(args.input_artifact, args.mode, args.child_digits)
        return
    _run(args)


if __name__ == "__main__":
    main()
