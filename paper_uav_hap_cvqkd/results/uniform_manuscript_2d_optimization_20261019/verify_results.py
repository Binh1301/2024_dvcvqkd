"""Saved evidence and source/provenance validation; no SKR/source rerun."""
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from scripts.exact_cache_provenance import verify_source_payload

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
start=read(HERE/'startup_manifest.json')
summary=read(HERE/'summary.json')
with (HERE/'all_candidates.csv').open(encoding='utf-8',newline='') as stream:
    rows=list(csv.DictReader(stream))
assert len(rows)==summary['all_candidates']
assert len({r['VA_hex'] for r in rows})==len(rows)
assert all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in summary['checks'])
assert all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in [read(HERE/'numerical_test_receipt.json')])
control=read(HERE/'source_parity_control.json')
assert control['status']=='CURRENTLY_VERIFIED_PASS' and control['ensemble_hash_match']
assert control['C_difference']==0 and control['w_difference']==0
best=max(rows,key=lambda r:float(r['K_raw']))
assert best['VA_hex']==summary['best']['VA_hex']
channel_hash=sha(HERE/'channel_once.json')
source_checks=[]
for row in rows:
    path=ROOT/row['source_path'];payload=read(path)
    verify_source_payload(payload,payload['source_settings'])
    assert sha(path)==row['source_sha256']
    assert payload['ensemble_hash']==row['ensemble_hash'] and payload['support_size']==256
    assert float.fromhex(payload['nu_mb_raw_hex'])==0
    assert payload['V_A_hex']==row['VA_hex']
    assert float(row['C'])==payload['C'] and float(row['w'])==payload['w']
    assert channel_hash==row['channel_sha256']
    assert min(float(row[k]) for k in ('nu_1','nu_2','nu_3'))>=1
    V,W,Z=1+float(row['VA']),float(row['W']),float(row['Z'])
    gamma=np.array([[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]])
    omega=np.kron(np.eye(2),np.array([[0.,1.],[-1.,0.]]))
    assert np.linalg.eigvalsh(gamma).min()>0 and np.linalg.eigvalsh(gamma+1j*omega).min()>0
    numerical=np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
    assert max(abs(numerical-np.sort([float(row['nu_1']),float(row['nu_2'])])))<1e-10
    assert abs(float(row['K_raw'])-(float(row['beta_I_AB'])-float(row['chi_BE'])))<2e-18
    assert math.isclose(float(row['beta_I_AB']),.95*float(row['I_AB_2D']),abs_tol=2e-18)
    if row['source_origin']=='FRESH_EXACT_SOURCE_SEPARATE_CACHE':
        receipt=read(HERE/'source_receipts'/(row['ensemble_hash']+'.json'))
        final=receipt['diagnostic']['fallback_rows'][-2:]
        assert len(final)==2 and all(r['resolved'] and r['rank']==256 for r in final)
        assert all(Decimal(r['minimum_eigenvalue'])>0 for r in final)
        for name in ('C','w'):
            a,b=map(Decimal,(final[0][name],final[1][name]))
            assert abs(a-b)<=Decimal('1e-7')+Decimal('1e-6')*max(abs(a),abs(b))
        for name,digest in receipt.get('additional_producers_sha256',{}).items():
            assert sha(HERE/name)==digest
    source_checks.append(dict(VA=float(row['VA']),source_verified=True))
protocol=read(HERE/'search_protocol.json')
covered={float(row['VA']) for row in rows}
assert set(protocol['coarse_grid']+protocol['fine_grid']+protocol['local_refinement']['candidates'])<=covered
for path in (HERE/'source_logs').glob('*.json'):
    job=read(path)
    assert job['returncode']==0 and not job['deadline_exceeded'] and job['elapsed_seconds']<3720
with (HERE/'MI_convergence.csv').open(encoding='utf-8',newline='') as stream:
    convergence=list(csv.DictReader(stream))
for row in rows:
    group=[x for x in convergence if x['VA_hex']==row['VA_hex']]
    assert {int(x['order']) for x in group}=={16,32,64}
    assert max(abs(float(x['difference_from_GH64'])) for x in group)<2e-13
    assert float(next(x['I_AB_2D'] for x in group if int(x['order'])==64))==float(row['I_AB_2D'])
with (HERE/'same_MB_MI_kernel_check.csv').open(encoding='utf-8',newline='') as stream:
    direct=list(csv.DictReader(stream))
assert len(direct)==3 and max(abs(float(x['residual'])) for x in direct)<2e-13
assert sha(ROOT/'scripts/optimize_uniform_manuscript_2d.py')==summary['producer_sha256']
assert sha(ROOT/'results/manuscript_homodyne_noise_recheck_20261019/result.json')==summary['MB_result_sha256']
mutable={'paper_uav_hap_cvqkd/'+name for name in ('docs/EVIDENCE.md','docs/DECISION_LOG.md',
         'docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md')}
changed=[name for name,value in start['protected_sha256'].items()
         if not (ROOT.parent/name).is_file() or sha(ROOT.parent/name)!=value]
assert not set(changed)-mutable,sorted(set(changed)-mutable)
assert sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==start['frozen_actual_sha256']
figures=[]
for stem in ('uniform_SKR_vs_VA','uniform_MI_Holevo_vs_VA','uniform_vs_fixed_MB','uniform_SKR_local_refinement'):
    png,pdf=HERE/(stem+'.png'),HERE/(stem+'.pdf')
    with Image.open(png) as image:
        assert min(image.info['dpi'])>=300
        dimensions=image.size
    assert pdf.read_bytes().startswith(b'%PDF') and b'/Subtype /Image' not in pdf.read_bytes()
    figures.append(dict(figure=stem,png_pixels=dimensions,vector_PDF=True,PNG_dpi_at_least_300=True))
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
assert diff.returncode==0,diff.stdout+diff.stderr
assets=list(HERE.rglob('*'))+[ROOT/'docs/UNIFORM_MANUSCRIPT_2D_OPTIMIZATION_VI.md']
receipt=dict(status='CURRENTLY_VERIFIED_PASS',scope='exact-tested Uniform numerical and artifact/provenance checks',
             protected_preexisting_files=len(start['protected_sha256']),
             unchanged_preexisting_files=len(start['protected_sha256'])-len(changed),
             task_ledger_updates=changed,unexpected_changes=[],candidate_count=len(rows),
             source_checks=source_checks,all_symplectic_eigenvalues_physical=True,
             source_parity_control_pass=True,all_recorded_grid_candidates_present=True,figures=figures,
             independent_covariance_uncertainty_and_matrix_spectrum_checks=True,
             all_GH16_32_64_checked=True,original_MB_tensor_kernel_checked=True,
             no_source_or_SKR_interpolation=True,MB_source_not_used_for_Uniform=True,
             production_or_optical_or_frozen_changes=False,
             scientific_diagnostic='normalized2D MI plus manuscript homodyne Holevo',
             global_optimality_certificate=False,security_status='UNVALIDATED_SECURITY_MODEL',
             lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',git_diff_check='CURRENTLY_VERIFIED_PASS',
             verifier_sha256=sha(Path(__file__)),artifact_sha256={str(p.relative_to(ROOT)):sha(p)
             for p in assets if p.is_file() and p.name!='validation_receipt.json'})
(HERE/'validation_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('artifact_sha256','source_checks')},indent=2))
