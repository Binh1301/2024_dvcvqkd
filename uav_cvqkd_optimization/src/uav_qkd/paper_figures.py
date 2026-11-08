"""Provenance-gated IEEE figures from existing models and sealed saved results.

python -m uav_qkd.paper_figures --config configs/paper.yaml --output figures/paper
No optimizer or experiment runner is invoked. BLOCKED figures have no images.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from .config import load_config, build_scenario
from .propulsion import PropulsionParams, propulsion_power, EnergyModel
from .finite_size import finite_key
from .verify import verify_results

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT/'results/paper_configuration_audit_20261107'
STYLES = {
    'Stationary': dict(color='#777777', linestyle='-', hatch=''),
    'SKR-Greedy': dict(color='#0072b2', linestyle='--', hatch='//'),
    'Energy-Aware Greedy': dict(color='#e69f00', linestyle='-.', hatch='\\\\'),
    'Pareto DP': dict(color='#009e73', linestyle=':', hatch='xx'),
}
LABELS = {'Stationary': 'Stationary', 'SKR-Greedy': 'SKR-Greedy',
          'Energy-Aware Greedy': 'Energy-Aware Greedy', 'Pareto DP': 'Proposed DP'}
CATALOG = [
    ('fig01_rotor_power', 'Rotor propulsion power and its sampled lower convex envelope. The source parameter version is retained; this model illustration does not constitute a mission result.'),
    ('fig02_cloud_maps', 'Gaussian CLWC and binary cloud coverage at the configured times. Each binary mask thresholds the identical CLWC samples. Coverage alone does not determine three-dimensional optical-path intersection.'),
    ('fig03_skr_lookup', 'Native spatial SKR samples in bits per channel use, without smoothing, clipping or new optimization. Finite-catalog maxima are not continuous global optima.'),
    ('fig04_trajectory_P1', 'Selected P1 trajectories maximizing estimated average key rate on the supplied graph and horizon. Coincident trajectories may overlap.'),
    ('fig05_trajectory_P2', 'Selected P2 trajectories maximizing estimated total key on the supplied graph and horizon. Coincident trajectories may overlap.'),
    ('fig06_energy', 'Cumulative propulsion energy along the separately selected P1 and P2 trajectory prefixes. Curves end at their actual selected stopping times.'),
    ('fig07_finite_size', 'Accumulated valid signals, asymptotic contribution, accumulated-block finite-size penalty and estimated key along P2 prefixes. The penalty is applied once to each accumulated prefix, not summed slotwise; this is a performance approximation, not a composable-security proof.'),
    ('fig08_key_comparison', 'Selected P1 average estimated key rate and P2 total estimated key for the four methods. DP uses future cloud predictions; greedy actions use current-slot information. All methods use retrospective prefix selection.'),
    ('fig09_runtime_memory', 'Recorded method runtime, Python allocation peak and sampled process RSS from the saved experiment. Shared precomputation is excluded; runtime includes instrumentation and RSS is sampled rather than an exact continuous peak.'),
    ('fig10_sensitivity', 'Recorded sensitivity to energy budget, CLWC threshold, waypoint spacing and DP label cap. Approximate and finite-graph results do not establish continuous global optimality.'),
]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'{path}: expected a JSON mapping')
    return value


def _config_values(config):
    return {k: v for k, v in config.items() if k != '_config_path'}


def _number(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError(f'{name} requires a finite recorded numerical value')
    if minimum is not None and value < minimum:
        raise ValueError(f'{name} is below {minimum}')
    return value


def validate_report(report):
    """Check stored quantities using the existing accumulated-block evaluator."""
    config = report['config']
    runs = report['runs']
    if len(runs) != 4 or {r['method'] for r in runs} != set(STYLES):
        raise ValueError('Exactly one recorded result for each of the four methods is required')
    for run in runs:
        for name in ('runtime_s', 'python_peak_bytes', 'sampled_peak_rss_bytes'):
            _number(run.get(name), name, 0)
        if run['classification'] not in ('heuristic', 'exact-on-graph', 'approximate'):
            raise ValueError('Missing or unsupported algorithm classification')
        if run.get('status') == 'INFEASIBLE':
            if run['solutions']:
                raise ValueError('Infeasible method must not contain fabricated solutions')
            continue
        if set(run['solutions']) != {'P1', 'P2'}:
            raise ValueError('Both selected objective prefixes are required')
        for objective, solution in run['solutions'].items():
            rows = solution['series']
            q = np.asarray(solution['trajectory_m'], float)
            if not rows or len(rows) != solution['K'] or q.shape != (len(rows)+1, 2) or not np.isfinite(q).all():
                raise ValueError('Invalid trajectory shape or stopping prefix')
            previous_energy = 0.
            for k, row in enumerate(rows, 1):
                expected = finite_key(row['a'], row['unblocked_slots'], config['m0'], config['epsilon'])
                for name, value in expected.items():
                    if not np.isclose(_number(row.get(name), name), value, rtol=1e-12, atol=1e-8):
                        raise ValueError(f'Accumulated {name} inconsistent with the stored signals/contribution')
                energy = _number(row.get('energy_j'), 'energy_j', 0)
                if energy < previous_energy or energy > config['energy_budget_j']:
                    raise ValueError('Cumulative energy violates its recorded budget')
                previous_energy = energy
                if row['k'] != k or row['time_s'] != k*config['dt'] or row['blocked_slots']+row['unblocked_slots'] != k:
                    raise ValueError('Invalid recorded slot/time/availability count')
            for name in ('energy_j', 'valid_signals', 'asymptotic_bits', 'penalty_bits', 'key_bits', 'average_skr_bits_s'):
                if not np.isclose(solution[name], rows[-1][name], rtol=1e-12, atol=1e-8):
                    raise ValueError(f'Terminal {name} differs from its final cumulative row')
            metric = 'average_skr_bits_s' if objective == 'P1' else 'key_bits'
            if not np.isclose(solution['objective_value'], solution[metric], rtol=1e-12, atol=1e-8):
                raise ValueError('Objective units/value mismatch')


def _readiness_reasons(config):
    reasons = []
    try:
        current = _json(AUDIT/'audit_summary.json')
        lookup = _json(AUDIT/'skr_lookup_audit.json')
        if current['paper_experiment_status'] == 'NOT_RUN':
            reasons.append('Paper-mode remains NOT_RUN in the source-configuration audit.')
        if not lookup.get('paper_admissible'):
            reasons.append('The 2,601-point lookup remains INSUFFICIENT_EVIDENCE; source/security readiness is not established.')
    except (OSError, ValueError, KeyError) as error:
        reasons.append(f'Required readiness audit unavailable or invalid: {error}')
    missing = [k for k in ('initial_m', 'hap_m', 'energy_budget_j', 'm0', 'epsilon', 'graph', 'cloud', 'blockage', 'max_horizon') if config.get(k) is None]
    if missing:
        reasons.append('Missing required scientific inputs: '+', '.join(missing))
    return reasons


def _validate_seals(directory, report):
    """The legacy verifier checks listed hashes; require the consumed files too."""
    manifest = _json(directory/'output_manifest.json')
    required = {'results.json', 'input_manifest.json', 'scenario.npz', 'skr_input.csv'}
    if (directory/'sensitivities.csv').exists():
        required.add('sensitivities.csv')
    if not required <= set(manifest):
        raise ValueError('Incomplete saved-output seal: missing '+', '.join(sorted(required-set(manifest))))
    for name in manifest:
        if not (directory/name).resolve().is_relative_to(directory.resolve()):
            raise ValueError('Output manifest path escapes the selected result directory')
    inputs = _json(directory/'input_manifest.json')
    sources = {name.replace('\\', '/'): digest for name, digest in inputs.get('source_sha256', {}).items()}
    required_sources = {f'src/uav_qkd/{name}.py' for name in
                        ('config', 'propulsion', 'finite_size', 'evaluation', 'cloud_model', 'blockage',
                         'skr_lookup', 'waypoint_graph', 'dp_solver', 'baselines', 'experiments', 'verify')}
    if not required_sources <= set(sources):
        raise ValueError('Incomplete producer manifest: required model/evaluation source bindings are absent')
    for name in sources:
        if not (ROOT/name).resolve().is_relative_to(ROOT):
            raise ValueError('Producer manifest path escapes the package directory')
    bound_inputs = {str(Path(name).resolve()) for name in inputs.get('input_sha256', {})}
    if str(Path(report['config']['_config_path']).resolve()) not in bound_inputs:
        raise ValueError('Saved input manifest does not bind the experiment configuration')


def load_figure_inputs(config_path, results_dir, *, exploratory=False):
    """Read and verify saved data; do not generate a realization or optimize a path."""
    config = load_config(config_path)
    directory = Path(results_dir)
    report = _json(directory/'results.json')
    if _config_values(config) != _config_values(report['config']):
        raise ValueError('Selected configuration differs from the saved experiment configuration')
    status = report.get('data_status', '')
    if not exploratory:
        reasons = _readiness_reasons(config)
        if config.get('mode') != 'paper' or 'SYNTHETIC' in status or 'UNVALIDATED' in status or not status:
            reasons.append('EXPLORATORY data cannot be promoted to paper-ready results.')
        if reasons:
            raise ValueError(' '.join(reasons))
    _validate_seals(directory, report)
    validation = verify_results(directory)
    validate_report(report)
    scenario, context = build_scenario(report['config'])
    sweeps = []
    path = directory/'sensitivities.csv'
    if path.exists():
        with path.open(encoding='utf-8', newline='') as f:
            sweeps = list(csv.DictReader(f))
        for row in sweeps:
            if row['method'] not in STYLES or row['data_status'] != status:
                raise ValueError('Sensitivity method/status mismatch')
            if row.get('status') == 'INFEASIBLE':
                continue
            terminal = finite_key(float(row['a']), int(row['unblocked_slots']), config['m0'], config['epsilon'])
            for name, value in terminal.items():
                if not np.isclose(float(row[name]), value, rtol=1e-12, atol=1e-8):
                    raise ValueError(f'Sensitivity {name} inconsistent with the finite-size model')
            expected = terminal['key_bits']/(int(row['K'])*config['dt']) if row['objective']=='P1' else terminal['key_bits']
            if not np.isclose(float(row['objective_value']), expected, rtol=1e-12, atol=1e-8):
                raise ValueError('Sensitivity objective units/value mismatch')
    return dict(config=report['config'], report=report, scenario=scenario, context=context,
                sweeps=sweeps, directory=directory, validation=validation,
                status='EXPLORATORY' if exploratory else 'READY')


def _figure(column, rows=1, cols=1, height=None):
    if column not in ('single', 'double'):
        raise ValueError('Column must be single or double')
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                         'mathtext.fontset': 'stix', 'font.size': 7.5, 'axes.labelsize': 7.5,
                         'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5, 'legend.fontsize': 6.5,
                         'axes.linewidth': .6, 'lines.linewidth': 1.1,
                         'pdf.fonttype': 42, 'ps.fonttype': 42, 'savefig.facecolor': 'white'})
    width = 3.5 if column == 'single' else 7.16
    return plt.subplots(rows, cols, figsize=(width, height or (2.55*rows)), squeeze=False, facecolor='white')


def _runs(data):
    by_name = {run['method']: run for run in data['report']['runs']}
    return [by_name[name] for name in STYLES]


def _line(ax, x, y, name):
    style = STYLES[name]
    return ax.plot(x, y, color=style['color'], linestyle=style['linestyle'], label=LABELS[name])[0]


def _two_panels(column):
    fig, axes = _figure(column, 2 if column=='single' else 1, 1 if column=='single' else 2)
    return fig, axes.ravel()


def plot_fig01_rotor_power(config, column='double'):
    params = PropulsionParams(**config['propulsion'])
    v = np.linspace(0, params.v_max, config['velocity_samples'])
    fig, axes = _figure(column)
    ax = axes[0, 0]
    ax.plot(v, propulsion_power(v, params), color='#777777', linestyle='-', label=r'$P(v)$')
    ax.plot(v, EnergyModel(params, config['velocity_samples']).energy(v, 1.), color='#009e73',
            linestyle='--', label='Numerical lower convex envelope')
    ax.set(xlabel='Speed (m/s)', ylabel='Propulsion power (W)', xlim=(0, params.v_max))
    ax.legend(frameon=False)
    return fig


def plot_fig02_cloud_maps(data, column='double'):
    config = data['config']
    times = config['plot_times_s']
    fig, axes = _figure(column, 2 if column=='double' else len(times), len(times) if column=='double' else 2,
                        height=4.1 if column=='double' else 2.15*len(times))
    gray_axes = list(axes[0]) if column=='double' else list(axes[:, 0])
    binary_axes = list(axes[1]) if column=='double' else list(axes[:, 1])
    # Order axes consistently for data-integrity inspection in either layout.
    fields = [data['context']['field'].grid(*config['area_m'], t)[2] for t in times]
    vmax = max(float(field.max()) for field in fields)
    extent = (0, config['area_m'][0], 0, config['area_m'][1])
    image = None
    for ax, field, t in zip(gray_axes, fields, times):
        image = ax.imshow(field, origin='lower', extent=extent, cmap='Greys', vmin=0, vmax=vmax if vmax else 1,
                          interpolation='nearest', rasterized=True)
        ax.set(title=f'CLWC: t = {t:g} s', xlabel='x (m)', ylabel='y (m)')
    for ax, field, t in zip(binary_axes, fields, times):
        mask = field >= config['cloud']['threshold_mg_m3']
        ax.imshow(mask, origin='lower', extent=extent, cmap=ListedColormap(['white', '#222222']),
                  vmin=0, vmax=1, interpolation='nearest', rasterized=True)
        ax.set(title=f'Blockage: t = {t:g} s', xlabel='x (m)', ylabel='y (m)')
    fig.colorbar(image, ax=gray_axes[-1], fraction=.045, pad=.04, label='CLWC (mg/m³)')
    binary_axes[-1].legend(handles=[Patch(color='#222222', label='Blocking coverage'),
                                   Patch(facecolor='white', edgecolor='black', label='Non-blocking')],
                           loc='lower right', fontsize=5.5)
    return fig


def plot_fig03_skr_lookup(data, column='double'):
    lookup = data['context']['lookup']
    points, rates = lookup.points, lookup.rates
    fig, axes = _figure(column, height=3.0)
    ax = axes[0, 0]
    x, y = np.unique(points[:, 0]), np.unique(points[:, 1])
    if len(x)*len(y) == len(points):
        order = np.lexsort((points[:, 0], points[:, 1]))
        image = ax.pcolormesh(x, y, rates[order].reshape(len(y), len(x)), shading='nearest', cmap='viridis', rasterized=True)
    else:
        image = ax.scatter(points[:, 0], points[:, 1], c=rates, cmap='viridis', s=8, marker='s', rasterized=True)
    ax.set(xlabel='x (m)', ylabel='y (m)', aspect='equal',
           xlim=(points[:, 0].min(), points[:, 0].max()), ylim=(points[:, 1].min(), points[:, 1].max()))
    fig.colorbar(image, ax=ax, label='Asymptotic SKR (bits/use)')
    return fig


def _trajectory(data, column, objective):
    fig, axes = _figure(column, height=3.15)
    ax = axes[0, 0]
    extents = [np.asarray(data['config']['initial_m'], float)[None, :]]
    for run in _runs(data):
        solution = run['solutions'].get(objective)
        if solution is None:
            continue
        points = np.asarray(solution['trajectory_m'])
        extents.append(points)
        _line(ax, points[:, 0], points[:, 1], run['method'])
    ax.scatter(*data['config']['initial_m'], marker='*', s=35, color='black', label='Initial position', zorder=5)
    # Equal physical scales, zoomed to the actual path extent; no coordinates move.
    points = np.vstack(extents)
    span = float(np.ptp(points, axis=0).max())
    if span == 0:
        ax.set_xlim(0, data['config']['area_m'][0])
        ax.set_ylim(0, data['config']['area_m'][1])
    else:
        center = (points.min(axis=0)+points.max(axis=0))/2
        half = .7*span
        ax.set_xlim(center[0]-half, center[0]+half)
        ax.set_ylim(center[1]-half, center[1]+half)
    ax.set(xlabel='x (m)', ylabel='y (m)', aspect='equal', title=f'{objective}: trajectory extent')
    ax.legend(frameon=False, ncol=2)
    return fig


def plot_fig04_trajectory_p1(data, column='double'):
    return _trajectory(data, column, 'P1')


def plot_fig05_trajectory_p2(data, column='double'):
    return _trajectory(data, column, 'P2')


def plot_fig06_energy(data, column='double'):
    fig, axes = _two_panels(column)
    for ax, objective in zip(axes, ('P1', 'P2')):
        for run in _runs(data):
            solution = run['solutions'].get(objective)
            if solution is None:
                continue
            rows = solution['series']
            _line(ax, [0]+[r['time_s'] for r in rows], [0]+[r['energy_j'] for r in rows], run['method'])
        ax.set(title=objective, xlabel='Time (s)', ylabel='Cumulative propulsion energy (J)')
        ax.legend(frameon=False)
    return fig


def plot_fig07_finite_size(data, column='double'):
    fig, axes = _figure(column, 2, 2, height=4.6 if column=='double' else 5.)
    metrics = [('valid_signals', 'Valid signals'), ('asymptotic_bits', 'Asymptotic contribution (bits)'),
               ('penalty_bits', 'Accumulated-block penalty (bits)'), ('key_bits', 'Estimated key length (bits)')]
    for ax, (metric, ylabel) in zip(axes.ravel(), metrics):
        for run in _runs(data):
            sol = run['solutions'].get('P2')
            if sol is None:
                continue
            rows = sol['series']
            _line(ax, [0]+[r['time_s'] for r in rows], [0]+[r[metric] for r in rows], run['method'])
        ax.set(xlabel='Time (s)', ylabel=ylabel)
    axes[0, 0].legend(frameon=False)
    return fig


def _bars(ax, values):
    for i, (name, value) in enumerate(zip(STYLES, values)):
        if value is None:
            ax.text(i, .02, 'INFEASIBLE', rotation=90, ha='center', transform=ax.get_xaxis_transform(), fontsize=5.5)
        else:
            style = STYLES[name]
            ax.bar(i, value, color=style['color'], hatch=style['hatch'], edgecolor='black', linewidth=.4)
    ax.set_xticks(range(4), ['Stationary', 'SKR-Greedy', 'Energy-Aware\nGreedy', 'Proposed DP'], rotation=20)
    ax.set_ylim(bottom=0)


def plot_fig08_key_comparison(data, column='double'):
    fig, axes = _two_panels(column)
    for ax, objective, metric, ylabel in zip(axes, ('P1', 'P2'), ('average_skr_bits_s', 'key_bits'),
                                            ('Average estimated SKR (bits/s)', 'Total estimated key (bits)')):
        _bars(ax, [run['solutions'].get(objective, {}).get(metric) for run in _runs(data)])
        ax.set(title=objective, ylabel=ylabel)
    return fig


def plot_fig09_runtime_memory(data, column='double'):
    fig, axes = _figure(column, 3 if column=='single' else 1, 1 if column=='single' else 3,
                        height=6.8 if column=='single' else 2.9)
    for ax, metric, unit, factor in zip(axes.ravel(), ('runtime_s', 'python_peak_bytes', 'sampled_peak_rss_bytes'),
                                        ('Recorded runtime (s)', 'Peak Python allocation (MiB)', 'Sampled process RSS (MiB)'), (1., 2**20, 2**20)):
        _bars(ax, [_number(run.get(metric), metric, 0)/factor for run in _runs(data)])
        ax.set_ylabel(unit)
    return fig


def plot_fig10_sensitivity(data, column='double', objective='P2'):
    if objective not in ('P1', 'P2'):
        raise ValueError('Sensitivity objective must be P1 or P2')
    fig, axes = _figure(column, 2, 2, height=4.5 if column=='double' else 5.)
    for ax, kind, xlabel in zip(axes.ravel(), ('energy', 'threshold', 'resolution', 'pruning'),
                                ('Energy budget (J)', 'CLWC threshold (mg/m³)', 'Waypoint spacing (m)', 'Labels per state')):
        for name in STYLES:
            rows = [r for r in data['sweeps'] if r['sensitivity']==kind and r['objective']==objective and r['method']==name]
            if not rows:
                raise ValueError(f'Missing recorded {kind} sensitivity for {name}/{objective}')
            x = [r['parameter'] for r in rows] if kind=='pruning' else [float(r['parameter']) for r in rows]
            y = [np.nan if r.get('status')=='INFEASIBLE' else float(r['objective_value']) for r in rows]
            _line(ax, x, y, name)
        ax.set(xlabel=xlabel, ylabel='Estimated key (bits)' if objective=='P2' else 'Average estimated SKR (bits/s)')
    axes[0, 0].legend(frameon=False)
    return fig


PLOTTERS = [plot_fig01_rotor_power, plot_fig02_cloud_maps, plot_fig03_skr_lookup,
            plot_fig04_trajectory_p1, plot_fig05_trajectory_p2, plot_fig06_energy,
            plot_fig07_finite_size, plot_fig08_key_comparison, plot_fig09_runtime_memory,
            plot_fig10_sensitivity]


def _rotor_reasons(config_path, config):
    reasons = []
    if config.get('verified_context', {}).get('rotor', {}).get('source_variant') != 'arxiv_v1_2018_not_IEEE_2019_parameter_table':
        reasons.append('Rotor source/version is not bound to the verified parameter audit.')
    try:
        receipt = _json(AUDIT/'configuration_validation.json')
        if receipt['status'] != 'CURRENTLY_VERIFIED_PASS' or receipt['paper_yaml_sha256'] != _sha(config_path):
            reasons.append('Rotor/configuration audit hash is stale or invalid.')
        for name in ('parameter_provenance.md', 'paper_configuration_audit_vi.md'):
            if not (ROOT/'docs'/name).is_file():
                reasons.append(f'Required source documentation missing: {name}')
    except (OSError, ValueError, KeyError) as error:
        reasons.append(f'Required rotor audit unavailable or invalid: {error}')
    return reasons


def generate_figures(config_path, results_dir, output, *, column='double', exploratory=False, sensitivity_objective='P2'):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Refusing to overwrite a nonempty figure directory; choose a new output path')
    config_path = Path(config_path).resolve()
    config_error = None
    try:
        config = load_config(config_path)
    except (OSError, ValueError) as error:
        config, config_error = {}, f'Required configuration unavailable or invalid: {error}'
    if column not in ('single', 'double'):
        raise ValueError('Column must be single or double')
    output.mkdir(parents=True, exist_ok=True)
    input_paths = [config_path, ROOT/'docs/parameter_provenance.md', ROOT/'docs/paper_configuration_audit_vi.md',
                   AUDIT/'configuration_validation.json', AUDIT/'audit_summary.json', AUDIT/'skr_lookup_audit.json']
    data, common_reasons = None, []
    if config_error:
        common_reasons = [config_error]
    elif results_dir is None:
        common_reasons = _readiness_reasons(config)+['No verified saved experiment directory supplied; no new results are generated.']
    else:
        directory = Path(results_dir).resolve()
        input_paths += [directory/name for name in ('results.json', 'input_manifest.json', 'output_manifest.json', 'sensitivities.csv', 'scenario.npz', 'skr_input.csv')]
        try:
            data = load_figure_inputs(config_path, directory, exploratory=exploratory)
        except (ValueError, KeyError, TypeError, OSError) as error:
            common_reasons = [str(error)]
    inputs = {str(p): {'exists': p.is_file(), 'sha256': _sha(p) if p.is_file() else None} for p in input_paths}
    manifests = []
    for index, (stem, caption) in enumerate(CATALOG):
        status = 'EXPLORATORY' if exploratory else 'READY'
        reasons = ([config_error] if config_error else _rotor_reasons(config_path, config) if not exploratory else []) if index==0 else list(common_reasons)
        if index > 0 and data is None and not reasons:
            reasons = ['Verified result data are unavailable.']
        manifest = dict(figure=stem, status='BLOCKED' if reasons else status, reasons=reasons,
                        configuration={'path': str(config_path), 'sha256': _sha(config_path) if config_path.is_file() else None, 'values': _config_values(config)},
                        inputs=inputs, caption=caption, column=column, width_in=3.5 if column=='single' else 7.16,
                        png_dpi=600, outputs={}, producer_sha256=_sha(__file__),
                        scientific_scope='Model illustration only; paper-mode remains NOT_RUN.' if index==0 else 'Saved-data rendering only; no continuous/global optimum or composable-security claim.')
        if index==0:
            rotor = config.get('verified_context', {}).get('rotor', {})
            manifest['source_variant'] = rotor.get('source_variant', 'Unverified configuration; exploratory only')
            manifest['caption'] += ' Source: '+rotor.get('source_url', 'explicitly selected exploratory configuration')+'.'
        if data is not None and index>0:
            manifest['algorithm_classifications'] = {r['method']: r['classification'] for r in _runs(data)}
            manifest['recorded_information_scope'] = data['report']['information_scope']
            manifest['caption'] += ' Recorded DP mode: '+_runs(data)[-1]['classification']+'.'
            if index in (3, 4):
                manifest['caption'] += ' Axes show the trajectory extent in meters with equal spatial scales; the operating area remains '+str(config['area_m'])+' m.'
        if index==9:
            manifest['sensitivity_objective'] = sensitivity_objective
        if not reasons:
            fig = None
            try:
                if index==0:
                    fig = PLOTTERS[index](config, column)
                elif index==9:
                    fig = PLOTTERS[index](data, column, sensitivity_objective)
                else:
                    fig = PLOTTERS[index](data, column)
                if status == 'EXPLORATORY':
                    fig.text(.5, .012, 'EXPLORATORY — NOT PAPER RESULTS', ha='center', fontsize=6, color='#a00000')
                fig.tight_layout(rect=(0, .055 if status=='EXPLORATORY' else 0, 1, 1))
                for ext in ('pdf', 'png'):
                    path = output/f'{stem}.{ext}'
                    fig.savefig(path, dpi=600, facecolor='white')
                    manifest['outputs'][ext] = {'path': str(path.resolve()), 'sha256': _sha(path)}
                manifest['data_status'] = data['report']['data_status'] if index>0 else ('SOURCE-VERIFIED ROTOR MODEL' if status=='READY' else 'EXPLORATORY CONFIGURATION')
            except (ValueError, KeyError, TypeError, OSError) as error:
                # Remove only files from this failed export in the new, owned output directory.
                for ext in ('pdf', 'png'):
                    (output/f'{stem}.{ext}').unlink(missing_ok=True)
                manifest.update(status='BLOCKED', reasons=[str(error)], outputs={})
            finally:
                if fig is not None:
                    plt.close(fig)
        if manifest['status'] != 'READY':
            manifest['caption'] = manifest['status']+': '+manifest['caption']
        (output/f'{stem}.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
        (output/f'{stem}.caption.txt').write_text(manifest['caption']+'\n', encoding='utf-8')
        manifests.append(manifest)
    summary = dict(paper_mode='NOT_RUN', figures=manifests,
                   counts={status: sum(m['status']==status for m in manifests) for status in ('READY', 'BLOCKED', 'EXPLORATORY')})
    (output/'status.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/paper.yaml')
    parser.add_argument('--results')
    parser.add_argument('--output', default='figures/paper')
    parser.add_argument('--column', choices=['single', 'double'], default='double')
    parser.add_argument('--exploratory', action='store_true')
    parser.add_argument('--sensitivity-objective', choices=['P1', 'P2'], default='P2')
    args = parser.parse_args(argv)
    summary = generate_figures(args.config, args.results, args.output, column=args.column,
                                exploratory=args.exploratory, sensitivity_objective=args.sensitivity_objective)
    for row in summary['figures']:
        print(row['figure'], row['status'], '; '.join(row['reasons']))
    return 2 if summary['counts']['BLOCKED'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
