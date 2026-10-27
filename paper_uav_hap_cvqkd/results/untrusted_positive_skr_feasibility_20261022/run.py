"""Bounded exact-catalog investigation; all results remain numerical diagnostics."""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import mpmath as mp
import numpy as np
from scipy.optimize import brentq
import model as m

OUT=Path(__file__).resolve().parent
ROOT=m.ROOT
DIAMETERS=[.08,.10,.20,.30,.40,.55,.75]
DIVERGENCES=[233,100,50,25,10]
ANGLES=[0,15,30,45]
EFFICIENCIES=[.8,.85,.9,.95,1.]
NOISES=[.0135,.010,.005,.001,0.]
EVALUATIONS=[]
SOURCES=[]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def clean(x):
    if isinstance(x,mp.mpf):return mp.nstr(x,70)
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    return x
def save(name,value):
    (OUT/name).write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n',encoding='utf-8')
def write(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def channel_record(ch,mo):
    return {**{k:float(v) if isinstance(v,mp.mpf) else v for k,v in ch.items()},**mo}


def evaluate(c,ch,mo,stage,eta=.8,noise=.0135,active=False):
    result=m.evaluate(c,mo,eta,noise,active_only=active)
    row={**channel_record(ch,mo),**result,'stage':stage}
    EVALUATIONS.append(row)
    return row


def catalog(ch,mo,stage,eta=.8,noise=.0135):
    records=[evaluate(c,ch,mo,stage,eta,noise) for c in SOURCES]
    return records,max(records,key=lambda r:r['K_raw'])


def candidate(row):
    return next(c for c in SOURCES if c['ensemble_hash']==row['ensemble_hash'])


def configure(row):
    return m.optical(row['D_r'],row['theta_div_urad'],row['zenith_deg'],row['position_factor'],
                     row['angular_factor'],row.get('turbulence_factor',1.))


def regression():
    from scripts import run_corrected_excess_noise_trial as old
    old.OUT=OUT  # Keep any failure log in this new namespace, never the sealed prior trial.
    prior=ROOT/'results/corrected_excess_noise_trial_20261022'
    receipt=read(prior/'receipt.json')
    assert all(sha(prior/p)==h for p,h in receipt['artifacts'].items())
    assert sha(ROOT/receipt['producer'])==receipt['producer_sha256']
    saved=read(prior/'result.json')['results'][0]
    source=read(prior/'result.json')['PDF_audits'][0]
    cc=old.verified_candidate(ROOT/source['source_path'],old.unconstrained_config())
    m1,mh,va,C,w=[old.M(x) for x in (saved['mean_eta'],saved['mean_sqrt_eta'],saved['V_A'],source['C'],source['w'])]
    mass=old.M(saved['PDF_retained_mass']);eta=old.M('.8')
    n_ch=old.M('.0186')*m1;n_det=old.M('.0135')/eta*mass;fading=(m1-mh*mh)*va
    cv=old.covariance(va,mp.sqrt(eta)*mh,eta*mh*mh,eta*(fading+n_ch+n_det),C,w,'homodyne')
    info=old.measurement(cc,eta*mh*mh,eta*(fading+n_ch+n_det),'homodyne',64)
    kval=old.M('.95')*old.M(info)-cv['chi_BE']
    assert info==saved['I_AB']
    assert abs(cv['chi_BE']-old.M(saved['chi_BE']))<old.M('1e-70')
    assert abs(kval-old.M(saved['K_raw']))<old.M('1e-70')
    save('regression.json',dict(status='CURRENTLY_VERIFIED_PASS',prior_receipt_sha256=sha(prior/'receipt.json'),
         I_AB=info,chi_BE=cv['chi_BE'],K_raw=kval,N_fading=fading,N_channel=n_ch,N_detector=n_det,
         detector_over_channel=n_det/n_ch,fading_over_channel=fading/n_ch,
         source_sha256=sha(ROOT/source['source_path']),saved=saved,
         security_claim=False,meaning='Exact numerical regression of unchanged saved diagnostic functions'))
    mp.mp.dps=80


def alternating(records,configuration_id):
    mb=[r for r in records if r['family']=='MB'];logs=[]
    for initial in (.05,.10,.165,.30):
        current=min(mb,key=lambda r:(abs(r['nu_raw']-initial),abs(r['VA']-5.475)))
        for iteration in range(20):
            va_best=max((r for r in mb if r['nu_raw']==current['nu_raw']),key=lambda r:r['K_raw'])
            nu_best=max((r for r in mb if r['VA']==va_best['VA']),key=lambda r:r['K_raw'])
            delta=nu_best['K_raw']-current['K_raw']
            logs.append(dict(configuration_id=configuration_id,start_nu=initial,iteration=iteration,
                before_hash=current['ensemble_hash'],after_P1_hash=va_best['ensemble_hash'],
                after_P2_hash=nu_best['ensemble_hash'],K_before=current['K_raw'],K_after=nu_best['K_raw'],
                delta_K=delta,status='CATALOG_COORDINATE_FIXED_POINT' if delta<1e-8 else 'CONTINUE',
                source_neighborhood='AUTHENTICATED_EXISTING_CATALOG_ONLY'))
            assert delta>=-1e-14
            current=nu_best
            if delta<1e-8:break
        else:raise ValueError('Finite-catalog alternating ascent did not stop')
    return logs


def main():
    if (OUT/'startup_manifest.json').exists():raise FileExistsError('Preserve started investigation')
    started=time.perf_counter()
    paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z','paper_uav_hap_cvqkd'],cwd=ROOT.parent).decode().split('\0')
    protected={p:sha(ROOT.parent/p) for p in paths if p and (ROOT.parent/p).is_file()
               and not (ROOT.parent/p).resolve().is_relative_to(OUT)}
    save('startup_manifest.json',dict(HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
         branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
         git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT).decode(),protected=protected,
         request_sha256=sha(Path('C:/Users/HP/.codex/attachments/64840f73-a858-41de-b7ba-3ea71eef948f/Pasted text.txt')),
         producers={p.name:sha(p) for p in OUT.glob('*.py')}))
    global SOURCES
    SOURCES=m.load_catalog(read(ROOT/'configs/manuscript_mobility.json'))
    fixed=next(c for c in SOURCES if c['family']=='MB' and c['VA']==5.475 and c['nu_raw']==.165)
    write('source_roster.csv',[{k:v for k,v in c.items() if k not in ('p','alpha')} for c in SOURCES])
    regression();print('REGRESSION PASS; catalog',len(SOURCES),flush=True)
    save('protocol.json',dict(status='DIAGNOSTIC_ONLY_NOT_SECURITY_VALIDATED',diameters=DIAMETERS,
        full_divergence_urad=DIVERGENCES,zenith_angles=ANGLES,detector_efficiencies=EFFICIENCIES,
        detector_output_excess_noise=NOISES,receiver='homodyne_1D',detector_security='untrusted_only',
        channel_excess_noise=.0186,beta=.95,primary_law='power_conserving_random_width',
        comparison_laws=['conditional_active','invalid_tail_to_erasure'],full_Z_grid=33,
        GH_order=64,GH_validation=[32,64,128],source_selection='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
        alternating_delta_K=1e-8,new_source_generation=False,source_interpolation=False,
        original_AO='OFF',original_phase_noise='OFF',no_operational_security_claim=True))
    base=m.optical(.08,233,30);base_m=m.power_conserving(base)
    optical_rows=[]
    for angle in ANGLES:
        for diameter in DIAMETERS:
            for divergence in DIVERGENCES:
                ch=m.optical(diameter,divergence,angle)
                for treatment in ('power_conserving_random_width','conditional_active','invalid_tail_to_erasure'):
                    mo=m.power_conserving(ch) if treatment=='power_conserving_random_width' else m.bounded(ch,treatment)
                    optical_rows.append(evaluate(fixed,ch,mo,'fixed_optical_grid'))
        print('OPTICAL angle complete',angle,flush=True)
    optical_rows.sort(key=lambda r:r['K_raw'],reverse=True)
    write('table_B_optical_feasibility.csv',optical_rows)
    primary=[r for r in optical_rows if r['treatment']=='power_conserving_random_width']
    best_opt=max(primary,key=lambda r:r['K_raw'])
    print('BEST FIXED OPTICAL',best_opt['D_r'],best_opt['theta_div_urad'],best_opt['zenith_deg'],best_opt['K_raw'],flush=True)
    improvement=[]
    for pf,af in [(1,1),(.5,1),(.25,1),(.1,1),(1,.5),(1,.25),(1,.1),(.5,.5),(.25,.25),(.1,.1)]:
        ch=m.optical(best_opt['D_r'],best_opt['theta_div_urad'],best_opt['zenith_deg'],pf,af)
        improvement.append(evaluate(fixed,ch,m.power_conserving(ch),'pointing_improvements'))
    for turbulence in (.5,.25,.1):
        ch=m.optical(best_opt['D_r'],best_opt['theta_div_urad'],best_opt['zenith_deg'],turbulence_factor=turbulence)
        improvement.append(evaluate(fixed,ch,m.power_conserving(ch),'turbulence_improvements'))
    write('pointing_turbulence_sensitivity.csv',improvement)
    best_point=max(improvement,key=lambda r:r['K_raw'])
    configs=[('original',base),('best_optical',configure(best_opt)),('best_pointing',configure(best_point))]
    scans=[];winners=[];ascents=[]
    for label,ch in configs:
        mo=m.power_conserving(ch);records,best=catalog(ch,mo,'catalog_'+label)
        scans.extend({**r,'configuration_id':label} for r in records)
        for family in ('Uniform','MB'):
            row=max((r for r in records if r['family']==family),key=lambda r:r['K_raw'])
            winners.append({**row,'configuration_id':label,'source_group':'catalog_best_'+family})
        fixed_row=next(r for r in records if r['ensemble_hash']==fixed['ensemble_hash'])
        winners.append({**fixed_row,'configuration_id':label,'source_group':'fixed_MB'})
        ascents.extend(alternating(records,label))
        print('CATALOG',label,'best',best['family'],best['VA'],best['nu_raw'],best['K_raw'],flush=True)
    write('exact_catalog_evaluations.csv',scans);write('source_comparison.csv',winners);write('alternating_catalog_search.csv',ascents)
    best=max(winners,key=lambda r:r['K_raw'])
    detector_rows=[];detector_all=[]
    for label,ch in [('original',base),('recommended_optical_pointing',configure(best))]:
        mo=m.power_conserving(ch)
        for eta in EFFICIENCIES:
            for noise in NOISES:
                records,winner=catalog(ch,mo,'detector_'+label,eta,noise)
                detector_all.extend({**r,'configuration_id':label} for r in records)
                detector_rows.append({**winner,'configuration_id':label,'best_exact_source':winner['ensemble_hash']})
            print('DETECTOR',label,eta,'complete',flush=True)
    write('table_C_detector_sensitivity.csv',detector_rows);write('detector_all_exact_evaluations.csv',detector_all)
    thresholds=[]
    for label,ch,source in [('original',base,candidate(next(r for r in winners if r['configuration_id']=='original' and r['source_group']=='catalog_best_MB'))),
                            ('recommended',configure(best),candidate(best))]:
        mo=m.power_conserving(ch)
        for variable,grid in [('epsilon_det',sorted(NOISES)),('eta_det',EFFICIENCIES)]:
            def objective(x):
                return evaluate(source,ch,mo,'threshold',eta=x if variable=='eta_det' else .8,
                                noise=x if variable=='epsilon_det' else .0135)['K_raw']
            vals=[objective(x) for x in grid];brackets=[]
            for lo,hi,flo,fhi in zip(grid[:-1],grid[1:],vals[:-1],vals[1:]):
                if flo*fhi<0:
                    root=brentq(objective,lo,hi,xtol=1e-10,rtol=1e-12)
                    brackets.append(dict(lower=lo,upper=hi,root=root,K_at_root=objective(root)))
            thresholds.append(dict(configuration_id=label,variable=variable,fixed_source_hash=source['ensemble_hash'],
                grid=grid,K_values=vals,brackets=brackets,status='BRACKETED_FIXED_SOURCE_ROOT' if brackets else 'NO_CROSSING_IN_TESTED_RANGE'))
    save('thresholds.json',thresholds)
    distances=[]
    for label,row in [('original',next(r for r in winners if r['configuration_id']=='original' and r['source_group']=='catalog_best_MB')),
                      ('best_optical',next(r for r in winners if r['configuration_id']=='best_optical' and r['source_group']=='catalog_best_MB')),
                      ('recommended',best)]:
        source=candidate(row)
        for length in sorted(set([float(x) for x in range(19,39)]+[21.9393102292])):
            angle=0. if length==19 else min(60.,math.degrees(math.acos(19/length)))
            ch=m.optical(row['D_r'],row['theta_div_urad'],angle,row['position_factor'],row['angular_factor'],row['turbulence_factor'])
            distances.append({**evaluate(source,ch,m.power_conserving(ch),'distance'),
                              'configuration_id':label,'requested_L_km':length})
    write('distance_scan.csv',distances)
    comparisons=[]
    for label,ch in [('original',base),('recommended',configure(best))]:
        mo=m.power_conserving(ch)
        for active in (False,True):
            comparisons.append({**evaluate(candidate(best) if label=='recommended' else fixed,ch,mo,'outage_comparison',active=active),'configuration_id':label})
    write('outage_comparison.csv',comparisons)
    save('selection.json',dict(best_optical_fixed=best_opt,best_pointing_fixed=best_point,recommended=best,
        original_fixed=next(r for r in primary if r['D_r']==.08 and r['theta_div_urad']==233 and r['zenith_deg']==30),
        tested_source_count=len(SOURCES),source_claim='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
        original_detector_positive_count=sum(r['K_raw']>0 for r in winners),
        security_valid=False,source_expansion_status='NOT_RUN_NO_VALIDATED_SECURITY_OBJECTIVE_REQUIRING_AP_EXPANSION'))
    write('all_evaluations.csv',EVALUATIONS)
    ledgers={f'paper_uav_hap_cvqkd/{p}' for p in ('docs/PROJECT_STATE.md','docs/EVIDENCE.md',
        'docs/DECISION_LOG.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md')}
    assert all(sha(ROOT.parent/p)==h for p,h in protected.items() if p not in ledgers),'Protected prior file changed'
    save('run_receipt.json',dict(status='NUMERICAL_SCAN_COMPLETE_DIAGNOSTIC_ONLY',
         all_prior_files_unchanged=len(protected),evaluation_count=len(EVALUATIONS),elapsed_seconds=time.perf_counter()-started,
         artifacts={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.suffix in ('.json','.csv')},
         producer_hashes={p.name:sha(p) for p in OUT.glob('*.py')},security_valid=False))
    print('SCAN COMPLETE',len(EVALUATIONS),'evaluations',time.perf_counter()-started,'seconds',flush=True)


if __name__=='__main__':main()
