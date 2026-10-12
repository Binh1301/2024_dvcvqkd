"""Focused saved-data scientific export: no channel/source/security/AO rerun."""
from collections import Counter
from contextlib import ExitStack
import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao
from scripts import run_theta10_D55_alt_opt_distance_sweep as sweep
from scripts import run_theta10_D55_unconstrained_three_scheme as source
from scripts import audit_theta10_D55_ao_numerical_optimum as audit
from scripts.exact_cache_provenance import objective_identity, objective_compatible
from scripts.render_theta10_D55_three_scheme_log10 import positive_runs

OUT = ROOT / 'results/theta10_D55_ao_final_scientific_results'
BASE = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation/overnight_ao_run'
CURVES = ROOT / 'results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme/skr_vs_distance_three_scheme.csv'
PROTECTED = ROOT / 'results/theta10_D55_ao_numerical_optimum_validation/observer_v2_recovery/path_fixed_probe_A/protected_input_manifest.json'
REF = 21.9393102292
DIRS = tuple(ROOT / 'results' / p / 'exact_source_cache' for p in (
    'exact_mb_test2', 'theta10_D55_alt_opt_closure_continuation',
    'theta10_D55_mb_exact_targeted_expansion/resumed_sleep_safe_run',
    'theta10_D55_mb_exact_targeted_expansion/batch_2', 'theta10_D55_mb_exact_targeted_expansion/batch_3',
    'theta10_D55_ao_numerical_optimum_validation/phase_2A'))


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def pair(n, v):
    return float(n).hex(), float(v).hex()


def write_csv(name, data):
    fields = list(dict.fromkeys(k for r in data for k in r)) or ['status']
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields);writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in r.items()} for r in data)


def unchanged():
    manifest = read(PROTECTED)
    assert all(sweep.sha256(ROOT / name) == digest for name, digest in manifest.items())
    return len(manifest)


def analyze():
    """Verify stored ensemble/objective provenance, then rank actual values."""
    config = source.unconstrained_config()
    bank = source.load_source_payloads(config, DIRS)
    mb = {pair(float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])): p
          for p in bank.values() if float.fromhex(p['nu_mb_raw_hex']) > 0}
    assert len(mb) == 147
    checkpoint = read(BASE / 'objective_checkpoint.json')
    runs = read(BASE / 'cache_only_runs.json')
    searches = read(BASE / 'cache_only_searches.json')
    assert len(runs) == 129 and sum(len(r['iterations']) for r in runs) == 283
    aligned, finals = audit.align_searches(runs, searches)
    assert len(checkpoint) == 26
    best_rows = [];rankings = {};lookups = {};all_histories = [];terminals = []
    for distance in sweep.DISTANCES_KM:
        saved = checkpoint[str(distance)]
        channel = saved['identity']['identity']['channel']
        assert objective_compatible(saved['identity'], objective_identity(config, channel))
        assert channel['distance_km'] == distance and channel['AO'] == channel['phase_noise'] == 'OFF'
        assert channel['theta_div_full_rad'] == 1e-5 and channel['receiver_diameter_m'] == .55
        assert channel['w0_m'] == .0986760647169751
        index = {}
        for row in saved['rows']:
            p = mb[pair(row['nu_raw'], row['V_A'])]
            assert row['ensemble_hash'] == p['ensemble_hash'] and row['source_cache_key'] == p['cache_key']
            assert row['channel_hash'] == channel['channel_hash'] and row['status'] == 'PASS'
            assert row['security_evaluator'] == 'current_exact_direct_Z_minus'
            assert all(math.isfinite(float(row[k])) for k in ('I_AB', 'beta_I_AB', 'chi_BE', 'SKR'))
            assert abs(.95 * row['I_AB'] - row['beta_I_AB']) < 5e-15
            assert abs(row['beta_I_AB'] - row['chi_BE'] - row['SKR']) < 5e-15
            index[pair(row['nu_raw'], row['V_A'])] = row
        assert set(index) == set(mb)
        lookups[distance] = index
        ranked = sorted(index.values(), key=lambda r: r['SKR'], reverse=True)
        rankings[distance] = ranked;best = ranked[0]
        local = [r for r in runs if r['L_km'] == distance]
        selected = max((r for r in local if r['final']), key=lambda r: r['final']['SKR'])
        match = selected['final']['SKR'] == best['SKR'] and pair(selected['final']['nu_raw'], selected['final']['V_A']) == pair(best['nu_raw'], best['V_A'])
        complete = all(ao.coordinate_search_complete(s) for s in finals[distance])
        best_rows.append({'L_km': distance, 'best_nu_raw': best['nu_raw'], 'best_V_A': best['V_A'],
            'I_AB': best['I_AB'], 'beta_I_AB': best['beta_I_AB'], 'chi_BE': best['chi_BE'], 'best_SKR': best['SKR'],
            'AO_status': selected['status'], 'selected_start': selected['start_id'], 'AO_matches_catalog': match,
            'catalog_size': len(ranked), 'runner_up_nu': ranked[1]['nu_raw'], 'runner_up_V_A': ranked[1]['V_A'],
            'runner_up_K': ranked[1]['SKR'], 'top_two_gap': best['SKR'] - ranked[1]['SKR'],
            'coordinate_complete': complete, 'classification': 'FINITE_CATALOG_MAXIMUM;COORDINATE_SEARCH_INCOMPLETE;GLOBAL_OPTIMUM_NOT_CERTIFIED' if not complete else 'FINITE_CATALOG_MAXIMUM;GLOBAL_OPTIMUM_NOT_CERTIFIED',
            'source_cache_key': best['source_cache_key'], 'objective_identity_sha256': saved['identity']['sha256']})
        for r in local:
            assert len(r['trajectory']) == 1 + 2 * len(r['iterations'])
            for it in r['iterations']:
                for n, v, k in ((it['nu_before'], it['V_A_before'], it['K_before']),
                               (it['nu_before'], it['optimized_V_A'], it['K_after_VA']),
                               (it['optimized_nu'], it['optimized_V_A'], it['K_after_nu'])):
                    assert index[pair(n, v)]['SKR'] == k
                assert abs(it['delta_K'] - (it['K_after_nu'] - it['K_before'])) < 1e-16
                all_histories.append({'L_km': distance, 'start_id': r['start_id'],
                    'recorded_iteration_zero_based': it['iteration'], 'iteration': it['iteration'] + 1,
                    'nu_before': it['nu_before'], 'V_A_before': it['V_A_before'], 'K_before': it['K_before'],
                    'nu_after_P1': it['nu_before'], 'V_A_after_P1': it['optimized_V_A'], 'K_after_P1': it['K_after_VA'],
                    'nu': it['optimized_nu'], 'V_A': it['optimized_V_A'], 'K': it['K_after_nu'],
                    'Delta_K': it['delta_K'], 'P1_status': it['V_A_search_status'], 'P2_status': it['nu_search_status'],
                    'P1_bracket': it['V_A_bracket'], 'P2_bracket': it['nu_bracket'],
                    'termination_state': it['convergence_status'], 'run_terminal_state': r['status'],
                    'history_source': str((BASE / 'cache_only_runs.json').relative_to(ROOT))})
            terminal = r['final']
            terminals.append({'L_km': distance, 'start_id': r['start_id'], 'initial_nu': r['start_nu'],
                'initial_V_A': r['start_V_A'], 'terminal_nu': terminal['nu_raw'], 'terminal_V_A': terminal['V_A'],
                'terminal_K': terminal['SKR'], 'gap_to_catalog_best': best['SKR'] - terminal['SKR'],
                'status': r['status'], 'outer_iterations': len(r['iterations']),
                'matches_catalog': terminal['SKR'] == best['SKR']})
    comparison = []
    for raw in rows(CURVES):
        if raw['scheme'] == sweep.OPTIMIZED_MB_SCHEME:
            continue
        d = float(raw['distance_km']);p = bank[raw['ensemble_hash']]
        assert p['cache_key'] == raw['source_cache_key']
        assert raw['channel_hash'] == checkpoint[str(d)]['identity']['identity']['channel']['channel_hash']
        assert raw['security_evaluator'] == 'current_exact_direct_Z_minus'
        assert float(raw['theta_div_full_rad']) == 1e-5 and float(raw['D_r_m']) == .55
        assert abs(float(raw['beta_I_AB']) - float(raw['chi_BE']) - float(raw['K'])) < 5e-15
        comparison.append({'scheme': raw['scheme'], 'distance_km': d, 'nu_raw': raw['nu_raw'],
            'V_A': raw['V_A'], 'I_AB': raw['I_AB'], 'beta_I_AB': raw['beta_I_AB'], 'chi_BE': raw['chi_BE'],
            'K': float(raw['K']), 'source_cache_key': raw['source_cache_key']})
    comparison += [{'scheme': 'AO-optimized MB-shaped 256-QAM', 'distance_km': r['L_km'],
        'nu_raw': r['best_nu_raw'], 'V_A': r['best_V_A'], 'I_AB': r['I_AB'],
        'beta_I_AB': r['beta_I_AB'], 'chi_BE': r['chi_BE'], 'K': r['best_SKR'], 'source_cache_key': r['source_cache_key']} for r in best_rows]
    assert len(comparison) == 78
    fixed = [r for r in comparison if r['scheme'] == sweep.FIXED_MB_SCHEME]
    assert {pair(r['nu_raw'], r['V_A']) for r in fixed} == {pair(.2, 1.3833230302980657)}
    assert max(r['distance_km'] for r in comparison if r['scheme'] == sweep.UNIFORM_SCHEME and r['K'] > 0) == 25
    targeted = read(BASE / 'reference_targeted_coordinate_searches.json')
    assert [s['bracket'] for s in targeted] == [[5.4875, 5.5125], [.1625, .16562500000000002]]
    historical = read(ROOT / 'results/theta10_D55_alt_opt_catalog_certification/final_report.json')
    assert historical['available_MB_count'] == 139 and historical['new_AP_generations'] == 0
    return {'best': best_rows, 'rankings': rankings, 'runs': runs, 'history': all_histories,
            'terminals': terminals, 'comparison': comparison, 'checkpoint': checkpoint,
            'aligned': aligned, 'finals': finals, 'targeted': targeted, 'historical_certificate': historical}


def figure(path, fig):
    fig.savefig(OUT / (path + '.png'), dpi=400, bbox_inches='tight')
    fig.savefig(OUT / (path + '.pdf'), bbox_inches='tight')


def plots(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'font.family': 'serif', 'font.size': 9, 'axes.labelsize': 10,
        'legend.fontsize': 8, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    local = [r for r in data['runs'] if r['L_km'] == REF]
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    fig2, axes = plt.subplots(2, 1, figsize=(6.4, 6.0), sharex=True)
    markers = ('o', 's', '^', 'D', 'v');styles = ('-', '--', '-.', ':', '--')
    for i, run in enumerate(local):
        its = run['iterations'];first = its[0]
        x = [0];kk = [first['K_before']];va = [first['V_A_before']];nu = [first['nu_before']]
        for it in its:
            j = it['iteration'] + 1;x += [j - .5, j]
            kk += [it['K_after_VA'], it['K_after_nu']]
            va += [it['optimized_V_A'], it['optimized_V_A']]
            nu += [it['nu_before'], it['optimized_nu']]
        label = r'$\nu_0=' + str(run['start_nu']) + '$' if run['start_id'] != 'warm_previous_distance' else 'Previous-distance warm start'
        for a, y in ((ax, kk), (axes[0], va), (axes[1], nu)):
            a.plot(x, y, color=f'C{i}', linestyle=styles[i], linewidth=1.2, label=label)
            a.scatter(x[::2], y[::2], marker=markers[i], color=f'C{i}', s=23, zorder=3)
            a.scatter(x[1::2], y[1::2], marker='x', color=f'C{i}', s=22, zorder=3)
    ax.scatter([], [], marker='x', color='black', s=22, label='P1 half-step')
    ax.set(xlabel='AO iteration (0: initialization)', ylabel='Secret Key Rate (bits/use)', title='Recorded AO objective trajectory')
    ax.set_xticks(range(4));ax.grid(alpha=.22);ax.legend(frameon=False, ncol=2)
    fig.tight_layout();figure('ao_convergence', fig);plt.close(fig)
    axes[0].set(ylabel=r'$V_A$ (SNU)', title='Recorded evolution of modulation parameters')
    axes[1].set(xlabel='AO iteration (0: initialization)', ylabel=r'$\nu_{\rm MB}$ (raw)')
    axes[0].legend(frameon=False, ncol=2)
    for a in axes:a.set_xticks([0, .5, 1, 1.5, 2, 2.5, 3]);a.grid(alpha=.22)
    fig2.tight_layout();figure('ao_parameter_evolution', fig2);plt.close(fig2)
    for d, tag in ((REF, 'reference'), (22., '22km')):
        best = data['rankings'][d][0]
        for variable, fixed in (('V_A', best['nu_raw']), ('nu_raw', best['V_A'])):
            points = sorted((r for r in data['rankings'][d]
                if float(r['nu_raw' if variable == 'V_A' else 'V_A']).hex() == float(fixed).hex()), key=lambda r: r[variable])
            write_csv(f'coordinate_{tag}_{variable}.csv', points)
            f, a = plt.subplots(figsize=(6.4, 3.8))
            a.scatter([r[variable] for r in points], [r['SKR'] for r in points], s=25, label='Exact evaluated points')
            a.scatter([best[variable]], [best['SKR']], marker='*', s=105, color='C3', label='Finite-catalog best')
            a.set(xlabel=r'$V_A$ (SNU)' if variable == 'V_A' else r'$\nu_{\rm MB}$ (raw)',
                ylabel='Secret Key Rate (bits/use)', title=f'{d:g} km: fixed ' + ('raw MB parameter' if variable == 'V_A' else 'modulation variance') + f' = {fixed:g}')
            span = .08 if variable == 'V_A' else .005
            a.set_xlim(best[variable] - span, best[variable] + span)
            nearby = [r['SKR'] for r in points if abs(r[variable] - best[variable]) <= span]
            spread = max(max(nearby) - min(nearby), 1e-7)
            a.set_ylim(min(nearby) - .15 * spread, max(nearby) + .15 * spread)
            a.ticklabel_format(axis='y', style='plain', useOffset=False)
            a.grid(alpha=.22);a.legend(frameon=False)
            f.tight_layout();figure(f'coordinate_{tag}_{variable}', f);plt.close(f)
    f, a = plt.subplots(figsize=(6.4, 4.1))
    for i, scheme in enumerate((sweep.UNIFORM_SCHEME, sweep.FIXED_MB_SCHEME, 'AO-optimized MB-shaped 256-QAM')):
        local = sorted((r for r in data['comparison'] if r['scheme'] == scheme), key=lambda r: r['distance_km'])
        for j, segment in enumerate(positive_runs(local)):
            a.plot([x for x, _ in segment], [k for _, k in segment], marker=markers[i], linestyle=styles[i],
                color=f'C{i}', markersize=4, linewidth=1.3, label=scheme if j == 0 else '_nolegend_')
    a.set_yscale('log', base=10)
    a.set(xlim=(20, 40), xlabel='Link Distance (km)', ylabel='Secret Key Rate (bits/use)', title='SKR versus Link Distance')
    a.grid(which='both', alpha=.22);a.legend(frameon=False)
    f.tight_layout();figure('skr_vs_distance', f);plt.close(f)


def documents(data, validation):
    reference = data['rankings'][REF];best = reference[0]
    starts = [r for r in data['terminals'] if r['L_km'] == REF]
    probes = []
    for rank, (n, v, coordinate, bracket) in enumerate((
        (.165, 5.49375, 'P1', [5.4875, 5.5125]), (.165, 5.50625, 'P1', [5.4875, 5.5125]),
        (.16375, 5.5, 'P2', [.1625, .16562500000000002]),
        (.16531250000000003, 5.5, 'P2', [.1625, .16562500000000002])), 1):
        probes.append({'priority': rank, 'nu_raw': n, 'V_A': v, 'nu_raw_hex': n.hex(), 'V_A_hex': v.hex(),
            'coordinate': coordinate, 'bracket': bracket, 'condition': 'Only if still requested by unchanged AO after preceding valid result'})
    validation['proposed_probes_not_executed'] = probes
    text = ['# AO numerical validation', '',
        f"Current saved-data verification: {validation['protected_hashes_unchanged']} protected hashes unchanged, 147 compatible MB pairs/3822 metrics/26 identities. No physical/security/source/objective/AO rerun. Original epsilon1e-8/parameter1e-6/outer6/inner4/boundary3 unchanged.",
        f"Independent 147-row maxima agree with genuine AO terminal selection at {validation['catalog_matches']}/26 distances. Selected-direction closures={validation['coordinate_closures']}; no numerical/global certification.",
        'Reference top evaluated candidates:', '', '| nu_raw | VA | K | Gap from best |', '|---|---|---|---|']
    text += [f"| {r['nu_raw']!r} | {r['V_A']!r} | {r['SKR']!r} | {best['SKR']-r['SKR']!r} |" for r in reference[:5]]
    text += ['', 'Reference multi-start terminal results:', '', '| Start | nu | VA | K | State |', '|---|---|---|---|---|']
    text += [f"| {r['start_id']} | {r['terminal_nu']} | {r['terminal_V_A']} | {r['terminal_K']} | {r['status']} |" for r in starts]
    for s in data['targeted']:
        text += ['', f"{s['label']}: bracket={s['bracket']}, width={s['bracket'][1]-s['bracket'][0]!r}; status={s['status']}; missing={s['source_missing']}."]
    text += ['', 'At 22 km P1/P2 selected-final diagnostics:', str([audit.diagnostic(s, data['rankings'][22.]) for s in data['finals'][22.]]),
        '', 'Code semantics: starts .1/.15/.3/.8 plus warm pair; initial VA is warm value only if available, otherwise smallest slice value. Every available positive coordinate value is compared. Endpoint halving/doubling cap3; paired nearest-neighbor midpoints cap4; radius tolerance checked at loop entry. An attempted missing-pair stage is not a completed refinement. Earlier unresolved-search latch persists. At small objective change, open boundary => UNRESOLVED_BOUNDARY; incomplete/latch => STAGNATED_IN_EXACT_CATALOG; only complete/warning-free searches permit CONVERGED_NUMERICALLY. Caps/failures do not certify closure.',
        '', 'nu0=.8 actual full-cycle pairs: (.8,1.5)->(.5,1.5)->(.4,3)->(.4,3), finalK=.06912585821984563. Final missing (.4,1.5) and(.2,3), not proven distinct basin. Four other starts reach reference best. All-distance multi-start terminals in ao_multistart_terminal_results.csv.',
        '', 'Local support: both reference nearest evaluated VA and nu neighbors have lower recorded K. Missing midpoints and remote directions prevent continuous optimality. Whole-objective error at the top-two gap is unbounded; GH8 deterministic MI and original AP1050/1250/1450 preserved, not promoted to an error certificate.',
        '', 'Historical139-MB numerical/certification catalog was inspected, not mixed into 147-source maximum claims. Historical comparison curve is stored compatible Uniform/fixedMB only; MB curve uses current147 best. Uniform omission is rendering only (last positive25km); no invented crossing/interpolation/abs/zero replacement.',
        '', 'Theory nu>=0 vs implementation nu>0 remains unresolved. Frozen-spec historical expected hash differs from unchanged current re-freeze; recorded PREEXISTING_UNCHANGED. Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS; manuscript-ready formatting does not authorize training/finaltest/security/global claims.',
        '', f"Regression evidence: {validation['test_count']} tests PASS; gitdiffcheck PASS. LaTeX compile={validation['latex_compilation']}; snippet packages/figures supplied, no unsupported local compile claim."]
    (OUT / 'ao_numerical_validation.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    plan = ['# Minimal targeted exact-source requests (planning only)', '',
        'No AP computations are authorized or performed by this export. Priorities follow the actual paired-coordinate request order, not catalog growth. Reassess the incumbent/bracket and active missing requests after each valid source; do not automatically execute all four.',
        '', '| Order | Raw nu | VA | Search | Current bracket |', '|---|---|---|---|---|']
    plan += [f"| {p['priority']} | {p['nu_raw']!r} | {p['V_A']!r} | {p['coordinate']} | {p['bracket']} |" for p in probes]
    plan += ['', 'P1 lower midpoint is the first requested point, directly testing the narrower variance neighborhood of the reference incumbent. Its upper partner is needed to complete that paired stage only if it remains an active request after reevaluation. P2 lower/upper midpoint order follows the implemented routine; both assess shaping at the current VA only while that slice remains relevant. No SKR gain is promised.',
        '', 'For a separately approved single P1 computation: propose total90min, source ceiling75min, reserve15min for original26distance objective/cache-onlyAO and cleanup, one attempt. The original source evaluator plus previously validated minimal AC/Sleep/Windows Job deadline supervision is required; do not invoke the recently failing observer path. Runtime-to-valid-source is unknown; older stopped attempts do not demonstrate numerical impossibility or predict completion. P2 has timeout history and needs a separately chosen adequate ceiling, not an unapproved extension or automatic retry.',
        '', 'Expected scientific output: original validated C,w with unchanged binary64 key/provenance, exact SKR on26distances, actual incumbent/bracket/nextrequests, original cache-onlyAO and independent finite-catalog comparison. No interpolation or promised convergence.',
        '', 'Four requested points alone do not certify the whole domain. Other distances and nu0=.8 have additional dependencies; original4-stage cap/6outer/stagnation latch, nu=0 endpoint, remote directions and objective-error bounds must remain explicit.']
    plan += ['', 'Exact parameter identities:'] + [str(p) for p in probes]
    (OUT / 'targeted_next_exact_probes.md').write_text('\n'.join(plan) + '\n', encoding='utf-8')
    summary = ['# Final scientific summary', '',
        'Status: SCIENTIFIC_DELIVERABLES_COMPLETE_FROM_SAVED_EXACT_DATA; CONTINUOUS_OPTIMUM_NOT_CERTIFIED.',
        '', f"147 MB sources,3822 stored exact-source numerical objectives,129 historical starts/283 outer iterations; independently verified AO/catalog agreement{validation['catalog_matches']}/26. Zero new AP/channel/security/objective/AO executions; no observer changes.",
        '', 'Reference best(.165,5.5),K=.07798099387393764;22km best(.165,5.475),K=.07661740491526092. Reference four/five starts agree; nu0=.8 lower/incomplete. All26 parameters/IAB/betaIAB/chi/K/statuses in optimized_skr_26_distances.csv.',
        '', 'Algorithm1 and joint optimization LaTeX section reflect actual P1/P2, initialization, endpoint expansion, midpoint refinement, persistent unresolved flag and stopping logic. Upload this directory to Overleaf with listed packages; input joint_optimization_section.tex from manuscript root.',
        '', 'Genuine iteration/parameter plots and exact reference/22km coordinate slices supplied as vectorPDF/400dpiPNG. Distance plot uses original raw SKR samples, positive-only standard base10 logarithmic axis; Uniform ends25km, bothMB through40km. Captions distinguish finite evaluated best from continuous/globaloptimum.',
        '', f"Source provenance/protected hashes/tests/diffPASS; LaTeX compile={validation['latex_compilation']}. Publication-quality artifacts do not change NOT_READY_FOR_PUBLICATION_SCALE_RUNS lifecycle.",
        '', 'Next scientific requests are conditional P1 lower/upper then P2 lower/upper active midpoints, documented with binary64 identities and risk/budget proposal. No execution authority inferred; stronger optimality needs moments, numerical-error and domain/termination evidence.']
    (OUT / 'final_scientific_summary.md').write_text('\n'.join(summary) + '\n', encoding='utf-8')


def main():
    if (OUT / 'optimized_skr_26_distances.csv').exists():
        raise FileExistsError('Scientific export exists; never overwrite or rerun')
    OUT.mkdir(exist_ok=True)
    before = unchanged()
    with ExitStack() as stack:
        for module, name in ((ao, 'evaluate_candidate'), (ao.ExactMBEvaluator, 'source_moments'),
                             (audit.gram_moments, '_fallback'), (sweep, 'make_channel'),
                             (ao, 'adaptive_maximize_1d'), (sweep, 'run_single_distance_ao')):
            stack.enter_context(patch.object(module, name, audit.forbidden))
        data = analyze()
    write_csv('optimized_skr_26_distances.csv', data['best'])
    write_csv('ao_iteration_history.csv', data['history'])
    write_csv('ao_multistart_terminal_results.csv', data['terminals'])
    write_csv('three_scheme_exact_data.csv', data['comparison'])
    write_csv('coordinate_search_status.csv', [audit.diagnostic(s, data['rankings'][d]) for d, ss in data['finals'].items() for s in ss])
    plots(data)
    tests = []
    for pattern in ('test_ao_scientific_export.py', 'test_alt_opt_provenance_and_stopping.py', 'test_ao_numerical_optimum_audit.py'):
        completed = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        output = completed.stdout + completed.stderr
        count = next(int(line.split()[1]) for line in output.splitlines() if line.startswith('Ran '))
        tests.append({'pattern': pattern, 'count': count, 'returncode': completed.returncode, 'output': output})
        assert completed.returncode == 0, tests[-1]
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    assert unchanged() == before
    identities = [BASE / n for n in ('objective_checkpoint.json', 'cache_only_runs.json', 'cache_only_searches.json', 'reference_targeted_coordinate_searches.json')]
    validation = {'status': 'CURRENTLY_VERIFIED_PASS_SAVED_DATA_EXPORT',
        'MB_sources': 147, 'stored_metrics': 3822, 'starts': 129, 'outer_iterations': 283,
        'catalog_matches': sum(r['AO_matches_catalog'] for r in data['best']),
        'coordinate_closures': sum(ao.coordinate_search_complete(s) for ss in data['finals'].values() for s in ss),
        'protected_hashes_unchanged': before, 'protected_manifest': str(PROTECTED.relative_to(ROOT)),
        'protected_manifest_sha256': sweep.sha256(PROTECTED),
        'input_hashes': {str(p.relative_to(ROOT)): sweep.sha256(p) for p in [*identities, CURVES]},
        'producer_sha256': sweep.sha256(Path(__file__)), 'tests': tests, 'test_count': sum(t['count'] for t in tests),
        'new_AP_source_channel_security_objective_AO_calls': 0, 'observer_modified_or_invoked': False,
        'no_interpolation': True, 'ordinary_log_base': 10, 'Uniform_last_positive_km': 25,
        'displayed_positive_samples': dict(Counter(r['scheme'] for r in data['comparison'] if r['K'] > 0)),
        'latex_compilation': 'NOT_RUN_NO_LOCAL_LATEX_ENGINE' if not shutil.which('pdflatex') else 'NOT_RUN_SNIPPETS_ONLY',
        'classification': 'FINITE_CATALOG_MAXIMUM;COORDINATE_SEARCH_INCOMPLETE;GLOBAL_OPTIMUM_NOT_CERTIFIED',
        'historical_frozen_hash_discrepancy': 'PREEXISTING_UNCHANGED', 'lifecycle': 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS'}
    assert validation['catalog_matches'] == 26 and validation['coordinate_closures'] == 0
    documents(data, validation)
    (OUT / 'scientific_validation.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: validation[k] for k in ('status', 'MB_sources', 'stored_metrics', 'catalog_matches', 'coordinate_closures', 'test_count')}, indent=2))


if __name__ == '__main__':main()
