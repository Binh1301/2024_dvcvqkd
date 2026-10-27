"""Validate saved rates, compare sampled signs, and render CSV-only figures."""
from collections import Counter
import json
import math
from pathlib import Path
import sys
import time

OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(OUT))
import sweep as run
import numpy as np
import mpmath as mp

PASS, BASE, ROOT = run.PASS,run.BASE,run.ROOT
read,rows,save,write,sha = run.read,run.rows,run.save,run.write,run.sha
SHORT = ['Uniform','Fixed MB','Optimized MB']


def validate_saved(data,sources,task):
    by_hash = {s['ensemble_hash']:s for s in sources}
    baseline = {(int(float(r['zenith_deg'])),r['ensemble_hash']):r for r in rows(BASE/'diagnostic_results.csv')}
    pairs=set();reused=0;rate_error=z_error=0.
    for r in data:
        angle=int(float(r['zenith_deg']));key=(angle,r['ensemble_hash'])
        assert key not in pairs
        pairs.add(key);source=by_hash[key[1]]
        assert r['source_evidence_class']==source['classification']
        assert r['source_id']==source['canonical_source_identity']
        assert r['result_scope']=='DIAGNOSTIC_ONLY' and r['source_Cw_recomputed']=='False'
        assert r['channel_protocol_sha256']==task['physical_protocol_sha256']
        assert r['correlation_policy']=='manuscript_eq14_direct'
        assert sha(OUT/f'angle_{angle:02d}_context.json')==r['channel_context_sha256']
        for k in ['VA','nu_raw','C','w']: assert float(r[k]).hex()==source[k].hex()
        assert r['source_sha256']==sha(ROOT/r['source_path'])
        if key in baseline:
            reused+=1
            assert r['evaluation_origin']=='REUSED_NINE_ANGLE'
            old=baseline[key]
            for k,v in old.items():
                if k in ['result_scope','zenith_deg','Cw_reused','source_Cw_recomputed','security_valid']:continue
                if k in run.NUMERIC:
                    assert (float(v).hex() if v else None)==(float(r[k]).hex() if r[k] is not None else None),(key,k)
                else: assert str(r[k])==v,(key,k)
        else: assert r['evaluation_origin']=='NEW_RATE_HISTORICAL_CW'
        if r['numerical_status']!=PASS:
            assert r['K_raw'] is None and r['K_operational'] is None and r['reason']
            continue
        assert all(math.isfinite(float(r[k])) for k in ['I_AB','beta_I_AB','chi_BE','K_raw','eta_f','xi_f','Z_manuscript_eq14'])
        rate_error=max(rate_error,abs(r['K_raw']-(r['beta_I_AB']-r['chi_BE'])))
        z=2*math.sqrt(r['eta_f'])*r['C']-math.sqrt(2*r['eta_f']*r['xi_f']*r['w'])
        z_error=max(z_error,abs(z-r['Z_manuscript_eq14']))
        assert abs(r['beta_I_AB']-.95*r['I_AB'])<=2e-15
        assert r['K_operational']==max(0,r['K_raw'])
        assert r['MI_GH64_128_difference']<=2e-10
    assert len(pairs)==61*212 and reused==1908
    assert rate_error<=2e-15 and z_error<=2e-11
    return dict(status=PASS,unique_pairs=len(pairs),reused_values_unchanged=reused,
        duplicate_pairs=0,max_raw_rate_residual=rate_error,max_Eq14_float_residual=z_error)


def independent(selected,sources):
    helpers=run.canonical.prior_model.helpers();by_hash={s['ensemble_hash']:s for s in sources}
    previous={(int(float(r['zenith_deg'])),r['ensemble_hash']):r for r in rows(BASE/'selected_independent_validation.csv')}
    checked={};start=time.perf_counter()
    for row in selected:
        if row['numerical_status']!=PASS:continue
        key=(int(float(row['zenith_deg'])),row['ensemble_hash'])
        if key in checked:continue
        if row['evaluation_origin']=='REUSED_NINE_ANGLE' and key in previous:
            checked[key]=dict(previous[key],validation_origin='REUSED_BASELINE',
                validation_artifact_sha256=sha(BASE/'selected_independent_validation.csv'))
            continue
        source=by_hash[key[1]]
        mi,error=helpers.independent_mi(source['p'],source['alpha'],row['eta_f'],1+row['N_effective'])
        mi256=helpers.homodyne_mi(source['p'],source['alpha'],row['eta_f'],1+row['N_effective'],order=256)
        V,W,Z=[row[k] for k in ['V','W','Z_manuscript_eq14']]
        gamma=np.array([[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]])
        omega=np.kron(np.eye(2),np.array([[0.,1.],[-1.,0.]]))
        eigenvalues=np.linalg.eigvals(1j*omega@gamma)
        spectrum=np.sort(abs(eigenvalues.real))[[0,2]]
        sd=float(max(abs(spectrum-np.sort([row['nu_1'],row['nu_2']]))))
        cd=abs(math.sqrt(np.linalg.det(np.diag([V-Z*Z/W,V])))-row['nu_3'])
        high=run.evaluator.components(source['VA'],row['eta_f'],row['xi_f'],source['C'],source['w'],digits=160)
        with mp.workdps(170):
            hd=max(float(abs(mp.mpf(v)-mp.mpf(row['decimal_'+k]))) for k,v in high['decimal'].items())
        passed=(abs(mi-row['I_AB'])<=2e-10 and abs(mi256-row['I_AB'])<=2e-10
            and sd<=2e-11 and cd<=2e-11 and hd<=2e-11 and max(abs(eigenvalues.imag))<=2e-11)
        checked[key]=dict(zenith_deg=key[0],ensemble_hash=key[1],source_evidence_class=row['source_evidence_class'],
            adaptive_MI=mi,MI_difference=abs(mi-row['I_AB']),integration_error_estimate=error,
            GH128_256_difference=abs(mi256-row['I_AB']),covariance_spectrum_difference=sd,
            conditional_covariance_difference=cd,components110_160_difference=hd,
            status=PASS if passed else 'FAILED',validation_origin='NEW_INDEPENDENT_CHECK')
    result=list(checked.values());write('independent_validation.csv',result)
    assert all(r['status']==PASS for r in result)
    return dict(total=len(result),reused=sum(r['validation_origin']=='REUSED_BASELINE' for r in result),
        new=sum(r['validation_origin']=='NEW_INDEPENDENT_CHECK' for r in result),
        elapsed_seconds=time.perf_counter()-start,
        max_adaptive_MI_difference=max(float(r['MI_difference']) for r in result),
        max_covariance_difference=max(float(r['covariance_spectrum_difference']) for r in result),
        max_conditional_difference=max(float(r['conditional_covariance_difference']) for r in result))


def sampled_ranges(selected):
    result={}
    for scheme,short in zip(run.SCHEMES,SHORT):
        points=sorted([r for r in selected if r['scheme']==scheme],key=lambda r:float(r['zenith_deg']))
        valid=[r for r in points if r['numerical_status']==PASS]
        positive=[r for r in valid if r['K_raw']>0]
        nonpositive=[r for r in valid if r['K_raw']<=0]
        crossings=[]
        for a,b in zip(points,points[1:]):
            if a['numerical_status']==b['numerical_status']==PASS and (a['K_raw']>0)!=(b['K_raw']>0):
                crossings.append(dict(interval_deg=[float(a['zenith_deg']),float(b['zenith_deg'])],
                    endpoint_raw_K=[a['K_raw'],b['K_raw']],direction='POSITIVE_TO_NONPOSITIVE' if a['K_raw']>0 else 'NONPOSITIVE_TO_POSITIVE'))
        best=max(valid,key=lambda r:r['K_raw'])
        result[short]=dict(best_raw_K=best['K_raw'],best_angle_deg=float(best['zenith_deg']),
            best_VA=best['VA'],best_nu_raw=best['nu_raw'],best_evidence_class=best['source_evidence_class'],
            positive_sampled_angles=[float(r['zenith_deg']) for r in positive],
            last_sampled_positive_deg=float(positive[-1]['zenith_deg']) if positive else None,
            first_sampled_nonpositive_deg=float(nonpositive[0]['zenith_deg']) if nonpositive else None,
            zero_crossing_intervals=crossings,
            all_selected_evidence_counts=dict(Counter(r['source_evidence_class'] for r in valid)))
    return result


def main():
    task=read(OUT/'protocol.json');physical=read(ROOT/task['physical_protocol_path'])
    data=run.numeric(rows(OUT/'diagnostic_skr_61_angles.csv'))
    sources=list(run.source_pool(physical));saved_validation=validate_saved(data,sources,task)
    selected=[];strict=[];near_ties=[]
    for a in task['angles_deg']:
        candidates=[r for r in data if int(float(r['zenith_deg']))==a]
        assert len(candidates)==212
        best=run.nine.select(candidates,physical)
        strict_best=run.nine.select(candidates,physical,strict=True)
        for r in best+strict_best:
            r.update(result_scope='DIAGNOSTIC_ONLY',selection_scope='BEST_AVAILABLE_HISTORICAL_CATALOG',
                K_operational=max(0,r['K_raw']) if r['K_raw'] is not None else None)
        selected.extend(best);strict.extend(strict_best)
        for r in best:
            if r.get('best_second_gap') is not None and r['best_second_gap']<=1e-8:
                eligible=[c for c in candidates if c['numerical_status']==PASS and
                    (r['scheme']==run.SCHEMES[2] or (r['scheme']==run.SCHEMES[0] and c['family']=='Uniform'))]
                near_ties.extend(sorted(eligible,key=lambda c:c['K_raw'],reverse=True)[:2])
        valid=[r for r in best if r['numerical_status']==PASS]
        if len(valid)==3:
            assert best[2]['K_raw']+2e-10>=max(best[0]['K_raw'],best[1]['K_raw'])
            winner=max(valid,key=lambda r:r['K_raw'])['scheme']
            for r in best:r['best_scheme_at_angle']=winner
    write('best_scheme_by_angle.csv',selected)
    write('strict_evidence_selected.csv',strict)
    # Validate every selected source, including switches and crossing endpoints.
    independent_result=independent(selected+strict+near_ties,sources)
    contexts=[read(OUT/f'angle_{a:02d}_context.json') for a in task['angles_deg']]
    ranges=sampled_ranges(selected)
    optimized=[r for r in selected if r['scheme']==run.SCHEMES[2]]
    transitions=[];last=None
    for r in optimized:
        if r['ensemble_hash']!=last:
            transitions.append({k:r[k] for k in ['zenith_deg','VA','nu_raw','ensemble_hash','source_evidence_class']})
            last=r['ensemble_hash']
    write('optimized_MB_parameter_transitions.csv',transitions)
    good=[r for r in data if r['numerical_status']==PASS]
    summary={**read(OUT/'execution_summary.json'),'saved_validation':saved_validation,
        'independent_validation':independent_result,'sampled_scheme_results':ranges,
        'source_evidence_counts':dict(Counter(s['classification'] for s in sources)),
        'positive_candidate_rows':sum(r['K_raw']>0 for r in good),
        'negative_candidate_rows':sum(r['K_raw']<0 for r in good),
        'zero_candidate_rows':sum(r['K_raw']==0 for r in good),
        'positive_evidence_counts':dict(Counter(r['source_evidence_class'] for r in good if r['K_raw']>0)),
        'source_evidence_incomplete_rows':sum(r['source_evidence_class']=='INSUFFICIENT_EVIDENCE' for r in data),
        'optimized_MB_transitions':transitions,'near_tie_selected_rows':len(near_ties),
        'max_channel_direct_moment_residual':max(c['moment_residual'] for c in contexts),
        'max_channel_precision_residual':max(c['precision_residual'] for c in contexts),
        'probability_deficit_range':[min(c['probability_deficit'] for c in contexts),max(c['probability_deficit'] for c in contexts)],
        'strict_source_subset_positive_selected_rows':sum(r['numerical_status']==PASS and r['K_raw']>0 for r in strict),
        'strict_Phase_B_ready':False,'security_model_status':'UNVALIDATED_SECURITY_MODEL',
        'publication_status':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
    save('diagnostic_summary.json',summary)
    print(json.dumps(run.clean(summary),indent=2),flush=True)


if __name__=='__main__':main()
