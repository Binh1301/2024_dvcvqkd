"""Phase1: authenticate/regress, fixed-source sensitivity and staged fixed8cm search."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import mpmath as mp
import numpy as np
import numeric as n

OUT=n.OUT;ROOT=n.ROOT
BASE=(20.,1.,30.,233.,15.61,1.,.8,.0135,.92)
DIV=[233.,150.,100.,75.,50.,35.,25.,20.,15.,10.]
JT=[15.61,10.,7.5,5.,3.,2.,1.561,1.]
SIG=[1.,.75,.5,.3,.2,.1,.05]
ROWS=[];CACHE={};REUSED={};SOURCES=[]
FIELDS=['h_hap_km','h_uav_km','zenith_deg','divergence_urad','jitter_urad','sigma_h_m','eta_det','epsilon_det','tau_zen']


def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,mp.mpf):return float(v)
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    return v
def save(name,v):(OUT/name).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n',encoding='utf-8')
def write(name,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def parameters(r):return tuple(float(r[k]) for k in FIELDS)
def source(r):return next(c for c in SOURCES if c['ensemble_hash']==r['ensemble_hash'])
def quality(r):return r['eta_f']/(r['epsilon_det']/r['eta_det']+.0186*r['m1']+r['variance_sqrt_eta'])


def initialize():
    global SOURCES
    SOURCES=n.previous.load_catalog(read(ROOT/'configs/manuscript_mobility.json'))
    if (OUT/'evaluations.jsonl').exists():
        assert read(OUT/'startup_manifest.json')['numeric_sha256']==sha(OUT/'numeric.py')
        for line in (OUT/'evaluations.jsonl').read_text().splitlines():
            r=json.loads(line);CACHE[(r['ensemble_hash'],*parameters(r),int(r['radial_order']),int(r['width_order']))]=r;ROWS.append(r)
    prior=ROOT/'results/minimal_physical_positive_skr_20261022/evaluations.jsonl'
    for index,line in enumerate(prior.read_text().splitlines(),1):
        r=json.loads(line)
        if r['D_r']!=.08:continue
        par=(20.,1.,r['zenith_deg'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['eta_det'],r['epsilon_det'],.92)
        ch,_=n.optical(*par[:6],par[8])
        r={**clean(ch),**r,'h_hap_km':20.,'h_uav_km':1.,'tau_zen':.92,
            'atmosphere_scope':'ORIGINAL_HEIGHT_CALIBRATED_SCENARIO',
            'origin':'AUTHENTICATED_REUSED_EXACT_NODE','hardware_validated':False,'reused_from':prior.relative_to(ROOT).as_posix(),
            'reused_line':index,'reused_line_sha256':hashlib.sha256(line.encode()).hexdigest()}
        REUSED[(r['ensemble_hash'],*par,int(r['radial_order']),int(r['width_order']))]=r


def evaluate(c,par,stage,radial=128,width=16):
    par=tuple(par);key=(c['ensemble_hash'],*par,radial,width)
    if key not in CACHE:
        row=REUSED.get(key)
        if row is None:row={**clean(n.evaluate(c,par,radial,width)),'origin':'NEW_EXACT_EVALUATION'}
        row={**row,'stage':stage};CACHE[key]=row;ROWS.append(row)
        with (OUT/'evaluations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
    return CACHE[key]


def catalog(par,label):
    rows=[{**evaluate(c,par,'source_'+label),'context':label} for c in SOURCES]
    write('catalog_'+label+'.csv',rows);best=max(rows,key=lambda r:r['K_raw']);logs=[]
    mb=[r for r in rows if r['family']=='MB']
    for start in [.05,.1,.165,.3]:
        current=min(mb,key=lambda r:(abs(r['nu_raw']-start),abs(r['VA']-5.475)))
        for iteration in range(20):
            p1=max((r for r in mb if r['nu_raw']==current['nu_raw']),key=lambda r:r['K_raw'])
            p2=max((r for r in mb if r['VA']==p1['VA']),key=lambda r:r['K_raw']);delta=p2['K_raw']-current['K_raw']
            assert delta>=-1e-13
            logs.append(dict(context=label,start=start,iteration=iteration,before=current['ensemble_hash'],after_P1=p1['ensemble_hash'],after_P2=p2['ensemble_hash'],delta_K=delta,status='CATALOG_FIXED_POINT' if delta<1e-8 else 'CONTINUE'))
            current=p2
            if delta<1e-8:break
        else:raise AssertionError('Finite catalog ascent did not terminate')
    write('alternating_'+label+'.csv',logs)
    print('CATALOG',label,par,best['VA'],best['nu_raw'],best['K_raw'],flush=True)
    return best


def snapshot_and_regress():
    if not (OUT/'startup_manifest.json').exists():
        paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z','paper_uav_hap_cvqkd'],cwd=ROOT.parent).decode().split('\0')
        save('startup_manifest.json',dict(HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
            git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT).decode(),protected={p:sha(ROOT.parent/p) for p in paths if p and (ROOT.parent/p).is_file() and not (ROOT.parent/p).resolve().is_relative_to(OUT)},
            request_sha256=sha(Path('C:/Users/HP/.codex/attachments/599ac194-fdec-45ec-a570-61588bd2a669/Pasted text.txt')),numeric_sha256=sha(OUT/'numeric.py')))
    for name in ['untrusted_positive_skr_feasibility_20261022','minimal_physical_positive_skr_20261022']:
        folder=ROOT/'results'/name;receipt=read(folder/'final_receipt.json')
        assert all(sha(folder/p)==h for p,h in receipt['artifact_sha256'].items())
    import run as historical_run
    historical_run.OUT=OUT;mp.mp.dps=110;historical_run.regression()
    print('HISTORICAL REGRESSION PASS',flush=True)


def main():
    if (OUT/'phase1.json').exists():raise FileExistsError('Preserve completed phase1')
    snapshot_and_regress();initialize()
    fixed=next(c for c in SOURCES if c['VA']==5.475 and c['nu_raw']==.165)
    baseline=evaluate(fixed,BASE,'bounded_baseline',512,48)
    assert abs(baseline['K_raw']-(-.05869636307980502))<1e-12
    save('bounded_baseline.json',baseline);write('source_roster.csv',[{k:v for k,v in c.items() if k not in ('p','alpha')} for c in SOURCES])
    # Check the local geometry generalization at the original heights and angle.
    old=n.previous.optical(.08,233,30)
    new,_=n.optical(*BASE[:6],BASE[8])
    deltas={k:float(new[k])-float(old[k]) for k in ['L_km','w0_m','wL_m','w_eff_m','G_d','v','eta_atm','sigma_s_m','P0']}
    assert max(abs(x) for x in deltas.values())<1e-12
    save('geometry_regression.json',dict(status='CURRENTLY_VERIFIED_PASS',differences=deltas))
    A=[]
    scans=[(2,[0.,5.,10.,15.,20.,25.,30.],'zenith'),(0,[17.,18.,19.,20.,22.,25.],'HAP_height'),
        (1,[1.,2.,3.,5.],'UAV_height'),(6,[.8,.85,.9,.95,.98,1.],'detector_efficiency'),
        (7,[.0135,.010,.005,.002,.001,.0005,0.],'detector_noise'),(3,DIV+[223.],'divergence'),(4,JT,'angular_jitter'),(5,SIG,'position')]
    for axis,values,label in scans:
        for value in values:
            par=list(BASE);par[axis]=value;r=evaluate(fixed,par,'A_'+label)
            A.append({**r,'changed_parameter':label,'original_value':BASE[axis],'modified_value':value,'delta_K':r['K_raw']-baseline['K_raw']})
    write('table_1_individual_sensitivity.csv',A);print('STAGE A COMPLETE',flush=True)
    # Fixed receiver, geometry progression; stronger PAT only after moderate tiers.
    geometries=[(20.,1.,30.),(20.,1.,0.),(17.,1.,0.),(20.,3.,0.),(20.,5.,0.),(17.,5.,0.)]
    tiers=[(15.61,1.),(10.,.5),(7.5,.3),(5.,.2),(3.,.1),(2.,.1),(1.561,.05),(1.,.05)]
    physical=[];shortlist=[];progress=[]
    for index,geometry in enumerate(geometries):
        local=[]
        for jitter,sigma in tiers:
            current=[evaluate(fixed,(*geometry,div,jitter,sigma,.8,.0135,.92),'B_fixed_detector') for div in DIV]
            local.extend(current);physical.extend(current)
            progress.append(dict(h_hap_km=geometry[0],h_uav_km=geometry[1],zenith_deg=geometry[2],jitter_urad=jitter,sigma_h_m=sigma,best_K=max(r['K_raw'] for r in current)))
            if any(r['K_raw']>=1e-4 for r in current):break
        context=max(local,key=quality);shortlist.append(context)
        write('stage_B_physical_scan.csv',physical);write('stage_B_progress.csv',progress)
        print('STAGE B',geometry,'best_fixed_K',max(r['K_raw'] for r in local),flush=True)
    optimized=[catalog(parameters(r),'B_'+str(i)) for i,r in enumerate(shortlist)]
    save('phase1.json',dict(baseline=baseline,fixed_source_hash=fixed['ensemble_hash'],B_shortlist=shortlist,B_catalog_best=optimized,
        altitude_extinction='VERTICAL_PROFILE_NOT_PROVIDED; changed heights diagnostic only',
        user_weather_pairs=[dict(visibility_km=v,tau_zen=t) for v,t in [(23,.92),(15,.89),(5,.75)]],security_valid=False))
    write('all_evaluations.csv',ROWS);print('PHASE1 COMPLETE',len(ROWS),flush=True)


if __name__=='__main__':main()
