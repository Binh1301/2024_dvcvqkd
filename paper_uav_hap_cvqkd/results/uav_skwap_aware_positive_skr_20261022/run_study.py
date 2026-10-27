"""Focused aperture/detector study using the preserved diagnostic equations."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
from scipy.optimize import brentq
import parameter_adapter as n

OUT=n.OUT;ROOT=n.ROOT
BASE=(20.,1.,30.,233.,15.61,1.,.8,.0135,.92,.08)
FIELDS=['h_hap_km','h_uav_km','zenith_deg','divergence_urad','jitter_urad','sigma_h_m','eta_det','epsilon_det','tau_zen','D_r']
DR=[.08,.12,.15,.20,.25,.30];FALLBACK=[.32,.35,.38,.40,.45]
DIV=[15.,20.,25.,35.,50.];JT=[15.61,10.,5.,3.,1.561];SIG=[1.,.5,.3,.2,.1]
TIERS=[(15.61,1.),(10.,.5),(5.,.3),(3.,.2),(3.,.1),(1.561,.1)];ANGLES=[0.,15.,30.]
DETECTORS=[(e,q) for q in [.0135,.005] for e in [.8,.85,.9,.95]]
CORNERS=[(.8,.0135),(.95,.0135),(.8,.005),(.95,.005)]
ROWS=[];CACHE={};REUSED={};SOURCES=[];START=time.monotonic()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,n.saved.mp.mpf):return float(v)
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
def allowed(p):
    assert p[:2]==(20.,1.) and p[8]==.92 and 0<=p[2]<=30 and .08<=p[9]<=.55
    assert min(p[3:6])>0 and p[6] in [.8,.85,.9,.95] and p[7] in [.0135,.005]


def initialize():
    global SOURCES
    start=read(OUT/'startup_manifest.json');protocol=read(OUT/'protocol.json')
    assert all(sha(ROOT/p)==h for p,h in start['imported_model_sha256'].items())
    assert sha(OUT/'parameter_adapter.py')==protocol['adapter_sha256']
    SOURCES=n.previous.load_catalog(read(ROOT/'configs/manuscript_mobility.json'));assert len(SOURCES)==233
    if (OUT/'evaluations.jsonl').exists():
        for line in (OUT/'evaluations.jsonl').read_text().splitlines():
            r=json.loads(line);allowed(par(r));ROWS.append(r);CACHE[key(r,par(r),r['radial_order'],r['width_order'])]=r
    for name in ['minimal_physical_positive_skr_20261022','positive_skr_without_receiver_enlargement_20261022','lightweight_uav_positive_skr_20261022']:
        path=ROOT/'results'/name/'evaluations.jsonl'
        for index,line in enumerate(path.read_text().splitlines(),1):
            old=json.loads(line);r={**old,'h_hap_km':old.get('h_hap_km',20.),'h_uav_km':old.get('h_uav_km',1.),'tau_zen':old.get('tau_zen',.92)}
            if r['h_hap_km']!=20 or r['h_uav_km']!=1 or r['tau_zen']!=.92 or r['epsilon_det'] not in [.0135,.005] or r['eta_det'] not in [.8,.85,.9,.95]:continue
            if not .08<=r['D_r']<=.55 or r['zenith_deg']>30:continue
            REUSED[key(r,par(r),r['radial_order'],r['width_order'])]={**r,'origin':'AUTHENTICATED_REUSED_EXACT_NODE',
                'reused_from':path.relative_to(ROOT).as_posix(),'reused_line':index,'reused_line_sha256':hashlib.sha256(line.encode()).hexdigest()}


def evaluate(c,p,stage,radial=128,width=16,force=False):
    p=tuple(p);allowed(p);k=key(c,p,radial,width)
    if k not in CACHE:
        r=None if force else REUSED.get(k)
        if r is None:r={**clean(n.evaluate(c,p,radial,width)),'origin':'NEW_EXACT_EVALUATION'}
        r={**r,'stage':stage,'hardware_validated':False};CACHE[k]=r;ROWS.append(r)
        with (OUT/'evaluations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(r,allow_nan=False)+'\n')
        if len(ROWS)%200==0:print('NODES',len(ROWS),'elapsed_s',round(time.monotonic()-START,1),flush=True)
    return CACHE[k]


def catalog(p,label):
    rows=[{**evaluate(c,p,'catalog_'+label),'context':label} for c in SOURCES]
    if not (OUT/('catalog_'+label+'.csv')).exists():write('catalog_'+label+'.csv',rows)
    mb=[r for r in rows if r['family']=='MB'];logs=[]
    for start in [.05,.1,.165,.3]:
        current=min(mb,key=lambda r:(abs(r['nu_raw']-start),abs(r['VA']-5.475)))
        for it in range(20):
            p1=max((r for r in mb if r['nu_raw']==current['nu_raw']),key=lambda r:r['K_raw'])
            p2=max((r for r in mb if r['VA']==p1['VA']),key=lambda r:r['K_raw']);delta=p2['K_raw']-current['K_raw'];assert delta>=-1e-13
            logs.append(dict(context=label,start=start,iteration=it,before=current['ensemble_hash'],after_P1=p1['ensemble_hash'],after_P2=p2['ensemble_hash'],delta_K=delta,status='CATALOG_FIXED_POINT' if delta<1e-8 else 'CONTINUE'))
            current=p2
            if delta<1e-8:break
        else:raise AssertionError('Finite catalog ascent did not terminate')
    if not (OUT/('alternating_'+label+'.csv')).exists():write('alternating_'+label+'.csv',logs)
    result=dict(context=label,parameters=list(p),best_MB=max(mb,key=lambda r:r['K_raw']),
        best_Uniform=max((r for r in rows if r['family']=='Uniform'),key=lambda r:r['K_raw']),
        fixed_MB=next(r for r in rows if r['ensemble_hash']==fixed()['ensemble_hash']))
    r=result['best_MB'];print('CATALOG',label,'Dr',p[9],'PAT',p[4:6],'det',p[6:8],'K',r['K_raw'],flush=True)
    return result


def regress():
    old=read(ROOT/'results/minimal_physical_positive_skr_20261022/final_selection.json')['recommendations']
    recent=read(ROOT/'results/lightweight_uav_positive_skr_20261022/selection.json')['recommendations'][-1]
    baseline=read(ROOT/'results/lightweight_uav_positive_skr_20261022/baseline_regression.json')['result']
    records=[]
    for label,r in [('baseline8',baseline),('recent8',recent),('historical40cm',old[0]),('historical55cm',old[1])]:
        p=(20.,1.,r['zenith_deg'],r['divergence_urad'],r['jitter_urad'],r['sigma_h_m'],r['eta_det'],r['epsilon_det'],.92,r['D_r'])
        now=evaluate(source(r),p,'regression_'+label,512,48,force=True)
        differences={k:now[k]-r[k] for k in ['m1','mh','I_AB','chi_BE','K_raw']}
        assert max(abs(v) for v in differences.values())<5e-12,(label,differences)
        records.append(dict(label=label,status='CURRENTLY_VERIFIED_PASS',differences=differences,result=now,expected_K=r['K_raw']))
    assert n.fading_mi.__code__ is n.saved.fading_mi.__code__
    save('regression.json',dict(status='CURRENTLY_VERIFIED_PASS',records=records,MI_bytecode_identical=True))
    print('FOUR MATCHING REGRESSIONS PASS',flush=True)


def screen(diameter):
    result=[]
    for eta,noise in CORNERS:
        for angle in ANGLES:
            for jitter,sigma in TIERS:
                for div in DIV:
                    p=(20.,1.,angle,div,jitter,sigma,eta,noise,.92,diameter)
                    result.append(evaluate(fixed(),p,'physical_screen'))
    print('PHYSICAL Dr',diameter,'fixed_source_bestK',max(r['K_raw'] for r in result),flush=True)
    return result


def physical():
    if (OUT/'physical.json').exists():raise FileExistsError('Preserve completed physical stage')
    initialize();regress();A=[];physical_rows=[]
    write('source_roster.csv',[{k:v for k,v in c.items() if k not in ['p','alpha']} for c in SOURCES])
    for diameter in DR:
        for eta,noise in DETECTORS:
            for context,div,jitter,sigma,angle in [('original_optics',233.,15.61,1.,30.),('improved_fixed_optics',35.,3.,.1,30.),('improved_nadir',35.,3.,.1,0.)]:
                p=(20.,1.,angle,div,jitter,sigma,eta,noise,.92,diameter)
                A.append({**evaluate(fixed(),p,'A_aperture_detector'),'optical_context':context})
        physical_rows.extend(screen(diameter))
        write('table_A_receiver_detector.csv',A);write('physical_screen.csv',physical_rows)
    save('physical.json',dict(status='CURRENTLY_VERIFIED_PASS',primary_diameters=DR,logged_rows=len(ROWS),screen_rows=len(physical_rows),security_valid=False))
    print('PRIMARY PHYSICAL COMPLETE',len(ROWS),flush=True)


def optimize():
    if (OUT/'optimization.json').exists():raise FileExistsError('Preserve completed optimization')
    initialize();assert (OUT/'physical.json').exists();contexts={};history=[]
    if (OUT/'optimization_progress.json').exists():
        old=read(OUT/'optimization_progress.json');contexts={tuple(v['parameters']):v for v in old['contexts']};history=old['history']
    def get(p,label):
        p=tuple(p)
        if p not in contexts:contexts[p]=catalog(p,label)
        return contexts[p]
    def diameter_sources(diameter):
        if any(x['D_r']==diameter for x in history):return
        local=[r for r in ROWS if r['stage']=='physical_screen' and r['D_r']==diameter]
        for index,(eta,noise) in enumerate(CORNERS):
            physical_rows=[r for r in local if (r['eta_det'],r['epsilon_det'])==(eta,noise)]
            for tag,condition in [('moderate',lambda r:r['jitter_urad']>=3),('demanding',lambda r:True)]:
                seed=max((r for r in physical_rows if condition(r)),key=lambda r:r['K_raw'])
                get(par(seed),f'D{diameter:g}_d{index}_{tag}')
            winners={v['best_MB']['ensemble_hash']:source(v['best_MB']) for p,v in contexts.items() if p[9]==diameter and p[6:8]==(eta,noise)}
            tested=[evaluate(c,par(r),'source_physical_coordinate') for c in winners.values() for r in physical_rows]
            # Retain a moderate-PAT branch even when the demanding branch has higher K.
            for tag,condition in [('moderate',lambda r:r['jitter_urad']>=3),('all',lambda r:True)]:
                winner=max((r for r in tested if condition(r)),key=lambda r:r['K_raw'])
                get(par(winner),f'D{diameter:g}_d{index}_coordinate_{tag}')
        history.append(dict(D_r=diameter,positive_contexts=sum(v['best_MB']['K_raw']>0 for p,v in contexts.items() if p[9]==diameter)))
        save('optimization_progress.json',dict(contexts=list(contexts.values()),history=history))
    for diameter in DR:diameter_sources(diameter)
    positive_primary=[v['best_MB'] for v in contexts.values() if v['best_MB']['D_r']<=.30 and v['best_MB']['K_raw']>0]
    fallback=[]
    if not positive_primary:
        for diameter in FALLBACK:
            rows=screen(diameter);fallback.extend(rows);diameter_sources(diameter)
            write('fallback_physical_screen.csv',fallback)
            if any(v['best_MB']['K_raw']>1e-4 for p,v in contexts.items() if p[9]==diameter):break
    save('optimization.json',dict(status='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',contexts=list(contexts.values()),
        history=history,fallback_used=not bool(positive_primary),fallback_diameters=sorted({r['D_r'] for r in fallback}),global_optimum=False,security_valid=False))
    print('OPTIMIZATION COMPLETE',len(ROWS),'contexts',len(contexts),flush=True)


if __name__=='__main__':
    stage=sys.argv[1] if len(sys.argv)>1 else 'physical'
    {'physical':physical,'source':optimize}[stage]()
