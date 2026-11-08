"""Orchestration fixtures only; scientific benchmarking is run separately."""
import json
import pytest
from pathlib import Path


def test_representative_selection_is_deterministic_and_keeps_fifty_geometries():
    from uav_qkd.lookup_benchmark import benchmark_points
    from uav_qkd.skr_pilot import LOOKUP,read_rows
    rows=read_rows(LOOKUP/'skr_map.csv')
    a=benchmark_points(rows,50)
    assert len(a)==50 and a==benchmark_points(rows,50)
    assert len({r['radius2_m2'] for r in a})==50
    assert min(r['radius2_m2'] for r in a)==0 and max(r['radius2_m2'] for r in a)==2000000
    for bad in (49,101,True):
        with pytest.raises(ValueError):benchmark_points(rows,bad)


def test_full_permission_must_bind_scope_config_and_candidate_pool(tmp_path):
    from uav_qkd.lookup_benchmark import require_full_approval
    with pytest.raises(ValueError,match='approval'):require_full_approval(None,'config','pool')
    f=tmp_path/'approval.json'
    f.write_text(json.dumps(dict(author_approved=True,scope='PHASE5D_FULL_LOOKUP',config_sha256='config',candidate_pool_sha256='pool')))
    require_full_approval(f,'config','pool')
    f.write_text(json.dumps(dict(author_approved='true',scope='PHASE5D_FULL_LOOKUP',config_sha256='config',candidate_pool_sha256='pool')))
    with pytest.raises(ValueError):require_full_approval(f,'config','pool')


def test_mode_comparison_rejects_changed_winner_or_signed_raw_rate():
    from uav_qkd.lookup_benchmark import compare_modes
    c=dict(family='MB',ensemble_hash='source',VA=1.,nu_raw=.3,eta_f=.2,xi_f=.1,I_AB=.3,chi_BE=.4,K_raw=-.115)
    r=dict(point={'point_id':'p0'},candidates=[c],winners={'MB':c})
    assert compare_modes([r],[r])['passed']
    bad=dict(r,candidates=[dict(c,K_raw=.115)])
    assert not compare_modes([r],[bad])['passed']


def test_full_cli_without_approval_cannot_create_output(tmp_path):
    from uav_qkd.lookup_benchmark import full_regeneration
    config=tmp_path/'config.json';config.write_text(json.dumps({'candidate_pool_sha256':'pool'}))
    out=tmp_path/'must-not-exist'
    with pytest.raises(ValueError,match='approval'):
        full_regeneration(config,out,approval=None)
    assert not out.exists()


def test_partial_write_is_archived_before_retry(tmp_path):
    from uav_qkd.lookup_benchmark import _write_new
    path=tmp_path/'point.json'
    (tmp_path/'point.json.partial').write_text('incomplete')
    _write_new(path,{'complete':True})
    assert json.loads(path.read_text())=={'complete':True}
    assert [f.read_text() for f in tmp_path.glob('*.interrupted_*')]==['incomplete']


@pytest.mark.parametrize('fault',['family','evidence','security'])
def test_checkpoint_rejects_removed_family_or_promoted_labels(fault):
    from copy import deepcopy
    from uav_qkd.lookup_benchmark import _validate_record
    from uav_qkd.skr_pilot import read,ROOT,sha
    d=ROOT/'results/phase5d_benchmark_20261108';r=read(d/'serial/b000.json');m=read(d/'input_manifest.json')
    args=('serial',r['point'],sha(d/'input_manifest.json'),m['config_sha256'],r['active_effective_protocol'],m['roster'])
    _validate_record(r,*args)
    bad=deepcopy(r)
    if fault=='family':bad['winners']={}
    elif fault=='evidence':bad['candidates'][0]['source_evidence_class']='VERIFIED_EXACT'
    else:bad['security_valid']=True
    with pytest.raises(ValueError):_validate_record(bad,*args)


def test_complete_valid_point_without_seal_resumes_without_evaluation(tmp_path,monkeypatch):
    from uav_qkd import lookup_benchmark as b
    from uav_qkd.skr_pilot import read,ROOT,sha
    d=ROOT/'results/phase5d_benchmark_20261108';r=read(d/'serial/b000.json');m=read(d/'input_manifest.json')
    stage=tmp_path/'serial';stage.mkdir();(stage/'b000.json').write_bytes((d/'serial/b000.json').read_bytes())
    monkeypatch.setattr(b,'_ENGINE',{'protocol':r['active_effective_protocol']})
    monkeypatch.setattr(b,'_evaluate_job',lambda job:pytest.fail('Must recover a validated complete record'))
    records,resource=b._run_stage(tmp_path,[r['point']],'serial',m['config_sha256'],sha(d/'input_manifest.json'),m)
    assert records==[r] and resource['fresh_evaluator_calls']==0
    assert (stage/'b000.seal.json').exists()


def test_export_round_trips_loader_provenance_and_is_idempotent(tmp_path):
    import numpy as np
    from uav_qkd.lookup_benchmark import _export_map
    from uav_qkd.skr_lookup import SKRLookup
    from uav_qkd.skr_pilot import sha
    # SOFTWARE export fixtures only; no simulated research result.
    rows=[dict(x_m=x,y_m=y,skr_bits_per_use=r,K_raw_bits_per_use=r,
               MB_source_evidence_class='SOFTWARE_TEST_ONLY',Uniform_source_evidence_class='SOFTWARE_TEST_ONLY')
          for x,y,r in [(0.,0.,-.1),(1.,0.,.2),(0.,1.,.3)]]
    meta=dict(config_sha256='test-config',input_manifest_sha256='test-input',candidate_pool_sha256='test-pool')
    _export_map(tmp_path,rows,meta)
    for suffix in ('csv','npz'):
        table=SKRLookup.load(tmp_path/('skr_map.'+suffix),coordinate_units='m',rate_units='bits/use')
        np.testing.assert_array_equal(table.rates,[-.1,.2,.3])
    with np.load(tmp_path/'skr_map.npz',allow_pickle=False) as data:
        for name,value in meta.items():assert data[name].item()==value
        assert data['MB_source_evidence_class'].tolist()==['SOFTWARE_TEST_ONLY']*3
    old=sha(tmp_path/'skr_map.npz');_export_map(tmp_path,rows,meta)
    assert sha(tmp_path/'skr_map.npz')==old
    with (tmp_path/'skr_map.csv').open('a') as f:f.write('tampered')
    with pytest.raises(ValueError):_export_map(tmp_path,rows,meta)


def test_owned_resume_can_finish_summary_without_output_seal(tmp_path,monkeypatch):
    from uav_qkd import lookup_benchmark as b
    monkeypatch.setattr(b,'ROOT',tmp_path)
    path=tmp_path/'results/phase5d_fixture';path.mkdir(parents=True)
    (path/'config.json').write_text('{}');(path/'summary.json').write_text('{}')
    assert b._output_directory(path,resume=True)==path.resolve()


def test_full_controller_software_export_can_resume_after_interrupted_seal(tmp_path,monkeypatch):
    """Controller/export fixture: native initialization/evaluation are NEVER called."""
    from uav_qkd import lookup_benchmark as b
    config=b.full_configuration();config_path=tmp_path/'approved_config.json'
    config_path.write_text(json.dumps(config))
    approval=tmp_path/'TEST_ONLY_approval.json'
    approval.write_text(json.dumps(dict(author_approved=True,scope='PHASE5D_FULL_LOOKUP',
        config_sha256=b.sha(config_path),candidate_pool_sha256=config['candidate_pool_sha256'])))
    output=tmp_path/'software_export';output.mkdir()
    def prepare(out,job,**kwargs):return output,'test-config','test-input',{'input_sha256':{},'producer_sha256':{}},{}
    def stage(out,points,*args,**kwargs):
        def winner(family):return dict(K_raw=-.1,I_AB=.2,chi_BE=.3,eta_f=.2,xi_f=.1,VA=1.,nu_raw=.3,
                                     ensemble_hash='TEST_'+family,source_evidence_class='SOFTWARE_TEST_ONLY')
        return [dict(point=p,winners={f:winner(f) for f in ('MB','Uniform')}) for p in points],{'native_evaluator_calls':0,'scope':'SOFTWARE_TEST_ONLY'}
    monkeypatch.setattr(b,'_prepare',prepare);monkeypatch.setattr(b,'_run_stage',stage)
    seal=b._seal
    monkeypatch.setattr(b,'_seal',lambda out:(_ for _ in ()).throw(RuntimeError('simulated interruption')))
    with pytest.raises(RuntimeError,match='interruption'):
        b.full_regeneration(config_path,output,approval=approval)
    assert (output/'summary.json').exists() and not (output/'output_manifest.json').exists()
    old=b.sha(output/'skr_map.npz')
    monkeypatch.setattr(b,'_seal',seal)
    result=b.full_regeneration(config_path,output,approval=approval,resume=True)
    assert result['spatial_points']==2601 and result['candidates_per_context']==212
    assert b.sha(output/'skr_map.npz')==old
    assert (output/'output_manifest.json').exists()
