"""Fixed-distance/fixed-duration energy using the unchanged parent power model."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import os
import platform
import sys

BASE = Path(__file__).resolve().parent
STUDY = BASE.parent
sys.dont_write_bytecode = True
for folder in ('figures', 'data', '.cache/matplotlib', '.cache/tmp'):
    (BASE / folder).mkdir(parents=True, exist_ok=True)


def local_environment():
    os.environ['MPLCONFIGDIR'] = str(BASE / '.cache/matplotlib')
    for key in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[key] = str(BASE / '.cache/tmp')


local_environment()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.collections import QuadMesh
import numpy as np
import scipy
from scipy.optimize import brentq, linprog, minimize_scalar


def previous_files():
    return {p.relative_to(STUDY).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in STUDY.rglob('*') if p.is_file() and BASE not in p.parents}


BEFORE = previous_files()
spec = importlib.util.spec_from_file_location('original_uav_power', STUDY / 'main.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
# The parent module sets cache paths on import; keep every new output here.
local_environment()
power, derivatives = model.power, model.derivatives
FIXED_TIMES = (100, 200, 300, 500, 800)
FIXED_DISTANCES = (500, 1000, 2000, 3000, 5000)
COLORS = ('#0072B2', '#D55E00', '#009E73', '#CC79A7', '#6B5B00')


def envelope(speed, switch):
    v = np.asarray(speed, dtype=float)
    p = power(v)
    return np.where(v < switch, power(0) + (power(switch)-power(0))*v/switch, p)


def evaluate(distance, duration, switch):
    d, t = np.broadcast_arrays(np.asarray(distance, dtype=float),
                               np.asarray(duration, dtype=float))
    if np.any(~np.isfinite(d)) or np.any(~np.isfinite(t)) or np.any(d < 0) or np.any(t <= 0):
        raise ValueError('Distance must be finite and nonnegative; time finite and positive.')
    feasible = d <= model.VMAX*t
    mean = d/t
    constant, minimum, cruise, fly, hover = [np.full(d.shape, np.nan) for _ in range(5)]
    v = np.minimum(mean[feasible], model.VMAX)
    constant[feasible] = t[feasible]*power(v)
    minimum[feasible] = t[feasible]*envelope(v, switch)
    cruise[feasible] = np.maximum(v, switch)
    fly[feasible] = np.where(v < switch, d[feasible]/cruise[feasible], t[feasible])
    hover[feasible] = t[feasible]-fly[feasible]
    strategy = np.where(~feasible, 'infeasible',
                        np.where(mean < switch, 'hover_fly', 'constant'))
    strategy = np.where(feasible & (d == 0), 'hover', strategy)
    return dict(distance_m=d, time_s=t, feasible=feasible, mean_speed_m_s=mean,
                constant_energy_J=constant, minimum_energy_J=minimum,
                savings_J=constant-minimum, savings_percent=100*(constant-minimum)/constant,
                strategy=strategy, fly_speed_m_s=cruise, fly_time_s=fly, hover_time_s=hover)


def write_csv(name, columns):
    arrays = [np.asarray(v).ravel() for v in columns.values()]
    with (BASE / 'data' / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for row in zip(*arrays):
            writer.writerow(['' if isinstance(x, (float, np.floating)) and not np.isfinite(x)
                             else x.item() if isinstance(x, np.generic) else x for x in row])


def save(fig, name):
    # Matplotlib otherwise rasterizes dense colorbars in vector exports.
    for artist in fig.findobj():
        if artist.get_rasterized():
            artist.set_rasterized(False)
        if isinstance(artist, QuadMesh):
            artist.set_edgecolor('face')
            artist.set_linewidth(1.0)
    fig.savefig(BASE / 'figures' / f'{name}.png', dpi=320, facecolor='white')
    fig.savefig(BASE / 'figures' / f'{name}.pdf', facecolor='white')
    plt.close(fig)


def axes(title, xlabel, ylabel, size=(7.6, 5.4)):
    fig, ax = plt.subplots(figsize=size, layout='constrained')
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(alpha=0.18)
    return fig, ax


def boundaries(ax, switch):
    t = np.linspace(20, 1000, 1001)
    for speed, style in ((model.VMAX, '--'), (switch, ':')):
        d = speed*t
        use = (d >= 100) & (d <= 5000)
        ax.plot(d[use], t[use], style, color='black', lw=1.25, zorder=5,
                path_effects=[path_effects.Stroke(linewidth=2.6, foreground='white'),
                              path_effects.Normal()])
    ax.set(xlim=(100, 5000), ylim=(20, 1000), facecolor='#eeeeee')
    handles = [Line2D([], [], color='black', ls='--', label=r'Feasibility: $D=30t$'),
               Line2D([], [], color='black', ls=':', label=r'Strategy: $D=V_*t$'),
               Patch(facecolor='#eeeeee', label='Infeasible')]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.16),
              ncol=3, fontsize=8, frameon=False)


def make_figures(grid, time_slices, distance_slices, switch, mr):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.titlesize': 12, 'axes.labelsize': 11, 'legend.fontsize': 9,
                         'lines.linewidth': 1.9, 'pdf.fonttype': 42, 'savefig.dpi': 320})
    d, t = grid['distance_m'], grid['time_s']
    z = np.ma.masked_invalid(grid['minimum_energy_J']/1000)
    fig = plt.figure(figsize=(9.2, 6.8), layout='constrained')
    ax = fig.add_subplot(projection='3d')
    surface = ax.plot_surface(d, t, z, cmap='viridis', rcount=125, ccount=125,
                              linewidth=0.4, antialiased=False)
    surface.set_edgecolor('face')
    ax.set(xlabel='Distance (m)', ylabel='Time (s)', zlabel='Minimum Energy (kJ)',
           title='Global minimum propulsion energy', xlim=(100, 5000), ylim=(20, 1000))
    ax.view_init(elev=26, azim=-133)
    ax.set_box_aspect((1.15, 1, 0.8))
    ax.xaxis.labelpad = ax.yaxis.labelpad = ax.zaxis.labelpad = 10
    fig.colorbar(surface, ax=ax, shrink=0.65, pad=0.1, label='Minimum Energy (kJ)')
    fig.text(0.48, 0.025, r'Feasible domain: $D\leq30t$; instantaneous speed switching',
             ha='center', fontsize=9)
    save(fig, 'fig01_emin_surface')

    fig, ax = axes('Minimum energy contours', 'Distance (m)', 'Time (s)', (8.2, 6.2))
    filled = ax.contourf(d, t, z, levels=np.linspace(0, 170, 35), cmap='viridis')
    lines = ax.contour(d, t, z, levels=[10, 25, 50, 75, 100, 125, 150],
                       colors='white', linewidths=0.7)
    ax.clabel(lines, fmt='%g kJ', fontsize=8)
    fig.colorbar(filled, ax=ax, label='Minimum Energy (kJ)', pad=0.025)
    boundaries(ax, switch)
    ax.grid(False)
    save(fig, 'fig02_emin_contour')

    for field, filename, title, label, cmap in (
        ('minimum_energy_J', 'fig03_emin_heatmap', 'Minimum energy across distance and time',
         'Minimum Energy (kJ)', 'viridis'),
        ('savings_percent', 'fig07_savings_heatmap', 'Energy saved by optimal speed sharing',
         'Energy savings (%)', 'magma'),
    ):
        fig, ax = axes(title, 'Distance (m)', 'Time (s)', (8.2, 6.2))
        values = grid[field]/1000 if field == 'minimum_energy_J' else grid[field]
        heat = ax.pcolormesh(d, t, np.ma.masked_invalid(values), shading='nearest',
                             cmap=cmap, edgecolors='none', rasterized=False, vmin=0)
        fig.colorbar(heat, ax=ax, label=label, pad=0.025)
        boundaries(ax, switch)
        ax.grid(False)
        save(fig, filename)

    fig, ax = axes('Minimum energy at fixed flight times', 'Distance (m)', 'Minimum Energy (kJ)')
    for duration, color, data in zip(FIXED_TIMES, COLORS, time_slices):
        ax.plot(data['distance_m'], data['minimum_energy_J']/1000,
                color=color, label=f't = {duration} s')
    ax.set(xlim=(100, 5000))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    save(fig, 'fig04_emin_vs_distance')

    fig, ax = axes('Minimum energy at fixed flight distances', 'Time (s)', 'Minimum Energy (kJ)')
    for distance, color, data in zip(FIXED_DISTANCES, COLORS, distance_slices):
        ax.plot(data['time_s'], data['minimum_energy_J']/1000,
                color=color, label=f'D = {distance} m')
        best_time = np.clip(distance/mr, 20, 1000)
        best = evaluate(distance, best_time, switch)
        ax.plot(best_time, float(best['minimum_energy_J'])/1000, 'o', color=color, ms=4)
    ax.set(xlim=(20, 1000))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    ax.text(0.98, 0.05, r'Dots: minimum over allowed time, $t=D/V_{\rm mr}$',
             transform=ax.transAxes, ha='right', fontsize=8)
    save(fig, 'fig05_emin_vs_time')

    fig, panels = plt.subplots(1, 2, figsize=(10.8, 4.9), layout='constrained')
    fig.suptitle('Constant speed versus the global optimum')
    selected = distance_slices[1]
    ax = panels[0]
    ax.plot(selected['time_s'], selected['constant_energy_J']/1000, color=COLORS[0],
             label='Constant speed')
    ax.plot(selected['time_s'], selected['minimum_energy_J']/1000, '--', color=COLORS[1],
             label='Global optimum')
    improves = selected['feasible'] & (selected['mean_speed_m_s'] < switch)
    ax.fill_between(selected['time_s'], selected['minimum_energy_J']/1000,
                     selected['constant_energy_J']/1000, where=improves,
                     color=COLORS[1], alpha=0.22, label='Energy saved')
    ax.axvline(1000/switch, color='0.4', ls=':', lw=1.2)
    ax.set(title='D = 1000 m', xlabel='Time (s)', ylabel='Energy (kJ)', xlim=(20, 1000))
    ax.legend(loc='upper left', frameon=False)
    ax.grid(alpha=0.18)
    ax = panels[1]
    speeds = np.linspace(0, model.VMAX, 6001)
    ax.plot(speeds, 100*(power(speeds)-envelope(speeds, switch))/power(speeds),
             color=COLORS[1], label='Relative savings')
    ax.axvspan(0, switch, alpha=0.09, color=COLORS[1], label='Hover + fly')
    ax.axvline(switch, color='0.4', ls=':', lw=1.2, label=f'V* = {switch:.4f} m/s')
    ax.set(title=r'Savings depend only on $D/t$', xlabel='Mean speed D/t (m/s)',
           ylabel='Energy savings (%)', xlim=(0, 15), ylim=(0, 3.7))
    ax.legend(loc='upper right', frameon=False)
    ax.grid(alpha=0.18)
    save(fig, 'fig06_constant_vs_global')

    fig, ax = axes('Power model and its lower convex envelope', 'Speed (m/s)', 'Power (W)')
    ax.plot(speeds, power(speeds), color=COLORS[0], label='Original P(V)')
    ax.plot(speeds, envelope(speeds, switch), '--', color=COLORS[1], label='Lower convex envelope')
    ax.axvspan(0, switch, color=COLORS[1], alpha=0.08)
    ax.scatter([0, switch], [power(0), power(switch)], color='black', s=23, zorder=5)
    ax.axvline(switch, color='0.4', ls=':', lw=1)
    ax.text(0.34, 0.76, f'Tangent contact: V* = {switch:.6f} m/s', transform=ax.transAxes)
    ax.set(xlim=(0, model.VMAX))
    ax.legend(loc='upper left', frameon=False)
    save(fig, 'fig08_power_envelope')


def main():
    checks = []

    def check(name, passed, **evidence):
        checks.append(dict(check=name, passed=bool(passed), **evidence))
        if not passed:
            raise AssertionError(f'{name}: {evidence}')

    vc = model.V0*np.sqrt(2/np.sqrt(3))
    inflection = brentq(lambda v: derivatives(v)[1], 0, vc, xtol=1e-12)
    me = brentq(lambda v: derivatives(v)[0], inflection, model.VMAX, xtol=1e-12)
    mr = brentq(lambda v: v*derivatives(v)[0]-power(v), inflection, model.VMAX, xtol=1e-12)
    switch = brentq(lambda v: v*derivatives(v)[0]-power(v)+power(0), inflection, me, xtol=1e-12)
    references = [('V_me', me, 10.211690, 1e-6, 'm/s'),
                  ('V_mr', mr, 18.294479, 1e-6, 'm/s'),
                  ('P_min', float(power(me)), 125.990760, 1e-6, 'W'),
                  ('E_1000m_100s', float(evaluate(1000, 100, switch)['minimum_energy_J']),
                   12601.691755, 1e-6, 'J')]
    for name, actual, expected, tolerance, unit in references:
        check(name, abs(actual-expected) <= tolerance, actual=float(actual),
              reference=expected, absolute_error=float(abs(actual-expected)), tolerance=tolerance, unit=unit)
    write_csv('reference_checks.csv', dict(quantity=[r[0] for r in references],
              computed=[r[1] for r in references], reference=[r[2] for r in references],
              absolute_error=[abs(r[1]-r[2]) for r in references],
              tolerance=[r[3] for r in references], unit=[r[4] for r in references]))

    dense = np.linspace(0, model.VMAX, 30001)
    probe = np.linspace(0.02, model.VMAX-0.02, 501)
    h = 0.002
    fd1 = (-power(probe+2*h)+8*power(probe+h)-8*power(probe-h)+power(probe-2*h))/(12*h)
    fd2 = (power(probe+h)-2*power(probe)+power(probe-h))/h**2
    error1 = float(np.max(np.abs(fd1-derivatives(probe)[0])))
    error2 = float(np.max(np.abs(fd2-derivatives(probe)[1])))
    check('derivatives_vs_original_power', error1 < 1e-7 and error2 < 1e-5,
          max_first_error=error1, max_second_error=error2)
    check('single_inflection_shape', derivatives(0)[1] < 0 < derivatives(vc)[1]
          and 0 < inflection < vc < switch < me < mr < model.VMAX
          and len(model.roots(lambda v: derivatives(v)[1], dense)) == 1,
          inflection_m_s=inflection, induced_convexity_threshold_m_s=vc)
    tangent_residual = float(switch*derivatives(switch)[0]-power(switch)+power(0))
    check('tangency_and_minorant', abs(tangent_residual) < 1e-8
          and np.min(power(dense)-envelope(dense, switch)) >= -1e-9,
          tangent_residual_W=tangent_residual)

    distances, times = np.arange(100., 5001., 10.), np.arange(20., 1001., 2.)
    d, t = np.meshgrid(distances, times)
    grid = evaluate(d, t, switch)
    valid = grid['feasible']
    distance_error = float(np.max(np.abs(grid['fly_speed_m_s'][valid]*grid['fly_time_s'][valid]-d[valid])))
    time_error = float(np.max(np.abs(grid['fly_time_s'][valid]+grid['hover_time_s'][valid]-t[valid])))
    schedule_energy = (power(grid['fly_speed_m_s'][valid])*grid['fly_time_s'][valid]
                       + power(0)*grid['hover_time_s'][valid])
    energy_error = float(np.max(np.abs(schedule_energy-grid['minimum_energy_J'][valid])))
    check('all_grid_profiles_feasible', distance_error < 1e-8 and time_error < 1e-10
          and np.min(grid['hover_time_s'][valid]) >= -1e-10
          and np.max(grid['fly_speed_m_s'][valid]) <= model.VMAX,
          max_distance_residual_m=distance_error, max_time_residual_s=time_error)
    check('all_grid_energies_attained', energy_error < 1e-6
          and np.all(grid['savings_J'][valid] >= -1e-7)
          and np.all(grid['minimum_energy_J'][valid] >= t[valid]*power(me)-1e-7),
          max_schedule_energy_residual_J=energy_error)
    check('infeasible_energies_absent', np.all(np.isnan(grid['minimum_energy_J'][~valid]))
          and np.all(np.isnan(grid['constant_energy_J'][~valid])), infeasible_points=int(np.sum(~valid)))
    for bad_d, bad_t in ((-1, 100), (100, 0), (np.inf, 100), (100, np.nan)):
        try:
            evaluate(bad_d, bad_t, switch)
        except ValueError:
            continue
        raise AssertionError('Invalid input was accepted')
    edge = evaluate([0, switch*100, model.VMAX*100, model.VMAX*100+1], 100, switch)
    check('domain_and_strategy_boundaries', np.array_equal(edge['feasible'], [True, True, True, False])
          and abs(edge['minimum_energy_J'][0]-100*power(0)) < 1e-9
          and abs(edge['savings_J'][1]) < 1e-7 and edge['savings_J'][2] == 0)

    convergence = []
    for points in (601, 1201, 6001, 30001):
        speeds = np.linspace(0, model.VMAX, points)
        hull = model.lower_hull(speeds, power(speeds))
        delta = np.interp(dense, speeds[hull], power(speeds[hull]))-envelope(dense, switch)
        convergence.append((points, float(np.max(np.abs(delta))), float(np.min(delta))))
    check('independent_sampled_hull_convergence', convergence[-1][1] < 1e-6
          and all(b[1] <= a[1] for a, b in zip(convergence, convergence[1:])),
          finest_max_error_W=convergence[-1][1])
    write_csv('hull_convergence.csv', dict(speed_points=[r[0] for r in convergence],
              maximum_absolute_power_error_W=[r[1] for r in convergence],
              minimum_signed_power_error_W=[r[2] for r in convergence]))
    lp_gaps = []
    for mean in (0, 0.1, 2, 5, switch, 10, 20, model.VMAX):
        speeds = np.unique(np.r_[np.linspace(0, model.VMAX, 3001), mean])
        result = linprog(power(speeds), A_eq=np.array([np.ones(speeds.size), speeds]),
                         b_eq=[1, mean], bounds=(0, None), method='highs')
        check(f'independent_linear_program_{mean:.6f}', result.success
              and abs(result.fun-float(envelope(mean, switch))) < 2e-4,
              mean_speed_m_s=float(mean), power_gap_W=float(result.fun-envelope(mean, switch)))
        lp_gaps.append(float(result.fun-envelope(mean, switch)))

    rng = np.random.default_rng(20261028)
    velocities, weights = rng.uniform(0, model.VMAX, (5000, 8)), rng.dirichlet(np.ones(8), 5000)
    gap = np.sum(weights*power(velocities), axis=1)-envelope(np.sum(weights*velocities, axis=1), switch)
    check('random_eight_level_profiles', np.min(gap) >= -1e-8,
          profiles=5000, minimum_gap_W=float(np.min(gap)), seed=20261028)
    old = {r['metric']: float(r['value']) for r in csv.DictReader(
        (STUDY / 'results/summary.csv').read_text(encoding='utf-8').splitlines())}
    parent_gaps = [abs(me-old['maximum_endurance_speed']), abs(mr-old['maximum_range_speed']),
                   abs(float(power(me))-old['minimum_power']),
                   abs(switch-old['hover_cruise_transition_speed']),
                   abs(references[-1][1]-old['fixed_time_optimized_energy'])]
    old_curve = np.genfromtxt(STUDY / 'results/power_convex_envelope.csv', delimiter=',', names=True)
    curve_error = float(np.max(np.abs(power(old_curve['speed_m_s'])-old_curve['power_W'])))
    check('original_results_reproduced', max(parent_gaps) < 1e-9 and curve_error < 1e-9,
          max_scalar_absolute_difference=float(max(parent_gaps)), max_power_curve_difference_W=curve_error)

    time_slices = []
    for duration in FIXED_TIMES:
        knots = [x for x in (duration*switch, duration*model.VMAX) if 100 <= x <= 5000]
        time_slices.append(evaluate(np.unique(np.r_[distances, knots]), duration, switch))
    distance_slices = []
    for distance in FIXED_DISTANCES:
        knots = [x for x in (distance/model.VMAX, distance/switch, distance/mr) if 20 <= x <= 1000]
        distance_slices.append(evaluate(distance, np.unique(np.r_[times, knots]), switch))
    write_csv('emin_grid.csv', grid)
    write_csv('fixed_time_slices.csv', {k: np.concatenate([r[k] for r in time_slices]) for k in grid})
    write_csv('fixed_distance_slices.csv', {k: np.concatenate([r[k] for r in distance_slices]) for k in grid})
    write_csv('power_envelope.csv', dict(speed_m_s=dense, original_power_W=power(dense),
              convex_envelope_power_W=envelope(dense, switch)))
    best_times = np.clip(distances/mr, 20, 1000)
    best = evaluate(distances, best_times, switch)
    write_csv('optimal_duration_by_distance.csv', best)
    check('time_optimum_independent_search', all(
        abs(minimize_scalar(lambda time: float(evaluate(distance, time, switch)['minimum_energy_J']),
            bounds=(max(20, distance/model.VMAX), 1000), method='bounded').x-distance/mr) < 1e-3
        for distance in FIXED_DISTANCES))
    peak = minimize_scalar(lambda v: -100*(power(v)-envelope(v, switch))/power(v),
                            bounds=(0, switch), method='bounded')
    make_figures(grid, time_slices, distance_slices, switch, mr)

    after = previous_files()
    preservation = dict(status='PASS' if BEFORE == after else 'FAIL',
                        files_checked=len(BEFORE), before_sha256=BEFORE, after_sha256=after,
                        scope='Pre-existing files under uav_energy_speed_study, excluding emin_distance_time.')
    check('previous_study_files_unchanged', BEFORE == after, files_checked=len(BEFORE))
    (BASE / 'preservation.json').write_text(json.dumps(preservation, indent=2)+'\n', encoding='utf-8')
    summary = dict(V_me_m_s=me, V_mr_m_s=mr, P_min_W=float(power(me)),
                   P_hover_W=float(power(0)), switch_speed_m_s=switch,
                   inflection_speed_m_s=inflection, chord_slope_W_per_m_s=float(derivatives(switch)[0]),
                   benchmark_energy_J=references[-1][1], maximum_savings_percent=float(-peak.fun),
                   maximum_savings_mean_speed_m_s=float(peak.x),
                   feasible_grid_points=int(np.sum(valid)), infeasible_grid_points=int(np.sum(~valid)),
                   variable_speed_grid_points=int(np.sum(valid & (grid['mean_speed_m_s'] < switch))))
    report = dict(status='PASS', checks=checks, summary=summary,
                  grid=dict(distance_m=[100, 5000], time_s=[20, 1000], distance_step_m=10,
                            time_step_s=2, shape=list(d.shape), feasibility='D <= 30*t'),
                  model_source='../main.py', model_source_sha256=BEFORE['main.py'],
                  producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  parameters={k: getattr(model, k) for k in
                              ('P0', 'PI', 'UTIP', 'V0', 'D0', 'RHO', 'SOLIDITY', 'AREA', 'VMAX')},
                  environment=dict(python=platform.python_version(), interpreter=sys.executable,
                      numpy=np.__version__, scipy=scipy.__version__, matplotlib=matplotlib.__version__),
                  scope='Ideal horizontal propulsion; instantaneous switching; no acceleration or endpoint-speed constraints.')
    (BASE / 'validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    manifest = {p.relative_to(BASE).as_posix(): dict(bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(BASE.rglob('*')) if p.is_file() and '.cache' not in p.parts
                and p.name != 'artifact_manifest.json'}
    (BASE / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS', checks=len(checks), summary=summary,
                         output_files=len(manifest)+1), indent=2))


if __name__ == '__main__':
    main()
