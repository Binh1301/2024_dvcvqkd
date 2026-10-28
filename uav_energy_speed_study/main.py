"""Standalone rotary-wing propulsion study; all writes stay beside this script."""
from pathlib import Path
import os
import sys

BASE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
for name in ('figures', 'results', '.cache/matplotlib', '.cache/tmp'):
    (BASE / name).mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(BASE / '.cache/matplotlib')
os.environ['TEMP'] = os.environ['TMP'] = os.environ['TMPDIR'] = str(BASE / '.cache/tmp')

import csv
import hashlib
import json
import platform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.optimize import brentq, minimize, minimize_scalar

P0, PI = 79.85628, 88.62794
UTIP, V0 = 120.0, 4.02854
D0, RHO, SOLIDITY, AREA = 0.6, 1.225, 0.05, 0.503
VMAX, DISTANCE, DURATION = 30.0, 1000.0, 100.0
AVERAGES = (2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0)
BLUE, ORANGE, GREEN = '#0072B2', '#D55E00', '#009E73'


def power(speed):
    v = np.asarray(speed, dtype=float)
    if np.any(~np.isfinite(v)) or np.any((v < 0) | (v > VMAX)):
        raise ValueError('Speed must be finite and lie in [0, 30] m/s.')
    return (P0 * (1 + 3 * v**2 / UTIP**2)
            + PI * np.sqrt(np.sqrt(1 + v**4 / (4 * V0**4)) - v**2 / (2 * V0**2))
            + 0.5 * D0 * RHO * SOLIDITY * AREA * v**3)


def derivatives(speed):
    v = np.asarray(speed, dtype=float)
    x = v**2 / (2 * V0**2)
    r = np.sqrt(1 + x**2)
    q = np.exp(-np.arcsinh(x) / 2)
    first = 6 * P0 * v / UTIP**2 - PI * q * v / (2 * V0**2 * r)
    first += 1.5 * D0 * RHO * SOLIDITY * AREA * v**2
    second = 6 * P0 / UTIP**2 + PI * q * (x*r + x**2 - 1) / (2 * V0**2 * r**3)
    second += 3 * D0 * RHO * SOLIDITY * AREA * v
    return first, second


def roots(function, grid):
    values = function(grid)
    brackets = np.flatnonzero(values[:-1] * values[1:] < 0)
    return [brentq(function, grid[i], grid[i+1], xtol=1e-12) for i in brackets]


def lower_hull(v, p):
    hull = []
    for i in range(len(v)):
        while len(hull) >= 2:
            a, b = hull[-2:]
            if (p[b]-p[a])*(v[i]-v[b]) < (p[i]-p[b])*(v[b]-v[a]):
                break
            hull.pop()
        hull.append(i)
    return np.asarray(hull)


def profile(mean, low, high):
    if high - low <= 1e-12:
        return (mean, mean, 0.5, float(power(mean)))
    fraction = (high - mean) / (high - low)
    value = fraction * power(low) + (1 - fraction) * power(high)
    return (float(low), float(high), float(fraction), float(value))


def landscape(mean, points):
    v1 = np.linspace(0, VMAX, points)
    fractions = np.linspace(0, 1, points)
    a = fractions[1:-1, None]
    second = (mean - a * v1[None, :]) / (1 - a)
    feasible = (second >= 0) & (second <= VMAX)
    energy = np.full((points, points), np.nan)
    middle = energy[1:-1]
    weighted_first = np.broadcast_to(a * power(v1), second.shape)
    weighted_second = np.broadcast_to(1-a, second.shape)
    middle[feasible] = DURATION * (weighted_first[feasible]
                                 + weighted_second[feasible] * power(second[feasible]))
    energy[0, :] = DURATION * power(mean)
    energy[-1, np.isclose(v1, mean, rtol=0, atol=1e-12)] = DURATION * power(mean)
    return fractions, v1, energy


def grid_best(mean, points):
    fractions, v1, energy = landscape(mean, points)
    i, j = np.unravel_index(np.nanargmin(energy), energy.shape)
    a = fractions[i]
    if a == 0 or a == 1:
        candidate = profile(mean, mean, mean)
    else:
        second = (mean - a * v1[j]) / (1-a)
        candidate = profile(mean, min(v1[j], second), max(v1[j], second))
    constant = profile(mean, mean, mean)
    return candidate if candidate[3] < constant[3] - 1e-10 else constant


def refine(mean, candidate):
    constant = profile(mean, mean, mean)
    if mean == 0 or mean == VMAX:
        return constant
    options = [constant, candidate]
    starts = [(candidate[0], candidate[1]), (0, max(mean, 8)),
              (mean/2, (mean+VMAX)/2), (0, VMAX)]
    for start in starts:
        result = minimize(lambda pair: profile(mean, *pair)[3], start,
                          method='SLSQP', bounds=[(0, mean), (mean, VMAX)],
                          options={'ftol': 1e-12, 'maxiter': 300})
        if result.success:
            options.append(profile(mean, *result.x))
    hover = minimize_scalar(lambda high: profile(mean, 0, high)[3],
                            bounds=(mean, VMAX), method='bounded',
                            options={'xatol': 1e-11})
    if not hover.success:
        raise RuntimeError(hover.message)
    high = float(hover.x)
    stationary = lambda v: v * derivatives(v)[0] - power(v) + power(0)
    left, right = max(mean, high-0.1), min(VMAX, high+0.1)
    if stationary(left) * stationary(right) < 0:
        high = brentq(stationary, left, right, xtol=1e-12)
    options.append(profile(mean, 0, high))
    best = min(options, key=lambda row: row[3])
    return best if best[3] < constant[3] - 1e-10 else constant


def save_csv(name, rows):
    with (BASE / 'results' / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def figure(title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(7.2, 4.8), layout='constrained')
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    ax.grid(alpha=0.2)
    ax.spines[['top', 'right']].set_visible(False)
    return fig, ax


def save_figure(fig, name):
    fig.savefig(BASE / 'figures' / name, dpi=320, facecolor='white')
    plt.close(fig)


def mark_speeds(ax, function, me, mr):
    for speed, label, color, marker in ((me, r'$V_{\rm me}$', GREEN, 's'),
                                         (mr, r'$V_{\rm mr}$', ORANGE, 'o')):
        ax.scatter(speed, function(speed), color=color, marker=marker, s=48, zorder=5,
                   label=f'{label} = {speed:.3f} m/s')
        ax.axvline(speed, color=color, linewidth=0.9, linestyle=':', alpha=0.7)


def make_figures(me, mr, switch, rows, dense, sampled_envelope, exact_envelope):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.titlesize': 12, 'legend.fontsize': 9,
                         'lines.linewidth': 2, 'savefig.dpi': 320})
    v = np.linspace(0, VMAX, 3001)
    vp = np.geomspace(0.1, VMAX, 2001)
    fig, ax = figure('Rotary-wing propulsion power', 'Speed $V$ (m/s)', 'Power $P(V)$ (W)')
    ax.plot(v, power(v), color=BLUE, label='Propulsion power')
    ax.plot(v, power(mr)/mr*v, '--', color='0.45', label='Tangent from the origin')
    mark_speeds(ax, power, me, mr)
    ax.scatter(0, power(0), color='black', s=40, zorder=5, label=f'Hover: {power(0):.3f} W')
    ax.annotate(f'{power(me):.3f} W', (me, power(me)), xytext=(-38, 18), textcoords='offset points')
    ax.annotate(f'{power(mr):.3f} W', (mr, power(mr)), xytext=(7, 11), textcoords='offset points')
    ax.set(xlim=(0, VMAX), ylim=(0, 390))
    ax.legend(loc='upper left')
    save_figure(fig, 'fig01_power_vs_velocity.png')

    for filename, title, ylabel, function in (
        ('fig02_energy_vs_velocity.png', 'Energy for a fixed distance of 1000 m',
         'Propulsion energy (kJ)', lambda speed: DISTANCE*power(speed)/speed/1000),
        ('fig03_duration_vs_velocity.png', 'Flight duration for a fixed distance of 1000 m',
         'Flight duration (s)', lambda speed: DISTANCE/speed),
        ('fig04_energy_per_meter.png', 'Propulsion energy per unit distance',
         'Energy per distance (J/m)', lambda speed: power(speed)/speed),
    ):
        fig, ax = figure(title, 'Speed $V$ (m/s)', ylabel)
        ax.plot(vp, function(vp), color=BLUE)
        mark_speeds(ax, function, me, mr)
        ax.set(xlim=(0, VMAX), yscale='log')
        ax.text(0.98, 0.95, 'Logarithmic vertical axis\nPlotted from $V=0.1$ m/s',
                transform=ax.transAxes, ha='right', va='top', fontsize=9)
        ax.legend(loc='center right')
        if 'duration' not in filename:
            ax.annotate(f'Minimum: {function(mr):.6f}', (mr, function(mr)),
                        xytext=(0, 18), textcoords='offset points', ha='center', fontsize=9)
        save_figure(fig, filename)

    selected = next(row for row in rows if row['average_speed_m_s'] == 10)
    v1, v2, fraction = (selected[k] for k in ('v1_m_s', 'v2_m_s', 'alpha'))
    time = np.linspace(0, DURATION, 1001)
    speed = np.where(time < fraction*DURATION, v1, v2)
    cumulative = (power(v1)*np.minimum(time, fraction*DURATION)
                  + power(v2)*np.maximum(time-fraction*DURATION, 0))
    fig, ax = figure('Optimal speed profiles: $D=1000$ m, $T=100$ s',
                     'Time $t$ (s)', 'Speed $V(t)$ (m/s)')
    ax.plot(time, np.full_like(time, 10), color=BLUE, linewidth=3, label='Constant-speed benchmark')
    ax.plot(time, speed, '--', color=ORANGE, label='Optimized two-level strategy')
    ax.text(0.5, 0.83, 'Profiles coincide: 10 m/s for the entire flight',
            transform=ax.transAxes, ha='center')
    ax.set(xlim=(0, 100), ylim=(8.5, 11.5))
    ax.legend(loc='lower center')
    save_figure(fig, 'fig05_velocity_profiles.png')

    fig, ax = figure('Cumulative energy: $D=1000$ m, $T=100$ s',
                     'Time $t$ (s)', 'Cumulative propulsion energy (kJ)')
    ax.plot(time, time*power(10)/1000, color=BLUE, linewidth=3, label='Constant-speed benchmark')
    ax.plot(time, cumulative/1000, '--', color=ORANGE, label='Optimized two-level strategy')
    ax.text(0.05, 0.8, f'Identical energy: {selected["optimized_energy_J"]/1000:.6f} kJ',
            transform=ax.transAxes)
    ax.set(xlim=(0, 100), ylim=(0, 14))
    ax.legend(loc='upper left')
    save_figure(fig, 'fig06_cumulative_energy.png')

    fractions, speeds, energy = landscape(10, 601)
    fig, ax = figure('Two-level energy: $D=1000$ m, $T=100$ s',
                     r'First-level duration fraction $\alpha$', 'First-level speed $V_1$ (m/s)')
    heat = ax.pcolormesh(fractions, speeds, np.ma.masked_invalid(energy.T/1000),
                         shading='auto', cmap='viridis', rasterized=True)
    fig.colorbar(heat, ax=ax, label='Total propulsion energy (kJ)')
    ax.plot([0, 1], [10, 10], '--', color='white', label='Constant-speed benchmark / optimal ridge')
    ax.scatter([0.5], [10], marker='*', s=180, color=ORANGE, edgecolor='white',
               zorder=5, label='Selected global optimum')
    ax.text(0.97, 0.95, 'Blank region: infeasible', ha='right', va='top', transform=ax.transAxes)
    ax.set(xlim=(0, 1), ylim=(0, 30))
    ax.legend(loc='lower left', facecolor='0.25', labelcolor='white')
    save_figure(fig, 'fig07_energy_landscape.png')

    average = np.array([row['average_speed_m_s'] for row in rows])
    fig, ax = figure(r'Fixed-time energy comparison: $T=100$ s, $D=\overline{V}T$',
                     r'Average speed $\overline{V}$ (m/s)', 'Propulsion energy (kJ)')
    ax.plot(average, [r['constant_energy_J']/1000 for r in rows], 'o-', color=BLUE, label='Constant speed')
    ax.plot(average, [r['optimized_energy_J']/1000 for r in rows], 's--', color=ORANGE,
            markerfacecolor='none', label='Optimized two-level speed')
    ax.axhline(DURATION*power(me)/1000, color=GREEN, linestyle=':',
               label=r'Universal bound $T P(V_{\rm me})$; not generally feasible')
    ax.set(xlim=(0, 31), ylim=(11, 38))
    ax.legend(loc='upper left')
    save_figure(fig, 'fig08_energy_comparison.png')

    fig, ax = figure('Savings from optimal speed sharing',
                     r'Average speed $\overline{V}$ (m/s)', 'Energy savings (%)')
    means = np.linspace(0, VMAX, 1501)
    savings = 100 * (power(means)-exact_envelope(means))/power(means)
    ax.plot(means, savings, color=ORANGE, label='Continuous convex-envelope prediction')
    ax.scatter(average, [r['savings_percent'] for r in rows], color=BLUE, zorder=5,
               label='Optimized sensitivity scenarios')
    ax.axvline(switch, color='0.45', linestyle=':', label=f'Transition: {switch:.4f} m/s')
    ax.set(xlim=(0, VMAX), ylim=(-0.25, max(savings)*1.2))
    ax.legend(loc='upper right')
    save_figure(fig, 'fig09_energy_savings.png')

    fig, ax = figure('Lower convex envelope of propulsion power',
                     'Speed $V$ (m/s)', 'Power (W)')
    ax.axvspan(0, switch, color=ORANGE, alpha=0.1, label='Hover + cruise improves energy')
    ax.axvspan(switch, VMAX, color=GREEN, alpha=0.07, label='Constant speed is optimal')
    ax.plot(dense, power(dense), color=BLUE, label='$P(V)$')
    ax.plot(dense, sampled_envelope, '--', color=ORANGE, label='Numerical lower convex envelope')
    ax.scatter([0, switch], [power(0), power(switch)], color='black', s=30, zorder=5)
    ax.axvline(switch, color='0.45', linewidth=1, linestyle=':')
    ax.annotate(f'Tangent contact: {switch:.6f} m/s', (switch, power(switch)),
                xytext=(6, -33), textcoords='offset points', fontsize=9)
    ax.set(xlim=(0, VMAX), ylim=(100, 385))
    ax.legend(loc='upper left')
    save_figure(fig, 'fig10_convex_envelope.png')


def main():
    checks = []

    def check(name, condition, **evidence):
        checks.append(dict(check=name, passed=bool(condition), **evidence))
        if not condition:
            raise AssertionError(f'{name}: {evidence}')

    dense = np.linspace(0, VMAX, 30001)
    positive = dense[1:]
    vc = np.sqrt(2/np.sqrt(3))*V0
    inflection = brentq(lambda v: derivatives(v)[1], 0, vc, xtol=1e-12)
    me = brentq(lambda v: derivatives(v)[0], inflection, VMAX, xtol=1e-12)
    mr = brentq(lambda v: v*derivatives(v)[0]-power(v), inflection, VMAX, xtol=1e-12)
    switch = brentq(lambda v: v*derivatives(v)[0]-power(v)+power(0), inflection, me, xtol=1e-12)
    slope = (power(switch)-power(0))/switch

    def envelope(v):
        v = np.asarray(v)
        return np.where(v <= switch, power(0)+slope*v, power(v))

    check('hover_power', power(0) == P0+PI and power(0) > 0, power_W=float(power(0)))
    check('continuous_shape_certificate', derivatives(0)[1] < 0 < derivatives(vc)[1]
          and derivatives(VMAX)[0] > 0 and VMAX*derivatives(VMAX)[0]-power(VMAX) > 0,
          inflection_m_s=inflection, induced_convexity_threshold_m_s=vc,
          second_derivative_at_zero=float(derivatives(0)[1]),
          range_stationarity_at_vmax=float(VMAX*derivatives(VMAX)[0]-power(VMAX)))
    check('unique_interior_roots', len(roots(lambda v: derivatives(v)[0], positive)) == 1
          and len(roots(lambda v: v*derivatives(v)[0]-power(v), positive)) == 1
          and len(roots(lambda v: derivatives(v)[1], dense)) == 1)
    check('power_global_minimum', power(me) <= np.min(power(dense))+1e-10,
          optimum_W=float(power(me)), endpoint_powers_W=[float(power(0)), float(power(VMAX))])
    check('range_global_minimum', power(mr)/mr <= np.min(power(positive)/positive)+1e-10,
          optimum_J_m=float(power(mr)/mr), endpoint_30_J_m=float(power(VMAX)/VMAX),
          near_zero_J_m=float(power(1e-8)/1e-8), zero_limit='positive infinity')
    bounded = minimize_scalar(lambda v: DISTANCE*power(v)/v, bounds=(1e-8, VMAX),
                              method='bounded', options={'xatol': 1e-11})
    check('independent_fixed_distance_optimization', bounded.success and abs(bounded.x-mr) < 1e-5,
          independent_optimum_m_s=float(bounded.x), difference_m_s=float(bounded.x-mr))
    probes = np.linspace(0.02, 29.98, 501)
    step = 0.002
    finite_first = (-power(probes+2*step)+8*power(probes+step)
                    -8*power(probes-step)+power(probes-2*step))/(12*step)
    finite_second = (power(probes+step)-2*power(probes)+power(probes-step))/step**2
    first_error = float(np.max(np.abs(finite_first-derivatives(probes)[0])))
    second_error = float(np.max(np.abs(finite_second-derivatives(probes)[1])))
    check('independent_derivative_checks', first_error < 1e-7 and second_error < 1e-5,
          max_first_error=first_error, max_second_error=second_error)
    check('stationarity_and_tangency', abs(derivatives(me)[0]) < 1e-9
          and abs(mr*derivatives(mr)[0]-power(mr)) < 1e-8
          and abs(switch*derivatives(switch)[0]-power(switch)+power(0)) < 1e-8,
          power_derivative_at_me=float(derivatives(me)[0]),
          origin_tangent_residual_W=float(mr*derivatives(mr)[0]-power(mr)),
          hover_tangent_residual_W=float(switch*derivatives(switch)[0]-power(switch)+power(0)))
    check('envelope_minorant', np.min(power(dense)-envelope(dense)) >= -1e-9,
          minimum_gap_W=float(np.min(power(dense)-envelope(dense))))

    rows, convergence = [], []
    for mean in AVERAGES:
        previous = float('inf')
        for points in (121, 241, 481, 961):
            candidate = grid_best(mean, points)
            grid_energy = DURATION*candidate[3]
            check(f'grid_monotonic_{mean}_{points}', grid_energy <= previous+1e-7)
            previous = grid_energy
            convergence.append(dict(method='alpha_speed_grid', velocity_points=points,
                                    alpha_points=points, average_speed_m_s=mean, energy_J=grid_energy,
                                    envelope_energy_J=float(DURATION*envelope(mean)),
                                    gap_J=float(grid_energy-DURATION*envelope(mean))))
        best = refine(mean, candidate)
        v1, v2, fraction, mean_power = best
        constant, optimized = float(DURATION*power(mean)), DURATION*mean_power
        saving = constant-optimized
        duration1, duration2 = fraction*DURATION, (1-fraction)*DURATION
        traveled = v1*duration1 + v2*duration2
        hover_seconds = (duration1 if v1 == 0 else 0) + (duration2 if v2 == 0 else 0)
        check(f'profile_feasible_{mean}', 0 <= v1 <= VMAX and 0 <= v2 <= VMAX
              and 0 <= fraction <= 1 and abs(traveled-mean*DURATION) < 1e-8
              and abs(duration1+duration2-DURATION) < 1e-12,
              distance_residual_m=traveled-mean*DURATION,
              duration_residual_s=duration1+duration2-DURATION)
        check(f'energy_optimality_{mean}', optimized <= constant+1e-7
              and optimized >= DURATION*power(me)-1e-7
              and abs(optimized-DURATION*envelope(mean)) < 1e-6,
              gap_to_envelope_J=float(optimized-DURATION*envelope(mean)))
        check(f'fine_optimization_grid_{mean}', grid_energy-optimized < 0.05,
              grid_gap_J=grid_energy-optimized)
        rows.append(dict(average_speed_m_s=mean, distance_m=mean*DURATION, duration_s=DURATION,
                         constant_energy_J=constant, optimized_energy_J=optimized,
                         v1_m_s=v1, v2_m_s=v2, alpha=fraction, duration1_s=duration1,
                         duration2_s=duration2, savings_J=saving, savings_percent=100*saving/constant,
                         hover_in_optimum=hover_seconds > 0, hover_duration_s=hover_seconds,
                         hover_energy_J=float(hover_seconds*power(0)),
                         envelope_energy_J=float(DURATION*envelope(mean)),
                         universal_bound_J=float(DURATION*power(me)),
                         constant_globally_optimal=abs(saving) < 1e-7))
    for points in (301, 601, 1201, 2401, 4801):
        speeds = np.linspace(0, VMAX, points)
        values = power(speeds)
        hull = lower_hull(speeds, values)
        hull_energy = DURATION*np.interp(AVERAGES, speeds[hull], values[hull])
        for mean, energy in zip(AVERAGES, hull_energy):
            convergence.append(dict(method='lower_convex_hull', velocity_points=points,
                                    alpha_points=0, average_speed_m_s=mean, energy_J=float(energy),
                                    envelope_energy_J=float(DURATION*envelope(mean)),
                                    gap_J=float(energy-DURATION*envelope(mean))))
        if points == 4801:
            check('convex_hull_convergence', np.max(np.abs(hull_energy-DURATION*envelope(AVERAGES))) < 0.005,
                  max_scenario_error_J=float(np.max(np.abs(hull_energy-DURATION*envelope(AVERAGES)))))
    hull = lower_hull(dense, power(dense))
    sampled_envelope = np.interp(dense, dense[hull], power(dense)[hull])
    check('dense_convex_envelope_agreement', np.max(np.abs(sampled_envelope-envelope(dense))) < 1e-5,
          max_error_W=float(np.max(np.abs(sampled_envelope-envelope(dense)))))
    for mean in (0.0, 10.0, VMAX):
        a, v, e = landscape(mean, 301)
        check(f'alpha_endpoints_and_constant_{mean}', np.all(e[0] == DURATION*power(mean))
              and np.all(e[-1, np.isclose(v, mean)] == DURATION*power(mean))
              and profile(mean, mean, mean)[3] == power(mean))
    rng = np.random.default_rng(20261028)
    random_speeds = rng.uniform(0, VMAX, (5000, 8))
    weights = rng.dirichlet(np.ones(8), size=5000)
    means = np.sum(weights*random_speeds, axis=1)
    random_energy = DURATION*np.sum(weights*power(random_speeds), axis=1)
    check('arbitrary_eight_level_trajectories', np.all(random_energy >= DURATION*envelope(means)-1e-8)
          and np.all(random_energy >= DURATION*power(me)-1e-8), trajectories=5000, seed=20261028)

    selected = next(r for r in rows if r['average_speed_m_s'] == DISTANCE/DURATION)
    check('selected_case_is_constant', selected['constant_globally_optimal']
          and selected['v1_m_s'] == 10 and selected['v2_m_s'] == 10)
    summary = [
        ('maximum_endurance_speed', me, 'm/s'), ('maximum_range_speed', mr, 'm/s'),
        ('minimum_power', float(power(me)), 'W'), ('power_at_maximum_range', float(power(mr)), 'W'),
        ('hover_power', float(power(0)), 'W'), ('minimum_energy_per_distance', float(power(mr)/mr), 'J/m'),
        ('fixed_distance_minimum_energy', float(DISTANCE*power(mr)/mr), 'J'),
        ('fixed_distance_duration_at_mr', DISTANCE/mr, 's'),
        ('fixed_distance_energy_at_me', float(DISTANCE*power(me)/me), 'J'),
        ('fixed_distance_duration_at_me', DISTANCE/me, 's'),
        ('fixed_time_constant_energy', selected['constant_energy_J'], 'J'),
        ('fixed_time_optimized_energy', selected['optimized_energy_J'], 'J'),
        ('fixed_time_savings', selected['savings_J'], 'J'),
        ('fixed_time_savings_percent', selected['savings_percent'], '%'),
        ('hover_cruise_transition_speed', switch, 'm/s'),
        ('inflection_speed', inflection, 'm/s'), ('universal_fixed_time_energy_bound', float(DURATION*power(me)), 'J'),
    ]
    save_csv('summary.csv', [dict(metric=k, value=v, unit=u) for k, v, u in summary])
    fixed_speeds = np.unique(np.r_[np.geomspace(0.1, VMAX, 2001), me, mr])
    save_csv('fixed_distance.csv', [dict(speed_m_s=float(v), distance_m=DISTANCE, power_W=float(power(v)),
             duration_s=DISTANCE/v, energy_J=float(DISTANCE*power(v)/v), energy_per_m_J=float(power(v)/v),
             is_maximum_endurance=bool(v == me), is_maximum_range=bool(v == mr)) for v in fixed_speeds])
    save_csv('fixed_time_variable_speed.csv', [dict(strategy='constant', **{
        **selected, 'v1_m_s': 10.0, 'v2_m_s': 10.0, 'alpha': 0.5}), dict(strategy='optimized_two_level', **selected)])
    save_csv('sensitivity.csv', rows)
    save_csv('convergence.csv', convergence)
    save_csv('power_convex_envelope.csv', [dict(speed_m_s=float(v), power_W=float(p),
             numerical_envelope_W=float(h), continuous_envelope_W=float(e))
             for v, p, h, e in zip(dense, power(dense), sampled_envelope, envelope(dense))])
    times = np.linspace(0, DURATION, 1001)
    save_csv('profiles.csv', [dict(time_s=float(t), constant_speed_m_s=10.0,
             optimized_speed_m_s=10.0, constant_distance_m=10*t, optimized_distance_m=10*t,
             constant_cumulative_energy_J=float(t*power(10)),
             optimized_cumulative_energy_J=float(t*power(10))) for t in times])
    make_figures(me, mr, switch, rows, dense, sampled_envelope, envelope)
    report = dict(status='CURRENTLY_VERIFIED_PASS', checks=checks, check_count=len(checks),
                  python=platform.python_version(), interpreter=sys.executable,
                  packages=dict(numpy=np.__version__, scipy=scipy.__version__, matplotlib=matplotlib.__version__),
                  producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  parameters=dict(P0_W=P0, Pi_W=PI, Utip_m_s=UTIP, v0_m_s=V0, d0=D0,
                                  rho_kg_m3=RHO, solidity=SOLIDITY, area_m2=AREA, vmax_m_s=VMAX),
                  tolerances=dict(energy_J=1e-6, distance_m=1e-8, duration_s=1e-12,
                                  fine_optimization_grid_J=0.05, fine_hull_J=0.005),
                  scope='Constant-altitude, no-wind propulsion only; instantaneous switching; no acceleration costs.',
                  global_argument='Single inflection and hover-tangent convex envelope; derivation in README.md.')
    (BASE / 'results/validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], checks=len(checks),
                         summary={k: v for k, v, _ in summary}), indent=2))


if __name__ == '__main__':
    main()
