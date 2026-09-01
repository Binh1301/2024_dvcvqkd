"""Windows Job-Object wall-clock enforcement for V3 certification workers.

The V3 watchdog deliberately has no non-Windows execution fallback.  A
certification worker is created suspended, assigned to a kill-on-close Job
Object, and only then resumed.  Standard output and error go to ordinary files
so an inherited descendant handle cannot make parent finalization block.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Sequence

try:  # unavailable by design on non-Windows validation hosts
    import msvcrt
except ImportError:  # pragma: no cover - exercised on non-Windows CI
    msvcrt = None  # type: ignore[assignment]


_SCHEMA_VERSION = "taylor-eigencluster-watchdog-v3"
_CREATE_SUSPENDED = 0x00000004
_CREATE_NO_WINDOW = 0x08000000
_STARTF_USESTDHANDLES = 0x00000100
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258
_WAIT_FAILED = 0xFFFFFFFF
_STILL_ACTIVE = 259


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return (json.dumps(
        payload, indent=2, sort_keys=True, allow_nan=False
    ) + "\n").encode("utf-8")


def _durable_atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.tmp-{os.getpid()}-{time.perf_counter_ns()}"
    )
    data = _canonical_json(payload)
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _file_identity(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    }


def _read_tail(path: Path, maximum_bytes: int) -> str:
    if maximum_bytes < 0:
        raise ValueError("maximum_bytes must be nonnegative")
    if maximum_bytes == 0 or not path.is_file():
        return ""
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(max(0, size - maximum_bytes), os.SEEK_SET)
        return stream.read(maximum_bytes).decode("utf-8", errors="replace")


if os.name == "nt":
    _ULONG_PTR = ctypes.c_size_t

    class _STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class _PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", _ULONG_PTR),
            ("MaximumWorkingSetSize", _ULONG_PTR),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", _ULONG_PTR),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", _ULONG_PTR),
            ("JobMemoryLimit", _ULONG_PTR),
            ("PeakProcessMemoryUsed", _ULONG_PTR),
            ("PeakJobMemoryUsed", _ULONG_PTR),
        ]

    class _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
    ]
    _kernel32.SetInformationJobObject.restype = wintypes.BOOL
    _kernel32.CreateProcessW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
        wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
        ctypes.POINTER(_STARTUPINFOW), ctypes.POINTER(_PROCESS_INFORMATION),
    ]
    _kernel32.CreateProcessW.restype = wintypes.BOOL
    _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    _kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    _kernel32.ResumeThread.restype = wintypes.DWORD
    _kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _kernel32.WaitForSingleObject.restype = wintypes.DWORD
    _kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateJobObject.restype = wintypes.BOOL
    _kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateProcess.restype = wintypes.BOOL
    _kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    _kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)
    ]
    _kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL


def _windows_error(operation: str) -> OSError:
    code = ctypes.get_last_error()
    return ctypes.WinError(code, f"{operation} failed")


def _query_accounting(job: Any) -> dict[str, int]:
    info = _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    returned = wintypes.DWORD()
    if not _kernel32.QueryInformationJobObject(
        job, _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION, ctypes.byref(info),
        ctypes.sizeof(info), ctypes.byref(returned),
    ):
        raise _windows_error("QueryInformationJobObject")
    return {
        "total_processes": int(info.TotalProcesses),
        "active_processes": int(info.ActiveProcesses),
        "terminated_processes": int(info.TotalTerminatedProcesses),
    }


def _close_handle(handle: Any) -> None:
    if handle:
        _kernel32.CloseHandle(handle)


def _platform_is_windows() -> bool:
    return os.name == "nt"


def _unsupported_row(
    *, fixture: str, interval: str, time_limit_seconds: float,
    kill_grace_seconds: float, finalization_allowance_seconds: float,
) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "status": "WATCHDOG_PLATFORM_UNSUPPORTED",
        "reason": "WINDOWS_JOB_OBJECT_REQUIRED",
        "fixture": fixture,
        "interval": interval,
        "scientific_evaluation_started": False,
        "configured_time_limit_seconds": float(time_limit_seconds),
        "kill_grace_seconds": float(kill_grace_seconds),
        "finalization_allowance_seconds": float(finalization_allowance_seconds),
        "tree_termination_confirmed": None,
    }


def run_with_job_timeout(
    command: Sequence[str],
    *,
    cwd: Path,
    time_limit_seconds: float,
    kill_grace_seconds: float,
    finalization_allowance_seconds: float,
    fixture: str,
    interval: str,
    status_path: Path,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    log_tail_bytes: int = 4000,
) -> dict[str, Any]:
    """Execute ``command`` in a kill-on-close Windows Job Object.

    The returned elapsed-time bound is an observed acceptance contract, not a
    real-time operating-system guarantee.  Any observed breach fails closed.
    """

    if time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be positive")
    if kill_grace_seconds < 0 or finalization_allowance_seconds < 0:
        raise ValueError("grace/finalization allowances must be nonnegative")
    if not command or any(not isinstance(value, str) or not value for value in command):
        raise ValueError("command must be a nonempty sequence of nonempty strings")
    if log_tail_bytes < 0:
        raise ValueError("log_tail_bytes must be nonnegative")

    cwd = Path(cwd).resolve()
    status_path = Path(status_path).resolve()
    stdout_path = Path(stdout_path or status_path.with_suffix(".stdout.log")).resolve()
    stderr_path = Path(stderr_path or status_path.with_suffix(".stderr.log")).resolve()
    for path in (status_path, stdout_path, stderr_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    if not _platform_is_windows():
        row = _unsupported_row(
            fixture=fixture, interval=interval,
            time_limit_seconds=time_limit_seconds,
            kill_grace_seconds=kill_grace_seconds,
            finalization_allowance_seconds=finalization_allowance_seconds,
        )
        _durable_atomic_json(status_path, row)
        return row
    if msvcrt is None:  # defensive: os.name and module availability must agree
        raise RuntimeError("Windows CRT handle support is unavailable.")

    job = process_handle = thread_handle = None
    stdout_fd = stderr_fd = stdin_fd = None
    worker_pid: int | None = None
    launch_started: float | None = None
    status = "WATCHDOG_LAUNCH_FAILURE"
    reason: str | None = None
    accounting: dict[str, int] | None = None
    process_exit_code: int | None = None
    tree_termination_confirmed = False
    process_signaled_before_deadline = False
    scientific_evaluation_started = False
    termination_requested = False

    try:
        job = _kernel32.CreateJobObjectW(None, None)
        if not job:
            raise _windows_error("CreateJobObjectW")
        limits = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _kernel32.SetInformationJobObject(
            job, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            raise _windows_error("SetInformationJobObject")

        binary_flag = getattr(os, "O_BINARY", 0)
        stdout_fd = os.open(
            stdout_path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | binary_flag, 0o600
        )
        stderr_fd = os.open(
            stderr_path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | binary_flag, 0o600
        )
        stdin_fd = os.open(os.devnull, os.O_RDONLY | binary_flag)
        for descriptor in (stdout_fd, stderr_fd, stdin_fd):
            os.set_handle_inheritable(msvcrt.get_osfhandle(descriptor), True)

        startup = _STARTUPINFOW()
        startup.cb = ctypes.sizeof(startup)
        startup.dwFlags = _STARTF_USESTDHANDLES
        startup.hStdInput = wintypes.HANDLE(msvcrt.get_osfhandle(stdin_fd))
        startup.hStdOutput = wintypes.HANDLE(msvcrt.get_osfhandle(stdout_fd))
        startup.hStdError = wintypes.HANDLE(msvcrt.get_osfhandle(stderr_fd))
        process_info = _PROCESS_INFORMATION()
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(list(command)))
        if not _kernel32.CreateProcessW(
            None, command_line, None, None, True,
            _CREATE_SUSPENDED | _CREATE_NO_WINDOW, None, str(cwd),
            ctypes.byref(startup), ctypes.byref(process_info),
        ):
            raise _windows_error("CreateProcessW")
        process_handle = process_info.hProcess
        thread_handle = process_info.hThread
        worker_pid = int(process_info.dwProcessId)
        if not _kernel32.AssignProcessToJobObject(job, process_handle):
            _kernel32.TerminateProcess(process_handle, 125)
            raise _windows_error("AssignProcessToJobObject")

        launch_started = time.perf_counter()
        if _kernel32.ResumeThread(thread_handle) == 0xFFFFFFFF:
            _kernel32.TerminateJobObject(job, 125)
            raise _windows_error("ResumeThread")
        scientific_evaluation_started = True
        for descriptor_name in ("stdin_fd", "stdout_fd", "stderr_fd"):
            descriptor = locals()[descriptor_name]
            if descriptor is not None:
                os.close(descriptor)
                if descriptor_name == "stdin_fd":
                    stdin_fd = None
                elif descriptor_name == "stdout_fd":
                    stdout_fd = None
                else:
                    stderr_fd = None

        deadline = launch_started + time_limit_seconds
        while True:
            now = time.perf_counter()
            if now >= deadline:
                break
            root_wait = _kernel32.WaitForSingleObject(process_handle, 0)
            if root_wait == _WAIT_FAILED:
                raise _windows_error("WaitForSingleObject")
            accounting = _query_accounting(job)
            if root_wait == _WAIT_OBJECT_0 and accounting["active_processes"] == 0:
                process_signaled_before_deadline = True
                tree_termination_confirmed = True
                status = "WORKER_COMPLETED"
                reason = None
                break
            time.sleep(min(0.01, max(0.0, deadline - now)))
        else:  # pragma: no cover - the loop exits explicitly
            raise AssertionError("unreachable")

        if status != "WORKER_COMPLETED":
            termination_requested = True
            if not _kernel32.TerminateJobObject(job, 124):
                raise _windows_error("TerminateJobObject")
            grace_deadline = time.perf_counter() + kill_grace_seconds
            while True:
                accounting = _query_accounting(job)
                if accounting["active_processes"] == 0:
                    tree_termination_confirmed = True
                    break
                if time.perf_counter() >= grace_deadline:
                    break
                time.sleep(min(0.01, max(0.0, grace_deadline - time.perf_counter())))
            status = "RESOURCE_LIMIT"
            reason = "HARD_WALL_CLOCK_TIMEOUT"

        exit_code = wintypes.DWORD()
        if _kernel32.GetExitCodeProcess(process_handle, ctypes.byref(exit_code)):
            process_exit_code = int(exit_code.value)
            if process_exit_code == _STILL_ACTIVE:
                process_exit_code = None
        if status == "WORKER_COMPLETED" and process_exit_code not in (0, None):
            status = "WORKER_FAILURE"
            reason = f"EXIT_CODE_{process_exit_code}"
    except Exception as error:  # all launch/API failures are evidence, not crashes
        reason = f"{type(error).__name__}: {error}"
        if scientific_evaluation_started:
            status = "WATCHDOG_CONTRACT_BREACH"
        if job:
            termination_requested = True
            _kernel32.TerminateJobObject(job, 125)
            try:
                accounting = _query_accounting(job)
                tree_termination_confirmed = accounting["active_processes"] == 0
            except OSError:
                pass
        elif process_handle:
            _kernel32.TerminateProcess(process_handle, 125)
    finally:
        for descriptor in (stdin_fd, stdout_fd, stderr_fd):
            if descriptor is not None:
                os.close(descriptor)
        _close_handle(thread_handle)
        _close_handle(process_handle)
        _close_handle(job)

    finalized_at = time.perf_counter()
    if launch_started is None:
        process_elapsed = None
        return_elapsed = None
        overshoot = None
        contract_satisfied = False
    else:
        process_elapsed = finalized_at - launch_started
        # Tail reads and status serialization are included prospectively below.
        return_elapsed = process_elapsed
        overshoot = max(0.0, return_elapsed - time_limit_seconds)
        contract_satisfied = (
            return_elapsed <= time_limit_seconds + kill_grace_seconds
            + finalization_allowance_seconds
        )

    row = {
        "schema_version": _SCHEMA_VERSION,
        "status": status,
        "reason": reason,
        "fixture": fixture,
        "interval": interval,
        "scientific_evaluation_started": scientific_evaluation_started,
        "configured_time_limit_seconds": float(time_limit_seconds),
        "kill_grace_seconds": float(kill_grace_seconds),
        "finalization_allowance_seconds": float(finalization_allowance_seconds),
        "maximum_allowed_return_seconds": float(
            time_limit_seconds + kill_grace_seconds + finalization_allowance_seconds
        ),
        "process_elapsed_seconds": process_elapsed,
        "watchdog_return_elapsed_seconds": return_elapsed,
        "overshoot_seconds": overshoot,
        "return_bound_satisfied": contract_satisfied,
        "process_signaled_before_deadline": process_signaled_before_deadline,
        "termination_requested": termination_requested,
        "tree_termination_confirmed": tree_termination_confirmed,
        "worker_pid": worker_pid,
        "worker_exit_code": process_exit_code,
        "job_accounting": accounting,
        "stdout": _file_identity(stdout_path),
        "stderr": _file_identity(stderr_path),
        "stdout_tail": _read_tail(stdout_path, log_tail_bytes),
        "stderr_tail": _read_tail(stderr_path, log_tail_bytes),
        "log_tail_bytes": int(log_tail_bytes),
    }
    # Finalization is measured again after bounded log reads.  Status-file I/O
    # is measured by the caller from this recorded pre-write point; a later
    # verifier may reject an observed outer elapsed-time breach as well.
    if launch_started is not None:
        row["watchdog_return_elapsed_seconds"] = time.perf_counter() - launch_started
        row["overshoot_seconds"] = max(
            0.0, row["watchdog_return_elapsed_seconds"] - time_limit_seconds
        )
        row["return_bound_satisfied"] = (
            row["watchdog_return_elapsed_seconds"]
            <= row["maximum_allowed_return_seconds"]
        )
        if not row["return_bound_satisfied"]:
            row["status"] = "WATCHDOG_CONTRACT_BREACH"
            row["reason"] = "MEASURED_RETURN_BOUND_EXCEEDED"
        if row["status"] == "RESOURCE_LIMIT" and not tree_termination_confirmed:
            row["status"] = "WATCHDOG_CONTRACT_BREACH"
            row["reason"] = "PROCESS_TREE_ACTIVE_AFTER_GRACE"
    _durable_atomic_json(status_path, row)
    return row
