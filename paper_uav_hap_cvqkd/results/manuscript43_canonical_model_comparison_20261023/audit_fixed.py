"""Focused, immutable-source audit; no search/controller/canonical promotion."""
import csv
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
AUDIT=ROOT/'results/manuscript43_homodyne_audit_20261023'
sys.path.insert(0,str(AUDIT))
import audit_model as a
import run_audit as r
import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.stats import ncx2,rice
from src.channel.pointing_error import manuscript_pointing_parameters
from src.channel.scintillation import hufnagel_valley_scintillation

spec=importlib.util.spec_from_file_location('_unchanged_uniform_v43',
    ROOT/'results/uniform_positive_skr_manuscript43_20261023/search.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(name,value):(OUT/name).write_text(json.dumps(r.clean(value),indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def write(name,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(r.clean(rows))


def optical(g):
    diameter,div,jitter,sigma,angle=g
    return a.legacy.optical(diameter,div,angle,sigma,mp.mpf(str(jitter))/mp.mpf('15.61'))


def bounded_moments(ch,order=32):
    m=a.legacy.power_conserving(ch,order)
    return dict(M0=m['physical_mass'],m1=m['m1'],mh=m['mh'],P0=m['P0'],
        normalized_within_tolerance=True,law=s.BOUNDED,raw_upper_tail_mass=0.,renormalized=False,
        clipped=False,continuous_mass=m['Pactive'],width_order=order,radial_error=m['radial_quadrature_error'])


def effective(m,va=3.):
    t=m['mh']**2;mn=.0186*m['m1']+.005*m['M0'];noise=(m['m1']-t)*va+mn
    return dict(E_eta=m['m1'],E_sqrt_eta=m['mh'],eta_f=t,E_eta_xi=mn,N_effective=noise,xi_f=noise/t)


def model_row(name,label,m,c,value):
    return dict(scenario=name,channel_model=label,
        manuscript_equivalent='REFERENCE_IDENTITY_PENDING' if label=='A_Eq10' else 'DIFFERENT',
        pdf_mass=m['M0'],mass_above_one=m['raw_upper_tail_mass'],P0=m['P0'],
        continuous_mass=m['M0']-m['P0'],full_positive_support_mass=1.,
        **effective(m),I_AB=None if value is None else value['I_AB'],
        beta_I_AB=None if value is None else value['beta_I_AB'],chi_BE=None if value is None else value['chi_BE'],
        raw_SKR=None if value is None else value['K_raw'],
        validation_status='BLOCKED_PDF_NORMALIZATION' if value is None else 'CURRENTLY_VERIFIED_PASS',
        difference_reason='Unbounded lognormal product retained on[0,1]; no repair' if label=='A_Eq10'
            else 'Random width coupled to scintillation; exact circular collection; B and C share the same implementation',
        source_hash=c['ensemble_hash'],source_path=c['source_path'],source_sha256=c['source_sha256'],
        VA=c['VA'],xi_ch=.0186,xi_det=.005,security_valid=False,requested_PDF_identity_verified=False)


def true_rician_moments(ch,rho):
    """Exact product of Eq5 and Eq8, with tail integrals after exponential tilting."""
    B,d,v,sigma,p0,p1=[float(ch[k]) for k in ['B','d','v','sigma_s_m','P0','P1']]
    lam=rho*rho/(sigma*sigma);root=math.sqrt(v)
    threshold=(-math.log(B)+v/2)/root
    result={};errors={}
    for q in [0.,.5,1.]:
        factor=d/(d+q)*math.exp(-lam*q/(2*(d+q)))
        full=p1*B**q*factor*math.exp(v*(q*q-q)/2)
        def above(z):
            y=-v/2+root*z
            boundary=2*(d+q)*(math.log(B)+y)
            return math.exp(-z*z/2+q*y)/math.sqrt(2*math.pi)*ncx2.cdf(boundary,2,lam*d/(d+q))
        tail,error=quad(above,threshold,math.inf,epsabs=2e-13,epsrel=2e-12,limit=400)
        tail*=p1*B**q*factor
        result[q]=dict(full=full,retained=full-tail,above_one_weighted=tail)
        errors[q]=error*p1*B**q*factor
        laplace,laplace_error=quad(lambda radial:rice.pdf(radial,rho/sigma,scale=sigma)
            *math.exp(-q*2*radial*radial/float(ch['w_eq_m'])**2),0,math.inf,epsabs=2e-13,epsrel=2e-12,limit=400)
        if abs(laplace-factor)>2e-10:raise ValueError('Independent Rice Laplace integration disagrees')
        result[q].update(Rice_Laplace_closed=factor,Rice_Laplace_direct=laplace,Rice_quad_error=laplace_error)
    if max(errors.values())>2e-10:raise ValueError('Rician tail quadrature failed')
    return dict(rho=rho,M0=p0+result[0.]['retained'],m1=result[1.]['retained'],mh=result[.5]['retained'],
        raw_upper_tail_mass=result[0.]['above_one_weighted'],moments=result,quadrature_errors=errors)


def rice_diagnostics(critical):
    rows=[]
    baseline=optical([.08,233.,15.61,1.,30.])
    for name,ch,rhos in [('critical',critical,[0.,.03,.1]),('manuscript_baseline',baseline,[0.,.5])]:
        for rho in rhos:
            raw=a.raw_pdf_moments(ch,rho);exact=true_rician_moments(ch,rho)
            B,d,v,sigma,p1=[float(ch[k]) for k in ['B','d','v','sigma_s_m','P1']]
            for q in [.5,1.]:
                cf=a.raw_coefficients(ch,rho)
                with mp.workdps(90):
                    aq=mp.mpf(str(q));dd=cf['d']
                    whole=cf['P1']*cf['B']**aq*dd/(dd+aq)*mp.exp(
                        cf['logC1']+(dd+aq)**2/(4*cf['C3']**2)-(dd+aq)*cf['mu'])
                exact_full=exact['moments'][q]['full']
                ratio=math.exp(rho*rho*q**3/(2*sigma*sigma*d*d*(d+q)))
                if abs(float(whole)/exact_full-ratio)>2e-10:raise ValueError('Nonzero-rho moment ratio identity failed')
                actual=raw['mh'] if q==.5 else raw['m1']
                target=exact['mh'] if q==.5 else exact['m1']
                if rho==0 and abs(actual-target)>2e-10:raise ValueError('Eq10/Rice rho0 mismatch')
                rows.append(dict(scenario=name,rho_m=rho,power=q,Eq10_full_moment=float(whole),
                    Rician_product_full_moment=exact_full,predicted_relative_ratio=ratio,
                    Eq10_retained_moment=actual,Rician_product_retained_moment=target,
                    retained_difference=actual-target,Eq10_pdf_mass=raw['M0'],Rician_pdf_mass=exact['M0'],
                    Eq10_upper_tail=raw['raw_upper_tail_mass'],Rician_upper_tail=exact['raw_upper_tail_mass'],
                    classification='EQUIVALENT_RHO0' if rho==0 else 'DIFFERENT_NONZERO_RHO',
                    Rice_Laplace_direct=exact['moments'][q]['Rice_Laplace_direct'],
                    Rice_Laplace_closed=exact['moments'][q]['Rice_Laplace_closed']))
    write('rician_comparison.csv',rows);save('rician_comparison.json',rows)


def optical_diagnostics(ch):
    prod=manuscript_pointing_parameters(.15,ch['w0_m'],1.55e-6,19000.,math.inf,1000.,20000.,0.,21.,1e-14)
    scint=hufnagel_valley_scintillation(1000.,20000.,1.55e-6,0.,21.,1e-14,.3)
    target_A0=float(ch['B'])/ch['eta_atm']
    save('production_optical_comparison.json',dict(
        reference='Available v43 Eq6; requested v43(2) not identified',
        production_nu=prod.nu,reference_nu=math.sqrt(math.pi)*.3/(2*math.sqrt(2)*ch['w_eff_m']),
        production_A0=prod.a0,reference_A0=target_A0,delta_A0=prod.a0-target_A0,
        production_w_eq=prod.omega_l_eq_m,reference_w_eq=ch['w_eq_m'],
        delta_w_eq=prod.omega_l_eq_m-ch['w_eq_m'],
        production_nu_uses_wL_not_wLeff=True,raw_Rytov=float(ch['v']),production_scintillation=scint,
        sigma_R2_residual=scint['sigma_R0_squared']-float(ch['v']),
        optional_finite_aperture_mapping_is_different_from_Eq5_v_equals_sigma_R2=True))


def moment_attribution(ch,raw,bounded):
    B,d,v,p0,p1=[float(ch[k]) for k in ['B','d','v','P0','P1']]
    full=lambda q:p1*B**q*d/(d+q)*math.exp(v*(q*q-q)/2)
    retained=raw['active_retained_mass']/p1
    conditional=dict(M0=1.,m1=raw['m1']/retained,mh=raw['mh']/retained,P0=p0)
    radius=ch['D_r']/2;width=ch['w_eff_m'];sigma=ch['sigma_s_m']
    def integral(q):
        return quad(lambda x:math.exp(-x)*ncx2.cdf((2*radius/width)**2,2,8*sigma*sigma*x/width**2)**q,
            0,math.inf,epsabs=2e-13,epsrel=2e-12,limit=400)[0]
    fixed=dict(M0=1.,m1=p1*ch['eta_atm']*integral(1.),
        mh=p1*math.sqrt(ch['eta_atm'])*math.exp(-v/8)*integral(.5),P0=p0)
    rows=[]
    for label,m,operation in [
        ('raw_Eq10_retained',raw,'Integration only on[0,1]; subprobability'),
        ('raw_active_conditioned_DIFFERENT',conditional,'Divide continuous law by retained ACTIVE probability; keep AoA atom'),
        ('raw_unbounded_MOMENT_REFERENCE',dict(M0=1.,m1=full(1.),mh=full(.5),P0=p0),'Integrate original product on(0,infinity); eta>1 remains'),
        ('fixed_width_exact_CDF_UNBOUNDED',fixed,'Only replace Eq6 equivalent-beam approximation by exact circular collection, independent lognormal gain'),
        ('random_width_exact_CDF',bounded,'Couple lognormal intensity to width; collect exact circular power per beam')]:
        rows.append(dict(channel_variant=label,pdf_mass=m['M0'],P0=m['P0'],**effective(m),
            operation=operation,raw_SKR=None,rate_reason='MOMENT_ONLY_ATTRIBUTION_NOT_A_CANONICAL_RATE'))
    write('moment_attribution.csv',rows);save('moment_attribution.json',rows)


def controlled(c,ch,m):
    reference=s.model(c,m,128,129)
    variants=[]
    def append(label,value,description,classification='DIFFERENT'):
        variants.append(dict(diagnostic=label,classification=classification,
            I_AB=value.get('I_AB'),chi_BE=value.get('chi_BE'),raw_SKR=value.get('K_raw'),
            delta_I_AB=None if value.get('I_AB') is None else value['I_AB']-reference['I_AB'],
            delta_chi_BE=None if value.get('chi_BE') is None else value['chi_BE']-reference['chi_BE'],
            delta_K=None if value.get('K_raw') is None else value['K_raw']-reference['K_raw'],
            source_hash=c['ensemble_hash'],description=description))
    append('canonical_noise_Gaussian_homodyne_reference',reference,'Same source and bounded channel; NOT canonical Eq10','REFERENCE')
    old=a.evaluate_physical(c,m,.95,.005,order=128,grid=129)
    append('historical_eta0.95_output_epsilon0.005',old,'Change detector convention only; explicit untrusted physical output, same source/channel')
    active_mn=.0186*m['m1']+.005*(m['M0']-m['P0'])
    n=(m['m1']-m['mh']**2)*c['VA']+active_mn
    h=a.legacy.full_holevo(1+c['VA'],1+reference['eta_f']*c['VA']+n,
        2*math.sqrt(reference['eta_f'])*c['C'],math.sqrt(2*n*c['w']),129)
    mi=a.homodyne_mi(c['p'],c['alpha'],reference['eta_f'],1+n,order=128)
    append('active_only_noise_at_outage',dict(I_AB=mi,chi_BE=h['chi_BE'],K_raw=.95*mi-h['chi_BE']),
        'Only eta*xi at outage changes from xi_det to zero; detector-noise moment delta=-xi_det*P0')
    scaled=a.homodyne_mi(c['p'],c['alpha'],reference['eta_f'],reference['sigma2_MI'],order=128,scale=.5)
    if abs(scaled-reference['I_AB'])>2e-12:raise ValueError('Classical scaling MI changed')
    append('invertible_classical_scaling_y_over2',dict(I_AB=scaled,chi_BE=reference['chi_BE'],K_raw=.95*scaled-reference['chi_BE']),
        'Scale means/noise consistently; quantum covariance/source unchanged','EQUIVALENT')
    direct=reference['chi_at_lower']
    append('Eq14_Zminus_if_unclipped',dict(I_AB=reference['I_AB'],chi_BE=direct,K_raw=.95*reference['I_AB']-direct),
        'Only compare when physical lower equals actual printed Zminus','EQUIVALENT_AT_THIS_FIXTURE')
    actual_lower=2*math.sqrt(reference['eta_f'])*c['C']-math.sqrt(2*reference['N_effective']*c['w'])
    if actual_lower!=reference['Z_lower']:raise ValueError('Direct-Zminus diagnostic would silently clip')
    append('literal_Vmod_nbar_over2_same_source',{},'NON-EQUIVALENT: VA3 source has nbar1.5, printed Vmod.75; cannot relabel covariance/source at fixed vacuum1','NON_EQUIVALENT')
    pooled=[]
    for radial,width in [(128,16),(256,32),(512,64)]:
        value=a.legacy.pooled_mi(c,ch,eta_det=1.,epsilon_det=.005,radial_order=radial,width_order=width)
        pooled.append(value)
        if len(pooled)>1 and abs(pooled[-1]['I_AB_pooled']-pooled[-2]['I_AB_pooled'])<2e-8:break
    converged=len(pooled)>1 and abs(pooled[-1]['I_AB_pooled']-pooled[-2]['I_AB_pooled'])<2e-8
    pmi=pooled[-1]['I_AB_pooled']
    append('pooled_fading_homodyne_MI_same_no_eta_detector',
        dict(I_AB=pmi,chi_BE=reference['chi_BE'],K_raw=.95*pmi-reference['chi_BE']) if converged else {},
        'Replace Gaussian effective likelihood by actual fading mixture only; hold source, moments and Holevo',
        'DIFFERENT' if converged else 'BLOCKED_NUMERICAL_PRECISION')
    save('pooled_MI_precision.json',dict(status='CURRENTLY_VERIFIED_PASS' if converged else 'BLOCKED_BY_NUMERICAL_PRECISION',
        records=pooled,reference_moments=m))
    save('controlled_comparisons.json',variants);write('controlled_comparisons.csv',variants)
    # Printed complex alpha on a real output has a non-unit conditional mass.
    masses=np.exp(-2*reference['eta_f']*c['alpha'].imag**2/reference['sigma2_MI'])
    save('literal_internal_consistency.json',dict(source_hash=c['ensemble_hash'],
        nbar=float(c['p']@abs(c['alpha'])**2),VA=c['VA'],literal_Vmod=float(c['p']@abs(c['alpha'])**2)/2,
        X_variance=float(c['p']@(2*c['alpha'].real)**2),vacuum_variance=1.,
        printed_conditional_mass_min=float(masses.min()),printed_conditional_mass_max=float(masses.max()),
        corrected_conditional_mass=1.,literal_rate_status='BLOCKED_LITERAL_LIKELIHOOD',
        source_moments_reusable_under_notation_correction=True))


def main():
    if (OUT/'numerical_receipt.json').exists():raise FileExistsError('Preserve completed fixed checks')
    protocol=read(OUT/'protocol.json')
    catalog=r.catalog();c=next(c for c in catalog if c['family']=='Uniform' and c['VA']==3.)
    a.validate_source(c)
    if not np.all(c['p']==1/256):raise ValueError('Uniform probabilities changed')
    save('fixed_source.json',{k:c[k] for k in ['family','VA','nu_raw','C','w','ensemble_hash','source_path','source_sha256']})
    context={};rows=[];checks=[]
    for name,g in protocol['scenarios'].items():
        ch=optical(g);raw=a.raw_pdf_moments(ch);b32=bounded_moments(ch);b64=bounded_moments(ch,64)
        # Historical B and Uniform-search C invoke this very same function.
        cb=s.a.legacy.power_conserving(ch)
        if max(abs(b32[k]-b64[k]) for k in ['m1','mh'])>2e-11:raise ValueError('Bounded quadrature mismatch')
        if cb['m1']!=b32['m1'] or cb['mh']!=b32['mh']:raise ValueError('B/C alias identity failed')
        values={}
        for label,m in [('A_Eq10',raw),('B_historical_random_width',b32),('C_Uniform_search_bounded',b32)]:
            value=None
            if m['normalized_within_tolerance']:
                value=s.model(c,m,128,129)
                verification=s.verified.selected_checks(c,value,m)
                if verification['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Independent selected check failed')
                checks.append(dict(scenario=name,channel_model=label,**verification))
            values[label]=value;rows.append(model_row(name,label,m,c,value))
        context[name]=dict(geometry=g,channel=ch,raw_moments=raw,bounded_moments=b32,
            bounded_high=b64,evaluations=values)
        print('FIXED',name,[(row['channel_model'],row['raw_SKR']) for row in rows if row['scenario']==name],flush=True)
    save('fixed_contexts.json',context);save('fixed_validation.json',checks)
    save('three_model_comparison.json',rows);write('three_model_comparison.csv',rows)
    critical=context['critical_uniform_positive']
    optical_diagnostics(critical['channel'])
    rice_diagnostics(critical['channel'])
    moment_attribution(critical['channel'],critical['raw_moments'],critical['bounded_moments'])
    controlled(c,critical['channel'],critical['bounded_moments'])
    fn=a.legacy.power_conserving
    save('channel_alias_identity.json',dict(status='CURRENTLY_VERIFIED_PASS',historical_function=inspect.getsourcefile(fn),
        Uniform_search_function=inspect.getsourcefile(s.a.legacy.power_conserving),
        same_module_object=s.a.legacy is a.legacy,same_function_object=fn is s.a.legacy.power_conserving,
        function_source_sha256=hashlib.sha256(inspect.getsource(fn).encode()).hexdigest(),
        three_requested_labels_are_two_channel_laws=True))
    save('numerical_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',scenarios=len(context),rows=len(rows),
        independent_checks=sum(len(x['checks']) for x in checks),source_hash=c['ensemble_hash'],
        primary_reference_v43_2_status='BLOCKED_REFERENCE_NOT_LOCATED',optimization=False,new_AP=False,
        source_cache_modified=False,security_approved=False,producer_sha256=a.sha(__file__),
        protocol_sha256=a.sha(OUT/'protocol.json')))
    print('FIXED AUDIT COMPLETE',flush=True)


if __name__=='__main__':main()
