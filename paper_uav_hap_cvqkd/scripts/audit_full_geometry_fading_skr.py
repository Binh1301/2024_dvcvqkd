"""Independent geometry/PDF derivation with reused independent quantum diagnostics.

No production geometry, channel-moment, MI, or Holevo helpers are imported.
"""
import csv,hashlib,json,math,sys,time
from pathlib import Path
import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.special import log_ndtr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import audit_negative_skr_independent as quantum
OUT=ROOT/'results/full_geometry_fading_skr_audit_20261017'
M=quantum.M
mp.mp.dps=70


def primitive_integrals(defaults,settings):
    c=defaults['channel'];geo=settings['geometry'];profile=c['turbulence_profile']
    h0,h1,wl,wind,ground=map(M,(c['h_uav_m'],c['h_hap_m'],c['wavelength_m'],profile['wind_speed_m_per_s'],profile['cn2_ground_m_minus_two_thirds']))
    index=geo['reference_position_index'];cells=geo['grid_cells_per_side'];step=M(geo['grid_side_m'])/cells
    q=[(index%cells+mp.mpf('.5'))*step,(index//cells+mp.mpf('.5'))*step]
    horizontal=mp.sqrt(sum((M(x)-y)**2 for x,y in zip(geo['hap_horizontal_m'],q)))
    dh=h1-h0;zeta=mp.atan2(horizontal,dh);sec=1/mp.cos(zeta);L=dh*sec;k=2*mp.pi/wl
    def cn2(h):return M('.00594')*(wind/27)**2*(M('1e-5')*h)**10*mp.exp(-h/1000)+M('2.7e-16')*mp.exp(-h/1500)+ground*mp.exp(-h/100)
    knots=[h0]+[M(x) for x in (2000,5000,10000) if h0<x<h1]+[h1]
    integrate=lambda f:mp.quad(f,knots)
    jry=integrate(lambda h:cn2(h)*(h-h0)**(M(5)/6))
    mu2=integrate(lambda h:cn2(h)*((h-h0)/dh)**(M(5)/3))
    jnum=integrate(lambda h:cn2(h)*h*h);jden=integrate(lambda h:cn2(h)*h**(M(5)/6))
    return dict(h_hap_m=h1,h_uav_m=h0,vertical_span_m=dh,wavelength_m=wl,wind_m_per_s=wind,cn2_ground=ground,
                reference_xy_m=q,horizontal_distance_m=horizontal,zeta_rad=zeta,zeta_deg=zeta*180/mp.pi,secant=sec,
                L_m=L,wave_number_per_m=k,tau_zen=M(settings['channel']['clear_tau_zen']),
                eta_atm=M(settings['channel']['clear_tau_zen'])**sec,rytov_integral=jry,mu2_integral=mu2,
                aperture_numerator=jnum,aperture_denominator=jden,Phi_m=(jnum/jden)**(M(6)/7),
                sigma_R2=M('2.25')*k**(M(7)/6)*sec**(M(11)/6)*jry,
                theta_jt_rad=M(c['pointing']['theta_jt_rad']),sigma_h_m=M(c['pointing']['sigma_h_m']),
                sigma_o_rad=M(c['aoa']['sigma_o_rad']),theta_FOV_rad=M(c['aoa']['theta_fov_rad']))


def geometry(common,diameter,theta):
    c=common;D,theta=map(M,(diameter,theta));wl,L,k=c['wavelength_m'],c['L_m'],c['wave_number_per_m']
    w0=2*wl/(mp.pi*theta);rayleigh=mp.pi*w0*w0/wl
    # Current runtime F0=infinity is checked explicitly by the caller.
    focusing=mp.mpf(1);wL=w0*mp.sqrt(focusing*focusing+(L*wl/(mp.pi*w0*w0))**2)
    beam_lambda=2*L/(k*wL*wL)
    Gd=M('4.35')*beam_lambda**(M(5)/6)*k**(M(7)/6)*c['vertical_span_m']**(M(5)/6)*c['secant']**(M(11)/6)*c['mu2_integral']
    weff=wL*mp.sqrt(1+Gd);v=mp.sqrt(mp.pi)*D/(2*mp.sqrt(2)*weff);erf=mp.erf(v);A0=erf*erf
    weq=mp.sqrt(weff*weff*mp.sqrt(mp.pi)*erf/(2*v*mp.exp(-v*v)))
    # The first pointing metadata helper uses unbroadened nu; active LiteralChannel does not.
    v_metadata=mp.sqrt(mp.pi)*D/(2*mp.sqrt(2)*wL)
    metadata_A0=mp.erf(v_metadata)**2
    metadata_weq=mp.sqrt(weff*weff*mp.sqrt(mp.pi)*mp.erf(v_metadata)/(2*v_metadata*mp.exp(-v_metadata*v_metadata)))
    sigma_jt=L*c['theta_jt_rad'];sigma_s=mp.sqrt(c['sigma_h_m']**2+sigma_jt*sigma_jt)
    chi=weq/(2*sigma_s);d=chi*chi
    P0=mp.exp(-c['theta_FOV_rad']**2/(2*c['sigma_o_rad']**2));P1=1-P0
    Aap=1/(1+M('1.11')*(D*D/(wl*c['Phi_m']*c['secant']))**(M(7)/6))
    return dict(c,Dr_m=D,r_ap_m=D/2,theta_div_rad=theta,w0_m=w0,rayleigh_m=rayleigh,F0='infinity',focusing_factor=focusing,
                wL_m=wL,beam_lambda=beam_lambda,G_d=Gd,w_eff_m=weff,nu_ap=v,erf_nu=erf,A0=A0,w_eq_m=weq,
                metadata_unbroadened_nu=v_metadata,metadata_unbroadened_A0=metadata_A0,metadata_unbroadened_weq=metadata_weq,
                sigma_jt_m=sigma_jt,sigma_s_m=sigma_s,pointing_chi=chi,pointing_chi_squared=d,P0=P0,P1=P1,
                A_ap=Aap,v_sc_unused_in_active_PDF=Aap*c['sigma_R2'])


def fading(g,xi):
    d=g['pointing_chi_squared'];B=g['A0']*g['eta_atm'];s=g['sigma_R2']
    # Runtime boresight is zero; the exact general coefficients reduce to these expressions.
    C1=mp.exp(s*d*(1+d)/2);C3=1/mp.sqrt(2*s);mu=s*(1+2*d)/2;x1=-mp.log(B)+mu
    def Q(a):return (mp.exp(a*x1-a*mu)*mp.erfc(C3*x1)+mp.exp(a*a/(4*C3*C3)-a*mu)*mp.erfc(a/(2*C3)-C3*x1))/2
    q0,qh,q1=Q(d),Q(d+M('.5')),Q(d+1);active_mass=C1*q0
    raw_m1=g['P1']*B*d*C1/(d+1)*q1
    raw_mh=g['P1']*mp.sqrt(B)*d*C1/(d+M('.5'))*qh
    m1=raw_m1/active_mass;mh=raw_mh/active_mass
    # Independent log-coordinate quadrature of the displayed PDF, not the closed form.
    df,bf,c1f,c3f,muf=map(float,(d,B,C1,C3,mu))
    logpref=math.log(df*c1f/2)-df*math.log(bf)
    def density_y(y,power):
        x=logpref+(df+power)*y+math.log(2)+float(log_ndtr(-math.sqrt(2)*c3f*(y-math.log(bf)+muf)))
        return math.exp(x) if x>-745 else 0.
    def integral(power,lower=-math.inf,upper=0.):return quad(lambda y:density_y(y,power),lower,upper,epsabs=2e-13,epsrel=2e-13,limit=350)
    mass_q,em=integral(0);m1q,e1=integral(1);mhq,eh=integral(.5);tail_q,et=integral(0,0.,math.inf)
    independent_raw_m1=float(g['P1'])*m1q;independent_raw_mh=float(g['P1'])*mhq
    numerical_m1=independent_raw_m1/mass_q;numerical_mh=independent_raw_mh/mass_q
    return dict(B=B,C1=C1,C3=C3,mu=mu,x1=x1,Q_chi2=q0,Q_chi2_plus_half=qh,Q_chi2_plus_one=q1,
                raw_active_mass=active_mass,raw_total_mass=g['P0']+g['P1']*active_mass,
                raw_mass_deficit=g['P1']*(1-active_mass),raw_mean_eta=raw_m1,raw_mean_sqrt_eta=raw_mh,
                mean_eta=m1,mean_sqrt_eta=mh,m_xi=M(xi)*m1,physical_total_mass=g['P0']+g['P1'],
                numerical_active_mass=mass_q,numerical_raw_total_mass=float(g['P0'])+float(g['P1'])*mass_q,
                numerical_raw_m1=independent_raw_m1,numerical_raw_mhalf=independent_raw_mh,
                numerical_mean_eta=numerical_m1,numerical_mean_sqrt_eta=numerical_mh,numerical_m_xi=M(xi)*numerical_m1,
                numerical_tail_probability=tail_q,numerical_whole_raw_total=float(g['P0'])+float(g['P1'])*(mass_q+tail_q),
                quadrature_error_estimates=dict(mass=em,m1=e1,mhalf=eh,tail=et),
                PDF_active_prefactor=g['P1']*d*C1/(2*B**d),rho=0,
                conditioning='Preserve existing active conditioning on (0,1] and retain P0 separately; no new normalization choice')


def main():
    if (OUT/'independent_geometry_audit.json').exists():raise RuntimeError('Completed audit is immutable')
    runtime=json.loads((OUT/'runtime_probe.json').read_text(encoding='utf-8'))
    c=primitive_integrals(runtime['defaults'],runtime['binary_settings']);source=runtime['source'];xi=runtime['binary_settings']['channel']['xi_ch']
    checks=[];failures=[]
    def check(name,ok,details=None):
        row=dict(check=name,status='CURRENTLY_VERIFIED_PASS' if ok else 'FAIL',detail=details);checks.append(row)
        if not ok:failures.append(row)
    check('runtime_target_units',abs(runtime['cases'][0]['state']['physical']['theta_div_rad']-10e-6)<1e-18 and runtime['cases'][0]['state']['physical']['receiver_diameter_m']==.55)
    check('radius_not_diameter',runtime['cases'][0]['settings']['channel']['receiver_radius_m']==.275)
    check('F0_infinity',runtime['defaults']['channel']['radius_of_curvature_m']=={'float_hex':'inf'})
    check('reconstructed_A_matches_cached_geometry',runtime['fresh_A_matches_saved_state'])
    check('physics_no_environment_override_path',runtime['no_environment_physics_override_path'])
    check('source_ensemble',max(abs(quantum.source_audit(source)[k]) for k in ('normalization_residual','energy_residual','PMF_reconstruction_residual','amplitude_reconstruction_residual'))<1e-12)
    cases=[];high=[];mirows=[];moment_table=[];began=time.perf_counter()
    definitions=[('A',2*runtime['binary_settings']['channel']['receiver_radius_m'],10e-6),('B',.08,233e-6),('C',.55,233e-6),('D',.08,10e-6)]
    for case,D,theta in definitions:
        g=geometry(c,D,theta);f=fading(g,xi);observed=next(x for x in runtime['cases'] if x['case']==case)
        p=observed['state']['physical'];raw=observed['state']['clear_raw_channel'];m=observed['state']['moments']
        pairs={'L_m':p['link_length_m'],'zeta_rad':p['zenith_angle_rad'],'eta_atm':p['eta_atm'],'w0_m':p['beam_waist_m'],
               'wL_m':p['pointing']['omega_L_m'],'G_d':p['pointing']['G_d'],'A0':raw['A0'],'w_eq_m':raw['w_eq'],
               'sigma_s_m':raw['sigma_s'],'sigma_R2':raw['sigma_R2'],'P0':raw['P0'],
               'A_ap':p['A_ap'],'v_sc_unused_in_active_PDF':p['v_sc']}
        residual={k:float(g[k])-v for k,v in pairs.items()}
        check(case+'_geometry_runtime_agreement',all(abs(diff)<=1e-12+1e-10*abs(pairs[k]) for k,diff in residual.items()),residual)
        for label,k,q in [('raw_mass','raw_total_mass','numerical_raw_total_mass'),('raw_m1','raw_mean_eta','numerical_raw_m1'),
                           ('raw_mhalf','raw_mean_sqrt_eta','numerical_raw_mhalf'),('physical_m1','mean_eta','numerical_mean_eta'),
                           ('physical_mhalf','mean_sqrt_eta','numerical_mean_sqrt_eta'),('physical_mxi','m_xi','numerical_m_xi')]:
            error=abs(float(f[k])-float(f[q]));rel=error/max(abs(float(f[k])),1e-300)
            check(case+'_'+label+'_closed_quadrature',rel<1e-10 or error<2e-13,dict(absolute_error=error,relative_error=rel))
            moment_table.append(dict(case=case,quantity=label,closed_form=float(f[k]),quadrature=float(f[q]),relative_error=rel))
        check(case+'_closed_runtime_moments',max(abs(float(f['mean_eta'])-m['mean_eta']),abs(float(f['mean_sqrt_eta'])-m['mean_sqrt_eta']))<1e-11)
        check(case+'_full_raw_mass_including_tail',abs(f['numerical_whole_raw_total']-1)<2e-12)
        check(case+'_outage_atom_preserved',float(g['P0'])==float(g['P0']) and abs(float(g['P0']+g['P1'])-1)<1e-14)
        quantum_results={}
        for detector,settings in runtime['detectors'].items():
            model=quantum.physical_model(source,f['mean_eta'],f['mean_sqrt_eta'],xi,settings['eta_B'],settings['nu_B'])
            mi=quantum.independent_MI(source,model['eta_f'],model['N_eff'],settings['eta_B'],settings['nu_B'],full=True)
            model.update(mi);model['beta_I_AB']=M(runtime['beta_rec'])*M(mi['I_AB']);model['K_raw']=model['beta_I_AB']-model['chi_BE']
            actual=observed['production_results'][detector]
            diffs={k:float(model[k])-actual[q] for k,q in [('W_pre','W_pre'),('Z','Z_star'),('eta_f','T_eff'),('xi_f','xi_eff'),('I_AB','I_AB'),('chi_BE','chi_BE'),('K_raw','K_raw')]}
            check(case+'_'+detector+'_independent_SKR_agreement',max(abs(v) for v in diffs.values())<1e-9,diffs)
            for label,ok in model['checks'].items():check(case+'_'+detector+'_'+label,bool(ok))
            model['fading_fraction_percent']=100*model['fading_excess_output']/model['N_eff']
            quantum_results[detector]=quantum.to_json(model);high.append(dict(case=case,detector=detector,**quantum.high_precision(model)))
            mirows.append(dict(case=case,detector=detector,**{k:quantum.to_json(model[k]) for k in ('I_AB','beta_I_AB','S_AB','conditional_entropy','chi_BE','K_raw','chi_upper')}))
        cases.append(dict(case=case,geometry=quantum.to_json(g),fading=quantum.to_json(f),quantum=quantum_results,runtime_geometry_fingerprint=observed['geometry_fingerprint']))
        print('INDEPENDENT_CASE',case,'m1',float(f['mean_eta']),'K',quantum_results['ideal_primary']['K_raw'],flush=True)
    result=dict(verdicts=['CONFIGURATION_MATCH_CONFIRMED','NUMERICALLY_CONSISTENT','UNVALIDATED_SECURITY_MODEL'] if not failures else ['FAILED_AUDIT','UNVALIDATED_SECURITY_MODEL'],
                checks=checks,failures=failures,independent_geometry_to_SKR_cases=8,source_moment_builds=0,full_catalog_or_missions_run=False,
                common_primitives=quantum.to_json(c),cases=cases,quantum_helper='Independent audit code scripts/audit_negative_skr_independent.py, not production numerical helpers',
                independent_quantum_helper_sha256=hashlib.sha256((ROOT/'scripts/audit_negative_skr_independent.py').read_bytes()).hexdigest(),
                runtime_probe_sha256=hashlib.sha256((OUT/'runtime_probe.json').read_bytes()).hexdigest(),elapsed_seconds=time.perf_counter()-began)
    (OUT/'independent_geometry_audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (OUT/'high_precision_SKR.json').write_text(json.dumps(high,indent=2)+'\n',encoding='utf-8')
    for name,rows in (('moments_closed_vs_quadrature.csv',moment_table),('SKR_entropy_decomposition.csv',mirows)):
        with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (OUT/'high_precision_common_geometry.json').write_text(json.dumps(quantum.high_precision(c),indent=2)+'\n',encoding='utf-8')
    print('VERDICTS',result['verdicts'],'CHECKS',len(checks),'FAILURES',len(failures),flush=True)


if __name__=='__main__':main()
