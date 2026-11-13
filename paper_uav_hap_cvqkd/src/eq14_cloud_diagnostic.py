"""Torch-free wiring of preserved Eq14 numeric functions, not new physics.

The historical CLI imports Torch through unrelated source constructors. Execute
only explicitly named existing numeric function definitions; never load a blocked
DLL, alter application-control policy, substitute Torch, or rewrite equations.
"""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.special import log_ndtr,logsumexp,roots_hermitenorm

ROOT=Path(__file__).resolve().parents[1]
EXECUTED={}


def definitions(path,names,namespace):
    p=ROOT/path
    tree=ast.parse(p.read_text(encoding='utf-8-sig'))
    selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    if {n.name for n in selected}!=set(names):raise ValueError('Missing preserved function')
    EXECUTED[path]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),functions=list(names))
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(p),'exec'),namespace)
    return namespace


def primitives():
    M=lambda x:mp.mpf(str(x))
    common=dict(mp=mp,np=np,math=math,Path=Path,ROOT=ROOT,M=M,
                quad=quad,log_ndtr=log_ndtr,logsumexp=logsumexp,roots_hermitenorm=roots_hermitenorm)
    ch=definitions('results/skr_vs_zenith_angle_20261019/run_sweep.py',['channel_at_angle'],dict(common))
    opt=definitions('results/untrusted_positive_skr_feasibility_20261022/model.py',['optical'],
                    dict(common,channel_at_angle=ch['channel_at_angle'],_GEOMETRIES={}))
    h=definitions('results/manuscript43_homodyne_audit_20261023/audit_model.py',
        ['finite','marginal','homodyne_mi','independent_mi','raw_coefficients','raw_pdf_moments'],dict(common))
    h['legacy']=SimpleNamespace(optical=opt['optical'])
    model=definitions('results/skr_vs_zenith_eq14_v43_20261023/model.py',
        ['number','entropy_g','correlation_eq14','components','moment_check'],dict(common,POLICY='manuscript_eq14_direct',helpers=lambda:SimpleNamespace(**h)))
    return opt,h,model


def load_sources():
    pool=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/source_pool.csv'
    with pool.open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    archive=ROOT/'results/skr_vs_zenith_angle_20261019/verified_ensembles.npz'
    data=np.load(archive,allow_pickle=False)
    pmfs={hashlib.sha256(data[k].tobytes()).hexdigest():data[k] for k in data.files if k.endswith('_p')}
    sources=[];missing=[]
    for row in rows:
        identity=row['ensemble_hash'];payload=ROOT/row['source_path']
        if hashlib.sha256(payload.read_bytes()).hexdigest()!=row['source_sha256']:raise ValueError('Source hash changed')
        numeric=dict(row,VA=float.fromhex(row['VA_hex']),nu_raw=float.fromhex(row['nu_raw_hex']),C=float(row['C']),w=float(row['w']))
        digests=json.loads(row['input_digests_json'])
        if identity+'_p' not in data:
            p=pmfs.get(digests['pmf_sha256'])
            alpha=recover_exact_amplitudes(p,numeric['VA'],digests['amplitude_sha256']) if p is not None else None
            if alpha is None:missing.append(numeric);continue
        else:p,alpha=data[identity+'_p'],data[identity+'_alpha']
        if (hashlib.sha256(p.tobytes()).hexdigest()!=digests['pmf_sha256'] or
            hashlib.sha256(alpha.tobytes()).hexdigest()!=digests['amplitude_sha256']):raise ValueError('Archived array mismatch')
        source=dict(row,p=p,alpha=alpha,VA=float.fromhex(row['VA_hex']),
            nu_raw=float.fromhex(row['nu_raw_hex']),C=float(row['C']),w=float(row['w']))
        if abs(2*np.dot(p,abs(alpha)**2)-source['VA'])>2e-12:raise ValueError('Source normalization')
        sources.append(source)
    return sources,missing


def recover_exact_amplitudes(p,va,target_sha):
    """Recover existing binary inputs, accepted ONLY by their original digest.

    PMF bytes are already archived. Enumerate rounding of the known scalar
    normalization, never source parameters or C,w. A mismatch is unavailable.
    """
    def nearby(x):
        yield x
        for direction in [-np.inf,np.inf]:
            y=x
            for _ in range(12):y=np.nextafter(y,direction);yield y
    levels=np.arange(16)-7.5
    points=(levels[:,None]+1j*levels[None,:]).ravel()/math.sqrt(30)
    for divisor in nearby(math.sqrt(np.mean(abs(points)**2))):
        for base in [points/divisor,points*(1/divisor)]:
            for scale in nearby(math.sqrt(va/(2*np.dot(p,abs(base)**2)))):
                a=base*scale
                if hashlib.sha256(a.tobytes()).hexdigest()==target_sha:return a
    return None


class Eq14Diagnostic:
    def __init__(self):
        self.opt,self.h,self.model=primitives()
        self.sources,self.missing=load_sources()
        self.protocol=json.loads((ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/protocol.json').read_text())
        self.contexts={};self.calls=0

    def context(self,angle):
        if angle not in self.contexts:
            with mp.workdps(110):
                ch=self.opt['optical'](.30,35.,float(angle),.10,mp.mpf('1.561')/mp.mpf('15.61'))
                moments=self.h['raw_pdf_moments'](ch,0.)
                precision=[self.model['moment_check'](ch,.0186,.005,n) for n in [80,110]]
            if max(abs(x['residual']) for x in moments['direct'].values())>2e-10:raise ValueError('Channel quadrature failed')
            if max(abs(precision[0][k]-precision[1][k]) for k in ['m1','mh','M0'])>2e-11:raise ValueError('Channel precision failed')
            self.contexts[angle]=dict(angle=float(angle),moments=moments)
        return self.contexts[angle]

    def evaluate(self,source,context,A):
        m=context['moments'];s=10**(-float(A)/10)
        m1,mh=s*m['m1'],math.sqrt(s)*m['mh'];t=mh*mh
        noise=(m1-t)*source['VA']+.0186*m1+.005*m['M0']
        high=self.model['components'](source['VA'],t,noise/t,source['C'],source['w'],digits=110)
        low=self.model['components'](source['VA'],t,noise/t,source['C'],source['w'],digits=80)
        if abs(high['chi_BE']-low['chi_BE'])>2e-11:raise ValueError('Holevo precision disagreement')
        mi64,mi=[self.h['homodyne_mi'](source['p'],source['alpha'],t,1+noise,order=o) for o in [64,128]]
        if abs(mi-mi64)>2e-10:raise ValueError('MI quadrature disagreement')
        self.calls+=1
        return dict(A_db=float(A),K_raw=.95*mi-high['chi_BE'],I_AB=mi,chi_BE=high['chi_BE'],
            VA=source['VA'],nu_raw=source['nu_raw'],ensemble_hash=source['ensemble_hash'],
            source_evidence_class=source['source_evidence_class'],t=t,N_effective=noise,
            MI_difference=abs(mi-mi64),security_valid=False)


class BatchedEq14:
    """Vectorized evaluation of the SAME discrete MI and Eq13/14 expressions.

    This is a numerical accelerator only. Canonical preserved functions must
    validate its outputs before use and independently validate selected roots.
    """
    def __init__(self,sources,*,bounds_only=False):
        self.sources=sources
        self.va=np.array([s['VA'] for s in sources]);self.c=np.array([s['C'] for s in sources]);self.w=np.array([s['w'] for s in sources])
        if bounds_only:return
        levels=[];probs=[]
        for s in sources:
            x,inv=np.unique(2*s['alpha'].real,return_inverse=True)
            if len(x)!=16:raise ValueError('Expected 16 real homodyne levels')
            levels.append(x);probs.append(np.bincount(inv,weights=s['p']))
        self.levels=np.array(levels);self.p=np.array(probs)
        self.quadrature={}
        for o in [64,128]:
            n,w=roots_hermitenorm(o);self.quadrature[o]=(n,w/math.sqrt(2*math.pi))

    def covariance(self,context,A):
        m=context['moments'];s=10**(-float(A)/10);t=s*m['mh']**2
        noise=s*((m['m1']-m['mh']**2)*self.va+.0186*m['m1'])+.005*m['M0']
        z=2*math.sqrt(t)*self.c-np.sqrt(2*noise*self.w)
        v=1+self.va;w=1+t*self.va+noise
        delta=v*v+w*w-2*z*z;det=(v*w-z*z)**2
        disc=delta*delta-4*det
        if np.any(disc<0):raise ValueError('Negative covariance discriminant; no repair')
        roots=np.array([(delta+np.sqrt(disc))/2,(delta-np.sqrt(disc))/2,v*(v-z*z/w)])
        if np.any(roots<1):raise ValueError('Nonphysical candidate spectrum; no repair')
        nu=np.sqrt(roots);x=(nu-1)/2
        from scipy.special import xlogy
        g=(xlogy(x+1,x+1)-xlogy(x,x))/math.log(2)
        chi=g[0]+g[1]-g[2]
        return t,noise,chi

    def upper_bounds(self,context,A):
        t,noise,chi=self.covariance(context,A)
        # Classical AWGN capacity is only a screening upper bound on discrete MI;
        # reported SKR always comes from the unchanged canonical discrete MI.
        return .95*.5*np.log1p(t*self.va/(1+noise))/math.log(2)-chi

    def evaluate(self,context,A):
        t,noise,chi=self.covariance(context,A)
        means=math.sqrt(t)*self.levels;sigma=np.sqrt(1+noise)
        mi=[]
        for order in [64,128]:
            nodes,weights=self.quadrature[order]
            difference=(means[:,:,None,None]-means[:,None,None,:])/sigma[:,None,None,None]
            difference=difference+nodes[None,None,:,None]
            mixture=logsumexp(np.log(self.p)[:,None,None,:]-.5*difference**2,axis=-1)
            info=-.5*nodes[None,None,:]**2-mixture
            mi.append(np.sum(self.p*np.sum(info*weights[None,None,:],axis=-1),axis=-1)/math.log(2))
        error=abs(mi[0]-mi[1])
        if np.any(error>2e-10):raise ValueError('Batched discrete MI failed GH64/128 refinement')
        raw=.95*mi[1]-chi
        if not np.isfinite(raw).all():raise ValueError('Nonfinite raw rate')
        return dict(K_raw=raw,I_AB=mi[1],chi_BE=chi,MI_difference=error)


def catalog_maximum(model,batch,context,A,tolerance=1e-10):
    """Same finite-source maximum, screened by an MI upper bound, no C,w fits."""
    bounds=batch.upper_bounds(context,A)+1e-11
    order=np.argsort(-bounds);best=None;evaluated=0
    for i in order:
        if best is not None and bounds[i]<=best['K_raw']+tolerance:break
        row=model.evaluate(model.sources[i],context,A);evaluated+=1
        if best is None or row['K_raw']>best['K_raw']:best=row
    remaining=max([bounds[i] for i in order[evaluated:]],default=best['K_raw'])
    if model.missing:
        if not hasattr(model,'missing_bounds'):model.missing_bounds=BatchedEq14(model.missing,bounds_only=True)
        unavailable_bound=float(np.max(model.missing_bounds.upper_bounds(context,A)))+1e-11
        if unavailable_bound>best['K_raw']+tolerance and unavailable_bound>=0:
            raise ValueError('An unarchived source can still beat the selected candidate; catalog maximum unresolved')
        remaining=max(remaining,unavailable_bound)
    return dict(best,candidates_evaluated=evaluated,candidates_available=len(order),
                unavailable_sources_excluded_by_upper_bound=len(model.missing),
                catalog_size=len(order)+len(model.missing),
                catalog_maximum_resolved=bool(remaining<=best['K_raw']+tolerance),
                catalog_K_upper=max(float(remaining),best['K_raw']),
                catalog_upper_gap=max(0.,float(remaining-best['K_raw'])),
                selection_scope='HASH_MATCHED_ARCHIVED_SOURCE_CATALOG_ONLY')
