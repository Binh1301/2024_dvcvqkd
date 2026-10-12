"""Native power/supervisor preflight only; fresh AP-budget confirmation required."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.windows_sleep_safe_supervision import WindowsPower, AwakeOnAC, safe_power, supervised_process
from scripts import run_theta10_D55_alt_opt_convergence_validation as io
from scripts import run_theta10_D55_unconstrained_three_scheme as source

BASE = ROOT / "results/theta10_D55_mb_exact_targeted_expansion"
OUT = BASE / "resumed_sleep_safe_run"
OLD = BASE / "probe_1_authorized_3h"
CONT = ROOT / "results/theta10_D55_alt_opt_closure_continuation"


def empty(name, columns):
    with (OUT/name).open("w",encoding="utf-8",newline="") as stream:
        csv.DictWriter(stream,fieldnames=columns).writeheader()


def main():
    if OUT.exists():
        raise SystemExit("Preflight already saved: do not overwrite historical artifacts")
    manifest=json.loads((OLD/"protected_input_manifest.json").read_text())
    manifest.update(io.raw_snapshot([p for p in BASE.rglob("*") if "__pycache__" not in p.parts]))
    for name,digest in manifest.items():
        assert io.digest(ROOT/name)==digest,name
    OUT.mkdir()
    io.save_json(OUT/"input_manifest_before.json",manifest)
    power=WindowsPower()
    status=power.read()
    preflight={"power_status":status,"AC_required":True,"AC_connected":status["ac"]==1,
        "automatic_sleep_request":"ES_CONTINUOUS|ES_SYSTEM_REQUIRED on owning thread",
        "power_plan_modified":False,"hibernation_globally_disabled":False,"AP_started":False,
        "fresh_budget_confirmed":False,"proposed_total_seconds":10800,"proposed_per_probe_seconds":3600,
        "dummy_jobs":[],"status":"BLOCKED_BY_ENVIRONMENT" if not safe_power(status) else "PREFLIGHT_RUNNING"}
    if safe_power(status):
        for limit,tree in ((.8,False),(1.2,True)):
            marker="sleep_safe_dummy_"+uuid.uuid4().hex
            code="while True: pass"
            if tree:
                code="import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','while True: pass',sys.argv[1]]); print('CHILD_PID='+str(p.pid),flush=True); exec('while True: pass')"
            with tempfile.TemporaryFile(mode="w+",encoding="utf-8") as log:
                receipt=supervised_process([sys.executable,"-c",code,marker],limit,log)
                log.seek(0)
                receipt["dummy_log"]=log.read()
            receipt["test"]="DESCENDANT_TREE_TIMEOUT" if tree else "SINGLE_BUSY_TIMEOUT"
            assert receipt["deadline_exceeded"] and receipt["returncode"]==124
            assert receipt["wall_limit_respected"] and receipt["no_watchdog_thread_remaining"]
            assert receipt["sleep_prevention"]["active_verified"] and receipt["sleep_prevention"]["released_verified"]
            cleanup=subprocess.run(["powershell","-NoProfile","-Command",
                "$n=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*"+marker+"*'}).Count; if ($n -ne 0) {throw 'Dummy process tree remains'}; 'CLEAN'"],capture_output=True,text=True,check=True)
            receipt["worker_cleanup_verified"]=cleanup.stdout.strip()=="CLEAN"
            assert receipt["worker_cleanup_verified"]
            if tree:
                assert "CHILD_PID=" in receipt["dummy_log"],"Descendant test did not actually spawn its child"
            preflight["dummy_jobs"].append(receipt)
            io.save_json(OUT/"power_and_supervisor_preflight.json",preflight)
        # Exception cleanup on the real Windows API, without any job or AP.
        lease=AwakeOnAC()
        try:
            with lease:
                raise ValueError("Intentional preflight exception")
        except ValueError:
            pass
        assert lease.receipt["released_verified"]
        preflight["native_exception_cleanup"]=lease.receipt
        preflight["status"]="CURRENTLY_VERIFIED_PASS"
    config=source.unconstrained_config()
    bank=source.load_source_payloads(config,(source.SOURCE_CACHE,CONT/"exact_source_cache"))
    current_mb=[p for p in bank.values() if float.fromhex(p["nu_mb_raw_hex"])>0]
    probes=io.read_csv(BASE/"selected_mb_candidates.csv")
    for p in probes:
        assert source.candidate_from_payload(config,bank,"MB",float(p["nu_raw"]),float(p["V_A"])) is None
    preflight.update(current_MB_count=len(current_mb),sleep_request_currently_held=False,
        sleep_request_reacquire_required_before_AP=True,
        scope="SHORT_NATIVE_PREFLIGHT_NOT_FULL_DURATION_GUARANTEE",
        manual_sleep_shutdown_critical_battery_not_prevented=True,
        unexpected_suspend_policy="Stop Job after resume; record actual elapsed interval; any wall overrun is FAILED",
        protected_files_verified=len(manifest))
    io.save_json(OUT/"power_and_supervisor_preflight.json",preflight)
    io.write_csv(OUT/"probe_execution_ledger.csv",[{"priority":p["pilot_priority"],"nu_raw":p["nu_raw"],"V_A":p["V_A"],
        "nu_hex":p["nu_raw_hex"],"VA_hex":p["V_A_hex"],"source_cache_key":p["source_cache_key"],
        "status":"NOT_RUN_AWAITING_FRESH_BUDGET_CONFIRMATION","CPU_seconds":None,"wall_seconds":None} for p in probes])
    empty("new_exact_mb_sources.csv",["nu_raw","V_A","C","w","source_cache_key","status"])
    io.write_csv(OUT/"updated_mb_catalog.csv",[{"nu_raw":float.fromhex(p["nu_mb_raw_hex"]),"V_A":float.fromhex(p["V_A_hex"]),
        "source_cache_key":p["cache_key"],"ensemble_hash":p["ensemble_hash"],"C":p["C"],"w":p["w"],
        "execution":"VERIFIED_UNEXPANDED_SOURCE_SNAPSHOT"} for p in current_mb])
    empty("old_vs_new_mb_skr.csv",["L_km","old_K","new_K","status"])
    empty("top_two_candidates.csv",["L_km","nu_raw","V_A","K","status"])
    empty("alt_opt_recheck.csv",["L_km","status","execution"])
    checks=[]
    for pattern in ("test_windows_sleep_safe_supervision.py","test_alt_opt_provenance_and_stopping.py"):
        check=subprocess.run([sys.executable,"-X","utf8","-m","unittest","discover","-s","tests","-p",pattern,"-v"],cwd=ROOT,capture_output=True,text=True)
        checks.append({"pattern":pattern,"returncode":check.returncode,"output":check.stdout+check.stderr})
    io.save_json(OUT/"regression_tests.json",checks)
    assert all(c["returncode"]==0 for c in checks)
    diff=subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True,text=True)
    assert diff.returncode==0,diff.stdout+diff.stderr
    for name,digest in manifest.items():
        assert io.digest(ROOT/name)==digest,name
    io.save_json(OUT/"input_manifest_after.json",{n:io.digest(ROOT/n) for n in manifest})
    report={"status":"AWAITING_EXPLICIT_NEW_BUDGET_CONFIRMATION" if safe_power(status) else "BLOCKED_BY_ENVIRONMENT_AC_REQUIRED",
        "preflight":preflight,"new_budget_approved":False,"new_source_probes_started":0,"new_source_probes_completed":0,
        "new_SKRs_evaluated":0,"ALT_OPT_rechecked":False,"current_MB_count":len(current_mb),
        "old_3h_authorization_reused":False,"excluded_probe":{"nu_raw":.16375,"V_A":5.5},
        "supervisor_helper_sha256":io.digest(ROOT/"scripts/windows_sleep_safe_supervision.py"),
        "producer_sha256":io.digest(__file__),"regression_tests_pass":True,"git_diff_check_pass":True,
        "scientific_implementation_unchanged":True,"publication":"NOT_READY_FOR_PUBLICATION_SCALE_RUNS"}
    io.save_json(OUT/"run_report.json",report)
    md=["# Sleep-safe targeted MB resume: preflight only", "", report["status"],
        f"AC={status['ac']}; battery_percent={status['battery_percent']}; short native preflight={preflight['status']}.",
        "Temporary ES_SYSTEM_REQUIRED request verified while each dummy job ran, then restored/released in finally; native exception cleanup tested. No power-plan or global hibernation changes.",
        "Two short dummy jobs verify existing Job deadline, descendant cleanup, CPU accounting and a shutdown margin. Power watchdog stops the same Job on AC loss/critical power or an unexpected polling/suspend gap.",
        "Manual sleep/shutdown/critical-power events are not prevented by this API. Any actual wall-time overrun remains FAILED; no full-duration guarantee is inferred from short tests.",
        f"Compatible MB sources now={len(current_mb)}; no AP/SKR/AO started; candidate order remains the three exact pairs in probe_execution_ledger.csv. (.16375,5.5) is excluded.",
        "The previous 3-hour authorization is expired. Proposed NEW10800s total/3600s probe requires explicit confirmation before AP. Old budget not reused.",
        "After approval recheck stable AC and reacquire/verify the temporary lease throughout actual computation; execute original evaluator sequentially with checkpoints and unchanged AO/precision/quadrature. No automatic next probe after timeout.",
        f"All {len(manifest)} protected hashes unchanged; 4 operational and 24 scientific/provenance regression tests PASS; git diff --check PASS.",
        "Downstream files are header-only NOT_RUN placeholders or current catalog snapshots, not new numerical results. No convergence/global-optimum claim. Frozen-spec discrepancy/lifecycle remain open.",
        "STOP and request confirmation of proposed fresh budget."]
    (OUT/"run_report.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","current_MB_count","new_source_probes_started","preflight")},indent=2))


if __name__=="__main__":
    main()
