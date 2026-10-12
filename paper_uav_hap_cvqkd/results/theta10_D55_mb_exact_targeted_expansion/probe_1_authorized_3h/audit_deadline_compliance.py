"""Read-only execution audit plus separate receipts; never launch a probe."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
ledger = json.loads((OUT / "source_generation_ledger.json").read_text())
report = json.loads((OUT / "run_report.json").read_text())
attempt = ledger["attempts"][0]
assert len(ledger["attempts"]) == 1 and attempt["status"] == "TIMEOUT"
manifest = json.loads((OUT / "protected_input_manifest.json").read_text())
for name, expected in manifest.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
assert hashlib.sha256((OUT / "executed_driver.py").read_bytes()).hexdigest() == ledger["producer_sha256"]
assert not list((OUT / "exact_source_cache").glob("*.json"))
# System log evidence was retrieved after recovery; preserve it separately.
events = [
    {"provider": "Microsoft-Windows-Kernel-Power", "id": 42,
     "event_utc": "2026-10-08T15:52:53.7469873Z", "message": "The system is entering sleep. Sleep Reason: Battery"},
    {"provider": "Microsoft-Windows-Power-Troubleshooter", "id": 1,
     "event_utc": "2026-10-08T23:47:43.8620479Z",
     "sleep_utc": "2026-10-08T15:52:50.627478900Z", "wake_utc": "2026-10-08T23:47:41.516142700Z",
     "message": "The system has returned from a low power state. Wake Source: Unknown"},
    {"provider": "Microsoft-Windows-Kernel-Power", "id": 507,
     "event_utc": "2026-10-08T23:47:41.5626931Z", "message": "Exiting Modern Standby: Resume from Hibernate"},
]
result = subprocess.run(["powershell", "-NoProfile", "-Command",
    "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {($_.CommandLine -like '*probe_1_authorized_3h*' -or $_.CommandLine -like '*run_theta10_D55_mb_targeted_probe1*') -and $_.CommandLine -notlike '*audit_deadline_compliance.py*'} | Select-Object ProcessId,ParentProcessId,CommandLine) | ConvertTo-Json -Compress"],
    capture_output=True, text=True, check=True)
assert not result.stdout.strip(), "Scoped Python process remains; do not claim cleanup complete"
audit = {
    "source_outcome": "TIMEOUT_NO_COMPLETED_SOURCE", "deadline_compliance": "FAILED",
    "probe_wall_limit_seconds": ledger["per_probe_timeout_seconds"],
    "probe_wall_measured_seconds": attempt["wall_seconds"],
    "probe_wall_overrun_seconds": attempt["wall_seconds"]-ledger["per_probe_timeout_seconds"],
    "total_wall_limit_seconds": ledger["total_compute_budget_seconds"],
    "total_wall_measured_seconds": ledger["budget_session_wall_seconds"],
    "total_wall_overrun_seconds": ledger["budget_session_wall_seconds"]-ledger["total_compute_budget_seconds"],
    "aggregate_job_cpu_seconds": attempt["cpu_seconds"],
    "cpu_within_probe_limit": attempt["cpu_seconds"] <= ledger["per_probe_timeout_seconds"],
    "cpu_within_probe_limit_is_NOT_wall_time_compliance": True,
    "supervisor_returncode": attempt["supervision"]["returncode"],
    "supervisor_detected_overdue_deadline_after_resume": attempt["supervision"]["deadline_exceeded"],
    "verified_power_events": events,
    "cause": "Windows sleep/hibernate due to battery; supervisor polling could not execute during host suspension. It terminated the Job on resume, not at the real-time deadline.",
    "limitations": "This is not a completed 60-minute active-compute feasibility test and does not prove the ensemble invalid or inferior.",
    "new_exact_sources": 0, "new_SKR_evaluations": 0, "new_AO_runs": 0,
    "compatible_MB_count_unchanged": 139, "probes_2_and_3_started": False,
    "scoped_worker_processes_remaining": 0, "protected_file_hashes_unchanged": len(manifest),
    "regression_tests_pass": report["regression_tests_pass"], "git_diff_check_pass": report["git_diff_check_pass"],
    "raw_ledgers_and_reports_preserved": True,
    "budget_disposition": "Treat the wall-time authorization as exhausted; no further execution under this ledger",
    "next_step": "Stop. Before any new computation, separately agree stable power/no-suspend operating conditions and fresh authorization. No power setting or source method changed here."
}
(OUT / "deadline_compliance_audit.json").write_text(json.dumps(audit, indent=2)+"\n",encoding="utf-8")
md = ["# Probe1 outcome and deadline-compliance incident", "",
    "Source outcome: TIMEOUT; no completed C,w. Deadline compliance: FAILED.",
    f"Probe wall={attempt['wall_seconds']}s (limit3600s); total wall={ledger['budget_session_wall_seconds']}s (limit10800s).",
    f"Aggregate Job CPU={attempt['cpu_seconds']}s; low CPU time is NOT a wall-time PASS.",
    "Windows System events confirm sleep due to Battery at 2026-10-08T15:52:50Z and wake at 23:47:41Z.",
    "Bangkok(+07): sleep22:52:50 Oct08; wake06:47:41 Oct09. Supervisor returned124 and killed the Job after recovery.",
    "No scoped worker remains. SKR26distance and coordinate validation were NOT_RUN; probes2/3 NOT_RUN.",
    "No new source; MB count remains139. No convergence or SKR improvement claim. The attempt does not establish intrinsic source invalidity or a60-minute active-compute timeout.",
    f"Protected hashes unchanged={len(manifest)}; regressions PASS={report['regression_tests_pass']}; diff check PASS={report['git_diff_check_pass']}, scoped separately from FAILED deadline compliance.",
    "Original methods/precision/quadrature/formulas/AO and all prior artifacts unchanged. Raw execution ledger/report are preserved rather than rewriting elapsed time as CPU time.",
    "Stop. The wall-time budget is exhausted. Before any new attempt, require separately agreed stable-power/no-suspend conditions and fresh runtime authorization; no power settings changed here."]
(OUT / "probe_1_outcome.md").write_text("\n".join(md)+"\n",encoding="utf-8")
print(json.dumps({k:audit[k] for k in ("source_outcome","deadline_compliance","aggregate_job_cpu_seconds","scoped_worker_processes_remaining","protected_file_hashes_unchanged")},indent=2))
