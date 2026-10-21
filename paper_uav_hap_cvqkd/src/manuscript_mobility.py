"""Read-only manuscript evaluator adapter and finite-grid mobility comparison.

The approved synthetic comparison retains its unvalidated security model and
does not authorize publication evaluation or source-moment generation.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np

from src.uav_mobility import (best_stationary, candidate_grid, link_geometry,
                              optimize_trajectory, scalar, transition_distances)
from scripts.exact_cache_provenance import source_settings, verify_source_payload
from scripts.recheck_manuscript_homodyne_noise import M, converted, security
from scripts.optimize_uniform_manuscript_2d import uniform_mi_2d
from scripts.run_exact_mb_test2 import ensemble_hash
from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config

ROOT = Path(__file__).resolve().parents[1]
# Canonical JSON identity of the explicitly approved, separate configuration.
_APPROVED_CONFIG_SHA256 = 'baca7d771b5b4ee0acd840ffd3706eaf39fc3635af9273c41d19e93893850635'
_MULTIPLIERS = [0, .0001, .0003, .001, .003, .01, .03, .1, .3, 1]
_spec = importlib.util.spec_from_file_location(
    '_manuscript_channel_reference', ROOT/'results/skr_vs_zenith_angle_20261019/run_sweep.py')
_reference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reference)
channel_at_angle = _reference.channel_at_angle


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def validate_config(settings):
    try:
        identity = hashlib.sha256(json.dumps(settings, sort_keys=True, separators=(',', ':'),
                                            allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError) as error:
        raise ValueError('Invalid manuscript configuration') from error
    if identity != _APPROVED_CONFIG_SHA256:
        raise ValueError('Configuration differs from the approved manuscript mobility protocol')
    reference = json.loads((ROOT/settings['reference_directory']/'protocol.json').read_text(encoding='utf-8'))
    if settings['optical'] != reference['optical']:
        raise ValueError('Optical configuration differs from the manuscript reference')
    for key, value in settings['security'].items():
        if reference[key] != value:
            raise ValueError('Security convention differs from manuscript reference: '+key)
    if (settings['numerical']['GH_orders'] != reference['quadrature_orders']
            or settings['numerical']['entropy_digits'] != reference['entropy_decimal_digits']
            or settings['numerical']['GH_absolute_tolerance'] != reference['GH_absolute_tolerance']):
        raise ValueError('Numerical conventions differ from manuscript reference')
    geometry = settings['geometry']
    return candidate_grid(geometry['grid_side_m'], geometry['grid_cells_per_side'])


def _validate_ensemble(p, alpha, nu, va):
    p, alpha = np.asarray(p, dtype=float), np.asarray(alpha, dtype=complex)
    if (p.shape != (256,) or alpha.shape != (256,) or not np.isfinite(p).all()
            or not np.isfinite(alpha).all() or np.any(p <= 0)
            or abs(p.sum()-1) >= 1e-14):
        raise ValueError('Invalid full-support ensemble probabilities/amplitudes')
    x, ix = np.unique(alpha.real, return_inverse=True)
    y, iy = np.unique(alpha.imag, return_inverse=True)
    if len(x) != 16 or len(y) != 16 or len(np.unique(alpha)) != 256:
        raise ValueError('Source is not the full Cartesian 256-state ensemble')
    px, py = np.bincount(ix, weights=p), np.bincount(iy, weights=p)
    raw = np.arange(16)-7.5
    target = np.exp(-nu*raw**2); target /= target.sum()
    scale = math.sqrt(va/(4*np.dot(target, raw**2)))
    if (abs(2*np.dot(p, abs(alpha)**2)-va) >= 2e-12
            or np.max(abs(p-px[ix]*py[iy])) >= 1e-14
            or max(np.max(abs(px-target)), np.max(abs(py-target))) >= 2e-14
            or max(np.max(abs(x-scale*raw)), np.max(abs(y-scale*raw))) >= 2e-13):
        raise ValueError('Source PMF/product/energy/geometry reconstruction failed')
    return p, alpha


def load_catalog(settings):
    validate_config(settings)
    config = unconstrained_config()
    expected_settings = source_settings(config)
    candidates, seen_parameters, seen_hashes = [], set(), set()
    for family in ('MB', 'Uniform'):
        roster = settings['source_rosters'][family]
        path = ROOT/roster['path']
        if sha(path) != roster['sha256']:
            raise ValueError('Roster digest mismatch: '+family)
        rows = read_csv(path)
        if family == 'MB':
            rows = [r for r in rows if r['family'] == family]
        if len(rows) != roster['count']:
            raise ValueError('Roster count mismatch: '+family)
        for row in rows:
            source_path = ROOT/row['source_path']
            source_sha = sha(source_path)
            expected_sha = row.get('source_sha256', row.get('source_payload_sha256'))
            if not expected_sha or source_sha != expected_sha:
                raise ValueError('Source full-payload digest mismatch: '+str(source_path))
            payload = json.loads(source_path.read_text(encoding='utf-8'))
            verification = verify_source_payload(payload, expected_settings)
            va = scalar(row.get('VA', row.get('V_A')), 'VA', positive=True)
            nu = scalar(row.get('nu_raw', 0.), 'nu_raw', nonnegative=True)
            if (family == 'Uniform' and nu != 0
                    or payload['V_A_hex'] != va.hex()
                    or payload['nu_mb_raw_hex'] != nu.hex()
                    or row.get('VA_hex', va.hex()) != va.hex()
                    or row.get('nu_raw_hex', nu.hex()) != nu.hex()
                    or float(payload['C']) != float(row['C'])
                    or float(payload['w']) != float(row['w'])
                    or float(payload['C']) <= 0 or float(payload['w']) < 0
                    or payload['cache_key'] != row['source_cache_key']
                    or payload['source_moment_route'] != row.get('source_route', row.get('source_moment_route'))):
                raise ValueError('Source parameter/moment/identity mismatch')
            ensemble = make_ensemble(config, family, nu, va)
            identity = ensemble_hash(ensemble)
            if identity != row['ensemble_hash'] or identity != payload['ensemble_hash']:
                raise ValueError('Reconstructed ensemble hash mismatch')
            parameters = family, nu.hex(), va.hex()
            if parameters in seen_parameters or identity in seen_hashes:
                raise ValueError('Duplicate exact source')
            seen_parameters.add(parameters); seen_hashes.add(identity)
            p, alpha = _validate_ensemble(ensemble.probabilities[0].numpy(),
                                          ensemble.amplitudes[0].numpy(), nu, va)
            candidates.append(dict(family=family, nu_raw=nu, VA=va, C=payload['C'], w=payload['w'],
                                   ensemble_hash=identity, source_path=source_path.relative_to(ROOT).as_posix(),
                                   source_sha256=source_sha, cache_key=payload['cache_key'],
                                   canonical_cache_key=verification['canonical_source_cache_key'],
                                   source_moment_route=payload['source_moment_route'], support_size=256,
                                   nu_raw_hex=nu.hex(), VA_hex=va.hex(), p=p, alpha=alpha))
    return sorted(candidates, key=lambda c: (c['family'], c['nu_raw'], c['VA'], c['ensemble_hash']))


def geometry_table(settings):
    positions = validate_config(settings)
    g = settings['geometry']
    distances, angles = link_geometry(positions, g['hap_horizontal_m'], g['h_hap_m'], g['h_uav_m'])
    horizontal_squared = np.sum((positions-np.asarray(g['hap_horizontal_m']))**2, axis=1)
    position_rows, geometry_rows, groups = [], [], {}
    for index, (position, distance, angle, h2) in enumerate(zip(positions, distances, angles, horizontal_squared)):
        degrees = float(np.degrees(angle))
        key = float(h2).hex(), float(distance).hex(), degrees.hex()
        first = key not in groups
        if first:
            groups[key] = f'g{len(groups):03d}'
        row = dict(position_index=index, j=index+1, x_m=float(position[0]), y_m=float(position[1]),
                   z_m=g['h_uav_m'], distance_km=float(distance/1000), zenith_deg=degrees,
                   zenith_hex=degrees.hex(), horizontal_squared_hex=float(h2).hex(), geometry_id=groups[key])
        position_rows.append(row)
        if first:
            geometry_rows.append(row.copy())
    if len(geometry_rows) != 60:
        raise ValueError('Approved geometry does not yield exactly 60 exact groups')
    return position_rows, geometry_rows


def evaluate_source(candidate, ch):
    va = scalar(candidate['VA'], 'VA', positive=True)
    nu = scalar(candidate['nu_raw'], 'nu_raw', nonnegative=True)
    C = scalar(candidate['C'], 'C', positive=True)
    w = scalar(candidate['w'], 'w', nonnegative=True)
    p, alpha = _validate_ensemble(candidate['p'], candidate['alpha'], nu, va)
    m1, mh = M(ch['mean_eta']), M(ch['mean_sqrt_eta'])
    if (not mp.isfinite(m1) or not mp.isfinite(mh) or not 0 < m1 <= 1
            or not 0 < mh <= 1 or mh**2 > m1):
        raise ValueError('Invalid channel moments')
    model = security(m1, mh, M(va), M(C), M(w))
    if not model['physical'] or not all(mp.isfinite(v) for v in model.values()):
        raise ValueError('Invalid or unphysical manuscript covariance')
    values = [uniform_mi_2d(p, alpha, float(model['eta_f']), float(model['eta_f_xi_f']), order)
              for order in (16, 32, 64)]
    delta = max(abs(value-values[-1]) for value in values)
    V, W, Z = [float(model[k]) for k in ('V', 'W', 'Z')]
    gamma = np.array([[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]])
    omega = np.kron(np.eye(2), np.array([[0.,1.],[-1.,0.]]))
    eig = np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
    spectrum_delta = float(max(abs(eig-np.sort([float(model['nu_1']),float(model['nu_2'])]))))
    uncertainty = float(np.linalg.eigvalsh(gamma+1j*omega).min())
    if (not np.isfinite(values).all() or delta > 2e-13
            or not 0 <= values[-1] <= -float(np.dot(p,np.log2(p)))
            or uncertainty <= 0 or spectrum_delta >= 2e-11
            or abs(model['eta_f_xi_f']-((m1-mh**2)*M(va)+M('.0186')*m1)) >= M('1e-65')):
        raise ValueError('MI convergence, entropy bound or independent covariance check failed')
    row = dict(family=candidate['family'], nu_raw=nu, VA=va, C=C, w=w,
               I_AB_2D=values[-1], beta_I_AB=float(M('.95')*M(values[-1])),
               chi_BE=float(model['chi_BE']), K_raw=float(M('.95')*M(values[-1])-model['chi_BE']),
               eta_f=float(model['eta_f']), xi_f=float(model['xi_f']), N=float(model['eta_f_xi_f']),
               V=V, W=W, Z=Z, nu_1=float(model['nu_1']),nu_2=float(model['nu_2']),nu_3=float(model['nu_3']),
               MI_GH16=values[0], MI_GH32=values[1], MI_GH64=values[2],GH_max_difference=delta,
               uncertainty_min_eigenvalue=uncertainty,matrix_spectrum_max_difference=spectrum_delta,
               ensemble_hash=candidate['ensemble_hash'],source_sha256=candidate['source_sha256'])
    return row, model


def select_winner(rows):
    if not rows:
        raise ValueError('Cannot select from an empty catalog')
    for row in rows:
        scalar(row['K_raw'], 'raw SKR')
        scalar(row['nu_raw'], 'nu_raw', nonnegative=True)
        scalar(row['VA'], 'VA', positive=True)
        if not isinstance(row['ensemble_hash'], str) or not row['ensemble_hash']:
            raise ValueError('Missing candidate hash')
    return min(rows, key=lambda row: (-row['K_raw'], row['nu_raw'], row['VA'], row['ensemble_hash']))


def lambda_schedule(Kstar, positions, reference_distance_m):
    rates = np.asarray(Kstar, dtype=float)
    if rates.ndim != 1 or not len(rates) or not np.isfinite(rates).all() or np.any(rates < 0):
        raise ValueError('Kstar must be a finite nonnegative vector')
    distance = transition_distances(positions)
    reference = scalar(reference_distance_m, 'reference distance', positive=True)
    if len(distance) != len(rates) or len(distance) < 2 or np.any(distance[np.triu_indices(len(distance),1)] <= 0):
        raise ValueError('Lambda schedule requires distinct matching positions')
    dmin, kmax = float(distance[distance > 0].min()), float(rates.max())
    hi = 2*kmax*reference/dmin
    return dict(lambda_hi=hi, d_min_m=dmin, K_max=kmax, multipliers=_MULTIPLIERS.copy(),
                values=[hi*v for v in _MULTIPLIERS] if kmax else [0.], representative=.003*hi)


def greedy_step(rates_now, previous_index, distances, feasible, *, slots,
                penalty_bits_per_use, reference_distance_m):
    rates = np.asarray(rates_now, dtype=float)
    distance, graph = np.asarray(distances, dtype=float), np.asarray(feasible)
    if (rates.ndim != 1 or not len(rates) or not np.isfinite(rates).all() or np.any(rates < 0)
            or distance.shape != (len(rates),len(rates)) or not np.isfinite(distance).all()
            or np.any(distance < 0) or not np.array_equal(distance,distance.T)
            or np.any(np.diag(distance) != 0) or graph.shape != distance.shape
            or graph.dtype != np.dtype(bool) or not np.array_equal(graph,graph.T) or not np.diag(graph).all()):
        raise ValueError('Invalid rates, transition distances or feasible graph')
    if not isinstance(slots, (int,np.integer)) or isinstance(slots,(bool,np.bool_)) or slots <= 0:
        raise ValueError('Slots must be a positive integer')
    penalty = scalar(penalty_bits_per_use,'movement penalty',nonnegative=True)
    reference = scalar(reference_distance_m,'reference distance',positive=True)
    if previous_index is None:
        return int(np.argmax(rates))
    if (not isinstance(previous_index,(int,np.integer)) or isinstance(previous_index,(bool,np.bool_))
            or not 0 <= previous_index < len(rates)):
        raise ValueError('Invalid previous position')
    scores = rates-slots*penalty*distance[previous_index]/reference
    return int(np.argmax(np.where(graph[previous_index],scores,-np.inf)))


def _mission(S, positions, slot_duration_s, max_speed_m_per_s, penalty_bits_per_use, reference_distance_m):
    rates = np.asarray(S,dtype=float)
    if rates.ndim != 2 or not all(rates.shape) or not np.isfinite(rates).all() or np.any(rates < 0):
        raise ValueError('Usable SKR must be nonempty finite nonnegative JxNt')
    distances = transition_distances(positions)
    if len(distances) != len(rates):
        raise ValueError('Position/SKR table sizes differ')
    dt = scalar(slot_duration_s,'slot duration',positive=True)
    speed = scalar(max_speed_m_per_s,'maximum speed',nonnegative=True)
    penalty = scalar(penalty_bits_per_use,'movement penalty',nonnegative=True)
    reference = scalar(reference_distance_m,'reference distance',positive=True)
    return rates,distances,distances <= speed*dt,penalty,reference


def _path_result(S, path, distance, feasible, penalty, reference):
    legs = distance[path[:-1],path[1:]]
    if not feasible[path[:-1],path[1:]].all():
        raise ValueError('Infeasible trajectory transition')
    rates = S[path,np.arange(S.shape[1])]
    flight = float(legs.sum())
    return dict(path=path,rates=rates,average_skr=float(rates.mean()),total_flight_distance_m=flight,
                penalized_objective=float(rates.mean())-penalty*flight/reference,
                penalty_bits_per_use=penalty,max_transition_m=float(legs.max()) if len(legs) else 0.)


def greedy_trajectory(S, positions, *, slot_duration_s,max_speed_m_per_s,
                      penalty_bits_per_use,reference_distance_m):
    rates,distance,feasible,penalty,reference = _mission(S,positions,slot_duration_s,max_speed_m_per_s,
                                                       penalty_bits_per_use,reference_distance_m)
    slots = rates.shape[1]
    path = np.empty(slots,dtype=int)
    for slot in range(slots):
        path[slot] = greedy_step(rates[:,slot],None if slot == 0 else int(path[slot-1]),distance,feasible,
                                 slots=slots,penalty_bits_per_use=penalty,reference_distance_m=reference)
    return _path_result(rates,path,distance,feasible,penalty,reference)


def compare_paths(S,blocked,positions,*,slot_duration_s,max_speed_m_per_s,
                  penalty_bits_per_use,reference_distance_m):
    rates,distance,feasible,penalty,reference = _mission(S,positions,slot_duration_s,max_speed_m_per_s,
                                                       penalty_bits_per_use,reference_distance_m)
    blocked = np.asarray(blocked)
    if blocked.shape != rates.shape or blocked.dtype != np.dtype(bool) or np.any(rates[blocked] != 0):
        raise ValueError('Boolean blockage matrix must match rates and blocked rates must be exactly zero')
    kwargs=dict(slot_duration_s=slot_duration_s,max_speed_m_per_s=max_speed_m_per_s,
                penalty_bits_per_use=penalty,reference_distance_m=reference)
    stationary,_ = best_stationary(rates)
    paths = dict(Stationary=np.full(rates.shape[1],stationary,dtype=int),
                 Greedy=greedy_trajectory(rates,positions,**kwargs)['path'],
                 DP=optimize_trajectory(rates,positions,**kwargs)['path'])
    summaries,series = [],[]
    for strategy,path in paths.items():
        result = _path_result(rates,path,distance,feasible,penalty,reference)
        selected_blocked = blocked[path,np.arange(rates.shape[1])]
        summaries.append(dict(strategy=strategy,average_skr_bits_per_use=result['average_skr'],
                              total_distance_m=result['total_flight_distance_m'],objective_bits_per_use=result['penalized_objective'],
                              clear_slots=int((~selected_blocked).sum()),blocked_slots=int(selected_blocked.sum()),
                              positive_slots=int((result['rates']>0).sum()),availability=float(np.mean(result['rates']>0)),
                              repositionings=int(np.count_nonzero(np.diff(path))),initial_position_index=int(path[0]),
                              final_position_index=int(path[-1]),max_transition_m=result['max_transition_m']))
        cumulative = np.cumsum(result['rates'])/rates.shape[1]
        for n,index in enumerate(path):
            series.append(dict(strategy=strategy,slot=n+1,position_index=int(index),x_m=float(positions[index][0]),
                               y_m=float(positions[index][1]),blocked=bool(selected_blocked[n]),usable_skr=float(result['rates'][n]),
                               leg_distance_m=0. if n==0 else float(distance[path[n-1],index]),
                               cumulative_normalized_skr=float(cumulative[n])))
    dp = summaries[-1]['objective_bits_per_use']
    if any(dp < row['objective_bits_per_use'] and not math.isclose(dp,row['objective_bits_per_use'],abs_tol=1e-12,rel_tol=1e-12)
           for row in summaries[:-1]):
        raise ValueError('DP objective is inferior to a feasible comparison path')
    return summaries,paths,series
