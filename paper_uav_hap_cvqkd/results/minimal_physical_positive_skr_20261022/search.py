"""Staged minimal engineering-change search, fixed detector and existing exact sources."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
import numpy as np
from scipy.optimize import brentq
import numeric as n

OUT=n.OUT;ROOT=n.ROOT
DIV=[233.,223.,150.,100.,75.,50.,35.,25.,15.,10.]
DR=[.08,.10,.12,.15,.20,.25,.30,.40,.55,.75]
JT=[15.61,12.,10.,7.5,5.,3.,1.561]
SIG=[1.,.75,.5,.3,.2,.1]
TIERS=[(15.61,1.),(12.,.75),(10.,.5),(7.5,.3),(5.,.2),(3.,.2),(3.,.1),(1.561,.1)]
ROWS=[];CACHE={};SOURCES=[]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def clean(v):
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    return v
def save(name,value):(OUT/name).write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n',encoding='utf-8')
def write(name,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def parameters(row):return tuple(float(row[k]) for k in ['D_r','divergence_urad','jitter_urad','sigma_h_m'])
def source(row):return next(c for c in SOURCES if c['ensemble_hash']==row['ensemble_hash'])

def evaluate(c,par,stage,radial=128,width=16):
    key=(c['ensemble_hash'],*par,radial,width)
    if key not in CACHE:
        row=clean(n.evaluate(c,tuple(par),radial,width));row['stage']=stage
        CACHE[key]=row;ROWS.append(row)
        with (OUT/'evaluations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
    return CACHE[key]

def catalog(par,label):
    rows=[{**evaluate(c,par,'source_'+label),'context':label} for c in SOURCES]
    write('catalog_'+label+'.csv',rows)
    winners=[]
    for family in ('Uniform','MB'):
        winners.append(max((r for r in rows if r['family']==family),key=lambda r:r['K_raw']))
    fixed=next(r for r in rows if r['VA']==5.475 and r['nu_raw']==.165)
    winners.append({**fixed,'family':'Fixed MB'})
    mb=[r for r in rows if r['family']=='MB'];logs=[]
    for initial in (.05,.1,.165,.3):
        current=min(mb,key=lambda r:(abs(r['nu_raw']-initial),abs(r['VA']-5.475)))
        for iteration in range(20):
            p1=max((r for r in mb if r['nu_raw']==current['nu_raw']),key=lambda r:r['K_raw'])
            p2=max((r for r in mb if r['VA']==p1['VA']),key=lambda r:r['K_raw'])
            delta=p2['K_raw']-current['K_raw'];assert delta>=-1e-13
            logs.append(dict(context=label,start=initial,iteration=iteration,before=current['ensemble_hash'],
                after_P1=p1['ensemble_hash'],after_P2=p2['ensemble_hash'],delta_K=delta,
                status='CATALOG_FIXED_POINT' if delta<1e-8 else 'CONTINUE'))
            current=p2
            if delta<1e-8:break
        else:raise ValueError('Finite-catalog ascent failed to stop')
    write('alternating_'+label+'.csv',logs)
    best=max(rows,key=lambda r:r['K_raw'])
    print('CATALOG',label,par,best['VA'],best['nu_raw'],best['K_raw'],flush=True)
    return best,winners

def quality(row):return row['eta_f']/(.016875+.0186*row['m1']+row['variance_sqrt_eta'])

def regress():
    prior=read(n.PRIOR/'final_receipt.json')
    assert all(sha(n.PRIOR/p)==h for p,h in prior['artifact_sha256'].items())
    sel=read(n.PRIOR/'selection.json')['recommended_reference_geometry']
    practical=read(n.PRIOR/'boundary_selection.json')['practical_candidate']
    records=[]
    for label,r in [('A',sel),('B',practical)]:
        par=(r['D_r'],r['theta_div_urad'],1.561,.1)
        c=next(c for c in SOURCES if c['ensemble_hash']==r['ensemble_hash'])
        actual=evaluate(c,par,'regression',512,48)
        expected=.4027555072603608 if label=='A' else .10154737376363399
        assert abs(actual['K_raw']-expected)<5e-12
        direct=n.previous.pooled_mi(c,n.optical(*par)[0],radial_order=128,width_order=16)
        fft=n.fading_mi(c,par,128,16)
        half_grid=n.fading_mi(c,par,128,16,spacing=.0125)
        assert abs(direct['I_AB_pooled']-fft['I_AB_actual'])<5e-12
        assert abs(fft['I_AB_actual']-half_grid['I_AB_actual'])<5e-12
        records.append(dict(label=label,K_raw=actual['K_raw'],expected=expected,
            direct_minus_Fourier=direct['I_AB_pooled']-fft['I_AB_actual'],
            half_grid_difference=half_grid['I_AB_actual']-fft['I_AB_actual'],status='CURRENTLY_VERIFIED_PASS'))
    save('regression.json',records)

def main():
    global SOURCES
    if (OUT/'selection.json').exists():raise FileExistsError('Completed search is immutable')
    paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z','paper_uav_hap_cvqkd'],cwd=ROOT.parent).decode().split('\0')
    if not (OUT/'startup_manifest.json').exists():
        save('startup_manifest.json',dict(HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
            git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT).decode(),
            protected={p:sha(ROOT.parent/p) for p in paths if p and (ROOT.parent/p).is_file() and not (ROOT.parent/p).resolve().is_relative_to(OUT)},
            request_sha256=sha(Path('C:/Users/HP/.codex/attachments/f1566258-97a1-499f-8c3f-8ca4e16902b0/Pasted text.txt')),
            numeric_sha256=sha(OUT/'numeric.py')))
    else:
        assert read(OUT/'startup_manifest.json')['numeric_sha256']==sha(OUT/'numeric.py')
        for line in (OUT/'evaluations.jsonl').read_text().splitlines():
            row=json.loads(line);key=(row['ensemble_hash'],*parameters(row),int(row['radial_order']),int(row['width_order']))
            CACHE[key]=row;ROWS.append(row)
    SOURCES=n.previous.load_catalog(read(ROOT/'configs/manuscript_mobility.json'))
    write('source_roster.csv',[{k:v for k,v in c.items() if k not in ('p','alpha')} for c in SOURCES])
    regress();print('REGRESSIONS PASS',flush=True)
    fixed=next(c for c in SOURCES if c['family']=='MB' and c['VA']==5.475 and c['nu_raw']==.165)
    base=(.08,233.,15.61,1.);baseline=evaluate(fixed,base,'baseline',512,48)
    save('baseline.json',baseline)
    A=[]
    for index,values,label in [(1,DIV,'divergence'),(0,DR,'receiver'),(2,JT,'angular_jitter'),(3,SIG,'position')]:
        for value in values:
            par=list(base);par[index]=value;row=evaluate(fixed,tuple(par),'stage_A_'+label)
            A.append({**row,'changed_parameter':label,'original_value':base[index],'tested_value':value,'delta_K':row['K_raw']-baseline['K_raw']})
    write('table_A_baseline_sensitivity.csv',A);print('STAGE A COMPLETE',flush=True)
    physical=[];receiver_best=[];stage_log=[]
    for diameter in DR:
        local=[]
        for tier,(jitter,sigma) in enumerate(TIERS):
            current=[evaluate(fixed,(diameter,divergence,jitter,sigma),'stage_B' if diameter==.08 else 'stage_C') for divergence in DIV]
            local.extend(current);physical.extend(current)
            positive=[r for r in current if r['K_raw']>=1e-4]
            stage_log.append(dict(D_r=diameter,tier=tier,jitter_urad=jitter,sigma_h_m=sigma,
                best_K=max(r['K_raw'] for r in current),positive_count=len(positive)))
            if positive:break
        receiver_best.append(max(local,key=quality))
        write('staged_physical_scan.csv',physical);write('stage_log.csv',stage_log)
        print('RECEIVER',diameter,'fixed-source bestK',max(x['K_raw'] for x in local),'contexts',len(local),flush=True)
        if diameter>=.20 and any(r['K_raw']>=1e-4 for r in local):break
    all_winners=[];catalog_best=[]
    for i,row in enumerate(receiver_best):
        best,winners=catalog(parameters(row),'receiver_'+str(i));catalog_best.append(best);all_winners.extend(winners)
    write('source_comparisons.csv',all_winners)
    positive=sorted([r for r in catalog_best if r['K_raw']>=1e-4],key=lambda r:r['D_r'])
    if not positive:
        save('selection.json',dict(status='NO_POSITIVE_WITHIN_TESTED_CONTEXTS',best=max(catalog_best,key=lambda r:r['K_raw']),
                                  security_valid=False));return
    # Explore least demanding coordinates only around actual positive channels.
    relaxed=[]
    for i,start in enumerate(positive[:3]):
        c=source(start);par=list(parameters(start))
        for iteration in range(3):
            before=tuple(par)
            for axis,values in [(1,DIV),(2,JT),(3,SIG)]:
                for value in values:
                    changed=par.copy();changed[axis]=value
                    row=evaluate(c,tuple(changed),'local_relaxation');relaxed.append(row)
                    if row['K_raw']>=1.2e-4:par=changed;break
            if tuple(par)==before:break
        _,winners=catalog(tuple(par),'relaxed_'+str(i));all_winners.extend(winners)
    write('local_relaxation.csv',relaxed);write('source_comparisons.csv',all_winners)
    # Engineering Pareto: rate, smaller Rx/Tx, less demanding angular/position accuracy.
    by_physical={}
    for row in ROWS:
        if row['K_raw']<1.2e-4:continue
        par=parameters(row)
        if par not in by_physical or row['K_raw']>by_physical[par]['K_raw']:by_physical[par]=row
    candidates=list(by_physical.values());pareto=[]
    def dimensions(row):return np.array([-row['D_r'],row['divergence_urad'],row['jitter_urad'],row['sigma_h_m'],row['K_raw']])
    for row in candidates:
        d=dimensions(row)
        if not any(np.all(dimensions(other)>=d) and np.any(dimensions(other)>d) for other in candidates):pareto.append(row)
    pareto.sort(key=lambda r:(r['D_r'],-r['divergence_urad'],-r['jitter_urad'],-r['sigma_h_m']))
    write('pareto_screening.csv',pareto)
    minimal=pareto[0]
    def demands(row):return max(row['D_r']/.08,233/row['divergence_urad'],15.61/row['jitter_urad'],1/row['sigma_h_m'])
    balanced=min(pareto,key=lambda x:(demands(x),x['D_r'],-x['K_raw']))
    high=max(candidates,key=lambda x:x['K_raw'])
    # If the fixed-source screen stopped too early, test one safer pointing tier at the
    # selected receiver. This is robustness exploration, not arbitrary new hardware.
    robust_rows=[]
    for row in sorted(pareto,key=lambda x:(demands(x),x['D_r']))[:12]:
        c=source(row);par=parameters(row)
        stressed=evaluate(c,(par[0],par[1],par[2]*1.2,par[3]*1.2),'robustness_screen')
        robust_rows.append({**stressed,'nominal_hash':row['ensemble_hash']})
        if stressed['K_raw']>=1.2e-4:balanced=row;break
    write('robustness_screen.csv',robust_rows)
    selected=[('minimal',minimal),('balanced',balanced),('higher_performance',high)]
    final=[];robustness=[];convergence=[];roots=[]
    for label,row in selected:
        c=source(row);par=parameters(row);last=None;values=[]
        for radial,width in [(256,32),(512,48),(1024,64)]:
            result=evaluate(c,par,'final_'+label,radial,width);values.append(result)
            if last is not None and abs(result['I_AB']-last['I_AB'])<2e-6:break
            last=result
        error=abs(values[-1]['I_AB']-values[-2]['I_AB'])
        assert error<2e-6 and result['K_raw']>2*.95*error
        convergence.append(dict(label=label,orders=[(x['radial_order'],x['width_order']) for x in values],
            observed_MI_change=error,conservative_K_margin=result['K_raw']-2*.95*error))
        result={**result,'recommendation':label,'numerical_MI_error_observed':error};final.append(result)
        for angular in (.8,.9,1.,1.1,1.2):
            for horizontal in (.8,.9,1.,1.1,1.2):
                tested=evaluate(c,(par[0],par[1],par[2]*angular,par[3]*horizontal),'robustness_'+label)
                robustness.append({**tested,'recommendation':label,'angular_perturbation':angular,'horizontal_perturbation':horizontal})
        for axis,name,baseline_value in [(0,'D_r',.08),(1,'divergence_urad',233.),(2,'jitter_urad',15.61),(3,'sigma_h_m',1.)]:
            for target in (0.,1e-4):
                def objective(value):
                    test=list(par);test[axis]=value
                    return evaluate(c,tuple(test),'boundary_'+label,256,32)['K_raw']-target
                low,upper=sorted((par[axis],baseline_value))
                if low==upper:continue
                flo,fhi=objective(low),objective(upper)
                if flo*fhi<0:
                    root=brentq(objective,low,upper,xtol=1e-8,rtol=1e-11)
                    roots.append(dict(recommendation=label,variable=name,target_K=target,root=root,
                        bracket_lower=low,bracket_upper=upper,residual=objective(root),
                        exact_source_hash=c['ensemble_hash'],scope='FIXED_SOURCE_OTHERS_FIXED_NOT_GLOBAL_THRESHOLD'))
    write('robustness.csv',robustness);write('boundary_roots.csv',roots)
    write('table_B_positive_candidates.csv',sorted(final,key=lambda x:(x['D_r'],-x['divergence_urad'])))
    save('selected_convergence.json',convergence)
    save('selection.json',dict(status='POSITIVE_NUMERICAL_DIAGNOSTIC_CANDIDATES',recommendations=final,
        baseline=baseline,receiver_contexts=catalog_best,security_valid=False,hardware_validated=False,
        note='Pareto/engineering demands apply only within sampled menus; no monetary cost or global optimum'))
    write('all_evaluations.csv',ROWS)
    print('SEARCH COMPLETE',[(x['recommendation'],parameters(x),x['K_raw']) for x in final],len(ROWS),flush=True)

if __name__=='__main__':main()
