"""Independent saved-artifact verification. No channel/MI/Holevo execution.

--seal is for the initial completion only; the default mode is strictly read-only.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT/'results/skr_vs_zenith_angle_20261019'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def rows(name,base=OUT):
    with (base/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def run_checks():
    checks=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    def close(a,b,atol=1e-17,rtol=2e-14):
        return math.isclose(float(a),float(b),abs_tol=atol,rel_tol=rtol)
    startup=load('startup_manifest.json')
    for name,h in startup['protected_files'].items():
        if name not in startup['allowed_changed']:
            check('protected_bytes:'+name,sha(ROOT/name)==h)
    for name,h in load('input_manifest.json').items():
        check('input_bytes:'+name,sha(ROOT/name)==h)
    check('frozen_mismatch_preserved',sha(ROOT/'docs/FINAL_MODEL_SPEC.md')==startup['frozen_actual']
          and startup['frozen_actual']!=startup['frozen_expected'])
    result=load('diagnostic_results.json')
    check('flags',result['security_status']=='UNVALIDATED_SECURITY_MODEL'
          and result['lifecycle']=='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    check('call_budget',len(rows('validation/new_fixed_source_calls.csv'))==result['new_rate_calls']==78
          and result['new_source_search_calls']==result['new_Cw_calls']==0)
    history=load('validation/execution_history.json')
    check('aborted_attempt_disclosed',history['total_completed_rate_calls_including_aborted_attempt']==81
          and history['aborted_attempt_completed_duplicate_rate_calls']==3
          and history['aborted_attempt_security_only_calls']==1)
    check('failed_assert_resolution_retained',load('validation/attempt_1_failure.json')['status']=='FAILED'
          and load('validation/attempt_1_resolution.json')['physical_covariance'])
    producer=load('validation/numerical_checks.json')
    check('producer_checks_complete',producer['count']==len(producer['checks'])==8408
          and all(r['status']=='CURRENTLY_VERIFIED_PASS' for r in producer['checks']))
    original=rows('skr_vs_zenith_angle_detailed.csv',OLD)
    derived=rows('skr_decomposition.csv')
    check('93_selected_rows',len(original)==len(derived)==93)
    for i,(a,b) in enumerate(zip(original,derived)):
        check('all_original_selected_fields_unchanged:'+str(i),all(a[k]==b[k] for k in a))
        check('independent_K:'+str(i),abs(.95*float(b['I_AB_2D'])-float(b['chi_BE'])-float(b['K_raw']))<1e-17)
    original_curves=rows('skr_vs_zenith_angle.csv',OLD)
    curves=rows('diagnostic_summary.csv')
    check('31_original_angles',[int(r['zenith_deg']) for r in curves]==list(range(0,61,2)))
    for a,b in zip(original_curves,curves):
        for key in ('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw'):
            check(f'curve:{a["zenith_deg"]}:{key}',a[key]==b[key])
    check('signed_curves_not_clipped',all(any(float(r[k])<0 for r in curves)
          for k in ('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw')))
    for key,angle in [('Uniform_K_raw',52),('Fixed_MB_K_raw',48),('Optimized_MB_K_raw',48)]:
        check('discrete_peak:'+key,int(max(curves,key=lambda r:float(r[key]))['zenith_deg'])==angle)
    check('same_source_near_MB_peak',len({(r['Optimized_MB_nu_raw'],r['Optimized_MB_VA'])
           for r in curves if int(r['zenith_deg'])>=24})==1)
    check('same_source_near_Uniform_peak',len({r['Uniform_VA'] for r in curves if int(r['zenith_deg'])>=42})==1)
    moments=rows('channel_moments.csv')
    params=rows('channel_parameters.csv')
    noises=rows('noise_decomposition.csv')
    for m,p,n in zip(moments,params,noises):
        deg=int(m['zenith_deg']);mean,half,t,var,rf=[float(m[k]) for k in
            ('mean_T','mean_sqrt_T','T_eff','variance_sqrt_T','R_f')]
        check('moments:'+str(deg),0<t<=mean<=1 and close(half*half,t) and close(mean-t,var)
              and close(var/t,rf) and close(m['pdf_mass'],1))
        check('geometry:'+str(deg),close(p['distance_km'],19/math.cos(math.radians(deg)),atol=1e-12)
              and close(p['eta_atm'],.92**(1/math.cos(math.radians(deg)))))
        check('pointing:'+str(deg),close(p['sigma_s_squared_m2'],1+(float(p['L_m'])*15.61e-6)**2)
              and close(p['chi2'],float(p['w_eq_m'])**2/(4*float(p['sigma_s_squared_m2']))))
        d=float(p['chi2'])
        reconstructed=math.exp(float(p['sigma_R2'])/4)*(d+.5)**2/(d*(d+1))/float(p['P1'])-1
        check('factorization:'+str(deg),close(reconstructed,rf,atol=5e-15))
        check('input_noise:'+str(deg),close(n['xi_fading'],rf*5.475,atol=3e-15)
              and close(n['xi_physical'],(1+rf)*.0186)
              and close(n['xi_f'],float(n['xi_fading'])+float(n['xi_physical']),atol=3e-15))
        expected=(mean-t)*5.475+.0186*mean
        check('output_noise:'+str(deg),close(n['N_total'],expected)
              and close(t*float(n['xi_f']),expected)
              and close(n['N_total'],float(n['N_fading'])+float(n['N_physical'])))
    decreasing=lambda rs,k:all(float(b[k])<float(a[k]) for a,b in zip(rs,rs[1:]))
    check('Tf_decreases',decreasing(moments,'T_eff'))
    check('meanT_decreases',decreasing(moments,'mean_T'))
    check('Rf_minimum_56',int(min(moments,key=lambda r:float(r['R_f']))['zenith_deg'])==56)
    check('noise_minimum_56',int(min(noises,key=lambda r:float(r['xi_f']))['zenith_deg'])==56)
    check('output_noise_decreases',decreasing(noises,'N_total'))
    fixed=sorted([r for r in derived if r['scheme']=='Fixed MB'],key=lambda r:int(r['zenith_deg']))
    check('MI_decreases',decreasing(fixed,'I_AB_2D'))
    check('Holevo_decreases',decreasing(fixed,'chi_BE'))
    for j,(a,b,r) in enumerate(zip(fixed,fixed[1:],rows('adjacent_skr_differences.csv'))):
        di=float(b['beta_I_AB'])-float(a['beta_I_AB']);dh=float(b['chi_BE'])-float(a['chi_BE'])
        dk=float(b['K_raw'])-float(a['K_raw'])
        check('difference_terms:'+str(j),close(di,r['delta_beta_I_AB'])
              and close(dh,r['delta_chi_BE']) and close(dk,r['delta_K']) and close(dk,di-dh))
        check('rise_fall:'+str(j),(dk>0)==(int(b['zenith_deg'])<=48)
              and di<0 and dh<0 and ((-dh)>-di)==(dk>0))
    controls=rows('controlled_diagnostics.csv')
    for label in {r['check'] for r in controls}:
        group=[r for r in controls if r['check']==label]
        check('control_count:'+label,len(group)==31)
        check('control_decreases:'+label,decreasing(group,'K_raw'))
    orig30=next(r for r in fixed if r['zenith_deg']=='30')
    ref=next(r for r in params if r['zenith_deg']=='30')
    for r in controls:
        deg=int(r['zenith_deg'])
        if r['check'].startswith('A_'):
            original=next(p for p in params if int(p['zenith_deg'])==deg)
            scale=float(original['B'])/float(ref['B'])
            check('control_A_scaling:'+str(deg),close(r['mean_T'],float(orig30['mean_T'])*scale)
                  and close(r['T_eff'],float(orig30['eta_f'])*scale)
                  and close(r['R_f'],orig30['R_f']))
        else:
            actual=next(m for m in moments if int(m['zenith_deg'])==deg)
            check('control_C_nonfading:'+str(deg),close(r['mean_T'],actual['mean_T'])
                  and close(r['T_eff'],actual['mean_T']) and abs(float(r['R_f']))<1e-100
                  and close(r['xi_f'],.0186))
    for r in rows('validation/new_fixed_source_calls.csv'):
        check('controlled_arithmetic:'+r['check']+':'+r['zenith_deg'],
            abs(float(r['beta_I_AB'])-float(r['chi_BE'])-float(r['K_raw']))<2e-17
            and float(r['GH_delta'])<2e-13)
    for r in rows('coordinate_attribution.csv'):
        aa=int(r['from_deg']);bb=int(r['to_deg'])
        ka=float(next(x['K_raw'] for x in fixed if int(x['zenith_deg'])==aa))
        kb=float(next(x['K_raw'] for x in fixed if int(x['zenith_deg'])==bb))
        ba,ab=float(r['K_Tb_Ra']),float(r['K_Ta_Rb'])
        dt=((ba-ka)+(kb-ab))/2;dr=((ab-ka)+(kb-ba))/2
        check(f'coordinate_decomposition:{aa}:{bb}',close(dt,r['contribution_Teff_at_fixed_Rf'])
              and close(dr,r['contribution_Rf_at_fixed_Teff']) and close(dt+dr,kb-ka))
    render=load('render_receipt.json')
    check('plotter_identity',render['producer_sha256']==sha(OUT/'render_figures.py')
          and not render['scientific_evaluators_called'])
    for name,h in render['csv_sha256'].items():
        check('plot_input:'+name,sha(OUT/name)==h)
    check('twelve_figure_pairs',len(render['figures'])==12
          and len(list((OUT/'figures').glob('*.pdf')))==len(list((OUT/'figures').glob('*.png')))==12)
    for fig in render['figures']:
        name=fig['name']
        pdf=(OUT/'figures'/f'{name}.pdf').read_bytes()
        check('vector_PDF:'+name,pdf.startswith(b'%PDF') and b'/Subtype /Image' not in pdf)
        check('Times_embedded:'+name,b'TimesNewRoman' in pdf and b'/FontFile2' in pdf)
        with Image.open(OUT/'figures'/f'{name}.png') as im:
            check('PNG_350dpi:'+name,min(im.info['dpi'])>=349.9 and min(im.size)>800)
        for ai,ax in enumerate(fig['axes']):
            check(f'axis_scale:{name}:{ai}',ax['xscale']=='linear' and ax['yscale']==
                  ('log' if name in ('fig_01_original_semilog','fig_J_relative_fading_factors') else 'linear'))
            for ci,curve in enumerate(ax['curves']):
                src=curve['source'];data=rows(src['csv'])
                data=[r for r in data if all(r[k]==str(v) for k,v in src['selection'].items())]
                xx=[float(r[src['x']]) for r in data]
                yy=[float(r[src['y']]) for r in data]
                yy=[None if src['positive_mask'] and y<=0 else y for y in yy]
                check(f'plotted_points:{name}:{ai}:{ci}',curve['x']==xx and curve['y']==yy)
    check('four_main_figures_exist',all((OUT/'figures'/f'fig_{name}.pdf').exists()
          for name in ['D_channel_moments','E_noise_decomposition','F_MI_Holevo_SKR','G_source_optimization']))
    # Validate local Markdown links; no external access during the read-only verifier.
    for file in ['report_vi.md','README_vi.md','figure_captions_en.md']:
        for target in re.findall(r'\]\(([^)]+)\)',(OUT/file).read_text(encoding='utf-8')):
            if not target.startswith(('https:','http:')):
                check('local_link:'+file+':'+target,(OUT/target).exists())
    return checks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    receipt=OUT/'validation/final_receipt.json'
    if args.seal and receipt.exists():raise FileExistsError('Sealed outputs are immutable')
    checks=run_checks()
    if args.seal:
        v=dict(status='CURRENTLY_VERIFIED_PASS',scope='SAVED_ARTIFACT_ARITHMETIC_PROVENANCE_AND_PLOTTING',
               count=len(checks),checks=checks,scientific_evaluators_called=False)
        (OUT/'validation/independent_checks.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
        report=f'''# Validation report

**CURRENTLY_VERIFIED_PASS for the stated numerical/provenance scope only.**
**UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.**

- 8408 producer checks; {len(checks)} independent saved-artifact checks.
- Original receipt members and historical inputs authenticate; all 5539 startup
  files are protected apart from the five expressly permitted project ledgers.
- 218 authenticated exact sources; 6758 stored candidate rows; 93 stored selected
  decompositions; all 31 original angles and signed curves retained.
- Historical K subtraction residual at most 6.844026213814747e-19 bit/use.
- Geometry/HV/pointing reconstructed at 31 angles; 15 independent PDF integrals;
  exact [0,1] domain and separate outage atom retained without renormalization.
- Saved GH and direct full-symbol-mixture controls reused. Four fixed-source
  probes have zero double-precision K replay residual. Independent 80/110 digit
  entropy checks pass; this is not a complete arbitrary-precision source proof.
- 78 canonical fixed-source rate calls: 62 controls, four probes, 12 attribution
  corners. An earlier aborted diagnostic adds three duplicate completed calls
  and one security-only call; see execution_history.json. No source optimization,
  new C,w, production edit, mobility simulation, or new cloud generation.
- Initial sqrt(T)**2 exact-inequality assertion FAILED at deterministic 2deg;
  covariance was physical. The 110-digit sqrt-square rounding residual was
  4.06070693970504e-115. Failure and resolution are retained in attempt_1_*.
  Only the fixture boundary guard now admits four current-arithmetic ulps;
  GH/SKR tolerances and historical data/evaluators are unchanged. This is not
  an unresolved physicality failure or a retrospective scientific tolerance change.
- Twelve figures: vector PDFs without image XObjects, embedded Times fonts,
  PNGs at 350 dpi. Every numeric plotted curve matches its CSV exactly; only
  the original semilog display masks nonpositive values. No smoothing.
- Figure previews/contact sheet were inspected; panel labels were moved clear
  of early-angle data. Initial render metadata is retained for traceability.
- Stronger security, true-fading MI, full-Z extremum, finite-key, operational
  security, continuous-angle optimum, and general physical validation NOT_RUN.
- Frozen-spec historical hash discrepancy, Objective C USER_STOPPED and all
  lifecycle restrictions remain. No final-test/held-out access, manuscript
  equation edit, commit or push.

The default verify_results.py entry point is read-only and never imports a
scientific evaluator. The final receipt binds all diagnostic artifacts except
itself. Historical ledger edits are permitted only for recording this task.
'''
        (OUT/'validation_report.md').write_text(report,encoding='utf-8')
        hashes={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*'))
                if p.is_file() and p!=receipt and '__pycache__' not in p.parts}
        final=dict(status='CURRENTLY_VERIFIED_PASS',artifact_sha256=hashes,
            independent_checks=len(checks),producer_checks=8408,
            security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
        receipt.write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
        print('SEALED',len(hashes),'artifacts; receipt SHA256',sha(receipt))
    else:
        sealed=load('validation/final_receipt.json')
        for name,h in sealed['artifact_sha256'].items():
            if sha(OUT/name)!=h:raise AssertionError('Sealed artifact changed: '+name)
        if len(checks)!=sealed['independent_checks']:raise AssertionError('Verification coverage changed')
        print('CURRENTLY_VERIFIED_PASS:',len(checks),'independent checks;',len(sealed['artifact_sha256']),'sealed artifacts')


if __name__=='__main__':
    main()
