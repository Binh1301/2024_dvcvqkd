"""One explicitly requested retry; reuse the validated source and Job paths."""
import time
START = time.monotonic()
import argparse
import copy
import datetime
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_full_51_grid as batch

BASE = batch.OUT
OUT = BASE.parent / 'grid_timeout_retry_1'
batch.OUT, batch.CACHE = OUT, OUT / 'exact_source_cache'
TOTAL, RESERVE = 7200., 1800.


def candidate():
    old = batch.read(BASE / 'batch_checkpoint.json')
    assert old['controller_pid'] == 0 and old['status'] == 'ALL_31_QUEUE_ITEMS_PROCESSED'
    rows = [r for r in old['queue'] if r['status'] == 'TIMEOUT']
    assert len(rows) == 1 and (rows[0]['nu_raw'], rows[0]['V_A']) == (.25, 3.5)
    row = copy.deepcopy(rows[0])
    row.update(index=1, previous_batch_index=28, previous_attempt_number=1,
               attempt_number=0, status='PENDING', started_UTC='', finished_UTC='',
               C='', w='', source_validation='NOT_RUN', source_path='', SKR_status='PENDING',
               worker_cleanup='NOT_RUN', error='', supervision_receipts=[], CPU_seconds=0.)
    assert row['nu_raw_hex'] == .25.hex() and row['V_A_hex'] == 3.5.hex()
    return old, row


def supervise(row, phase, deadline):
    limit = min(batch.SOURCE_OUTER if phase == 'source' else batch.POST_OUTER,
                deadline - time.monotonic() - RESERVE)
    assert limit > 0
    command = [sys.executable, '-B', '-X', 'utf8', '-u', str(Path(__file__).resolve()), '--child', phase]
    stage = batch.stage_path(row)
    with (stage / (phase + '.log')).open('w', encoding='utf-8') as log:
        receipt = batch.original.checked_supervised_process(command, limit, log)
    batch.atomic_json(stage / (phase + '_supervision.json'), receipt)
    row['supervision_receipts'].append(receipt)
    assert batch.safety_ok(receipt), 'ACTUAL_WORKER_SAFETY_FAILED'
    return receipt


def compare_saved_results(row):
    fresh = batch.read(batch.stage_path(row) / 'validated_objectives.json')
    baseline = batch.read(BASE / 'objective_checkpoint.json')
    assert len(fresh) == len(baseline) == 26
    expanded, comparisons = [], []
    for entry, new in zip(baseline, fresh):
        assert entry['L_km'] == new['L_km'] and len(entry['rows']) == 181
        assert new['SKR'] == new['beta_I_AB'] - new['chi_BE'] and new['status'] == 'PASS'
        assert batch.saved.pair(new['nu_raw'], new['V_A']) not in {
            batch.saved.pair(r['nu_raw'], r['V_A']) for r in entry['rows']}
        previous = batch.grid.audit.ranked(entry['rows'])[0]
        rows = entry['rows'] + [new]
        best = batch.grid.audit.ranked(rows)[0]
        comparisons.append(dict(L_km=entry['L_km'], probe_SKR=new['SKR'],
            previous_best_SKR=previous['SKR'], best_SKR=best['SKR'],
            nu_raw=best['nu_raw'], V_A=best['V_A'], improved=best['SKR'] > previous['SKR']))
        expanded.append({**entry, 'rows': rows})
    batch.atomic_json(OUT / 'objective_checkpoint.json', expanded)
    batch.atomic_csv(OUT / 'best_vs_catalog181_26_distances.csv', comparisons)
    return comparisons


def run():
    assert not OUT.exists(), 'One attempt only; existing retry output must not be overwritten'
    old, row = candidate()
    origin = datetime.datetime.now(datetime.timezone.utc)
    remaining = (datetime.datetime.fromisoformat(old['authorization']['deadline_UTC']) - origin).total_seconds()
    deadline = min(START + TOTAL, time.monotonic() + remaining)
    assert deadline - time.monotonic() >= batch.SOURCE_OUTER + batch.POST_OUTER + RESERVE
    bank = batch.cache_bank(batch.saved.source.unconstrained_config())
    assert len(bank) == 181 and batch.saved.pair(.25, 3.5) not in bank
    manifest = batch.read(BASE / 'protected_input_manifest.json')
    for path in BASE.rglob('*'):
        if path.is_file():
            manifest[path.relative_to(ROOT).as_posix()] = batch.grid.audit.digest(path)
    manifest[Path(__file__).relative_to(ROOT).as_posix()] = batch.grid.audit.digest(Path(__file__))
    assert all(batch.grid.audit.digest(ROOT / p) == h for p, h in manifest.items())
    OUT.mkdir(); batch.CACHE.mkdir()
    stage = batch.stage_path(row); stage.mkdir()
    assert len(str(batch.CACHE / (row['source_cache_key'] + '.json.tmp'))) <= 247
    batch.atomic_json(OUT / 'protected_input_manifest.json', manifest)
    batch.atomic_json(stage / 'protected_input_manifest.json', manifest)
    batch.atomic_json(stage / 'confirmed_candidate.json', {'original_source_identity': row['original_source_identity']})
    batch.atomic_json(stage / 'execution_authorization.json', dict(maximum_attempts=1, source_cache_key=row['source_cache_key']))
    state = dict(status='RUNTIME_PREFLIGHT', controller_pid=os.getpid(), queue=[row], AP_attempts=0,
        authorization=dict(user_request='chay lai not cai time out', maximum_attempts=1,
            original_internal_timeout_seconds=3600, total_wall_cap_seconds=TOTAL, reserve_seconds=RESERVE,
            no_further_retry=True, previous_batch=BASE.relative_to(ROOT).as_posix(),
            deadline_UTC=(origin + datetime.timedelta(seconds=deadline-time.monotonic())).isoformat()))
    batch.persist(state)
    lease = batch.prior.safe.AwakeOnAC()
    try:
        with lease:
            samples = []
            for _ in range(3):
                samples.append(lease.power.read()); time.sleep(.25)
            assert all(batch.prior.safe.safe_power(p) for p in samples)
            state['AC_samples'] = samples
            batch.verify()
            row.update(status='RUNNING', started_UTC=batch.utc(), attempt_number=1)
            state.update(status='RUNNING_ONE_EXPLICIT_RETRY', AP_attempts=1)
            batch.atomic_json(stage / 'source_attempt_started.json', {'attempt_number': 1})
            batch.persist(state)
            print('SOURCE_STARTED: (.25,3.5); ONE attempt; internal3600s unchanged', flush=True)
            receipt = supervise(row, 'source', deadline)
            result = batch.read(stage / 'source_result.json') if (stage / 'source_result.json').exists() else {}
            if receipt['deadline_exceeded'] or result.get('status') == 'TIMEOUT_INTERNAL_EVALUATOR':
                row.update(status='TIMEOUT', SKR_status='NOT_RUN', error=result.get('error', 'SUPERVISOR_TIMEOUT'))
            else:
                assert receipt['returncode'] == 0 and result.get('status') == 'COMPLETED_EXACT', result
                batch.validate_source(row); batch.persist(state)
                receipt = supervise(row, 'objectives', deadline)
                assert receipt['returncode'] == 0 and not receipt['deadline_exceeded']
                comparisons = compare_saved_results(row)
                row.update(status='VALIDATED_SUCCESS', SKR_status='VALIDATED_26_DISTANCES')
                state.update(source_catalog_size=182, grid_complete_points=51,
                    improved_distances=[r['L_km'] for r in comparisons if r['improved']], AO_runs=0)
    except BaseException as error:
        row.update(status='ABORTED', error=f'{type(error).__name__}: {error}')
    finally:
        try:
            protected = batch.verify()
        except BaseException as error:
            protected = None
            row.update(status='ABORTED', error=f'FINAL_PROVENANCE_FAILURE: {error}')
        state.update(status=row['status'], controller_pid=0, protected_files=protected,
            outer_Sleep_lease=lease.receipt, wall_seconds=time.monotonic()-START,
            scientific_methods_changed=False, continuous_optimum_certified=False)
        row.update(finished_UTC=batch.utc(),
            CPU_seconds=sum(r.get('aggregate_cpu_seconds', 0) for r in row['supervision_receipts']),
            worker_cleanup='VERIFIED_EMPTY_CLOSED' if row['supervision_receipts'] and all(
                batch.safety_ok(r) for r in row['supervision_receipts']) else 'UNVERIFIED_OR_NOT_RUN')
        batch.persist(state)
        batch.atomic_json(OUT / 'final_report.json', state)
        print(batch.original.prep.storage.checked_json(state), flush=True)
    return 0 if row['status'] == 'VALIDATED_SUCCESS' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--approved-one-retry', action='store_true')
    parser.add_argument('--child', choices=['source', 'objectives'])
    args = parser.parse_args()
    if args.child:
        raise SystemExit(batch.source_child(1) if args.child == 'source' else batch.objective_child(1))
    if not args.approved_one_retry:
        raise SystemExit('AP NOT_RUN: explicit single retry authorization required')
    raise SystemExit(run())
