"""Exactly the three manuscript baselines with a common prefix evaluator."""
import numpy as np
from .evaluation import Scenario, selected_solutions


def solve_baseline(s: Scenario, method: str, lambda_bits_per_j: float = 0.) -> dict:
    if method not in ('Stationary', 'SKR-Greedy', 'Energy-Aware Greedy'):
        raise ValueError('Unknown baseline method')
    if not np.isfinite(lambda_bits_per_j) or lambda_bits_per_j < 0:
        raise ValueError('Greedy lambda must be nonnegative and finite in bits/J')
    path, prefixes, energy = [s.graph.initial], [], 0.
    for k in range(s.horizon):
        i = path[-1]
        feasible = [j for j in s.graph.successors[i] if energy+s.graph.costs[i, j] <= s.budget]
        if method == 'Stationary':
            feasible = [i] if i in feasible else []
        if not feasible:
            break
        weight = lambda_bits_per_j if method == 'Energy-Aware Greedy' else 0.
        j = min(feasible, key=lambda j: (-(s.m0*s.z[k, j]*s.rate_at(k, j)-weight*s.graph.costs[i, j]),
                                          s.graph.costs[i, j], j))
        energy += float(s.graph.costs[i, j])
        path.append(j)
        prefixes.append(path.copy())
    return dict(method=method, classification='heuristic',
                lambda_bits_per_j=lambda_bits_per_j if method == 'Energy-Aware Greedy' else None,
                solutions=selected_solutions(s, prefixes, 'heuristic'),
                diagnostics=dict(evaluated_prefixes=len(prefixes)))
