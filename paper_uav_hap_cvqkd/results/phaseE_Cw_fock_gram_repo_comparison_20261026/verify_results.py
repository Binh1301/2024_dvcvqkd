"""Read-only Phase E input, stored-output and preservation checks."""
import csv
import hashlib
import json
from pathlib import Path
import mpmath as mp
import numpy as np

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def verify():
    start=read(OUT/'startup_manifest.json')
    for name,digest in start['protected'].items():assert sha(ROOT.parent/name)==digest,name
    metadata={r['name']:r for r in read(OUT/'inputs/source_metadata.json')}
    validations={r['source']:r for r in read(OUT/'input_validation.json')}
    for name,ref in metadata.items():
        assert sha(ROOT/ref['source_path'])==ref['source_sha256']
        assert read(ROOT/ref['source_path'])['ensemble_hash']==ref['ensemble_hash']
        a=np.load(OUT/'inputs'/f'{name}.npz');p,z=a['p'],a['alpha']
        assert len(p)==len(z)==256 and p.min()>0
        assert len(set(map(complex,z)))==256
        assert abs(p.sum()-1)<1e-12 and abs(p@z)<1e-12
        assert abs(2*p@abs(z)**2-float(ref['VA']))<1e-12
        assert sha_bytes(p)==validations[name]['PMF_sha256'] and sha_bytes(z)==validations[name]['alpha_sha256']
    receipts=read(OUT/'job_receipts.json');assert len(receipts)==66
    complete=0;values=0;incomplete=[]
    for r in receipts:
        method='independent_fock_Cw.py' if r['method']=='A' else 'independent_gram_Cw.py'
        assert sha(OUT/method)==r['producer_sha256']
        if r['status']!='COMPLETED':
            assert not r['output'];incomplete.append(r['job']);continue
        complete+=1
        result=read(OUT/r['output'])
        expected=r['NF'] if r['method']=='A' else len(np.load(OUT/'inputs'/f"{r['source']}.npz")['p'])
        assert len(result['spectrum'])==expected
        for row in result['rows']:
            values+=1
            assert mp.isfinite(mp.mpf(row['C'])) and mp.isfinite(mp.mpf(row['w_direct'])) and mp.isfinite(mp.mpf(row['w_residual']))
            assert row['digits']==r['digits']
    comparison=rows(OUT/'Cw_comparison.csv');assert len(comparison)==6
    rounded=[]
    with mp.workdps(100):
        for r in comparison:
            ref=metadata[r['source']]
            if r['method']=='Repository':continue
            dc=mp.mpf(r['C'])-mp.mpf(float(ref['C']))
            dw=mp.mpf(r['w'])-mp.mpf(float(ref['w']))
            assert abs(dc-mp.mpf(r['delta_C_vs_repo']))<mp.mpf('1e-58')
            assert abs(dw-mp.mpf(r['delta_w_vs_repo']))<mp.mpf('1e-58')
            rounded.append(float(r['C'])==float(ref['C']) and float(r['w'])==float(ref['w']))
    Z=rows(OUT/'Z_SKR_sensitivity.csv');assert len(Z)==3
    assert all(r['chi_BE']==r['K_raw']=='' for r in Z if r['method']!='Repository')
    assert read(OUT/'downstream_execution.json')['new_alternative_Holevo_SKR_evaluations']==0
    assert read(OUT/'convergence_assessment.json')['overall']=='INCONCLUSIVE'
    assert len(read(OUT/'focused_checks.json')['checks'])==11
    assert all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in read(OUT/'sanity_verification.json'))
    required=['mathematical_derivation.md','repository_Cw_audit.md','independent_fock_Cw.py','independent_gram_Cw.py',
        'Cw_comparison.csv','convergence_diagnostics.csv','Cw_numerical_stability.md','Z_SKR_sensitivity.csv',
        'validation_report_vi.md','artifact_integrity_report.md']
    for name in required:assert (OUT/name).is_file(),name
    result=dict(verification_status='CURRENTLY_VERIFIED_PASS',scientific_result='INCONCLUSIVE',
        protected_historical_files=len(start['protected']),existing_catalog_sources_modified=0,
        completed_jobs=complete,limited_jobs=len(incomplete),numeric_diagnostic_rows=values,
        six_small_case_comparisons='PASS (MB4 aliases Uniform4)',focused_checks=11,
        rounded_best_tested_Cw_match_cached_binary64=all(rounded),
        full256_source_support_verified=False,source_evidence_upgrades=0,new_channel_integrations=0,
        new_alternative_Holevo_SKR_evaluations=0,PHASE_B_STRICT_READY=False,result_scope='DIAGNOSTIC_ONLY')
    if (OUT/'artifact_manifest.json').exists():
        manifest=read(OUT/'artifact_manifest.json')
        for name,digest in manifest.items():assert sha(OUT/name)==digest,name
        result['sealed_artifacts']=len(manifest)
    return result


def sha_bytes(array):return hashlib.sha256(array.tobytes()).hexdigest()


if __name__=='__main__':print(json.dumps(verify(),indent=2))
