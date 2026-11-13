"""Read-only verification of preflight, old inputs and source identity."""
from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in json.loads((OUT/'artifact_hashes.json').read_text()).items():
    assert sha(OUT/name)==h,name
for filename in ['input_hashes.json','protected_inputs.json']:
    for name,h in json.loads((OUT/filename).read_text()).items():assert sha(ROOT/name)==h,name
v=json.loads((OUT/'verification.json').read_text())
for name,h in v['source_hashes'].items():assert sha(ROOT/name)==h,name
r=json.loads((OUT/'readiness.json').read_text())
assert r['requested_task_complete'] is False and r['selected_physical_branch'] is None
assert r['critical_attenuation_fixed_db'] is r['critical_attenuation_reoptimized_db'] is None
assert not any(r[k] for k in ['new_channel_evaluations','new_MI_evaluations','new_Holevo_evaluations','new_source_Cw_computations','new_optimizer_calls'])
log=(OUT/'unit_tests.log').read_text()
assert 'Ran 8 tests' in log and '\nOK\n' in log
print(json.dumps({'audit_software_verification':'CURRENTLY_VERIFIED_PASS',
      'physical_threshold_study':'NOT_RUN','requested_task_complete':False,
      'root_pushforward_tests':8,'protected_previous_files':1070},indent=2))
