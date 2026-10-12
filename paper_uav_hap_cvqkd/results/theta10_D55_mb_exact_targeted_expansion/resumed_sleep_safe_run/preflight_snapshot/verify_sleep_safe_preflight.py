"""Read-only receipts verification plus one native dummy with simulated AC loss."""
import hashlib
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from unittest.mock import patch

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.windows_sleep_safe_supervision import WindowsPower,supervised_process

before=json.loads((OUT/"input_manifest_before.json").read_text())
assert before==json.loads((OUT/"input_manifest_after.json").read_text())
for name,digest in before.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
report=json.loads((OUT/"run_report.json").read_text())
assert hashlib.sha256((ROOT/"scripts/windows_sleep_safe_supervision.py").read_bytes()).hexdigest()==report["supervisor_helper_sha256"]
assert report["new_source_probes_started"]==0 and not report["new_budget_approved"]
required=("power_and_supervisor_preflight.json","probe_execution_ledger.csv","new_exact_mb_sources.csv",
    "updated_mb_catalog.csv","old_vs_new_mb_skr.csv","top_two_candidates.csv","alt_opt_recheck.csv","run_report.md","run_report.json")
assert all((OUT/name).is_file() for name in required)
assert len(list(csv.DictReader((OUT/"updated_mb_catalog.csv").open())))==139
assert not list(csv.DictReader((OUT/"new_exact_mb_sources.csv").open()))
assert report["preflight"]["status"]=="CURRENTLY_VERIFIED_PASS"
assert all(r["wall_limit_respected"] and r["worker_cleanup_verified"] and r["sleep_prevention"]["released_verified"]
           for r in report["preflight"]["dummy_jobs"])
if "--artifacts-only" in sys.argv:
    print("FINAL PASS: 9 output paths, native power/sleep/dummy receipts, 139 MB, 709 preserved hashes; no AP/new budget confirmation")
    raise SystemExit(0)
original_read=WindowsPower.read
calls=0
def simulated_read(self):
    global calls
    status=original_read(self)
    calls+=1
    return status if calls==1 else {**status,"ac":0}
marker="sleep_safe_power_loss_dummy_"+uuid.uuid4().hex
with patch.object(WindowsPower,"read",simulated_read):
    with tempfile.TemporaryFile(mode="w+",encoding="utf-8") as log:
        receipt=supervised_process([sys.executable,"-c","while True: pass",marker],1.2,log)
assert receipt["returncode"]==125
assert receipt["power_watch"]["abort_reason"]=="AC_LOST_OR_CRITICAL_BATTERY"
assert receipt["wall_limit_respected"] and receipt["no_watchdog_thread_remaining"]
assert receipt["sleep_prevention"]["active_verified"] and receipt["sleep_prevention"]["released_verified"]
cleanup=subprocess.run(["powershell","-NoProfile","-Command",
    "$n=@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {$_.CommandLine -like '*"+marker+"*'}).Count; if ($n) {throw 'Dummy remains'}"],capture_output=True,text=True,check=True)
receipt.update(test="SIMULATED_AC_LOSS_NATIVE_JOB_TERMINATION",power_read_only_injected_for_dummy=True,
    physical_AC_was_NOT_changed=True,worker_cleanup_verified=True)
(OUT/"simulated_power_loss_dummy.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
print("CURRENTLY_VERIFIED_PASS: native simulated AC-loss abort125; sleep lease released; dummy cleanup; 709 protected hashes; no AP")
