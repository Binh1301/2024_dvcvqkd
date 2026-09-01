"""Capture the V3 certification environment without loading a fixture."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

try:
    from _common import ROOT
except ModuleNotFoundError:
    from scripts._common import ROOT
from src.validation.certification_provenance_v3 import live_environment, sha256


def _atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.perf_counter_ns()}")
    data = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with temporary.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def capture(output: Path) -> dict:
    producer = Path(__file__).resolve()
    artifact = {
        "schema_version": "taylor-eigencluster-environment-v3",
        "status": "CERTIFICATION_ENVIRONMENT_CAPTURED",
        "live_environment": live_environment(),
        "requirements_lock_sha256": sha256(
            ROOT / "requirements-certification-inertia.lock"
        ),
        "final_model_spec_sha256": sha256(ROOT / "docs/FINAL_MODEL_SPEC.md"),
        "scientific_evaluation_started": False,
        "lifecycle_guards": {
            "threshold_approved": False, "publication_training_performed": False,
            "final_test_accessed": False, "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
        "provenance": {"producer_sha256": sha256(producer)},
    }
    _atomic(output, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(capture(args.output.resolve()), indent=2))


if __name__ == "__main__":
    main()
