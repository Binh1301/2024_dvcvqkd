"""Scoped numerical/provenance self-checks for the saved diagnostic."""
import json
import math
import numpy as np
import search as s
from validate import precise_entropy


def main():
    sources=s.n.previous.load_catalog(s.read(s.ROOT/'configs/manuscript_mobility.json'))
    roster={c['ensemble_hash']:c for c in sources}
    rows=[json.loads(line) for line in (s.OUT/'evaluations.jsonl').read_text().splitlines()]
    checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(name=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED',detail=detail))
        if not ok:
            s.save('check_failure.json',checks[-1]);raise AssertionError(name)
    check('authenticated_exact_sources',len(roster)==233,{'MB':sum(c['family']=='MB' for c in sources),'Uniform':sum(c['family']=='Uniform' for c in sources)})
    for r in rows:
        c=roster[r['ensemble_hash']]
        assert all(r[k]==c[k] for k in ['C','w','VA','nu_raw'])
        assert r['physical_mass']==1 and 0<=r['eta_f']<=r['m1']<=r['eta_atm']<=1
        assert abs(r['eta_f']-r['mh']**2)<1e-14
        assert r['eta_det']==.8 and r['epsilon_det']==.0135 and not r['active_only']
        assert r['receiver']=='homodyne_1D' and r['detector_security']=='untrusted' and not r['security_valid']
        assert r['turbulence_factor']==1 and r['zenith_deg']==30 and r['AO']=='OFF'
        assert r['phase_noise']=='OFF_HISTORICAL_ASSUMPTION'
        assert r['rate_per']=='transmitted_use_including_outage'
        assert abs(r['N_fading']-(r['m1']-r['eta_f'])*r['VA'])<2e-13
        assert abs(r['N_channel']-.0186*r['m1'])<2e-13
        assert abs(r['N_detector']-.0135/.8)<2e-13
        assert abs(r['N_post']-(.8*(r['N_fading']+r['N_channel'])+.0135))<2e-13
        assert abs(r['K_raw']-(.95*r['I_AB_actual']-r['chi_BE']))<2e-13
        assert r['I_AB']==r['I_AB_actual'] and 0<=r['I_AB']<=4
        assert r['conditional_mass_error']<2e-12 and r['FFT_negative_roundoff_mass']<1e-12
        assert min(r[k] for k in ['nu_1','nu_2','nu_3'])>=1 and r['uncertainty_min_eigenvalue']>=-1e-11
        assert r['Z_lower']<=r['Z_worst']<=r['Z_upper']
    check('all_saved_evaluations_consistent',True,dict(rows=len(rows),maximum_FFT_negative_roundoff_mass=max(r['FFT_negative_roundoff_mass'] for r in rows)))
    selection=s.read(s.OUT/'final_selection.json')
    for r in selection['recommendations']:
        label=r['recommendation'];par=s.parameters(r);c=roster[r['ensemble_hash']]
        ch,mo=s.n.optical(*par);fine=s.n.previous.power_conserving(ch,64)
        check(label+'_width32_64',max(abs(mo[k]-fine[k]) for k in ['m1','mh'])<2e-10)
        security=s.n.previous.evaluate(c,mo,grid=129)
        check(label+'_full_Z33_129',abs(security['chi_BE']-r['chi_BE'])<2e-8,security['chi_BE']-r['chi_BE'])
        entropy=precise_entropy(r['a'],r['b'],r['Z_worst'],110)
        check(label+'_entropy110',abs(float(entropy['chi'])-r['chi_BE'])<2e-12)
        direct=s.n.previous.pooled_mi(c,ch,radial_order=128,width_order=16)
        fast=s.n.fading_mi(c,par,128,16)
        check(label+'_direct_likelihood_vs_Fourier',abs(direct['I_AB_pooled']-fast['I_AB_actual'])<5e-12,direct['I_AB_pooled']-fast['I_AB_actual'])
        half=s.n.fading_mi(c,par,int(r['radial_order']),int(r['width_order']),spacing=.0125)
        check(label+'_half_output_spacing',abs(half['I_AB_actual']-r['I_AB'])<5e-12)
        t,p=s.n.quadrature(*par,256,32)
        check(label+'_passive_support_and_atom',0<=t.min()<=t.max()<=ch['eta_atm'] and abs(p.sum()-1)<1e-13 and p[t==0].sum()>=mo['P0'],dict(T_min=float(t.min()),T_max=float(t.max()),eta_atm=ch['eta_atm'],atom_P0=mo['P0']))
        w0=2*1.55e-6/(math.pi*par[1]*1e-6)
        check(label+'_transmitter_geometry',abs(w0-r['w0_m'])<1e-14 and abs(2*w0*math.sqrt(math.log(100)/2)-r['transmitter_diameter_99percent_m'])<1e-14)
    roots=__import__('csv').DictReader((s.OUT/'refined_boundary_roots.csv').open())
    residual=max(abs(float(r['residual'])) for r in roots)
    check('fixed_source_root_residuals',residual<1e-7,residual)
    check('final_convergence_margins',all(r['positive_margin_after_2changes']>1e-4 for r in s.read(s.OUT/'final_convergence.json')))
    start=s.read(s.OUT/'startup_manifest.json')
    ledgers={f'paper_uav_hap_cvqkd/{p}' for p in ['docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']}
    changed=[p for p,h in start['protected'].items() if p not in ledgers and s.sha(s.ROOT.parent/p)!=h]
    check('protected_inputs_unchanged',not changed,dict(protected=len(start['protected']),allowed_ledgers=sorted(ledgers),unexpected_changes=changed))
    s.save('checks.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,rows=len(rows),security_valid=False,hardware_validated=False))
    print('CHECKS PASS',len(checks),'rows',len(rows),flush=True)


if __name__=='__main__':main()
