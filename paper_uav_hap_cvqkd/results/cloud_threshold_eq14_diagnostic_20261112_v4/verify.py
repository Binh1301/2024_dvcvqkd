"""Read-only integrity and numerical-record checks; no source/MI/optimizer runs."""
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def rows(name):
    with (OUT/name).open(encoding='utf-8') as f:return list(csv.DictReader(f))


def verify():
    for name,h in read('artifact_hashes.json').items():assert sha(OUT/name)==h,name
    protected=read('protected_inputs.json')
    for name,h in protected.items():assert sha(ROOT/name)==h,name
    design=read('design_receipt.json')
    for name,h in design['producer_hashes'].items():assert sha(ROOT/name)==h,name
    final=read('final_provenance.json')
    for name,h in final['source_hashes'].items():assert sha(ROOT/name)==h,name
    validation=read('adapter_validation.json')
    assert validation['status']=='CURRENTLY_VERIFIED_PASS'
    for name,d in validation['executed_preserved_functions'].items():assert sha(ROOT/name)==d['sha256'],name
    assert validation['archive_sources']==209 and validation['unarchived_sources']==3
    assert len(validation['checkpoints'])==9 and validation['saved_A0_replay_max_error']<2e-10
    for c in validation['checkpoints']:
        assert c['max_float_Holevo_error']<1e-11 and c['missing_source_float_Holevo_error']<1e-11
        assert c['maximum_difference']<=1e-10 and c['upper_bound_violation']<=1e-11
    proto=json.loads((ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/protocol.json').read_text())
    pool=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/source_pool.csv'
    assert sha(pool)==proto['source_pool_sha256']
    with pool.open() as f:sources=list(csv.DictReader(f))
    by_source={s['ensemble_hash']:s for s in sources};assert len(by_source)==212
    for s in sources:
        path=ROOT/s['source_path'];assert sha(path)==s['source_sha256']
        payload=json.loads(path.read_text())
        assert float(payload['C'])==float(s['C']) and float(payload['w'])==float(s['w'])
        assert payload['V_A_hex']==s['VA_hex'] and payload['nu_mb_raw_hex']==s['nu_raw_hex']
    resume=read('resume_provenance.json');origin=Path(resume['source'])
    assert sha(origin/'design_receipt.json')==resume['source_design_sha256']
    for f in resume['reused']:
        assert sha(OUT/f['file'])==sha(origin/f['file'])==f['sha256']
        assert sha(OUT/f['csv'])==sha(origin/f['csv'])==f['csv_sha256']
    total=0;full=0;bound=0;unresolved=0;largest_bound=-math.inf
    summaries={}
    for job in read('geometry_jobs.json'):
        name=job['id'];s=read(name+'_summary.json');summaries[name]=s
        records=rows(name+'_evaluations.csv');total+=len(records)
        assert s['zenith_deg']==job['zenith_deg'] and s['distance_km']==job['distance_km']
        assert abs(s['distance_km']-19/math.cos(math.radians(s['zenith_deg'])))<1e-12
        is_full=s.get('scan_scope','FULL_201_RAW_SWEEP')=='FULL_201_RAW_SWEEP'
        full+=int(is_full);bound+=int(not is_full)
        for row in records:
            a,k,i,chi=(float(row[f]) for f in ['A_db','K_raw','I_AB','chi_BE'])
            assert all(math.isfinite(v) for v in [a,k,i,chi])
            assert abs(k-(.95*i-chi))<1e-15
            assert row['security_valid']=='False'
            assert row['ensemble_hash'] in by_source
            source=by_source[row['ensemble_hash']]
            assert float(row['VA'])==float(source['VA']) and float(row['nu_raw'])==float(source['nu_raw'])
            m=s['channel']['moments'];factor=10**(-a/10)
            expected_t=factor*m['mh']**2
            expected_noise=factor*((m['m1']-m['mh']**2)*float(row['VA'])+.0186*m['m1'])+.005*m['M0']
            assert abs(float(row['t'])-expected_t)<1e-14
            assert abs(float(row['N_effective'])-expected_noise)<1e-14
            if row['mode']=='fixed_clear_optimum':assert row['ensemble_hash']==s['clear_selection']['ensemble_hash']
            else:
                assert int(row['catalog_size'])==212
                if row['catalog_maximum_resolved']!='True':
                    unresolved+=1;assert float(row['catalog_K_upper'])<0 and k<0
                assert float(row['catalog_K_upper'])>=k
        for mode,search in s['searches'].items():
            selected={float(r['A_db']):float(r['K_raw']) for r in records if r['mode']==mode}
            required=np.arange(0,100.1,.5) if is_full else [0.,.5]
            assert all(float(a) in selected for a in required)
            br=search['diagnostic_crossing_interval_db']
            if br:
                assert br[1]-br[0]<=.001 and selected[br[0]]>0 and selected[br[1]]<=0
                assert search['clear_raw_skr']>0
            else:assert search['clear_raw_skr']<=0 and search['zero_additional_margin']
            assert search['threshold_outage_rule_certified'] is False
        if not is_full:
            checks=s['full_range_bound_checks'];assert len(checks)==200
            np.testing.assert_array_equal([r['A_db'] for r in checks],np.arange(.5,100.1,.5))
            assert max(r['catalog_upper_bound'] for r in checks)<-1e-10
            largest_bound=max(largest_bound,max(r['catalog_upper_bound'] for r in checks))
    assert len(summaries)==257 and full==79 and bound==178
    positions=rows('critical_threshold_map.csv');assert len(positions)==5000
    table=rows('critical_thresholds.csv');assert len(table)==514
    maps=np.load(OUT/'threshold_maps.npz',allow_pickle=False)
    for row in positions:
        ix,iy=int(row['ix']),int(row['iy']);s=summaries[row['geometry']]
        x,y=20+40*ix,20+40*iy
        assert float(row['x_m'])==x and float(row['y_m'])==y
        assert abs(float(row['zenith_deg'])-math.degrees(math.atan2(math.hypot(x-1000,y-1000),19000)))<1e-12
        value=s['searches'][row['mode']]['diagnostic_crossing_midpoint_db']
        assert float(row['A_crit_db'])==value
        key='fixed_db' if row['mode']=='fixed_clear_optimum' else 'catalog_reselected_db'
        assert maps[key][iy,ix]==value
    for key in ['fixed_db','catalog_reselected_db']:
        assert maps[key].shape==(50,50) and np.isfinite(maps[key]).all()
        np.testing.assert_array_equal(maps[key],maps[key][::-1,:])
        np.testing.assert_array_equal(maps[key],maps[key][:,::-1])
    assert 'Ran 11 tests' in (OUT/'unit_tests.log').read_text() and '\nOK\n' in (OUT/'unit_tests.log').read_text()
    assert read('visual_qa.json')['status']=='CURRENTLY_VERIFIED_PASS'
    assert len(list(OUT.glob('figure_*.pdf')))==len(list(OUT.glob('figure_*.png')))==3
    for p in OUT.glob('figure_*.png'):
        with Image.open(p) as im:assert min(im.info['dpi'])>399
    return dict(status='CURRENTLY_VERIFIED_PASS',scope='conditional Eq14 numerical/software diagnostic only',
        geometry_groups=257,positions=2500,full_raw_sweep_groups=full,root_and_bound_groups=bound,
        selected_evaluation_rows=total,unresolved_negative_catalog_rows=unresolved,
        largest_later_grid_upper_bound=largest_bound,protected_previous_files=len(protected),
        focused_tests=11,finite_catalog=212,array_inputs=209,unavailable_bound_only=3,
        minimum_grid_crossing_db=float(maps['fixed_db'].min()),maximum_grid_crossing_db=float(maps['fixed_db'].max()),
        maximum_fixed_vs_catalog_grid_difference_db=float(np.max(abs(maps['fixed_db']-maps['catalog_reselected_db']))),
        continuous_global_reoptimization='NOT_RUN',security_certification=False)


if __name__=='__main__':print(json.dumps(verify(),indent=2))
