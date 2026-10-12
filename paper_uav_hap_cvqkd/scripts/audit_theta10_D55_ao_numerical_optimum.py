"""Saved-record AO audit. No channel replay, objective evaluation, or AP allowed."""
from collections import Counter, defaultdict
from contextlib import ExitStack
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_mb_batch3 as baseline
from scripts.exact_cache_provenance import verify_source_payload, source_settings
from src.cvqkd import gram_moments

ao, io, source, sweep = baseline.ao, baseline.io, baseline.source, baseline.sweep
# ExactObjective reads these from its callable even during read-only restoration.
BETA, EPSILON, GH_ORDER = (ao.evaluate_candidate.__globals__[k] for k in ('BETA', 'EPSILON', 'GH_ORDER'))
BASE = baseline.OUT
OUT = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation'
REF = 21.9393102292


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def pair(nu, va):
    return float(nu).hex(), float(va).hex()


def forbidden(*args, **kwargs):
    raise AssertionError('Phase1 forbids new source moments, channel replay, objective evaluation and optimization')


def events(value):
    return json.loads(value) if isinstance(value, str) else value


def align_searches(runs, searches):
    """Prove the recorded call ordering against each iteration, not just counts."""
    aligned, finals, index = [], {}, 0
    for distance in sweep.DISTANCES_KM:
        local = [r for r in runs if float(r['L_km']) == distance]
        for run in local:
            previous = None
            for it in run['iterations']:
                if previous:
                    assert pair(it['nu_before'], it['V_A_before']) == pair(previous['optimized_nu'], previous['optimized_V_A'])
                    assert float(it['K_before']) == float(previous['K_after_nu'])
                for variable, fixed, prefix, k in (
                    ('V_A', it['nu_before'], 'V_A', 'K_after_VA'),
                    ('nu_raw', it['optimized_V_A'], 'nu', 'K_after_nu')):
                    s = searches[index]
                    assert s['L_km'] == distance and s['variable'] == variable and float(s['fixed']).hex() == float(fixed).hex()
                    assert s['best_K'] == float(it[k]) and s['status'] == it[prefix + '_search_status']
                    assert s['history'] == events(it[prefix + '_candidate_history'])
                    aligned.append({**s, 'search_index': index, 'start_id': run['start_id'], 'iteration': it['iteration'], 'role': 'ITERATION'})
                    index += 1
                previous = it
        selected = max((r for r in local if r.get('final')), key=lambda r: float(r['final']['SKR']))
        checks = []
        for variable, fixed in (('V_A', selected['final']['nu_raw']), ('nu_raw', selected['final']['V_A'])):
            s = searches[index]
            assert s['L_km'] == distance and s['variable'] == variable and float(s['fixed']).hex() == float(fixed).hex()
            checks.append({**s, 'search_index': index, 'start_id': selected['start_id'], 'iteration': 'FINAL_POSTCHECK', 'role': 'SELECTED_FINAL'})
            index += 1
        finals[distance] = checks
        aligned.extend(checks)
    assert index == len(searches)
    return aligned, finals


def enrich_iteration(row, artifact, bank, scope):
    row = dict(row)
    nu, va, new_nu = map(float, (row['nu_before'], row['optimized_V_A'], row['optimized_nu']))
    row.update({'artifact': str(artifact.relative_to(ROOT)), 'history_scope': scope,
                'L_km': float(row.get('distance_km', row.get('L_km', REF))),
                'start_id': row.get('start_id', row.get('run_id', 'NOT_RECORDED')),
                'VA_after_P1': va, 'K_after_P1': float(row['K_after_VA']),
                'nu_after_P2': new_nu, 'K_after_P2': float(row['K_after_nu']),
                'P1_status': row['V_A_search_status'], 'P2_status': row['nu_search_status'],
                'P1_objective_calls': 'NOT_RECORDED', 'P2_objective_calls': 'NOT_RECORDED',
                'monotonicity_tolerance': ao.K_TOLERANCE,
                'monotonicity_P1': float(row['K_after_VA']) + ao.K_TOLERANCE >= float(row['K_before']),
                'monotonicity_P2': float(row['K_after_nu']) + ao.K_TOLERANCE >= float(row['K_after_VA']),
                'total_objective_error_bound': 'NOT_ESTABLISHED'})
    for prefix, n, v in (('P1', nu, va), ('P2', new_nu, va)):
        payload = bank.get(pair(n, v))
        row[prefix + '_selected_source_key'] = payload['cache_key'] if payload else 'UNAVAILABLE_IN_CURRENT_COMPATIBLE_BANK'
        row[prefix + '_source_key_attribution'] = 'PAIR_LOOKUP_CURRENT_VERIFIED_BANK_NOT_HISTORICAL_KEY_ASSERTION'
        hist = events(row[('V_A' if prefix == 'P1' else 'nu') + '_candidate_history'])
        row[prefix + '_all_evaluated_source_keys'] = json.dumps(sorted({bank[pair(e['nu_raw'], e['V_A'])]['cache_key']
            for e in hist if e['status'] == 'EXACT_EVALUATED' and pair(e['nu_raw'], e['V_A']) in bank}))
        row[prefix + '_missing_attempts'] = sum(e['status'] == 'EXACT_SOURCE_MISSING' for e in hist)
        row[prefix + '_recorded_event_count'] = len(hist)
    return row


def diagnostic(search, rows):
    best = search['best']
    variable, value = search['variable'], float(search['best_value'])
    bracket = search['bracket']
    lower, upper = bracket
    exact = [r for r in rows if float(r['nu_raw' if variable == 'V_A' else 'V_A']).hex() == float(search['fixed']).hex()]
    neighbors = [r for r in exact if float(r[variable]) in (lower, upper)]
    issues = ['NUMERICAL_ACCURACY_UNRESOLVED']
    if ao.coordinate_search_complete(search):
        issues.insert(0, 'COORDINATE_REFINEMENT_COMPLETED')
    if search['source_missing']:
        issues.insert(0, 'MISSING_SOURCE_BLOCKED')
    if search['boundary_status'] == 'BOUNDARY_NOT_CLOSED':
        issues.insert(0, 'BOUNDARY_UNRESOLVED')
    if search['refinement_status'] == 'REFINEMENT_LIMIT_REACHED':
        issues.append('ITERATION_LIMIT_REACHED')
    radius = max(value - lower, upper - value) if lower is not None and upper is not None else None
    halvings = math.ceil(math.log2(radius / ao.PARAMETER_TOLERANCE)) if radius and radius > ao.PARAMETER_TOLERANCE else 0 if radius is not None else None
    return {'L_km': search['L_km'], 'coordinate': variable, 'fixed': search['fixed'], 'current_candidate': value,
        'K': best['SKR'], 'source_cache_key': best['source_cache_key'], 'bracket': json.dumps(bracket),
        'bracket_width': upper - lower if radius is not None else '', 'radius': radius if radius is not None else '',
        'parameter_tolerance': ao.PARAMETER_TOLERANCE, 'conditional_fixed_best_midpoint_levels': halvings,
        'conditional_required_loop_stages': halvings + 1 if halvings else '',
        'conditional_radius_after_four_levels': radius / 16 if radius else '',
        'neighbor_values_and_gaps': json.dumps([{'value': r[variable], 'K': r['SKR'], 'gap': float(best['SKR']) - float(r['SKR']), 'source_cache_key': r['source_cache_key']} for r in neighbors]),
        'missing_exact_points': json.dumps(search['source_missing']), 'range': json.dumps(search['range']),
        'termination_reason': search['refinement_status'], 'original_status': search['status'],
        'status_categories': ';'.join(issues), 'evaluated_points': search['evaluated'],
        'boundary_expansions': search['boundary_expansions'], 'refinement_stages': search['refinement_stages'],
        'coordinate_complete': ao.coordinate_search_complete(search), 'global_domain_closed': False}


def make_plots(runs, maxima, checkpoint, comparison):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'font.family': 'serif', 'font.size': 10, 'axes.labelsize': 11, 'legend.fontsize': 8})
    names = []
    local = [r for r in runs if r['L_km'] == REF]
    for name, field, label in (
        ('figure_A_skr_iterations', 'K_after_nu', 'Secret Key Rate (bits/use)'),
        ('figure_B_VA_iterations', 'optimized_V_A', 'Modulation Variance (SNU)'),
        ('figure_B_nu_iterations', 'optimized_nu', 'Raw MB Parameter')):
        fig, ax = plt.subplots(figsize=(6.5, 4.0))
        for i, run in enumerate(local):
            its = run['iterations']
            initial = {'K_after_nu': its[0]['K_before'], 'optimized_V_A': its[0]['V_A_before'], 'optimized_nu': its[0]['nu_before']}[field]
            ys = [initial] + [r[field] for r in its]
            ax.plot(range(len(ys)), ys, marker=('o', 's', '^', 'D', 'v')[i], linestyle=('-', '--', '-.', ':', '--')[i],
                    label=run['start_id'].replace('_', ' '), linewidth=1.2, markersize=4)
            if field == 'K_after_nu':
                ax.scatter([float(r['iteration']) + 0.5 for r in its], [r['K_after_VA'] for r in its], color=f'C{i}', s=12, marker='x')
        ax.set(xlabel='AO Iteration (0 = initialization)', ylabel=label, title='Recorded AO updates at 21.9393102292 km')
        if field == 'K_after_nu':
            ax.scatter([], [], marker='x', color='black', s=12, label='P1 (half-step)')
        ax.set_xticks(range(4)); ax.grid(alpha=.25); ax.legend(frameon=False)
        fig.text(.5, .015, 'Incomplete searches: stagnation is not convergence.', ha='center', fontsize=8)
        fig.tight_layout(rect=(0, .035, 1, 1)); ao.save_figure(OUT / name, fig); names.append(name)
    for distance, tag in ((REF, 'reference'), (22., '22km')):
        best = maxima[distance]
        for variable, fixed in (('V_A', best['nu_raw']), ('nu_raw', best['V_A'])):
            rows = sorted((r for r in checkpoint[str(distance)]['rows'] if float(r['nu_raw' if variable == 'V_A' else 'V_A']).hex() == float(fixed).hex()), key=lambda r: r[variable])
            io.write_csv(OUT / f'exact_slice_{tag}_{variable}.csv', rows)
            fig, ax = plt.subplots(figsize=(6.5, 4.0))
            ax.scatter([r[variable] for r in rows], [r['SKR'] for r in rows], marker='o', s=20, label='Exact evaluated points')
            ax.scatter([best[variable]], [best['SKR']], marker='*', s=90, color='C3', label='Catalog best')
            ax.set(xlabel='Modulation Variance (SNU)' if variable == 'V_A' else 'Raw MB Parameter', ylabel='Secret Key Rate (bits/use)',
                   title=f'{distance:g} km; fixed {"nu raw" if variable == "V_A" else "VA"} = {fixed:g}')
            if variable == 'V_A':
                ax.set_xlim(best[variable] - .11, best[variable] + .11)
                nearby = [r['SKR'] for r in rows if abs(r[variable] - best[variable]) < .11]
                span = max(nearby) - min(nearby)
                ax.set_ylim(min(nearby) - max(span*.15, 1e-8), max(nearby) + max(span*.15, 1e-8))
            elif len(rows) > 1:
                ax.set_xlim(best[variable] - .006, best[variable] + .006)
                nearby = [r['SKR'] for r in rows if abs(r[variable] - best[variable]) < .006]
                span = max(nearby) - min(nearby)
                ax.set_ylim(min(nearby) - span*.15, max(nearby) + span*.15)
            else:
                fig.text(.5, .015, 'One measured point only; both outer directions unresolved.', ha='center', fontsize=8)
            ax.ticklabel_format(axis='y', style='plain', useOffset=False)
            ax.grid(alpha=.25); ax.legend(frameon=False); fig.tight_layout(rect=(0, .035, 1, 1))
            name = f'figure_C_{tag}_{variable}'; ao.save_figure(OUT / name, fig); names.append(name)
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    for scheme, marker, style in ((sweep.UNIFORM_SCHEME, 'o', '-'), (sweep.FIXED_MB_SCHEME, 's', '--'),
                                  ('AO MB: finite-catalog best', '^', '-.')):
        rows = [r for r in comparison if r['scheme'] == scheme and float(r['K']) > 0]
        ax.plot([r['L_km'] for r in rows], [r['K'] for r in rows], marker=marker, linestyle=style, markersize=4, label=scheme)
    ax.set_yscale('log', base=10)
    ax.set(xlim=(20, 40), title='SKR versus Link Distance', xlabel='Link Distance (km)', ylabel='Secret Key Rate (bits/use)')
    ax.grid(alpha=.25, which='both'); ax.legend(frameon=False)
    fig.text(.5, .015, 'Display: K > 0 only. Signed values retained in CSV; AO not certified global.', ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .035, 1, 1)); ao.save_figure(OUT / 'skr_vs_distance_positive_only', fig)
    names.append('skr_vs_distance_positive_only')
    return [str((OUT / (n + ext)).relative_to(ROOT)) for n in names for ext in ('.png', '.pdf')]


def main():
    if (OUT / 'ao_validation_report.json').exists():
        raise SystemExit('Completed audit exists: previous artifacts must not be overwritten')
    started, cpu = time.monotonic(), time.process_time()
    import torch
    torch.set_num_threads(1)
    OUT.mkdir(exist_ok=True)
    config = source.unconstrained_config()
    assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS, ao.MAX_REFINEMENT_STAGES, ao.MAX_BOUNDARY_EXPANSIONS) == (1e-8, 1e-6, 6, 4, 3)
    results = ROOT / 'results'
    input_dirs = [BASE, baseline.BASE, results/'theta10_D55_mb_exact_targeted_expansion/resumed_sleep_safe_run',
        results/'theta10_D55_alt_opt', results/'theta10_D55_alt_opt_distance_sweep',
        results/'theta10_D55_alt_opt_26distance_strict_rerun', results/'theta10_D55_alt_opt_convergence_validation',
        results/'theta10_D55_alt_opt_closure_continuation', results/'theta10_D55_alt_opt_closure_diagnostic',
        results/'theta10_D55_alt_opt_catalog_certification', sweep.PREVIOUS_CSV.parent,
        results/'theta10_D55_mb_exact_targeted_expansion/batch_3_preparation', results/'exact_mb_test2a',
        results/'joint_mb_va_global', results/'redesigned_baseline_global_mb_va']
    files = [p for directory in input_dirs + [ROOT/'src', ROOT/'configs', ROOT/'scripts', ROOT/'tests']
             for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT/'docs'/n for n in ('FINAL_MODEL_SPEC.md', 'SECURITY_SCOPE_FREEZE.md', 'NUMERICAL_CONVERGENCE_PREREGISTRATION.md')]
    protected = read(BASE/'protected_input_manifest.json')
    for name, digest in protected.items():
        assert io.digest(ROOT/name) == digest, name
    protected.update(io.raw_snapshot(files))
    io.save_json(OUT/'protected_input_manifest.json', protected)
    diff = subprocess.run(['git', 'diff'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    (OUT/'preexisting_worktree.diff').write_text(diff.stdout, encoding='utf-8')
    checkpoint = read(BASE/'objective_checkpoint.json')
    runs = read(BASE/'cache_only_runs.json')
    searches = read(BASE/'cache_only_searches.json')
    records = {float(r['L_km']): r for r in io.read_csv(BASE/'alt_opt_validation.csv')}
    maxima, verified = {}, []
    with ExitStack() as guard:
        for obj, method in ((ao.ExactMBEvaluator, 'source_moments'), (gram_moments, '_fallback'),
                            (ao, 'evaluate_candidate'), (sweep, 'make_channel'), (ao, 'adaptive_maximize_1d'), (sweep, 'run_single_distance_ao')):
            guard.enter_context(patch.object(obj, method, forbidden))
        payloads = source.load_source_payloads(config, baseline.DIRS)
        bank = {pair(float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])): p for p in payloads.values()}
        mb = {k: p for k, p in bank.items() if float.fromhex(k[0]) > 0}
        assert len(mb) == 146 and len(bank) == 175
        io.write_csv(OUT/'verified_source_catalog.csv', [{'nu_raw':float.fromhex(k[0]), 'V_A':float.fromhex(k[1]),
            'nu_raw_hex':k[0], 'V_A_hex':k[1], 'source_cache_key':p['cache_key'], 'ensemble_hash':p['ensemble_hash'],
            'C':p['C'], 'w':p['w'], 'support_size':p['support_size'], 'route':p['source_moment_route'],
            'source_path':p['_path'], 'provenance_status':p['_provenance']['status'],
            'candidate_specific_AP_error_bound':'NOT_RETAINED'} for k,p in mb.items()])
        repeats=io.read_csv(BASE/'new_source_objective_reproducibility.csv')
        assert len(repeats)==6 and all(float(r['delta_'+k])==0 for r in repeats for k in ('I_AB','beta_I_AB','chi_BE','SKR'))
        io.save_json(OUT/'retained_repeatability_review.json', {'artifact':str((BASE/'new_source_objective_reproducibility.csv').relative_to(ROOT)),
            'rows':repeats,'scope':'HISTORICAL_MEASURED_REPEATS_REVIEWED_NOT_RERUN','total_K_error_bound':'NOT_ESTABLISHED'})
        cert=results/'theta10_D55_alt_opt_catalog_certification'
        cert_starts=io.read_csv(cert/'all_multistart_iterations.csv')
        assert len(cert_starts)==129
        io.save_json(OUT/'historical_catalog_certificate_review.json', {'identity':read(cert/'catalog_identity.json'),
            'report':read(cert/'final_report.json'),'runtime':read(cert/'runtime_settings.json'),
            'start_summary_rows':len(cert_starts),'recorded_iteration_total':sum(int(r['AO_iterations']) for r in cert_starts),
            'scope':'HISTORICAL_FINITE_CERTIFICATE_NOT_SUBSTITUTED_FOR_CURRENT146'})
        for distance in sweep.DISTANCES_KM:
            stored = checkpoint[str(distance)]
            obj = ao.ExactObjective(config, stored['identity']['identity']['channel'], OUT,
                allow_new_source=False, source_cache_dirs=baseline.DIRS)
            assert obj.restore_objective_rows(stored['rows'], stored['identity']) == 146
            assert {(float(r['nu_raw']).hex(), float(r['V_A']).hex()) for r in obj.rows.values()} == set(mb)
            ranked = sorted(obj.rows.values(), key=lambda r: float(r['SKR']), reverse=True)
            best, second = ranked[:2]; maxima[distance] = best
            assert float(records[distance]['K']) == best['SKR'] and records[distance]['matches_catalog_maximum'] == 'True'
            verified.append({'L_km': distance, 'nu_raw': best['nu_raw'], 'V_A': best['V_A'],
                'I_AB': best['I_AB'], 'beta_I_AB': best['beta_I_AB'], 'chi_BE': best['chi_BE'], 'K': best['SKR'],
                'AO_validation_status': records[distance]['status'], 'claim': 'FINITE_CATALOG_MAXIMUM_ONLY',
                'source_cache_key': best['source_cache_key'], 'catalog_count': 146, 'top_two_gap': best['SKR']-second['SKR'],
                'objective_identity_sha256': obj.context_hash, 'continuous_converged': False, 'global_optimum_certified': False})
            assert obj.requested_calls == obj.unique_exact_evaluations == obj.cache_hits == 0
        identity_builder = obj.evaluator
        extra_cache = []
        for path in results.rglob('exact_source_cache/*.json'):
            try:
                p = read(path)
                verification = verify_source_payload(p, source_settings(config))
                extra_cache.append({'path': str(path.relative_to(ROOT)), 'status': verification['status'],
                    'nu_raw_hex': p['nu_mb_raw_hex'], 'V_A_hex': p['V_A_hex'], 'source_cache_key': p['cache_key']})
            except (ValueError, KeyError) as error:
                extra_cache.append({'path': str(path.relative_to(ROOT)), 'status': 'REJECTED_INCOMPATIBLE_OR_INCOMPLETE', 'reason': str(error)})
        io.write_csv(OUT/'other_cache_compatibility.csv', extra_cache)
        aligned, finals = align_searches(runs, searches)
        assert len(runs) == 129 and sum(len(r['iterations']) for r in runs) == 283 and len(aligned) == 618
        # Historical records are exported separately, never used to replace the146-objective matrix.
        historical_files = [(results/d/f) for d,f in (
            ('theta10_D55_alt_opt','ao_iterations.csv'), ('theta10_D55_alt_opt_distance_sweep','ao_iterations.csv'),
            ('theta10_D55_alt_opt_26distance_strict_rerun','ao_iterations.csv'),
            ('theta10_D55_alt_opt_convergence_validation','ao_iteration_history.csv'),
            ('theta10_D55_alt_opt_closure_continuation','ao_iteration_history.csv'))]
        history, historical_summary = [], []
        for path in historical_files:
            groups = defaultdict(list)
            for r in io.read_csv(path):
                row = enrich_iteration(r, path, bank, 'HISTORICAL_RECORD_NOT_CURRENT_146_CATALOG')
                history.append(row); groups[(row['L_km'], row['start_id'], r.get('batch',''), r.get('execution',''))].append(row)
            historical_summary.append({'artifact': str(path.relative_to(ROOT)), 'recorded_iterations': sum(len(v) for v in groups.values()),
                'recorded_start_trajectories': len(groups), 'distances': sorted({k[0] for k in groups}),
                'scope': 'Combined closure history uses batch/execution keys; child snapshots are not double counted.'})
        json_histories = [results/'theta10_D55_alt_opt_closure_diagnostic/cache_only_runs.json',
            results/'theta10_D55_mb_exact_targeted_expansion/resumed_sleep_safe_run/cache_only_runs.json',
            baseline.BASE/'cache_only_runs.json', BASE/'cache_only_runs.json']
        for path in json_histories:
            past = read(path)
            for run in past:
                for it in run['iterations']:
                    row = enrich_iteration({**it, 'distance_km': run['L_km']}, path, bank,
                        'CURRENT_146_CATALOG' if path.parent == BASE else 'HISTORICAL_RECORD_NOT_CURRENT_146_CATALOG')
                    row['run_terminal_status'] = run['status']; row['run_objective_calls'] = run.get('requested_evaluations','NOT_RECORDED')
                    history.append(row)
            historical_summary.append({'artifact': str(path.relative_to(ROOT)), 'recorded_iterations': sum(len(r['iterations']) for r in past),
                'recorded_start_trajectories': len(past), 'distances': sorted({r['L_km'] for r in past})})
        io.write_csv(OUT/'ao_multistart_history.csv', history)
        for distance, name in ((REF, 'reference'), (22., '22km')):
            io.write_csv(OUT/f'ao_iteration_trace_{name}.csv', [r for r in history if r['L_km'] == distance])
        io.save_json(OUT/'historical_execution_inventory.json', historical_summary)
        current_terminal = [{'L_km': r['L_km'], 'start_id': r['start_id'], 'initial_nu': r['start_nu'], 'initial_V_A': r['start_V_A'],
            'nu_raw': r['final']['nu_raw'], 'V_A': r['final']['V_A'], 'K': r['final']['SKR'], 'iterations': len(r['iterations']),
            'status': r['status'], 'matches_catalog': r['final']['SKR'] == maxima[r['L_km']]['SKR'],
            'recorded_run_objective_calls': r['requested_evaluations'], 'recorded_run_cache_hits': r['cache_hits'],
            'recorded_run_fresh_evaluations': r['exact_evaluations']} for r in runs]
        io.write_csv(OUT/'multistart_terminal_comparison.csv', current_terminal)
        diagnostics = [diagnostic(s, checkpoint[str(d)]['rows']) for d, checks in finals.items() for s in checks]
        for r in diagnostics:
            selected = max((x for x in runs if x['L_km'] == r['L_km']), key=lambda x: x['final']['SKR'])
            if abs(selected['iterations'][-1]['delta_K']) <= ao.K_TOLERANCE:
                r['status_categories'] += ';OBJECTIVE_STAGNATED_ONLY'
        io.write_csv(OUT/'coordinate_search_diagnostics.csv', diagnostics)
        io.save_json(OUT/'aligned_search_history.json', aligned)
        attempts = []
        for directory in (results/'theta10_D55_alt_opt_closure_continuation',
            results/'theta10_D55_mb_exact_targeted_expansion/probe_1_authorized_3h',
            results/'theta10_D55_mb_exact_targeted_expansion/resumed_sleep_safe_run', baseline.BASE, BASE):
            path = directory/'source_generation_ledger.json'
            if path.exists():
                for a in read(path).get('attempts', []):
                    if 'nu_raw' in a and 'V_A' in a:
                        attempts.append({**{k:a.get(k) for k in ('nu_raw','V_A','status','wall_seconds','cpu_seconds','timeout_seconds','cache_key')},
                                         'artifact': str(path.relative_to(ROOT))})
        missing = defaultdict(list)
        for s in aligned:
            for event in s['source_missing']:
                nu, va = (s['fixed'], event['value']) if s['variable'] == 'V_A' else (event['value'], s['fixed'])
                missing[pair(nu,va)].append({'L_km':s['L_km'], 'coordinate':s['variable'], 'role':s['role'],
                    'start_id':s['start_id'], 'iteration':s['iteration'], 'search_index':s['search_index'],
                    'inside_bracket': all(x is not None for x in s['bracket']) and s['bracket'][0] < event['value'] < s['bracket'][1],
                    'request_kind': 'PAIRED_MIDPOINT' if s['refinement_status']=='SOURCE_MISSING_REFINEMENT' else 'OUTER_BOUNDARY',
                    'value':event['value']})
        assert len(missing) == 55
        assert set(missing) == {pair(r['nu_raw'],r['V_A']) for r in io.read_csv(BASE/'remaining_missing_exact_pairs.csv')}
        priorities = []
        for (nh,vh), deps in missing.items():
            nu,va=float.fromhex(nh),float.fromhex(vh)
            ident=identity_builder._source_identity(source.make_ensemble(config,'MB',nu,va),nu,va)
            priority = 'A' if any(d['L_km']==REF and d['role']=='SELECTED_FINAL' for d in deps) else (
                'B' if any(d['L_km']==22. and d['role']=='SELECTED_FINAL' for d in deps) else (
                'C' if len({d['L_km'] for d in deps})>1 else 'D' if any(d['inside_bracket'] for d in deps) else 'E'))
            prior=[a for a in attempts if pair(a['nu_raw'],a['V_A'])==(nh,vh)]
            available=[c for c in extra_cache if c['status']=='VERIFIED' and (c['nu_raw_hex'],c['V_A_hex'])==(nh,vh)]
            assert not available, 'Compatible missing source discovered: requires explicit catalog reconciliation'
            priorities.append({'nu_raw':nu,'V_A':va,'nu_raw_hex':nh,'V_A_hex':vh,'source_cache_key':source.json_hash(ident),
                'ensemble_hash':ident['ensemble_hash'],'priority':priority, 'affected_distances':json.dumps(sorted({d['L_km'] for d in deps})),
                'affected_coordinates':';'.join(sorted({d['coordinate'] for d in deps})), 'request_count':len(deps),
                'dependencies':json.dumps(deps),'inside_any_bracket':any(d['inside_bracket'] for d in deps),
                'can_advance_one_step':True,'can_certify_search_alone':False,'available_other_compatible_cache':False,
                'previous_attempts':json.dumps(prior),'runtime_risk':'PRIOR_TIMEOUT_NO_AUTOMATIC_RETRY' if any(a['status']=='TIMEOUT' for a in prior)
                    else 'PRIOR_AC_ABORT_NO_AUTOMATIC_RETRY' if prior else 'UNMEASURED_MAY_EXCEED_60_MIN',
                'unknown_K':'NOT_EVALUATED','diagnostic_purpose':'Close an actual selected search dependency' if priority in 'AB' else 'Challenge or refine recorded nonselected trajectories; no promised gain'})
        priorities.sort(key=lambda r:(r['priority'],r['runtime_risk'].startswith('PRIOR_TIMEOUT'),-r['request_count'],r['nu_raw'],r['V_A']))
        io.write_csv(OUT/'missing_source_priority.csv',[{'rank':i,**r} for i,r in enumerate(priorities,1)])
        io.write_csv(OUT/'optimized_skr_26_distances.csv',verified)
        comparison=[]
        baseline_report=read(sweep.PREVIOUS_CSV.parent/'run_report.json')
        assert baseline_report['configuration']['mi']=='deterministic_heterodyne_product_GH8'
        for r in io.read_csv(sweep.PREVIOUS_CSV):
            if r['scheme'] not in (sweep.UNIFORM_SCHEME,sweep.FIXED_MB_SCHEME):
                continue
            d=float(r['L_km']);n=0. if r['family']=='Uniform' else float(r['nu_raw']);v=float(r['V_A'])
            p=bank[pair(n,v)]
            assert r['source_cache_key']==p['cache_key'] and r['ensemble_hash']==p['ensemble_hash']
            assert r['channel_hash']==maxima[d]['channel_hash'] and float(r['T_eff'])==float(maxima[d]['T_eff'])
            assert r['security_evaluator']=='current_exact_direct_Z_minus' and float(r['w0_m'])==ao.W0_M and float(r['D_r_m'])==.55
            comparison.append({**r,'L_km':d,'K':float(r['SKR']),'provenance_scope':'STORED_COMPATIBLE_HISTORICAL_METRICS_NOT_RERUN'})
        comparison += [{'scheme':'AO MB: finite-catalog best',**r} for r in verified]
        assert len(comparison)==78
        io.write_csv(OUT/'three_scheme_comparison.csv',comparison)
        figures=make_plots(runs,maxima,checkpoint,comparison)
    emit_documents(verified,diagnostics,priorities,historical_summary,current_terminal,baseline_report)
    checks=[]
    patterns=('test_ao_numerical_optimum_audit.py','test_alt_opt_provenance_and_stopping.py',
        'test_windows_sleep_safe_supervision.py','test_mb_sleep_safe_expansion.py','test_mb_batch2.py',
        'test_mb_batch3_preparation.py','test_mb_batch3.py','test_mb_batch3_resume.py')
    for pattern in patterns:
        done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        checks.append({'pattern':pattern,'returncode':done.returncode,'output':done.stdout+done.stderr})
    done=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest',
        'tests.test_exact_mb_test2a.DeterministicMBMITests.test_deterministic_mi_repeats_and_full_matches_product','-v'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    checks.append({'pattern':'fixed_GH8_MI_only','returncode':done.returncode,'output':done.stdout+done.stderr})
    io.save_json(OUT/'regression_tests.json',checks)
    assert all(c['returncode']==0 for c in checks), 'See regression_tests.json'
    for name,digest in protected.items():
        assert io.digest(ROOT/name)==digest,name
    after={name:io.digest(ROOT/name) for name in protected}
    io.save_json(OUT/'input_manifest_after.json',after)
    diffcheck=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    assert diffcheck.returncode==0,diffcheck.stdout+diffcheck.stderr
    report={'status':'CURRENTLY_VERIFIED_PASS_FOR_CACHE_ONLY_AUDIT', 'phase':'PHASE1_COMPLETE_STOP_BEFORE_NEW_AP',
        'compatible_MB_count':146,'objective_rows_verified':3796,'AO_matches_catalog':26,'distances':26,
        'starts':129,'outer_iterations':283,'coordinate_invocations':618,'coordinate_status_counts':dict(Counter(s['status'] for s in searches)),
        'closed_final_directions':sum(r['coordinate_complete'] for r in diagnostics),'unique_missing_pairs':55,
        'all_search_indexing_and_history_alignment_verified':True,'current_monotonicity_violations':sum(not r[k] for r in history if r['history_scope']=='CURRENT_146_CATALOG' for k in ('monotonicity_P1','monotonicity_P2')),
        'multistart_catalog_agreement':{str(d):sum(r['matches_catalog'] for r in current_terminal if r['L_km']==d) for d in (REF,22.)},
        'new_AP_calls':0,'new_channel_calls':0,'new_objective_calls':0,'new_optimization_calls':0,
        'numerical_accuracy':'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED','total_objective_error_bound':'NOT_ESTABLISHED',
        'continuous_converged':False,'global_optimum_certified':False,'nu_zero_implementation_gap':True,
        'uniform_and_fixed_data':'COMPATIBLE_STORED_METRICS_NO_RERUN', 'fixed_MB_actual_VA':baseline_report['fixed_mb']['V_A_exact_source_row'],
        'distance_plot':{'yscale':'log','base':10,'rule':'K>0_ONLY_DISPLAY_SIGNED_CSV_RETAINED',
            'last_positive_distance_by_scheme':{scheme:max(float(r['L_km']) for r in comparison if r['scheme']==scheme and float(r['K'])>0)
                for scheme in (sweep.UNIFORM_SCHEME,sweep.FIXED_MB_SCHEME,'AO MB: finite-catalog best')}},
        'source_cache_scan_files':len(extra_cache),'other_compatible_missing_sources':0,
        'protected_files_unchanged':len(protected),'tests':'CURRENTLY_VERIFIED_PASS','git_diff_check':'CURRENTLY_VERIFIED_PASS',
        'frozen_spec_sha256':io.digest(ROOT/'docs/FINAL_MODEL_SPEC.md'),'historical_spec_hash_discrepancy':'PREEXISTING_UNCHANGED',
        'lifecycle':'NOT_READY_FOR_PUBLICATION_SCALE_RUNS','figures':figures,'wall_seconds':time.monotonic()-started,'controller_CPU_seconds':time.process_time()-cpu,
        'CPU_scope':'Current process only; regression child CPU not measured', 'historical_execution_inventory':historical_summary}
    io.save_json(OUT/'ao_validation_report.json',report)
    print(json.dumps(report,indent=2))


def emit_documents(verified, diagnostics, priorities, inventory, terminals, old_report):
    def write(name, text):
        (OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
    write('ao_implementation_audit.md', r'''
# Actual AO implementation audit

Scope: Phase1 saved-record audit only; no AP, channel, MI/Holevo or optimizer rerun.
Authoritative implementation: scripts/run_theta10_D55_alt_opt.py (ExactObjective,
adaptive_maximize_1d, coordinate_search_complete, stopping_status) and
run_theta10_D55_alt_opt_distance_sweep.py (starting_va, run_single_distance_ao).
Batch3 evaluate() supplies genuine records and selected-final postchecks.

P1 fixes nu^(r-1) and searches VA; P2 fixes the NEW VA^(r) and searches nu.
The following P1 fixes the NEW nu^(r). All618 search records were aligned with
all283 real iterations and52 final postchecks, validating fixed binary64 values,
returned K, status and entire candidate-event histories. No final-copy trajectory.

The mathematical argmax over a continuous domain is a TARGET, not the returned
result: each inner call returns the maximum of its valid exact-tested candidates.
Implementation domain is nu_raw>0,VA>0; the requested nu>=0 includes Uniform at
nu=0, which register_catalog and ExactObjective explicitly exclude. No silent
domain change. A stored Uniform comparison is not an AO nu=0 boundary closure.

Starts are nu=.1,.15,.3,.8, plus previous-distance selected (nu,VA) after the
first distance. Initial VA is the smallest available exact VA on that nu slice,
unless the warm VA exists with exactly the same binary64 key.129 starts total.
The original four-start reference experiment is retained separately; later
records have five reference starts, not four. See historical_execution_inventory.

Inner search evaluates every existing exact slice point, not a preset dense box.
An endpoint maximum requests half the smallest value or twice the largest,
up to3 expansions; missing source leaves BOUNDARY_NOT_CLOSED. A singleton does
not become closed after one lower outer point: the other side is untested.
An interior best uses nearest measured lower/upper neighbors. If radius>1e-6,
both binary64 arithmetic midpoints are requested. Paired attempts consume one
refinement stage, even if missing, then stop immediately on missing data.
Four stages maximum; radius is checked at the next stage ENTRY. At the cap,
successful midpoint attempts without an entry tolerance check return failure.
None of the618 current calls reached the refinement cap: missing data/open
boundary are the active blockers. No monotonicity in either parameter assumed.

Objective caching binds current scientific code, config, exact channel context,
GH8, beta=.95, epsilon=.0186, ensemble/source keys and float.hex() coordinates.
Sources retain historical raw keys; only proven LF/CRLF aliases are accepted.
allow_new_source=False fails closed; no interpolation, abs(K), clipping or fitting.
Audit guards forbid source_moments, underlying AP fallback, fresh objective,
channel generation and optimizer calls. Current checkpoint rows only are restored.

Outer stopping uses |Delta K|<=1e-8, BOTH coordinate searches numerically closed,
no earlier unresolved search, and no current numerical/monotonic warning.
Small Delta K with incomplete inner search is STAGNATED_IN_EXACT_CATALOG or
UNRESOLVED_BOUNDARY, never CONVERGED_NUMERICALLY. Outer cap6 remains unchanged.
Sampled interior bracketing is LOCAL evidence, not closure of all remote extrema
of an unbounded non-monotone objective. Even local closure would not prove global.

Actual per-coordinate fresh evaluation/cache-hit counts are recorded in each
iteration and exported unchanged. Requested objective-call counters are only
stored per RUN/distance, not per coordinate: these fields are NOT_RECORDED.
Recorded event counts are reported separately, not relabeled as objective calls.
Historical source keys are attributed via verified current pair lookup and
explicitly are not asserted to be original historical raw keys. Current146 rows
are independently validated against the original source and objective identities.

All settings/scientific files remain unchanged. Frozen-spec hash differs from
AGENTS historical expected hash (existing author re-freeze); it is neither repaired
nor certification authority. Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
''')
    selected=[r for r in diagnostics if r['L_km'] in (REF,22.)]
    table='\n'.join(f"|{r['L_km']}|{r['coordinate']}|{r['fixed']}|{r['current_candidate']}|{r['bracket']}|{r['radius']}|{r['status_categories']}|" for r in selected)
    plan=['# Targeted exact continuation plan','', 'Phase1 complete; Phase2 NOT AUTHORIZED. Do not request a new budget in this task.',
        'Do not reuse expired Batch3 budgets, execute all55 sources, predict K, or restart a rectangular grid.', '',
        '## Primary and secondary coordinate blockers','', '|L km|coordinate|fixed|candidate|bracket|radius|issues|', '|---|---|---|---|---|---|---|',table,'',
        '## Smallest useful sets (one original paired step, NOT full convergence)', '',
        'Reference P1: (.165,5.49375) and (.165,5.5125). Both are needed to finish its first paired midpoint attempt.',
        'Reference P2: (.16375,5.5) and (.16531250000000003,5.5). The lower source previously timed out at3600s.',
        'Thus4 source pairs advance BOTH selected reference coordinates by one step; no smaller set finishes both paired attempts.',
        'A one-source pilot (.16531250000000003,5.5) is informative shaping evidence, but cannot close P2 without its lower partner.',
        'At22km P1: (.165,5.4625) and (.165,5.481249999999999); preserve the latter binary64, not5.48125.',
        'The first was AC-aborted; never automatically retry. It needs explicit fresh authority and safe power.',
        'At22km P2 the actual first request is (.0825,5.475), an OUTER half-value, not a local midpoint.',
        'The opposite outer (.33,5.475) is NOT yet requested and NOT in the55 inventory. Whether/when it is requested depends on',
        'measured lower-outer ordering and the unchanged singleton/endpoint logic. Do not invent a bracket or nu midpoint here.',
        'For progress on all four selected calls the initial actual dependency set contains7 pairs (4 reference +3 at22).',
        'No finite minimum number guarantees final parameter closure or numerical accuracy; later requests depend on exact results.', '',
        '## Refinement-limit implications', '',
        'If the incumbent stays fixed and both sides halve, reference VA radius=.025 requires15 midpoint levels,',
        'nu radius=.0025 requires12; the entry-check semantics require16/13 allowed loop stages, respectively.',
        '22km VA radius=.025 likewise requires15 levels/16 entry stages. P2 has no measurable radius.',
        'These are conditional geometric calculations only, not simulated outcomes, guaranteed iterations, or error estimates.',
        'Four steps cannot close those current radii within a single call. Exact probes can make the next invocation start',
        'from a narrower catalog bracket; change no settings now. A future larger cap needs separate prospective approval.',
        'Earlier unresolved-search memory also prevents an individual resumed trajectory from being called converged',
        'merely because its latest coordinates later close. Reassess with the original multi-start driver and report actual status.', '',
        '## Runtime and execution gates', '',
        'Existing successful sources cost roughly36-53 minutes; cost for unmeasured points is unknown and can exceed60min.',
        'The prior lower reference nu source timed out; AC abort is not a numerical failure or timeout.',
        'A future explicitly authorized campaign must be sequential with fresh total/per-source deadlines, stableAC,',
        'temporary Sleep prevention, validated Windows Job supervision, provenance checkpoints and full tree cleanup.',
        'Every successful source then gets all26 original-evaluator objectives; adaptive planning uses only measured results.',
        'Restoration of the original execution state is mandatory; no unattended/retried worker is authorized here.', '',
        '## Per-distance continuation dependencies', '',
        'Other24 distances are deferred until stronger reference/22 local and accuracy evidence exists.',
        'For each distance below, finish the listed actual P1/P2 dependencies, then recheck both searches, all starts,',
        'outerDeltaK, earlier unresolved flags and numerical accuracy. Currentcache alone is insufficient at every distance.',
        'Source availability may satisfy one paired stage or permit a boundary request; no single probe promises stopping.',
        '|L km|nu|VA|K bits/use|P1 missing values|P2 missing values|gate|', '|---|---|---|---|---|---|---|']
    for v in verified:
        d=v['L_km'];local=[r for r in diagnostics if r['L_km']==d]
        plan.append(f"|{d}|{v['nu_raw']}|{v['V_A']}|{v['K']}|{[(e['value']) for e in json.loads(local[0]['missing_exact_points'])]} (fixed nu={local[0]['fixed']})|{[e['value'] for e in json.loads(local[1]['missing_exact_points'])]} (fixed VA={local[1]['fixed']})|{'PRIMARY' if d==REF else 'SECONDARY' if d==22 else 'DEFERRED'}|")
    write('targeted_exact_continuation_plan.md','\n'.join(plan))
    write('numerical_accuracy_assessment.md', r'''
# Numerical accuracy assessment

ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED. No new evaluation or quadrature/precision sweep.

146 source identities/full support256 are verified against original construction,
settings and code.1050/1250/1450 is unchanged; full_support_c4_worker.py accepts
final1250/1450 resolved rank256 and per-C/w agreement1e-7+1e-6*max(abs(reference)).
Production caches retain binary64 C,w but discard fallback per-precision rows.
The new5.4875 receipt retains the rejected complex128 gate, not the AP observable
residuals. A small rejected-fast-route residual is not a full-support AP bound.
No current candidate-specific AP error enclosure can be recovered from these files.

Batch3 new_source_objective_reproducibility.csv records6 original GH8/direct-Z
metric repeats with bit-exact differences0. Earlier145 preparation records24
repeats. These are historical measured repeatability, not fresh results here,
and not independent arithmetic or truncation-error validation. File hashes protected.

MI is deterministic discrete-input heterodyne product GH8, not Gaussian-input MI.
The existing fixed-GH8 full/product test is rerun without changing quadrature.
exact_mb_test2a/gh_convergence.json and joint_mb_va_global/gh_convergence.csv
cover different ensembles/channel fixtures. The redesigned baseline continuation
reports top10 GH8->64 difference1.498e-10 under w0=.10, not the current .098676...
reference/22 ridge. None is a validated quadrature bound for every current best.

Direct-Z Holevo uses the same source/ensemble/excess noise and rejects wrong
mode/nonphysical inputs. Existing software tests validate conventions and guards;
they do not enclose errors in eigenvalues, square roots or entropy cancellation.
No independent high-precision whole-objective bound is retained at these winners.

At reference betaI=.602479799960547,chi=.5244988060866094, so K=.07798099387393764.
Neighbor gaps are7.834476867252249e-8(reference runner-up) and
1.733217454003011e-7(22km runner-up). Final subtraction input-ULPs are of order1e-16;
this scale does NOT bound source, quadrature, channel, covariance or entropy error.
epsilon_opt=1e-8,parameter_tolerance=1e-6 and physicality tolerances are different
quantities, not total-K accuracy bounds. Reproduced tiny gains cannot be called
error-resolved or physically significant. Current ordering is reproducible only.

Future reliable approximate numerical optimality needs candidate-specific retained
source convergence/residual records, compatible existing MI convergence evidence
or separately authorized diagnostics, stable physicality/Holevo checks, and an
explicit total-objective accuracy assessment relative to relevant gaps. Do not
silently change the evaluator or claim this proposed work is already done.
''')
    write('algorithm1_ao.tex', r'''
% Requires \usepackage{algorithm,algpseudocode,amsmath}.
% LaTeX-ready description of existing code; not a newly implemented optimizer.
\begin{algorithm}[t]
\caption{Exact-evaluation alternating search with explicit incomplete status}
\label{alg:exact-ao}
\begin{algorithmic}[1]
\Require Distance $L$, frozen channel/source/security settings, $\beta=0.95$,
verified source/objective caches, $\varepsilon_K=10^{-8}$,
$\varepsilon_p=10^{-6}$, outer cap $6$, inner cap $4$, expansion cap $3$.
\State $\mathcal S\gets\{0.1,0.15,0.3,0.8\}$ plus previous-distance selected warm pair if available.
\For{each initialization $s\in\mathcal S$}
  \State Set $\nu^{(0)}$ from $s$; choose the smallest available exact $V_A$ on its slice, or exact-matching warm $V_A$.
  \State Validate/evaluate the initial pair; on missing source or numerical failure, record incomplete/failed start and continue.
  \State $u\gets\mathrm{false}$; status $\gets$ outer iteration limit.
  \For{$r=1,\ldots,6$}
    \State $K_{\rm before}\gets K(L,\nu^{(r-1)},V_A^{(r-1)})$.
    \State $(V_A^{(r)},S_1)\gets\Call{InnerExactSearch}{V_A;\nu^{(r-1)}}$ \Comment{P1}
    \State If no valid best is returned, record failure and terminate this start.
    \State $(\nu^{(r)},S_2)\gets\Call{InnerExactSearch}{\nu;V_A^{(r)}}$ \Comment{P2 uses NEW $V_A$}
    \State If no valid best is returned, record failure and terminate this start.
    \State Record actual P1/P2 metrics, candidates, source dependencies, brackets, counters and statuses.
    \State $u\gets u\lor\neg(\Call{Complete}{S_1}\land\Call{Complete}{S_2})$.
    \State $\Delta K\gets K(L,\nu^{(r)},V_A^{(r)})-K_{\rm before}$.
    \If{nonfinite metrics, recorded numerical failure, or decrease beyond $\varepsilon_K$}
      \State status $\gets$ numerical failure; \textbf{break}.
    \ElsIf{$|\Delta K|\le\varepsilon_K$}
      \State status $\gets$ unresolved boundary if a current boundary is open;
      otherwise catalog stagnation if $u$ or either search is incomplete;
      otherwise numerical convergence. \textbf{break}.
    \EndIf
  \EndFor
\EndFor
\State Select the largest final $K$ among starts with a valid final pair.
\State Run both original coordinate postchecks at that pair; never retain a convergence label if either is incomplete or improves beyond tolerance.
\State Carry selected $(\nu,V_A)$ as the next distance's warm pair.
\Ensure Best observed multi-start final $(\widehat\nu,\widehat V_A,\widehat K)$, inner/outer status and unresolved dependencies.
\Function{InnerExactSearch}{$x;f$}
  \State Search $x>0$: evaluate all available exact slice candidates at fixed $f$ using compatible cache or unchanged evaluator.
  \State An endpoint winner requests half/double outside, up to3 expansions; missing sources or failure remain unresolved.
  \State For an interior winner, set nearest evaluated lower/upper neighbors $(a,b)$.
  \State At each of at most4 stages, first check $\max(x-a,b-x)\le\varepsilon_p$.
  \State Otherwise request both arithmetic midpoints $(a+x)/2,(x+b)/2$; count one stage; stop incomplete if either is missing.
  \State Return the largest valid exact-tested $K$ and actual status; cap exhaustion is not convergence.
\EndFunction
\Function{Complete}{$S$}
  \State \Return numerically closed local bracket, no source/numerical failure, and no unresolved boundary.
\EndFunction
\end{algorithmic}
\end{algorithm}

The ideal P1/P2 argmax equations are continuous-domain targets, not claims about
the returned exact-tested inner maximizers. The implementation uses $\nu>0$,
whereas the scientific target includes $\nu=0$; stored Uniform comparisons do
not close that boundary. Local bracket closure or multi-start agreement does
not certify a global optimum of a non-monotone unbounded objective. In the
present run, all selected coordinate searches remain incomplete, so outputs
are finite-catalog best candidates rather than certified $K^*(L)$.
''')
    terminal_table='\n'.join(f"|{r['L_km']}|{r['start_id']}|{r['iterations']}|{r['nu_raw']}|{r['V_A']}|{r['K']}|{r['status']}|" for r in terminals if r['L_km'] in (REF,22.))
    write('ao_validation_report.md', f'''
# AO numerical optimum validation — Phase1

Audit complete.146 compatible MB sources,3796 saved objective rows,26/26 selected
AO finite-catalog maxima. No new AP, source moments, channel, MI/Holevo or optimizer
evaluation. Old artifacts and scientific files are hash-protected. Numeric validity
and incomplete optimization are separate outcomes; no lifecycle promotion.

## Required conclusions

1. P1/P2 indexing is consistent: P1 fixes previousnu, P2 fixes the NEW VA. Domain
   difference: implementation excludesnu=0, unlike the mathematical target.
2. Each iteration runs the two original exact-tested slice searches, propagates
   their candidates and computes genuine DeltaK; no reconstructed final copies.
3. All283 iterations/129 starts genuinely alternate;618 recorded calls include52
   selected-final postchecks. Per-coordinate fresh/cache counters are available;
   requested-call counts are only recorded at run/distance level.
4. Both coordinates are blocked by missing source moments.312 calls have open
   boundaries,306 have bracketed missing sources.0 selected directions complete.
   None reaches the four-stage cap now, but that cap would be insufficient for
   one-call refinement of the present priority brackets. Total numerical accuracy
   also remains unresolved, independently of source coverage.
5. Reference (.165,5.5),K=.07798099387393764 is a verified finite-catalog maximum
   and best observed multi-start result. It is not a validated continuous local
   numerical optimum, a completed approximate coordinate optimum or global optimum.
6. Reference: both lower/upper VA midpoints and both nu midpoints are required.
   At22km(.165,5.475),K=.07661740491526092, P1 is bracketed but P2 is singleton:
   original lowerouternu=.0825 is missing and opposite side untested.
7.4 actual pairs are the minimum set to finish one paired step in BOTH reference
   calls;7 initial dependencies advance the two reference and two22km calls.
   This is not a promise of final convergence. See targeted plan and55-entry priority CSV.
8. Multi-start stability is partial, not universal:4/5 starts match the catalog
   winner at each priority distance;nu0=.8 returns(.4,3.0) with lowerK. Full table below.
9. Sources/provenance and deterministic original-evaluator repeatability support
   reported numbers. Retained source convergence/quadrature/entropy evidence does
   NOT bound whole-K error; tiny rank gaps remain error-unbounded.
10. A defensible Algorithm1 can already describe the ACTUAL incomplete procedure.
    A convergence discussion must say catalog stagnation, not convergence. TeX
    supplied with dependencies; compilation is NOT_RUN in this environment.
11. Before reliable optimizedSKRall26: validate both priority coordinate searches,
    candidate-specific numerical accuracy and multistart/boundary coverage; then
    repeat original procedure for the other24 with explicit status. Addressnu=0
    scope prospectively, never silently; finite tests alone cannot certify global.

## Actual priority multistart terminals

|L km|start|iterations|nu|VA|K bits/use|status|
|---|---|---|---|---|---|---|
{terminal_table}

## Manuscript and comparison caveats

Eight figure pairs (PNG300dpi/vectorPDF) use recorded histories and exact scatter
slices. FigureA uses initial/P2 values with P1 crosses; lines indicate update
sequence, not a fit. Both parameter plots use actual initialization and updates.
The22km nu slice contains only one measured point. Missing values never plotted.
Local slice CSVs include the full exact slice while viewports focus on the incumbent.

three_scheme_comparison.csv retains all78 signed SKRs. The distance figure follows
the established positive-only renderer: Uniform ends25km, both MB reach40km;
standard base10log, no abs/zero substitution/interpolated zero crossing/K=0line.
AO curve label says finite-catalog best, not certified global. Stored Uniform
selection is not newly optimized or certified in this task. Fixed MB uses actual
VA={old_report['fixed_mb']['V_A_exact_source_row']} (not exactly requested1.3833230303);
that historical discrepancy is preserved and disclosed, not silently repaired.

Historical records are exported by artifact/execution identity. Counts are in
historical_execution_inventory.json; old catalogs/status policies are not promoted
to current scientific evidence or combined into one fictitious trajectory.
The closure aggregate already includes its coordinate-batch snapshots, so they
are not counted twice. Historical certification all_multistart_iterations.csv is
a129-start SUMMARY, not an iteration trace; actual CSV/JSON histories are used.

Fresh phase2 scope/budget is required. This task stops beforeAP and does not ask
for a budget. Science/model/settings/thresholds/train/test access remain unchanged.
Frozen-spec historical-hash discrepancy is pre-existing; lifecycle remains
NOT_READY_FOR_PUBLICATION_SCALE_RUNS. Machine report records current verification,
protected hashes, test outputs and actual cache-only runtime.
''')


if __name__=='__main__':
    main()
