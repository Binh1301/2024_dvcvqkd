import hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.integrate import quad
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));out=ROOT/'results/full_geometry_fading_skr_audit_20261017'
from scripts import audit_full_geometry_fading_skr as audit
from src.channel import pointing_error as production
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
runtime=read(out/'runtime_probe.json');independent=read(out/'independent_geometry_audit.json')
physical=runtime['cases'][0]['state']['physical'];record=[];original=production.quad

def capture(f,*args,**kwargs):
    observed=original(f,*args,**kwargs)
    tighter=original(f,*args,**dict(kwargs,epsabs=1e-28,epsrel=2e-13))
    record.append(dict(interval=list(args),kwargs=kwargs,observed_value=observed[0],observed_error_estimate=observed[1],tighter_value=tighter[0],tighter_error_estimate=tighter[1]))
    return observed
production.quad=capture
try:
    p=production.manuscript_pointing_parameters(physical['receiver_radius_m'],physical['beam_waist_m'],physical['wavelength_m'],physical['link_length_m'],math.inf,physical['h_uav_m'],physical['h_hap_m'],physical['zenith_angle_rad'],physical['wind_m_per_s'],physical['cn2_ground_m_minus_two_thirds'])
finally:production.quad=original
high=read(out/'high_precision_common_geometry.json')
def m(x):
    if isinstance(x,list):return [m(v) for v in x]
    if isinstance(x,dict):return {k:m(v) for k,v in x.items()}
    return audit.M(x)
common=m(high);truth=common['mu2_integral'];observed=audit.M(record[0]['observed_value'])
checks=[]
def check(name,ok,detail=None):checks.append(dict(check=name,status='CURRENTLY_VERIFIED_PASS' if ok else 'FAIL',detail=detail))
check('mu2_original_error_within_its_reported_uncertainty',abs(float(truth)-float(observed))<=record[0]['observed_error_estimate'])
check('mu2_tighter_quad_matches_MP',abs(record[0]['tighter_value']-float(truth))<=max(record[0]['tighter_error_estimate'],1e-27))
reconstructions=[]
for entry in runtime['cases']:
    case=entry['case'];D=entry['state']['physical']['receiver_diameter_m'];theta=entry['state']['physical']['theta_div_rad']
    cc=dict(common,mu2_integral=observed)
    gg=audit.geometry(cc,D,theta);ff=audit.fading(gg,entry['settings']['channel']['xi_ch'])
    residuals=dict(G_d=float(gg['G_d'])-entry['state']['physical']['pointing']['G_d'],mean_eta=float(ff['mean_eta'])-entry['state']['moments']['mean_eta'],mean_sqrt_eta=float(ff['mean_sqrt_eta'])-entry['state']['moments']['mean_sqrt_eta'])
    check(case+'_quadrature_cause_reconstructs_runtime',max(abs(v) for v in residuals.values())<1e-13,residuals)
    raw=entry['state']['clear_raw_channel'];mom=entry['state']['moments']
    check(case+'_AoA_preserved_in_runtime_distribution',abs(raw['P0']-mom['outage_atom'])<1e-15 and abs(raw['P0']+raw['P1']-1)<1e-15 and abs(mom['physical_probability_mass']-1)<1e-10)
    model=next(c for c in independent['cases'] if c['case']==case)
    for detector,row in model['quantum'].items():
        old=entry['production_results'][detector]
        check(case+'_'+detector+'_signed_SKR_residual',abs(row['K_raw']-old['K_raw'])<1e-9,dict(K_difference=row['K_raw']-old['K_raw'],xi_difference=row['xi_f']-old['xi_eff'],xi_relative_difference=(row['xi_f']-old['xi_eff'])/old['xi_eff']))
    reconstructions.append(dict(case=case,residuals=residuals,mean_eta_using_original_mu2=float(ff['mean_eta'])))
result=dict(status='CURRENTLY_VERIFIED_PASS' if all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in checks) else 'FAILED',root_cause='Finite precision of production mu2 quadrature with epsabs=1e-18; not a hardware-configuration mismatch',source_file='src/channel/pointing_error.py',function='manuscript_pointing_parameters',original_quadrature=record,MP_mu2=str(truth),mu2_difference_original_minus_MP=float(observed-truth),Gd_difference_independent_minus_runtime=independent['failures'][0]['detail']['G_d'],original_strict_checks_preserved=True,original_failures=independent['failures'],checks=checks,reconstructed_runtime_cases=reconstructions,production_files_edited=False,tighter_quadrature_is_diagnostic_only=True)
(out/'quadrature_precision_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2));assert result['status']=='CURRENTLY_VERIFIED_PASS'
