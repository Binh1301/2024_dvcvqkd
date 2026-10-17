"""Final preservation/diff receipt; no numerical rerun or production mutation."""
import base64,difflib,hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=read(OUT/'startup_manifest.json');receipt=read(OUT/'validation_receipt.json')
changed=[p for p,h in start['protected_hashes'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
assert not changed,changed
for p,h in receipt['producer_sha256'].items():assert sha(ROOT/p)==h,p
for p,h in receipt['artifact_sha256'].items():assert sha(OUT/p)==h,p
assert sha(ROOT/'docs/FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md')==receipt['canonical_report_sha256']
patch=[];docs={};preserved={}
for p,b64 in start['documentation_before_base64'].items():
    before=base64.b64decode(b64).decode('utf-8').replace('\r\n','\n');after=(ROOT/p).read_text(encoding='utf-8')
    docs[p]=sha(ROOT/p)
    if p in ('docs/EVIDENCE.md','docs/DECISION_LOG.md'):preserved[p]=after.startswith(before)
    if p in ('docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md'):preserved[p]=before.split('\n',1)[1] in after
    patch.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/paper_uav_hap_cvqkd/'+p,tofile='b/paper_uav_hap_cvqkd/'+p))
for p in ('scripts/probe_full_geometry_runtime.py','scripts/audit_full_geometry_fading_skr.py','docs/FULL_GEOMETRY_FADING_SKR_AUDIT_VI.md'):
    patch.extend(difflib.unified_diff([],(ROOT/p).read_text(encoding='utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile='b/paper_uav_hap_cvqkd/'+p))
text=''.join(patch);(OUT/'current_task_changes.patch').write_text(text,encoding='utf-8',newline='\n')
whitespace=[i for i,x in enumerate(text.splitlines(),1) if x.startswith('+') and not x.startswith('+++') and x.rstrip()!=x]
assert all(preserved.values()) and not whitespace
branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert branch==start['branch'] and head==start['HEAD']
res=subprocess.run(['git','-c','core.longpaths=true','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--check'],capture_output=True,text=True)
assert res.returncode==0,res.stdout
end=dict(status='CURRENTLY_VERIFIED_PASS',verification_scope='Final integrity and documentation only; numerical strict failures retained',
         checked_utc=datetime.now(timezone.utc).isoformat(),validation_receipt_sha256=sha(OUT/'validation_receipt.json'),
         protected_files=len(start['protected_hashes']),protected_changes=changed,old_documentation_preserved=preserved,
         all_producer_artifact_hashes_match=True,canonical_report_matches=True,documentation_sha256=docs,
         git_branch=branch,git_HEAD=head,git_diff_check=dict(exit_code=res.returncode,stdout=res.stdout,stderr=res.stderr),
         new_line_whitespace_issues=whitespace,scoped_patch_sha256=sha(OUT/'current_task_changes.patch'),
         strict_numerical_comparisons=dict(passed=89,failed=5,status='FAILED'),production_code_changed=False,
         source_or_config_changed=False,security_functional_changed=False,frozen_model_changed=False,
         P1_P3_run=False,training_or_test_access=False,baseline_or_threshold_approval=False,end_state='AUDIT_COMPLETE_WITH_DOCUMENTED_DIFFERENCES_STOP')
(OUT/'completion_integrity_receipt.json').write_text(json.dumps(end,indent=2)+'\n',encoding='utf-8')
print(json.dumps(end,indent=2))
