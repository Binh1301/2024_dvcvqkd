"""Parent-owned hard wall-clock enforcement for certification workers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Sequence


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _checkpoint_identity(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    }


def run_with_hard_timeout(
    command: Sequence[str],
    *,
    cwd: Path,
    time_limit_seconds: float,
    kill_grace_seconds: float,
    fixture: str,
    interval: str,
    checkpoint_path: Path,
    status_path: Path,
) -> dict[str, Any]:
    """Run one worker and let the parent own the deadline and final status."""

    if time_limit_seconds <= 0 or kill_grace_seconds < 0:
        raise ValueError("Watchdog limits must be positive/nonnegative.")
    started = time.perf_counter()
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
    )
    try:
        stdout, stderr = process.communicate(timeout=time_limit_seconds)
        elapsed = time.perf_counter() - started
        if elapsed > time_limit_seconds:
            # A result arriving after the preregistered deadline is inadmissible.
            status = "RESOURCE_LIMIT"
            reason = "RESULT_RECEIVED_AFTER_DEADLINE"
        elif process.returncode == 0:
            status = "WORKER_COMPLETED"
            reason = None
        else:
            status = "WORKER_FAILURE"
            reason = f"EXIT_CODE_{process.returncode}"
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=kill_grace_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        elapsed = time.perf_counter() - started
        status = "RESOURCE_LIMIT"
        reason = "HARD_WALL_CLOCK_TIMEOUT"

    row = {
        "status": status,
        "reason": reason,
        "fixture": fixture,
        "interval": interval,
        "elapsed_seconds": elapsed,
        "configured_time_limit_seconds": float(time_limit_seconds),
        "kill_grace_seconds": float(kill_grace_seconds),
        "worker_pid": process.pid,
        "worker_exit_code": process.returncode,
        "last_durable_checkpoint": _checkpoint_identity(checkpoint_path),
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }
    _atomic_json(status_path, row)
    return row

