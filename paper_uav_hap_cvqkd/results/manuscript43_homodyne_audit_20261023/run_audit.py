"""Fresh preserved regressions -> audit tests/findings -> focused corrected comparisons."""
import copy
import csv
from functools import lru_cache
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import FunctionType
import unittest

import mpmath as mp
import numpy as np
from scipy.integrate import quad
import audit_model as a

OUT, ROOT = a.OUT, a.ROOT


def clean(x):
    if isinstance(x, dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)):return [clean(v) for v in x]
    if isinstance(x, np.ndarray):return x.tolist()
    if isinstance(x, np.generic):return x.item()
    if isinstance(x, mp.mpf):return float(x)
    return x


def save(name, value):
    (OUT/name).write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write(name, rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(clean(rows))


def csvrows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


@lru_cache(1)
def catalog():
    start=a.read(OUT/'startup_manifest.json')
    for p in ['src/manuscript_mobility.py','src/manuscript_literal_3moments.py',
              'results/untrusted_positive_skr_feasibility_20261022/model.py',
              'results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py']:
        assert a.sha(ROOT/p)==start['protected']['paper_uav_hap_cvqkd/'+p]
    return a.legacy.load_catalog(a.read(ROOT/'configs/manuscript_mobility.json'))


def source(r):return next(c for c in catalog() if c['ensemble_hash']==r['ensemble_hash'])


@lru_cache(1)
def adapter():
    spec=importlib.util.spec_from_file_location('_v43_preserved_aperture_adapter',
        ROOT/'results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def parameters(r):
    return (20.,1.,float(r['zenith_deg']),float(r['divergence_urad']),float(r['jitter_urad']),
        float(r['sigma_h_m']),float(r['eta_det']),float(r['epsilon_det']),.92,float(r['D_r']))


def raw_channel(p):
    return a.legacy.optical(p[9],p[3],p[2],p[5],mp.mpf(str(p[4]))/mp.mpf('15.61'))


def references():
    latest=ROOT/'results/uav_skwap_aware_positive_skr_20261022'
    refs=[dict(label=x['label'],saved=x['result']) for x in a.read(latest/'regression.json')['records']]
    sel=a.read(latest/'selection.json')['recommendations']
    refs += [dict(label='receiver28p1',saved=sel[0]),dict(label='receiver30',saved=sel[2])]
    rows=csvrows(latest/'aperture_best_exact_tested.csv')
    for diameter in [.15,.20,.25]:
        candidates=[r for r in rows if float(r['D_r'])==diameter]
        refs.append(dict(label=f'receiver{diameter*100:g}',saved=max(candidates,key=lambda r:float(r['K_raw']))))
    return refs


def regress():
    if (OUT/'historical_regressions.json').exists():raise FileExistsError('Preserve completed regressions')
    records=[]
    for item in references():
        old=item['saved'];c=source(old);p=parameters(old)
        now=adapter().evaluate(c,p,int(old['radial_order']),int(old['width_order']))
        delta={k:now[k]-float(old[k]) for k in ['m1','mh','I_AB','chi_BE','K_raw']}
        assert max(abs(v) for v in delta.values())<5e-12,(item['label'],delta)
        records.append(dict(label=item['label'],status='CURRENTLY_VERIFIED_PASS',saved=old,fresh=now,differences=delta,
            producer='preserved_parameter_adapter_same_orders',source_sha256=c['source_sha256']))
        print('LEGACY MATCH',item['label'],now['K_raw'],flush=True)
    from scripts import run_corrected_excess_noise_trial as trial
    from scripts.recheck_manuscript_homodyne_noise import channel, mi_gh
    c=next(c for c in catalog() if c['family']=='MB' and c['nu_raw']==.165 and c['VA']==5.475)
    def guard(name,ok,detail=None):
        if not ok:raise ValueError((name,detail))
    original_check=trial.covariance.__globals__['check']
    covariance=FunctionType(trial.covariance.__code__,{**trial.covariance.__globals__,'check':guard},
        trial.covariance.__name__,trial.covariance.__defaults__)
    with mp.workdps(110):
        ch=channel();eta=mp.mpf('.8');va=mp.mpf('5.475')
        tf=ch['mean_sqrt_eta']**2;noise=eta*((ch['mean_eta']-tf)*va+mp.mpf('.0186')*ch['mean_eta'])+mp.mpf('.0135')
        h=covariance(va,mp.sqrt(eta)*ch['mean_sqrt_eta'],eta*tf,noise,mp.mpf(str(c['C'])),mp.mpf(str(c['w'])),'homodyne')
        x,px=a.legacy.source_factors(c)
        i=mi_gh(px,x.astype(complex),float(eta*tf),float(noise),64,dimension=1)
        now=dict(I_AB=i,chi_BE=float(h['chi_BE']),K_raw=.95*i-float(h['chi_BE']))
    expected=a.read(ROOT/'results/corrected_excess_noise_trial_20261022/result.json')['results'][0]
    delta={k:now[k]-float(expected[k]) for k in now}
    assert max(abs(v) for v in delta.values())<5e-12
    assert trial.covariance.__globals__['check'] is original_check
    records.append(dict(label='original_manuscript_trial8',status='CURRENTLY_VERIFIED_PASS',saved=expected,fresh=now,differences=delta,
        producer='identical_preserved_covariance_bytecode_no_old_file_writes',source_sha256=c['source_sha256']))
    save('historical_regressions.json',dict(status='CURRENTLY_VERIFIED_PASS',records=records,new_source_moments=False))
    print('HISTORICAL REGRESSIONS COMPLETE',len(records),flush=True)


def validation():
    if (OUT/'validation.json').exists():raise FileExistsError('Preserve completed validation')
    assert a.read(OUT/'historical_regressions.json')['status']=='CURRENTLY_VERIFIED_PASS'
    suite=unittest.defaultTestLoader.discover(str(OUT),pattern='test_audit_model.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    save('unit_tests.json',dict(status='CURRENTLY_VERIFIED_PASS' if result.wasSuccessful() else 'FAILED',tests=result.testsRun,
        failures=[dict(test=str(t),traceback=s) for t,s in result.failures],errors=[dict(test=str(t),traceback=s) for t,s in result.errors]))
    if not result.wasSuccessful():raise AssertionError('Unit tests failed; corrected comparisons blocked')
    source_rows=[]
    for c in catalog():
        p,alpha=a.validate_source(c);x=2*alpha.real;y=2*alpha.imag
        nbar=float(p@abs(alpha)**2);mean=float(p@x);second=float(p@x**2)
        row={k:c[k] for k in ['family','nu_raw','VA','C','w','ensemble_hash','source_path','source_sha256']}
        row.update(nbar=nbar,mean_alpha_real=float((p@alpha).real),mean_alpha_imag=float((p@alpha).imag),
            mean_X=mean,second_X=second,variance_X=second-mean**2,variance_P=float(p@y**2-(p@y)**2),
            PMF_sum=float(p.sum()),repo_VA_identity_residual=2*nbar-c['VA'],manuscript_nbar_over2=nbar/2,
            manuscript_VA_factor=4.,raw_to_repo_nu=42.5*c['nu_raw'],cache_changed=False)
        assert abs(second-mean**2-c['VA'])<2e-12
        source_rows.append(row)
    write('source_normalization.csv',source_rows)
    contexts=[(r['label'],parameters(r['saved'])) for r in references()]
    pdf=[];mom=[]
    for label,p in contexts:
        ch=raw_channel(p)
        raw=a.raw_pdf_moments(ch)
        assert max(abs(r['residual']) for r in raw['direct'].values())<2e-10,(label,raw['direct'])
        assert abs(raw['upper_tail_quadrature']-(1-raw['M0']))<2e-10
        ordering=0<=raw['mh']**2<=raw['m1']<=1
        raw.update(context=label,parameters=p,geometry=a.read(OUT/'protocol.json')['scope'],moment_ordering=ordering,
            normalization_status='CURRENTLY_VERIFIED_PASS' if raw['normalized_within_tolerance'] else 'FAILED',
            root_cause='Lognormal gain has unbounded upper support; retaining eta<=1 discards probability without renormalizing')
        pdf.append(raw)
        for q,info in raw['direct'].items():mom.append(dict(context=label,power=q,**info))
        print('PDF',label,'M0',repr(raw['M0']),'tail',raw['raw_upper_tail_mass'],flush=True)
    save('channel_pdf_audit.json',dict(status='AUDIT_COMPLETE',contexts=pdf,normalization_failures=sum(not r['normalized_within_tolerance'] for r in pdf),silent_model_replacement=False))
    write('channel_moment_checks.csv',mom)
    conditionals=[];mi=[];cov=[]
    for c in [catalog()[0],next(c for c in catalog() if c['family']=='Uniform')]:
        p,alpha=a.validate_source(c);e=a.effective(dict(M0=1.,m1=.11,mh=.3,P0=.01,law='normalized_unit_fixture'),c['VA'],.8,.0135)
        for level in np.unique(2*alpha.real):
            mean=math.sqrt(e['T_quantum'])*level
            value,error=quad(lambda y:a.conditional_pdf(y,mean,e['sigma2_output']),-math.inf,math.inf,epsabs=1e-12,epsrel=1e-12)
            conditionals.append(dict(source_hash=c['ensemble_hash'],X=level,mean=mean,variance=e['sigma2_output'],mass=value,error=error))
        i64=a.homodyne_mi(p,alpha,e['T_quantum'],e['sigma2_output'],order=64)
        i128=a.homodyne_mi(p,alpha,e['T_quantum'],e['sigma2_output'],order=128)
        independent,error=a.independent_mi(p,alpha,e['T_quantum'],e['sigma2_output'])
        mi.append(dict(source_hash=c['ensemble_hash'],I_GH64=i64,I_GH128=i128,I_adaptive=independent,adaptive_error=error,
            I_256=a.homodyne_mi(p,alpha,e['T_quantum'],e['sigma2_output'],grouped=False),
            I_rescaled=a.homodyne_mi(p,alpha,e['T_quantum'],e['sigma2_output'],scale=1/math.sqrt(.8))))
        r=a.evaluate_physical(c,dict(M0=1.,m1=.11,mh=.3,P0=.01,law='normalized_unit_fixture'),.8,.0135)
        cov.append(r)
    write('conditional_pdf_normalization.csv',conditionals);write('MI_independent_checks.csv',mi);save('covariance_unit_checks.json',cov)
    save('validation.json',dict(status='CURRENTLY_VERIFIED_PASS',unit_tests=result.testsRun,source_checks=len(source_rows),
        PDF_contexts=len(pdf),PDF_normalization_failures=sum(not r['normalized_within_tolerance'] for r in pdf),
        PDF_equations_not_renormalized=True,model_scientifically_validated=False,recommended_secure_default=False))
    print('COMPONENT VALIDATION PASS; MODEL FINDINGS RETAINED',result.testsRun,flush=True)


if __name__=='__main__':
    {'regress':regress,'validate':validation}[sys.argv[1]]()
