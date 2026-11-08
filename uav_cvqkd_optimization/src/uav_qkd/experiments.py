"""Reproducible four-method experiments, prior calibration and scoped sweeps."""
import copy
import csv
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
import threading
import time
import tracemalloc
import numpy as np
import psutil
from .config import build_scenario, SYNTHETIC
from .baselines import solve_baseline
from .dp_solver import solve_dp
from .evaluation import InfeasibleProblem


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def write_csv(path, rows, *, data_status):
    rows = [dict(data_status=data_status, **row) for row in rows]
    if not rows:
        return
    names = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, names)
        writer.writeheader()
        writer.writerows(rows)


def measured(function):
    """Per-call Python allocation peak and sampled process RSS, including tracing overhead."""
    process = psutil.Process()
    initial = process.memory_info().rss
    peak = [initial]
    stop = threading.Event()

    def sample():
        while not stop.wait(.01):
            peak[0] = max(peak[0], process.memory_info().rss)

    thread = threading.Thread(target=sample, daemon=True)
    tracemalloc.start()
    thread.start()
    start = time.perf_counter()
    try:
        result = function()
        elapsed = time.perf_counter()-start
        _, python_peak = tracemalloc.get_traced_memory()
        peak[0] = max(peak[0], process.memory_info().rss)
    finally:
        stop.set()
        thread.join()
        tracemalloc.stop()
    result.update(runtime_s=elapsed, python_peak_bytes=python_peak,
                  sampled_peak_rss_bytes=peak[0], start_rss_bytes=initial,
                  sampled_incremental_rss_bytes=peak[0]-initial)
    return result


def run_methods(s, c, weight: float, *, measure=True):
    methods = [(name, lambda name=name: solve_baseline(s, name, weight))
               for name in ('Stationary', 'SKR-Greedy', 'Energy-Aware Greedy')]
    cap = c['dp']['label_cap'] if c['dp']['mode'] == 'approximate' else None
    methods.append(('Pareto DP', lambda: solve_dp(s, label_cap=cap)))
    def safely(name, fn):
        try:
            return dict(status='FEASIBLE', **fn())
        except InfeasibleProblem as error:
            return dict(method=name, status='INFEASIBLE', reason=str(error), solutions={},
                        classification=('approximate' if cap is not None else 'exact-on-graph') if name == 'Pareto DP' else 'heuristic')
    return [measured(lambda name=name, fn=fn: safely(name, fn)) if measure else safely(name, fn)
            for name, fn in methods]


def calibrate_lambda(c):
    g = c['greedy']
    if g['selection'] == 'configured_prior':
        weight = g['lambda_bits_per_j']
        if weight is None or not np.isfinite(weight) or weight < 0:
            raise ValueError('A finite nonnegative prior lambda in bits/J is required')
        return float(weight), dict(selection='configured_prior', provenance=g.get('lambda_provenance'), sweep=[])
    if g['selection'] != 'synthetic_calibration_p2' or c['mode'] != 'synthetic':
        raise ValueError('Data-driven lambda selection is allowed only on the separate synthetic calibration scenario')
    calibration = copy.deepcopy(c)
    rng = np.random.default_rng(g['calibration_seed'])
    for cluster in calibration['cloud']['clusters']:
        cluster['center'] = (np.array(cluster['center'])+rng.normal(0, g['calibration_center_jitter_m'], 2)).tolist()
    scenario, _ = build_scenario(calibration)
    rows = []
    for weight in g['lambda_sweep']:
        result = solve_baseline(scenario, 'Energy-Aware Greedy', weight)
        rows.append(dict(lambda_bits_per_j=float(weight),
                         calibration_P1=result['solutions']['P1']['objective_value'],
                         calibration_P2=result['solutions']['P2']['objective_value']))
    if not rows:
        raise ValueError('Lambda sweep must not be empty')
    chosen = min(rows, key=lambda row: (-row['calibration_P2'], row['lambda_bits_per_j']))
    return chosen['lambda_bits_per_j'], dict(selection='synthetic independent-center calibration, maximize P2; smallest lambda on ties',
                  calibration_seed=g['calibration_seed'], calibration_clusters=calibration['cloud']['clusters'], sweep=rows)


def summary_rows(runs):
    for run in runs:
        if run.get('status') == 'INFEASIBLE':
            for objective in ('P1', 'P2'):
                yield dict(method=run['method'], objective=objective, status='INFEASIBLE',
                           reason=run['reason'], objective_value=None, classification=run['classification'],
                           runtime_s=run.get('runtime_s'), python_peak_bytes=run.get('python_peak_bytes'))
            continue
        for objective, solution in run['solutions'].items():
            yield dict(method=run['method'], objective=objective, status='FEASIBLE',
                       **{key: value for key, value in solution.items() if key not in ('series', 'path_indices', 'trajectory_m')},
                       runtime_s=run.get('runtime_s'), python_peak_bytes=run.get('python_peak_bytes'),
                       sampled_peak_rss_bytes=run.get('sampled_peak_rss_bytes'),
                       lambda_bits_per_j=run.get('lambda_bits_per_j'))


def sensitivity_runs(c, weight):
    settings = c.get('sensitivities', {})
    rows = []
    groups = [('energy', 'energy_budget_j'), ('threshold', 'thresholds_mg_m3'),
              ('resolution', 'waypoint_spacings_m'), ('pruning', 'label_caps')]
    for kind, key in groups:
        for value in settings.get(key, []):
            if kind == 'pruning' and value is None and c['dp']['mode'] == 'approximate':
                continue
            variant = copy.deepcopy(c)
            if kind == 'energy':
                variant['energy_budget_j'] = value
            elif kind == 'threshold':
                variant['cloud']['threshold_mg_m3'] = value
            elif kind == 'resolution':
                if variant['graph']['kind'] not in ('lattice', 'restricted_lattice'):
                    raise ValueError('Resolution sweep requires a lattice graph')
                variant['graph']['spacing_m'] = value
            else:
                variant['dp'] = dict(mode='exact' if value is None else 'approximate', label_cap=value)
            scenario, _ = build_scenario(variant)
            runs = run_methods(scenario, variant, weight)
            for row in summary_rows(runs):
                rows.append(dict(sensitivity=kind, parameter='exact' if value is None else value,
                                 waypoints=len(scenario.graph.positions), horizon=scenario.horizon, **row))
    return rows


def run_experiment(c, output, *, figures=True, sensitivities=True):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    scenario, context = build_scenario(c)
    weight, calibration = calibrate_lambda(c)
    runs = run_methods(scenario, c, weight)
    exact = runs[-1] if c['dp']['mode'] == 'exact' and runs[-1]['status'] == 'FEASIBLE' else None
    caps = sorted(set(c.get('sensitivities', {}).get('label_caps', [1, 2]))-{None})
    gaps = []
    for cap in caps if exact is not None else []:
        approximate = measured(lambda: solve_dp(scenario, label_cap=cap))
        for objective in ('P1', 'P2'):
            value = exact['solutions'][objective]['objective_value']
            approx_value = approximate['solutions'][objective]['objective_value']
            gaps.append(dict(label_cap=cap, objective=objective, exact_value=value, approximate_value=approx_value,
                             absolute_gap=value-approx_value, relative_gap=(value-approx_value)/value if value else None,
                             heuristic_discarded_labels=approximate['diagnostics']['heuristic_discarded_labels'],
                             runtime_s=approximate['runtime_s'], python_peak_bytes=approximate['python_peak_bytes']))
    status = SYNTHETIC if c['mode'] == 'synthetic' else 'UNVALIDATED_SECURITY_MODEL — RESEARCH PERFORMANCE APPROXIMATION'
    report = dict(data_status=status, config=c, graph=scenario.graph.diagnostics,
                  horizon=scenario.horizon, energy_horizon=context['energy_horizon'],
                  horizon_scope='energy bound intersected with configured prediction horizon',
                  selected_lambda_bits_per_j=weight, lambda_selection=calibration, runs=runs,
                  approximation_comparison=gaps,
                  approximation_comparison_status='CURRENTLY_VERIFIED_PASS' if exact is not None else 'NOT_RUN: exact comparison requires a separate small exact-mode configuration',
                  information_scope='DP: full predicted horizon; greedy: current slot; all methods: retrospective best prefix',
                  memory_scope='Per-method tracemalloc peak and process RSS sampled at 10 ms; shared precomputation excluded; runtime includes instrumentation')
    write_json(output/'results.json', report)
    write_csv(output/'summary.csv', summary_rows(runs), data_status=status)
    write_csv(output/'lambda_calibration.csv', calibration['sweep'], data_status=status)
    write_csv(output/'approximation_gaps.csv', gaps, data_status=status)
    write_csv(output/'trajectories.csv', [dict(method=run['method'], objective=obj, **row)
              for run in runs for obj, sol in run['solutions'].items() for row in sol['series']], data_status=status)
    np.savez_compressed(output/'scenario.npz', positions=scenario.graph.positions, edge_costs_j=scenario.graph.costs,
                        rates_bits_use=scenario.rates, z=scenario.z, initial_index=scenario.graph.initial, data_status=status)
    points = context['lookup'].points
    write_csv(output/'skr_input.csv', [dict(x_m=float(q[0]), y_m=float(q[1]), skr_bits_per_use=float(r))
                                     for q, r in zip(points, context['lookup'].rates)], data_status=status)
    sweeps = sensitivity_runs(c, weight) if sensitivities else []
    write_csv(output/'sensitivities.csv', sweeps, data_status=status)
    if figures:
        from .visualization import plot_all
        plot_all(output, report, scenario, context, sweeps)
    package = Path(__file__).resolve().parents[2]
    source_hashes = {str(p.relative_to(package)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((package/'src').rglob('*.py'))}
    input_files = [Path(c['_config_path'])] if c.get('_config_path') else []
    for section in ('lookup', 'cloud'):
        if c[section].get('file'):
            input_files.append(Path(c['_config_path']).parent/c[section]['file'])
    write_json(output/'input_manifest.json', dict(source_sha256=source_hashes,
               input_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in input_files},
               python=platform.python_version(), dependencies={name: version(name) for name in ('numpy', 'scipy', 'matplotlib', 'PyYAML', 'psutil')}))
    hashes = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'output_manifest.json'}
    write_json(output/'output_manifest.json', hashes)
    return report
