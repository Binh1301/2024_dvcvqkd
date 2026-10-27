"""61-angle homodyne-v43 diagnostic; exhaustive unchanged exact-source catalog."""
import csv
from datetime import datetime,timezone
import importlib.util
import inspect
import json
import math
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
AUDIT=ROOT/'results/manuscript43_homodyne_audit_20261023'
sys.path.insert(0,str(AUDIT))
import audit_model as a
import run_audit as r
from compare import independent_entropy
import numpy as np
from scipy.integrate import quad

spec=importlib.util.spec_from_file_location('_preserved_receiver30_literal',
    AUDIT/'receiver30_configuration_verification_20261023/inspect_receiver30.py')
literal=importlib.util.module_from_spec(spec);spec.loader.exec_module(literal)
SCHEMES=['Optimized Uniform 256-QAM','Fixed MB-shaped 256-QAM','Optimized MB-shaped 256-QAM']
OMEGA=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path,data):
    path.write_text(json.dumps(r.clean(data),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def write(path,rows):
    fields=list(dict.fromkeys(k for x in rows for k in x))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(r.clean(rows))


def covariance(value,va):
    aa=1+va;bb=1+value['eta_f']*va+value['N_effective'];z=value['Z_worst']
    gamma=np.array([[aa,0,z,0],[0,aa,0,-z],[z,0,bb,0],[0,-z,0,bb]])
    minimum=float(np.linalg.eigvalsh(gamma+1j*OMEGA).min())
    eigen=np.sort(abs(np.linalg.eigvals(1j*OMEGA@gamma)))[::2]
    error=float(max(abs(eigen-np.sort([value['nu_1'],value['nu_2']]))))
    if minimum < -1e-11 or error > 1e-10 or min(value[k] for k in ['nu_1','nu_2','nu_3'])<1:
        raise ValueError('Invalid independent quantum covariance/spectrum; no repair')
    return dict(a=aa,b=bb,uncertainty_min_eigenvalue=minimum,matrix_spectrum_residual=error)


def evaluate(c,raw):
    result=literal.literal_model_B(c,raw,.005,1e-10)
    if result['I_AB'] is None:raise ValueError('Channel normalization gate prevents candidate evaluation')
    _,px=a.marginal(c['p'],c['alpha'])
    entropy=-float(px@np.log2(px))
    capacity=.5*math.log2(1+result['eta_f']*c['VA']/result['sigma2_MI'])
    if (not all(math.isfinite(result[k]) for k in ['I_AB','chi_BE','K_raw'])
        or result['I_AB'] < -2e-12 or result['I_AB']>min(entropy,capacity)+2e-10 or result['chi_BE']<0):
        raise ValueError('Invalid discrete homodyne MI/Holevo domain')
    return {**result,**covariance(result,c['VA']),**{k:c[k] for k in [
        'family','VA','nu_raw','ensemble_hash','source_path','source_sha256','C','w']},
        'quadrature_entropy':entropy,'Gaussian_capacity_reference':capacity}


def selected_checks(c,value,raw):
    records=[]
    def check(name,ok,**detail):
        records.append(dict(check=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED',**detail))
    p,alpha=a.validate_source(c);t=value['eta_f'];variance=value['sigma2_MI']
    i64=a.homodyne_mi(p,alpha,t,variance,order=64)
    separate,error=a.independent_mi(p,alpha,t,variance)
    check('MI_GH64_128',abs(i64-value['I_AB'])<2e-10,coarse=i64,fine=value['I_AB'])
    check('MI_independent_adaptive',abs(separate-value['I_AB'])<2e-10 and error<2e-10,MI=separate,error=error)
    i256=a.homodyne_mi(p,alpha,t,variance,order=128,grouped=False)
    ip=a.homodyne_mi(p,alpha,t,variance,order=128,axis='P')
    scaled=a.homodyne_mi(p,alpha,t,variance,order=128,scale=1.7)
    check('MI_256_equals_16',abs(i256-value['I_AB'])<2e-12,MI256=i256)
    check('MI_X_P_symmetry',abs(ip-value['I_AB'])<2e-12,MI_P=ip)
    check('MI_classical_scaling',abs(scaled-value['I_AB'])<2e-12,MI_scaled=scaled)
    center=2*math.sqrt(t)*c['C'];radius=math.sqrt(2*value['N_effective']*c['w'])
    coarse=a.legacy.full_holevo(value['a'],value['b'],center,radius,33)
    check('Holevo_full_Z33_129',abs(coarse['chi_BE']-value['chi_BE'])<2e-8,
        chi33=coarse['chi_BE'],chi129=value['chi_BE'])
    for digits in [80,110]:
        entropy=independent_entropy(value,digits)
        check('Holevo_independent_entropy_'+str(digits),abs(entropy-value['chi_BE'])<2e-11,chi=entropy)
    masses=[]
    for level in np.unique(2*alpha.real):
        mean=math.sqrt(t)*level
        mass,err=quad(lambda y:a.conditional_pdf(y,mean,variance),-math.inf,math.inf,epsabs=1e-12,epsrel=1e-12)
        masses.append(dict(X=float(level),mass=mass,error=err))
    check('All_16_conditional_PDFs_normalized',all(abs(x['mass']-1)<2e-10 and x['error']<2e-10 for x in masses),
        max_mass_residual=max(abs(x['mass']-1) for x in masses),max_error=max(x['error'] for x in masses))
    check('Physical_covariance_and_spectrum',value['uncertainty_min_eigenvalue']>=-1e-11
        and value['matrix_spectrum_residual']<1e-10,
        minimum=value['uncertainty_min_eigenvalue'],spectrum_residual=value['matrix_spectrum_residual'])
    check('Same_v43_effective_quantum_channel',
        value['T_Holevo']==t and abs(value['b']-(1+t*c['VA']+value['N_effective']))<1e-14
        and value['xi_det']==.005 and 'eta_det' not in value)
    check('Raw_SKR_unclipped',abs(value['K_raw']-(.95*value['I_AB']-value['chi_BE']))<1e-14)
    return dict(status='CURRENTLY_VERIFIED_PASS' if all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in records) else 'FAILED',
        checks=records,conditional_masses=masses,source_hash=c['ensemble_hash'])


def row(angle,scheme,ch,raw,c,value,verification,reason):
    va=None if c is None else c['VA']
    tf=raw['mh']**2;mn=.0186*raw['m1']+.005*raw['M0']
    noise=None if va is None else (raw['m1']-tf)*va+mn
    numerical=value is not None and verification is not None and verification['status']=='CURRENTLY_VERIFIED_PASS'
    positive=numerical and value['K_raw']>0
    if numerical and not positive:reason='NON_POSITIVE_RAW_SKR'
    return dict(zenith_deg=angle,scheme=scheme,slant_distance_km=ch['L_km'],
        Dr_m=.30,divergence_urad=35.,jitter_urad=1.561,xi_det=.005,xi_ch=.0186,
        V_mod_or_VA=va,nu_raw=None if c is None else c['nu_raw'],
        E_eta=raw['m1'],E_sqrt_eta=raw['mh'],eta_f=tf,E_eta_xi=mn,
        xi_f=None if noise is None else noise/tf,
        I_AB=None if value is None else value['I_AB'],
        beta_I_AB=None if value is None else value['beta_I_AB'],
        chi_BE=None if value is None else value['chi_BE'],
        SKR=None if value is None else value['K_raw'],
        valid_point=positive,exclusion_reason='' if positive else reason,
        numerically_valid=numerical,plot_point=positive,
        M0=raw['M0'],PDF_mass_decimal=raw['M0_decimal'],
        mass_deficit=raw['raw_upper_tail_mass'],mass_deficit_decimal=raw['upper_tail_decimal'],
        PDF_normalization_status='CURRENTLY_VERIFIED_PASS' if raw['normalized_within_tolerance'] else 'FAILED',
        conditional_noise_variance=None if noise is None else 1+noise,
        quantum_transmittance=tf,source_hash=None if c is None else c['ensemble_hash'],
        C=None if c is None else c['C'],w=None if c is None else c['w'],
        source_path=None if c is None else c['source_path'],source_sha256=None if c is None else c['source_sha256'],
        optimization_scope='FIXED_SOURCE' if scheme==SCHEMES[1] else 'BEST_VALID_EXACT_CATALOG_POINT_ONLY',
        source_search_status='EVALUATED' if value is not None else 'NOT_RUN_OR_NO_VALID_CANDIDATE',
        sigma_h_m=.1,w0_m=ch['w0_m'],wL_m=ch['wL_m'],w_eff_m=ch['w_eff_m'],
        w_eq_m=ch['w_eq_m'],G_d=ch['G_d'],eta_atm=ch['eta_atm'],tau_zen=.92,
        sigma_s_m=ch['sigma_s_m'],Rytov_variance=float(ch['v']),P0=raw['P0'],
        nu_1=None if value is None else value['nu_1'],nu_2=None if value is None else value['nu_2'],
        nu_3=None if value is None else value['nu_3'],
        uncertainty_min_eigenvalue=None if value is None else value['uncertainty_min_eigenvalue'],
        matrix_spectrum_residual=None if value is None else value['matrix_spectrum_residual'],
        validation_status='NOT_RUN' if verification is None else verification['status'],
        channel_law=raw['law'],measurement='homodyne_1D_Gaussian_effective',security_valid=False)


def intervals(values):
    output=[]
    for n in values:
        if output and n==output[-1][1]+1:output[-1][1]=n
        else:output.append([n,n])
    return output


def aggregate(protocol):
    data=[read(OUT/'angles'/f'angle_{n:03d}.json') for n in protocol['angles_deg']]
    rows=[x for block in data for x in block['selected_rows']]
    write(OUT/'skr_vs_zenith.csv',rows)
    source=read(OUT/'source_catalog_receipt.json')
    schemes={}
    for label in SCHEMES:
        values=[x for x in rows if x['scheme']==label]
        numeric=[x for x in values if x['numerically_valid']]
        positive=[x['zenith_deg'] for x in values if x['valid_point']]
        best=max(numeric,key=lambda x:x['SKR']) if numeric else None
        schemes[label]=dict(numerically_valid_angles=len(numeric),positive_angles=positive,
            positive_intervals_deg=intervals(positive),excluded_angles=[x['zenith_deg'] for x in values if not x['valid_point']],
            maximum_raw_SKR=None if best is None else best['SKR'],
            maximum_angle_deg=None if best is None else best['zenith_deg'],
            maximum_source=None if best is None else {k:best[k] for k in ['V_mod_or_VA','nu_raw','source_hash']})
    winners={s:0 for s in SCHEMES};ties=0
    for angle in protocol['angles_deg']:
        evaluated=[x for x in rows if x['zenith_deg']==angle and x['numerically_valid']]
        if not evaluated:continue
        top=max(x['SKR'] for x in evaluated);best=[x for x in evaluated if abs(x['SKR']-top)<2e-12]
        if len(best)>1:ties+=1
        for value in best:winners[value['scheme']]+=1
    summary=dict(status='COMPLETED_DIAGNOSTIC_WITH_EXCLUSIONS',schemes=schemes,
        PDF_failed_angles=[x['zenith_deg'] for x in data if not x['raw_PDF']['normalized_within_tolerance']],
        candidate_evaluations=sum(len(x['candidates'])+len(x['candidate_failures']) for x in data),
        candidate_failures=sum(len(x['candidate_failures']) for x in data),source_counts=source['counts'],
        selected_rows=len(rows),positive_plotted_points=sum(x['valid_point'] for x in rows),
        selected_numerical_failures=sum(x['validation_status']=='FAILED' for x in rows),
        per_angle_best_counts_including_ties=winners,tied_angles=ties,
        security_valid=False,optimization_domain='Finite existing exact catalog; no interpolation/new source AP',
        recommended_secure_default=None)
    save(OUT/'summary.json',summary)
    save(OUT/'sweep_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',angles=len(data),rows=len(rows),
        producer_sha256=a.sha(Path(__file__)),protocol_sha256=a.sha(OUT/'protocol.json'),
        summary_sha256=a.sha(OUT/'summary.json'),CSV_sha256=a.sha(OUT/'skr_vs_zenith.csv'),
        scientific_PDF_failures=summary['PDF_failed_angles'],new_source_AP=False,optimization_is_catalog_only=True))


def main():
    if (OUT/'sweep_receipt.json').exists():raise FileExistsError('Preserve completed sweep')
    protocol=read(OUT/'protocol.json')
    assert a.sha(Path(__file__))==protocol['implementation_sha256']['run_sweep.py']
    assert 'eta_det' not in inspect.signature(literal.literal_model_B).parameters
    catalog=r.catalog()
    fixed=next(c for c in catalog if c['ensemble_hash']==protocol['fixed_MB']['ensemble_hash'])
    for c in catalog:a.validate_source(c)
    source_rows=[{**{k:c[k] for k in ['family','VA','nu_raw','ensemble_hash','C','w','source_path','source_sha256']},
        'normalization':'VA=2*nbar','nu_repo':42.5*c['nu_raw'],'source_changed':False} for c in catalog]
    write(OUT/'source_catalog.csv',source_rows)
    save(OUT/'source_catalog_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',
        counts={f:sum(c['family']==f for c in catalog) for f in ['Uniform','MB']},sources=len(catalog),
        all_source_payloads_authenticated=True,source_C_w_recomputed=False,interpolation=False,
        fixed_source_hash=fixed['ensemble_hash']))
    (OUT/'angles').mkdir(exist_ok=True)
    started=datetime.now(timezone.utc).isoformat()
    for angle in protocol['angles_deg']:
        path=OUT/'angles'/f'angle_{angle:03d}.json'
        if path.exists():
            saved=read(path)
            assert saved['producer_sha256']==a.sha(Path(__file__)) and saved['protocol_sha256']==a.sha(OUT/'protocol.json')
            print('EXACT CHECKPOINT REUSE',angle,flush=True);continue
        ch=a.legacy.optical(.3,35.,angle,.1,.1)
        raw=a.raw_pdf_moments(ch)
        if max(abs(x['residual']) for x in raw['direct'].values())>2e-10:
            raise ValueError('Raw PDF closed/direct moments disagree')
        if not 0<=raw['mh']**2<=raw['m1']<=1:raise ValueError('Invalid bounded moments')
        if angle==0:
            previous=read(AUDIT/'receiver30_configuration_verification_20261023/results.json')['model_B_PDF']
            assert abs(raw['raw_upper_tail_mass']-previous['raw_upper_tail_mass'])<1e-20
        candidates=[];failures=[];selected=[];validation={}
        byhash={c['ensemble_hash']:c for c in catalog}
        if not raw['normalized_within_tolerance']:
            for label in SCHEMES:selected.append(row(angle,label,ch,raw,fixed if label==SCHEMES[1] else None,
                None,None,'FAILED_CHANNEL_PDF_NORMALIZATION'))
        else:
            for c in catalog:
                try:candidates.append(evaluate(c,raw))
                except ValueError as error:failures.append(dict(source_hash=c['ensemble_hash'],family=c['family'],
                    VA=c['VA'],nu_raw=c['nu_raw'],status='FAILED',reason=str(error)))
            chosen=[]
            for label,family in [(SCHEMES[0],'Uniform'),(SCHEMES[1],'MB'),(SCHEMES[2],'MB')]:
                admissible=[v for v in candidates if v['family']==family and
                    (label!=SCHEMES[1] or v['ensemble_hash']==fixed['ensemble_hash'])]
                best=min(admissible,key=lambda v:(-v['K_raw'],v['nu_raw'],v['VA'],v['ensemble_hash'])) if admissible else None
                chosen.append((label,best))
            for label,best in chosen:
                if best is None:
                    selected.append(row(angle,label,ch,raw,fixed if label==SCHEMES[1] else None,None,None,'NO_VALID_EXACT_SOURCE_CANDIDATE'))
                    continue
                identity=best['ensemble_hash'];c=byhash[identity]
                if identity not in validation:validation[identity]=selected_checks(c,best,raw)
                result=validation[identity]
                selected.append(row(angle,label,ch,raw,c,best,result,
                    '' if result['status']=='CURRENTLY_VERIFIED_PASS' else 'FAILED_SELECTED_NUMERICAL_CHECKS'))
            mb=[x for x in selected if x['scheme']==SCHEMES[2] and x['numerically_valid']]
            fixed_rows=[x for x in selected if x['scheme']==SCHEMES[1] and x['numerically_valid']]
            if mb and fixed_rows:assert mb[0]['SKR']>=fixed_rows[0]['SKR']-2e-12
        save(path,dict(zenith_deg=angle,producer_sha256=a.sha(Path(__file__)),
            protocol_sha256=a.sha(OUT/'protocol.json'),channel=ch,raw_PDF=raw,candidates=candidates,
            candidate_failures=failures,selected_rows=selected,selected_checks=validation))
        print('ANGLE',angle,'Lkm',round(ch['L_km'],5),'mass deficit',raw['raw_upper_tail_mass'],
            'positive',sum(x['valid_point'] for x in selected),'candidates',len(candidates),'failed',len(failures),flush=True)
    aggregate(protocol)
    save(OUT/'execution_history.json',dict(started_UTC=started,completed_UTC=datetime.now(timezone.utc).isoformat(),
        numerical_producer_sha256=a.sha(Path(__file__)),protocol_sha256=a.sha(OUT/'protocol.json'),
        shared_model='Preserved receiver30 literal_model_B; no detector efficiency',
        source_generation=False,source_interpolation=False,optimization='Finite source catalog only at61angles',
        training_final_test_heldout_publication=False,security_valid=False))
    print('SWEEP COMPLETE',read(OUT/'summary.json')['positive_plotted_points'],'positive plotted points',flush=True)


if __name__=='__main__':main()
