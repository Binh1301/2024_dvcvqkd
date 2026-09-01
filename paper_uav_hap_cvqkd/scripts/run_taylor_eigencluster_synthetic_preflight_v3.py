"""Run and persist the frozen 20-case V3 synthetic preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    from _common import ROOT, load_yaml
except ModuleNotFoundError:
    from scripts._common import ROOT, load_yaml
from src.validation.certification_provenance_v3 import live_environment, sha256
from src.validation.durable_journal_v3 import DurableJournal, replay_journal
from src.validation.hard_watchdog_v3 import run_with_job_timeout


TEST_FILE = "tests/test_v3_synthetic_preflight_cases.py"


def _atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    data = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with temporary.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def run(config_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    names = list(settings["synthetic_preflight"]["required_cases"])
    if len(names) != 20:
        raise ValueError("The frozen preflight must contain exactly 20 cases.")
    cases = []
    for index, name in enumerate(names, start=1):
        node = f"{TEST_FILE}::test_case_{index:02d}_{name}"
        started = time.perf_counter()
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", node], cwd=ROOT,
            text=True, capture_output=True,
        )
        cases.append({
            "index": index, "name": name, "node_id": node,
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "runtime_seconds": time.perf_counter() - started,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        })

    with tempfile.TemporaryDirectory(prefix="v3-preflight-", dir=output_path.parent) as raw:
        temporary = Path(raw)
        watchdog_row = run_with_job_timeout(
            [sys.executable, "-c", "import subprocess,sys,time;"
             "subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);"
             "time.sleep(30)"],
            cwd=temporary, time_limit_seconds=.5, kill_grace_seconds=1.5,
            finalization_allowance_seconds=.5, fixture="preflight-tree",
            interval="point", status_path=temporary / "watchdog.json",
        )
        identity = {"config_sha256": sha256(config_path)}
        journal_dir = temporary / "journal"
        with DurableJournal(
            journal_dir, attempt_id="preflight", segment_id="synthetic/ps",
            identity=identity,
        ) as journal:
            journal.append("RUN_STARTED", {})
            journal.append("PATH_DOMAIN_COMMITTED", {"path_domain": {
                "status": "PATH_DOMAIN_CERTIFIED",
            }})
            journal.append("WORK_QUEUE_INITIALIZED", {"pending": []})
            for index in range(3):
                node_id = f"node-{index}"
                journal.append("NODE_STARTED", {"node_id": node_id})
                journal.append("NODE_COMMITTED", {
                    "node_id": node_id, "node": {"status": "UNCERTIFIED"},
                    "action": "UNRESOLVED",
                })
        replay = replay_journal(journal_dir)
        journal_row = {
            "passed": len(replay.completed_nodes) == 3,
            "recovered_completed_node_count": len(replay.completed_nodes),
            "journal_head_sha256": replay.head_sha256,
        }

    passed = sum(row["passed"] for row in cases)
    watchdog_passed = (
        watchdog_row["status"] == "RESOURCE_LIMIT"
        and watchdog_row["tree_termination_confirmed"] is True
        and watchdog_row["return_bound_satisfied"] is True
        and float(watchdog_row["overshoot_seconds"]) <= 2.0
    )
    artifact = {
        "schema_version": "taylor-eigencluster-synthetic-preflight-v3",
        "status": "SYNTHETIC_PREFLIGHT_PASS" if (
            passed == 20 and watchdog_passed and journal_row["passed"]
        ) else "SYNTHETIC_PREFLIGHT_FAIL",
        "required_case_count": 20, "passed_case_count": passed,
        "failed_case_count": 20 - passed, "cases": cases,
        "watchdog": {
            "passed": watchdog_passed,
            "maximum_observed_overshoot_seconds": watchdog_row.get("overshoot_seconds"),
            "record": watchdog_row,
        },
        "journal_recovery": journal_row,
        "provenance": {
            "producer_sha256": sha256(Path(__file__)),
            "test_file_sha256": sha256(ROOT / TEST_FILE),
            "config_sha256": sha256(config_path),
            "environment": live_environment(),
        },
        "lifecycle_guards": {
            "threshold_approved": False, "publication_training_performed": False,
            "final_test_accessed": False, "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
    }
    _atomic(output_path, artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = run(args.config.resolve(), args.output.resolve())
    print(json.dumps({"status": artifact["status"],
                      "passed": artifact["passed_case_count"]}, indent=2))


if __name__ == "__main__":
    main()
