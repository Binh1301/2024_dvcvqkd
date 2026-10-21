"""Verify saved evidence and immutable inputs; no channel/source/MI/SKR rerun."""
import csv
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))


def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    checks=[]

    def check(name,condition):
        assert condition,name
        checks.append(name)

    startup=load('startup_manifest.json')
    changed=[]
    for name,value in startup['protected_files'].items():
        if sha(ROOT/name)!=value:
            changed.append(name)
    check('all_preexisting_files_preserved_except_explicit_task_ledgers',set(changed)<=set(startup['allowed_changed']))
    for name,value in load('input_manifest.json').items():
        check('input_hash:'+name,sha(ROOT/name)==value)
    roster=rows('source_roster.csv')
    for r in roster:
        check('source_full_file_hash:'+r['ensemble_hash'],sha(ROOT/r['source_path'])==r['source_sha256'])
    source_by_hash={r['ensemble_hash']:r for r in roster}
    check('catalog_membership',len(roster)==218 and sum(r['family']=='MB' for r in roster)==182
          and sum(r['family']=='Uniform' for r in roster)==36 and len(source_by_hash)==218)
    check('all_numerical_self_checks_pass',load('numerical_test_receipt.json')['status']=='CURRENTLY_VERIFIED_PASS')
    summary=load('summary.json')
    check('producer_immutable',summary['producer_sha256']==sha(OUT/'run_sweep.py')
          ==load('environment.json')['producer_sha256'])
    check('reference_gate_pass',load('reference_gate.json')['status']=='CURRENTLY_VERIFIED_PASS')
    check('producer_checks_pass',all(r['status']=='CURRENTLY_VERIFIED_PASS' for r in load('checks.json')))
    sweep=rows('skr_vs_zenith_angle.csv')
    candidate_rows=rows('all_candidate_evaluations.csv')
    detailed=rows('skr_vs_zenith_angle_detailed.csv')
    check('complete_initial_grid',[float(r['zenith_deg']) for r in sweep if r['grid_stage']=='initial_2deg']==list(range(0,61,2)))
    check('counts',len(sweep)==summary['total_angles'] and len(candidate_rows)==218*len(sweep)==summary['candidate_evaluations']
          and len(detailed)==3*len(sweep))
    groups={float(r['zenith_deg']):[] for r in sweep}
    for r in candidate_rows:
        groups[float(r['zenith_deg'])].append(r)
        source=source_by_hash[r['ensemble_hash']]
        assert all(float(r[k])==float(source[k]) for k in ('VA','nu_raw','C','w'))
        assert r['source_sha256']==source['source_sha256']
        assert abs(.95*float(r['I_AB_2D'])-float(r['chi_BE'])-float(r['K_raw']))<1e-17
        assert max(abs(float(r['MI_GH'+str(order)])-float(r['MI_GH64'])) for order in (16,32,64))<2e-13
        assert float(r['uncertainty_min_eigenvalue'])>0
        assert min(float(r[k]) for k in ('nu_1','nu_2','nu_3'))>=1
    check('all_saved_evaluations_source_GH_and_physicality',True)
    channels=load('channel_by_angle.json')
    for r in sweep:
        deg=float(r['zenith_deg']);group=groups[deg]
        assert len({x['ensemble_hash'] for x in group})==218
        uni=max((x for x in group if x['family']=='Uniform'),key=lambda x:float(x['K_raw']))
        mb=max((x for x in group if x['family']=='MB'),key=lambda x:float(x['K_raw']))
        fixed=next(x for x in group if float(x['nu_raw'])==.165 and float(x['VA'])==5.475)
        assert float(r['Uniform_K_raw'])==float(uni['K_raw']) and float(r['Uniform_optimal_VA'])==float(uni['VA'])
        assert float(r['Optimized_MB_K_raw'])==float(mb['K_raw'])
        assert float(r['MB_optimal_nu_raw'])==float(mb['nu_raw']) and float(r['MB_optimal_VA'])==float(mb['VA'])
        assert float(r['Fixed_MB_K_raw'])==float(fixed['K_raw'])
        assert abs(float(r['distance_km'])-19/math.cos(math.radians(deg)))<1e-11
        ch=channels[str(int(deg)) if deg.is_integer() and str(int(deg)) in channels else str(deg)]
        m1,mh=float(ch['mean_eta']),float(ch['mean_sqrt_eta'])
        assert abs(float(ch['eta_atm'])-.92**(1/math.cos(math.radians(deg))))<1e-15
        for x in group:
            noise=(m1-mh*mh)*float(x['VA'])+.0186*m1
            assert abs(noise-float(x['N']))<1e-18
        decomp=[x for x in detailed if float(x['zenith_deg'])==deg]
        assert [x['ensemble_hash'] for x in decomp]==[uni['ensemble_hash'],fixed['ensemble_hash'],mb['ensemble_hash']]
    check('all_angle_geometry_channel_noise_and_raw_argmax',True)
    by_angle={float(r['zenith_deg']):r for r in sweep}
    for op,key in zip(rows('operational_zenith_angles.csv'),('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw')):
        positive=[r for r in sweep if float(r[key])>0]
        negative=[r for r in sweep if float(r[key])<=0]
        assert op['maximum_tested_positive_deg']==('' if not positive else positive[-1]['zenith_deg'])
        assert op['first_tested_nonpositive_deg']==('' if not negative else negative[0]['zenith_deg'])
        if op['operational_lower_deg']:
            lo,hi=float(op['operational_lower_deg']),float(op['operational_upper_deg'])
            assert hi-lo<=.25 and float(by_angle[lo][key])>0>=float(by_angle[hi][key])
            assert float(op['distance_lower_km'])==float(by_angle[lo]['distance_km'])
            assert float(op['distance_upper_km'])==float(by_angle[hi]['distance_km'])
    check('direct_operational_brackets_and_no_invented_crossing',True)
    for r in load('plot_metadata.json'):
        assert r['displayed']==(r['positive'] if r['scale']=='log' else len(sweep))
    check('raw_negative_values_preserved_log_excludes_nonpositive',True)
    renderer=load('render_receipt.json')
    check('final_layout_renderer_provenance',renderer['layout_only'] and not renderer['scientific_recalculation']
          and renderer['CSV_sha256']==sha(OUT/'skr_vs_zenith_angle.csv')
          and renderer['producer_sha256']==sha(OUT/'render_figures.py')
          and all(r['data_points']==len(sweep) for r in renderer['figures']))
    figure_info=[]
    for name in ('skr_vs_zenith_angle','skr_vs_zenith_angle_linear'):
        with Image.open(OUT/(name+'.png')) as im:
            check('PNG_resolution:'+name,min(im.info['dpi'])>=349 and im.width>=3000)
            figure_info.append(dict(name=name,pixels=list(im.size),dpi=list(im.info['dpi'])))
        data=(OUT/(name+'.pdf')).read_bytes()
        check('vector_PDF:'+name,data.startswith(b'%PDF') and b'/Subtype /Image' not in data)
    check('completed_no_pending_work',load('checkpoint.json')['status']=='COMPLETE')
    check('visual_review_recorded',load('visual_review.json')['status']=='CURRENTLY_VERIFIED_PASS')
    artifact_hashes={(p.relative_to(ROOT).as_posix()):sha(p) for p in sorted(OUT.rglob('*'))
                     if p.is_file() and p.name!='validation_receipt.json'}
    receipt=dict(status='CURRENTLY_VERIFIED_PASS',checks=len(checks),check_names=checks,
        protected_preexisting_files=len(startup['protected_files']),allowed_changed_files=changed,
        unchanged_preexisting_files=len(startup['protected_files'])-len(changed),
        artifact_sha256=artifact_hashes,figures=figure_info,saved_artifact_verification_only=True,
        scope='MANUSCRIPT_STYLE_NUMERICAL_COMPARISON_NOT_PHYSICAL_HOMODYNE_SECURITY')
    target=OUT/'validation_receipt.json'
    if target.exists():
        check('existing_receipt_matches',json.loads(target.read_text(encoding='utf-8'))==receipt)
    else:
        target.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('CURRENTLY_VERIFIED_PASS:',len(checks),'saved-evidence checks;',receipt['unchanged_preexisting_files'],
          'old files unchanged;',len(changed),'authorized ledger updates')


if __name__=='__main__':
    main()
