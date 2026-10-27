"""Read-only integrity and saved-result checks; no scientific evaluator imports."""
import csv
import hashlib
import json
import math
from pathlib import Path

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def verify():
    startup=read(OUT/'startup_manifest.json')
    for name,digest in startup['protected'].items():assert sha(ROOT.parent/name)==digest,'Historical file changed: '+name
    manifest=read(OUT/'artifact_manifest.json')
    for name,digest in manifest['files'].items():assert sha(OUT/name)==digest,'Artifact changed: '+name
    protocol=read(OUT/'protocol.json')
    for name,digest in protocol['diagnostic_code_sha256'].items():
        assert sha(OUT/'execution_producers'/name)==digest,'Original execution code changed'
    scope=read(OUT/'available_catalog_protocol.json')
    for name,digest in scope['code_sha256'].items():
        executed=OUT/name if sha(OUT/name)==digest else OUT/'execution_producers'/name
        assert sha(executed)==digest,'Additional execution producer changed: '+name
    data=rows('diagnostic_results.csv');inventory=rows('exact_source_inventory.csv');pilot=rows('pilot_source_coverage.csv')
    assert len(data)==1908 and len(inventory)==235 and len(pilot)==81
    by_hash={r['ensemble_hash']:r for r in inventory}
    pilot_class={r['ensemble_hash']:r['classification'] for r in pilot if r['ensemble_hash']}
    pairs=set();max_rate_residual=0.;max_z_residual=0.
    for r in data:
        key=(r['ensemble_hash'],int(float(r['zenith_deg'])));assert key not in pairs;pairs.add(key)
        source=by_hash[r['ensemble_hash']]
        assert float(r['C']).hex()==source['C_hex']==r['C_hex']
        assert float(r['w']).hex()==source['w_hex']==r['w_hex']
        if r['ensemble_hash'] in pilot_class:assert r['source_evidence_class']==pilot_class[r['ensemble_hash']]
        assert r['numerical_status']=='CURRENTLY_VERIFIED_PASS'
        assert r['result_scope']=='HISTORICAL_EXACT_RESTRICTED_CATALOG_DIAGNOSTIC'
        assert r['source_Cw_recomputed']=='False'
        delta=abs(float(r['K_raw'])-(float(r['beta_I_AB'])-float(r['chi_BE'])))
        max_rate_residual=max(max_rate_residual,delta);assert delta<=2e-15
        t,xi,C,w=map(float,[r['eta_f'],r['xi_f'],r['C'],r['w']])
        z=2*math.sqrt(t)*C-math.sqrt(2*t*xi*w)
        delta=abs(z-float(r['Z_manuscript_eq14']));max_z_residual=max(max_z_residual,delta);assert delta<=2e-11
    assert len(pairs)==212*9
    original=rows('pilot_candidate_diagnostic_results.csv');lookup={(r['ensemble_hash'],r['zenith_deg']):r for r in data}
    for row in original:
        reused=lookup[(row['ensemble_hash'],row['zenith_deg'])]
        for k in ['K_raw','I_AB','chi_BE','Z_manuscript_eq14','C','w','eta_f','xi_f']:
            assert float(row[k]).hex()==float(reused[k]).hex(),'Pilot result changed: '+k
    selected=rows('diagnostic_selected_schemes.csv')+rows('strict_source_evidence_selected.csv')
    independent=rows('selected_independent_validation.csv')
    checked={(r['ensemble_hash'],r['zenith_deg']) for r in independent if r['status']=='CURRENTLY_VERIFIED_PASS'}
    for r in selected:
        if r['numerical_status']=='CURRENTLY_VERIFIED_PASS':assert (r['ensemble_hash'],r['zenith_deg']) in checked
    assert len(rows('nine_angle_coverage.csv'))==236 and len(rows('pilot_nine_angle_coverage.csv'))==81
    assert len(rows('strict_source_evidence_results.csv'))==198 and len(rows('incomplete_source_evidence_results.csv'))==1710
    summary=read(OUT/'diagnostic_summary.json')
    assert summary['source_Cw_computations']==0 and not summary['strict_Phase_B_ready'] and not summary['full61_sweep_executed']
    for p in (ROOT/'results').glob('**/exact_source_cache/*.json'):
        assert p.relative_to(ROOT.parent).as_posix() in startup['protected'],'Unexpected new source payload'
    return dict(status='CURRENTLY_VERIFIED_PASS',protected_files=len(startup['protected']),artifacts=len(manifest['files']),
        candidate_rows=1908,pilot_rows_unchanged=720,source_inventory=235,strict_Phase_B_ready=False,
        max_saved_rate_arithmetic_residual=max_rate_residual,max_direct_Eq14_float_check_residual=max_z_residual,
        source_Cw_computations=0,full61_sweep_executed=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
