"""Read-only reproduction/integrity checks; --seal only seals this new namespace."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def save(name,value):(OUT/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))


def verify(sealed=True):
    task=read(OUT/'protocol.json');startup=read(OUT/'startup_manifest.json')
    for name,digest in startup['protected'].items():
        assert sha(ROOT.parent/name)==digest,'Historical file changed: '+name
    assert sha(ROOT/task['grid_origin'])==task['grid_origin_sha256']
    assert task['angles_deg']==read(ROOT/task['grid_origin'])['angles_deg']
    assert set(task['previous_angles_deg'])<=set(task['angles_deg'])
    assert sha(ROOT/task['physical_protocol_path'])==task['physical_protocol_sha256']
    assert sha(ROOT/task['canonical_evaluator_path'])==task['canonical_evaluator_sha256']
    assert sha(OUT/'sweep.py')==task['sweep_producer_sha256']
    assert sha(OUT/'source_pool.csv')==task['source_pool_sha256']
    base=ROOT/task['baseline_path']
    assert sha(base/'diagnostic_results.csv')==task['baseline_results_sha256']
    assert sha(base/'artifact_manifest.json')==task['baseline_manifest_sha256']
    assert sha(base/'channel_contexts.json')==task['baseline_contexts_sha256']
    sources=rows(OUT/'source_pool.csv');assert len(sources)==212
    by_hash={r['ensemble_hash']:r for r in sources};assert len(by_hash)==212
    assert len({r['canonical_source_identity'] for r in sources})==212
    for s in sources: assert sha(ROOT/s['source_path'])==s['source_sha256']
    data=rows(OUT/'diagnostic_skr_61_angles.csv');assert len(data)==12932
    pairs={};reused=0
    baseline={(int(float(r['zenith_deg'])),r['ensemble_hash']):r for r in rows(base/'diagnostic_results.csv')}
    max_rate=max_z=0.
    for r in data:
        a=int(float(r['zenith_deg']));key=(a,r['ensemble_hash'])
        assert key not in pairs;pairs[key]=r
        s=by_hash[key[1]]
        assert r['source_evidence_class']==s['classification']==s['source_evidence_class']
        assert r['source_id']==r['Cw_source_id']==s['canonical_source_identity']
        for k in ['VA','nu_raw','C','w']:assert float(r[k]).hex()==float(s[k]).hex()
        assert r['source_Cw_recomputed']=='False' and r['Cw_reused']=='True'
        assert r['result_scope']=='DIAGNOSTIC_ONLY' and r['correlation_policy']=='manuscript_eq14_direct'
        assert float(r['nu_repo'])==42.5*float(r['nu_raw'])
        if key in baseline:
            reused+=1;assert r['evaluation_origin']=='REUSED_NINE_ANGLE'
            old=baseline[key]
            for k in ['K_raw','I_AB','beta_I_AB','chi_BE','Z_manuscript_eq14','eta_f','xi_f','C','w']:
                assert float(r[k]).hex()==float(old[k]).hex()
        else:assert r['evaluation_origin']=='NEW_RATE_HISTORICAL_CW'
        if r['numerical_status']!='CURRENTLY_VERIFIED_PASS':
            assert not r['K_raw'] and not r['K_operational'] and r['reason'];continue
        k,mi,bmi,chi,t,xi,c,w,z=map(float,[r[n] for n in
            ['K_raw','I_AB','beta_I_AB','chi_BE','eta_f','xi_f','C','w','Z_manuscript_eq14']])
        assert all(math.isfinite(v) for v in [k,mi,bmi,chi,t,xi,c,w,z])
        assert float(r['K_operational'])==max(0,k)
        max_rate=max(max_rate,abs(k-(bmi-chi)))
        max_z=max(max_z,abs(z-(2*math.sqrt(t)*c-math.sqrt(2*t*xi*w))))
    assert reused==1908 and max_rate<=2e-15 and max_z<=2e-11
    checked={(int(float(r['zenith_deg'])),r['ensemble_hash']) for r in rows(OUT/'independent_validation.csv')
        if r['status']=='CURRENTLY_VERIFIED_PASS'}
    selected=rows(OUT/'best_scheme_by_angle.csv');assert len(selected)==183
    for a in task['angles_deg']:
        angle=[r for r in data if int(float(r['zenith_deg']))==a]
        assert len(angle)==212 and {r['ensemble_hash'] for r in angle}==set(by_hash)
        assert len(rows(OUT/f'angle_{a:02d}_candidates.csv'))==212
        ctx=read(OUT/f'angle_{a:02d}_context.json')
        assert ctx['numerical_status']=='CURRENTLY_VERIFIED_PASS' and ctx['numerical_experiment_accepted']
        assert not ctx['renormalized'] and not ctx['clipped']
        assert ctx['protocol_sha256']==task['physical_protocol_sha256']
        if a in task['previous_angles_deg']:
            old=next(c for c in read(base/'channel_contexts.json') if c['zenith_deg']==a)
            assert ctx==old
    physical=read(ROOT/task['physical_protocol_path'])
    for r in selected:
        a=int(float(r['zenith_deg']));valid=[c for (angle,_),c in pairs.items() if angle==a
            and c['numerical_status']=='CURRENTLY_VERIFIED_PASS']
        if r['scheme']=='Optimized Uniform 256-QAM':valid=[c for c in valid if c['family']=='Uniform']
        elif r['scheme']=='Fixed MB-shaped 256-QAM':valid=[c for c in valid if c['ensemble_hash']==physical['fixed_MB']['ensemble_hash']]
        if not valid:assert r['numerical_status']!='CURRENTLY_VERIFIED_PASS';continue
        assert float(r['K_raw'])==max(float(c['K_raw']) for c in valid)
        assert (a,r['ensemble_hash']) in checked
    for path in (ROOT/'results').glob('**/exact_source_cache/*.json'):
        assert path.relative_to(ROOT.parent).as_posix() in startup['protected'],'New source payload: '+str(path)
    assert not list(OUT.glob('**/exact_source_cache/*'))
    summary=read(OUT/'diagnostic_summary.json')
    assert summary['source_Cw_computations']==summary['source_generation_attempts']==0
    assert summary['strict_Phase_B_ready'] is False
    assert summary['source_evidence_counts']==dict(Counter(s['classification'] for s in sources))
    required=['diagnostic_skr_61_angles.csv','best_scheme_by_angle.csv','skr_vs_zenith.png',
        'skr_zero_crossing_zoom.png','optimal_parameters_vs_zenith.png','information_decomposition.png',
        'numerical_validation.md','artifact_integrity_report.md','validation_report_vi.md']
    for name in required:assert (OUT/name).is_file(),name
    if sealed:
        manifest=read(OUT/'artifact_manifest.json')
        for name,digest in manifest['files'].items():assert sha(OUT/name)==digest,'Artifact changed: '+name
    return dict(status='CURRENTLY_VERIFIED_PASS',result_scope='DIAGNOSTIC_ONLY',
        protected_historical_files=len(startup['protected']),candidate_rows=len(data),
        selected_rows=len(selected),reused_rows_unchanged=reused,new_candidate_evaluations=11024,
        duplicate_source_identities=0,duplicate_pairs=0,source_Cw_computations=0,
        source_generation_attempts=0,max_rate_residual=max_rate,max_direct_Eq14_residual=max_z,
        source_classifications_unchanged=True,strict_Phase_B_ready=False)


if __name__=='__main__':
    if sys.argv[1:]==['--seal']:
        if (OUT/'artifact_manifest.json').exists():raise FileExistsError('Do not overwrite seal')
        verify(sealed=False)
        files={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.name not in {'artifact_manifest.json','verification.json'}}
        save('artifact_manifest.json',dict(result_scope='DIAGNOSTIC_ONLY',files=files))
        result=verify();result['manifest_sha256']=sha(OUT/'artifact_manifest.json')
        result['artifacts']=len(files);save('verification.json',result)
    elif not sys.argv[1:]:result=verify()
    else:raise SystemExit('Read-only default; --seal is single-use for this new package')
    print(json.dumps(result,indent=2))
