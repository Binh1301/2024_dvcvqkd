from itertools import product
import numpy as np
import pytest

from uav_qkd.propulsion import PropulsionParams, EnergyModel
from uav_qkd.waypoint_graph import WaypointGraph, regular_waypoints
from uav_qkd.evaluation import Scenario, evaluate_path
from uav_qkd.baselines import solve_baseline
from uav_qkd.dp_solver import solve_dp


def fixture(z=None, budget=550.):
    params = PropulsionParams(79.86, 88.63, 120., 4.03, .6, 1.225, .05, .503, 20.)
    graph = WaypointGraph.build([[0, 0], [10, 0], [20, 0]], [0, 0], [2000, 2000],
                               1., EnergyModel(params, 1001), energy_tolerance_j=.001)
    if z is None:
        z = np.array([[1, 0, 1], [0, 1, 1], [1, 1, 0], [1, 0, 1]])
    return Scenario(graph, np.array([.10, .13, .16]), z, budget, 1e6, 1e-6)


def brute(scenario):
    best = {'P1': (-1., None), 'P2': (-1., None)}
    for k in range(1, scenario.horizon+1):
        for tail in product(range(len(scenario.graph.positions)), repeat=k):
            path = (scenario.graph.initial,)+tail
            cost = sum(scenario.graph.costs[i, j] for i, j in zip(path, path[1:]))
            if cost > scenario.budget:
                continue
            u = sum(int(scenario.z[t, j]) for t, j in enumerate(tail))
            a = sum(scenario.z[t, j]*scenario.rates[j] for t, j in enumerate(tail))
            key = max(0., scenario.m0*a-7*np.sqrt(scenario.m0*u*np.log2(2/scenario.epsilon)))
            for objective, value in [('P1', key/(k*scenario.graph.dt)), ('P2', key)]:
                if value > best[objective][0]:
                    best[objective] = value, path
    return best


def test_dp_matches_brute_with_and_without_dominance():
    s = fixture()
    exact = brute(s)
    for prune in (False, True):
        result = solve_dp(s, dominance=prune)
        for objective in ('P1', 'P2'):
            actual = result['solutions'][objective]
            assert actual['objective_value'] == pytest.approx(exact[objective][0], abs=1e-7)
            assert actual['energy_j'] <= s.budget
            evaluate_path(s, actual['path_indices'])


def test_baselines_feasible_and_zero_blockage():
    for z in (np.zeros((4, 3), int), np.ones((4, 3), int)):
        s = fixture(z)
        for method in ('Stationary', 'SKR-Greedy', 'Energy-Aware Greedy'):
            run = solve_baseline(s, method, lambda_bits_per_j=.5)
            for sol in run['solutions'].values():
                assert sol['K'] >= 1 and sol['energy_j'] > 0
                assert sol['energy_j'] <= s.budget
                if not z.any():
                    assert sol['key_bits'] == 0 and sol['blocked_slots'] == sol['K']
            if method == 'Stationary':
                assert len(set(run['solutions']['P2']['path_indices'])) == 1


def test_variable_duration_and_approximation():
    s = fixture(np.array([[1, 1, 1], [0, 0, 0], [1, 1, 1], [0, 0, 0]]))
    run = solve_dp(s)
    assert run['solutions']['P1']['K'] != run['solutions']['P2']['K']
    approx = solve_dp(s, label_cap=1)
    assert approx['classification'] == 'approximate'
    for objective in ('P1', 'P2'):
        assert approx['solutions'][objective]['objective_value'] <= run['solutions'][objective]['objective_value']+1e-8
    assert solve_dp(s) == run


def test_graph_connectivity_initial_and_infeasible():
    s = fixture()
    assert s.graph.diagnostics['reachable_waypoints'] == 3
    assert s.horizon == min(4, int(s.budget//s.graph.min_cost))
    with pytest.raises(ValueError, match='infeasible'):
        fixture(budget=.001)
    points = regular_waypoints([40, 40], 10, [3, 4])
    assert any(np.array_equal(p, [3, 4]) for p in points)
    disconnected = WaypointGraph.build([[0, 0], [100, 0]], [0, 0], [2000, 2000],
                                        1., EnergyModel(s.graph.energy.params))
    assert disconnected.diagnostics['movement_edges'] == 0
    assert disconnected.diagnostics['reachable_waypoints'] == 1


def test_greedy_ties_choose_energy_then_index():
    s = fixture(np.zeros((4, 3), int))
    first = solve_baseline(s, 'SKR-Greedy')['solutions']['P1']['path_indices'][1]
    choices = s.graph.successors[s.graph.initial]
    assert first == min(choices, key=lambda j: (s.graph.costs[s.graph.initial, j], j))
