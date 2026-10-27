"""Authorized 61-angle diagnostic: read historical C,w; evaluate only missing rates."""
import csv
from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = ROOT / 'results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024'
sys.path.insert(0, str(BASE))
import inventory as historical
import diagnostic_model as evaluator

canonical = historical.canonical
read, sha, rows = historical.read, historical.sha, historical.rows
clean = historical.prior_run.old.clean
STRICT = historical.STRICT
PASS = 'CURRENTLY_VERIFIED_PASS'
LABEL = 'DIAGNOSTIC_ONLY'
NUMERIC = {'VA','nu_raw','nu_repo','C','w','eta_f','xi_f','N_effective','I_AB',
    'beta_I_AB','chi_BE','K_raw','K_operational','Z_manuscript_eq14','V','W',
    'Delta','D','nu_1','nu_2','nu_3','MI_GH64_128_difference','MI_seconds',
    'Holevo_seconds','probability_deficit','M0','E_sqrt_eta','E_eta','P0',
    'best_second_gap'}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


nine = load('_preserved_nine_angle_selection', BASE / 'run.py')
SCHEMES = nine.SCHEMES


def save(name, value):
    (OUT/name).write_bytes((json.dumps(clean(value), ensure_ascii=False,
        indent=2, allow_nan=False)+'\n').encode('utf-8'))


def write(name, records):
    fields = list(dict.fromkeys(k for r in records for k in r))
    with (OUT/name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(clean(records))


def numeric(records):
    return [{k: (float(v) if v != '' else None) if k in NUMERIC else v
             for k, v in row.items()} for row in records]


def source_pool(physical):
    domain = physical['source_domain']
    pool = [r for r in rows(BASE/'exact_source_inventory.csv')
        if domain['VA'][0] <= float(r['VA']) <= domain['VA'][1]
        and domain['nu_raw'][0] <= float(r['nu_raw']) <= domain['nu_raw'][1]]
    assert len(pool) == 212
    assert len({s['canonical_source_identity'] for s in pool}) == len(pool)
    assert len({s['ensemble_hash'] for s in pool}) == len(pool)
    for row in pool:
        assert row['compatibility_status'] == PASS
        assert row['source_evidence_class'] in STRICT | {'INSUFFICIENT_EVIDENCE'}
        assert sha(ROOT/row['source_path']) == row['source_sha256']
        source = dict(row, VA=float.fromhex(row['VA_hex']), nu_raw=float.fromhex(row['nu_raw_hex']),
            C=float(row['C']), w=float(row['w']), classification=row['source_evidence_class'])
        payload = read(ROOT/source['source_path'])
        historical.verify_source_payload(payload, json.loads(row['source_settings_json']))
        assert source['C'].hex() == row['C_hex'] and source['w'].hex() == row['w_hex']
        assert float(row['nu_repo']) == 42.5*source['nu_raw']
        source = historical.with_ensemble(source)
        p, alpha = canonical.prior_model.helpers().validate_source(source)
        assert historical.input_digests(source) == json.loads(row['input_digests_json'])
        assert abs(float(p @ (2*alpha.real)**2)-source['VA']) <= 2e-12
        yield source


def prepare():
    if (OUT/'protocol.json').exists():
        raise FileExistsError('Preserve existing experiment; preparation is single-use')
    old_start = read(BASE/'startup_manifest.json')
    protected = dict(old_start['protected'])
    for path in BASE.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            protected[path.relative_to(ROOT.parent).as_posix()] = sha(path)
    for name, digest in protected.items():
        assert sha(ROOT.parent/name) == digest, name
    git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, encoding='utf-8')
    save('startup_manifest.json', dict(branch=git('branch','--show-current').strip(),
        HEAD=git('rev-parse','HEAD').strip(), git_status=git('status','--short'),
        protected=protected, ledger_exceptions=old_start['ledger_exceptions']))
    (OUT/'startup_git_diff.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=ROOT))
    for name in old_start['ledger_exceptions']:
        path = ROOT.parent/name
        if not path.exists(): path = ROOT/name
        target = OUT/'startup_ledgers'/path.name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(path.read_bytes())
    baseline_check = load('_read_only_baseline_check', BASE/'verify.py').verify()
    save('baseline_verification.json', baseline_check)
    origin = ROOT/'results/skr_vs_zenith_eq14_v43_20261023/protocol.json'
    original = read(origin)
    angles, pilot_angles = original['angles_deg'], original['pilot_angles_deg']
    assert len(angles) == 61 and angles == sorted(set(angles))
    assert set(pilot_angles).issubset(angles)
    contexts = read(BASE/'channel_contexts.json')
    assert sorted(c['zenith_deg'] for c in contexts) == pilot_angles
    scope = read(BASE/'available_catalog_protocol.json')
    old = read(BASE/'protocol.json')
    physical_path = ROOT/old['physical_protocol_path']
    assert sha(physical_path) == old['physical_protocol_sha256'] == scope['physical_protocol_sha256']
    for name, digest in scope['code_sha256'].items():
        executed = BASE/name if sha(BASE/name) == digest else BASE/'execution_producers'/name
        assert sha(executed) == digest
    assert sha(BASE/'diagnostic_model.py') == scope['code_sha256']['diagnostic_model.py']
    physical = read(physical_path)
    canonical.validate_protocol(physical)
    sources = list(source_pool(physical))
    pool_rows = [{k:v for k,v in s.items() if k not in {'p','alpha'}} for s in sources]
    write('source_pool.csv', pool_rows)
    save('authorization.json', dict(date='2026-10-24', user_task=
        'Phase B: 61-Angle Diagnostic SKR Sweep Using Historical Exact C,w',
        authorized='61 original angles; reuse 212 historical sources and 1908 matching rates',
        new_Cw=False, interpolation=False, strict_gate_relaxed=False,
        manuscript_or_production_or_historical_edits=False, publication=False))
    save('protocol.json', dict(version=1, result_scope=LABEL,
        grid_origin=origin.relative_to(ROOT).as_posix(), grid_origin_sha256=sha(origin),
        grid_json_pointer='/angles_deg', angles_deg=angles, previous_angles_deg=pilot_angles,
        physical_protocol_path=old['physical_protocol_path'], physical_protocol_sha256=sha(physical_path),
        experiment_spec_sha256=physical['experiment_spec_sha256'],
        baseline_path=BASE.relative_to(ROOT).as_posix(), baseline_manifest_sha256=sha(BASE/'artifact_manifest.json'),
        baseline_results_sha256=sha(BASE/'diagnostic_results.csv'),
        baseline_contexts_sha256=sha(BASE/'channel_contexts.json'),
        source_pool_sha256=sha(OUT/'source_pool.csv'), source_pool_count=212,
        source_domain=physical['source_domain'], source_evidence_policy='PRESERVE_HISTORICAL_CLASSIFICATIONS',
        correlation_policy='manuscript_eq14_direct', source_normalization=physical['source_normalization'],
        nu_conversion='nu_repo=42.5*nu_raw', truncation_policy=physical['truncation_policy'],
        numerical=physical['numerical'], raw_objective='beta*I_AB-chi_BE',
        operational_reporting='max(0,K_raw); never inside candidate ranking',
        canonical_evaluator_path=(BASE/'diagnostic_model.py').relative_to(ROOT).as_posix(),
        canonical_evaluator_sha256=sha(BASE/'diagnostic_model.py'),
        baseline_producer_hashes=scope['code_sha256'], sweep_producer_sha256=sha(OUT/'sweep.py'),
        expected_reused_evaluations=1908, expected_new_evaluations=11024,
        source_Cw_computations=0, source_generation_attempts=0,
        strict_Phase_B_ready=False, strict_Phase_B_complete=False,
        missing_Uniform_VA_hex='0x1.9ffff84830112p+0', missing_Uniform_nu_raw=0.0))


def decorate(record, source, angle, context, reused=False, baseline_row=None):
    record = dict(record)
    original_scope = record.get('result_scope','')
    record.update(result_scope=LABEL, previous_result_scope=original_scope if reused else '',
        zenith_deg=angle, source_id=source['canonical_source_identity'], Cw_source_id=source['canonical_source_identity'],
        scheme='Uniform candidate' if source['family']=='Uniform' else 'MB candidate',
        eligible_schemes=';'.join([SCHEMES[2]] + ([SCHEMES[0]] if source['family']=='Uniform' else [])
            + ([SCHEMES[1]] if source['ensemble_hash']==PHYSICAL['fixed_MB']['ensemble_hash'] else [])),
        source_evidence_class=source['classification'], source_convergence_status=source['classification'],
        source_convergence_receipts=source['convergence_receipts'],
        evaluation_origin='REUSED_NINE_ANGLE' if reused else 'NEW_RATE_HISTORICAL_CW',
        reused_from=(BASE/'diagnostic_results.csv').relative_to(ROOT).as_posix() if reused else '',
        reused_row_number=baseline_row if reused else '',
        experiment_protocol_sha256=sha(OUT/'protocol.json'),
        channel_context_sha256=sha(OUT/f'angle_{angle:02d}_context.json'),
        Cw_reused=True, source_Cw_recomputed=False, security_valid=False,
        K_operational=max(0.,float(record['K_raw'])) if record.get('K_raw') is not None else None)
    return record


def execute():
    global PHYSICAL
    task = read(OUT/'protocol.json')
    if (OUT/'execution_summary.json').exists(): raise FileExistsError('Completed run is immutable')
    assert sha(OUT/'sweep.py') == task['sweep_producer_sha256']
    assert sha(ROOT/task['physical_protocol_path']) == task['physical_protocol_sha256']
    PHYSICAL = read(ROOT/task['physical_protocol_path'])
    canonical.validate_protocol(PHYSICAL)
    sources = list(source_pool(PHYSICAL))
    old_records = numeric(rows(BASE/'diagnostic_results.csv'))
    cached = {(int(float(r['zenith_deg'])),r['ensemble_hash']):(i+2,r) for i,r in enumerate(old_records)}
    assert len(cached) == 1908
    old_context = {c['zenith_deg']:c for c in read(BASE/'channel_contexts.json')}
    began = time.perf_counter()
    for angle in task['angles_deg']:
        target = OUT/f'angle_{angle:02d}_candidates.csv'
        if target.exists(): raise FileExistsError('Do not repeat saved candidate work: '+str(target))
        start = time.perf_counter()
        context = old_context.get(angle)
        if context is None: context = clean(canonical.channel_context(angle,PHYSICAL))
        assert context['protocol_sha256'] == task['physical_protocol_sha256']
        assert context['numerical_status'] == PASS and context['numerical_experiment_accepted']
        save(f'angle_{angle:02d}_context.json',context)
        angle_records = []
        for source in sources:
            key = (angle,source['ensemble_hash'])
            if key in cached:
                row_number,record = cached[key]
                assert record['source_sha256'] == source['source_sha256']
                assert record['channel_protocol_sha256'] == task['physical_protocol_sha256']
                assert record['correlation_policy'] == task['correlation_policy']
                for k in ['VA','nu_raw','C','w']: assert float(record[k]).hex() == source[k].hex()
                record = decorate(record,source,angle,context,True,row_number)
            else:
                record = {k:source[k] for k in ['family','VA','VA_hex','nu_raw','nu_raw_hex','nu_repo',
                    'ensemble_hash','source_path','source_sha256','C','w','classification','C_hex','w_hex']}
                m = context['moments']
                record.update(channel_protocol_sha256=task['physical_protocol_sha256'], correlation_policy=task['correlation_policy'],
                    M0=m['M0'], E_sqrt_eta=m['mh'], E_eta=m['m1'], P0=m['P0'])
                try:
                    result = evaluator.evaluate(source,context,PHYSICAL)
                    decimals = result.pop('decimal')
                    record.update(result,numerical_status=PASS,reason='')
                    record.update({'decimal_'+k:v for k,v in decimals.items()})
                except ValueError as error:
                    # Preserve the failure; a higher-precision domain check never repairs Z.
                    t = m['mh']**2
                    noise = (m['m1']-t)*source['VA']+PHYSICAL['xi_ch']*m['m1']+PHYSICAL['xi_det']*m['M0']
                    try:
                        evaluator.components(source['VA'],t,noise/t,source['C'],source['w'],digits=160)
                        recheck = 'DOMAIN_VALID_AT160_REVIEW_REQUIRED'
                    except ValueError as second: recheck = str(second)
                    record.update(numerical_status='FAILED_NUMERICAL_VALIDATION',reason=str(error),
                        component_recheck160=recheck, K_raw=None,I_AB=None,beta_I_AB=None,chi_BE=None,
                        Z_manuscript_eq14=None,eta_f=t,xi_f=noise/t,N_effective=noise)
                record = decorate(record,source,angle,context)
            angle_records.append(record)
        write(target.name,angle_records)
        print(json.dumps(dict(angle=angle, rows=len(angle_records), reused=angle in old_context,
            failures=sum(r['numerical_status']!=PASS for r in angle_records),
            seconds=round(time.perf_counter()-start,3))),flush=True)
    combined = [r for a in task['angles_deg'] for r in numeric(rows(OUT/f'angle_{a:02d}_candidates.csv'))]
    write('diagnostic_skr_61_angles.csv',combined)
    canonical.validate_protocol(PHYSICAL)
    save('execution_summary.json',dict(result_scope=LABEL, angles=61, sources=212,
        unique_evaluations=len(combined), reused_evaluations=1908, new_evaluations=11024,
        reused_channel_contexts=9,new_channel_contexts=52,
        numerical_status_counts=dict(Counter(r['numerical_status'] for r in combined)),
        source_Cw_computations=0,source_generation_attempts=0,strict_Phase_B_ready=False,
        elapsed_seconds=time.perf_counter()-began))


if __name__ == '__main__':
    if sys.argv[1:] == ['--prepare']: prepare()
    elif sys.argv[1:] == ['--execute']: execute()
    else: raise SystemExit('Use --prepare once, then --execute once. No source jobs.')
