"""Vector manuscript figures from finalized artifacts only; no scientific evaluator."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


COLORS = {'Stationary': 'black', 'Greedy': 'tab:orange', 'DP': 'tab:red'}
DISTANCE_SERIES = (
    ('Uniform_K_raw', 'Optimized Uniform', 'tab:blue'),
    ('Fixed_MB_K_raw', 'Fixed MB', 'tab:orange'),
    ('Optimized_MB_K_raw', 'Optimized MB', 'tab:red'),
)


def _read(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def _write(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _style(ax):
    ax.set_axisbelow(True)
    ax.minorticks_on()
    ax.grid(which='major', color='#d8d8d8', linewidth=.5)
    ax.grid(which='minor', color='#eeeeee', linewidth=.3)


def export_results(output: Path, settings: dict) -> None:
    """Render saved arrays, preserve raw negatives, and record every input hash."""
    output = Path(output)
    inputs = ['positions.csv', 'p1/winners.csv', 'p1/family_winners.csv',
              'clouds/states.npz', 'mobility/lambda_schedule.json',
              'mobility/representative_paths.csv', 'mobility/representative_metrics.csv',
              'mobility/lambda_statistics.csv', 'figures/figure1_distance.csv']
    hashes = {name: _sha(output/name) for name in inputs}
    positions = sorted(_read(output/'positions.csv'), key=lambda r: int(r['position_index']))
    if [int(p['position_index']) for p in positions] != list(range(len(positions))):
        raise ValueError('Position indices must be contiguous')
    xy = np.array([[float(p['x_m']), float(p['y_m'])] for p in positions])
    side = float(settings['geometry']['grid_side_m'])
    xs, ys = np.unique(xy[:, 0]), np.unique(xy[:, 1])
    if len(xs)*len(ys) != len(xy) or len(set(map(tuple, xy))) != len(xy):
        raise ValueError('A complete rectangular candidate grid is required')
    schedule = json.loads((output/'mobility/lambda_schedule.json').read_text(encoding='utf-8'))
    representative = float(schedule['representative'])
    with np.load(output/'clouds/states.npz', allow_pickle=False) as archive:
        blocked = archive['blocked'].copy()
        usable_shape = archive['usable_skr'].shape
    if (blocked.dtype != np.bool_ or blocked.ndim != 3 or blocked.shape[1] != len(xy)
            or blocked.shape[2] != 30 or blocked.shape != usable_shape):
        raise ValueError('Unexpected cloud/usable SKR dimensions or dtype')
    raw_paths = _read(output/'mobility/representative_paths.csv')
    paths = {}
    for strategy in COLORS:
        rows = sorted([r for r in raw_paths if r['strategy'] == strategy], key=lambda r: int(r['slot']))
        if [int(r['slot']) for r in rows] != list(range(1, 31)):
            raise ValueError('Representative path must have ordered slots 1..30')
        if any(int(r['realization_id']) != 0 or float(r['lambda_bits_per_use']) != representative for r in rows):
            raise ValueError('Representative mission/lambda mismatch')
        coords = np.array([[float(r['x_m']), float(r['y_m'])] for r in rows])
        if any(int(r['position_index']) < 0 or int(r['position_index']) >= len(xy) for r in rows):
            raise ValueError('Invalid path position index')
        if not np.array_equal(coords, xy[[int(r['position_index']) for r in rows]]):
            raise ValueError('Path coordinates differ from saved candidate positions')
        legs = np.linalg.norm(np.diff(coords, axis=0), axis=1)
        limit = settings['mission']['slot_duration_s']*settings['mission']['max_speed_m_per_s']
        if np.any(legs > limit+1e-9) or (strategy == 'Stationary' and np.any(legs != 0)):
            raise ValueError('Saved path is not feasible')
        paths[strategy] = coords
    winners = {int(r['position_index']): r for r in _read(output/'p1/winners.csv')}
    if set(winners) != set(range(len(xy))):
        raise ValueError('Missing P1 winner positions')
    statistics = _read(output/'mobility/lambda_statistics.csv')
    distance_rows = _read(output/'figures/figure1_distance.csv')
    exclusions = {key: sum(float(r[key]) <= 0 for r in distance_rows) for key, _, _ in DISTANCE_SERIES}
    values = sorted(set(map(float, schedule['values'])))
    if not values or min(values) < 0 or not np.all(np.isfinite(values)):
        raise ValueError('Invalid saved lambda values')
    positive = [v for v in values if v > 0]
    linthresh = min(positive) if positive else None
    figures = output/'figures'
    data = figures/'plot_data'
    data.mkdir(parents=True, exist_ok=True)
    # Copy only finalized inputs; display arrays below never replace their raw sources.
    for relative in inputs:
        source = output/relative
        if source.suffix == '.csv':
            shutil.copyfile(source, data/relative.replace('/', '__'))
    display_rows = []
    for row in distance_rows:
        display = dict(row)
        for key, _, _ in DISTANCE_SERIES:
            display[key.replace('_raw', '_log_display')] = row[key] if float(row[key]) > 0 else ''
        display_rows.append(display)
    _write(data/'fig1_distance_display.csv', display_rows)
    cloud_rows = [dict(position_index=i, x_m=xy[i, 0], y_m=xy[i, 1],
                       cloud_free_fraction=float((~blocked[0, i]).mean()),
                       **{f'blocked_slot_{slot:02d}': int(blocked[0, i, slot-1]) for slot in (1, 10, 20, 30)})
                  for i in range(len(xy))]
    _write(data/'cloud_display.csv', cloud_rows)
    figure_paths = []

    def save(fig, name, top=1., bottom=0.):
        fig.tight_layout(pad=.7, rect=(0, bottom, 1, top))
        for ext in ('pdf', 'png'):
            path = figures/f'{name}.{ext}'
            fig.savefig(path, dpi=350, facecolor='white')
            figure_paths.append(path.relative_to(output).as_posix())
        plt.close(fig)

    def grid_values(values):
        z = np.empty((len(ys), len(xs)))
        for (x, y), value in zip(xy, values):
            z[np.searchsorted(ys, y), np.searchsorted(xs, x)] = value
        return z

    def map_plot(values, title, label, cmap='viridis', vmin=None, vmax=None):
        fig, ax = plt.subplots(figsize=(4.8, 4.1))
        # Grid boundaries describe the saved cell centers; pcolormesh remains vector.
        xedges = np.r_[0., (xs[:-1]+xs[1:])/2, side]/1000
        yedges = np.r_[0., (ys[:-1]+ys[1:])/2, side]/1000
        mesh = ax.pcolormesh(xedges, yedges, grid_values(values), cmap=cmap,
                             shading='flat', vmin=vmin, vmax=vmax, rasterized=False)
        bar = fig.colorbar(mesh, ax=ax, pad=.025)
        bar.set_label(label)
        if bar.solids is not None:
            bar.solids.set_rasterized(False)
        ax.set(xlabel='x (km)', ylabel='y (km)', title=title,
               xlim=(0, side/1000), ylim=(0, side/1000), aspect='equal')
        _style(ax)
        ax.set_axisbelow(False)
        return fig, ax

    with plt.rc_context({'font.family': 'serif', 'font.size': 9, 'axes.titlesize': 10,
                         'axes.labelsize': 9, 'legend.fontsize': 8, 'lines.linewidth': 1.4,
                         'pdf.fonttype': 42, 'savefig.facecolor': 'white'}):
        distances = [float(r['distance_km']) for r in distance_rows]
        for log in (True, False):
            fig, ax = plt.subplots(figsize=(5.3, 3.7))
            for key, label, color in DISTANCE_SERIES:
                rates = np.array([float(r[key]) for r in distance_rows])
                shown = np.where(rates > 0, rates, np.nan) if log else rates
                ax.plot(distances, shown, color=color, label=label, marker='o', markersize=2.2)
            if log:
                if any(float(r[key]) > 0 for r in distance_rows for key, _, _ in DISTANCE_SERIES):
                    ax.set_yscale('log')
                else:
                    ax.set_yscale('log')
                    ax.set_ylim(.1, 1)
                    ax.text(.5, .5, 'No positive saved SKR values', ha='center', transform=ax.transAxes)
            else:
                ax.axhline(0, color='.45', linewidth=.6)
            ax.set(xlabel='Link Distance (km)',
                   ylabel='Secret Key Rate (bits/use)')
            _style(ax)
            fig.suptitle('SKR versus HAP–UAV Link Distance', y=.99, fontsize=10)
            fig.legend(*ax.get_legend_handles_labels(), loc='upper center',
                       bbox_to_anchor=(.5, .925), ncol=3, frameon=False)
            save(fig, 'fig1_skr_distance' + ('' if log else '_linear'), top=.88)

        fig, ax = map_plot((~blocked[0]).mean(axis=1), '',
                           'Cloud-free fraction (mission 0)', 'Blues_r', 0, 1)
        ax.scatter(xy[:, 0]/1000, xy[:, 1]/1000, color='.35', s=7, alpha=.65, label='Candidates', zorder=3)
        for strategy, color in COLORS.items():
            coords = paths[strategy]/1000
            if strategy == 'Stationary':
                ax.scatter(*coords[0], marker='*', s=100, color=color, label=strategy, zorder=6)
            else:
                ax.plot(coords[:, 0], coords[:, 1], color=color, label=strategy, alpha=.9, zorder=4,
                        linestyle='--' if strategy == 'Greedy' else '-',
                        linewidth=2.3 if strategy == 'Greedy' else 1.3)
                ax.scatter(*coords[0], marker='o', s=35, facecolors='none', edgecolors=color, zorder=5)
                ax.scatter(*coords[-1], marker='X', s=35, color=color, zorder=5)
        ax.plot([], [], 'o', color='.3', fillstyle='none', label='Start')
        ax.plot([], [], 'X', color='.3', label='End')
        fig.suptitle('Clouds and feasible UAV trajectories', y=.99, fontsize=10)
        fig.text(.5, .937, f'Mission ID 0; λ = {representative:.6g} bits/use',
                 ha='center', va='center', fontsize=8)
        fig.legend(*ax.get_legend_handles_labels(), loc='upper center',
                   bbox_to_anchor=(.5, .91), ncol=3, frameon=False)
        save(fig, 'fig2_cloud_trajectories', top=.83)

        fig, axes = plt.subplots(1, 2, figsize=(7.16, 3.25), sharex=True)
        for ax, metric, ylabel in zip(axes, ('average_skr_bits_per_use', 'total_distance_m'),
                                      ('Mean average SKR (bits/use)', 'Mean distance (m)')):
            for strategy, color in COLORS.items():
                rows = sorted([r for r in statistics if r['strategy'] == strategy and r['metric'] == metric],
                              key=lambda r: float(r['lambda_bits_per_use']))
                if [float(r['lambda_bits_per_use']) for r in rows] != values:
                    raise ValueError('Lambda statistics do not match saved schedule')
                x = np.array([float(r['lambda_bits_per_use']) for r in rows])
                mean = np.array([float(r['mean']) for r in rows])
                low = np.array([float(r['ci95_low']) for r in rows])
                high = np.array([float(r['ci95_high']) for r in rows])
                ax.errorbar(x, mean, yerr=np.array([mean-low, high-mean]), color=color,
                            marker='o', markersize=3, capsize=2, label=strategy)
            if linthresh is not None:
                ax.set_xscale('symlog', linthresh=linthresh, base=10)
                ax.set_xticks(values)
                ax.set_xticklabels([f'{v:.2g}' for v in values], rotation=35, ha='right', fontsize=7)
            else:
                ax.set_xticks([0])
                ax.annotate('Single saved λ = 0', (.5, .96), xycoords='axes fraction', ha='center', va='top')
            ax.set(xlabel='λ (bits/use)', ylabel=ylabel)
            _style(ax)
            ax.margins(y=.15)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=3, frameon=False)
        if linthresh is not None:
            fig.text(.5, .01, f'λ axis: base-10 symlog; linear threshold = {linthresh:.6g} bits/use',
                     ha='center', va='bottom', fontsize=7)
        save(fig, 'fig3_mobility_tradeoff', top=.9, bottom=.075 if linthresh is not None else 0.)
        for key, name, title, label in (
            ('K_star', 'p1_skr_heatmap', 'P1 selected usable SKR', 'K* (bits/use)'),
            ('VA', 'p1_VA_heatmap', 'P1 selected modulation variance', 'V_A (SNU)'),
            ('nu_raw', 'p1_nu_heatmap', 'P1 selected MB parameter', 'ν_raw')):
            fig, _ = map_plot([float(winners[i][key]) for i in range(len(xy))], title, label)
            save(fig, name)
        for slot in (1, 10, 20, 30):
            fig, ax = map_plot(blocked[0, :, slot-1].astype(int), f'Cloud blockage: mission 0, slot {slot}',
                               'Blocked (0 = clear, 1 = blocked)', 'Greys', 0, 1)
            ax.scatter(xy[:, 0]/1000, xy[:, 1]/1000, s=7, color='tab:blue')
            save(fig, f'cloud_slot_{slot:02d}')
    if hashes != {name: _sha(output/name) for name in inputs}:
        raise ValueError('Input changed during rendering')
    receipt = dict(schema='saved-mobility-render-v1', renderer_sha256=_sha(Path(__file__)),
                   settings_sha256=hashlib.sha256(json.dumps(settings, sort_keys=True, allow_nan=False).encode()).hexdigest(),
                   input_sha256=hashes, scientific_recalculation=False,
                   nonpositive_exclusions=exclusions, symlog_linthresh=linthresh,
                   png_dpi=350, pdf_vector=True, strategy_colors=COLORS, figure_paths=figure_paths,
                   representative_mission=0, representative_lambda_bits_per_use=representative,
                   captions={
                       'fig1_skr_distance': 'Positive raw saved SKR only; nonpositive values create NaN gaps, no epsilon floor. Linear companion retains all raw values.',
                       'fig2_cloud_trajectories': 'Mission 0 cloud-free slot fraction; ordered saved paths without displacement. Start/end may coincide. HAP is outside the map; geometry is recorded below.',
                       'fig3_mobility_tradeoff': ('Mean and saved 95% confidence intervals; actual λ axis uses base-10 symlog with threshold at smallest positive λ.'
                                                if linthresh else 'Single saved λ = 0; no sweep was invented.')},
                   geometry=settings['geometry'])
    (figures/'render_receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n', encoding='utf-8')
