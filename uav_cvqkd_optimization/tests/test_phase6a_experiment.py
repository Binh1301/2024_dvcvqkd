import copy
from pathlib import Path
import numpy as np
import pytest

from uav_qkd import phase6a_experiment as p


def test_approved_seed_is_new_realization_and_original_recipe_reproduced():
    old = p.generate_cloud(42)
    with np.load(p.ROOT.parent/'dynamic_gaussian_cloud_figure/cloud_field_data.npz') as saved:
        np.testing.assert_array_equal(old['field'], saved['field'])
        np.testing.assert_array_equal(old['cx'], saved['component_x'])
    new = p.generate_cloud(20261108)
    assert new['field'].shape == (50,400)
    assert len(new['amplitude']) == 400
    assert not np.array_equal(old['field'], new['field'])
    assert new['threshold'] == np.percentile(new['field'],90,method='linear')


@pytest.fixture(scope='module')
def built():
    return p.build_scenario(p.read_config())


def test_cardinal_edges_and_derived_energy(built):
    s,ctx = built
    assert len(s.graph.positions)==121 and s.horizon==100
    for i,js in enumerate(s.graph.successors):
        for j in js:
            d=np.abs(s.graph.positions[i]-s.graph.positions[j])
            assert tuple(d) in ((0,0),(200,0),(0,200))
            assert np.linalg.norm(d)/s.graph.dt <= 30
    assert s.budget == 1.1*ctx['rotor']['derived']['hover_power_W']*1000
    assert s.m0==800000 and s.epsilon==3e-8
    assert len(s.graph.successors[s.graph.initial])==5


def test_lambda_is_dimensionally_normalized_and_predeclared(built):
    s,ctx=built
    scale=ctx['lambda']
    assert scale['lambda_bits_per_j']==scale['reward_scale_bits']/scale['energy_scale_j']
    reward=s.m0*s.rates[0]
    energy=s.graph.costs[s.graph.initial,s.graph.initial]
    lam=scale['lambda_bits_per_j']
    normalized=.5*reward/scale['reward_scale_bits']-.5*energy/scale['energy_scale_j']
    assert normalized==pytest.approx(.5/scale['reward_scale_bits']*(reward-lam*energy))


def test_3d_los_spacing_and_end_slot_mask(built):
    s,ctx=built
    nodes,groups=p.los_samples(ctx['model'],s.graph.positions,20)
    assert len(groups)==121
    assert min(len(g) for g in groups)>=101
    # Zenith projects to one horizontal position but still samples the full2km slab.
    zen=groups[s.graph.initial]
    assert len(zen)==101 and np.all(nodes[zen]==[1000,1000])
    assert ctx['preflight']['los_convergence']['disagreements']==0
    assert s.z.shape==(100,121)


def test_finite_reference_and_cloud_erasure_once(built):
    s,ctx=built
    ref=ctx['preflight']['clear_sky_reference']
    assert ref['valid_signals']==8e7
    assert ref['key_bits']>0
    path=[s.graph.initial]*101
    out=p.evaluate_path(s,path)
    clear=sum(int(s.z[k,s.graph.initial]) for k in range(100))
    assert out['valid_signals']==800000*clear
    assert out['asymptotic_bits']==pytest.approx(800000*sum(s.z[k,s.graph.initial]*s.rate_at(k,s.graph.initial) for k in range(100)))
    assert out['penalty_bits']==pytest.approx(7*np.sqrt(out['valid_signals']*np.log2(2/3e-8)))


def test_approval_fails_closed_and_test_guard_unchanged():
    config=p.read_config()
    altered=copy.deepcopy(config);altered['mission']['dt_s']=1
    with pytest.raises(ValueError,match='approval|configuration'):
        p.validate_approval(altered)
    altered=copy.deepcopy(config);altered['mode']='paper'
    with pytest.raises(ValueError,match='paper|NUMERICAL_DIAGNOSTIC'):
        p.validate_approval(altered)
    from uav_qkd.phase5f_integration import build_test_scenario
    with pytest.raises(ValueError):build_test_scenario(config)


def test_output_refuses_history_and_nonempty(tmp_path):
    with pytest.raises(ValueError):p.validate_output(p.ROOT/'results/phase5d_full_target_radial_2proc_PHASE5E_20261108')
    with pytest.raises(ValueError):p.validate_output(tmp_path)


def test_reduced_benchmark_is_separate_and_smaller(built):
    s,_=built
    small=p.reduced_scenario(s)
    assert len(small.graph.positions)==25 and small.horizon==20
    assert small.m0==s.m0 and small.budget==s.budget
    assert np.array_equal(small.graph.positions[small.graph.initial],s.graph.positions[s.graph.initial])


def test_watchdog_returns_failure_without_a_replacement_optimum(built,tmp_path):
    s,ctx=built
    run=p.execute_method(p.reduced_scenario(s),'Pareto DP',ctx['lambda']['lambda_bits_per_j'],
                         tmp_path/'limited',0,4*1024**3)
    assert run['status']=='FAILED_COMPUTATIONAL_LIMIT'
    assert run['reason']=='WALL_CLOCK_LIMIT'
    assert run['solutions']=={}
    assert run['classification']=='NO_FULL_OPTIMUM_RETURNED'


def test_baseline_child_export_and_shared_scenario(built,tmp_path):
    s,ctx=built
    small=p.reduced_scenario(s)
    digest=p._scenario_digest(small)
    run=p.execute_method(small,'Stationary',ctx['lambda']['lambda_bits_per_j'],tmp_path/'stationary',60,4*1024**3)
    assert run['status']=='FEASIBLE' and set(run['solutions'])=={'P1','P2'}
    assert p._scenario_digest(small)==digest
    assert run['runtime_s']>0 and run['sampled_peak_rss_bytes']>0
    summary=p.export_run(small,run,tmp_path/'stationary')
    assert len(summary)==2
    assert (tmp_path/'stationary/P1_trajectory.csv').exists()
    for row in summary:
        assert row['key_bits']>=0 and row['energy_j']<=small.budget


def test_runtime_worker_does_not_enable_python_allocation_tracing(monkeypatch,tmp_path):
    import tracemalloc
    def solve_without_tracing(s):
        assert not tracemalloc.is_tracing(), 'Runtime benchmark must not add Python allocation tracing'
        return dict(method='Pareto DP',solutions={})
    monkeypatch.setattr(p,'solve_dp',solve_without_tracing)
    p._worker(None,'Pareto DP',0,tmp_path)
    assert p.json.loads((tmp_path/'result.json').read_text())['status']=='FEASIBLE'


def test_progress_file_lock_does_not_stop_memory_sampling(monkeypatch,tmp_path):
    import time
    def solve_dp(s):
        time.sleep(1.2)
        return dict(method='Pareto DP',solutions={})
    def locked(*args):raise PermissionError('Simulated Windows progress file lock')
    monkeypatch.setattr(p,'solve_dp',solve_dp)
    monkeypatch.setattr(p,'_atomic',locked)
    p._worker(None,'Pareto DP',0,tmp_path)
    result=p.json.loads((tmp_path/'result.json').read_text())
    assert result['status']=='FEASIBLE'
    assert result['progress_telemetry_errors']>=1
    assert result['sampled_peak_rss_bytes']>0


def test_atomic_progress_retries_transient_windows_lock(monkeypatch,tmp_path):
    replace=Path.replace
    calls=[]
    def once_locked(path,target):
        calls.append(1)
        if len(calls)==1:raise PermissionError('Transient lock')
        return replace(path,target)
    monkeypatch.setattr(Path,'replace',once_locked)
    assert p._atomic(tmp_path/'progress.json',{'k':2}) is True
    assert len(calls)==2
    assert p.json.loads((tmp_path/'progress.json').read_text())=={'k':2}
