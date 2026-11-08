"""Source-version regression checks; synthetic fixtures do not supply paper inputs."""
from pathlib import Path
import numpy as np
import pytest
from uav_qkd.config import load_config, build_scenario
from uav_qkd.propulsion import PropulsionParams, propulsion_power, EnergyModel
from uav_qkd.waypoint_graph import WaypointGraph
from uav_qkd.evaluation import Scenario, evaluate_path
from uav_qkd.dp_solver import solve_dp
from uav_qkd.finite_size import finite_key
from uav_qkd.skr_lookup import SKRLookup
from uav_qkd.cloud_model import CloudField, GaussianCluster
from uav_qkd.blockage import BlockageModel

ROOT = Path(__file__).parents[1]


@pytest.fixture
def paper():
    return load_config(ROOT/'configs/paper.yaml')


def test_zeng_2018_preprint_derived_power_and_hover(paper):
    p = PropulsionParams(**paper['propulsion'])
    expected_p0 = (.012/8)*1.225*.05*.79*200**3
    expected_pi = 1.1*100**1.5/np.sqrt(2*1.225*.79)
    assert p.P0 == pytest.approx(expected_p0, abs=1e-10)
    assert p.Pi == pytest.approx(expected_pi, abs=1e-10)
    assert propulsion_power(0., p) == pytest.approx(1371.321522813272, abs=1e-9)
    assert p.v0 == 7.2 and p.v_max == 60 and p.d0 == .3


def test_rotor_source_version_and_rounding_are_explicit(paper):
    source = paper['verified_context']['rotor']
    assert source['source_url'] == 'https://arxiv.org/pdf/1804.02238v1'
    assert source['table_page'] == 27
    assert source['v0_derived_m_s'] == pytest.approx(7.187922934666108)
    assert source['source_variant'] == 'arxiv_v1_2018_not_IEEE_2019_parameter_table'


def test_unknown_paper_inputs_stay_unresolved(paper):
    for key in ('initial_m', 'hap_m', 'max_horizon', 'energy_budget_j', 'm0', 'epsilon', 'graph', 'cloud', 'blockage'):
        assert paper[key] is None
    assert paper['research_use_authorized'] is False
    assert paper['lookup']['file'] is None
    with pytest.raises(ValueError, match='Missing scientific inputs'):
        build_scenario(paper)


def test_verified_geometry_altitudes_are_not_inferred_horizontal_positions(paper):
    assert paper['uav_altitude_m'] == 1000.
    assert paper['verified_context']['hap_altitude_m'] == 20000.
    assert paper['hap_m'] is None
    assert paper['area_m'] == [2000., 2000.] and paper['dt'] == 1.
    assert paper['verified_context']['cloud_velocity_m_s'] == [-5., 0.]


def test_source_rotor_graph_energy_feasibility(paper):
    # Tiny software fixture: this budget/rate/epsilon is not a proposed paper scenario.
    energy = EnergyModel(PropulsionParams(**paper['propulsion']), 2001)
    graph = WaypointGraph.build([[0., 0.], [40., 0.]], [0., 0.], [2000., 2000.], 1., energy)
    budget = 2*float(graph.costs[0, 1])
    s = Scenario(graph, np.array([.1, .2]), np.ones((3, 2), int), budget, 1e6, 1e-6)
    for sol in solve_dp(s)['solutions'].values():
        result = evaluate_path(s, sol['path_indices'])
        assert result['energy_j'] <= budget
        q = np.array(result['trajectory_m'])
        assert np.linalg.norm(np.diff(q, axis=0), axis=1).max() <= 60.


def test_source_config_qkd_units_preserve_rate_scale(paper):
    assert paper['lookup']['coordinate_units'] == 'm'
    assert paper['lookup']['rate_units'] == 'bits/use'
    rows = [[0, 0, .0007], [1, 0, .0008], [0, 1, .0009]]
    rate = SKRLookup.from_array(rows, coordinate_units='m', rate_units='bits/use')
    assert rate([[0, 0]])[0] == .0007
    with pytest.raises(ValueError, match='units'):
        SKRLookup.from_array(rows, coordinate_units='m', rate_units='bits/s')


def test_valid_signals_are_not_automatically_pulse_rate(paper):
    assert paper['verified_context']['pulse_rate_hz'] is None
    assert paper['verified_context']['eta_valid'] is None
    # Explicit unit-test values: two clear slots from three, eta_valid=.25.
    m0 = 1000*paper['dt']*.25
    result = finite_key(.002, 2, m0, 1e-6)
    assert result['valid_signals'] == 500
    assert result['asymptotic_bits'] == .5


def test_source_altitude_geometry_with_explicit_fixture_layer(paper):
    # Horizontal HAP position and 11 km cloud layer are test fixtures only.
    field = CloudField([GaussianCluster(10., (900., 0.), (5., 5.))], (0., 0.))
    model = BlockageModel(field, 8., (0., 0., paper['verified_context']['hap_altitude_m']),
                          paper['uav_altitude_m'], mode='layer', sample_spacing_m=1.,
                          layer_bottom_m=11000., layer_top_m=11000.)
    np.testing.assert_allclose(model.projected_segment([1900., 0.]), [[900., 0.], [900., 0.]])
    assert model.blocked([1900., 0.], 0.)
    assert field.evaluate([[1900., 0.]], 0.)[0] < 8.
