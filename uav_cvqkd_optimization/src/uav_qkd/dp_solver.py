"""Multi-label graph DP; dominance only at identical (k,j,u)."""
from dataclasses import dataclass
import numpy as np
from .evaluation import Scenario, selected_solutions, InfeasibleProblem
from .finite_size import finite_key


@dataclass(frozen=True)
class Label:
    e: float
    a: float
    j: int
    k: int
    u: int
    previous: 'Label | None'


def pareto_prune(labels: list[Label]) -> list[Label]:
    """Strict float64 dominance, no tolerance/quantization; first duplicate wins."""
    ordered = sorted(labels, key=lambda label: (label.e, -label.a))
    keep, best = [], -np.inf
    for label in ordered:
        if label.a > best:
            keep.append(label)
            best = label.a
    return keep


def backtrack(label: Label) -> list[int]:
    path = []
    while label is not None:
        path.append(label.j)
        label = label.previous
    return path[::-1]


def solve_dp(s: Scenario, *, label_cap: int | None = None, dominance: bool = True) -> dict:
    if label_cap is not None and (isinstance(label_cap, bool) or int(label_cap) != label_cap or label_cap < 1):
        raise ValueError('Approximate label cap must be a positive integer')
    initial = Label(0., 0., s.graph.initial, 0, 0, None)
    previous = {(initial.j, 0): [initial]}
    terminals = {'P1': None, 'P2': None}
    values = {'P1': -np.inf, 'P2': -np.inf}
    generated, dominated, discarded, peak = 0, 0, 0, 1
    for k in range(1, s.horizon+1):
        current = {}
        for (i, u), labels in sorted(previous.items()):
            for old in labels:
                for j in s.graph.successors[i]:
                    e = old.e + float(s.graph.costs[i, j])
                    if e > s.budget:
                        continue
                    clear = int(s.z[k-1, j])
                    new = Label(e, old.a+clear*s.rate_at(k-1, j), j, k, u+clear, old)
                    current.setdefault((j, new.u), []).append(new)
                    generated += 1
        for state, labels in current.items():
            keep = pareto_prune(labels) if dominance else labels
            dominated += len(labels)-len(keep)
            if label_cap is not None and len(keep) > label_cap:
                discarded += len(keep)-label_cap
                keep = sorted(keep, key=lambda label: (-label.a, label.e))[:label_cap]
            current[state] = keep
            for label in keep:
                if s.terminal_index is not None and label.j != s.terminal_index:
                    continue
                key = finite_key(label.a, label.u, s.m0, s.epsilon)['key_bits']
                for objective, value in [('P1', key/(k*s.graph.dt)), ('P2', key)]:
                    old = terminals[objective]
                    if value > values[objective] or (value == values[objective] and old is not None and
                            (k, label.e, backtrack(label)) < (old.k, old.e, backtrack(old))):
                        values[objective], terminals[objective] = value, label
        peak = max(peak, sum(map(len, current.values())))
        previous = current
        if not current:
            break
    if terminals['P1'] is None:
        raise InfeasibleProblem('Problem infeasible: no K>=1 feasible terminal state')
    classification = 'exact-on-graph' if label_cap is None else 'approximate'
    paths = [backtrack(label) for label in terminals.values()]
    return dict(method='Pareto DP', classification=classification,
                solutions=selected_solutions(s, paths, classification),
                diagnostics=dict(generated_labels=generated, dominated_labels=dominated,
                                 heuristic_discarded_labels=discarded, peak_frontier_labels=peak,
                                 horizon=s.horizon, label_cap=label_cap,
                                 dominance='strict float64 within identical k,j,u; first identical duplicate retained'))
