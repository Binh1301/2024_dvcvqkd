"""Arithmetic software fixtures ONLY; no rates/trajectories here are research data."""
from dataclasses import replace
from itertools import product
import json
from pathlib import Path

import numpy as np
import pytest

from test_planning import fixture
from uav_qkd.baselines import solve_baseline
from uav_qkd.dp_solver import solve_dp
from uav_qkd.evaluation import Scenario, evaluate_path
from uav_qkd.experiments import run_methods
from uav_qkd.cloud_channel import CloudPolicy, LinkSlotResult

ROOT = Path(__file__).parents[1]


def all_methods(s):
    return run_methods(s, {'dp': {'mode': 'exact'}}, .5, measure=False)


def test_static_vector_and_repeated_matrix_are_identical_for_all_methods():
    s = fixture()
    dynamic = replace(s, rates=np.tile(s.rates, (len(s.z), 1)))
    assert all_methods(dynamic) == all_methods(s)


def test_dynamic_rates_are_sampled_at_each_destination_slot():
    s = replace(fixture(np.ones((4, 3), int)), rates=np.array([[.01, .9, .1], [.01, .1, .9], [.01, .9, .1], [.01, .1, .9]]))
    run = solve_baseline(s, 'SKR-Greedy')['solutions']['P2']
    assert run['path_indices'] == [0, 1, 2, 1, 2]
    assert [r['a'] for r in run['series']] == pytest.approx([.9, 1.8, 2.7, 3.6])
    assert [r['time_s'] for r in run['series']] == [1., 2., 3., 4.]


@pytest.mark.parametrize('seed', range(6))
def test_dynamic_dp_matches_independent_exhaustive_arithmetic(seed):
    rng = np.random.default_rng(seed)
    s = replace(fixture(), rates=rng.uniform(-.02, .2, (4, 3)), z=rng.integers(0, 2, (4, 3)),
                budget=550. if seed < 3 else 290., terminal_index=None if seed % 2 == 0 else 1)
    best = {'P1': -1., 'P2': -1.}
    for k in range(1, s.horizon+1):
        for tail in product(range(3), repeat=k):
            path = [s.graph.initial, *tail]
            e = sum(float(s.graph.costs[i, j]) for i, j in zip(path, path[1:]))
            if e > s.budget or (s.terminal_index is not None and tail[-1] != s.terminal_index):
                continue
            n = s.m0*sum(s.z[t, j] for t, j in enumerate(tail))
            total = s.m0*sum(s.z[t, j]*s.rates[t, j] for t, j in enumerate(tail))
            key = max(0., total-7*np.sqrt(n*np.log2(2/s.epsilon)))
            best['P1'] = max(best['P1'], key/(k*s.graph.dt))
            best['P2'] = max(best['P2'], key)
    for dominance in (False, True):
        run = solve_dp(s, dominance=dominance)
        for objective, value in best.items():
            assert run['solutions'][objective]['objective_value'] == pytest.approx(value, abs=1e-8)
            evaluate_path(s, run['solutions'][objective]['path_indices'])


def test_penalty_once_accumulated_signals_and_separate_stopping():
    s = replace(fixture(np.ones((4, 3), int)), rates=np.tile([.2, .001, .2, .001], (3, 1)).T, budget=700.)
    rows = evaluate_path(s, [0, 0, 0, 0, 0])['series']
    assert rows[-1]['valid_signals'] == 4*s.m0
    assert rows[-1]['asymptotic_bits'] == pytest.approx(.402*s.m0)
    penalty = 7*np.sqrt(4*s.m0*np.log2(2/s.epsilon))
    assert rows[-1]['penalty_bits'] == pytest.approx(penalty)
    assert rows[-1]['penalty_bits'] != pytest.approx(4*7*np.sqrt(s.m0*np.log2(2/s.epsilon)))
    run = solve_dp(s)['solutions']
    assert run['P1']['K'] != run['P2']['K']
    assert run['P1']['average_skr_bits_s'] == run['P1']['key_bits']/(run['P1']['K']*s.graph.dt)


def test_dynamic_stationary_and_feasibility():
    s = replace(fixture(np.ones((4, 3), int)), rates=np.full((4, 3), .2))
    sol = solve_baseline(s, 'Stationary')['solutions']['P2']
    assert set(sol['path_indices']) == {s.graph.initial}
    assert sol['energy_j'] == pytest.approx(sol['K']*s.graph.dt*(s.graph.energy.params.P0+s.graph.energy.params.Pi))
    with pytest.raises(ValueError, match='energy'):
        evaluate_path(replace(s, budget=140.), [0, 0])
    # Make a real graph with an edge outside v_max*dt, not an artificial cost.
    from uav_qkd.waypoint_graph import WaypointGraph
    g = WaypointGraph.build([[0, 0], [100, 0]], [0, 0], [2000, 2000], 1., s.graph.energy)
    far = Scenario(g, np.ones((2, 2))*.1, np.ones((2, 2)), 550., s.m0, s.epsilon)
    with pytest.raises(ValueError, match='speed'):
        evaluate_path(far, [0, 1])


def test_provider_time_key_and_snapshot_shared_by_all_methods():
    from uav_qkd.rate_provider import sample_rate_provider
    from uav_qkd.waypoint_graph import WaypointGraph
    s = fixture(np.ones((4, 3), int))
    g = WaypointGraph.build(s.graph.positions, [0, 0], [2000, 2000], 2., s.graph.energy)
    s = replace(s, graph=g, budget=1500.)
    calls = []
    def rate(q, t, scenario):
        assert scenario is s
        calls.append((tuple(q), t))
        return .1+t/100+q[0]/1000
    dynamic = sample_rate_provider(s, rate)
    assert len(calls) == s.horizon*len(s.graph.positions)
    assert sorted({t for q, t in calls}) == [2., 4., 6., 8.]
    assert dynamic.rate_at(0, 0) == pytest.approx(.12)
    assert dynamic.rate_at(1, 0) == pytest.approx(.14)
    before = calls.copy()
    assert all_methods(dynamic) == all_methods(dynamic)
    assert calls == before


@pytest.mark.parametrize('rates', [np.zeros((3, 3)), np.zeros((4, 2)), np.zeros((4, 3, 1)), np.full((4, 3), np.nan)])
def test_invalid_rate_matrix_rejected(rates):
    with pytest.raises(ValueError, match='SKR'):
        replace(fixture(), rates=rates)


def test_cloud_seed_replay_and_continuous_drift_at_endpoint_times():
    from uav_qkd.rate_provider import sample_link_provider
    from uav_qkd.cloud_model import CloudField, GaussianCluster
    from uav_qkd.blockage import BlockageModel
    s = replace(fixture(), z=np.ones((4, 3), int))
    policy = CloudPolicy('binary_erasure', True, 'SOFTWARE FIXTURE ONLY')
    def make():
        rng = np.random.default_rng(17)
        center = tuple(rng.uniform(0, 10, 2))
        field = CloudField([GaussianCluster(10., center, (3., 3.))], (-5., 0.))
        model = BlockageModel(field, 5., [0., 0., 100.], 0., mode='layer',
                              layer_bottom_m=50., layer_top_m=50., sample_spacing_m=1.)
        def provider(q, t, scenario):
            blocked = model.blocked(q, t)
            return LinkSlotResult(0. if blocked else s.m0, 0. if blocked else .1,
                                  0. if blocked else .5, not blocked, policy.mode, policy.provenance, {})
        return field, model, sample_link_provider(s, provider, policy)
    f, model, a = make(); _, _, b = make()
    np.testing.assert_array_equal(a.rates, b.rates)
    np.testing.assert_array_equal(a.z, b.z)
    np.testing.assert_array_equal(a.z, model.sequence(s.graph.positions, s.horizon, s.graph.dt))
    q = np.array([[2., 3.]])
    np.testing.assert_allclose(f.evaluate(q, .3), f.evaluate(q+np.array([[1.5, 0.]]), 0.))


def test_analog_provider_no_double_erasure_and_fractional_counts_rejected():
    from uav_qkd.rate_provider import sample_link_provider
    s = replace(fixture(), z=np.ones((4, 3), int))
    policy = CloudPolicy('optical_attenuation', True, 'SOFTWARE FIXTURE ONLY')
    def provider(q, t, scenario):
        return LinkSlotResult(s.m0, .1/t, .5/t, True, policy.mode, policy.provenance, {})
    dynamic = sample_link_provider(s, provider, policy)
    assert dynamic.z.all()
    assert dynamic.rates[0, 0] != dynamic.rates[1, 0]
    with pytest.raises(ValueError, match='erasure'):
        sample_link_provider(replace(s, z=np.zeros_like(s.z)), provider, policy)
    def fractional(q, t, scenario):
        return replace(provider(q, t, scenario), valid_signals=s.m0/2)
    with pytest.raises(ValueError, match='signals'):
        sample_link_provider(s, fractional, policy)
    with pytest.raises(ValueError, match='approved'):
        sample_link_provider(s, provider, replace(policy, author_approved=False))


def test_incompatible_lookup_rejected_before_any_file_or_backend_loading(tmp_path):
    from uav_qkd.skr_lookup import require_lookup_compatibility
    from uav_qkd.hap_uav_channel import load_channel_reference
    c = load_channel_reference(ROOT/'configs/channel/hap_uav_mb_reference.yaml')
    protocol = json.loads((ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json').read_text(encoding='utf-8'))
    with pytest.raises(ValueError, match='incompatible') as error:
        require_lookup_compatibility(c, protocol)
    assert all(name in str(error.value) for name in ('receiver_aperture_diameter_m', 'beam_full_divergence_rad', 'transmitter_jitter_angle_rad', 'uav_position_sd_m'))


def test_static_metrics_replay_historical_demo_without_admitting_old_producers():
    from uav_qkd.config import build_scenario
    from uav_qkd.verify import verify_results
    directory = ROOT/'results/final_demo_20261107'
    report = json.loads((directory/'results.json').read_text(encoding='utf-8'))
    scenario, _ = build_scenario(report['config'])
    for run in report['runs']:
        for sol in run['solutions'].values():
            assert evaluate_path(scenario, sol['path_indices'])['series'] == sol['series']
    # Metric equivalence is distinct from a current-producer provenance pass.
    with pytest.raises(ValueError, match='Source producer hash mismatch'):
        verify_results(directory)


def test_snapshots_are_copied_and_read_only_and_indices_are_guarded():
    s = fixture()
    rates = np.ones((4, 3))
    dynamic = replace(s, rates=rates)
    rates[:] = 2.
    assert dynamic.rate_at(0, 0) == 1.
    with pytest.raises(ValueError):
        dynamic.rates[0, 0] = 2.
    for slot, j in [(-1, 0), (4, 0), (0, -1), (0, 3), (True, 0), (0, .5)]:
        with pytest.raises(ValueError, match='Rate query'):
            dynamic.rate_at(slot, j)


def test_selected_reference_cannot_bypass_guard_by_partial_match_or_missing_file(tmp_path):
    from uav_qkd.skr_lookup import SKRLookup, require_lookup_compatibility
    from uav_qkd.hap_uav_channel import load_channel_reference
    c = load_channel_reference(ROOT/'configs/channel/hap_uav_mb_reference.yaml')
    protocol = json.loads((ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json').read_text(encoding='utf-8'))
    units = dict(coordinate_units='m', rate_units='bits/use')
    with pytest.raises(ValueError, match='incompatible'):
        SKRLookup.load(tmp_path/'not-read.csv', reference=c, protocol=protocol, **units)
    with pytest.raises(ValueError, match='both reference'):
        SKRLookup.load(tmp_path/'not-read.csv', reference=c, **units)
    # Even matching all twelve checked physical fields is not full compatibility.
    for name, value in dict(receiver_aperture_diameter_m=.3, beam_full_divergence_rad=35e-6,
                            transmitter_jitter_angle_rad=1.561e-6, uav_position_sd_m=.1).items():
        c[name] = value
    with pytest.raises(ValueError, match='not established'):
        require_lookup_compatibility(c, protocol)


def test_config_wires_explicit_selected_reference_to_lookup_guard(tmp_path):
    from uav_qkd.config import load_config, build_scenario
    config = load_config(ROOT/'configs/demo.yaml')
    config['lookup'] = dict(synthetic=False, file='must-not-be-read.csv', coordinate_units='m', rate_units='bits/use',
                            reference_config=str(ROOT/'configs/channel/hap_uav_mb_reference.yaml'),
                            protocol_file=str(ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json'))
    with pytest.raises(ValueError, match='incompatible'):
        build_scenario(config)
