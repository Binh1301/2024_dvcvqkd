"""Staged Uniform-only search; raw PDF primary, independent bounded law separate."""
import csv
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
AUDIT=ROOT/'results/manuscript43_homodyne_audit_20261023'
sys.path.insert(0,str(AUDIT))
import audit_model as a
import run_audit as r
from compare import independent_entropy
import mpmath as mp
import numpy as np
from scripts.exact_cache_provenance import source_settings,verify_source_payload
from scripts.run_exact_mb_test2 import ensemble_hash
from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble,unconstrained_config

spec=importlib.util.spec_from_file_location('_verified_v43_sweep',ROOT/'results/skr_vs_zenith_manuscript43_20261023/run_sweep.py')
verified=importlib.util.module_from_spec(spec);spec.loader.exec_module(verified)
RAW='manuscript43_Eq10_retained_0_to_1'
BOUNDED='power_conserving_random_width'


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(r.clean(v),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def write(p,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(r.clean(rows))
def key(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()


def bank(include_new=False):
    sources=[c for c in r.catalog() if c['family']=='Uniform' and .05<=c['VA']<=10]
    if include_new:
        config=unconstrained_config();settings=source_settings(config)
        for path in sorted((OUT/'new_exact_source/exact_source_cache').glob('*.json')):
            payload=read(path);verify_source_payload(payload,settings)
            va=float.fromhex(payload['V_A_hex']);ensemble=make_ensemble(config,'Uniform',0.,va)
            identity=ensemble_hash(ensemble)
            if identity!=payload['ensemble_hash']:raise ValueError('Fresh Uniform ensemble mismatch')
            sources.append(dict(family='Uniform',VA=va,nu_raw=0.,C=payload['C'],w=payload['w'],
                ensemble_hash=identity,source_path=path.relative_to(ROOT).as_posix(),source_sha256=a.sha(path),
                p=ensemble.probabilities[0].numpy(),alpha=ensemble.amplitudes[0].numpy(),
                source_moment_route=payload['source_moment_route']))
    unique={c['VA'].hex():c for c in sources}
    for c in unique.values():
        p,alpha=a.validate_source(c)
        if not np.all(p==1/256):raise ValueError('Uniform requires exactly equal256 probabilities')
    return sorted(unique.values(),key=lambda c:c['VA'])


def model(c,moments,order=64,grid=33):
    if not moments['normalized_within_tolerance']:raise ValueError('FAILED_PDF_NORMALIZATION')
    t=moments['mh']**2;mn=.0186*moments['m1']+.005*moments['M0']
    noise=(moments['m1']-t)*c['VA']+mn
    if not 0<=t<=moments['m1']<=1 or noise<0:raise ValueError('Invalid effective moments/noise')
    h=a.legacy.full_holevo(1+c['VA'],1+t*c['VA']+noise,2*math.sqrt(t)*c['C'],math.sqrt(2*noise*c['w']),grid)
    mi=a.homodyne_mi(c['p'],c['alpha'],t,1+noise,order=order)
    value=dict(**h,I_AB=mi,beta_I_AB=.95*mi,K_raw=.95*mi-h['chi_BE'],eta_f=t,
        N_effective=noise,mean_eta_xi=mn,xi_f=noise/t,sigma2_MI=1+noise,T_Holevo=t,xi_det=.005,
        **{k:c[k] for k in ['family','VA','nu_raw','ensemble_hash','C','w','source_path','source_sha256']})
    _,pmarg=a.marginal(c['p'],c['alpha'])
    entropy=-float(pmarg@np.log2(pmarg));capacity=.5*math.log2(1+t*c['VA']/(1+noise))
    if not all(math.isfinite(value[k]) for k in ['I_AB','chi_BE','K_raw']) or mi < -2e-12 or mi>min(entropy,capacity)+2e-10:
        raise ValueError('Invalid discrete homodyne information')
    return {**value,**verified.covariance(value,c['VA'])}


class Search:
    def __init__(self,sources):
        self.sources=sources;self.contexts={};self.best_rows=[];self.source_by_hash={c['ensemble_hash']:c for c in sources}
        (OUT/'contexts').mkdir(exist_ok=True)

    def context(self,g,law=RAW):
        identity=key([list(g),law])
        if identity in self.contexts:return self.contexts[identity]
        path=OUT/'contexts'/(identity+'.json')
        if path.exists():
            result=read(path)
        else:
            diameter,div,jitter,sigma,angle=g
            ch=a.legacy.optical(diameter,div,angle,sigma,mp.mpf(str(jitter))/mp.mpf('15.61'))
            if law==RAW:
                moments=a.raw_pdf_moments(ch)
                if max(abs(x['residual']) for x in moments['direct'].values())>2e-10:raise ValueError('PDF quadrature failure')
            elif law==BOUNDED:
                mo=a.legacy.power_conserving(ch)
                moments=dict(M0=mo['physical_mass'],m1=mo['m1'],mh=mo['mh'],P0=mo['P0'],
                    normalized_within_tolerance=True,raw_upper_tail_mass=0.,renormalized=False,clipped=False,law=BOUNDED,
                    independent_optical_law=True,width_GH_order=mo['width_GH_order'],radial_error=mo['radial_quadrature_error'])
            else:raise ValueError('Unknown law')
            result=dict(geometry=list(g),law=law,channel=r.clean(ch),moments=r.clean(moments),evaluations={},failures={})
        self.contexts[identity]=result
        return result

    def persist(self,ctx):save(OUT/'contexts'/(key([ctx['geometry'],ctx['law']])+'.json'),ctx)

    def optimize(self,g,stage,law=RAW,sources=None,adaptive=False):
        ctx=self.context(g,law);mom=ctx['moments'];sources=self.sources if sources is None else sources
        if not mom['normalized_within_tolerance']:
            self.persist(ctx);value=self.row(ctx,None,stage,'FAILED_PDF_NORMALIZATION')
            self.best_rows.append(value);return value
        def evaluate(c):
            identity=c['ensemble_hash']
            if identity not in ctx['evaluations'] and identity not in ctx['failures']:
                try:ctx['evaluations'][identity]=model(c,mom)
                except ValueError as error:ctx['failures'][identity]=dict(VA=c['VA'],source_hash=identity,reason=str(error))
            return ctx['evaluations'].get(identity)
        if adaptive:
            coarse=[c for c in sources if c['VA'] in [.05,.1,.2,.3,.5,1.,2.,3.,5.,8.,10.]]
            coarse_values=[(c,evaluate(c)) for c in coarse];peaks=[]
            for i,(c,v) in enumerate(coarse_values):
                if v is None:continue
                left=-math.inf if i==0 or coarse_values[i-1][1] is None else coarse_values[i-1][1]['K_raw']
                right=-math.inf if i==len(coarse_values)-1 or coarse_values[i+1][1] is None else coarse_values[i+1][1]['K_raw']
                if v['K_raw']>=max(left,right):
                    peaks.append((coarse[max(0,i-1)]['VA'],coarse[min(len(coarse)-1,i+1)]['VA']))
            candidates=[c for c in sources if any(lo<=c['VA']<=hi for lo,hi in peaks)]
        else:candidates=sources
        values=[evaluate(c) for c in candidates];values=[v for v in values if v is not None]
        # Include coarse points too; narrowing does not discard an already tested best.
        values.extend(v for v in ctx['evaluations'].values() if v['ensemble_hash'] in {c['ensemble_hash'] for c in sources})
        best=max(values,key=lambda v:(v['K_raw'],-v['VA'])) if values else None
        self.persist(ctx)
        value=self.row(ctx,best,stage,'' if best else 'FAILED_COVARIANCE_OR_INFORMATION')
        self.best_rows.append(value);return value

    def row(self,ctx,value,stage,reason):
        diameter,div,jitter,sigma,angle=ctx['geometry'];mo=ctx['moments'];ch=ctx['channel']
        return dict(stage=stage,zenith_deg=angle,distance_km=ch['L_km'],Dr_m=diameter,divergence_urad=div,
            jitter_urad=jitter,sigma_h_m=sigma,VA=None if value is None else value['VA'],
            source_hash=None if value is None else value['ensemble_hash'],channel_law=ctx['law'],pdf_mass=mo['M0'],
            mass_deficit=mo['raw_upper_tail_mass'],E_eta=mo['m1'],E_sqrt_eta=mo['mh'],eta_f=mo['mh']**2,
            E_eta_xi=.0186*mo['m1']+.005*mo['M0'],xi_f=None if value is None else value['xi_f'],
            I_AB=None if value is None else value['I_AB'],beta_I_AB=None if value is None else value['beta_I_AB'],
            chi_BE=None if value is None else value['chi_BE'],raw_SKR=None if value is None else value['K_raw'],
            validation_status='NUMERICALLY_VALID_SECURITY_PROVISIONAL' if value is not None else 'BLOCKED',
            exclusion_reason=reason,context_id=key([ctx['geometry'],ctx['law']]),
            source_path=None if value is None else value['source_path'],source_sha256=None if value is None else value['source_sha256'],
            xi_ch=.0186,xi_det=.005,security_valid=False)


def geometry(row):return (row['Dr_m'],row['divergence_urad'],row['jitter_urad'],row['sigma_h_m'],row['zenith_deg'])
def numeric(rows):return [x for x in rows if x['raw_SKR'] is not None]
def best(rows):return max(numeric(rows),key=lambda x:x['raw_SKR']) if numeric(rows) else None
def short_sources(sources):return [c for c in sources if c['VA'] in [.05,.1,.3,1.,5.]]


def screen():
    if (OUT/'screen_receipt.json').exists():raise FileExistsError('Preserve completed screen')
    sources=bank();search=Search(sources);A=[]
    for angle in range(31):A.append(search.optimize((.3,35.,1.561,.1,float(angle)),'A_initial',adaptive=True))
    save(OUT/'stage_A_initial.json',A)
    print('STAGE A INITIAL',best(A),flush=True)
    screenB=[];count=0
    for div,jitter,sigma,angle in itertools.product([10,15,20,25,30,35,40,50,60],[.5,1.,1.561,2.,3.],[.03,.05,.1,.15,.2],[0.,10.,20.]):
        screenB.append(search.optimize((.3,float(div),jitter,sigma,angle),'B_coarse',sources=short_sources(sources)))
        count+=1
        if count%75==0:print('STAGE B SCREEN',count,'/675',flush=True)
    refinedB=[search.optimize(geometry(x),'B_full_bank') for x in sorted(numeric(screenB),key=lambda x:-x['raw_SKR'])[:16]]
    settings=[]
    for row in sorted(numeric(refinedB),key=lambda x:-x['raw_SKR']):
        setting=geometry(row)[1:4]
        if setting not in settings:settings.append(setting)
        if len(settings)==4:break
    fineB=[]
    for div,jitter,sigma in settings:
        for angle in range(21):fineB.append(search.optimize((.3,div,jitter,sigma,float(angle)),'B_angle_refine'))
    B=screenB+refinedB+fineB;save(OUT/'stage_B_initial.json',B)
    print('STAGE B INITIAL BEST',best(B),flush=True)
    C=[];promising=[]
    if not any(x['raw_SKR'] is not None and x['raw_SKR']>0 for x in A+B):
        center=best(B)['divergence_urad'];all_div=[10,15,20,25,30,35,40,50,60];idx=all_div.index(center)
        promising=all_div[max(0,idx-1):min(len(all_div),idx+2)]
        for diameter in [.35,.4,.45,.5,.55,.6]:
            coarse=[]
            for div,jitter,sigma,angle in itertools.product(promising,[.5,1.,1.561],[.03,.1,.2],[0.,10.,20.,30.]):
                coarse.append(search.optimize((diameter,float(div),jitter,sigma,angle),'C_coarse',sources=short_sources(sources)))
            if not numeric(coarse):
                for div,jitter,sigma,angle in itertools.product(promising,[.5,1.,1.561],[.03,.1,.2],[40.,50.,60.]):
                    coarse.append(search.optimize((diameter,float(div),jitter,sigma,angle),'C_normalized_angle_fallback',sources=short_sources(sources)))
            fine=[search.optimize(geometry(x),'C_full_bank') for x in sorted(numeric(coarse),key=lambda x:-x['raw_SKR'])[:4]]
            C.extend(coarse+fine);print('STAGE C INITIAL',diameter,'BEST',best(coarse+fine),flush=True)
    save(OUT/'stage_C_initial.json',C)
    # Secondary law is separately defined, justified by the raw-PDF normalization blocker.
    secondary=[]
    if not any(x['raw_SKR'] is not None and x['raw_SKR']>0 for x in A+B+C):
        for div,jitter,sigma in itertools.product([10.,15.,20.,25.,35.,50.],[.5,1.,1.561],[.03,.05,.1]):
            secondary.append(search.optimize((.3,div,jitter,sigma,0.),'SECONDARY_bounded_screen',BOUNDED))
        print('SECONDARY BOUNDED BEST',best(secondary),flush=True)
    save(OUT/'secondary_initial.json',secondary)
    save(OUT/'screen_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',source_count=len(sources),
        A_best=best(A),B_best=best(B),C_best=best(C),secondary_best=best(secondary),
        primary_positive_found=any(x['raw_SKR'] is not None and x['raw_SKR']>0 for x in A+B+C),
        contexts=len(search.contexts),prospective_protocol_sha256=a.sha(OUT/'protocol.json'),
        producer_sha256=a.sha(Path(__file__)),new_AP_sources_pending=[10.,.25]))
    print('INITIAL SCREEN COMPLETE',len(search.contexts),'contexts',flush=True)


if __name__=='__main__':
    if sys.argv[1:]!=['screen']:raise ValueError('Use screen; completion producer follows saved adaptive decisions')
    screen()
