import copy
from itertools import product
from pathlib import Path
import numpy as np
import pytest

from uav_qkd.config import load_config, build_scenario
from uav_qkd.evaluation import Scenario
from uav_qkd.baselines import solve_baseline
from uav_qkd.dp_solver import Label, pareto_prune, solve_dp
from uav_qkd.propulsion import EnergyModel, PropulsionParams, propulsion_power
from uav_qkd.blockage import BlockageModel
from uav_qkd.cloud_model import GaussianCluster, CloudField
from uav_qkd.finite_size import finite_key


ROOT = Path(__file__).parents[1]


def test_all_methods_complete_blockage_and_reproducibility():
    c = load_config(ROOT/'configs/demo.yaml')
    original, _ = build_scenario(c)
    s = Scenario(original.graph, original.rates, np.zeros((4, len(original.rates))), original.budget, original.m0, original.epsilon)
    for fn in [lambda: solve_dp(s), *[lambda name=name: solve_baseline(s, name, 100.)
               for name in ('Stationary', 'SKR-Greedy', 'Energy-Aware Greedy')]]:
        first = fn()
        assert fn() == first
        for sol in first['solutions'].values():
            assert sol['key_bits'] == sol['unblocked_slots'] == 0
            assert sol['energy_j'] > 0 and sol['K'] >= 1


@pytest.mark.parametrize('seed', range(5))
def test_dp_random_tiny_exhaustive(seed):
    c = load_config(ROOT/'configs/demo.yaml')
    c['graph'] = dict(kind='points', points_m=[[1000., 1000.], [1010., 1000.], [1020., 1000.]])
    graph_s, _ = build_scenario(c)
    rng = np.random.default_rng(seed)
    s = Scenario(graph_s.graph, rng.uniform(.01, .2, 3), rng.integers(0, 2, (4, 3)), 550., c['m0'], c['epsilon'])
    best = {'P1': 0., 'P2': 0.}
    for k in range(1, s.horizon+1):
        for tail in product(range(3), repeat=k):
            path = (s.graph.initial,)+tail
            energy = sum(s.graph.costs[i, j] for i, j in zip(path, path[1:]))
            if energy > s.budget:
                continue
            n = s.m0*sum(s.z[t, j] for t, j in enumerate(tail))
            contribution = s.m0*sum(s.z[t, j]*s.rates[j] for t, j in enumerate(tail))
            key = max(0., contribution-7*np.sqrt(n*np.log2(2/s.epsilon)))
            best['P1'] = max(best['P1'], key/(k*s.graph.dt))
            best['P2'] = max(best['P2'], key)
    result = solve_dp(s)
    for objective in best:
        assert result['solutions'][objective]['objective_value'] == pytest.approx(best[objective], rel=1e-12, abs=1e-8)


def test_strict_dominance_duplicates_and_tradeoff():
    labels = [Label(e, a, 0, 1, 1, None) for e, a in [(1., 2.), (2., 1.), (2., 3.), (1., 2.)]]
    kept = pareto_prune(labels)
    assert [(x.e, x.a) for x in kept] == [(1., 2.), (2., 3.)]
    assert kept[0] is labels[0]
    # A sub-tolerance energy advantage must not be lost to epsilon-dominance.
    labels = [Label(1., 1., 0, 1, 1, None), Label(1.+1e-13, 1.+1e-13, 0, 1, 1, None)]
    assert len(pareto_prune(labels)) == 2


def test_energy_mixing_improves_on_constant_speed():
    params = PropulsionParams(79.86, 88.63, 120., 4.03, .6, 1.225, .05, .503, 20.)
    model = EnergyModel(params, 4001)
    assert model.energy(2., 1.) < propulsion_power(2., params)
    assert model.energy(0., 2.) == pytest.approx(2*(params.P0+params.Pi))


def test_slab_tangent_vertical_and_covariance():
    field = CloudField([GaussianCluster(10., (0., 0.), (1., 2.), covariance=((2., .5), (.5, 1.)))], (0., 0.))
    model = BlockageModel(field, 8., (0., 0., 100.), 0., mode='layer', layer_bottom_m=50., layer_top_m=50., sample_spacing_m=1.)
    assert model.blocked([0., 0.], 0.)
    assert not model.blocked([100., 0.], 0.)


def test_los_spacing_refinement_demo():
    c = load_config(ROOT/'configs/demo.yaml')
    original, _ = build_scenario(c)
    fine = copy.deepcopy(c)
    fine['blockage']['sample_spacing_m'] *= .5
    refined, _ = build_scenario(fine)
    np.testing.assert_array_equal(refined.z, original.z)


def test_extreme_valid_epsilon_is_finite():
    result = finite_key(.3, 1, 1e6, 1e-310)
    expected = 7*np.sqrt(1e6)*np.sqrt(1-np.log2(1e-310))
    assert np.isfinite(result['penalty_bits'])
    assert result['key_bits'] == pytest.approx(300000-expected)


def test_infeasible_stationary_does_not_abort_other_methods():
    from uav_qkd.experiments import run_methods
    c = load_config(ROOT/'configs/demo.yaml')
    c['graph'] = dict(kind='points', points_m=[[1000., 1000.], [1010., 1000.]])
    c['energy_budget_j'] = 140.
    s, _ = build_scenario(c)
    runs = run_methods(s, c, 0., measure=False)
    assert len(runs) == 4
    assert runs[0]['status'] == 'INFEASIBLE'
    assert runs[-1]['solutions']['P2']['K'] == 1


def test_quoted_false_does_not_authorize_paper():
    c = load_config(ROOT/'configs/demo.yaml')
    c.update(mode='paper', research_use_authorized='false', physical_input_provenance='fixture')
    c['lookup'] = dict(synthetic=False, file='missing.csv', sha256='0'*64,
                       provenance='fixture', coordinate_units='m', rate_units='bits/use')
    c['cloud']['provenance'] = 'fixture'
    c['greedy']['lambda_provenance'] = 'fixture'
    with pytest.raises(ValueError, match='authorization'):
        build_scenario(c)


def test_optional_terminal_reports_stationary_infeasible():
    from uav_qkd.experiments import run_methods
    c = load_config(ROOT/'configs/demo.yaml')
    c['graph'] = dict(kind='points', points_m=[[1000., 1000.], [1010., 1000.]])
    c['terminal_m'] = [1010., 1000.]
    s, _ = build_scenario(c)
    runs = run_methods(s, c, 0., measure=False)
    assert runs[0]['status'] == 'INFEASIBLE'
    for solution in runs[-1]['solutions'].values():
        assert solution['trajectory_m'][-1] == c['terminal_m']
