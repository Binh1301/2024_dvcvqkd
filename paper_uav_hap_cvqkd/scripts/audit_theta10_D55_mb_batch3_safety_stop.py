"""Read-only source/worker audit of the AC-aborted Batch3; never resumes AP."""
from datetime import datetime, timedelta, timezone
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_mb_batch3 as run


def main():
    out, io = run.OUT, run.io
    ledger = json.loads((out/'source_generation_ledger.json').read_text())
    assert ledger['status'] == 'STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET'
    attempts = ledger['attempts']
    assert len(attempts) == 1 and attempts[0]['status'] == 'PROCESS_FAILURE'
    supervision = attempts[0]['supervision']
    assert supervision['returncode'] == 125 and not supervision['deadline_exceeded']
    assert supervision['power_watch']['abort_reason'] == 'AC_LOST_OR_CRITICAL_BATTERY'
    assert supervision['power_watch']['termination_request_succeeded']
    assert supervision['power_watch']['last_power']['ac'] == 0
    assert supervision['no_watchdog_thread_remaining']
    assert ledger['sleep_prevention']['released_verified'] and ledger['wall_budget_respected']
    manifest = json.loads((out/'protected_input_manifest.json').read_text())
    for name, expected in manifest.items():
        assert io.digest(ROOT/name) == expected, name
    bank = run.source.load_source_payloads(run.source.unconstrained_config(), run.DIRS)
    mb = [p for p in bank.values() if float.fromhex(p['nu_mb_raw_hex']) > 0]
    assert len(mb) == 145 and not list((out/'exact_source_cache').glob('*.json'))
    for nu, va in run.PAIRS:
        assert run.source.candidate_from_payload(run.source.unconstrained_config(), bank, 'MB', nu, va) is None
    # Windows venv launcher may be a separate Python process for this audit.
    command = "$p=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -like 'python*' -and $_.ProcessId -ne " + str(os.getpid()) + " -and $_.CommandLine -notlike '*audit_theta10_D55_mb_batch3_safety_stop.py*'}); if($p.Count -gt 0){$p | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress}else{'[]'}"
    checked = subprocess.run(['powershell','-NoProfile','-Command',command], capture_output=True, text=True, check=True)
    remaining_python = json.loads(checked.stdout.strip())
    assert remaining_python == [], 'Other Python processes need scoped inspection; never kill unrelated processes'
    power = run.safe.WindowsPower().read()
    origin = datetime.strptime(ledger['authorization_session_origin_utc'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    deadline = origin + timedelta(seconds=10800)
    report = {'status': 'CURRENTLY_VERIFIED_PASS_FOR_SAFETY_STOP_AUDIT',
        'execution_status': 'BLOCKED_BY_ENVIRONMENT_AC_REQUIRED', 'current_power': power,
        'AC_abort_verified': True, 'AP_successful': 0, 'AP_timeout': 0, 'AP_power_aborted': 1,
        'remaining_probes_not_run': [list(p) for p in run.PAIRS[1:]],
        'compatible_MB_count': 145, 'new_C_w': 0, 'new_SKR_evaluations': 0,
        'new_ALT_OPT_validation': 'NOT_RUN_NO_NEW_VALID_SOURCE',
        'unchanged_baseline22': {'nu_raw': .165, 'V_A': 5.475, 'K': .07661740491526092,
            'scope': 'Existing145-catalog result, not a new optimization'},
        'probe1_wall_seconds': attempts[0]['wall_seconds'], 'probe1_Job_CPU_seconds': attempts[0]['cpu_seconds'],
        'active_session_wall_seconds': ledger['budget_session_wall_seconds'],
        'measured_current_controller_and_Job_CPU_seconds': ledger['total_CPU_seconds'],
        'CPU_scope': 'Current controller, native preflight jobs and aborted source job; earlier failed-preflight Job CPU not fully measured',
        'authorization_session_origin_utc': origin.isoformat(), 'original_absolute_deadline_utc': deadline.isoformat(),
        'audit_utc': now.isoformat(), 'unpaused_authorization_wall_seconds_at_audit': (now-origin).total_seconds(),
        'seconds_to_original_deadline_at_audit': max(0., (deadline-now).total_seconds()),
        'budget_reset': False, 'Sleep_original_state_restored': True, 'no_other_python_processes': True,
        'protected_files_unchanged': len(manifest), 'scientific_implementation_unchanged': True,
        'no_interpolation': True, 'producer_sha256': io.digest(__file__),
        'publication': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
    # The output here is a safety audit, not fabricated new source/objective/AO data.
    io.save_json(out/'safety_stop_audit.json', report)
    io.write_csv(out/'probe_execution_status_at_stop.csv', [
        {'priority': i, 'nu_raw': nu, 'V_A': va,
         'status': 'ABORTED_AC_LOST_PROCESS_FAILURE' if i == 1 else 'NOT_RUN_AFTER_SAFETY_STOP',
         'new_C_w_available': False, 'new_K_available': False} for i, (nu,va) in enumerate(run.PAIRS,1)])
    lines = ['# Batch3 stopped on AC loss', '',
        'Probe1 was aborted by Windows Job supervisor, returncode125, AC_LOST_OR_CRITICAL_BATTERY with AC0. This is NOT a timeout or an exact-evaluator numerical failure.',
        f"Wall={attempts[0]['wall_seconds']}s; Job CPU={attempts[0]['cpu_seconds']}s. Current-controller campaign wall={ledger['budget_session_wall_seconds']}s; measured CPU={ledger['total_CPU_seconds']}s.",
        'No C,w completed; exact catalog remains145. Probe2/3, new SKR and new ALT_OPT are NOT_RUN. Do not call the old26/26 result a fresh Batch3 result.',
        'Original Sleep state restored; no Python worker remains;885 protected files unchanged.',
        f'Live power at audit: {json.dumps(power)}.',
        f'Original unreset deadline: {deadline.isoformat()}; audit: {now.isoformat()}. Stop did not grant a fresh3h budget.',
        'Reconnect stable AC before further AP. Do not automatically rerun aborted probe1. A later continuation must preserve exact keys, prior attempts and the original deadline; if expired, fresh scope/runtime approval is required.',
        'Two earlier selection/controller preflight failures and snapshots are archived separately; no historical numerical artifact or scientific evaluator was modified.',
        'No formula/precision/quadrature/MI/Holevo/ALT_OPT changes, interpolation or lifecycle promotion.']
    (out/'safety_stop_audit.md').write_text('\n\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
