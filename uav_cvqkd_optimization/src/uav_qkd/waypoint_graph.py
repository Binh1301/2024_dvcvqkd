"""Independent waypoint graph with precomputed, convergence-checked edge costs."""
from dataclasses import dataclass
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order
from .propulsion import EnergyModel


def regular_waypoints(area, spacing: float, initial) -> np.ndarray:
    area = np.asarray(area, float)
    if area.shape != (2,) or not np.isfinite(area).all() or (area <= 0).any() or not np.isfinite(spacing) or spacing <= 0:
        raise ValueError('Area and waypoint spacing must be positive and finite')
    axes = [np.unique(np.r_[np.arange(0, side, spacing), side]) for side in area]
    X, Y = np.meshgrid(*axes)
    return np.unique(np.vstack([np.c_[X.ravel(), Y.ravel()], np.asarray(initial)]), axis=0)


@dataclass
class WaypointGraph:
    positions: np.ndarray
    initial: int
    costs: np.ndarray
    successors: list
    dt: float
    energy: EnergyModel
    diagnostics: dict

    @property
    def min_cost(self):
        return float(self.costs[np.isfinite(self.costs)].min())

    @classmethod
    def build(cls, positions, initial, area, dt: float, energy: EnergyModel,
              *, energy_tolerance_j: float = .001, max_refinements: int = 4):
        q, q0, area = np.asarray(positions, float), np.asarray(initial, float), np.asarray(area, float)
        if q.ndim != 2 or q.shape[1] != 2 or len(q) == 0 or q0.shape != (2,) or area.shape != (2,) or not np.isfinite(q).all() or not np.isfinite([*q0, *area, dt, energy_tolerance_j]).all() or (area <= 0).any() or dt <= 0 or energy_tolerance_j <= 0:
            raise ValueError('Invalid graph geometry, duration or energy convergence tolerance')
        if (q < 0).any() or (q > area).any() or len(np.unique(q, axis=0)) != len(q):
            raise ValueError('Waypoints must be unique and inside the operating area')
        found = np.flatnonzero(np.all(q == q0, axis=1))
        if len(found) != 1:
            raise ValueError('Initial position must appear exactly once in graph')
        distances = np.linalg.norm(q[:, None, :]-q[None, :, :], axis=2)
        costs = energy.energy(distances.ravel(), dt).reshape(distances.shape)
        finite = np.isfinite(costs)
        delta, history = np.inf, []
        for _ in range(max_refinements):
            finer = EnergyModel(energy.params, samples=2*energy.samples-1)
            new = finer.energy(distances.ravel(), dt).reshape(distances.shape)
            delta = float(np.max(abs(costs[finite]-new[finite])))
            history.append(dict(samples=finer.samples, max_change_j=delta))
            costs, energy = new, finer
            if delta <= energy_tolerance_j:
                break
        if delta > energy_tolerance_j:
            raise ValueError(f'Edge energy grid convergence not established: change {delta} J')
        if not (costs[finite] > 0).all():
            raise ValueError('Every feasible edge must have positive energy')
        successors = [np.flatnonzero(row).tolist() for row in finite]
        reachable = breadth_first_order(csr_matrix(finite), int(found[0]), directed=True, return_predecessors=False)
        diagnostics = dict(waypoints=len(q), movement_edges=int(finite.sum()-len(q)),
                           reachable_waypoints=len(reachable), successors=[len(s) for s in successors],
                           energy_refinement=history, energy_tolerance_j=energy_tolerance_j,
                           velocity_samples=energy.samples,
                           warning='No feasible movement edges' if finite.sum() == len(q) else None)
        return cls(q, int(found[0]), costs, successors, dt, energy, diagnostics)
