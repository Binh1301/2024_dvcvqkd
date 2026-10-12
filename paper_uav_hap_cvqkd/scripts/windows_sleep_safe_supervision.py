"""Temporary Windows sleep lease + power watch around the existing Job supervisor."""
import ctypes
from ctypes import wintypes as w
import threading
import time
from unittest.mock import patch

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


class PowerStatus(ctypes.Structure):
    _fields_ = [(n, w.BYTE) for n in ("ac", "battery_flag", "battery_percent", "system_status")] + [
        (n, w.DWORD) for n in ("life_seconds", "full_life_seconds")]


class WindowsPower:
    def __init__(self):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.GetSystemPowerStatus.argtypes = [ctypes.POINTER(PowerStatus)]
        self.kernel.GetSystemPowerStatus.restype = w.BOOL
        self.kernel.SetThreadExecutionState.argtypes = [w.DWORD]
        self.kernel.SetThreadExecutionState.restype = w.DWORD
        self.kernel.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
        self.kernel.TerminateJobObject.restype = w.BOOL
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.restype = w.BOOL

    def read(self):
        status = PowerStatus()
        if not self.kernel.GetSystemPowerStatus(ctypes.byref(status)):
            raise OSError(ctypes.get_last_error(), "Cannot determine AC power safely")
        return {n: int(getattr(status, n)) for n, _ in PowerStatus._fields_}

    def execution_state(self, flags):
        previous = int(self.kernel.SetThreadExecutionState(flags))
        if not previous:
            raise OSError(ctypes.get_last_error(), "Windows execution-state request failed")
        return previous


def safe_power(status):
    return status["ac"] == 1 and status["battery_flag"] != 255 and not status["battery_flag"] & 4


class AwakeOnAC:
    """Acquire/release on the SAME thread; never mutate power-plan settings."""
    def __init__(self, power=None):
        self.power = power or WindowsPower()
        self.receipt = {"active_verified": False, "released_verified": False}
        self.previous = None

    def __enter__(self):
        self.receipt["power_before"] = self.power.read()
        if not safe_power(self.receipt["power_before"]):
            raise RuntimeError("BLOCKED_BY_ENVIRONMENT: connected noncritical AC power required")
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        self.previous = self.power.execution_state(flags)
        try:
            verified = self.power.execution_state(flags)
            if not verified & ES_SYSTEM_REQUIRED:
                raise RuntimeError("Windows sleep-prevention state was not verified")
            self.receipt.update(requested_flags=flags, previous_state=self.previous,
                                active_verified=True, owner_thread=threading.get_ident())
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        if self.previous is not None:
            assert threading.get_ident() == self.receipt.get("owner_thread", threading.get_ident())
            state = self.previous | ES_CONTINUOUS
            self.power.execution_state(state)
            confirmed = self.power.execution_state(state)
            self.receipt["released_verified"] = confirmed == state
            self.receipt["restored_state"] = confirmed
            if not self.receipt["released_verified"]:
                raise RuntimeError("Cannot verify sleep-request cleanup")


def supervised_process(command, wall_limit, log):
    """Original supervisor owns the Job; watcher can terminate that same Job.

    ES_SYSTEM_REQUIRED prevents automatic idle sleep, NOT manual suspend,
    critical-battery hibernation, shutdown or loss of power. Any measured wall
    overrun is FAILED even if termination occurs promptly after resume.
    """
    from scripts.run_theta10_D55_alt_opt_closure_continuation import supervised_probe
    power = WindowsPower()
    stop = threading.Event()
    watch = {"abort_reason": None, "poll_gaps": []}
    threads = []
    current_job = {}
    started = time.monotonic()
    margin = min(5., wall_limit / 4.)
    operation_limit = wall_limit - margin
    if operation_limit <= 0:
        raise ValueError("Positive wall budget required")

    def watchdog():
        previous = time.monotonic()
        while not stop.wait(.2):
            now = time.monotonic()
            interrupted = now-previous > 5
            if interrupted:
                watch["poll_gaps"].append({"gap_seconds": now-previous, "possible_suspend_or_scheduler_gap": True})
            previous = now
            try:
                status = power.read()
                watch["last_power"] = status
                reason = "AC_LOST_OR_CRITICAL_BATTERY" if not safe_power(status) else None
            except Exception as error:
                reason = "POWER_CHECK_FAILED: " + str(error)
            if interrupted:
                reason = "UNEXPECTED_SUSPEND_OR_SCHEDULER_GAP"
            if now-started >= operation_limit:
                reason = "ABSOLUTE_DEADLINE"
            if reason:
                watch["abort_reason"] = reason
                watch["termination_request_succeeded"] = bool(power.kernel.TerminateJobObject(current_job["handle"], 124 if reason == "ABSOLUTE_DEADLINE" else 125))
                return

    original_win_dll = ctypes.WinDLL
    class WatchedKernel:
        def __init__(self, kernel):
            self.kernel = kernel
            assign = kernel.AssignProcessToJobObject
            assign.argtypes, assign.restype = [w.HANDLE, w.HANDLE], w.BOOL
            close = kernel.CloseHandle
            close.argtypes, close.restype = [w.HANDLE], w.BOOL
            def assign_job(job, process):
                success = assign(job, process)
                if success:
                    current_job["handle"] = job
                    thread = threading.Thread(target=watchdog, daemon=True)
                    threads.append(thread)
                    thread.start()
                return success
            def close_handle(handle):
                if handle == current_job.get("handle"):
                    stop.set()
                    for thread in threads:
                        thread.join(timeout=2)
                return close(handle)
            self.AssignProcessToJobObject, self.CloseHandle = assign_job, close_handle
        def __getattr__(self, name):
            return getattr(self.kernel, name)
    def watched_dll(name, *args, **kwargs):
        kernel = original_win_dll(name, *args, **kwargs)
        return WatchedKernel(kernel) if name.lower() == "kernel32" else kernel
    with AwakeOnAC(power) as lease:
        try:
            with patch.object(ctypes, "WinDLL", watched_dll):
                result = supervised_probe(command, operation_limit, log)
        finally:
            stop.set()
            for thread in threads:
                thread.join(timeout=2)
    elapsed = time.monotonic()-started
    return {**result, "deadline_exceeded": result["deadline_exceeded"] or watch["abort_reason"] == "ABSOLUTE_DEADLINE",
            "sleep_prevention": lease.receipt, "power_watch": watch,
            "approved_wall_limit_seconds": wall_limit, "operational_shutdown_margin_seconds": margin,
            "measured_wall_seconds_including_cleanup": elapsed,
            "wall_limit_respected": elapsed <= wall_limit,
            "no_watchdog_thread_remaining": all(not t.is_alive() for t in threads)}
