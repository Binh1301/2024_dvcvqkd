"""Continue saved initial scan with bright-link pointing contexts; never rerun it."""
import csv
import math
from pathlib import Path
import time
import numpy as np
from scipy.optimize import brentq
import model as m
import run as r

OUT=Path(__file__).resolve().parent


def read_csv(name):
    with (OUT/name).open(encoding='utf-8',newline='') as stream:records=list(csv.DictReader(stream))
    for record in records:
        for k,v in record.items():
            if v in ('True','False'):record[k]=v=='True'
            elif v=='':record[k]=None
            else:
                try:record[k]=float(v)
                except ValueError:pass
    return records


def main():
    if (OUT/'selection.json').exists():raise FileExistsError('Preserve completed extension')
    started=time.perf_counter();r.SOURCES=m.load_catalog(r.read(m.ROOT/'configs/manuscript_mobility.json'))
    fixed=next(c for c in r.SOURCES if c['family']=='MB' and c['VA']==5.475 and c['nu_raw']==.165)
    optical=read_csv('table_B_optical_feasibility.csv')
    primary=[x for x in optical if x['treatment']=='power_conserving_random_width']
    bright=max(primary,key=lambda x:x['m1'])
    improvements=[]
    for angle in (0,30):
        for pf,af in [(1,1),(.5,1),(.25,1),(.1,1),(1,.5),(1,.25),(1,.1),(.5,.5),(.25,.25),(.1,.1)]:
            ch=m.optical(bright['D_r'],bright['theta_div_urad'],angle,pf,af)
            improvements.append(r.evaluate(fixed,ch,m.power_conserving(ch),'bright_pointing'))
    r.write('bright_pointing_sensitivity.csv',improvements)
    cases=[('highest_collection',r.configure(bright))]
    for angle in (0,30):
        best=max((x for x in improvements if x['zenith_deg']==angle),key=lambda x:x['K_raw'])
        cases.append(('pointing_'+str(angle)+'deg',r.configure(best)))
    scans=[];winners=[];ascents=[]
    for label,ch in cases:
        records,best=r.catalog(ch,m.power_conserving(ch),'catalog_'+label)
        scans.extend({**x,'configuration_id':label} for x in records)
        for family in ('Uniform','MB'):
            win=max((x for x in records if x['family']==family),key=lambda x:x['K_raw'])
            winners.append({**win,'configuration_id':label,'source_group':'catalog_best_'+family})
        winners.append({**next(x for x in records if x['ensemble_hash']==fixed['ensemble_hash']),
                        'configuration_id':label,'source_group':'fixed_MB'})
        ascents.extend(r.alternating(records,label))
        print('BRIGHT CATALOG',label,best['family'],best['VA'],best['nu_raw'],best['K_raw'],flush=True)
    r.write('bright_catalog_evaluations.csv',scans);r.write('bright_source_comparison.csv',winners)
    r.write('bright_alternating_catalog_search.csv',ascents)
    best=max(winners,key=lambda x:x['K_raw'])
    reference=max((x for x in winners if x['configuration_id']=='pointing_30deg'),key=lambda x:x['K_raw'])
    ch=r.configure(best);mo=m.power_conserving(ch)
    sensitivity=[];detector_all=[]
    for eta in r.EFFICIENCIES:
        for noise in r.NOISES:
            records,win=r.catalog(ch,mo,'detector_bright',eta,noise)
            detector_all.extend({**x,'configuration_id':'recommended_bright'} for x in records)
            sensitivity.append({**win,'configuration_id':'recommended_bright','best_exact_source':win['ensemble_hash']})
        print('BRIGHT DETECTOR',eta,'complete',flush=True)
    r.write('bright_detector_all_exact.csv',detector_all)
    r.write('table_C_detector_sensitivity_final.csv',
        [x for x in read_csv('table_C_detector_sensitivity.csv') if x['configuration_id']=='original']+sensitivity)
    source=r.candidate(best);thresholds=[]
    for variable,values in [('epsilon_det',sorted(r.NOISES)),('eta_det',r.EFFICIENCIES)]:
        def objective(x):
            return r.evaluate(source,ch,mo,'bright_threshold',eta=x if variable=='eta_det' else .8,
                              noise=x if variable=='epsilon_det' else .0135)['K_raw']
        ks=[objective(x) for x in values];brackets=[]
        for lo,hi,klo,khi in zip(values[:-1],values[1:],ks[:-1],ks[1:]):
            if klo*khi<0:
                root=brentq(objective,lo,hi,xtol=1e-10,rtol=1e-12)
                brackets.append(dict(lower=lo,upper=hi,root=root,K_at_root=objective(root)))
        thresholds.append(dict(variable=variable,grid=values,K_values=ks,brackets=brackets,
             status='BRACKETED_FIXED_SOURCE_ROOT' if brackets else 'NO_CROSSING_IN_TESTED_RANGE',
             fixed_source_hash=source['ensemble_hash']))
    # Broader thresholds are diagnostic only and remain tied to this one exact source.
    for variable,lo,hi in [('epsilon_det',0.,.2),('eta_det',.05,1.),('pointing_factor',.1,1.)]:
        def objective(x):
            if variable=='pointing_factor':
                changed=m.optical(ch['D_r'],ch['theta_div_urad'],ch['zenith_deg'],x,x)
                return r.evaluate(source,changed,m.power_conserving(changed),'pointing_root')['K_raw']
            return r.evaluate(source,ch,mo,'expanded_detector_root',eta=x if variable=='eta_det' else .8,
                              noise=x if variable=='epsilon_det' else .0135)['K_raw']
        klo,khi=objective(lo),objective(hi)
        if klo*khi<0:
            root=brentq(objective,lo,hi,xtol=1e-9,rtol=1e-11)
            thresholds.append(dict(variable=variable,lower=lo,upper=hi,root=root,K_at_root=objective(root),
                status='EXPANDED_BRACKET_FIXED_SOURCE_DIAGNOSTIC',fixed_source_hash=source['ensemble_hash']))
    r.save('bright_thresholds.json',thresholds)
    geometry=[];distance_roots=[]
    for label,selected in [('recommended_0deg',best),('recommended_reference_geometry',reference)]:
        c=r.candidate(selected);previous=None
        def by_length(length):
            angle=0. if length==19 else min(60.,math.degrees(math.acos(19/length)))
            changed=m.optical(selected['D_r'],selected['theta_div_urad'],angle,
                              selected['position_factor'],selected['angular_factor'])
            return {**r.evaluate(c,changed,m.power_conserving(changed),'bright_distance'),
                    'configuration_id':label,'requested_L_km':length}
        for length in sorted(set([float(x) for x in range(19,39)]+[21.9393102292])):
            point=by_length(length);geometry.append(point)
            if previous and previous['K_raw']*point['K_raw']<0:
                root=brentq(lambda L:by_length(L)['K_raw'],previous['requested_L_km'],length,xtol=1e-7)
                distance_roots.append(dict(configuration_id=label,root_km=root,K_at_root=by_length(root)['K_raw']))
            previous=point
    r.write('bright_distance_scan.csv',geometry);r.save('distance_thresholds.json',distance_roots)
    # Resolve aperture/divergence thresholds at fixed exact source and improved pointing.
    physical=[]
    for diameter in r.DIAMETERS:
        for divergence in r.DIVERGENCES:
            changed=m.optical(diameter,divergence,30,.1,.1)
            physical.append(r.evaluate(r.candidate(reference),changed,m.power_conserving(changed),'improved_pointing_optical_grid'))
    r.write('improved_pointing_optical_grid.csv',physical)
    outage=[]
    for label,selected in [('recommended',best),('reference_geometry',reference)]:
        changed=r.configure(selected);mom=m.power_conserving(changed)
        for active in (False,True):
            outage.append({**r.evaluate(r.candidate(selected),changed,mom,'bright_outage',active=active),
                           'configuration_id':label})
    r.write('bright_outage_comparison.csv',outage)
    r.write('bright_all_evaluations.csv',r.EVALUATIONS)
    r.save('selection.json',dict(recommended=best,recommended_reference_geometry=reference,
        highest_collection_fixed=bright,pointing_fixed_winners=[max((x for x in improvements if x['zenith_deg']==angle),key=lambda x:x['K_raw']) for angle in (0,30)],
        source_claim='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',security_valid=False,
        modeling_status='PASSIVE_NORMALIZED_GAUSSIAN_RANDOM_WIDTH_SURROGATE_NOT_VALIDATED_ATMOSPHERIC_MODEL',
        source_expansion_status='NOT_RUN_EXISTING_EXACT_CATALOG_SUFFICIENT_FOR_DIAGNOSTIC_POSITIVITY',
        initial_pass_status='NUMERICAL_STAGES_SAVED_FINAL_SUMMARY_SERIALIZATION_FAILED_NUMPY_INT64',
        original_regression='CURRENTLY_VERIFIED_PASS'))
    r.save('extension_receipt.json',dict(status='DIAGNOSTIC_SCAN_COMPLETE',elapsed_seconds=time.perf_counter()-started,
        evaluation_count=len(r.EVALUATIONS),producer_hashes={p.name:r.sha(p) for p in OUT.glob('*.py')},
        artifacts={p.name:r.sha(p) for p in OUT.iterdir() if p.is_file() and p.suffix in ('.csv','.json')}))
    print('BRIGHT COMPLETE',best['K_raw'],reference['K_raw'],len(r.EVALUATIONS),flush=True)


if __name__=='__main__':main()
