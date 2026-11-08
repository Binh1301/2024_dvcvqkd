"""Shared feasibility and terminal evaluation used by every algorithm."""
from dataclasses import dataclass
import math
import numpy as np
from .finite_size import finite_key
from .waypoint_graph import WaypointGraph


class InfeasibleProblem(ValueError):
    """No permitted energy-feasible terminal, distinct from invalid inputs."""


@dataclass
class Scenario:
    graph: WaypointGraph
    rates: np.ndarray
    z: np.ndarray
    budget: float
    m0: float
    epsilon: float
    terminal_index: int | None = None

    def __post_init__(self):
        self.rates, self.z = np.array(self.rates, float, copy=True), np.array(self.z, copy=True)
        count = len(self.graph.positions)
        if self.z.ndim != 2 or self.z.shape[1] != count or not np.isin(self.z, [0, 1]).all():
            raise ValueError('Availability must be a binary slots x waypoints array')
        if self.rates.shape not in ((count,), self.z.shape) or not np.isfinite(self.rates).all():
            raise ValueError('Finite SKR (bits/use) must be waypoints or slots x waypoints, matching availability')
        self.rates.setflags(write=False)
        self.z.setflags(write=False)
        if not np.isfinite(self.budget) or self.budget <= 0:
            raise ValueError('Energy budget must be finite and positive')
        finite_key(0., 0, self.m0, self.epsilon)
        if self.terminal_index is not None and (int(self.terminal_index) != self.terminal_index or not 0 <= self.terminal_index < count):
            raise ValueError('Terminal waypoint index outside graph')
        if self.horizon < 1:
            raise InfeasibleProblem('Problem infeasible: no K>=1 inside energy/prediction horizon')

    @property
    def horizon(self):
        return min(len(self.z), math.floor(self.budget/self.graph.min_cost))

    def rate_at(self, slot: int, waypoint: int) -> float:
        """Zero-based row slot is destination q_k at t_k=(slot+1)*dt."""
        if (isinstance(slot, (bool, np.bool_)) or not isinstance(slot, (int, np.integer)) or not 0 <= slot < self.horizon
                or isinstance(waypoint, (bool, np.bool_)) or not isinstance(waypoint, (int, np.integer))
                or not 0 <= waypoint < len(self.graph.positions)):
            raise ValueError('Rate query needs a valid zero-based slot and waypoint')
        return float(self.rates[waypoint] if self.rates.ndim == 1 else self.rates[slot, waypoint])


def evaluate_path(s: Scenario, path) -> dict:
    path = list(path)
    if len(path) < 2 or path[0] != s.graph.initial or len(path)-1 > s.horizon:
        raise ValueError('Trajectory requires q0 and at least one feasible slot')
    if any(isinstance(j, bool) or int(j) != j or j < 0 or j >= len(s.graph.positions) for j in path):
        raise ValueError('Invalid waypoint indices')
    energy, a, u, rows = 0., 0., 0, []
    for k, (i, j) in enumerate(zip(path, path[1:]), 1):
        edge = s.graph.costs[i, j]
        energy += float(edge)
        if not np.isfinite(edge) or energy > s.budget:
            raise ValueError('Trajectory violates speed or cumulative energy constraint')
        clear = int(s.z[k-1, j])
        u += clear
        a += clear*s.rate_at(k-1, j)
        key = finite_key(a, u, s.m0, s.epsilon)
        rows.append(dict(k=k, time_s=k*s.graph.dt, waypoint=int(j), x_m=float(s.graph.positions[j, 0]),
                         y_m=float(s.graph.positions[j, 1]), clear=clear, energy_j=energy,
                         remaining_energy_j=s.budget-energy, unblocked_slots=u, blocked_slots=k-u,
                         a=float(a), average_skr_bits_s=key['key_bits']/(k*s.graph.dt), **key))
    return dict(K=len(path)-1, mission_time_s=(len(path)-1)*s.graph.dt,
                path_indices=[int(j) for j in path], trajectory_m=s.graph.positions[path].tolist(),
                series=rows, **{k: v for k, v in rows[-1].items() if k not in ('k', 'time_s', 'waypoint', 'x_m', 'y_m', 'clear')})


def selected_solutions(s: Scenario, paths, classification: str) -> dict:
    best = {'P1': None, 'P2': None}
    for path in paths:
        if s.terminal_index is not None and path[-1] != s.terminal_index:
            continue
        result = evaluate_path(s, path)
        for objective, metric in (('P1', 'average_skr_bits_s'), ('P2', 'key_bits')):
            value = result[metric]
            candidate = dict(result, objective_value=value, classification=classification)
            old = best[objective]
            if old is None or (-value, result['K'], result['energy_j'], result['path_indices']) < (-old['objective_value'], old['K'], old['energy_j'], old['path_indices']):
                best[objective] = candidate
    if any(value is None for value in best.values()):
        raise InfeasibleProblem('Problem infeasible: no feasible trajectory reaches a permitted terminal')
    return best
