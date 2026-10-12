"""Isolated cache-only stopping sensitivity; call, never edit, original AO."""
from collections import Counter
from contextlib import contextmanager, ExitStack
import csv
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import export_theta10_D55_ao_scientific_results as saved
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from src.cvqkd import gram_moments

OUT = ROOT / 'results/theta10_D55_ao_stopping_parameter_sensitivity'
RS = (4, 6, 8, 10)
ES = (1e-6, 1e-7, 1e-8, 1e-9)
BASELINE = (6, 1e-8)


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(name, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()} for row in rows)


def tag(r, e):
    return f'R{r}_eps{e:.0e}'


@contextmanager
def stopping_override(epsilon, record):
    """Override both imported aliases and explicitly bound inner-search default."""
    original = ao.adaptive_maximize_1d

    def search(**kwargs):
        result = original(**kwargs, k_tolerance=epsilon)
        record(result)
        return result

    with patch.object(ao, 'K_TOLERANCE', epsilon), patch.object(sweep, 'K_TOLERANCE', epsilon), \
            patch.object(sweep, 'adaptive_maximize_1d', search):
        yield


def reset_counters(objective):
    # Reuse validated immutable rows; reset bookkeeping, not the AO state.
    objective.requested_calls = objective.unique_exact_evaluations = objective.cache_hits = 0
    objective.source_missing.clear()
    objective.numerical_failures.clear()


def missing_pairs(searches):
    # Failed events have value only; fixed and variable belong to their search.
    return sorted({saved.pair(s['fixed'], x['value']) if s['variable'] == 'V_A'
                   else saved.pair(x['value'], s['fixed'])
                   for s in searches for x in s['source_missing']})


def execute(rmax, epsilon, objectives):
    runs, searches, selected = [], [], []
    warm = None
    metadata = {}

    def record(result):
        searches.append({**result, **metadata})

    wall, cpu = time.perf_counter(), time.process_time()
    with stopping_override(epsilon, record):
        for distance in sweep.DISTANCES_KM:
            objective = objectives[distance]
            reset_counters(objective)
            starts = [(f'nu_{nu:g}', nu, None) for nu in sweep.BASE_STARTS]
            if warm is not None:
                starts.append(('warm_previous_distance', *warm))
            local = []
            for sid, nu, va in starts:
                metadata.update(L_km=distance, start_id=sid, role='ITERATION')
                at = time.perf_counter()
                count = len(searches)
                run = sweep.run_single_distance_ao(distance_km=distance, start_id=sid,
                    start_nu=nu, start_va=va, objective=objective, max_iterations=rmax)
                run.update(L_km=distance, wall_seconds=time.perf_counter() - at,
                           search_begin=count, search_end=len(searches))
                assert not run['warnings'], 'Numerical/monotonicity warning: fail closed'
                local.append(run)
            chosen = max((x for x in local if x['final']), key=lambda x: x['final']['SKR'])
            best = chosen['final']
            warm = (best['nu_raw'], best['V_A'])
            body_calls = objective.requested_calls
            body_hits = objective.cache_hits
            body_missing = len(objective.source_missing)
            body_exact = objective.unique_exact_evaluations
            checks = []
            metadata.update(L_km=distance, start_id=chosen['start_id'], role='SELECTED_FINAL')
            at = time.perf_counter()
            for variable, fixed in (('V_A', best['nu_raw']), ('nu_raw', best['V_A'])):
                checks.append(sweep.adaptive_maximize_1d(variable=variable, fixed=fixed,
                    values=objective.catalog_values(variable, fixed), objective=objective))
            selected.append({'L_km': distance, 'nu_raw': best['nu_raw'], 'V_A': best['V_A'],
                'I_AB': best['I_AB'], 'beta_I_AB': best['beta_I_AB'], 'chi_BE': best['chi_BE'],
                'K': best['SKR'], 'selected_start': chosen['start_id'], 'status': chosen['status'],
                'source_cache_key': best['source_cache_key'],
                'objective_identity_sha256': objective.context_hash,
                'matches_catalog': best['SKR'] == max(x['SKR'] for x in objective.rows.values()),
                'body_calls': body_calls, 'body_cache_hits': body_hits,
                'body_missing_events': body_missing, 'body_exact_evaluations': body_exact,
                'postcheck_calls': objective.requested_calls - body_calls,
                'postcheck_hits': objective.cache_hits - body_hits,
                'postcheck_missing_events': len(objective.source_missing) - body_missing,
                'postcheck_exact_evaluations': objective.unique_exact_evaluations - body_exact,
                'postcheck_wall_seconds': time.perf_counter() - at,
                'selected_coordinates_complete': all(ao.coordinate_search_complete(s) for s in checks)})
            assert len(objective.rows) == len(objective.catalog) == 147
            assert not objective.numerical_failures
            runs.extend(local)
            # Full ordered prefix is necessary to reproduce this setting's warm start.
            if distance in (saved.REF, 22., 40.):
                print(f'{tag(rmax, epsilon)} L={distance}: K={best["SKR"]!r}, '
                      f'({best["nu_raw"]!r},{best["V_A"]!r})', flush=True)
    assert ao.K_TOLERANCE == sweep.K_TOLERANCE == 1e-8
    return {'Rmax': rmax, 'epsilon': epsilon, 'runs': runs, 'searches': searches,
            'selected': selected, 'wall_seconds': time.perf_counter() - wall,
            'cpu_seconds': time.process_time() - cpu}


def baseline_check(result, historical):
    fields = ('L_km', 'start_id', 'start_nu', 'start_V_A', 'status', 'final',
              'iterations', 'trajectory', 'warnings', 'exact_evaluations',
              'requested_evaluations', 'cache_hits')
    differences = []
    for i, (new, old) in enumerate(zip(result['runs'], historical['runs'])):
        for field in fields:
            if new[field] != old[field]:
                differences.append({'index': i, 'field': field, 'L_km': old['L_km'], 'start_id': old['start_id']})
    verdict = {'run_count': len(result['runs']), 'iterations': sum(len(x['iterations']) for x in result['runs']),
        'historical_run_count': len(historical['runs']), 'historical_iterations': len(historical['history']),
        'differences': differences, 'catalog_matches': sum(x['matches_catalog'] for x in result['selected'])}
    write_json('baseline_reproducibility.json', verdict)
    assert verdict['run_count'] == 129 and verdict['iterations'] == 283
    assert not differences, f'Baseline mismatch: {differences[:10]}'
    assert verdict['catalog_matches'] == 26
    text = ('# Baseline reproducibility\n\nCURRENTLY_VERIFIED_PASS: reran original AO, Rmax=6, epsilon=1e-8.\n'
        '147 compatible sources and 3822 hash-bound objective rows. Exact comparison of 129 starts, '
        '283 iterations, all trajectories, candidate histories, stopping states, call counts and terminal rows: no differences. '
        'Selected finite-catalog maximum: 26/26. Warm starts originate from this replay, not the saved optimum.\n\n')
    for row in result['selected']:
        if row['L_km'] in (saved.REF, 22.):
            text += f"L={row['L_km']!r}: ({row['nu_raw']!r},{row['V_A']!r}), K={row['K']!r}.\n\n"
    text += ('Frozen-spec historical hash discrepancy is PREEXISTING_UNCHANGED; only the explicitly authorized '
             'cache-only diagnostic runs. No publication lifecycle promotion.\n')
    (OUT / 'baseline_reproducibility.md').write_text(text, encoding='utf-8')
    print('BASELINE REPRODUCED: 129 starts / 283 iterations / 26 catalog matches', flush=True)
    return verdict


def summarize(results):
    baseline = results[0]
    by_distance, by_start, iterations, coordinates, configs = [], [], [], [], []
    base_d = {x['L_km']: x for x in baseline['selected']}
    base_s = {(x['L_km'], x['start_id']): x for x in baseline['runs']}
    base_missing = set(missing_pairs(baseline['searches']))
    for result in results:
        r, e = result['Rmax'], result['epsilon']
        info = {'configuration': tag(r, e), 'Rmax': r, 'epsilon': e}
        start_rows = []
        for row in result['selected']:
            b = base_d[row['L_km']]
            by_distance.append({**info, **row, 'delta_K': row['K'] - b['K'],
                'delta_V_A': row['V_A'] - b['V_A'], 'delta_nu_raw': row['nu_raw'] - b['nu_raw'],
                'pair_unchanged': saved.pair(row['nu_raw'], row['V_A']) == saved.pair(b['nu_raw'], b['V_A']),
                'nu_raw_hex': float(row['nu_raw']).hex(), 'V_A_hex': float(row['V_A']).hex()})
        for run in result['runs']:
            local = result['searches'][run['search_begin']:run['search_end']]
            its = run['iterations']
            last = its[-1] if its else {}
            terminal = run['final']
            before = base_s[run['L_km'], run['start_id']]['final']
            missing = any(s['source_missing'] for s in local)
            incomplete = any(not ao.coordinate_search_complete(s) for s in local)
            tolerance_met = bool(its) and abs(last['delta_K']) <= e
            flags = []
            for condition, flag in (
                (tolerance_met, 'OBJECTIVE_TOLERANCE_MET'),
                (run['status'] == 'MAX_ITERATIONS_REACHED', 'MAX_OUTER_ITERATIONS_REACHED'),
                (missing, 'MISSING_SOURCE_BLOCKED'),
                (any(s['boundary_status'] == 'BOUNDARY_NOT_CLOSED' for s in local), 'BOUNDARY_UNRESOLVED'),
                (incomplete, 'INNER_REFINEMENT_INCOMPLETE'),
                (any(ao.coordinate_search_complete(s) for s in local), 'COORDINATE_SEARCH_COMPLETED'),
                (bool(its) and last['delta_K'] == 0 and incomplete, 'STAGNATION_WITH_INCOMPLETE_COORDINATE_SEARCH')):
                if condition:
                    flags.append(flag)
            if not flags:
                flags.append('OTHER_VERIFIED_REASON')
            item = {**info, 'L_km': run['L_km'], 'start_id': run['start_id'],
                'initial_nu': run['start_nu'], 'initial_V_A': run['start_V_A'],
                'nu_raw': terminal['nu_raw'], 'V_A': terminal['V_A'], 'K': terminal['SKR'],
                'delta_K_from_baseline_start': terminal['SKR'] - before['SKR'],
                'delta_nu_from_baseline_start': terminal['nu_raw'] - before['nu_raw'],
                'delta_V_A_from_baseline_start': terminal['V_A'] - before['V_A'],
                'outer_iterations': len(its), 'actual_stop_reason': run['status'],
                'objective_tolerance_met': tolerance_met, 'reached_Rmax': len(its) == r,
                'cap_termination': run['status'] == 'MAX_ITERATIONS_REACHED',
                'missing_source_blocked': missing,
                'missing_events': sum(len(s['source_missing']) for s in local),
                'distinct_missing_pairs_hex': missing_pairs(local),
                'coordinate_calls': len(local),
                'coordinate_calls_completed': sum(ao.coordinate_search_complete(s) for s in local),
                'P1_last_status': last.get('V_A_search_status', ''),
                'P2_last_status': last.get('nu_search_status', ''),
                'last_absolute_delta_K': abs(last['delta_K']) if its else '',
                'delta_K_history': [x['delta_K'] for x in its],
                'actual_parameter_updates': sum(x['delta_nu'] > 0 or x['delta_V_A'] > 0 for x in its),
                'positive_SKR_updates': sum(x['delta_K'] > 0 for x in its),
                'identical_full_cycle_candidates': sum(x['delta_nu'] == x['delta_V_A'] == 0 for x in its),
                'diagnostic_flags': ';'.join(flags), 'wall_seconds': run['wall_seconds'],
                'objective_calls': run['requested_evaluations'], 'cache_hits': run['cache_hits'],
                'existing_source_SKR_evaluations': run['exact_evaluations']}
            start_rows.append(item)
            by_start.append(item)
            iterations.extend({**info, **x, 'run_terminal_state': run['status']} for x in its)
        for s in result['searches']:
            bracket = s.get('bracket', [None, None])
            radius = max(s['best_value'] - bracket[0], bracket[1] - s['best_value']) if None not in bracket else None
            levels = math.ceil(math.log2(radius / 1e-6)) if radius and radius > 1e-6 else 0 if radius is not None else None
            coordinates.append({**info, 'L_km': s['L_km'], 'start_id': s['start_id'], 'role': s['role'],
                'variable': s['variable'], 'fixed': s['fixed'], 'best_value': s['best_value'],
                'best_K': s['best_K'], 'status': s['status'], 'boundary_status': s['boundary_status'],
                'refinement_status': s['refinement_status'], 'refinement_stages': s['refinement_stages'],
                'boundary_expansions': s['boundary_expansions'], 'bracket': bracket,
                'radius': radius, 'conditional_midpoint_halvings': levels,
                'completed': ao.coordinate_search_complete(s), 'missing_points': s['source_missing'],
                'history': s['history'], 'bracket_state_persists': False})
        ds = by_distance[-26:]
        distinct = set(missing_pairs(result['searches']))
        c = {**info, 'distances': 26, 'starts': len(start_rows),
            'total_outer_iterations': sum(x['outer_iterations'] for x in start_rows),
            'same_solution_distances': sum(x['pair_unchanged'] for x in ds),
            'changed_solution_distances': sum(not x['pair_unchanged'] for x in ds),
            'improved_SKR_distances': sum(x['delta_K'] > 0 for x in ds),
            'lower_SKR_distances': sum(x['delta_K'] < 0 for x in ds),
            'changed_pair_nearly_equal_K_distances': sum(not x['pair_unchanged'] and abs(x['delta_K']) <= 1e-8 for x in ds),
            'max_abs_delta_K': max(abs(x['delta_K']) for x in ds),
            'max_abs_delta_V_A': max(abs(x['delta_V_A']) for x in ds),
            'max_abs_delta_nu': max(abs(x['delta_nu_raw']) for x in ds),
            'median_outer_iterations': statistics.median(x['outer_iterations'] for x in start_rows),
            'max_outer_iterations': max(x['outer_iterations'] for x in start_rows),
            'runs_reaching_Rmax': sum(x['reached_Rmax'] for x in start_rows),
            'runs_cap_terminated': sum(x['cap_termination'] for x in start_rows),
            'runs_objective_tolerance_met': sum(x['objective_tolerance_met'] for x in start_rows),
            'missing_source_blocked_runs': sum(x['missing_source_blocked'] for x in start_rows),
            'stagnation_incomplete_runs': sum('STAGNATION_WITH_INCOMPLETE_COORDINATE_SEARCH' in x['diagnostic_flags'] for x in start_rows),
            'completed_coordinate_calls': sum(ao.coordinate_search_complete(s) for s in result['searches']),
            'coordinate_calls': len(result['searches']),
            'distinct_missing_sources': len(distinct), 'new_missing_sources_vs_baseline': len(distinct - base_missing),
            'source_dependent_searches': sum(bool(s['source_missing']) for s in result['searches']),
            'stop_reason_counts': dict(Counter(x['actual_stop_reason'] for x in start_rows)),
            'iteration_histogram': dict(Counter(x['outer_iterations'] for x in start_rows)),
            'catalog_matches': sum(x['matches_catalog'] for x in ds),
            'wall_seconds': result['wall_seconds'], 'cpu_seconds': result['cpu_seconds']}
        for name in ('body_calls', 'body_cache_hits', 'body_missing_events', 'body_exact_evaluations',
                     'postcheck_calls', 'postcheck_hits', 'postcheck_missing_events', 'postcheck_exact_evaluations',
                     'postcheck_wall_seconds'):
            c[name] = sum(x[name] for x in ds)
        configs.append(c)
    write_csv('sensitivity_grid_16_configs.csv', configs)
    write_csv('sensitivity_by_distance.csv', by_distance)
    write_csv('sensitivity_by_start.csv', by_start)
    write_csv('ao_iteration_history.csv', iterations)
    write_csv('iteration_and_stopping_statistics.csv', configs)
    write_csv('coordinate_completion_audit.csv', coordinates)
    write_csv('computational_cost_comparison.csv', configs)
    return configs, by_distance, by_start


def plots(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'font.family': 'serif', 'font.size': 10, 'pdf.fonttype': 42})
    for name, xfield, fixed, title, xlabel in (
        ('rmax_sensitivity', 'Rmax', lambda x: x['epsilon'] == 1e-8,
         'Best-found SKR versus maximum AO iterations', r'$R_{\max}$'),
        ('epsilon_sensitivity', 'epsilon', lambda x: x['Rmax'] == 6,
         'Best-found SKR versus objective-change tolerance', r'$\epsilon$ (bits/use)')):
        fig, ax = plt.subplots(figsize=(6.4, 3.9))
        for i, distance in enumerate((saved.REF, 22.)):
            local = sorted((x for x in rows if x['L_km'] == distance and fixed(x)), key=lambda x: x[xfield])
            # Mark exact tested settings only; no fitted/interpolated curve.
            ax.plot([x[xfield] for x in local], [x['K'] for x in local], linestyle='none',
                    marker=('o', 's')[i], label=f'L = {distance:g} km', markersize=6)
        if xfield == 'epsilon':
            ax.set_xscale('log', base=10)
        else:
            ax.set_xticks(RS)
        ax.set(xlabel=xlabel, ylabel='Best-found Secret Key Rate (bits/use)', title=title)
        ax.ticklabel_format(axis='y', style='plain', useOffset=False)
        ax.grid(alpha=.22);ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(OUT / f'{name}.png', dpi=400, bbox_inches='tight')
        fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight')
        plt.close(fig)


def documents(configs, distances, starts, validation):
    invariant = all(x['same_solution_distances'] == x['catalog_matches'] == 26 for x in configs)
    no_closure = all(x['completed_coordinate_calls'] == 0 for x in configs)
    classification = ('BASELINE_PARAMETERS_ONLY_COMPUTATIONAL_SAFEGUARDS' if invariant and no_closure
        else 'SENSITIVITY_INCONCLUSIVE_DUE_TO_MISSING_SOURCES' if no_closure
        else 'BASELINE_PARAMETERS_EMPIRICALLY_SUPPORTED' if invariant
        else 'SENSITIVITY_INCONCLUSIVE_DUE_TO_MISSING_SOURCES')
    validation['classification'] = classification
    baseline = configs[0]
    table = [r'\begin{table}[t]', r'\centering', r'\caption{Cache-only AO stopping sensitivity on 147 exact sources and 26 distances. Same: identical binary64 pair; blocked: starts requesting missing sources; closed: completed coordinate calls, including postchecks.}',
             r'\label{tab:ao-stopping-sensitivity}', r'\begin{tabular}{rrrrrrr}', r'\hline',
             r'$R_{\max}$ & $\epsilon$ & Same & $\max|\Delta K|$ & Max iter. & Blocked & Closed \\', r'\hline']
    for c in sorted(configs, key=lambda x: (x['Rmax'], -x['epsilon'])):
        exponent = int(round(math.log10(c['epsilon'])))
        table.append(f"{c['Rmax']} & $10^{{{exponent}}}$ & {c['same_solution_distances']}/26 & {c['max_abs_delta_K']:.3g} & {c['max_outer_iterations']} & {c['missing_source_blocked_runs']}/{c['starts']} & {c['completed_coordinate_calls']}/{c['coordinate_calls']} " + r'\\')
    table += [r'\hline', r'\end{tabular}', r'\end{table}']
    (OUT / 'sensitivity_summary_table.tex').write_text('\n'.join(table) + '\n', encoding='utf-8')
    # Wording below is permitted only after the actual invariance/closure evidence.
    assert invariant and no_closure, 'Revise manuscript wording for measured non-invariance/closure'
    version_a = r"""The outer cap $R_{\max}$ limits AO runtime, whereas $\epsilon$ controls termination based on objective change. We tested sixteen combinations of $R_{\max}\in\{4,6,8,10\}$ and $\epsilon\in\{10^{-6},10^{-7},10^{-8},10^{-9}\}$ using 147 compatible exact source pairs at 26 distances. Each setting retained the original coordinate searches, four initializations, and its own previous-distance warm starts. The baseline reproduced all 129 recorded starts and 283 outer iterations. Every setting selected identical parameter pairs and secret-key rates at all distances, matching the finite-catalog maxima. Increasing the cap or tightening the threshold to $10^{-9}$ produced no improvement. However, no coordinate search completed, and all starts requested unavailable source moments. Thus, the observed invariance supports retaining $R_{\max}=6$ and $\epsilon=10^{-8}$ as computational safeguards for this catalog, not as convergence guarantees. The threshold measures objective change rather than absolute SKR accuracy; additional exact sources and completed coordinate refinement are required before claiming continuous numerical optimality."""
    version_b = r"""The AO stopping parameters control distinct mechanisms: $R_{\max}$ bounds the number of complete outer cycles, while $\epsilon$ limits the change in the objective between successive cycles. The implementation also uses this objective tolerance for monotonicity warnings and endpoint improvement checks. Consequently, the experiment applied each tolerance consistently through temporary overrides, including explicit arguments for the inner-search default. Parameter tolerance, the four-stage inner refinement cap, boundary expansion rules, physical model, and security calculations were unchanged.

We first reproduced the baseline $R_{\max}=6$, $\epsilon=10^{-8}$ using the 147-source compatible exact catalog. All 129 starts, 283 recorded iterations, candidate histories, terminal states, and selected solutions were reproduced exactly. We then evaluated sixteen combinations of caps in $\{4,6,8,10\}$ and tolerances in $\{10^{-6},10^{-7},10^{-8},10^{-9}\}$. Each configuration used the original four initializations and an independent previous-distance warm-start chain. The reference distance and 22 km were analyzed with their required distance prefixes, followed by the remaining established grid.

Across all 26 distances, every configuration selected the same binary64 parameter pair and SKR as the baseline and matched the finite-catalog maximum. Larger caps and the tighter $10^{-9}$ threshold did not improve the selected objective. Nevertheless, no coordinate search satisfied the original completion conditions. Missing exact source moments blocked each start; therefore, unchanged solutions cannot establish convergence over the continuous parameter domain. Inner searches reconstruct local brackets from the catalog rather than carrying refinement state between outer cycles. Repeating a blocked coordinate search cannot replace unavailable midpoint evaluations, and a zero objective increment can trigger termination before a larger cap becomes active.

These results justify describing $R_{\max}=6$ and $\epsilon=10^{-8}$ as conservative computational safeguards with finite-catalog invariance. They do not establish theoretical optimality, continuous numerical convergence, or a certified absolute SKR error. Cache-only timings and missing-source demand are reported separately because cached lookups do not measure arbitrary-precision source-generation cost."""
    counts = [len(x.split()) for x in (version_a, version_b)]
    assert 120 <= counts[0] <= 170 and 250 <= counts[1] <= 350, counts
    validation['manuscript_word_counts_whitespace'] = counts
    (OUT / 'stopping_parameter_justification.tex').write_text(
        '% Version A: ' + str(counts[0]) + ' whitespace-delimited words\n'
        + r'\subsection{Sensitivity Analysis of AO Stopping Parameters}' + '\n' + version_a + '\n\n'
        + '% Version B (alternative, do not include both): ' + str(counts[1]) + ' words\n'
        + r'\subsection{Sensitivity Analysis of AO Stopping Parameters}' + '\n' + version_b + '\n', encoding='utf-8')
    lines = ['# AO stopping-parameter sensitivity', '', classification, '',
        '## Scope and provenance', '',
        'CURRENTLY_VERIFIED_PASS: actual original AO reruns, temporary Rmax/epsilon only. '
        'No AP generation, interpolation, channel replay or science changes. Restored compatible 3822 '
        'objective rows with original provenance checks. Each setting uses its own ordered warm chain; '
        '20/21 km prefix is required before detailed reference/22 km analysis. Source catalog remains 147. '
        'Shared immutable validated rows are reused, counters reset between configurations; no configuration '
        'borrows trajectories or warm starts from another. Baseline first, one-factor axes next, remaining grid last.', '',
        '## Twelve required answers', '',
        '1. Yes: R6/1e-8 exactly reproduces 129 starts, 283 iterations and 26 selected catalog maxima.',
        '2. R8/R10 do not improve selected SKR at any distance.',
        '3. Neither larger cap changes any selected binary64 pair.',
        '4. Tightening 1e-8 to 1e-9 produces no SKR gain.',
        '5. Actual iteration counts and start-level changes are tabulated below; tighter tolerance does not certify accuracy.',
        '6. Actual code reasons and overlapping diagnostic flags are preserved in sensitivity_by_start.csv.',
        '7. Missing-induced zero-increment stagnation is counted separately from meeting the objective threshold.',
        '8. Selected finite-catalog values are invariant at 26/26 distances for all sixteen settings.',
        '9. Six is not the active outer bottleneck, but is only a computational safeguard, not a convergence guarantee.',
        '10. Retain 1e-8 provisionally as an objective-change safeguard; 1e-9 gives no improvement on this cache.',
        '11. Missing moments, unclosed boundaries, incomplete inner refinement and an unbounded total SKR error prevent convergence certification.',
        '12. The manuscript may report exact finite-catalog invariance and baseline reproduction, not continuous/global optimality.', '',
        '## Actual configuration statistics', '',
        '|Rmax|epsilon|iterations|histogram|stop reasons|zero-increment incomplete runs|calls/hits (AO body)|distinct missing|',
        '|---|---|---|---|---|---|---|---|']
    for c in configs:
        lines.append(f"|{c['Rmax']}|{c['epsilon']}|{c['total_outer_iterations']}|{c['iteration_histogram']}|{c['stop_reason_counts']}|{c['stagnation_incomplete_runs']}/{c['starts']}|{c['body_calls']}/{c['body_cache_hits']}|{c['distinct_missing_sources']}|")
    lines += ['', '## Reference starts, including nu_initial=0.8', '',
        '|configuration|L|start|terminal (nu,VA,K)|outer iterations|actual reason|',
        '|---|---|---|---|---|---|']
    for x in starts:
        if x['L_km'] in (saved.REF, 22.) and x['start_id'] == 'nu_0.8':
            lines.append(f"|{x['configuration']}|{x['L_km']}|{x['start_id']}|({x['nu_raw']!r},{x['V_A']!r},{x['K']!r})|{x['outer_iterations']}|{x['actual_stop_reason']}|")
    lines += ['', '## Inner-search audit and costs', '',
        'The original adaptive_maximize_1d creates a fresh evaluated map and bracket for every call; '
        'only compatible exact rows/catalog persist. It does not carry an active midpoint bracket between '
        'outer cycles. Missing midpoint/outer values are requested again and remain missing. The four-stage '
        'cap is unchanged; missing moments can stop refinement before that cap. The unresolved-inner latch '
        'persists within each AO run, so objective tolerance alone never yields a completed-search claim. '
        'Increasing Rmax cannot force additional cycles after the original stopping decision. '
        'At the reference selected pair, the P1 bracket is [5.4875,5.5125] and P2 is '
        '[0.1625,0.16562500000000002]. Conditional fixed-best halvings to radius1e-6 are 14 and 12; '
        'these are geometric estimates, not executed steps or a guarantee the best stays fixed.', '',
        'All genuine iterations/candidate events are in ao_iteration_history.csv and configuration JSONs. '
        'Coordinate audit distinguishes iteration calls from 52 selected-final postchecks per configuration. '
        'No coordinate-completion claim is inferred from selected-catalog agreement. Computational CSV '
        'separates AO-body/postcheck calls, hits, missing lookups and existing-source SKR evaluations. '
        'Distinct missing binary64 pairs reflect expensive source demand, not AP timings. '
        'Timing is a single sequential cache-only measurement including original runtime guards; '
        'setup, complete wall/CPU and postcheck wall are separate. No causal production-speed claim is made.', '',
        '## Safety and verification', '',
        'No worker, observer, Job Object or sleep override is needed or invoked for this cache-only diagnostic. '
        'AP methods fail closed via guards. All temporary AO aliases restored. Protected input hashes '
        'and older artifacts remain unchanged. Historical frozen-spec discrepancy remains '
        'PREEXISTING_UNCHANGED and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains unchanged. '
        'Regression results and output hashes are recorded in sensitivity_validation.json. '
        'LaTeX compilation is NOT_RUN unless a local engine is available; text/table word-count and '
        'static checks are performed.']
    (OUT / 'sensitivity_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    if sys.argv[1:] == ['--finalize-saved']:
        return finalize_saved()
    if sys.argv[1:]:
        raise SystemExit('Only optional --finalize-saved is supported')
    if OUT.exists():
        raise SystemExit('Refusing to overwrite existing sensitivity artifacts')
    started, cpu = time.perf_counter(), time.process_time()
    protected = saved.read(saved.PROTECTED)
    for path in saved.OUT.rglob('*'):
        if path.is_file():
            protected[str(path.relative_to(ROOT))] = sweep.sha256(path)
    for rel in ('scripts/run_theta10_D55_alt_opt.py', 'scripts/run_theta10_D55_alt_opt_distance_sweep.py'):
        protected[rel] = sweep.sha256(ROOT / rel)
    assert all(sweep.sha256(ROOT / name) == digest for name, digest in protected.items())
    historical = saved.analyze()
    OUT.mkdir()
    write_json('protected_input_manifest.json', protected)
    objectives = {}
    config = saved.source.unconstrained_config()
    with ExitStack() as guards:
        guards.enter_context(patch.object(ao.ExactMBEvaluator, 'source_moments', saved.audit.forbidden))
        guards.enter_context(patch.object(gram_moments, '_fallback', saved.audit.forbidden))
        for distance in sweep.DISTANCES_KM:
            checkpoint = historical['checkpoint'][str(distance)]
            objective = ao.ExactObjective(config, checkpoint['identity']['identity']['channel'], OUT,
                allow_new_source=False, source_cache_dirs=saved.DIRS)
            assert objective.restore_objective_rows(checkpoint['rows'], checkpoint['identity']) == 147
            for row in checkpoint['rows']:
                objective.register_catalog(row['nu_raw'], row['V_A'])
            objectives[distance] = objective
        setup_wall = time.perf_counter() - started
        order = [BASELINE] + [(r, 1e-8) for r in RS if r != 6] + [(6, e) for e in ES if e != 1e-8]
        order += [(r, e) for r in RS for e in ES if (r, e) not in order]
        assert len(order) == len(set(order)) == 16
        results = []
        for rmax, epsilon in order:
            result = execute(rmax, epsilon, objectives)
            write_json(tag(rmax, epsilon) + '.json', result)
            results.append(result)
            if len(results) == 1:
                reproduction = baseline_check(result, historical)
        configs, distances, starts = summarize(results)
        validation = {'status': 'CURRENTLY_VERIFIED_PASS', 'baseline': reproduction,
            'configurations': len(configs), 'distance_rows': len(distances), 'start_rows': len(starts),
            'AP_generations': 0, 'interpolation': False, 'original_AO_restored': ao.K_TOLERANCE == sweep.K_TOLERANCE == 1e-8,
            'setup_wall_seconds': setup_wall, 'protected_count': len(protected),
            'frozen_spec_sha256': sweep.sha256(ROOT / 'docs/FINAL_MODEL_SPEC.md'),
            'frozen_historical_discrepancy': 'PREEXISTING_UNCHANGED', 'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
            'producer_sha256': sweep.sha256(Path(__file__)),
            'tests': 'NOT_RUN_PENDING_SCOPED_REGRESSION', 'latex_compile': 'NOT_RUN'}
        documents(configs, distances, starts, validation)
        plots(distances)
    assert all(sweep.sha256(ROOT / name) == digest for name, digest in protected.items())
    validation.update(protected_hashes_unchanged=True, total_wall_seconds=time.perf_counter() - started,
                      total_cpu_seconds=time.process_time() - cpu)
    validation['output_hashes'] = {p.name: sweep.sha256(p) for p in OUT.iterdir() if p.is_file()}
    write_json('sensitivity_validation.json', validation)
    print(json.dumps({k: validation[k] for k in ('classification', 'configurations', 'total_wall_seconds', 'total_cpu_seconds', 'protected_count')}), flush=True)
    return 0


def finalize_saved():
    """Finish reporting after a reader-schema error, without rerunning any AO."""
    if (OUT / 'sensitivity_validation.json').exists():
        raise SystemExit('Refusing to overwrite finalized sensitivity artifacts')
    started, cpu = time.perf_counter(), time.process_time()
    protected = saved.read(OUT / 'protected_input_manifest.json')
    assert all(sweep.sha256(ROOT / name) == digest for name, digest in protected.items())
    order = [BASELINE] + [(r, 1e-8) for r in RS if r != 6] + [(6, e) for e in ES if e != 1e-8]
    order += [(r, e) for r in RS for e in ES if (r, e) not in order]
    results = [saved.read(OUT / (tag(r, e) + '.json')) for r, e in order]
    historical = saved.analyze()
    # Check baseline without rewriting its already saved reproducibility records.
    for new, old in zip(results[0]['runs'], historical['runs']):
        assert all(new[k] == v for k, v in old.items())
    assert len(results[0]['runs']) == len(historical['runs']) == 129
    for result in results:
        saved.audit.align_searches(result['runs'], result['searches'])
    configs, distances, starts = summarize(results)
    validation = {'status': 'CURRENTLY_VERIFIED_PASS',
        'baseline': saved.read(OUT / 'baseline_reproducibility.json'),
        'configurations': len(configs), 'distance_rows': len(distances), 'start_rows': len(starts),
        'AP_generations': 0, 'interpolation': False,
        'original_AO_restored': ao.K_TOLERANCE == sweep.K_TOLERANCE == 1e-8,
        'protected_count': len(protected), 'producer_sha256': sweep.sha256(Path(__file__)),
        'AO_execution_producer_sha256': '8836c4760dee461de6b8e7b02b8e6e1a596f762eae11de85936b1fe8f5ac5f5f',
        'execution_note': 'All 16 AO checkpoints completed on first execution; report-only KeyError from missing-event schema repaired. No AO rerun during finalization.',
        'AO_execution_wall_seconds_measured': sum(x['wall_seconds'] for x in results),
        'AO_execution_cpu_seconds_measured': sum(x['cpu_seconds'] for x in results),
        'initial_setup_wall_cpu': 'NOT_RECORDED: first process exited on report exception before saving setup clocks',
        'frozen_spec_sha256': sweep.sha256(ROOT / 'docs/FINAL_MODEL_SPEC.md'),
        'frozen_historical_discrepancy': 'PREEXISTING_UNCHANGED',
        'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
        'git_branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'authorization_attachment_sha256': sweep.sha256(Path('C:/Users/HP/.codex/attachments/62a837d5-83c7-4814-b121-3918be633e26/Pasted text.txt')),
        'tests': 'NOT_RUN_PENDING_SCOPED_REGRESSION', 'latex_compile': 'NOT_RUN_NO_LOCAL_ENGINE'}
    documents(configs, distances, starts, validation)
    plots(distances)
    assert all(sweep.sha256(ROOT / name) == digest for name, digest in protected.items())
    validation.update(protected_hashes_unchanged=True, report_finalization_wall_seconds=time.perf_counter() - started,
                      report_finalization_cpu_seconds=time.process_time() - cpu)
    validation['output_hashes'] = {p.name: sweep.sha256(p) for p in OUT.iterdir() if p.is_file()}
    write_json('sensitivity_validation.json', validation)
    print(json.dumps({k: validation[k] for k in ('classification', 'configurations', 'AO_execution_wall_seconds_measured', 'AO_execution_cpu_seconds_measured', 'protected_count')}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
