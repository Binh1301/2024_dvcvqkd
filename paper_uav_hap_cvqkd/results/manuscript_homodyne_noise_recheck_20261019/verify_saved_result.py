"""Verify saved single-point evidence and preservation; rerun no SKR calculation."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda name: json.loads((OUT/name).read_text(encoding='utf-8'))
start, result = read('startup_manifest.json'), read('result.json')
mutable = {'paper_uav_hap_cvqkd/'+name for name in (
    'docs/EVIDENCE.md', 'docs/DECISION_LOG.md', 'docs/PROJECT_STATE.md',
    'docs/NEXT_ACTIONS.md', '.agent/SESSION_HANDOFF.md')}
changed = [name for name, value in start['protected_sha256'].items()
           if not (ROOT.parent/name).is_file() or sha(ROOT.parent/name)!=value]
unexpected = sorted(set(changed)-mutable)
assert not unexpected, unexpected
assert sha(ROOT/'scripts/recheck_manuscript_homodyne_noise.py')==result['producer_sha256']
assert sha(Path(start['manuscript_path']))==result['manuscript_sha256']
assert sha(OUT/'request.txt')==start['request_sha256']
for name, value in result['inputs_sha256'].items():
    assert sha(ROOT/name)==value, name
assert sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==start['frozen_actual_sha256']
assert all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in result['checks'])
assert len(result['checks'])==17
assert result['source_audit']['literal_PDF_compatibility'].startswith('FAILED_VARIANCE_CONVENTION')
assert not result['literal_VA_relabel_audit']['physical']
model = result['model']
assert model['K']>0 and model['K_1D']<0
assert math.isclose(model['K'],.95*model['I_AB']-model['chi_BE'],abs_tol=2e-18)
assert math.isclose(model['eta_f_xi_f'],
                    model['variance_sqrt_eta']*5.475+.0186*model['mean_eta'],abs_tol=1e-18)
with (OUT/'required_table.csv').open(encoding='utf-8',newline='') as stream:
    table=list(csv.DictReader(stream))
assert len(table)==19 and all(float(row['value'])==model[row['parameter']] for row in table)
max_mi_delta=max(abs(row['I_AB_2D']-result['convergence'][-1]['I_AB_2D']) for row in result['convergence'])
assert max_mi_delta<2e-13
diff = subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
assert diff.returncode==0, diff.stdout+diff.stderr
paths=list(OUT.glob('*'))+[ROOT/'docs/MANUSCRIPT_HOMODYNE_NOISE_RECHECK_VI.md']
receipt=dict(status='CURRENTLY_VERIFIED_PASS', scope='saved-evidence-integrity-and-protected-file-preservation',
             numerical_checks=len(result['checks']), protected_tracked_files=len(start['protected_sha256']),
             unchanged_tracked_files=len(start['protected_sha256'])-len(changed),
             authorized_documentation_updates=changed,unexpected_changes=unexpected,
             producer_and_input_hashes_verified=True,required_table_rows=len(table),
             maximum_MI_difference_GH16_32_64=max_mi_delta,
             literal_PDF_compatibility='FAILED_VARIANCE_AND_MB_NOTATION; not a literal-point security result',
             reference_digits_reproduced=False, security_status='UNVALIDATED_SECURITY_MODEL',
             lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',git_diff_check='CURRENTLY_VERIFIED_PASS',
             scientific_source_changed=False,source_cache_changed=False,frozen_spec_changed=False,
             protected_preexisting_scripts_changed=False,optimization_run=False,
             training_or_test_dataset_or_final_test_access=False, publication_evaluation=False,
             verifier_sha256=sha(Path(__file__)),
             artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths
                              if p.is_file() and p.name!='validation_receipt.json'})
(OUT/'validation_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='artifact_sha256'},indent=2))
