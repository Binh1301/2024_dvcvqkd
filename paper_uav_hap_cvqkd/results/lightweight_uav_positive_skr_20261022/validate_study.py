"""Scoped numerical and provenance checks, with unchanged historical helpers."""
import ast
import csv
import hashlib
import json
import math
import numpy as np
import run_study as s
from validate import precise_entropy


def main():
    if (s.OUT/'validation.json').exists():raise FileExistsError('Preserve completed validation')
    s.initialize();selection=s.read(s.OUT/'selection.json');roster={c['ensemble_hash']:c for c in s.SOURCES};checks=[]
    def check(name,ok,detail=None):
        result=dict(name=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED',detail=detail);checks.append(result)
        if not ok:s.save('validation_failure.json',result);raise AssertionError(name)
    check('source_catalog_authenticated_233',len(roster)==233 and sum(c['family']=='MB' for c in roster.values())==197)
    for r in s.ROWS:
        p=s.par(r);s.allowed(p);c=roster[r['ensemble_hash']]
        assert all(r[k]==c[k] for k in ['C','w','VA','nu_raw'])
        assert r['D_r']==.08 and r['receiver']=='homodyne_1D' and r['detector_security']=='untrusted'
        assert not r['security_valid'] and not r['hardware_validated'] and not r['active_only']
        assert r['AO']=='OFF' and r['phase_noise']=='OFF_HISTORICAL_ASSUMPTION' and r['turbulence_factor']==1
        assert 0<=r['eta_f']<=r['m1']<=r['eta_atm']<=1 and r['physical_mass']==1
        assert abs(r['eta_f']-r['mh']**2)<2e-14 and abs(r['P0']+r['Pactive']-1)<2e-14
        assert abs(r['N_fading']-(r['m1']-r['eta_f'])*r['VA'])<2e-13
        assert abs(r['N_channel']-.0186*r['m1'])<2e-13
        assert abs(r['N_detector']-r['epsilon_det']/r['eta_det'])<2e-13
        assert abs(r['N_post']-(r['eta_det']*(r['N_fading']+r['N_channel'])+r['epsilon_det']))<2e-13
        assert abs(r['a']-(1+r['VA']))<2e-13
        assert abs(r['b']-(1+r['eta_det']*r['eta_f']*r['VA']+r['N_post']))<2e-13
        assert r['I_AB']==r['I_AB_actual'] and abs(r['K_raw']-(.95*r['I_AB']-r['chi_BE']))<2e-13
        assert min(r[k] for k in ['nu_1','nu_2','nu_3'])>=1 and r['uncertainty_min_eigenvalue']>=-1e-11
        assert r['Z_lower']<=r['Z_worst']<=r['Z_upper'] and r['full_Z_grid']==33
        assert r['conditional_mass_error']<2e-12 and r['FFT_negative_roundoff_mass']<1e-12
        assert abs(r['L_km']-19/math.cos(math.radians(r['zenith_deg'])))<1e-11
        assert abs(r['eta_atm']-.92**(1/math.cos(math.radians(r['zenith_deg']))))<2e-14
    check('all_rows_parameter_floor_and_unchanged_conventions',True,dict(rows=len(s.ROWS),detector_noises=sorted({r['epsilon_det'] for r in s.ROWS})))
    check('all_rows_exact_source_noise_once_covariance_mass_signed_rate',True)
    reused=[r for r in s.ROWS if r['origin'].startswith('AUTHENTICATED')]
    lines=(s.ROOT/'results/positive_skr_without_receiver_enlargement_20261022/evaluations.jsonl').read_text().splitlines()
    for r in reused:
        line=lines[r['reused_line']-1];old=json.loads(line)
        assert hashlib.sha256(line.encode()).hexdigest()==r['reused_line_sha256']
        assert s.par(old)==s.par(r) and all(old[k]==r[k] for k in ['ensemble_hash','C','w','I_AB','chi_BE','K_raw','radial_order','width_order'])
    check('reused_exact_nodes_original_line_hashes',True,len(reused))
    check('baseline_recomputed_before_search',s.ROWS[0]['stage']=='baseline_recomputed' and s.ROWS[0]['origin']=='NEW_EXACT_EVALUATION'
        and max(abs(v) for v in s.read(s.OUT/'baseline_regression.json')['differences'].values())<1e-12)
    # Reject prohibited inputs at the staging boundary without calling an evaluator.
    rejected=0
    for p in [(*s.BASE[:7],.0005,.92),(*s.BASE[:6],1.,.005,.92)]:
        try:s.allowed(p)
        except AssertionError:rejected+=1
    check('prohibited_parameters_rejected_without_evaluation',rejected==2)
    for path in s.OUT.glob('catalog_*.csv'):
        with path.open() as f:rows=list(csv.DictReader(f))
        assert len(rows)==233 and {r['ensemble_hash'] for r in rows}==set(roster)
    check('every_catalog_complete_exact_source_roster',True,len(list(s.OUT.glob('catalog_*.csv'))))
    for path in s.OUT.glob('alternating_*.csv'):
        with path.open() as f:rows=list(csv.DictReader(f))
        assert {float(r['start']) for r in rows}=={.05,.1,.165,.3}
        assert all(float(r['delta_K'])>=-1e-13 for r in rows)
    check('finite_catalog_P1_P2_ascent_logged',True)
    unique={r['ensemble_hash']+repr(s.par(r)):r for r in selection['recommendations']}
    for i,r in enumerate(unique.values()):
        p=s.par(r);c=roster[r['ensemble_hash']];ch,mo=s.n.optical(*p[:6],p[8]);fine=s.n.previous.power_conserving(ch,64)
        check(f'selected_{i}_moments_width32_64',max(abs(mo[k]-fine[k]) for k in ['m1','mh'])<2e-10)
        z=s.n.previous.evaluate(c,mo,eta_det=p[6],epsilon_det=p[7],grid=129)
        check(f'selected_{i}_full_Z33_129',abs(z['chi_BE']-r['chi_BE'])<2e-8)
        entropy=precise_entropy(r['a'],r['b'],r['Z_worst'],110)
        check(f'selected_{i}_entropy110',abs(float(entropy['chi'])-r['chi_BE'])<2e-12)
        direct=s.n.previous.pooled_mi(c,ch,eta_det=p[6],epsilon_det=p[7],radial_order=128,width_order=16)
        fast=s.n.fading_mi(c,p,128,16)
        check(f'selected_{i}_direct_vs_Fourier_MI',abs(direct['I_AB_pooled']-fast['I_AB_actual'])<5e-12)
        half=s.n.fading_mi(c,p,512,48,spacing=.0125)
        check(f'selected_{i}_half_output_spacing',abs(half['I_AB_actual']-r['I_AB'])<5e-12)
        t,w=s.n.quadrature(p,256,32)
        check(f'selected_{i}_passive_support_and_outage',0<=t.min()<=t.max()<=ch['eta_atm'] and abs(w.sum()-1)<1e-13 and w[t==0].sum()>=mo['P0'])
    conv=s.read(s.OUT/'convergence.json')
    check('eight_selected_actual_MI_convergence',len(conv)==8 and all(r['observed_MI_change']<2e-6 for r in conv),max(r['observed_MI_change'] for r in conv))
    check('positive_margin_if_any',all(r['K_512']>2*.95*r['observed_MI_change'] for r in conv if r['K_512']>0),
        dict(positive_scenarios=selection['nominal_positive_count'],vacuous_if_none=True))
    with (s.OUT/'robustness.csv').open() as f:robust=list(csv.DictReader(f))
    for i in range(8):
        rows=[r for r in robust if int(r['detector_index'])==i];nominal=selection['detector_scenario_best'][i]
        assert len(rows)==7 and len({r['ensemble_hash'] for r in rows})==1
        for r in rows:
            if r['case'].startswith('noise_'):continue
            expected={'nominal':(1,1),'jitter_plus10':(1.1,1),'centering_plus10':(1,1.1),'joint_plus10':(1.1,1.1),'joint_plus20':(1.2,1.2)}[r['case']]
            assert float(r['jitter_urad'])==nominal['jitter_urad']*expected[0] and float(r['sigma_h_m'])==nominal['sigma_h_m']*expected[1]
            assert float(r['eta_det'])==nominal['eta_det'] and float(r['epsilon_det'])==nominal['epsilon_det']
    check('all_requested_robustness_cases_fixed_source_and_other_parameters',True,56)
    start=s.read(s.OUT/'startup_manifest.json');allowed={f'paper_uav_hap_cvqkd/{p}' for p in ['docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/PROJECT_STATE.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']}
    changed=[p for p,h in start['protected'].items() if p not in allowed and s.sha(s.ROOT.parent/p)!=h]
    check('all_historical_sources_configs_caches_frozen_results_preserved',not changed,dict(protected_files=len(start['protected']),unexpected=changed))
    check('model_import_bytes_unchanged',all(s.sha(s.ROOT/p)==h for p,h in start['imported_model_sha256'].items()))
    protocol=s.read(s.OUT/'protocol.json')
    check('producer_matches_recorded_protocol_hash',s.sha(s.OUT/'run_study.py')==protocol['producer_sha256'])
    for p in s.OUT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
    check('python_producers_AST',True)
    s.save('validation.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,rows=len(s.ROWS),new_evaluations=len(s.ROWS)-len(reused),reused_evaluations=len(reused),security_valid=False,hardware_validated=False))
    print('VALIDATION PASS',len(checks),'rows',len(s.ROWS),'reused',len(reused),flush=True)


if __name__=='__main__':main()
