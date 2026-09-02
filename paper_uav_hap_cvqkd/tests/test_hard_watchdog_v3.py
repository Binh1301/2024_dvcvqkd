from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import time

import pytest

import src.validation.hard_watchdog_v3 as watchdog


def _alive(pid: int) -> bool:
    synchronize = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
    if not handle:
        return False
    try:
        return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == 258
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


@pytest.mark.parametrize("new_process_group", [False, True])
@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object test")
def test_job_timeout_kills_descendant_holding_stdout(tmp_path, new_process_group):
    descendant_pid = tmp_path / "descendant.pid"
    child = "import time; print('descendant-ready', flush=True); time.sleep(30)"
    creation = (
        "creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0),"
        if new_process_group else ""
    )
    parent = (
        "import pathlib,subprocess,sys,time;"
        f"p=subprocess.Popen([sys.executable,'-c',{child!r}],{creation});"
        f"pathlib.Path({str(descendant_pid)!r}).write_text(str(p.pid));"
        "print('parent-ready',flush=True);time.sleep(30)"
    )
    wall_started = time.perf_counter()
    row = watchdog.run_with_job_timeout(
        [sys.executable, "-c", parent], cwd=tmp_path,
        time_limit_seconds=0.5, kill_grace_seconds=1.0,
        finalization_allowance_seconds=1.0, fixture="synthetic-tree",
        interval="point", status_path=tmp_path / "watchdog.json",
    )
    wall_elapsed = time.perf_counter() - wall_started
    assert row["status"] == "RESOURCE_LIMIT"
    assert row["reason"] == "HARD_WALL_CLOCK_TIMEOUT"
    assert row["tree_termination_confirmed"] is True
    assert row["job_accounting"]["active_processes"] == 0
    assert row["return_bound_satisfied"] is True
    assert wall_elapsed <= 2.75
    assert not _alive(int(descendant_pid.read_text()))
    assert "parent-ready" in row["stdout_tail"]
    assert "descendant-ready" in row["stdout_tail"]


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object test")
def test_worker_completion_and_bounded_tail(tmp_path):
    row = watchdog.run_with_job_timeout(
        [sys.executable, "-c", "print('x'*10000)"], cwd=tmp_path,
        time_limit_seconds=3.0, kill_grace_seconds=0.5,
        finalization_allowance_seconds=1.0, fixture="synthetic-complete",
        interval="point", status_path=tmp_path / "watchdog.json",
        log_tail_bytes=128,
    )
    assert row["status"] == "WORKER_COMPLETED"
    assert row["process_signaled_before_deadline"] is True
    assert row["tree_termination_confirmed"] is True
    assert len(row["stdout_tail"].encode("utf-8")) <= 128
    persisted = json.loads((tmp_path / "watchdog.json").read_text())
    assert persisted["worker_pid"] == row["worker_pid"]


def test_non_windows_fails_closed_without_launch(monkeypatch, tmp_path):
    marker = tmp_path / "must-not-exist"
    monkeypatch.setattr(watchdog, "_platform_is_windows", lambda: False)
    row = watchdog.run_with_job_timeout(
        [sys.executable, "-c", f"open({str(marker)!r},'w').write('bad')"],
        cwd=tmp_path, time_limit_seconds=1.0, kill_grace_seconds=0.1,
        finalization_allowance_seconds=0.1, fixture="unsupported",
        interval="point", status_path=tmp_path / "watchdog.json",
    )
    assert row["status"] == "WATCHDOG_PLATFORM_UNSUPPORTED"
    assert row["scientific_evaluation_started"] is False
    assert not marker.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object test")
def test_job_assignment_failure_never_resumes_worker(monkeypatch, tmp_path):
    marker = tmp_path / "must-not-exist"
    monkeypatch.setattr(
        watchdog._kernel32, "AssignProcessToJobObject", lambda job, process: False
    )
    row = watchdog.run_with_job_timeout(
        [sys.executable, "-c", f"open({str(marker)!r},'w').write('bad')"],
        cwd=tmp_path, time_limit_seconds=1.0, kill_grace_seconds=0.1,
        finalization_allowance_seconds=0.1, fixture="assignment-failure",
        interval="point", status_path=tmp_path / "watchdog.json",
    )
    assert row["status"] == "WATCHDOG_LAUNCH_FAILURE"
    assert row["scientific_evaluation_started"] is False
    assert not marker.exists()


def test_invalid_limits_rejected_before_launch(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        watchdog.run_with_job_timeout(
            [sys.executable, "-c", "pass"], cwd=tmp_path,
            time_limit_seconds=0, kill_grace_seconds=0,
            finalization_allowance_seconds=0, fixture="invalid",
            interval="point", status_path=tmp_path / "watchdog.json",
        )
