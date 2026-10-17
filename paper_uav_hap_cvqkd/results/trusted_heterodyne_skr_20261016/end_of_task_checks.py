import base64,difflib,hashlib,json,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.run_ao_effective_channel_no_fading_noise_reference import verify_protected
root=Path.cwd();out=root/'results/trusted_heterodyne_skr_20261016';read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=read(out/'startup_manifest.json');completion=read(out/'completion_integrity_receipt.json');inputs=read(out/'inputs.json');full=read(out/'full_receipt.json')
changed=verify_protected(start)
assert changed==[]
for p,h in inputs['producers'].items():assert sha(root/p)==h,p
for p,h in full['output_sha256'].items():assert sha(out/p)==h,p
for p,h in completion['receipts_and_report_sha256'].items():assert sha(out/p)==h,p
assert sha(root/'docs/TRUSTED_HETERODYNE_SKR_REPORT_VI.md')==completion['canonical_report_sha256']
new=['src/trusted_heterodyne_skr.py','scripts/run_trusted_heterodyne_skr.py','tests/test_trusted_heterodyne_skr.py','configs/trusted_heterodyne_skr.json','docs/TRUSTED_HETERODYNE_SKR_REPORT_VI.md']
patch=[];docs={};preservation={}
for p,b64 in start['documentation_before_base64'].items():
 before=base64.b64decode(b64).decode('utf-8').replace('\r\n','\n');after=(root/p).read_text(encoding='utf-8');docs[p]=sha(root/p)
 patch.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='a/paper_uav_hap_cvqkd/'+p,tofile='b/paper_uav_hap_cvqkd/'+p))
 if p in ('docs/EVIDENCE.md','docs/DECISION_LOG.md'):preservation[p]=after.startswith(before)
 if p in ('docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md'):preservation[p]=before.split('\n',1)[1] in after
for p in new:
 patch.extend(difflib.unified_diff([], (root/p).read_text(encoding='utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile='b/paper_uav_hap_cvqkd/'+p))
patchtext=''.join(patch);(out/'current_task_changes.patch').write_text(patchtext,encoding='utf-8',newline='\n')
whitespace=[i for i,x in enumerate(patchtext.splitlines(),1) if x.startswith('+') and not x.startswith('+++') and x.rstrip()!=x]
assert not whitespace and all(preservation.values())
git=['git','-c','core.longpaths=true','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol']
res=subprocess.run(git+['diff','--check'],capture_output=True,text=True);assert res.returncode==0,res.stdout
branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip();head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert branch==start['branch'] and head==start['HEAD']
receipt=dict(status='CURRENTLY_VERIFIED_PASS',checked_utc=datetime.now(timezone.utc).isoformat(),completion_receipt_sha256=sha(out/'completion_integrity_receipt.json'),protected_files=len(start['protected_hashes']),protected_changes=changed,producers_unchanged=True,full_output_hashes_verified=True,receipt_hashes_verified=True,canonical_report_matches=True,documentation_old_content_preserved=preservation,documentation_sha256=docs,git_branch=branch,git_HEAD=head,git_diff_check={'exit_code':res.returncode,'stdout':res.stdout,'stderr':res.stderr},new_line_whitespace_issues=whitespace,current_task_patch_sha256=sha(out/'current_task_changes.patch'),end_state='COMPLETE_STOP')
(out/'post_documentation_integrity_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
