"""Read-only saved-artifact verification, without stochastic simulation."""
from pathlib import Path
import csv,hashlib,json,sys
import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from src.stochastic_cloud_grf import GRFConfig,CirculantGRF,relative_intensity


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify():
    manifest=json.loads((OUT/'artifact_hashes.json').read_text())
    for name,digest in manifest.items():assert sha(OUT/name)==digest,f'artifact: {name}'
    protected=json.loads((OUT/'protected_inputs.json').read_text())
    for name,digest in protected.items():assert sha(ROOT/name)==digest,f'protected: {name}'
    receipt=json.loads((OUT/'design_receipt.json').read_text(encoding='utf-8'))
    for name,digest in receipt['producer_hashes'].items():assert sha(ROOT/name)==digest,f'producer: {name}'
    assert sha(ROOT/'configs/stochastic_cloud_grf.json')==receipt['config_sha256']
    renderer=json.loads((OUT/'render_receipt.json').read_text())
    assert sha(ROOT/'scripts/plot_stochastic_cloud_grf.py')==renderer['producer_sha256']
    settings=receipt['settings'];c=GRFConfig(**settings['simulation']);embedding=CirculantGRF(c)
    r=json.loads((OUT/'validation.json').read_text());meta=json.loads((OUT/'metadata.json').read_text())
    d=np.load(OUT/'cloud_fields.npz',allow_pickle=False);ens=np.load(OUT/'ensemble_validation.npz',allow_pickle=False)
    for name in ('latent_field','relative_intensity','diagnostic_mask'):
        assert d[name].shape==(c.slots,c.ny,c.nx)
        assert np.isfinite(d[name]).all()
    assert d['latent_field'].dtype==d['relative_intensity'].dtype==np.float64
    assert d['diagnostic_mask'].dtype==np.uint8
    np.testing.assert_array_equal(d['time_s'],np.arange(c.slots)*c.dt_s)
    np.testing.assert_array_equal(d['x_m'],(np.arange(c.nx)+.5)*c.dx_m)
    np.testing.assert_array_equal(d['y_m'],(np.arange(c.ny)+.5)*c.dy_m)
    np.testing.assert_array_equal(d['diagnostic_mask'],d['latent_field']>meta['theta_c_actual'])
    np.testing.assert_array_equal(d['relative_intensity'],relative_intensity(d['latent_field'],meta['theta_c_actual'],c))
    assert (d['relative_intensity']>=0).all()
    np.testing.assert_array_equal(d['relative_intensity']>0,d['diagnostic_mask'])
    for name in ('metrics','material_correlation','space_time_covariance','spatial_covariance','histogram'):
        assert np.isfinite(ens[name]).all()
    assert len(ens['seeds'])>=10 and len(set(ens['seeds']))==len(ens['seeds'])
    np.testing.assert_allclose(d['latent_field'].mean((1,2)),ens['metrics'][0,:,0],atol=1e-13)
    np.testing.assert_allclose(d['latent_field'].var((1,2)),ens['metrics'][0,:,1],atol=1e-13)
    np.testing.assert_array_equal(d['diagnostic_mask'].mean((1,2)),ens['metrics'][0,:,3])
    assert embedding.boundary_receipt()==r['boundary']
    assert embedding.spectrum_receipt['minimum_eigenvalue']>0
    for key in ('minimum_eigenvalue','maximum_eigenvalue','target_marginal_variance'):
        assert abs(embedding.spectrum_receipt[key]-r['spectrum'][key])<1e-12*max(1,abs(r['spectrum'][key]))
    assert r['spectrum']['negative_eigenvalues']==r['spectrum']['clipped_eigenvalues']==0
    assert abs(r['expected_ROI_population_variance']-embedding.expected_roi_variance())<1e-14
    support=json.loads((OUT/'covariance_support_validation.json').read_text())
    for axis in ('x','y'):
        expected=(getattr(c,'n'+axis)-1)*getattr(c,'d'+axis+'_m')+abs(getattr(c,'v'+axis+'_m_s'))*(c.slots-1)*c.dt_s
        assert support['all_exported_pairs'][axis]['max_abs_h_minus_v_m_dt_m']==expected
        assert expected<support['all_exported_pairs'][axis]['embedding_half_period_m']
    assert support['status']=='CURRENTLY_VERIFIED_PASS'
    for row in csv.DictReader((OUT/'space_time_covariance.csv').open()):
        hx,hy,lag=float(row['hx_m']),float(row['hy_m']),int(row['lag'])
        assert abs(float(row['theory'])-embedding.covariance(hx,hy,lag))<1e-14
        assert abs(float(row['embedding_theory'])-float(row['theory']))<1e-14
    sigma=settings['validation']['seed_SE_multiplier'];tol=settings['validation']['numerical_tolerance']
    failed=[]
    for check in r['checks']:
        passed=abs(check['estimate']-check['target'])<=sigma*check['SE']+tol
        assert bool(passed)==check['passed']
        if not passed:failed.append(check)
    assert failed==r['failed_checks']
    frozen=np.load(OUT/'frozen_fields.npz',allow_pickle=False)
    np.testing.assert_array_equal(frozen['latent_field'][0],d['latent_field'][0])
    np.testing.assert_array_equal(frozen['latent_field'][8,:,:-1],frozen['latent_field'][0,:,1:])
    assert r['frozen']['status']=='CURRENTLY_VERIFIED_PASS'
    assert r['frozen']['full_variance_relative_change']==0
    assert r['frozen']['sorted_frozen_values_bitwise_identical']
    assert r['frozen']['eight_slot_displacement_x_m']==-40
    records=list(csv.DictReader((OUT/'track_segments.csv').open()))
    ids=set()
    for record in records:
        key=(int(record['seed']),int(record['track_id']))
        assert key not in ids;ids.add(key)
        first,last=int(record['first_slot']),int(record['last_slot'])
        assert 0<=first<=last<c.slots
        assert float(record['observed_span_s'])==(last-first)*c.dt_s
    log=(OUT/'regression_tests.log').read_bytes()
    log=log.decode('utf-16' if log.startswith(b'\xff\xfe') else 'utf-8-sig')
    assert 'Ran 33 tests' in log and 'OK' in log and 'FAILED (' not in log
    exports=[]
    for path in sorted(OUT.glob('figure_*.png')):
        with Image.open(path) as image:
            assert min(image.info['dpi'])>399
            exports.append({'file':path.name,'pixels':list(image.size),'dpi':image.info['dpi']})
    assert len(exports)==8 and len(list(OUT.glob('figure_*.pdf')))==8
    pdf_qa=json.loads((OUT/'pdf_export_validation.json').read_text())
    assert pdf_qa['status']=='CURRENTLY_VERIFIED_PASS' and len(pdf_qa['PDFs'])==8
    for row in pdf_qa['PDFs']:
        assert row['all_fonts_embedded'] and row['native_text_characters']>0
        if row['file'].startswith(('figure_E','figure_F','figure_G')):assert row['raster_image_XObjects']==0
    with Image.open(OUT/'cloud_1000_slots.gif') as gif:
        assert gif.n_frames==c.slots and gif.info['duration']==50
        for k in (0,400,999):
            gif.seek(k);pixels=np.asarray(gif.convert('RGB'))[34:,200:]
            expected=np.repeat(np.repeat(np.flipud(d['diagnostic_mask'][k]),4,axis=0),4,axis=1)*255
            np.testing.assert_array_equal(pixels,np.repeat(expected[:,:,None],3,axis=2))
    return {'status':'CURRENTLY_VERIFIED_PASS','scope':'artifact/provenance integrity, no stochastic rerun',
            'ensemble_validation_status':r['status'],'ensemble_checks':len(r['checks']),'failed_ensemble_checks':len(failed),
            'independent_seeds':len(ens['seeds']),'protected_existing_files':len(protected),'sealed_artifacts':len(manifest),
            'new_unit_tests':12,'old_model_regression_tests':21,'total_scoped_tests':33,
            'track_segments':len(records),'GIF_frames':c.slots,'PNG_exports':exports}


if __name__=='__main__':print(json.dumps(verify(),indent=2))
