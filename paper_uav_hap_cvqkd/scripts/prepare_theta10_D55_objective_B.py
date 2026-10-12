"""Phase B1: exact-cache coordinate reconstruction and bounded B2 plan only."""
from collections import Counter
from contextlib import ExitStack
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import export_theta10_D55_ao_scientific_results as saved
from scripts import exact_cache_provenance as provenance
from scripts import windows_sleep_safe_supervision as safe
from src.cvqkd import gram_moments

OUT = ROOT / 'results/theta10_D55_objective_B_numerical_skr_optimization'
ao, source, sweep = saved.ao, saved.source, saved.sweep
# ExactObjective inspects these globals even on a cache hit: preserve them in guard.
BETA, EPSILON, GH_ORDER = (ao.evaluate_candidate.__globals__[k] for k in ('BETA', 'EPSILON', 'GH_ORDER'))


def forbidden(*args, **kwargs):
    raise AssertionError('B1 forbids AP, fresh objective evaluation and full AO sweeps')


def scan_caches(config):
    valid, files, excluded = {}, [], []
    settings = provenance.source_settings(config)
    for path in sorted((ROOT / 'results').glob('**/exact_source_cache/*.json')):
        files.append(path)
        try:
            p = saved.read(path)
            p['_provenance'] = provenance.verify_source_payload(p, settings)
            p['_path'] = path.relative_to(ROOT).as_posix()
            valid[p['ensemble_hash']] = p
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            excluded.append({'path': path.relative_to(ROOT).as_posix(), 'reason': str(error)})
    return valid, files, excluded


def prior_attempts(nu, va):
    result = []
    for path in sorted((ROOT / 'results').glob('**/source_generation_ledger.json')):
        if 'checkpoint' in path.as_posix():
            continue
        for a in saved.read(path).get('attempts', []):
            if a.get('nu_raw') is not None and a.get('V_A') is not None and saved.pair(a['nu_raw'], a['V_A']) == saved.pair(nu, va):
                result.append({'ledger': path.relative_to(ROOT).as_posix(), 'status': a.get('status'),
                    'wall_seconds': a.get('wall_seconds', a.get('elapsed_seconds', 'NOT_RECORDED')),
                    'CPU_seconds': a.get('cpu_seconds', 'NOT_RECORDED')})
    return result


def main():
    if OUT.exists():
        raise SystemExit('Refusing to overwrite Objective B artifacts')
    protected = saved.read(ROOT / 'results/theta10_D55_ao_manuscript_finalization/protected_input_manifest.json')
    for p in (ROOT / 'results/theta10_D55_ao_manuscript_finalization').rglob('*'):
        if p.is_file():
            protected[p.relative_to(ROOT).as_posix()] = sweep.sha256(p)
    assert all(sweep.sha256(ROOT / n) == h for n, h in protected.items())
    config = source.unconstrained_config()
    bank, paths, excluded = scan_caches(config)
    for p in paths:
        protected[p.relative_to(ROOT).as_posix()] = sweep.sha256(p)
    OUT.mkdir()
    saved_export = saved.OUT
    # Reuse the existing CSV writer; only redirect its output, restore on exit.
    with patch.object(saved, 'OUT', OUT), ExitStack() as guards:
        for obj, name in ((ao.ExactMBEvaluator, 'source_moments'), (ao, 'evaluate_candidate'),
                          (gram_moments, '_fallback'), (sweep, 'make_channel'),
                          (ao, 'run_single_ao'), (sweep, 'run_single_distance_ao')):
            guards.enter_context(patch.object(obj, name, forbidden))
        data = saved.analyze()
        reference = data['checkpoint'][str(saved.REF)]
        obj = ao.ExactObjective(config, reference['identity']['identity']['channel'], OUT,
            allow_new_source=False, source_cache_dirs=saved.DIRS)
        obj.restore_objective_rows(reference['rows'], reference['identity'])
        for r in reference['rows']:
            obj.register_catalog(r['nu_raw'], r['V_A'])
        incumbent = data['rankings'][saved.REF][0]
        coordinates = []
        searches = []
        for variable, fixed in (('V_A', incumbent['nu_raw']), ('nu_raw', incumbent['V_A'])):
            result = ao.adaptive_maximize_1d(variable=variable, fixed=fixed,
                values=obj.catalog_values(variable, fixed), objective=obj)
            result['L_km'] = saved.REF
            old = next(x for x in data['targeted'] if x['variable'] == variable)
            assert result['history'] == old['history'] and result['bracket'] == old['bracket']
            assert result['best_K'] == incumbent['SKR']
            diagnostic = saved.audit.diagnostic(result, reference['rows'])
            coordinates.append({**diagnostic, 'candidate_history': result['history'],
                'source_scope': 'LIVE_ORIGINAL_CACHE_ONLY_COORDINATE_CALL',
                'bracket_persists_as_state': False, 'catalog_persists_as_state': True})
            searches.append(result)
        assert obj.unique_exact_evaluations == 0 and len(obj.catalog) == 147
        saved.write_csv('reference_ao_coordinate_search.csv', coordinates)
        plan = []
        for number, (nu, va, search) in enumerate((
            (.165, 5.49375, searches[0]), (.165, 5.50625, searches[0]),
            (.16375, 5.5, searches[1]), (.16531250000000003, 5.5, searches[1])), 1):
            ensemble = source.make_ensemble(config, 'MB', nu, va)
            identity = obj.evaluator._source_identity(ensemble, nu, va)
            key = ao.json_hash(identity)
            candidate = source.candidate_from_payload(config, bank, 'MB', nu, va)
            assert candidate is None, 'Previously missing source found: reassess before requesting AP'
            plan.append({'priority': number, 'nu_raw': nu, 'V_A': va, 'nu_raw_hex': nu.hex(), 'V_A_hex': va.hex(),
                'nu_repo_hex': (42.5 * nu).hex(), 'compatible_current_cache_key': key,
                'ensemble_hash': identity['ensemble_hash'], 'original_source_identity': identity,
                'coordinate': 'P1' if number <= 2 else 'P2', 'bracket': search['bracket'],
                'cache_available': False, 'prior_attempts': prior_attempts(nu, va),
                'purpose': 'Exact requested midpoint: test improvement and support paired coordinate refinement',
                'proposed_per_probe_seconds': 3600, 'proposed_total_seconds': 4500, 'cleanup_postprocessing_reserve_seconds': 900,
                'execution_scope': 'REQUEST_ONE_FRESH_ATTEMPT_NOW' if number == 1 else 'INVENTORY_ONLY_NOT_INCLUDED_IN_REQUESTED_B2',
                'condition': 'Fresh authorization plus safe minimal preflight; no auto retry' if number == 1
                             else 'Reconstruct original AO after preceding result; separately approve only if still requested',
                'source_worker': 'Original ExactMBEvaluator.source_moments -> gram_moments -> full_support_c4_worker; no profiler hook',
                'inner_AP_timeout_seconds': 3600, 'SKR_prediction': 'NOT_AVAILABLE'})
        saved.write_csv('targeted_exact_probe_plan.csv', plan)
        states = []
        for r in data['best']:
            d = r['L_km']
            checks = data['finals'][d]
            states.append({'L_km': d, 'nu_raw': r['best_nu_raw'], 'V_A': r['best_V_A'], 'stored_K': r['best_SKR'],
                'supported_level': 1, 'Level1_finite_catalog_maximum': True,
                'Level2_local_neighbor_evidence': 'PARTIAL_NOT_PARAMETER_TOLERANCE',
                'Level3_coordinate_optimum': False, 'Level4_multistart_numerically_converged': False,
                'Level5_global_certified': False, 'P1_status': checks[0]['status'], 'P2_status': checks[1]['status'],
                'top_two_stored_gap': r['top_two_gap'], 'gap_discrimination_accuracy': 'NOT_ESTABLISHED_TOTAL_K_ERROR_UNBOUNDED',
                'guaranteed_significant_digits': 'NOT_CERTIFIED', 'scope': 'VERIFIED_EXISTING_RECORD_NOT_NEW_DISTANCE_SWEEP'})
        saved.write_csv('numerical_optimality_status.csv', states)
        saved.write_csv('ao_multistart_validation.csv', [{**r, 'history_scope': 'GENUINE_EXISTING_BASELINE_NOT_RERUN',
            'complete_cycle_trajectory': next(x['trajectory'] for x in data['runs'] if x['L_km'] == r['L_km'] and x['start_id'] == r['start_id'])}
            for r in data['terminals']])
        saved.write_csv('optimized_skr_26_distances.csv', [{'L_km': r['L_km'], 'nu_raw': r['best_nu_raw'], 'V_A': r['best_V_A'],
            'I_AB': r['I_AB'], 'beta_I_AB': r['beta_I_AB'], 'chi_BE': r['chi_BE'], 'best_SKR': r['best_SKR'],
            'AO_status': r['AO_status'], 'P1_status': data['finals'][r['L_km']][0]['status'],
            'P2_status': data['finals'][r['L_km']][1]['status'], 'supported_level': 1,
            'source_cache_key': r['source_cache_key'], 'provenance_scope': 'EXISTING_147_SOURCE_BASELINE_NO_NEW_SWEEP'} for r in data['best']])
    assert saved.OUT == saved_export
    # All-repository inventory can reveal valid PREEXISTING sources absent from
    # the 147-source sweep. Test them only at reference; do not start a new sweep.
    baseline_pairs = {saved.pair(r['nu_raw'], r['V_A']) for r in reference['rows']}
    extra_reference = []
    for p in bank.values():
        nu, va = float.fromhex(p['nu_mb_raw_hex']), float.fromhex(p['V_A_hex'])
        if nu > 0 and saved.pair(nu, va) not in baseline_pairs:
            candidate = source.candidate_from_payload(config, bank, 'MB', nu, va)
            assert candidate is not None
            row = ao.evaluate_candidate(candidate, reference['identity']['identity']['channel'], config)
            assert row['SKR'] <= incumbent['SKR'], 'Existing-source improvement: reassess before AP plan'
            extra_reference.append(row)
    power = safe.WindowsPower().read()  # Read only; no power lease or worker started.
    details = f"""# Objective B — Phase B1 progress

B1 preparation COMPLETE; B2 NOT_AUTHORIZED, AP NOT_RUN. Scientific method and defaults unchanged.
147 sources/3822 existing metrics/26 distances independently revalidated. Reference highest stored K={incumbent['SKR']!r} at raw({incumbent['nu_raw']!r},{incumbent['V_A']!r}). Use about0.077981 bits/use for orientation; no number of accurate decimal digits is certified. Only Level1 finite-catalog ordering is established; partial local-neighbor evidence is not Level3/4/5.

Two actual original adaptive coordinate calls, cached147 objective rows, zero fresh SKR or C,w evaluations; histories/brackets reproduce recorded reference searches. P1/P2 record every exact or missing candidate event in reference_ao_coordinate_search.csv. All{len(paths)} repository exact_source_cache payload files scanned;{len(excluded)} incompatible records excluded with reasons in verification JSON. No required midpoint is present in compatible caches. Stored26-distance data are reported, not a fresh sweep: reference progress is not yet established.

## Fourteen scientific answers

1. Reference highest currently validated STORED numerical SKR:0.07798099387393764 bits/use, not an accuracy certificate.
2. Rawnu=.165,VA=5.5; repo=42.5*raw, never substituted in reports.
3. No compatible stored candidate improves this incumbent. Global cache inventory also revealed{len(extra_reference)} valid PREEXISTING source outside the147-source sweep: {json.dumps(extra_reference)}. These reference-only original-evaluator checks use existing C,w, not AP. No improvement occurs and no26-distance sweep is launched without P1/P2 progress. Missing objective values could improve the incumbent; no prediction is made.
4. P1 bracket[5.4875,5.5125], radius about.0125, missing(.165,5.49375)/(.165,5.50625), status BRACKETED_EXACT_CATALOG_SOURCE_MISSING. First paired stage stops with missing values before cap4, not at parameter tolerance.
5. P2 bracket[.1625,.16562500000000002], radius about.0025, missing(.16375,5.5)/(.16531250000000003,5.5); likewise incomplete. Remote directions andnu0 endpoint coverage are not certified.
6. Next original request is(.165,5.49375). Binary64 and original cache identity are in targeted_exact_probe_plan.csv. Later three points are inventory only, not included in the approval request.
7. A valid result directly supplies an active P1 request and its SKR at26 distances, but a SINGLE source does not complete a paired stage. The original function requests both midpoints even if the first is missing; after cache expansion, rederive the winning point/bracket before deciding whether the old upper partner remains relevant.
8. Inner evaluated-map/bracket and stage count restart each call; ExactObjective catalog/rows persist and successful NEW sources are registered, so future calls can start from genuinely narrower cached neighbors. Repeating calls without new sources does not help. Under fixed-incumbent halving, P1/P2 need14/12 successful levels, plus a subsequent loop-entry check; four levels from current radii give about7.8125e-4/1.5625e-4, still above1e-6. This is not a universal impossibility proof for a call starting from an already tight expanded catalog. Outer epsilon and persistent unresolved latch can stop useful continuation. Separate expanded-refinement experiment PROPOSED ONLY: J=4 versus16, original R6/epsilon1e-8/parameter1e-6/updates/evaluator/multi-start fixed; not executed or authorized by a one-probe B2 approval.
9. Nearest stored runner-up(.165,5.4875) has K.07798091552916897, gap7.834476867252249e-8. Ordering of stored floats is exact; physical/numerical discrimination at that scale is NOT_ESTABLISHED, not a proven tie or error bar.
10. Reference4/5 starts hit selected maximum;nu0=.8 ends(.4,3),K.06912585821984563 with missing(.4,1.5)/(.2,3). Genuine records establish unresolved search/coverage, not a distinct converged basin. Across26 distances59/129 individual matches,0 unanimous distances; best-selected matches26/26.
11. Source payloads verify full support256, finite C,w, compatible ensemble/code/settings and precision identity1050/1250/1450. Worker acceptance checks last-two resolved rank256 rows and original1e-7+1e-6*max(abs(values)) agreement; intermediate precision rows/pointwise convergence residuals are not fully serialized in these source caches. Deterministic GH8 MI has no hash-bound point-specific quadrature error certificate here. Direct-Z-minus finite/physicality-checked original evaluator has no total chi/K perturbation bound here. Stored betaI-chi decomposition reproduces K; float64 subtraction/spectral/source/MI error is not bounded by epsilon_opt. Reusing cached values across sensitivity runs is not an independent fresh numerical-accuracy experiment. Historical Monte-Carlo preregistration and exact_tau_oracle_v2_1.yaml do not certify this GH8/direct-Z snapshot; baseline_smoke.json is a different legacy configuration.
12. Obtain active P1 source(s), re-evaluate original SKR/AO, resolve actual new P1/P2 requests, control cap/parameter completion through separately authorized experiments if needed, test alternative starts/open directions/Uniform endpoint and bound point-specific source/MI/Holevo/K uncertainty. Do not generate all55 pairs indiscriminately. A global proof is not required for useful qualified local numerical results.
13. Existing selected147-source curve, genuine histories, finite-catalog comparison and safeguard sensitivity are manuscript-ready as qualified best-found results. Objective A is unchanged. Continuous convergence/unique or global optimum and error8decimal claims are not supported.
14. Smallest bounded pilot proposed: ONE freshly approved P1 attempt, total75min including processing/cleanup; probe max60min and reserve15min. Runtime-to-success unknown, no promised completion, no reuse of earlier budgets or automatic timeout/AC-abort retries.

## Minimal execution path and safety gates (not launched)

Use the original scientific API ExactMBEvaluator.source_moments in one small child invocation, which directly invokes unchanged full_support_c4_worker through the original fallback, under existing windows_sleep_safe_supervision.supervised_process and AwakeOnAC. Do NOT use old probe_worker/profile_worker or overnight/observer controllers: probe_worker rewrites the worker launch into a profiler and changes the inner timeout. The uninstrumented original fallback timeout is3600s; increasing only an outer deadline cannot extend it. Proposal intentionally respects that limit. Existing Job supervisor controls the whole tree and aggregate CPU; AC/read errors/suspend or scheduler gap/deadline abort, no retry, lease restoration in finally. Manual suspend is not preventable; any observed wall overrun is failure, not a guaranteed deadline pass during suspension.

Current read-only power snapshot:{json.dumps(power)}. This is NOT a stable-AC runtime receipt. At B2 startup require fresh stable AC, verified temporary Sleep lease, bounded native dummy containment/timeout/cleanup check for the selected minimal command and cache/provenance readiness. General existing supervisor code and unit receipts are not a current end-to-end AP launch certificate. If safe minimal path cannot pass these checks, stop AP/report blocker; no observer/heartbeat engineering project is authorized. No AP launch/controller has been created in B1.

After a successful source, validate C,w/cache identity, compute its exact SKR on26 saved compatible channels using original evaluator, re-run original cache-only multistart AO with its own warm chain, independently rank expanded catalog, record changed incumbent/brackets/next requests. Continue no additional AP outside explicit approval. After timeout/unsafe abort, kill whole tree, save status, restore Sleep and stop this one-attempt campaign.

Frozen historical hash discrepancy remains PREEXISTING_UNCHANGED; lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains. Preparation is explicitly authorized; it is not model-level, AP or publication approval. Old plots/LaTeX/configs/source caches are untouched.
"""
    (OUT / 'objective_B_progress.md').write_text(details, encoding='utf-8')
    summary = """# Objective B — B1 summary

No new reliable SKR improvement yet. Reference stored best raw(.165,5.5),K.07798099387393764;22km raw(.165,5.475),K.07661740491526092. Finite-catalog maximum26/26, no coordinate closure, no full numerical/global certificate. Live reference P1/P2 cache-only reconstruction reproduces original requests exactly; all compatible source caches checked and four midpoints remain missing.

Priority1 P1(.165,5.49375): propose fresh ONE attempt75min total/60min probe/15min verification-cleanup reserve. Do not launch old profiling/observer worker; use original direct scientific API with existing AC/Sleep/Job supervision only after approved budget and minimal safety preflight. Original internal3600s timeout is retained. No AP before explicit authorization; later three points are conditional inventory, not included in this request.

All seven requested B1 outputs are present. 26-distance CSV and multistart CSV explicitly carry existing-record scope, not new optimization or fabricated AO trajectories. Exact-source parameter keys/previous runtime failures and full candidate histories are attached to focused CSVs. Detailed14 answers and numerical-error/refinement/safety limitations are in objective_B_progress.md. B1 validation/protected hashes are in objective_B_verification.json; scoped regression checks recorded separately after execution. Objective A and all prior artifacts preserved. STOP and request B2 authorization once; no inference from unused old budgets.
"""
    (OUT / 'objective_B_summary.md').write_text(summary, encoding='utf-8')
    assert all(sweep.sha256(ROOT / n) == h for n, h in protected.items())
    validation = {'status': 'CURRENTLY_VERIFIED_PASS_B1_PREPARATION_ONLY', 'MB_sources': 147,
        'compatible_positive_sources_in_global_inventory': len(baseline_pairs) + len(extra_reference),
        'additional_reference_existing_source_checks': extra_reference,
        'stored_objectives': 3822, 'live_reference_coordinate_calls': 2, 'new_source_moments': 0,
        'new_SKR_evaluations': obj.unique_exact_evaluations + len(extra_reference), 'new_full_AO_sweeps': 0,
        'highest_supported_level': 1, 'source_cache_files_scanned': len(paths), 'incompatible_cache_records': excluded,
        'required_midpoints_missing': 4, 'probe1_identity': plan[0]['original_source_identity'],
        'proposed_B2_total_seconds': 4500, 'proposed_B2_probe_seconds': 3600, 'reserve_seconds': 900,
        'B2_authorized': False, 'AP_launch_readiness': 'NOT_VERIFIED_PENDING_APPROVAL_AND_MINIMAL_NATIVE_PREFLIGHT',
        'power_read_only': power, 'sleep_or_job_activated': False,
        'protected_input_hashes': protected, 'protected_count': len(protected),
        'producer_sha256': sweep.sha256(Path(__file__)),
        'output_hashes': {p.name: sweep.sha256(p) for p in OUT.iterdir() if p.is_file()}}
    (OUT / 'objective_B_verification.json').write_text(json.dumps(validation, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: validation[k] for k in ('status', 'protected_count', 'source_cache_files_scanned', 'required_midpoints_missing', 'B2_authorized')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
