"""Parameter-only staging around the unchanged, hash-bound saved evaluator."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'results/positive_skr_without_receiver_enlargement_20261022'))
import numeric as n

BASE=(20.,1.,30.,233.,15.61,1.,.8,.0135,.92)
FIELDS=['h_hap_km','h_uav_km','zenith_deg','divergence_urad','jitter_urad','sigma_h_m','eta_det','epsilon_det','tau_zen']
DIV=[233.,100.,75.,50.,35.,25.,20.,15.]
JT=[15.61,10.,7.5,5.,3.,1.561];SIG=[1.,.5,.3,.2,.1];ANGLES=[0.,15.,30.]
DETECTORS=[(e,q) for q in [.0135,.005] for e in [.8,.85,.9,.95]]
TIERS=list(zip(JT,[1.,.5,.3,.2,.1,.1]))
ROWS=[];CACHE={};REUSED={};SOURCES=[];START=time.monotonic()


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,n.mp.mpf):return float(v)
    if isinstance(v,n.np.generic):return v.item()
    if isinstance(v,n.np.ndarray):return v.tolist()
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    return v
def save(name,v):(OUT/name).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n',encoding='utf-8')
def write(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def par(r):return tuple(float(r[k]) for k in FIELDS)
def key(c,p,radial,width):return (c['ensemble_hash'],*p,radial,width)
def source(r):return next(c for c in SOURCES if c['ensemble_hash']==r['ensemble_hash'])
def fixed():return next(c for c in SOURCES if c['family']=='MB' and c['VA']==5.475 and c['nu_raw']==.165)
def quality(r):return r['eta_f']/(r['variance_sqrt_eta']+.0186*r['m1']+r['epsilon_det']/r['eta_det'])
def allowed(p):
    assert p[:2]==(20.,1.) and p[8]==.92 and 0<=p[2]<=30
    assert min(p[3:6])>0 and p[6] in [.8,.85,.9,.95] and p[7] in [.0135,.005]


def initialize():
    global SOURCES
    start=read(OUT/'startup_manifest.json')
    assert all(sha(ROOT/p)==h for p,h in start['imported_model_sha256'].items())
    SOURCES=n.previous.load_catalog(read(ROOT/'configs/manuscript_mobility.json'))
    assert len(SOURCES)==233
    if (OUT/'evaluations.jsonl').exists():
        for line in (OUT/'evaluations.jsonl').read_text().splitlines():
            r=json.loads(line);allowed(par(r));ROWS.append(r)
            CACHE[key(r,par(r),r['radial_order'],r['width_order'])]=r
    path=ROOT/'results/positive_skr_without_receiver_enlargement_20261022/evaluations.jsonl'
    for index,line in enumerate(path.read_text().splitlines(),1):
        r=json.loads(line)
        if (r['D_r']!=.08 or r['h_hap_km']!=20 or r['h_uav_km']!=1 or r['tau_zen']!=.92
                or r['epsilon_det'] not in [.0135,.005] or r['eta_det'] not in [.8,.85,.9,.95]):continue
        REUSED[key(r,par(r),r['radial_order'],r['width_order'])]={**r,
            'origin':'AUTHENTICATED_REUSED_EXACT_NODE','reused_from':path.relative_to(ROOT).as_posix(),
            'reused_line':index,'reused_line_sha256':hashlib.sha256(line.encode()).hexdigest()}


def evaluate(c,p,stage,radial=128,width=16,force=False):
    p=tuple(p);allowed(p);k=key(c,p,radial,width)
    if k not in CACHE:
        r=None if force else REUSED.get(k)
        if r is None:r={**clean(n.evaluate(c,p,radial,width)),'origin':'NEW_EXACT_EVALUATION'}
        r={**r,'stage':stage,'hardware_validated':False};CACHE[k]=r;ROWS.append(r)
        with (OUT/'evaluations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(r,allow_nan=False)+'\n')
        if len(ROWS)%100==0:print('NODES',len(ROWS),'elapsed_s',round(time.monotonic()-START,1),flush=True)
    return CACHE[k]


def catalog(p,label):
    path=OUT/('catalog_'+label+'.csv')
    rows=[{**evaluate(c,p,'E_catalog_'+label),'context':label} for c in SOURCES]
    if not path.exists():write(path.name,rows)
    mb=[r for r in rows if r['family']=='MB'];logs=[]
    for start in [.05,.1,.165,.3]:
        current=min(mb,key=lambda r:(abs(r['nu_raw']-start),abs(r['VA']-5.475)))
        for it in range(20):
            p1=max((r for r in mb if r['nu_raw']==current['nu_raw']),key=lambda r:r['K_raw'])
            p2=max((r for r in mb if r['VA']==p1['VA']),key=lambda r:r['K_raw'])
            delta=p2['K_raw']-current['K_raw'];assert delta>=-1e-13
            logs.append(dict(context=label,start=start,iteration=it,before=current['ensemble_hash'],
                after_P1=p1['ensemble_hash'],after_P2=p2['ensemble_hash'],delta_K=delta,
                status='CATALOG_FIXED_POINT' if delta<1e-8 else 'CONTINUE'))
            current=p2
            if delta<1e-8:break
        else:raise AssertionError('Finite catalog ascent did not terminate')
    if not (OUT/('alternating_'+label+'.csv')).exists():write('alternating_'+label+'.csv',logs)
    best=max(mb,key=lambda r:r['K_raw']);uniform=max((r for r in rows if r['family']=='Uniform'),key=lambda r:r['K_raw'])
    print('CATALOG',label,'VA',best['VA'],'nu',best['nu_raw'],'K',best['K_raw'],flush=True)
    return dict(context=label,parameters=list(p),best_MB=best,best_Uniform=uniform,
        fixed_MB=next(r for r in rows if r['ensemble_hash']==fixed()['ensemble_hash']))


def physical():
    if (OUT/'physical.json').exists():raise FileExistsError('Preserve completed physical stage')
    initialize()
    baseline=evaluate(fixed(),BASE,'baseline_recomputed',512,48,force=True)
    old=read(ROOT/'results/positive_skr_without_receiver_enlargement_20261022/bounded_baseline.json')
    diffs={k:baseline[k]-old[k] for k in ['m1','mh','eta_f','a','b','I_AB','chi_BE','K_raw']}
    assert max(abs(v) for v in diffs.values())<1e-12
    save('baseline_regression.json',dict(status='CURRENTLY_VERIFIED_PASS',differences=diffs,result=baseline,
        historical_corrected_trial=read(ROOT/'results/positive_skr_without_receiver_enlargement_20261022/regression.json'),
        historical_scope='Authenticated historical law only; not substituted for the current bounded baseline'))
    print('BASELINE PASS',baseline['K_raw'],flush=True)
    write('source_roster.csv',[{k:v for k,v in c.items() if k not in ['p','alpha']} for c in SOURCES])
    A=[];B=[];C=[];D=[]
    for eta,noise in DETECTORS:
        p=list(BASE);p[6:8]=eta,noise;r=evaluate(fixed(),p,'A_detector_only')
        A.append({**r,'remaining_gap':r['chi_BE']-r['beta_I_AB']})
        for div in DIV:
            p=list(BASE);p[3]=div;p[6:8]=eta,noise
            B.append(evaluate(fixed(),p,'B_transmitter'))
        for axis,values,label in [(4,JT,'angular_jitter'),(5,SIG,'centering')]:
            for value in values:
                p=list(BASE);p[axis]=value;p[6:8]=eta,noise
                C.append({**evaluate(fixed(),p,'C_'+label),'changed_parameter':label,'modified_value':value})
        for angle in ANGLES:
            for jt,sigma in TIERS:
                for div in DIV:
                    p=(20.,1.,angle,div,jt,sigma,eta,noise,.92)
                    D.append(evaluate(fixed(),p,'D_staged_physical'))
        print('PHYSICAL DETECTOR',eta,noise,'complete',flush=True)
    write('stage_A_detector_only.csv',A);write('stage_B_transmitter.csv',B)
    write('stage_C_independent_pointing.csv',C);write('stage_D_staged_physical.csv',D)
    save('physical.json',dict(baseline=baseline,rows=len(ROWS),fixed_source_hash=fixed()['ensemble_hash'],
        detector_scenarios=DETECTORS,PAT_tiers=TIERS,altitude_sweep='NOT_RUN; no altitude-dependent extinction profile',
        physical_parameter_tuples=len({par(r) for r in D}),security_valid=False))
    print('PHYSICAL COMPLETE',len(ROWS),flush=True)


def optimize():
    if (OUT/'optimization.json').exists():raise FileExistsError('Preserve completed source stage')
    initialize();assert (OUT/'physical.json').exists()
    physical_rows=[r for r in ROWS if r['ensemble_hash']==fixed()['ensemble_hash'] and r['radial_order']==128
        and r['zenith_deg'] in ANGLES and r['divergence_urad'] in DIV and (r['jitter_urad'],r['sigma_h_m']) in TIERS]
    contexts={};history=[]
    def get(p,label):
        p=tuple(p)
        if p not in contexts:contexts[p]=catalog(p,label)
        return contexts[p]
    for index,(eta,noise) in enumerate(DETECTORS):
        candidates=[r for r in physical_rows if (r['eta_det'],r['epsilon_det'])==(eta,noise)]
        for criterion,fn in [('fixedK',lambda r:r['K_raw']),('moment',quality)]:
            chosen=max(candidates,key=fn);get(par(chosen),f'd{index}_{criterion}')
        if eta==.8:
            p=list(BASE);p[6:8]=eta,noise;get(p,f'd{index}_baseline')
        # A second exact-source/physical coordinate step, not a continuous optimum.
        local=[v for p,v in contexts.items() if p[6:8]==(eta,noise)]
        winners={v['best_MB']['ensemble_hash']:source(v['best_MB']) for v in local}
        tested=[]
        for c in winners.values():
            tested.extend(evaluate(c,par(r),'E_physical_coordinate') for r in candidates)
        winner=max(tested,key=lambda r:r['K_raw']);final=get(par(winner),f'd{index}_coordinate')
        history.append(dict(detector_index=index,eta_det=eta,epsilon_det=noise,
            sources_scanned=list(winners),physical_contexts=len(candidates),
            after_physical=winner,after_source=final['best_MB']))
        save('optimization_progress.json',dict(contexts=list(contexts.values()),coordinate_history=history))
    save('optimization.json',dict(contexts=list(contexts.values()),coordinate_history=history,
        status='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',global_optimum=False,security_valid=False))
    print('OPTIMIZATION COMPLETE',len(ROWS),'catalog_contexts',len(contexts),flush=True)


def finish():
    if (OUT/'selection.json').exists():raise FileExistsError('Preserve completed selection')
    initialize();opt=read(OUT/'optimization.json');selected=[]
    for index,(eta,noise) in enumerate(DETECTORS):
        # Include all exact physical-coordinate probes, not just catalog maxima.
        candidates=[r for r in ROWS if r['family']=='MB' and (r['eta_det'],r['epsilon_det'])==(eta,noise)]
        short=sorted(candidates,key=lambda r:r['K_raw'],reverse=True)[:3]
        fine=[evaluate(source(r),par(r),'selected_refinement',512,48) for r in short]
        best=max(fine,key=lambda r:r['K_raw']);selected.append({**best,'detector_index':index})
    # No positive configuration is relabeled as a recommendation if it failed.
    A=max((r for r in selected if (r['eta_det'],r['epsilon_det'])==(.8,.0135)),key=lambda r:r['K_raw'])
    B=max((r for r in selected if r['eta_det']<=.9 and r['epsilon_det']==.005),key=lambda r:r['K_raw'])
    C=max(selected,key=lambda r:r['K_raw'])
    recommendations=[{**r,'configuration':label} for label,r in zip(['A_minimum_UAV_burden','B_balanced_reference','C_highest_tested_reference'],[A,B,C])]
    convergence=[];robust=[];curves=[];comparisons=[]
    for r in selected:
        c=source(r);p=par(r);coarse=evaluate(c,p,'convergence',256,32)
        convergence.append(dict(detector_index=r['detector_index'],parameters=p,ensemble_hash=r['ensemble_hash'],
            I_256=coarse['I_AB'],I_512=r['I_AB'],observed_MI_change=abs(coarse['I_AB']-r['I_AB']),K_512=r['K_raw']))
        for jf,sf,label in [(1.,1.,'nominal'),(1.1,1.,'jitter_plus10'),(1.,1.1,'centering_plus10'),(1.1,1.1,'joint_plus10'),(1.2,1.2,'joint_plus20')]:
            q=list(p);q[4]*=jf;q[5]*=sf
            robust.append({**evaluate(c,q,'robustness',256,32),'detector_index':r['detector_index'],'case':label})
        for noise in [.0135,.005]:
            q=list(p);q[7]=noise
            robust.append({**evaluate(c,q,'robustness_noise',256,32),'detector_index':r['detector_index'],'case':'noise_'+str(noise)})
        # Same-channel comparisons: catalog ranked at precisely this physical point.
        ctx=next((v for v in opt['contexts'] if tuple(v['parameters'])==p),None)
        if ctx is None:ctx=catalog(p,'final_d'+str(r['detector_index']))
        for scheme,reference in [('Uniform_best_catalog',ctx['best_Uniform']),('MB_fixed',ctx['fixed_MB']),('MB_best_exact_tested',r)]:
            comparisons.append({**evaluate(source(reference),p,'source_comparison',512,48),'detector_index':r['detector_index'],'scheme':scheme})
    for r in recommendations:
        c=source(r);p=par(r)
        for axis,values,label in [(2,ANGLES,'zenith'),(3,DIV,'divergence'),(4,JT,'angular_jitter'),(5,SIG,'centering'),(6,[.8,.85,.9,.95],'efficiency'),(7,[.0135,.005],'detector_noise')]:
            for value in values:
                q=list(p);q[axis]=value
                curves.append({**evaluate(c,q,'selected_sensitivity',256,32),'configuration':r['configuration'],'axis':label,'axis_value':value})
    write('detector_scenario_best.csv',selected);write('recommendations.csv',recommendations)
    write('robustness.csv',robust);write('source_comparison.csv',comparisons);write('selected_sensitivity.csv',curves)
    save('convergence.json',convergence)
    save('selection.json',dict(recommendations=recommendations,detector_scenario_best=selected,
        nominal_positive_count=sum(r['K_raw']>0 for r in selected),
        selected_status='POSITIVE_CANDIDATES' if any(r['K_raw']>0 for r in selected) else 'NO_POSITIVE_FOUND; CLOSEST_TESTED_REFERENCES_ONLY',
        security_valid=False,hardware_validated=False,global_optimum=False))
    write('all_evaluations.csv',ROWS)
    print('SELECTION COMPLETE',len(ROWS),'positive',sum(r['K_raw']>0 for r in selected),flush=True)


if __name__=='__main__':
    stage=sys.argv[1] if len(sys.argv)>1 else 'physical'
    {'physical':physical,'source':optimize,'finish':finish}[stage]()
