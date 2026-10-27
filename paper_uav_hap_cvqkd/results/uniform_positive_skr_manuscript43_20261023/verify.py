"""Read-only checks of saved artifacts; imports no channel/source/rate evaluator."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];REPO=ROOT.parent
RAW='manuscript43_Eq10_retained_0_to_1';BOUNDED='power_conserving_random_width'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def audit():
    checks=[]
    def check(name,ok,**details):
        checks.append(dict(check=name,status='CURRENTLY_VERIFIED_PASS' if ok else 'FAILED',**details))
        if not ok:raise AssertionError(name)
    start=read(OUT/'startup_manifest.json')
    changed=[n for n,h in start['protected'].items() if not (REPO/n).is_file() or sha(REPO/n)!=h]
    check('All pre-existing protected bytes unchanged',not changed,count=len(start['protected']),changed=changed)
    check('HEAD and branch unchanged',subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==start['HEAD']
        and subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==start['branch'])
    check('Frozen identity preserved',sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==start['frozen_sha256'],
        discrepancy_to_historical_expected=start['frozen_sha256']!=start['historical_frozen_expected'])
    protocol=read(OUT/'protocol.json');initial=read(OUT/'screen_receipt.json')
    check('Prospective protocol and initial producer intact',sha(OUT/'protocol.json')==initial['prospective_protocol_sha256']
        and sha(OUT/'search.py')==initial['producer_sha256'])
    check('Original failed launcher preserved',sha(OUT/'source_job.py')==protocol['initial_producer_sha256']['source_job.py'])
    check('Extension producer version preserved',sha(OUT/'producer_snapshots/complete_search_extension.py')
        ==read(OUT/'extension_receipt.json')['producer_sha256'])
    end=read(OUT/'completion_receipt.json')
    check('Completion producer and plan bound',sha(OUT/'complete_search.py')==end['producer_sha256']
        and sha(OUT/'completion_plan.json')==end['completion_plan_sha256'])
    check('No security or global optimum promotion',not end['security_valid'] and not end['global_optimum']
        and end['full_VA_requested_domain_complete']==(not end['source_gaps']))
    sources=read(OUT/'source_catalog.json');lookup={c['ensemble_hash']:c for c in sources}
    check('Authenticated source payloads unchanged',all(sha(ROOT/c['source_path'])==c['source_sha256'] for c in sources),
        sources=len(sources))
    new=list((OUT/'new_exact_source/exact_source_cache').glob('*.json'))
    check('Versioned fresh sources use full support and fixed precision',
        all(read(p)['support_size']==256 and min(read(p)['C'],read(p)['w'])>=0 for p in new)
        and all(read(p)['precision_ladder']==[1050,1250,1450]
            for p in (OUT/'new_exact_source/source_receipts').glob('*.json')),fresh_sources=len(new))
    check('No source jobs left pending',all(read(p)['status']!='RUNNING'
        for p in (OUT/'new_exact_source').glob('python_attempt_*.json')))
    all_rows=rows('candidate_comparison.csv')
    check('All-candidate count matches receipt',len(all_rows)==end['candidate_rows'])
    numerical=0;blocked=0;primary_uniform=[]
    for row in all_rows:
        if not row['raw_SKR']:
            blocked+=1
            assert row['exclusion_reason'] and all(not row[k] for k in ['I_AB','beta_I_AB','chi_BE','xi_f'])
            if row['exclusion_reason']=='FAILED_PDF_NORMALIZATION':
                assert not row['VA'] and not row['source_hash']
            else:
                assert row['VA'] and row['source_hash'] in lookup
            continue
        numerical+=1
        va,mi,bi,chi,k,t,m1,mh,m0,etaxi,xif=[float(row[f]) for f in
            ['VA','I_AB','beta_I_AB','chi_BE','raw_SKR','eta_f','E_eta','E_sqrt_eta','pdf_mass','E_eta_xi','xi_f']]
        assert all(math.isfinite(x) for x in [va,mi,bi,chi,k,t,m1,mh,m0,etaxi,xif])
        assert 0<=t<=m1<=1 and abs(t-mh**2)<2e-15 and abs(1-m0)<=1e-10+2e-16
        assert abs(etaxi-(.0186*m1+.005*m0))<2e-15
        assert abs(t*xif-((m1-t)*va+etaxi))<2e-12
        assert abs(bi-.95*mi)<2e-14 and abs(k-(bi-chi))<2e-14
        assert float(row['xi_ch'])==.0186 and float(row['xi_det'])==.005
        source=lookup[row['source_hash']]
        assert va==source['VA'] and row['family']==source['family']
        assert row['source_sha256']==source['source_sha256']
        if row['channel_law']==RAW and row['family']=='Uniform':primary_uniform.append(k)
    check('Candidate model identities and explicit exclusions',True,numerical=numerical,blocked=blocked)
    check('Primary positive flag refers to Uniform only',end['primary_positive_found']==any(k>0 for k in primary_uniform),
        strongest_primary_uniform=max(primary_uniform))
    check('Reported primary best matches all evaluated Uniform rows',
        abs(end['primary_best']['raw_SKR']-max(primary_uniform))<2e-8)
    validation=list((OUT/'selected_validation').glob('*.json'))
    check('Every saved selected independent check passed',
        all(read(p)['validation']['status']=='CURRENTLY_VERIFIED_PASS'
            and all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in read(p)['validation']['checks']) for p in validation),
        selected=len(validation),checks=sum(len(read(p)['validation']['checks']) for p in validation))
    for name in ['guard_checks.json','bounded_moment_validation.json','independent_bounded_validation.json',
                 'bounded_all_contexts_validation.json','source_diagonal_equivalence.json']:
        check(name,read(OUT/name)['status']=='CURRENTLY_VERIFIED_PASS')
    bounded_check=read(OUT/'bounded_all_contexts_validation.json')
    bounded_contexts={p.stem:read(p) for p in (OUT/'contexts').glob('*.json') if read(p)['law']==BOUNDED}
    check('Width quadrature validation covers all secondary contexts',
        {r['context_id'] for r in bounded_check['checks']}==set(bounded_contexts))
    comparisons=read(OUT/'three_scheme_comparison.json')
    for law in [RAW,BOUNDED]:
        selected=[r for r in comparisons if r['channel_law']==law]
        assert len(selected)==3
        assert len({(r['Dr_m'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['zenith_deg'],
            r['pdf_mass'],r['E_eta'],r['E_sqrt_eta'],r['E_eta_xi']) for r in selected})==1
        gain=selected[2]['raw_SKR']-selected[0]['raw_SKR']
        assert abs(gain-end['shaping_gain'][law])<1e-14
    check('Same-law same-channel shaping gains',True)
    pm=read(OUT/'plot_manifest.json')
    check('Plot positive-only and one law per curve',
        pm['positive_only'] and pm['no_connection_across_invalid'] and pm['one_law_per_curve']
        and all(len(c['channel_laws'])==1 for c in pm['curves']))
    check('Three figure pairs exist',len(list((OUT/'figures').glob('*.pdf')))==3
        and len(list((OUT/'figures').glob('*.png')))==3)
    if (OUT/'visual_verification.json').exists():
        check('PDF rendering and visual review passed',read(OUT/'visual_verification.json')['status']=='CURRENTLY_VERIFIED_PASS')
    seal=OUT/'final_seal.json'
    if seal.exists():
        seal=read(seal)
        mismatch=[n for n,h in seal['artifacts'].items() if not (OUT/n).is_file() or sha(OUT/n)!=h]
        check('Final artifact hashes',not mismatch,count=len(seal['artifacts']),mismatch=mismatch)
        check('Final ledger hashes',all(sha(ROOT/n)==h for n,h in seal['ledgers'].items()))
    return dict(status='CURRENTLY_VERIFIED_PASS',scope='FINITE_EXACT_TESTED_DIAGNOSTIC',checks=checks,
        full_VA_requested_domain_complete=end['full_VA_requested_domain_complete'],
        source_gaps=end['source_gaps'],security_status='UNVALIDATED_SECURITY_MODEL',
        lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',objective_C='USER_STOPPED',
        primary_Uniform_positive=end['primary_positive_found'],secondary_positive=end['secondary_positive_found'])


if __name__=='__main__':print(json.dumps(audit(),indent=2))
