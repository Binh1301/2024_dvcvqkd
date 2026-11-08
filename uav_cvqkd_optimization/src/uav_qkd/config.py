"""Explicit scientific inputs; a separate, clearly synthetic demonstration."""
from pathlib import Path
import hashlib
import math
import numpy as np
import yaml
from .propulsion import PropulsionParams, EnergyModel
from .cloud_model import GaussianCluster, CloudField
from .blockage import BlockageModel
from .skr_lookup import SKRLookup
from .waypoint_graph import WaypointGraph, regular_waypoints
from .evaluation import Scenario

SYNTHETIC = 'SYNTHETIC DEMONSTRATION — NOT PAPER RESULTS'


def load_config(path) -> dict:
    path = Path(path).resolve()
    with path.open(encoding='utf-8-sig') as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        raise ValueError('Configuration must be a YAML mapping')
    config['_config_path'] = str(path)
    return config


def build_scenario(c: dict) -> tuple[Scenario, dict]:
    required = ['mode', 'seed', 'area_m', 'initial_m', 'hap_m', 'uav_altitude_m',
                'dt', 'max_horizon', 'energy_budget_j', 'm0', 'epsilon', 'propulsion',
                'graph', 'cloud', 'blockage', 'lookup', 'dp', 'greedy',
                'velocity_samples', 'energy_tolerance_j']
    missing = [key for key in required if c.get(key) is None]
    if missing:
        raise ValueError('Missing scientific inputs: '+', '.join(missing)+'. Complete paper.yaml with verified data; use demo.yaml only for synthetic testing.')
    if c['mode'] not in ('synthetic', 'paper'):
        raise ValueError('mode must be synthetic or paper')
    for key in ('dt', 'energy_budget_j', 'm0', 'energy_tolerance_j'):
        value = c[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value <= 0:
            raise ValueError(f'{key} must be positive and finite')
    for key in ('max_horizon', 'velocity_samples', 'seed'):
        value = c[key]
        minimum = 0 if key == 'seed' else 1
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f'{key} must be an integer >= {minimum}')
    lookup_config = c['lookup']
    if c['mode'] == 'paper':
        if c.get('research_use_authorized') is not True:
            raise ValueError('Paper scientific research-use authorization must be the boolean true, not a quoted string')
        missing = [key for key in ('physical_input_provenance', 'research_use_authorized') if not c.get(key)]
        missing += ['lookup.'+key for key in ('file', 'sha256', 'provenance') if not lookup_config.get(key)]
        missing += ['cloud.provenance'] if not c['cloud'].get('provenance') else []
        missing += ['greedy.lambda_provenance'] if not c['greedy'].get('lambda_provenance') else []
        if lookup_config.get('synthetic') or missing:
            raise ValueError('Missing scientific provenance/authorization or synthetic input in paper mode: '+', '.join(missing))
    p = PropulsionParams(**c['propulsion'])
    graph_config = c['graph']
    if graph_config['kind'] == 'points':
        positions = np.asarray(graph_config['points_m'], float)
        if not any(np.array_equal(point, c['initial_m']) for point in positions):
            positions = np.vstack([positions, c['initial_m']])
    elif graph_config['kind'] in ('lattice', 'restricted_lattice'):
        if graph_config['kind'] == 'restricted_lattice':
            lower, upper = np.asarray(graph_config['bounds_m'], float)
        else:
            lower, upper = np.zeros(2), np.asarray(c['area_m'], float)
        positions = regular_waypoints(upper-lower, graph_config['spacing_m'], np.asarray(c['initial_m'])-lower)+lower
    else:
        raise ValueError('Graph kind must be points, lattice or restricted_lattice')
    graph = WaypointGraph.build(positions, c['initial_m'], c['area_m'], c['dt'],
                               EnergyModel(p, c['velocity_samples']), energy_tolerance_j=c['energy_tolerance_j'])
    cc = c['cloud']
    if cc.get('file'):
        import json
        cloud_path = Path(c['_config_path']).parent/cc['file']
        with cloud_path.open(encoding='utf-8-sig') as f:
            clusters = json.load(f)['clusters']
    else:
        clusters = cc['clusters']
    field = CloudField([GaussianCluster(**entry) for entry in clusters], cc['velocity_m_s'], cc.get('clip_max'))
    blockage = BlockageModel(field, cc['threshold_mg_m3'], c['hap_m'], c['uav_altitude_m'], **c['blockage'])
    if lookup_config.get('synthetic'):
        if c['mode'] != 'synthetic':
            raise ValueError('synthetic lookup is forbidden in paper mode')
        ny, nx = lookup_config['grid_shape']
        X, Y = np.meshgrid(np.linspace(0, c['area_m'][0], nx), np.linspace(0, c['area_m'][1], ny))
        points = np.c_[X.ravel(), Y.ravel()]
        delta = (points-np.array(lookup_config['rate_center_m']))/lookup_config['rate_sigma_m']
        rates = lookup_config['rate_floor']+(lookup_config['rate_peak']-lookup_config['rate_floor'])*np.exp(-.5*np.sum(delta**2, axis=1))
        lookup = SKRLookup(points, rates, coordinate_units='m', rate_units='bits/use')
    else:
        path = Path(c['_config_path']).parent/lookup_config['file']
        reference_path, protocol_path = lookup_config.get('reference_config'), lookup_config.get('protocol_file')
        binding = {}
        if reference_path is not None or protocol_path is not None:
            if not reference_path or not protocol_path:
                raise ValueError('Lookup context requires both reference_config and protocol_file')
            import json
            from .hap_uav_channel import load_channel_reference
            base = Path(c['_config_path']).parent
            binding = dict(reference=load_channel_reference(base/reference_path),
                           protocol=json.loads((base/protocol_path).read_text(encoding='utf-8')))
        if c['mode'] == 'paper' and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != lookup_config['sha256']:
            raise ValueError('SKR input SHA256 mismatch')
        lookup = SKRLookup.load(path, **binding, coordinate_units=lookup_config['coordinate_units'], rate_units=lookup_config['rate_units'])
    rates = lookup(graph.positions)
    horizon = min(c['max_horizon'], math.floor(c['energy_budget_j']/graph.min_cost))
    if horizon < 1:
        raise ValueError('Problem infeasible: insufficient propulsion energy for K>=1')
    z = blockage.sequence(graph.positions, horizon, c['dt'])
    terminal = c.get('terminal_m')
    terminal_index = None
    if terminal is not None:
        found = np.flatnonzero(np.all(graph.positions == terminal, axis=1))
        if len(found) != 1:
            raise ValueError('Configured terminal must be a graph waypoint')
        terminal_index = int(found[0])
    scenario = Scenario(graph, rates, z, c['energy_budget_j'], c['m0'], c['epsilon'], terminal_index)
    if c['dp']['mode'] not in ('exact', 'approximate'):
        raise ValueError('DP mode must be exact or approximate')
    if c['dp']['mode'] == 'approximate' and c['dp'].get('label_cap') is None:
        raise ValueError('Approximate DP requires a label cap')
    return scenario, dict(field=field, blockage=blockage, lookup=lookup,
                          energy_horizon=math.floor(c['energy_budget_j']/graph.min_cost),
                          configured_prediction_horizon=c['max_horizon'])
