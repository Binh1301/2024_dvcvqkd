"""Isolated, checkpointed C4 Gram diagnostics; controlled runs require authorization."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import mpmath as mp
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / 'results/phaseE_Cw_fock_gram_repo_comparison_20261026'
ALGORITHM = 'E2_exact_C4_overlap_sector_row_column_scaling_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value, interrupt_before_replace=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.pending')
    data = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    with pending.open('wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if interrupt_before_replace:
        raise InterruptedError('Injected interruption before atomic replacement')
    os.replace(pending, path)


def prior_module(name):
    spec = importlib.util.spec_from_file_location('phaseE2_' + name, PRIOR / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def input_source(path):
    with np.load(path, allow_pickle=False) as data:
        p, alpha = data['p'].copy(), data['alpha'].copy()
    if p.dtype != np.float64 or alpha.dtype != np.complex128:
        raise ValueError('Require the unchanged binary64 ensemble arrays')
    if len(p) != len(alpha) or not np.isfinite(p).all() or not np.isfinite(alpha).all():
        raise ValueError('Invalid ensemble')
    if not np.all(p > 0) or abs(p.sum() - 1) > 1e-12 or len(set(alpha)) != len(p):
        raise ValueError('Invalid probabilities or duplicate amplitudes')
    groups = prior_module('independent_gram_Cw').orbits_from_arrays(p, alpha)
    return p, alpha, groups


def identity(path, digits, sector):
    p, alpha, groups = input_source(path)
    p_hash = hashlib.sha256(p.tobytes()).hexdigest()
    a_hash = hashlib.sha256(alpha.tobytes()).hexdigest()
    canonical = next((row['ensemble_hash'] for row in cw_validations()
                      if row['PMF_sha256'] == p_hash and row['alpha_sha256'] == a_hash), None)
    return dict(algorithm=ALGORITHM, input_sha256=sha(path),
                probability_sha256=p_hash, amplitude_sha256=a_hash, canonical_ensemble_hash=canonical,
                producer_sha256=sha(__file__),
                prior_gram_sha256=sha(PRIOR / 'independent_gram_Cw.py'),
                mpmath_version=mp.__version__, python_version=sys.version,
                digits=digits, sector=sector, matrix_dimension=len(groups),
                source_size=len(p), Fock_cutoff=None, route='weighted_Gram_exact_C4',
                floor_policy='10**(-digits+20); diagnostic, never mathematical rank',
                tolerance_policy='relative Frobenius residual/reconstruction/orthogonality <=10**(-digits+10)')


def cw_validations():
    return read(PRIOR / 'input_validation.json')


def scale(matrix, rows=None, columns=None):
    return mp.matrix([[matrix[i, j] * (rows[i] if rows is not None else 1) *
                       (columns[j] if columns is not None else 1)
                       for j in range(matrix.cols)] for i in range(matrix.rows)])


def gram_sector(p, alpha, groups, sector):
    """Exactly F_s^H H F_s using C4 covariance, without building the full H."""
    weights = [mp.mpf(float(p[g[0]])) for g in groups]
    z = [mp.mpc(float(alpha[g[0]].real), float(alpha[g[0]].imag)) for g in groups]
    size = len(groups)
    block = mp.matrix(size)
    for i in range(size):
        for j in range(size):
            block[i, j] = mp.sqrt(weights[i] * weights[j]) * mp.fsum(
                mp.j**(sector * t) * mp.exp(-(abs(z[i])**2 + abs(z[j])**2) / 2 +
                                           mp.conj(z[i]) * mp.j**t * z[j]) for t in range(4))
    error = mp.norm(block - block.H) / mp.norm(block)
    if error > mp.power(10, -mp.mp.dps + 10):
        raise ArithmeticError('Unexpected C4 Hermiticity error')
    # Same roundoff symmetrization as Phase E; the exact block is Hermitian.
    return (block + block.H) / 2, error


def checks(block, values, vectors):
    size = block.rows
    if block.cols != size or len(values) != size or vectors.rows != size or vectors.cols != size:
        raise ValueError('Spectrum dimension mismatch')
    if not all(mp.isfinite(x) for x in list(block) + list(vectors) + list(values)):
        raise ValueError('Nonfinite spectrum')
    if any(values[i] > values[i + 1] for i in range(size - 1)):
        raise ValueError('Unsorted spectrum')
    norm = mp.norm(block)
    residual = block * vectors - scale(vectors, columns=values)
    eigenpair = [mp.sqrt(mp.fsum(abs(residual[i, j])**2 for i in range(size))) for j in range(size)]
    reconstruction = mp.norm(block - scale(vectors, columns=values) * vectors.H) / norm
    orthogonality = mp.norm(vectors.H * vectors - mp.eye(size))
    relative = mp.norm(residual) / norm
    hermitian = mp.norm(block - block.H) / norm
    tolerance = mp.power(10, -mp.mp.dps + 10)
    if max(relative, reconstruction, orthogonality, hermitian) > tolerance:
        raise ArithmeticError('Sector consistency checks failed')
    st = lambda x: mp.nstr(x, mp.mp.dps + 10)
    nominal_error = mp.norm(residual) + tolerance * norm
    retained = [x for x in values if x > mp.power(10, -mp.mp.dps + 20)]
    return dict(eigenpair_absolute_residuals=[st(x) for x in eigenpair],
                eigenpair_residual_over_abs_lambda=[st(eigenpair[j] / abs(values[j]))
                    if values[j] else None for j in range(size)],
                relative_Frobenius_residual=st(relative), reconstruction_error=st(reconstruction),
                orthogonality_error=st(orthogonality), Hermitian_error=st(hermitian),
                matrix_Frobenius_norm=st(norm), tolerance=st(tolerance),
                minimum_eigenvalue=st(min(values)), maximum_eigenvalue=st(max(values)),
                minimum_retained_eigenvalue=st(min(retained)) if retained else None,
                retained_condition=st(max(retained) / min(retained)) if retained else None,
                minimum_lambda_over_nominal_error=st(min(values) / nominal_error),
                nominal_error_status='HEURISTIC_ROUNDING_ALLOWANCE_PLUS_MEASURED_RESIDUAL; NOT_AN_ENCLOSURE',
                effective_rank=sum(x > mp.power(10, -mp.mp.dps + 20) for x in values),
                positive_count=sum(x > 0 for x in values),
                numerical_checks='CURRENTLY_VERIFIED_PASS', rigorous_roundoff_enclosure=False)


def pack(matrix):
    return [[[mp.nstr(mp.re(matrix[i, j]), mp.mp.dps + 10),
              mp.nstr(mp.im(matrix[i, j]), mp.mp.dps + 10)]
             for j in range(matrix.cols)] for i in range(matrix.rows)]


def unpack(data):
    return mp.matrix([[mp.mpc(*cell) for cell in row] for row in data])


def load_checkpoint(path, expected):
    receipt = read(path)
    if not receipt.get('complete') or receipt.get('identity') != expected:
        raise ValueError('Incomplete or incompatible checkpoint')
    if receipt.get('payload_sha256') != digest(receipt['payload']):
        raise ValueError('Corrupt checkpoint payload')
    with mp.workdps(expected['digits']):
        payload = receipt['payload']
        block, vectors = unpack(payload['matrix']), unpack(payload['eigenvectors'])
        values = [mp.mpf(x) for x in payload['eigenvalues']]
        checks(block, values, vectors)
    return receipt


def checkpoint_sector(path, expected, builder, interrupt_before_replace=False):
    path = Path(path)
    if path.exists():
        return load_checkpoint(path, expected), True
    with mp.workdps(expected['digits']):
        wall, cpu = time.perf_counter(), time.process_time()
        block, construction_error = builder()
        build_wall, build_cpu = time.perf_counter() - wall, time.process_time() - cpu
        eig_wall, eig_cpu = time.perf_counter(), time.process_time()
        values, vectors = mp.eighe(block)
        eig_seconds, eig_cpu_seconds = time.perf_counter() - eig_wall, time.process_time() - eig_cpu
        diagnostics = checks(block, values, vectors)
        payload = dict(matrix=pack(block), eigenvalues=[mp.nstr(x, mp.mp.dps + 10) for x in values],
                       eigenvectors=pack(vectors), diagnostics=diagnostics,
                       pre_symmetrization_Hermitian_error=mp.nstr(construction_error, mp.mp.dps + 10),
                       timing=dict(build_wall_seconds=build_wall, build_CPU_seconds=build_cpu,
                                   eig_wall_seconds=eig_seconds, eig_CPU_seconds=eig_cpu_seconds,
                                   total_wall_seconds=time.perf_counter() - wall,
                                   total_CPU_seconds=time.process_time() - cpu),
                       C_contribution=None, w_contribution=None,
                       moment_status='NOT_RUN_REQUIRES_ALL_FOUR_SECTORS')
        receipt = dict(complete=True, identity=expected, payload=payload,
                       payload_sha256=digest(payload),
                       completion_scope='VALIDATED_NUMERICAL_SECTOR; NOT_A_FULL_SUPPORT_CERTIFICATE')
        atomic_json(path, receipt, interrupt_before_replace)
        # Parse at the declared precision and recheck the serialized data.
        load_checkpoint(path, expected)
        return receipt, False


def sector_job(input_path, digits, sector, directory):
    p, alpha, groups = input_source(input_path)
    if not 0 <= sector < 4 or digits < 40:
        raise ValueError('Invalid precision or sector')
    expected = identity(input_path, digits, sector)
    return checkpoint_sector(Path(directory) / f'sector_{sector}.json', expected,
                             lambda: gram_sector(p, alpha, groups, sector))


def moment_job(input_path, digits, directory):
    """Same Phase E Gram C,w, with diagonal products implemented as scaling."""
    p, alpha, groups = input_source(input_path)
    wall, cpu = time.perf_counter(), time.process_time()
    with mp.workdps(digits):
        receipts = [load_checkpoint(Path(directory) / f'sector_{s}.json', identity(input_path, digits, s))
                    for s in range(4)]
        result_path = Path(directory) / 'moments.json'
        checkpoint_hashes = [sha(Path(directory) / f'sector_{s}.json') for s in range(4)]
        if result_path.exists():
            saved = read(result_path)
            if (saved['input_sha256'], saved['producer_sha256'], saved['digits'],
                saved['sector_checkpoint_sha256']) != (sha(input_path), sha(__file__), digits, checkpoint_hashes):
                raise ValueError('Incompatible moment checkpoint')
            if saved.get('result_sha256') != digest({k: v for k, v in saved.items() if k != 'result_sha256'}):
                raise ValueError('Corrupt moment checkpoint')
            return saved
        floor = mp.power(10, -digits + 20)
        values, vectors, blocks = [], [], []
        for receipt in receipts:
            data = receipt['payload']; raw = [mp.mpf(x) for x in data['eigenvalues']]
            keep = [j for j, value in enumerate(raw) if value > floor]
            U = unpack(data['eigenvectors'])
            values.append([raw[j] for j in keep])
            vectors.append(mp.matrix([[U[i, j] for j in keep] for i in range(U.rows)]))
            blocks.append(unpack(data['matrix']))
        weights = [mp.mpf(float(p[g[0]])) for g in groups]
        z = [mp.mpc(float(alpha[g[0]].real), float(alpha[g[0]].imag)) for g in groups]
        q = [scale(vectors[s].H, rows=[mp.sqrt(x) for x in values[s]],
                   columns=[1 / (2 * mp.sqrt(x)) for x in weights]) for s in range(4)]
        C_sector, u = [], []
        for out in range(4):
            inp = (out - 1) % 4
            # D_alpha F_(s-1) = F_s diag(z), hence L_s = H_s diag(z).
            local = vectors[out].H * scale(blocks[out], columns=z) * vectors[inp]
            A = scale(local, rows=[1 / mp.sqrt(x) for x in values[out]],
                      columns=[1 / mp.sqrt(x) for x in values[inp]])
            C_sector.append(mp.fsum(mp.sqrt(values[out][i] * values[inp][j]) * abs(A[i, j])**2
                                   for i in range(A.rows) for j in range(A.cols)))
            u.append(scale(A, rows=[mp.sqrt(x) for x in values[out]],
                           columns=[1 / mp.sqrt(x) for x in values[inp]]) * q[inp])
        direct, correction = mp.mpf(0), mp.mpf(0)
        residual_sector = [mp.mpf(0) for _ in range(4)]
        for k, weight in enumerate(weights):
            mean = mp.fsum(mp.conj(q[s][i, k]) * u[s][i, k]
                           for s in range(4) for i in range(q[s].rows))
            first = mp.fsum(abs(u[s][i, k])**2 for s in range(4) for i in range(q[s].rows))
            norm = mp.fsum(abs(q[s][i, k])**2 for s in range(4) for i in range(q[s].rows))
            direct += 4 * weight * (first - abs(mean)**2)
            correction += 4 * weight * (1 - norm) * abs(mean)**2
            for s in range(4):
                residual_sector[s] += 4 * weight * mp.fsum(
                    abs(u[s][i, k] - q[s][i, k] * mean)**2 for i in range(q[s].rows))
        stable = mp.fsum(residual_sector) + correction
        st = lambda x: mp.nstr(x, digits + 10)
        if abs(direct - stable) > mp.power(10, -digits + 15) * max(1, abs(direct)):
            raise ArithmeticError('Direct/residual identity failed')
        result = dict(C=st(mp.fsum(C_sector)), w_direct=st(direct), w_residual=st(stable),
                      C_contributions_by_output_sector=[st(x) for x in C_sector],
                      w_residual_norm_contributions_by_output_sector=[st(x) for x in residual_sector],
                      w_coherent_norm_correction=st(correction),
                      direct_residual_difference=st(direct - stable),
                      effective_rank=sum(len(x) for x in values), source_size=len(p),
                      input_sha256=sha(input_path), producer_sha256=sha(__file__), digits=digits,
                      sector_checkpoint_sha256=checkpoint_hashes,
                      wall_seconds=time.perf_counter() - wall, CPU_seconds=time.process_time() - cpu,
                      result_scope='DIAGNOSTIC_ONLY', convergence_certified=False)
        result['result_sha256'] = digest(result)
        atomic_json(result_path, result)
        return result


def controlled_run(plan_path, authorization_path):
    plan = read(plan_path)
    authorization = read(authorization_path)
    if authorization.get('decision') != 'USER_APPROVED_SINGLE_SOURCE_FULL_SUPPORT_RUN' or \
            authorization.get('plan_sha256') != sha(plan_path):
        raise PermissionError('A separate explicit user authorization bound to this plan is required')
    if plan['producer_sha256'] != sha(__file__) or sha(ROOT / plan['input_path']) != plan['input_sha256']:
        raise ValueError('Plan producer/source identity changed')
    monitor = prior_module('run_comparison')
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='1',
                       PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
                       PYTHONPATH=str(ROOT / '.venv/Lib/site-packages'))
    directory = OUT / plan['checkpoint_root']; directory.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    receipts_path = directory / 'execution_receipts.json'
    receipts = read(receipts_path) if receipts_path.exists() else []
    if any(r.get('plan_sha256') != sha(plan_path) for r in receipts):
        raise ValueError('Execution receipt plan mismatch')
    prior_wall = sum(r['elapsed_seconds'] for r in receipts)
    executable = getattr(sys, '_base_executable', sys.executable)
    for digits in plan['precision_levels']:
        target = directory / f'dps_{digits}'
        for stage in [0, 1, 2, 3, 'moments']:
            request = dict(input=str(ROOT / plan['input_path']), digits=digits,
                           directory=str(target), stage=stage, plan_sha256=sha(plan_path))
            request_path = directory / f'request_{digits}_{stage}.json'
            atomic_json(request_path, request)
            budget = min(plan['per_stage_wall_seconds'], plan['maximum_total_wall_seconds'] -
                         (time.monotonic() - start) - prior_wall)
            if budget <= 0:
                raise TimeoutError('Total controlled-run budget exhausted')
            then = time.monotonic(); peak = 0; status = 'COMPLETED'
            with (directory / f'worker_{digits}_{stage}.log').open('a', encoding='utf-8') as log:
                process = subprocess.Popen([executable, '-X', 'utf8', '-B', __file__, '--worker', str(request_path)],
                    cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                try:
                    while process.poll() is None:
                        if time.monotonic() - then >= budget:
                            status = 'INCONCLUSIVE_TIMEOUT'; break
                        try:
                            peak = max(peak, monitor.working_set(process.pid))
                        except OSError:
                            if process.poll() is not None:
                                break
                            status = 'BLOCKED_MEMORY_MONITOR'; break
                        if peak > plan['maximum_worker_working_set_MiB'] * 1024**2:
                            status = 'INCONCLUSIVE_MEMORY_LIMIT'; break
                        time.sleep(.1)
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
            if process.returncode and status == 'COMPLETED':
                status = 'FAILED_WORKER'
            if status == 'COMPLETED' and stage != 'moments':
                sector_result = load_checkpoint(target / f'sector_{stage}.json',
                                                identity(request['input'], digits, stage))
                diagnostics = sector_result['payload']['diagnostics']
                if diagnostics['effective_rank'] != sector_result['identity']['matrix_dimension']:
                    status = 'INCONCLUSIVE_UNRESOLVED_SUPPORT'
                if mp.mpf(diagnostics['minimum_lambda_over_nominal_error']) < mp.mpf('1e20'):
                    status = 'INCONCLUSIVE_SPECTRAL_MARGIN'
            receipts.append(dict(digits=digits, stage=stage, status=status, returncode=process.returncode,
                                 elapsed_seconds=time.monotonic() - then,
                                 observed_peak_worker_MiB=peak / 1024**2, worker_executable=executable,
                                 plan_sha256=sha(plan_path)))
            atomic_json(directory / 'execution_receipts.json', receipts)
            if status != 'COMPLETED':
                raise RuntimeError('Stopped; validated earlier sectors retained. No automatic retry.')
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker')
    parser.add_argument('--controlled-run')
    parser.add_argument('--authorization-file')
    args = parser.parse_args()
    if args.worker:
        request = read(args.worker)
        if request['stage'] == 'moments':
            result = moment_job(request['input'], request['digits'], request['directory'])
            print(json.dumps(dict(stage='moments', effective_rank=result['effective_rank'])))
        else:
            result, reused = sector_job(request['input'], request['digits'], request['stage'], request['directory'])
            print(json.dumps(dict(stage=request['stage'], reused=reused,
                                  checks=result['payload']['diagnostics']['numerical_checks'])))
    elif args.controlled_run and args.authorization_file:
        controlled_run(args.controlled_run, args.authorization_file)
    else:
        parser.error('Choose a worker request or a separately authorized controlled run')


if __name__ == '__main__':
    main()
