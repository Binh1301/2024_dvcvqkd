"""TEST_ONLY pipeline fixtures borrowing real sealed Phase5E clear rates."""
from dataclasses import replace
import copy
from pathlib import Path
import numpy as np
import pytest

from uav_qkd.config import load_config
from uav_qkd.experiments import run_methods
from uav_qkd.evaluation import evaluate_path

ROOT=Path(__file__).parents[1]


def test_technical_integration_entrypoint_exists():
    from uav_qkd.phase5f_integration import build_test_scenario,load_phase5e_lookup
    assert callable(build_test_scenario) and callable(load_phase5e_lookup)


@pytest.fixture(scope='module')
def source():
    from uav_qkd.phase5f_integration import load_phase5e_lookup
    c=load_config(ROOT/'configs/integration/phase5f_test_only.yaml')
    return load_phase5e_lookup(c['lookup'],Path(c['_config_path']).parent)


@pytest.fixture
def config():return load_config(ROOT/'configs/integration/phase5f_test_only.yaml')


def test_phase5e_raw_source_is_pinned_and_has_exact_geometry(source):
    assert len(source.points)==2601
    row=source.node([1000.,1000.])
    assert row['rate']==.00495533778991275 and row['transmittance']>0
    assert source.hap_m==(1000.,1000.,20000.) and source.uav_altitude_m==1000.
    with pytest.raises(ValueError,match='exact'):source.node([1001.,1000.])


def test_clear_sky_static_compatibility_all_four_methods(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    config['fixture']['cloud']['clusters']=[]
    s,ctx=build_test_scenario(config,source=source)
    assert s.z.all()
    static=replace(s,rates=np.array([source.node(q)['rate'] for q in s.graph.positions]))
    assert run_methods(s,config,.5,measure=False)==run_methods(static,config,.5,measure=False)
    assert ctx['provider'].effective_rate([1000.,1000.],1000.)==source.node([1000.,1000.])['rate']


def test_fully_blocked_LOS_has_zero_signals_contribution_and_penalty(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    config['fixture']['cloud']['clusters']=[dict(amplitude=10.,center=[1000.,1000.],sigma=[1e6,1e6])]
    s,ctx=build_test_scenario(config,source=source)
    assert not s.z.any() and np.all(s.rates>0)  # clear retained-use rate is NEVER masked a second time.
    slot=ctx['provider'].slot([1000.,1000.],2.,s.m0)
    assert slot['effective_rate']==slot['transmittance']==slot['valid_signals']==slot['raw_contribution']==0
    for run in run_methods(s,config,.5,measure=False):
        for sol in run['solutions'].values():
            assert sol['key_bits']==sol['asymptotic_bits']==sol['valid_signals']==sol['penalty_bits']==0


def test_dynamic_time_indexing_signal_accounting_and_reproducibility(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    a,ctx=build_test_scenario(config,source=source);b,_=build_test_scenario(config,source=source)
    np.testing.assert_array_equal(a.z,b.z);np.testing.assert_array_equal(a.rates,b.rates)
    center=a.graph.initial
    assert a.z[0,center]==0 and a.z[1,center]==1  # t=dt=2, then4 seconds; never t=0.
    assert ctx['provider'].effective_rate([1000.,1000.],2.)==0.
    assert ctx['provider'].effective_rate([1000.,1000.],4.)==source.node([1000.,1000.])['rate']
    assert run_methods(a,config,.5,measure=False)==run_methods(b,config,.5,measure=False)
    stationary=evaluate_path(a,[center]*5)
    n=a.m0*sum(a.z[:,center]);S=n*source.node([1000.,1000.])['rate']
    assert stationary['valid_signals']==n
    assert stationary['asymptotic_bits']==S
    assert stationary['penalty_bits']==pytest.approx(7*np.sqrt(n*np.log2(2/a.epsilon)))
    assert [r['time_s'] for r in stationary['series']]==[2.,4.,6.,8.]


def test_LOS_can_block_while_UAV_endpoint_is_clear(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    config['fixture']['cloud']['clusters']=[dict(amplitude=10.,center=[1031.,1000.],sigma=[2.,2.])]
    _,ctx=build_test_scenario(config,source=source)
    q=[1040.,1000.]
    assert ctx['field'].evaluate([q],0.)[0]<config['fixture']['cloud']['threshold_mg_m3']
    assert ctx['provider'].slot(q,0.,1e8)['z_los']==0


def test_shared_inputs_stationary_speed_and_energy(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    s,_=build_test_scenario(config,source=source)
    runs=run_methods(s,config,.5,measure=False)
    assert len(runs)==4 and all(r['status']=='FEASIBLE' for r in runs)
    assert len(set(runs[0]['solutions']['P2']['path_indices']))==1
    for r in runs:
        for sol in r['solutions'].values():
            assert sol['energy_j']<=s.budget
            evaluate_path(s,sol['path_indices'])
    left,right=0,2
    with pytest.raises(ValueError,match='speed'):
        evaluate_path(s,[s.graph.initial,left,right])


def test_wrong_geometry_and_historical_fallback_are_rejected(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario,load_phase5e_lookup
    bad=copy.deepcopy(config);bad['fixture']['hap_m'][0]=0.
    with pytest.raises(ValueError,match='geometry'):build_test_scenario(bad,source=source)
    bad=copy.deepcopy(config['lookup']);bad['directory']=str(ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106')
    with pytest.raises(ValueError,match='Phase5E'):load_phase5e_lookup(bad,ROOT)


def test_pending_and_paper_inputs_cannot_be_run(config):
    from uav_qkd.phase5f_integration import build_test_scenario
    pending=load_config(ROOT/'configs/integration/phase5f_candidate.yaml')
    with pytest.raises(ValueError,match='Missing'):build_test_scenario(pending)
    config['mode']='paper'
    with pytest.raises(ValueError,match='paper-mode'):build_test_scenario(config)


def test_test_only_output_cannot_enter_research_results(config,tmp_path,monkeypatch):
    from uav_qkd import phase5f_integration as f
    with pytest.raises(ValueError,match='TEST_ONLY'):
        f.run_test_only(config,ROOT/'results/not_allowed')
    monkeypatch.setattr(f,'TEST_ARTIFACT_ROOT',tmp_path)
    out=tmp_path/'phase5f_fixture'
    r=f.run_test_only(config,out)
    assert r['data_status'].startswith('TEST_ONLY') and r['paper_mode']=='NOT_RUN'
    assert r['cloud_candidate_author_approved'] is False
    assert len(r['runs'])==4
    with pytest.raises(FileExistsError):f.run_test_only(config,out)


def test_package_coverage_and_hash_mismatch_are_refused(config,tmp_path):
    from uav_qkd.phase5f_integration import load_phase5e_lookup
    source_dir=(Path(config['_config_path']).parent/config['lookup']['directory']).resolve()
    (tmp_path/'phase5e_package_manifest.json').write_bytes((source_dir/'phase5e_package_manifest.json').read_bytes())
    ref=dict(config['lookup'],directory=str(tmp_path))
    with pytest.raises(ValueError,match='coverage'):load_phase5e_lookup(ref)
    ref['package_manifest_sha256']='0'*64
    with pytest.raises(ValueError,match='Phase5E'):load_phase5e_lookup(ref)


def test_continuous_cloud_and_reference_windows_do_not_define_graph(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    from uav_qkd.cloud_candidate import cloud_reference_windows
    s,ctx=build_test_scenario(config,source=source)
    field=ctx['field'];q=np.array([[1002.,1000.]])
    np.testing.assert_allclose(field.evaluate(q,.3),field.evaluate(q+np.array([[1.5,0.]]),0.))
    windows=cloud_reference_windows(field)
    assert [w['bounds_m'][0] for w in windows]==[0.,1500.,5000.]
    assert all(w['clwc_mg_m3'].shape==(50,50) for w in windows)
    assert len(s.graph.positions)==3


def test_missing_fixture_signals_are_rejected_without_defaults(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    config['fixture']['finite_size']['m0']=None
    with pytest.raises(ValueError,match='Missing.*m0'):build_test_scenario(config,source=source)


def test_supplied_source_payload_cannot_override_official_rates(source,config):
    from types import MappingProxyType
    from uav_qkd.phase5f_integration import build_test_scenario
    spoof=replace(source,_nodes=MappingProxyType({q:(1.,*v[1:]) for q,v in source._nodes.items()}))
    with pytest.raises(ValueError,match='source'):build_test_scenario(config,source=spoof)


def test_per_cluster_drift_override_is_refused(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    config['fixture']['cloud']['clusters'][0]['velocity']=[0.,0.]
    with pytest.raises(ValueError,match='drift'):build_test_scenario(config,source=source)


def test_null_finite_block_rejected_as_missing_not_filled(source,config):
    from uav_qkd.phase5f_integration import build_test_scenario
    config['fixture']['finite_size']=None
    with pytest.raises(ValueError,match='Missing'):build_test_scenario(config,source=source)
