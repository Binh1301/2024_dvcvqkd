"""Nine-angle historical-source diagnostic only; no strict pilot, source job or full sweep."""
import argparse
from collections import Counter
import json
import time

import numpy as np
from inventory import OUT,ROOT,PRIOR,STRICT,LABEL,canonical,read,rows,save,write,sha,with_ensemble,prior_run
import diagnostic_model

SCHEMES=['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']


def load_sources():
    all_rows=rows(OUT/'pilot_source_coverage.csv')
    sources=[]
    for row in all_rows:
        if row['diagnostic_eligible']!='True':continue
        source=dict(row,VA=float.fromhex(row['VA_hex']),nu_raw=float.fromhex(row['nu_raw_hex']),
            C=float(row['C']),w=float(row['w']),compatibility_status='CURRENTLY_VERIFIED_PASS')
        source=with_ensemble(source)
        canonical.prior_model.helpers().validate_source(source)
        sources.append(source)
    return all_rows,sources


def select(records,protocol,strict=False):
    output=[]
    for scheme in SCHEMES:
        eligible=[r for r in records if (not strict or r['source_evidence_class'] in STRICT)
            and (scheme==SCHEMES[2] or (scheme==SCHEMES[0] and r['family']=='Uniform')
                 or (scheme==SCHEMES[1] and r['ensemble_hash']==protocol['fixed_MB']['ensemble_hash']))]
        valid=[r for r in eligible if r['numerical_status']=='CURRENTLY_VERIFIED_PASS']
        if valid:
            record=dict(max(valid,key=lambda r:r['K_raw']))
            ordered=sorted(valid,key=lambda r:r['K_raw'],reverse=True)
            record['best_second_gap']=ordered[0]['K_raw']-ordered[1]['K_raw'] if len(ordered)>1 else None
        else:
            record=dict(zenith_deg=records[0]['zenith_deg'],numerical_status='NO_EVALUABLE_SOURCE',
                reason='NO_STRICT_SOURCE_EVIDENCE' if strict and not eligible else 'NO_NUMERICALLY_VALID_CANDIDATE',K_raw=None)
        record.update(scheme=scheme,result_scope='STRICT_SOURCE_EVIDENCE_SUBSET_DIAGNOSTIC' if strict else LABEL,
            available_scheme_sources=len(eligible),valid_scheme_sources=len(valid),original81_pool_complete=False,
            strict_Phase_B_complete=False)
        output.append(record)
    return output


def independent_selected(selected,sources):
    helpers=canonical.prior_model.helpers();by_hash={s['ensemble_hash']:s for s in sources};verified=[]
    seen=set()
    for row in selected:
        if row['numerical_status']!='CURRENTLY_VERIFIED_PASS':continue
        key=(row['zenith_deg'],row['ensemble_hash'])
        if key in seen:continue
        seen.add(key);source=by_hash[row['ensemble_hash']]
        mi,error=helpers.independent_mi(source['p'],source['alpha'],row['eta_f'],1+row['N_effective'])
        V,W,Z=[row[k] for k in ['V','W','Z_manuscript_eq14']]
        gamma=np.array([[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]])
        omega=np.kron(np.eye(2),np.array([[0.,1.],[-1.,0.]]))
        spectrum=np.sort(np.abs(np.linalg.eigvals(1j*omega@gamma).real))[[0,2]]
        expected=np.sort([row['nu_1'],row['nu_2']])
        spectrum_delta=float(np.max(abs(spectrum-expected)))
        # The conditional homodyne covariance has diagonal V-Z^2/W,V.
        conditional=float(np.sqrt(np.linalg.det(np.diag([V-Z*Z/W,V]))))
        delta=abs(mi-row['I_AB'])
        passed=delta<=2e-10 and spectrum_delta<=2e-11 and abs(conditional-row['nu_3'])<=2e-11
        verified.append(dict(zenith_deg=key[0],ensemble_hash=key[1],source_evidence_class=row['source_evidence_class'],
            adaptive_MI=mi,MI_difference=delta,integration_error_estimate=error,
            covariance_spectrum_difference=spectrum_delta,conditional_covariance_difference=abs(conditional-row['nu_3']),
            status='CURRENTLY_VERIFIED_PASS' if passed else 'FAILED_INDEPENDENT_VALIDATION'))
    write('selected_independent_validation.csv',verified)
    return verified


def diagnostic():
    if (OUT/'diagnostic_summary.json').exists():raise FileExistsError('Preserve completed diagnostic')
    task=read(OUT/'protocol.json')
    assert task['angles_deg']==[0,5,10,15,20,30,40,50,60]
    assert sha(ROOT/task['physical_protocol_path'])==task['physical_protocol_sha256']
    protocol=read(ROOT/task['physical_protocol_path']);canonical.validate_protocol(protocol)
    required,sources=load_sources()
    assert len(required)==81 and len(sources)==80
    all_records=[];contexts=[];selected=[];strict_selected=[];coverage={r['expected_ensemble_hash']:dict(r) for r in required}
    began=time.perf_counter()
    for angle in task['angles_deg']:
        start=time.perf_counter();context=canonical.channel_context(angle,protocol)
        contexts.append(prior_run.old.clean(dict(context,context_seconds=time.perf_counter()-start)))
        angle_records=[]
        for source in sources:
            record={k:source[k] for k in ['family','VA','VA_hex','nu_raw','nu_raw_hex','nu_repo','ensemble_hash','source_path','source_sha256','C','w','classification','diagnostic_evidence_group']}
            record.update(zenith_deg=angle,source_evidence_class=source['classification'],result_scope=LABEL,
                C_hex=source['C'].hex(),w_hex=source['w'].hex(),Cw_reused=True,source_Cw_recomputed=False,
                channel_protocol_sha256=task['physical_protocol_sha256'],diagnostic_protocol_sha256=sha(OUT/'protocol.json'),
                correlation_policy='manuscript_eq14_direct',M0=context['moments']['M0'],
                E_sqrt_eta=context['moments']['mh'],E_eta=context['moments']['m1'],P0=context['moments']['P0'])
            try:
                result=diagnostic_model.evaluate(source,context,protocol)
                decimals=result.pop('decimal')
                record.update(result,numerical_status='CURRENTLY_VERIFIED_PASS',reason='')
                record.update({'decimal_'+k:v for k,v in decimals.items()})
            except ValueError as error:
                # Recheck the unchanged equations at160 digits; never repair an invalid point.
                m=context['moments'];t=m['mh']**2;noise=(m['m1']-t)*source['VA']+protocol['xi_ch']*m['m1']+protocol['xi_det']*m['M0']
                try:diagnostic_model.components(source['VA'],t,noise/t,source['C'],source['w'],digits=160);recheck='COMPONENT_DOMAIN_VALID_AT160_REVIEW_REQUIRED'
                except ValueError as second:recheck=str(second)
                record.update(numerical_status='FAILED_NUMERICAL_VALIDATION',reason=str(error),component_recheck160=recheck,
                    eta_f=t,xi_f=noise/t,N_effective=noise,K_raw=None,I_AB=None,beta_I_AB=None,chi_BE=None,Z_manuscript_eq14=None)
            angle_records.append(record)
            coverage[source['ensemble_hash']][f'zenith_{angle:02d}_deg']='EVALUATED_DIAGNOSTIC_ONLY' if record['numerical_status']=='CURRENTLY_VERIFIED_PASS' else 'NUMERICAL_VALIDATION_FAILED'
        for r in required:
            if r['diagnostic_eligible']!='True':coverage[r['expected_ensemble_hash']][f'zenith_{angle:02d}_deg']='MISSING_COMPATIBLE_SOURCE_PAYLOAD'
        all_records.extend(angle_records)
        selected.extend(select(angle_records,protocol));strict_selected.extend(select(angle_records,protocol,strict=True))
        print(json.dumps(dict(angle=angle,evaluated=len(angle_records),passed=sum(r['numerical_status']=='CURRENTLY_VERIFIED_PASS' for r in angle_records))),flush=True)
    save('channel_contexts.json',contexts)
    write('diagnostic_results.csv',all_records)
    write('diagnostic_selected_schemes.csv',selected)
    write('strict_source_evidence_results.csv',[r for r in all_records if r['source_evidence_class'] in STRICT])
    write('incomplete_source_evidence_results.csv',[r for r in all_records if r['source_evidence_class'] not in STRICT])
    write('strict_source_evidence_selected.csv',strict_selected)
    write('nine_angle_coverage.csv',list(coverage.values()))
    independent=independent_selected(selected+strict_selected,sources)
    canonical.validate_protocol(protocol)
    summary=dict(result_scope=LABEL,source_pool_size=len(sources),required_pool_size=81,angles=task['angles_deg'],
        angle_contexts=len(contexts),candidate_evaluations=len(all_records),numerical_status_counts=dict(Counter(r['numerical_status'] for r in all_records)),
        positive_candidate_rows=sum(r['numerical_status']=='CURRENTLY_VERIFIED_PASS' and r['K_raw']>0 for r in all_records),
        negative_candidate_rows=sum(r['numerical_status']=='CURRENTLY_VERIFIED_PASS' and r['K_raw']<0 for r in all_records),
        independent_selected_checks=len(independent),independent_validation_failures=sum(r['status']!='CURRENTLY_VERIFIED_PASS' for r in independent),
        selected_rows=len(selected),strict_source_rows=sum(r['source_evidence_class'] in STRICT for r in all_records),
        incomplete_source_rows=sum(r['source_evidence_class'] not in STRICT for r in all_records),
        source_Cw_computations=0,strict_Phase_B_ready=False,strict_Phase_B_complete=False,full61_sweep_executed=False,
        elapsed_seconds=time.perf_counter()-began)
    save('diagnostic_summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostic',action='store_true',required=True)
    parser.parse_args();diagnostic()
