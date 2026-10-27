"""Independent scoped checks of the fixed8cm saved numerical evidence."""
import json
import math
import numpy as np
from scipy.integrate import quad
import search as s
from validate import precise_entropy


def main():
    selection=s.read(s.OUT/'selection.json')
    sources=s.n.previous.load_catalog(s.read(s.ROOT/'configs/manuscript_mobility.json'));roster={c['ensemble_hash']:c for c in sources}
    rows=[json.loads(line) for line in (s.OUT/'evaluations.jsonl').read_text().splitlines()];checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(name=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED',detail=detail))
        if not ok:s.save('validation_failure.json',checks[-1]);raise AssertionError(name)
    check('authenticated233_sources',len(roster)==233)
    for r in rows:
        c=roster[r['ensemble_hash']]
        assert all(r[k]==c[k] for k in ['C','w','VA','nu_raw'])
        assert r['D_r']==.08 and r['receiver']=='homodyne_1D' and r['detector_security']=='untrusted' and not r['security_valid']
        assert r['AO']=='OFF' and r['phase_noise']=='OFF_HISTORICAL_ASSUMPTION' and r['turbulence_factor']==1
        assert r['physical_mass']==1 and 0<=r['eta_f']<=r['m1']<=r['eta_atm']<=1
        assert abs(r['eta_f']-r['mh']**2)<2e-14 and abs(r['Pactive']+r['P0']-1)<2e-14
        assert abs(r['N_channel']-.0186*r['m1'])<2e-13
        assert abs(r['N_detector']-r['epsilon_det']/r['eta_det'])<2e-13
        assert abs(r['N_fading']-(r['m1']-r['eta_f'])*r['VA'])<2e-13
        assert abs(r['N_post']-(r['eta_det']*(r['N_fading']+r['N_channel'])+r['epsilon_det']))<2e-13
        assert r['I_AB']==r['I_AB_actual'] and abs(r['K_raw']-(.95*r['I_AB']-r['chi_BE']))<2e-13
        assert min(r[k] for k in ['nu_1','nu_2','nu_3'])>=1 and r['uncertainty_min_eigenvalue']>=-1e-11
        assert r['conditional_mass_error']<2e-12 and r['FFT_negative_roundoff_mass']<1e-12
        assert r['Z_lower']<=r['Z_worst']<=r['Z_upper']
        assert abs(r['L_km']-(r['h_hap_km']-r['h_uav_km'])/math.cos(math.radians(r['zenith_deg'])))<1e-11
        assert abs(r['eta_atm']-r['tau_zen']**(1/math.cos(math.radians(r['zenith_deg']))))<2e-14
    check('all_rows_fixed8cm_noise_geometry_information_physicality',True,{'rows':len(rows),'new':sum(r['origin'].startswith('NEW') for r in rows),'reused':sum(r['origin'].startswith('AUTHENTICATED') for r in rows)})
    # Reuse is authenticated at the exact original line, not merely matching rounded values.
    prior=s.ROOT/'results/minimal_physical_positive_skr_20261022/evaluations.jsonl';lines=prior.read_text().splitlines()
    for r in rows:
        if not r['origin'].startswith('AUTHENTICATED'):continue
        line=lines[int(r['reused_line'])-1]
        assert __import__('hashlib').sha256(line.encode()).hexdigest()==r['reused_line_sha256']
        old=json.loads(line)
        assert old['ensemble_hash']==r['ensemble_hash'] and old['K_raw']==r['K_raw'] and old['I_AB_actual']==r['I_AB_actual']
        assert r['h_hap_km']==20 and r['h_uav_km']==1 and r['zenith_deg']==30 and r['tau_zen']==.92 and r['eta_det']==.8 and r['epsilon_det']==.0135
    check('every_reused_node_hash_and_complete_convention_match',True)
    for hH,hU in [(20.,1.),(17.,5.),(20.,3.)]:
        jry,jmu=s.n.primitives(hH,hU);h0,h1=hU*1000,hH*1000
        def hv(h):return .00594*(21/27)**2*(1e-5*h)**10*np.exp(-h/1000)+2.7e-16*np.exp(-h/1500)+1e-14*np.exp(-h/100)
        ry,_=quad(lambda h:1e14*hv(h)*(h-h0)**(5/6),h0,h1,epsabs=1e-8,epsrel=2e-11,limit=300)
        mu,_=quad(lambda h:1e14*hv(h)*((h-h0)/(h1-h0))**(5/3),h0,h1,epsabs=1e-10,epsrel=2e-11,limit=300)
        check(f'geometry_HV_independent_{hH}_{hU}',max(abs(ry/1e14/float(jry)-1),abs(mu/1e14/float(jmu)-1))<1e-8)
    for r in selection['recommendations']:
        label=r['configuration'];par=s.parameters(r);c=roster[r['ensemble_hash']]
        ch,mo=s.n.optical(*par[:6],par[8]);fine=s.n.previous.power_conserving(ch,64)
        check(label+'_width32_64',max(abs(mo[k]-fine[k]) for k in ['m1','mh'])<2e-10)
        z=s.n.previous.evaluate(c,mo,eta_det=par[6],epsilon_det=par[7],grid=129)
        check(label+'_fullZ33_129',abs(z['chi_BE']-r['chi_BE'])<2e-8)
        entropy=precise_entropy(r['a'],r['b'],r['Z_worst'],110)
        check(label+'_entropy110',abs(float(entropy['chi'])-r['chi_BE'])<2e-12)
        direct=s.n.previous.pooled_mi(c,ch,eta_det=par[6],epsilon_det=par[7],radial_order=128,width_order=16)
        fast=s.n.fading_mi(c,par,128,16)
        check(label+'_direct_vs_Fourier',abs(direct['I_AB_pooled']-fast['I_AB_actual'])<5e-12,direct['I_AB_pooled']-fast['I_AB_actual'])
        half=s.n.fading_mi(c,par,int(r['radial_order']),int(r['width_order']),spacing=.0125)
        check(label+'_half_spacing',abs(half['I_AB_actual']-r['I_AB'])<5e-12)
        t,p=s.n.quadrature(par,256,32)
        check(label+'_passive_support_atom',0<=t.min()<=t.max()<=ch['eta_atm'] and abs(p.sum()-1)<1e-13 and p[t==0].sum()>=mo['P0'])
        check(label+'_primary_height_not_uncalibrated_altitude',par[0:2]==(20.,1.))
    convergence=s.read(s.OUT/'convergence.json')
    check('selected_actual_MI_convergence',all(x['observed_MI_change']<2e-6 for x in convergence))
    check('positive_rate_exceeds_observed_numerical_change',all(x['K_after_2changes']>1e-4 for x in convergence if next(r['K_raw'] for r in selection['recommendations'] if r['configuration']==x['configuration'])>0))
    necessity=s.read(s.OUT/'necessity.json')
    check('necessity_and_original_geometry_positive_refinement',necessity['status']=='CURRENTLY_VERIFIED_PASS' and all(r['K_raw']>2*.95*r['observed_MI_change'] and abs(r['full_Z33_129_difference'])<2e-8 for r in necessity['additional_positive_original_geometry']))
    import csv
    for name,column in [('thresholds.csv','residual'),('geometry_detector_roots.csv','K_residual'),('divergence_thresholds.csv','residual')]:
        with (s.OUT/name).open() as f:root_rows=list(csv.DictReader(f))
        residual=max((abs(float(r[column])) for r in root_rows),default=0.)
        check('root_residual_'+name,residual<1e-7,dict(roots=len(root_rows),maximum_residual=residual))
    start=s.read(s.OUT/'startup_manifest.json')
    ledgers={f'paper_uav_hap_cvqkd/{p}' for p in ['docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']}
    changed=[p for p,h in start['protected'].items() if p not in ledgers and s.sha(s.ROOT.parent/p)!=h]
    check('historical_source_model_cache_artifacts_preserved',not changed,{'protected_files':len(start['protected']),'unexpected_changes':changed})
    s.save('validation.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,rows=len(rows),new_evaluations=sum(r['origin'].startswith('NEW') for r in rows),reused=sum(r['origin'].startswith('AUTHENTICATED') for r in rows),security_valid=False))
    print('VALIDATION PASS',len(checks),len(rows),flush=True)


if __name__=='__main__':main()
