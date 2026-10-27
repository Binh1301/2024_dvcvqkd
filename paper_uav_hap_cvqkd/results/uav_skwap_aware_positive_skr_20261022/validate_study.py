"""Independent scoped checks of saved aperture/detector diagnostic evidence."""
import ast
import csv
import hashlib
import json
import math
import numpy as np
import run_study as s
from validate import precise_entropy


def csv_rows(name):
    with (s.OUT/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))


def main():
    if (s.OUT/'validation.json').exists():raise FileExistsError('Preserve completed validation')
    s.initialize();selection=s.read(s.OUT/'selection.json');roster={c['ensemble_hash']:c for c in s.SOURCES};checks=[]
    def check(name,ok,detail=None):
        r=dict(name=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED',detail=detail);checks.append(r)
        if not ok:s.save('validation_failure.json',r);raise AssertionError(name)
    check('authenticated_exact_source_catalog',len(roster)==233 and sum(c['family']=='MB' for c in s.SOURCES)==197)
    for r in s.ROWS:
        p=s.par(r);s.allowed(p);c=roster[r['ensemble_hash']]
        assert all(r[k]==c[k] for k in ['C','w','VA','nu_raw'])
        assert r['receiver']=='homodyne_1D' and r['detector_security']=='untrusted' and not r['security_valid'] and not r['hardware_validated']
        assert r['AO']=='OFF' and r['phase_noise']=='OFF_HISTORICAL_ASSUMPTION' and r['turbulence_factor']==1
        assert not r['active_only'] and r['physical_mass']==1 and 0<=r['eta_f']<=r['m1']<=r['eta_atm']<=1
        assert abs(r['eta_f']-r['mh']**2)<2e-14 and abs(r['P0']+r['Pactive']-1)<2e-14
        assert abs(r['N_fading']-(r['m1']-r['eta_f'])*r['VA'])<2e-13
        assert abs(r['N_channel']-.0186*r['m1'])<2e-13 and abs(r['N_detector']-r['epsilon_det']/r['eta_det'])<2e-13
        assert abs(r['N_post']-(r['eta_det']*(r['N_fading']+r['N_channel'])+r['epsilon_det']))<2e-13
        assert abs(r['b']-(1+r['eta_det']*r['eta_f']*r['VA']+r['N_post']))<2e-13
        assert r['I_AB']==r['I_AB_actual'] and abs(r['K_raw']-(.95*r['I_AB']-r['chi_BE']))<2e-13
        assert min(r[k] for k in ['nu_1','nu_2','nu_3'])>=1 and r['uncertainty_min_eigenvalue']>=-1e-11
        assert r['Z_lower']<=r['Z_worst']<=r['Z_upper']
        assert r['conditional_mass_error']<2e-12 and r['FFT_negative_roundoff_mass']<1e-12
        assert abs(r['L_km']-19/math.cos(math.radians(r['zenith_deg'])))<1e-11
        assert abs(r['eta_atm']-.92**(1/math.cos(math.radians(r['zenith_deg']))))<2e-14
    check('all_nodes_allowed_parameters_noise_floor_and_measurement',True,len(s.ROWS))
    check('all_nodes_exact_source_noise_once_mass_covariance_signed_rate',True)
    files={};reused=[r for r in s.ROWS if r['origin'].startswith('AUTHENTICATED')]
    for r in reused:
        path=r['reused_from']
        if path not in files:files[path]=(s.ROOT/path).read_text().splitlines()
        line=files[path][r['reused_line']-1];old=json.loads(line)
        assert hashlib.sha256(line.encode()).hexdigest()==r['reused_line_sha256']
        assert all(old[k]==r[k] for k in ['ensemble_hash','D_r','divergence_urad','jitter_urad','sigma_h_m','zenith_deg','eta_det','epsilon_det','I_AB','chi_BE','K_raw','radial_order','width_order'])
    check('all_exact_reused_nodes_line_hash_and_convention_match',True,len(reused))
    regression=s.read(s.OUT/'regression.json')
    check('four_fresh_matching_regressions_before_search',regression['status']=='CURRENTLY_VERIFIED_PASS' and len(regression['records'])==4 and all(r['stage'].startswith('regression_') for r in s.ROWS[:4]))
    check('actual_MI_saved_bytecode_identical',s.n.fading_mi.__code__ is s.n.saved.fading_mi.__code__)
    check('historical_MI_quadrature_dependency_unmodified',s.n.saved.fading_mi.__globals__['quadrature'] is s.n.saved.quadrature and s.n.fading_mi.__globals__['quadrature'] is s.n.quadrature)
    for angle in [0.,15.,30.]:
        p=(20.,1.,angle,35.,3.,.1,.8,.005,.92,.08)
        t,w=s.n.quadrature(p,128,16);t0,w0=s.n.saved.quadrature(p[:9],128,16)
        check(f'Dr8_quadrature_exact_match_{angle}',np.array_equal(t,t0) and np.array_equal(w,w0))
    for diameter,angle in [(.15,0.),(.30,15.),(.401,30.)]:
        ch,mo=s.n.optical(diameter,35.,3.,.1,angle)
        old=s.n.previous.optical(diameter,35.,angle,.1,3/15.61);oldmo=s.n.previous.power_conserving(old)
        check(f'variable_D_same_existing_collector_{diameter}_{angle}',max(abs(mo[k]-oldmo[k]) for k in ['m1','mh'])<5e-12)
    coverage=s.read(s.OUT/'source_coverage.json')
    check('physical_source_coverage_includes_cached_A_nodes',coverage['status']=='CURRENTLY_VERIFIED_PASS' and all(x['physical_contexts']==90 for x in coverage['coverage']))
    for path in s.OUT.glob('catalog_*.csv'):
        with path.open() as f:rows=list(csv.DictReader(f))
        assert len(rows)==233 and {r['ensemble_hash'] for r in rows}==set(roster)
    check('all_catalog_contexts_full_233_exact_sources',True,len(list(s.OUT.glob('catalog_*.csv'))))
    for path in s.OUT.glob('alternating_*.csv'):
        with path.open() as f:rows=list(csv.DictReader(f))
        assert {float(r['start']) for r in rows}=={.05,.1,.165,.3} and all(float(r['delta_K'])>=-1e-13 for r in rows)
    check('P1_P2_ascent_and_starts_logged',True)
    roots=csv_rows('critical_receiver_roots.csv')
    assert all(abs(float(r['residual']))<1e-7 and float(r['bracket_lower_m'])<=float(r['D_crit_m'])<=float(r['bracket_upper_m']) for r in roots)
    check('fixed_source_local_root_brackets_and_residuals',True,len(roots))
    threshold=s.read(s.OUT/'threshold_reference.json')
    check('detector_threshold_comparison_uses_identical_source',all(r['ensemble_hash']==threshold['source']['ensemble_hash'] for r in roots))
    minimum=s.read(s.OUT/'source_refined_minimum.json')
    check('selected_source_local_aperture_refinement',minimum['status']=='CURRENTLY_VERIFIED_PASS' and minimum['final_D_m']<=minimum['initial_D_m']
        and all(abs(r['residual'])<1e-7 and r['lower_m']<=r['D_crit_m']<=r['upper_m'] for r in minimum['roots']))
    check('phase1_shortlist_artifacts_preserved',all(s.sha(s.OUT/'selection_phase1'/p)==h for p,h in minimum['phase1_sha256'].items()))
    conv=s.read(s.OUT/'convergence.json')
    check('positive_shortlist_convergence_and_observed_margin',all(r['observed_MI_change']<2e-6 and r['conservative_observed_margin']>0 for r in conv),len(conv))
    robust=csv_rows('robustness.csv');positive=csv_rows('table_B_positive_candidates.csv')
    for r in positive:
        rr=[x for x in robust if x['candidate']==r['candidate']]
        assert len(rr)==7 and len({x['ensemble_hash'] for x in rr})==1
        assert all(float(x['robustness_observed_MI_change'])<2e-6 and float(x['radial_order'])>=512 for x in rr)
        assert all(float(x['D_r'])==float(r['D_r']) and float(x['eta_det'])==float(r['eta_det']) for x in rr)
        factors={'nominal':(1.,1.),'jitter_plus10':(1.1,1.),'centering_plus10':(1.,1.1),'joint_plus10':(1.1,1.1),'joint_plus20':(1.2,1.2)}
        for x in rr:
            for field in ['ensemble_hash','divergence_urad','zenith_deg','VA','nu_raw']:
                assert x[field]==r[field]
            jf,sf=factors.get(x['case'],(1.,1.))
            assert abs(float(x['jitter_urad'])-float(r['jitter_urad'])*jf)<1e-13
            assert abs(float(x['sigma_h_m'])-float(r['sigma_h_m'])*sf)<1e-13
            expected_noise=float(x['case'].split('_',1)[1]) if x['case'].startswith('noise_') else float(r['epsilon_det'])
            assert float(x['epsilon_det'])==expected_noise
            cached=s.CACHE[s.key(roster[x['ensemble_hash']],s.par(x),int(x['radial_order']),int(x['width_order']))]
            assert all(float(x[k])==cached[k] for k in ['I_AB','chi_BE','K_raw'])

    check('all_positive_shortlist_candidates_have_requested_robustness_cases',True,len(positive))
    for i,r in enumerate(selection['recommendations']):
        p=s.par(r);c=roster[r['ensemble_hash']];ch,mo=s.n.optical(p[9],p[3],p[4],p[5],p[2]);fine=s.n.previous.power_conserving(ch,64)
        check(f'design{i}_width32_64',max(abs(mo[k]-fine[k]) for k in ['m1','mh'])<2e-10)
        z=s.n.previous.evaluate(c,mo,eta_det=p[6],epsilon_det=p[7],grid=129)
        check(f'design{i}_full_Z33_129',abs(z['chi_BE']-r['chi_BE'])<2e-8)
        entropy=precise_entropy(r['a'],r['b'],r['Z_worst'],110)
        check(f'design{i}_entropy110',abs(float(entropy['chi'])-r['chi_BE'])<2e-12)
        direct=s.n.previous.pooled_mi(c,ch,eta_det=p[6],epsilon_det=p[7],radial_order=128,width_order=16)
        fast=s.n.fading_mi(c,p,128,16)
        check(f'design{i}_direct_vs_Fourier_MI',abs(direct['I_AB_pooled']-fast['I_AB_actual'])<5e-12)
        half=s.n.fading_mi(c,p,int(r['radial_order']),int(r['width_order']),spacing=.0125)
        check(f'design{i}_half_output_spacing',abs(half['I_AB_actual']-r['I_AB'])<5e-12)
        t,w=s.n.quadrature(p,256,32)
        check(f'design{i}_passive_support_and_outage',0<=t.min()<=t.max()<=ch['eta_atm'] and abs(w.sum()-1)<1e-13 and w[t==0].sum()>=mo['P0'])
    hardware=s.read(s.OUT/'hardware_evidence.json');h=hardware['rows']
    detector=next(x for x in h if x['group']=='balanced_detector');adc=next(x for x in h if x['group']=='ADC_DAQ')
    check('grounded_component_power_arithmetic',abs(detector['electrical_operating_W']-15*(.120+.090))<1e-14 and abs(adc['electrical_operating_W']-2*.106)<1e-14)
    check('missing_system_power_rate_availability_not_fabricated',not hardware['aggregate_power_calculated'] and not hardware['throughput_energy_sortie_calculated'] and all(hardware[k] is None for k in ['selected_payload_mass_kg','selected_QKD_operating_power_W','selected_f_rep_Hz','external_link_availability','usable_flight_energy_Wh','flight_duration_s','duty_cycle']))
    start=s.read(s.OUT/'startup_manifest.json');allowed={f'paper_uav_hap_cvqkd/{p}' for p in ['docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']}
    changed=[p for p,h in start['protected'].items() if p not in allowed and s.sha(s.ROOT.parent/p)!=h]
    check('historical_sources_configs_caches_frozen_results_preserved',not changed,dict(protected_files=len(start['protected']),unexpected=changed))
    check('imported_optical_MI_security_model_bytes_unchanged',all(s.sha(s.ROOT/p)==h for p,h in start['imported_model_sha256'].items()))
    protocol=s.read(s.OUT/'protocol.json')
    check('adapter_and_initial_producer_hashes_unchanged',s.sha(s.OUT/'parameter_adapter.py')==protocol['adapter_sha256'] and s.sha(s.OUT/'run_study.py')==protocol['producer_sha256'])
    for p in s.OUT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    check('all_python_AST',True)
    s.save('validation.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,rows=len(s.ROWS),new_evaluations=len(s.ROWS)-len(reused),reused_evaluations=len(reused),positive_shortlist=len(positive),security_valid=False,hardware_validated=False))
    print('VALIDATION PASS',len(checks),'nodes',len(s.ROWS),'reused',len(reused),flush=True)


if __name__=='__main__':main()
