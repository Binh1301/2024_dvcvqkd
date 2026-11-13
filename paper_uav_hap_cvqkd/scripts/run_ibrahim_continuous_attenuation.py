"""Deterministically transform saved stationary clouds; never generate clouds/QKD."""
from pathlib import Path
import argparse
from dataclasses import asdict
import hashlib
import json
import platform
import sys
import time
import csv
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ibrahim_continuous_attenuation import (
    AttenuationScenario, gaussian_to_clwc, visibility_km, kim_exponent,
    specific_attenuation_db_km, path_attenuation_db, transmittance_from_db,
    layer_intersection, representative_link_attenuation, pooled_pearson,
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def write_csv(path, rows):
    rows = list(rows)
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def summary(a):
    positive = a[a > 0]
    result = dict(mean=float(a.mean()), std=float(a.std()), minimum=float(a.min()),
                  maximum=float(a.max()), zero_fraction=float(np.mean(a == 0)),
                  unique_values=int(np.unique(a).size))
    for q, value in zip([.5,.9,.95,.99,.999], np.quantile(a,[.5,.9,.95,.99,.999])):
        result[f'q{q:g}'] = float(value)
    result['positive_mean'] = float(positive.mean()) if positive.size else None
    result['positive_q95'] = float(np.quantile(positive,.95)) if positive.size else None
    return result


def run(config, output):
    started = time.perf_counter()
    cfg = json.loads(config.read_text(encoding='utf-8-sig'))
    if (output/'metadata.json').exists() or (output/'cloud_clwc.npz').exists():
        raise FileExistsError('Use a new output directory; existing outputs are immutable')
    output.mkdir(parents=True, exist_ok=True)
    scenarios = [AttenuationScenario(**s) for s in cfg['scenarios']]
    if len(set(s.name for s in scenarios)) != len(scenarios):
        raise ValueError('scenario names must be unique')
    primary = next(s for s in scenarios if s.name == cfg['primary_scenario'])
    if cfg['gamma0_mode'] != 'reuse_saved_gamma_fixed' or cfg['equation6_at_6_km'] != 'upper_branch_1.3_explicit_gap_completion':
        raise ValueError('Unsupported threshold or equation-6 completion')
    source, metapath = ROOT/cfg['input_npz'], ROOT/cfg['input_metadata']
    manifestpath = ROOT/cfg['input_manifest']
    manifest = json.loads(manifestpath.read_text())
    for f in [source, metapath]:
        if sha(f) != manifest[f.name]:
            raise ValueError(f'Original stationary artifact hash mismatch: {f}')
    with np.load(source,allow_pickle=False) as data:
        g, time_s, x, y = (data[k] for k in ['X','time_s','x_m','y_m'])
        meta = json.loads(str(data['metadata_json']))
    external_meta = json.loads(metapath.read_text())
    if meta != external_meta:
        raise ValueError('Embedded and external source metadata disagree')
    c = meta['parameters']
    required = dict(nx=50,ny=50,slots=1000,dx_m=40.,dy_m=40.,dt_s=1.,
                    vx_m_s=-5.,vy_m_s=0.,tau_c_s=300.,seed=20261111)
    if any(c[k] != v for k,v in required.items()):
        raise ValueError('Source does not match requested experiment')
    if g.dtype != np.float64 or g.shape != (1000,50,50) or not np.isfinite(g).all():
        raise ValueError('Invalid latent array')
    np.testing.assert_array_equal(time_s,np.arange(1000,dtype=float))
    np.testing.assert_array_equal(x,(np.arange(50)+.5)*40)
    np.testing.assert_array_equal(y,(np.arange(50)+.5)*40)
    gamma = float(meta['gamma_fixed'])
    np.testing.assert_equal(gamma,np.quantile(g[0],.7))
    producers = ['src/ibrahim_continuous_attenuation.py',
                 'scripts/run_ibrahim_continuous_attenuation.py',
                 'scripts/plot_ibrahim_continuous_attenuation.py',
                 'scripts/report_ibrahim_continuous_attenuation.py',
                 'tests/test_ibrahim_continuous_attenuation.py']
    write_json(output/'design_receipt.json', {
        'scope':'UNCALIBRATED_CONTINUOUS_ATTENUATION_DIAGNOSTIC_ONLY',
        'input_sha256':sha(source),'input_metadata_sha256':sha(metapath),
        'input_manifest_sha256':sha(manifestpath),'config_sha256':sha(config),
        'producer_hashes':{p:sha(ROOT/p) for p in producers},
        'settings':cfg,'source_parameters':c,'gamma_fixed':gamma,
        'pre_transform':True,'gaussian_regeneration_count':0,'rng_draw_count':0,
        'acceptance':'Deterministic formula/unit/hash checks; empirical correlations are descriptive, not pass/fail target fits'})
    write_json(output/'configuration.json',cfg)
    common = dict(time_s=time_s,x_m=x,y_m=y)
    saved_samples = {}
    scenario_rows, all_time_rows, distribution_rows = [], [], []
    reference_arrays = None
    for scenario in scenarios:
        s_started = time.perf_counter()
        l = gaussian_to_clwc(g,scenario.l0_g_m3,gamma)
        w = specific_attenuation_db_km(l,scenario.droplet_cm3,cfg['wavelength_nm'])
        a = path_attenuation_db(w,scenario.thickness_km,cfg['reference_zenith_deg'])
        t = transmittance_from_db(a)
        row = {**asdict(scenario),'label':'ILLUSTRATIVE_UNCALIBRATED',
               'CLWC':summary(l),'specific_db_km':summary(w),
               'attenuation_db':summary(a),'transmittance':summary(t)}
        # Infinite visibility is a limiting sentinel, never written as array/JSON data.
        v = visibility_km(l[l>0],scenario.droplet_cm3)
        row['positive_visibility_km'] = {'minimum':float(v.min()),'maximum':float(v.max())}
        row['positive_visibility_regime_counts'] = {'V_lt_6':int(np.sum(v<6)),
                   'V_eq_6':int(np.sum(v==6)),'V_6_to_50_inclusive':int(np.sum((v>=6)&(v<=50))),
                   'V_gt_50':int(np.sum(v>50))}
        row['transform_seconds'] = time.perf_counter()-s_started
        scenario_rows.append(row)
        for k in range(len(time_s)):
            all_time_rows.append(dict(scenario=scenario.name,slot=k,time_s=time_s[k],
                mean_db=float(a[k].mean()),max_db=float(a[k].max()),std_db=float(a[k].std()),
                q95_db=float(np.quantile(a[k],.95)),zero_fraction=float(np.mean(l[k]==0)),
                mean_clwc_g_m3=float(l[k].mean()),mean_transmittance=float(t[k].mean())))
        # Exact ECDF evaluations at these value nodes, including its zero atom.
        ordered = np.sort(a.ravel())
        nodes = np.unique(np.r_[0.,np.linspace(0,a.max(),300),np.quantile(a,np.linspace(0,1,300))])
        for value,count in zip(nodes,np.searchsorted(ordered,nodes,side='right')):
            distribution_rows.append(dict(scenario=scenario.name,attenuation_db=float(value),
                                          count_le=int(count),sample_count=a.size,cdf=float(count/a.size)))
        saved_samples[scenario.name+'_A_db'] = a[cfg['snapshot_slots']]
        saved_samples[scenario.name+'_CLWC_g_m3'] = l[cfg['snapshot_slots']]
        if scenario == primary:
            reference_arrays = l,a,t,w
    l,a,t,w = reference_arrays
    np.savez_compressed(output/'cloud_clwc.npz',clwc_g_m3=l,**common,
        gamma_fixed=np.array(gamma),l0_g_m3=np.array(primary.l0_g_m3),units=np.array('g/m^3'))
    np.savez_compressed(output/'cloud_attenuation_db.npz',attenuation_db=a,
        specific_db_km=w,**common,units=np.array('dB'),reference_zenith_deg=np.array(cfg['reference_zenith_deg']))
    np.savez_compressed(output/'cloud_transmittance.npz',transmittance=t,**common,units=np.array('dimensionless power ratio'))
    np.savez_compressed(output/'scenario_snapshots.npz',**saved_samples,
                        snapshot_slots=cfg['snapshot_slots'],x_m=x,y_m=y)
    write_csv(output/'time_statistics.csv',all_time_rows)
    write_csv(output/'empirical_cdf.csv',distribution_rows)
    flat_scenarios = [{**{k:r[k] for k in ['name','l0_g_m3','droplet_cm3','thickness_km','label']},
                      **{'A_'+k:v for k,v in r['attenuation_db'].items()},
                      'CLWC_positive_mean':r['CLWC']['positive_mean'],
                      'T_min':r['transmittance']['minimum']} for r in scenario_rows]
    write_csv(output/'scenario_summary.csv',flat_scenarios)
    fields = dict(G=g,L=l,A=a,T=t)
    spatial, temporal, advected = [], [], []
    for field,z in fields.items():
        for lag in cfg['spatial_lags_cells']:
            for axis in ['x','y']:
                aa,bb = ((z[:,:,:50-lag],z[:,:,lag:]) if axis=='x'
                         else (z[:,:50-lag,:],z[:,lag:,:]))
                spatial.append(dict(field=field,axis=axis,lag_cells=lag,lag_m=lag*40,
                                    pearson_r=pooled_pearson(aa,bb),pairs=aa.size))
        for lag in cfg['temporal_lags_slots']:
            aa,bb=z[:len(z)-lag],z[lag:]
            temporal.append(dict(field=field,lag_slots=lag,lag_s=float(lag),
                                 pearson_r=pooled_pearson(aa,bb),pairs=aa.size))
        for shift in [-80,-40,0,40,80]:
            cell=shift//40
            aa=z[:-8,:,max(0,-cell):min(50,50-cell)]
            bb=z[8:,:,max(0,cell):min(50,50+cell)]
            advected.append(dict(field=field,lag_s=8,hx_m=shift,
                                 pearson_r=pooled_pearson(aa,bb),pairs=aa.size))
    write_csv(output/'spatial_correlation.csv',spatial)
    write_csv(output/'temporal_correlation.csv',temporal)
    write_csv(output/'wind_lag_correlation.csv',advected)
    probes=[]
    for iy,ix in cfg['probe_indices_yx']:
        for k in range(len(time_s)):
            probes.append(dict(iy=iy,ix=ix,x_m=x[ix],y_m=y[iy],slot=k,time_s=time_s[k],
                               G=g[k,iy,ix],CLWC_g_m3=l[k,iy,ix],attenuation_db=a[k,iy,ix],T=t[k,iy,ix]))
    write_csv(output/'probe_time_series.csv',probes)
    edges=np.linspace(0,a.max(),101)
    counts,_=np.histogram(a,bins=edges)
    write_csv(output/'attenuation_histogram.csv',
              (dict(left_db=edges[i],right_db=edges[i+1],count=int(counts[i]),
                    probability=float(counts[i]/a.size)) for i in range(len(counts))))
    source_boundary=json.loads((source.parent/'boundary_validation.json').read_text())
    # Recompute unwrapped source bounds from the recorded source grid, no RNG.
    dom=source_boundary
    margins=[];backtraces=[]
    for seconds in [0,400,999,1000]:
        intervals={}
        for axis,index in [('x',1),('y',0)]:
            step=c['d'+axis+'_m']; origin=dom['crop_index_origin_yx'][index]*step
            velocity=c['v'+axis+'_m_s'];extent=dom['synthetic_extent_xy_m'][0 if axis=='x' else 1]
            interval=[origin-velocity*seconds,origin+c['n'+axis]*step-velocity*seconds]
            margins.append(min(interval[0],extent-interval[1]));intervals[axis]=interval
        backtraces.append(dict(time_s=seconds,source_intervals_m=intervals))
    assert min(margins)>=c['guard_m']-1e-9
    boundary={'status':'CURRENTLY_VERIFIED_PASS','backtraces':backtraces,
        'minimum_guard_m':min(margins),'mapping_is_pointwise':True,'new_advection_or_wrap_count':0,
        'scope':dom['limitation']}
    write_json(output/'boundary_validation.json',boundary)
    geometry_examples={
        'full_vertical':representative_link_attenuation(l[0],x,y,[1000,1000,1000],[1000,1000,20000],2000,2500,100),
        'cloud_below_UAV':representative_link_attenuation(l[0],x,y,[1000,1000,3000],[1000,1000,20000],2000,2500,100),
        'slant_coordinate_demo':layer_intersection([500,1000,1000],[10000,1000,20000],2000,2500),
        'partial_layer':layer_intersection([1000,1000,2250],[1000,1000,20000],2000,2500),
        'assumptions':'Illustrative endpoints and cloud altitudes only, not loaded from QKD; maps use vertical reference. Midpoint approximation is not a path integral.'}
    write_json(output/'geometry_examples.json',geometry_examples)
    assert np.isfinite(l).all() and np.isfinite(a).all() and np.isfinite(t).all()
    assert np.all(l>=0) and np.all(a>=0) and np.all((t>0)&(t<=1))
    np.testing.assert_array_equal(a[l==0],np.zeros(np.sum(l==0)))
    np.testing.assert_array_equal(t[l==0],np.ones(np.sum(l==0)))
    np.testing.assert_allclose(-10*np.log10(t),a,rtol=1e-12,atol=1e-14)
    np.testing.assert_array_equal(l,gaussian_to_clwc(g,primary.l0_g_m3,gamma))
    assert sha(source)==manifest[source.name]
    checks={name:True for name in ['input_hash_unchanged','saved_seed_parameters_match',
      'deterministic_repeat_equal','time_coordinate_order_exact','grid_units_exact',
      'nonnegative_CLWC_A','strictly_positive_T_le_one','zero_CLWC_A0_T1',
      'no_nonfinite_stored_arrays','A_T_inverse_consistent','fixed_gamma_all_slots',
      'continuous_valued_no_binary_blockage','no_geometric_reentry_inherited_rechecked']}
    if (output/'protected_inputs.json').exists():
        protected=json.loads((output/'protected_inputs.json').read_text())
        assert all(sha(ROOT/f)==h for f,h in protected.items())
        checks['all_protected_old_files_unchanged']=True
    else:
        protected={}
    validation={'status':'CURRENTLY_VERIFIED_PASS','checks':checks,
        'protected_files':len(protected),'input_sha256':sha(source),'gaussian_regeneration_count':0,
        'binary_blockage_count':0,'clipping_or_saturation_count':0,
        'max_A_T_inverse_error_db':float(np.max(abs(-10*np.log10(t)-a))),
        'finite_visibility_policy':'L=0 gives +inf as mathematical sentinel, excluded from stored arrays; A=0,T=1',
        'physical_validation':'NOT_RUN_UNCALIBRATED','actual_QKD_geometry_validation':'NOT_RUN_REFERENCE_MAP_ONLY'}
    write_json(output/'validation.json',validation)
    metadata={'model_name':cfg['model_name'],'scope':'ILLUSTRATIVE_UNCALIBRATED',
        'source':cfg['input_npz'],'source_sha256':sha(source),'source_parameters':c,
        'gamma_fixed':gamma,'reference_zenith_deg':cfg['reference_zenith_deg'],
        'primary_scenario':asdict(primary),'wavelength_nm':cfg['wavelength_nm'],
        'scenarios':scenario_rows,'Gaussian':summary(g),'boundary':boundary,
        'correlation_estimator':'Pairwise Pearson pooled over valid nonwrapped pairs; means computed separately per pair set; one correlated mission, no iid confidence intervals.',
        'paper_eq6_gap_completion':'V=6 ->1.3; printed branches jump at 6 and 50; continuous-valued, not globally continuous.',
        'transform_and_analysis_seconds':time.perf_counter()-started,
        'Python':platform.python_version(),'numpy':np.__version__,'source_gaussian_regenerated':False}
    write_json(output/'metadata.json',metadata)
    print(json.dumps({'status':validation['status'],'frames':len(g),'scenarios':len(scenarios),
                     'seconds':metadata['transform_and_analysis_seconds'],
                     'reference_A_db':next(r for r in scenario_rows if r['name']==primary.name)['attenuation_db']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/ibrahim_continuous_attenuation.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.config.resolve(),args.output.resolve())
