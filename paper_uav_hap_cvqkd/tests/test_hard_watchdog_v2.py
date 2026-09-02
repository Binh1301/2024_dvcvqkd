from __future__ import annotations

import json
from pathlib import Path
import sys

from src.validation.hard_watchdog_v2 import run_with_hard_timeout


def test_hard_timeout_is_parent_recorded(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text('{"last":"durable"}\n', encoding="utf-8")
    status_path = tmp_path / "status.json"
    row = run_with_hard_timeout(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        cwd=tmp_path,
        time_limit_seconds=0.1,
        kill_grace_seconds=0.1,
        fixture="synthetic",
        interval="0/1..1/1",
        checkpoint_path=checkpoint,
        status_path=status_path,
    )
    assert row["status"] == "RESOURCE_LIMIT"
    assert row["reason"] == "HARD_WALL_CLOCK_TIMEOUT"
    assert row["last_durable_checkpoint"]["sha256"]
    assert json.loads(status_path.read_text())["worker_pid"] == row["worker_pid"]


def test_worker_completion_before_deadline(tmp_path):
    row = run_with_hard_timeout(
        [sys.executable, "-c", "print('done')"],
        cwd=tmp_path,
        time_limit_seconds=2,
        kill_grace_seconds=0.1,
        fixture="synthetic",
        interval="point",
        checkpoint_path=tmp_path / "none.json",
        status_path=tmp_path / "status.json",
    )
    assert row["status"] == "WORKER_COMPLETED"
    assert "done" in row["stdout_tail"]

