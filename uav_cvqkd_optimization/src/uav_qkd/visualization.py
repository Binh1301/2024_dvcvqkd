"""IEEE-sized plots from computed data; every synthetic figure carries its label."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

COLORS = ['#777777', '#d55e00', '#0072b2', '#009e73']


def plot_all(output: Path, report, s, context, sweeps):
    plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                         'font.size': 8, 'mathtext.fontset': 'stix', 'pdf.fonttype': 42})
    directory = output/'figures'
    directory.mkdir(exist_ok=True)
    status = report['data_status']
    c = report['config']

    def export(fig, name):
        fig.text(.01, .012, status, fontsize=6, color='#a00000')
        fig.tight_layout(rect=[0, .065, 1, .98])
        for suffix in ('png', 'pdf'):
            fig.savefig(directory/f'{name}.{suffix}', dpi=300, facecolor='white')
        plt.close(fig)

    for binary in (False, True):
        times = c['plot_times_s']
        fields = [context['field'].grid(*c['area_m'], t)[2] for t in times]
        maximum = max(1., max(float(field.max()) for field in fields))
        fig, axes = plt.subplots(1, len(times), figsize=(7.2, 2.7), squeeze=False)
        for ax, t, field in zip(axes[0], times, fields):
            data = field >= c['cloud']['threshold_mg_m3'] if binary else field
            image = ax.imshow(data, origin='lower', extent=(0, c['area_m'][0], 0, c['area_m'][1]),
                      interpolation='nearest', cmap=ListedColormap(['white', '#222222']) if binary else 'Greys',
                      vmin=0, vmax=1 if binary else maximum)
            ax.set(title=f't = {t:g} s', xlabel='x (m)', ylabel='y (m)')
            if not binary:
                fig.colorbar(image, ax=ax, fraction=.045, pad=.04, label='CLWC (mg/m³)')
        if binary:
            from matplotlib.patches import Patch
            axes[0, -1].legend(handles=[Patch(color='#222222', label='Cloud blockage'),
                                       Patch(facecolor='white', edgecolor='black', label='Non-blocking')],
                               fontsize=6, loc='lower right')
        export(fig, '02_binary_cloud_maps' if binary else '01_gaussian_cloud_maps')

    def trajectories(objectives, filename):
        fig, axes = plt.subplots(1, len(objectives), figsize=(7.2 if len(objectives) > 1 else 4.5, 3.6), squeeze=False)
        for ax, objective in zip(axes[0], objectives):
            ax.scatter(s.graph.positions[:, 0], s.graph.positions[:, 1], s=7, color='.75', label='Waypoints')
            for run, color in zip(report['runs'], COLORS):
                if objective not in run['solutions']:
                    continue
                points = np.asarray(run['solutions'][objective]['trajectory_m'])
                ax.plot(points[:, 0], points[:, 1], '-o', ms=3, lw=1, color=color, label=run['method'])
            ax.scatter(*s.graph.positions[s.graph.initial], marker='*', s=70, c='black', label='Initial')
            ax.set(title=objective, xlabel='x (m)', ylabel='y (m)', aspect='equal')
            ax.legend(fontsize=6)
        export(fig, filename)

    trajectories(['P1', 'P2'], '03_trajectories_all')
    trajectories(['P1'], '04_trajectories_P1')
    trajectories(['P2'], '05_trajectories_P2')
    for number, metric, ylabel in [(6, 'energy_j', 'Cumulative propulsion energy (J)'),
                                    (7, 'asymptotic_bits', 'Accumulated asymptotic contribution (bits)'),
                                    (8, 'valid_signals', 'Accumulated valid signals')]:
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3))
        for ax, objective in zip(axes, ('P1', 'P2')):
            for run, color in zip(report['runs'], COLORS):
                if objective not in run['solutions']:
                    continue
                rows = run['solutions'][objective]['series']
                ax.plot([0]+[row['time_s'] for row in rows], [0]+[row[metric] for row in rows],
                        '-o', ms=2, color=color, label=run['method'])
            ax.set(title=objective, xlabel='Time (s)', ylabel=ylabel)
            ax.legend(fontsize=6)
        export(fig, f'{number:02}_{metric}')
    fig, ax = plt.subplots(figsize=(4.5, 3))
    n = np.geomspace(c['m0'], c['m0']*s.horizon, 100)
    ax.plot(n, 7*np.sqrt((1-np.log2(c['epsilon']))/n), color='black')
    ax.set(xlabel='Accumulated valid signals n', ylabel='Finite-size penalty per signal (bits/use)')
    export(fig, '09_penalty_per_signal')
    for number, metric, ylabel in [(10, 'key_bits', 'Total estimated secret key (bits)'),
                                    (11, 'average_skr_bits_s', 'Average estimated SKR (bits/s)')]:
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3))
        for ax, objective in zip(axes, ('P1', 'P2')):
            ax.bar(range(4), [run['solutions'].get(objective, {}).get(metric, np.nan) for run in report['runs']], color=COLORS)
            ax.set_xticks(range(4), ['Stationary', 'SKR-G', 'Energy-G', 'DP'], rotation=20)
            ax.set(title=objective, ylabel=ylabel)
        export(fig, f'{number:02}_{metric}')
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3))
    for ax, metric, ylabel, scale in zip(axes, ['runtime_s', 'python_peak_bytes'], ['Runtime (s)', 'Peak Python allocations (MiB)'], [1., 2**20]):
        ax.bar(range(4), [run[metric]/scale for run in report['runs']], color=COLORS)
        ax.set_xticks(range(4), ['Stationary', 'SKR-G', 'Energy-G', 'DP'], rotation=20)
        ax.set_ylabel(ylabel)
    export(fig, '12_runtime_memory')

    for number, kind, xlabel in [(13, 'energy', 'Energy budget (J)'),
                                 (14, 'threshold', 'CLWC threshold (mg/m³)'),
                                 (15, 'resolution', 'Restricted waypoint spacing (m)'),
                                 (16, 'pruning', 'Labels per state (exact = uncapped)')]:
        if not sweeps:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3))
        for ax, objective in zip(axes, ('P1', 'P2')):
            for run, color in zip(report['runs'], COLORS):
                rows = [row for row in sweeps if row['sensitivity'] == kind and row['objective'] == objective and row['method'] == run['method']]
                ax.plot([str(row['parameter']) for row in rows], [row['objective_value'] if row['objective_value'] is not None else np.nan for row in rows],
                        '-o', ms=3, color=color, label=run['method'])
            ax.set(title=objective, xlabel=xlabel, ylabel='bits/s' if objective == 'P1' else 'bits')
            ax.legend(fontsize=6)
        export(fig, f'{number:02}_{kind}_sensitivity')
