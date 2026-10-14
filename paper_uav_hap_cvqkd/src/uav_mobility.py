"""Circular-cloud geometry and exact finite-grid dynamic programming."""
from __future__ import annotations

import math
import numpy as np


def scalar(value, name, *, positive=False, nonnegative=False):
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0) or (nonnegative and value < 0):
        raise ValueError(f"Invalid {name}: {value}")
    return value


def xy(value, name):
    value = np.asarray(value, dtype=float)
    if value.shape != (2,) or not np.isfinite(value).all():
        raise ValueError(f"{name} requires two finite horizontal coordinates")
    return value


def candidate_grid(side_m=1000., cells=10):
    side_m = scalar(side_m, "grid side", positive=True)
    if not isinstance(cells, int) or isinstance(cells, bool) or cells <= 0:
        raise ValueError("Grid cells must be a positive integer")
    centers = (np.arange(cells) + .5) * side_m / cells
    return np.array([(x, y) for y in centers for x in centers])


def link_geometry(positions, hap_xy, h_hap, h_uav):
    positions = np.asarray(positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 2 or not len(positions) or not np.isfinite(positions).all():
        raise ValueError("Positions must be a nonempty finite Jx2 array")
    dh = scalar(h_hap, "HAP altitude") - scalar(h_uav, "UAV altitude")
    if dh <= 0:
        raise ValueError("HAP must be above UAV")
    horizontal = np.linalg.norm(positions - xy(hap_xy, "HAP position"), axis=1)
    distances = np.hypot(horizontal, dh)
    return distances, np.arctan2(horizontal, dh)


def path_intersections(positions, hap_xy, h_hap, h_uav, h_cloud):
    h_hap, h_uav, h_cloud = [scalar(v, "altitude") for v in (h_hap, h_uav, h_cloud)]
    if not h_uav < h_cloud < h_hap:
        raise ValueError("Cloud altitude must be strictly between UAV and HAP")
    positions = np.asarray(positions, dtype=float)
    link_geometry(positions, hap_xy, h_hap, h_uav)
    fraction = (h_cloud - h_uav) / (h_hap - h_uav)
    return positions + fraction * (xy(hap_xy, "HAP position") - positions)


def moving_cloud(intersections, times, center, velocity, radius):
    intersections = np.asarray(intersections, dtype=float)
    times = np.asarray(times, dtype=float)
    if intersections.ndim != 2 or intersections.shape[1] != 2 or not np.isfinite(intersections).all():
        raise ValueError("Cloud intersections must be finite Jx2 coordinates")
    if times.ndim != 1 or not len(times) or not np.isfinite(times).all() or (times < 0).any():
        raise ValueError("Cloud times must be finite and nonnegative")
    radius = scalar(radius, "cloud radius", positive=True)
    centers = xy(center, "cloud center") + times[:, None] * xy(velocity, "cloud velocity")
    separation = np.linalg.norm(intersections[:, None, :] - centers[None, :, :], axis=2)
    return separation <= radius, centers


def cloud_transmittance(attenuation_db, blocked):
    loss = scalar(attenuation_db, "cloud attenuation dB", nonnegative=True)
    transmission = 10 ** (-loss / 10) if blocked else 1.
    if transmission <= 0:
        raise ValueError("Cloud attenuation underflows; no silent zero substitution")
    return transmission


def usable_skr(raw_table):
    raw_table = np.asarray(raw_table, dtype=float)
    if raw_table.ndim != 2 or not all(raw_table.shape) or not np.isfinite(raw_table).all():
        raise ValueError("SKR table must be nonempty, finite JxN")
    return np.maximum(raw_table, 0.)


def best_stationary(skr_table):
    usable = usable_skr(skr_table)
    means = usable.mean(axis=1)
    return int(np.argmax(means)), means


def transition_distances(positions):
    positions = np.asarray(positions, dtype=float)
    link_geometry(positions, [0., 0.], 1., 0.)
    return np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)


def optimize_trajectory(skr_table, positions, *, slot_duration_s, max_speed_m_per_s,
                        penalty_bits_per_use, reference_distance_m):
    usable = usable_skr(skr_table)
    distance = transition_distances(positions)
    if len(distance) != len(usable):
        raise ValueError("Position/SKR table sizes differ")
    dt = scalar(slot_duration_s, "slot duration", positive=True)
    speed = scalar(max_speed_m_per_s, "maximum speed", nonnegative=True)
    penalty = scalar(penalty_bits_per_use, "movement penalty", nonnegative=True)
    reference = scalar(reference_distance_m, "reference distance", positive=True)
    feasible = distance <= speed * dt
    slots, count = usable.shape[1], usable.shape[0]
    values = usable[:, 0] / slots
    predecessors = np.full((slots, count), -1, dtype=int)
    for n in range(1, slots):
        # Rows are predecessors i; columns are destinations j.
        proposals = values[:, None] - penalty * distance / reference
        proposals = np.where(feasible, proposals, -np.inf)
        predecessors[n] = np.argmax(proposals, axis=0)
        values = usable[:, n] / slots + proposals[predecessors[n], np.arange(count)]
    path = np.empty(slots, dtype=int)
    path[-1] = int(np.argmax(values))
    for n in range(slots - 1, 0, -1):
        path[n-1] = predecessors[n, path[n]]
    legs = distance[path[:-1], path[1:]]
    if (legs > speed * dt).any():
        raise ValueError("DP returned an infeasible transition")
    rates = usable[path, np.arange(slots)]
    flight = float(legs.sum())
    objective = float(rates.mean()) - penalty * flight / reference
    if not math.isclose(objective, float(values[path[-1]]), abs_tol=1e-12, rel_tol=1e-12):
        raise ValueError("DP/backtracking objective disagreement")
    return dict(path=path, rates=rates, average_skr=float(rates.mean()),
                total_flight_distance_m=flight, penalized_objective=objective,
                penalty_bits_per_use=penalty, max_transition_m=float(legs.max()) if len(legs) else 0.)
