"""Read-only verification of sealed attenuation delivery; no random draws."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import sys
import numpy as np
from PIL import Image
import matplotlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.ibrahim_continuous_attenuation import pooled_pearson, layer_intersection


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(out):
    manifest=json.loads((out/'artifact_hashes.json').read_text(encoding='utf-8'))
    for name,value in manifest.items():
        assert sha(out/name)==value,f'artifact changed: {name}'
    protected=json.loads((out/'protected_inputs.json').read_text())
    for name,value in protected.items():
        assert sha(ROOT/name)==value,f'old input/artifact changed: {name}'
    receipt=json.loads((out/'design_receipt.json').read_text(encoding='utf-8'))
    final=json.loads((out/'verification_provenance.json').read_text())
    for name,value in receipt['producer_hashes'].items():
        original=out/final['initial_producer_snapshots'][name] if name in final['initial_producer_snapshots'] else ROOT/name
        assert sha(original)==value,f'initial producer changed: {name}'
    for name,value in final['source_hashes'].items():
        assert sha(ROOT/name)==value,f'final source changed: {name}'
    cfg=json.loads((out/'configuration.json').read_text(encoding='utf-8'))
    assert receipt['settings']==cfg
    assert sha(ROOT/'configs/ibrahim_continuous_attenuation.json')==receipt['config_sha256']
    assert sha(ROOT/cfg['input_npz'])==receipt['input_sha256']
    assert sha(ROOT/cfg['input_metadata'])==receipt['input_metadata_sha256']
    assert sha(ROOT/cfg['input_manifest'])==receipt['input_manifest_sha256']
    references=json.loads((out/'references.json').read_text(encoding='utf-8'))
    assert sha(references['paper']['local_pdf'])==references['paper']['local_pdf_sha256']
    with np.load(ROOT/cfg['input_npz'],allow_pickle=False) as d:
        g=d['X'];time_s=d['time_s'];x=d['x_m'];y=d['y_m']
        old_meta=json.loads(str(d['metadata_json']))
    datasets={}
    for filename,key in [('cloud_clwc.npz','clwc_g_m3'),
                         ('cloud_attenuation_db.npz','attenuation_db'),
                         ('cloud_transmittance.npz','transmittance')]:
        with np.load(out/filename,allow_pickle=False) as d:
            for name in d.files:
                if np.issubdtype(d[name].dtype,np.number):assert np.isfinite(d[name]).all(),name
            z=d[key];assert z.dtype==np.float64 and z.shape==g.shape==(1000,50,50)
            for axis,original in [('time_s',time_s),('x_m',x),('y_m',y)]:
                np.testing.assert_array_equal(d[axis],original)
            datasets[key]=z
            if filename=='cloud_attenuation_db.npz':w=d['specific_db_km']
    l,a,t=(datasets[k] for k in ['clwc_g_m3','attenuation_db','transmittance'])
    assert np.all(l>=0) and np.all(a>=0) and np.all((t>0)&(t<=1))
    gamma=old_meta['gamma_fixed']
    scenario=next(s for s in cfg['scenarios'] if s['name']==cfg['primary_scenario'])
    # Independent literal evaluation, not a call to the optical implementation.
    expected_l=scenario['l0_g_m3']*np.maximum(g-gamma,0)
    np.testing.assert_array_equal(l,expected_l)
    positive=l>0
    v=1.002/np.power(l[positive]*scenario['droplet_cm3'],.6473)
    exponent=np.where(v<6,.585*np.cbrt(v),np.where(v<=50,1.3,1.6))
    expected_w=np.zeros(g.shape)
    expected_w[positive]=3.91/v*np.power(cfg['wavelength_nm']/550,-exponent)
    np.testing.assert_allclose(w,expected_w,rtol=3e-14,atol=0)
    expected_a=expected_w*scenario['thickness_km']/math.cos(math.radians(cfg['reference_zenith_deg']))
    np.testing.assert_allclose(a,expected_a,rtol=3e-14,atol=0)
    np.testing.assert_allclose(t,10**(-a/10),rtol=1e-15,atol=0)
    np.testing.assert_allclose(-10*np.log10(t),a,rtol=1e-12,atol=1e-14)
    np.testing.assert_array_equal(a[~positive],0*a[~positive]);np.testing.assert_array_equal(t[~positive],np.ones(np.sum(~positive)))
    np.testing.assert_array_equal(time_s,np.arange(1000))
    assert cfg['wavelength_nm']==1550 and cfg['reference_zenith_deg']==0
    assert receipt['rng_draw_count']==receipt['gaussian_regeneration_count']==0
    validation=json.loads((out/'validation.json').read_text())
    assert validation['status']=='CURRENTLY_VERIFIED_PASS' and all(validation['checks'].values())
    assert validation['clipping_or_saturation_count']==validation['binary_blockage_count']==0
    fields=dict(G=g,L=l,A=a,T=t)
    def read(name):
        with (out/name).open(encoding='utf-8') as s:return list(csv.DictReader(s))
    for row in read('spatial_correlation.csv'):
        z=fields[row['field']];lag=int(row['lag_cells'])
        aa,bb=((z[:,:,:50-lag],z[:,:,lag:]) if row['axis']=='x' else (z[:,:50-lag,:],z[:,lag:,:]))
        assert aa.size==int(row['pairs'])
        assert abs(pooled_pearson(aa,bb)-float(row['pearson_r']))<1e-14
    for row in read('temporal_correlation.csv'):
        z=fields[row['field']];lag=int(row['lag_slots'])
        aa,bb=z[:1000-lag],z[lag:]
        assert aa.size==int(row['pairs'])
        assert abs(pooled_pearson(aa,bb)-float(row['pearson_r']))<1e-14
    for row in read('wind_lag_correlation.csv'):
        z=fields[row['field']];cell=int(row['hx_m'])//40
        aa=z[:-8,:,max(0,-cell):min(50,50-cell)];bb=z[8:,:,max(0,cell):min(50,50+cell)]
        assert abs(pooled_pearson(aa,bb)-float(row['pearson_r']))<1e-14
    for row in read('probe_time_series.csv'):
        k,iy,ix=(int(row[n]) for n in ['slot','iy','ix'])
        assert float(row['attenuation_db'])==a[k,iy,ix]
        assert float(row['CLWC_g_m3'])==l[k,iy,ix]
    for row in read('time_statistics.csv'):
        if row['scenario']==scenario['name']:
            k=int(row['slot'])
            assert float(row['mean_db'])==float(a[k].mean())
            assert float(row['max_db'])==float(a[k].max())
    counts=read('attenuation_histogram.csv')
    assert sum(int(r['count']) for r in counts)==a.size
    ordered=np.sort(a.ravel())
    for row in read('empirical_cdf.csv'):
        if row['scenario']==scenario['name']:
            count=int(np.searchsorted(ordered,float(row['attenuation_db']),side='right'))
            assert count==int(row['count_le'])
            assert abs(count/a.size-float(row['cdf']))<1e-15
    # Check every scenario snapshot against the original G with independent arithmetic.
    with np.load(out/'scenario_snapshots.npz',allow_pickle=False) as d:
        gg=g[cfg['snapshot_slots']]
        for sc in cfg['scenarios']:
            ll=sc['l0_g_m3']*np.maximum(gg-gamma,0)
            np.testing.assert_array_equal(d[sc['name']+'_CLWC_g_m3'],ll)
            pp=ll>0;vv=1.002/(ll[pp]*sc['droplet_cm3'])**.6473
            xx=np.where(vv<6,.585*np.cbrt(vv),np.where(vv<=50,1.3,1.6))
            aa=np.zeros(ll.shape);aa[pp]=3.91/vv*(1550/550)**(-xx)*sc['thickness_km']
            np.testing.assert_allclose(d[sc['name']+'_A_db'],aa,rtol=3e-14,atol=0)
    boundary=json.loads((out/'boundary_validation.json').read_text())
    assert boundary['status']=='CURRENTLY_VERIFIED_PASS' and boundary['new_advection_or_wrap_count']==0
    assert boundary['minimum_guard_m']>=1000
    c=old_meta['parameters'];dom=old_meta['domain']
    for row in boundary['backtraces']:
        for axis,j in [('x',1),('y',0)]:
            origin=dom['crop_index_origin_yx'][j]*c['d'+axis+'_m']
            v=c['v'+axis+'_m_s'];dt=row['time_s']
            expected=[origin-v*dt,origin+c['n'+axis]*c['d'+axis+'_m']-v*dt]
            assert row['source_intervals_m'][axis]==expected
    geom=json.loads((out/'geometry_examples.json').read_text())
    assert not geom['cloud_below_UAV']['geometry']['intersects']
    assert geom['cloud_below_UAV']['attenuation_db']==0 and geom['cloud_below_UAV']['transmittance']==1
    assert geom['slant_coordinate_demo']==layer_intersection([500,1000,1000],[10000,1000,20000],2000,2500)
    assert abs(geom['partial_layer']['path_length_km']-.25)<1e-14
    zenith_sensitivity=[]
    for angle in cfg['zenith_comparison_deg']:
        factor=1/math.cos(math.radians(angle));aa=a*factor
        tt=np.power(10.,-aa/10)
        assert np.all((tt>0)&(tt<=1))
        np.testing.assert_allclose(tt,t**factor,rtol=2e-14,atol=0)
        zenith_sensitivity.append(dict(zenith_deg=angle,path_factor=factor,
            mean_attenuation_db=float(aa.mean()),maximum_attenuation_db=float(aa.max()),
            minimum_transmittance=float(tt.min()),scope='same representative column only'))
    text=(out/'regression_tests.log').read_text(encoding='utf-8')
    assert 'Ran 49 tests' in text and '\nOK\n' in text and 'FAILED (' not in text
    old=json.loads((out/'previous_packages_validation.json').read_text())
    assert len(old)==3 and all(r['returncode']==0 for r in old)
    exports=json.loads((out/'pdf_export_validation.json').read_text())
    visual=json.loads((out/'visual_qa.json').read_text())
    assert exports['status']==visual['status']=='CURRENTLY_VERIFIED_PASS'
    assert len(exports['files'])==7 and len(visual['inspected_pdf_previews'])==7
    for f in out.glob('figure_*.png'):
        with Image.open(f) as im: assert min(im.info['dpi'])>399
    assert len(list(out.glob('figure_*.png')))==len(list(out.glob('figure_*.pdf')))==7
    render=json.loads((out/'render_receipt.json').read_text())
    assert render['plotter_sha256']==sha(ROOT/'scripts/plot_ibrahim_continuous_attenuation.py')
    # GIF quantization is for display only. Check actual field pixels, row orientation and fixed scale.
    palette=(matplotlib.colormaps['magma'](np.linspace(0,1,252))[:,:3]*255).astype(np.uint8)
    with Image.open(out/'cloud_continuous_attenuation.gif') as animation:
        assert animation.n_frames==1000 and animation.info['duration']==50
        for k in [0,400,999]:
            animation.seek(k)
            actual=np.asarray(animation.convert('RGB'))[42:342,20:320]
            indices=np.rint(np.flipud(a[k])/a.max()*251).astype(np.uint8)
            expected=np.repeat(np.repeat(palette[indices],6,axis=0),6,axis=1)
            np.testing.assert_array_equal(actual,expected)
    return {'status':'CURRENTLY_VERIFIED_PASS','scope':'read-only, no Gaussian or attenuation simulation rerun',
        'sealed_artifacts':len(manifest),'protected_existing_files':len(protected),
        'frames':1000,'new_unit_tests':16,'old_cloud_regression_tests':33,'total_unit_tests':49,
        'scenarios':len(cfg['scenarios']),'PNG_PDF_pairs':7,'GIF_frames':1000,
        'zenith_reference_sensitivity':zenith_sensitivity,
        'physical_calibration':'NOT_RUN_UNCALIBRATED','QKD_integration':'NOT_RUN'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    print(json.dumps(verify(p.parse_args().output.resolve()),indent=2))
