"""Run and provenance-bind the repository's standard-library unittest suite."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from _common import ROOT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output: Path, environment_manifest: Path, schema: Path) -> dict[str, object]:
    inventory = [
        {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}
        for path in sorted((ROOT / "tests").glob("test_*.py"))
    ]
    started = time.perf_counter()
    process = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    duration = time.perf_counter() - started
    match = re.search(r"Ran (\d+) tests?", process.stdout)
    test_count = int(match.group(1)) if match else 0
    passed = process.returncode == 0 and test_count > 0 and "\nOK" in process.stdout
    artifact: dict[str, object] = {
        "schema_version": "current-unittest-suite-v1",
        "status": "CURRENTLY_VERIFIED_PASS" if passed else "FAILED",
        "command": "python -m unittest discover -s tests -v",
        "test_count": test_count,
        "exit_code": process.returncode,
        "duration_seconds": duration,
        "test_inventory": inventory,
        "stdout_sha256": hashlib.sha256(process.stdout.encode("utf-8")).hexdigest(),
        "stdout_tail": process.stdout[-4000:],
        "lifecycle_guards": {
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "threshold_approved": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "environment_manifest_sha256": sha256(environment_manifest),
            "schema_sha256": sha256(schema),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
            "python_version": sys.version,
            "python_executable_role": "project_local_ignored_venv",
        },
    }
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "current_test_suite.json")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "current_environment_manifest.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "current_test_suite.schema.json")
    args = parser.parse_args()
    artifact = run(args.output, args.environment, args.schema)
    print(json.dumps({
        "status": artifact["status"], "test_count": artifact["test_count"],
        "exit_code": artifact["exit_code"], "duration_seconds": artifact["duration_seconds"],
    }, sort_keys=True))
    if artifact["status"] != "CURRENTLY_VERIFIED_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
