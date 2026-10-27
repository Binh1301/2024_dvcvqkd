"""Bounded float64 gate and saved-CPU checks; no arbitrary-precision C,w call."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

import mpmath as mp
import torch

from forensics import OUT, PRIOR, ROOT, decoded, read, save, sha


def diagnose():
    sys.path.insert(0,str(ROOT))
    from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config
    from scripts.run_exact_mb_test2 import ensemble_hash
    from src.modulation.qam256 import c4_orbit_indices
    from src.cvqkd.gram_moments import _sectors
    torch.set_num_threads(1)
    va=float.fromhex('0x1.9ffff84830112p+0')
    ensemble=make_ensemble(unconstrained_config(),'Uniform',0.,va)
    assert ensemble_hash(ensemble)==read(PRIOR/'source_job_preflight.json')['ensemble_hash']
    p,alpha=ensemble.probabilities[0],ensemble.amplitudes[0]
    assert torch.all(p==1/256) and abs(float(2*(p*alpha.abs().square()).sum())-va)<2e-12
    indices=c4_orbit_indices();pp=p[indices[:,0]];z=alpha[indices[:,0]]
    started=time.perf_counter()
    sectors=_sectors(pp,z)
    values=[torch.linalg.eigvalsh(matrix) for matrix in sectors]
    elapsed=time.perf_counter()-started
    gate=dict(minimum_eigenvalue=min(float(v.min()) for v in values),
        positive_modes_by_sector=[int((v>0).sum()) for v in values],
        max_eigenvalue=max(float(v.max()) for v in values),elapsed_seconds=elapsed,
        qualification='Float64 fallback-gate diagnostic only; NOT a full-support oracle or C,w evaluation')
    records=[]
    for record in read(OUT/'historical_process_observations.json'):
        raw=[]
        for value in decoded(record['output']):
            if isinstance(value,str) and any(line.lstrip().startswith('33676 ') for line in value.splitlines()):
                raw.append(value)
        if not raw: continue
        text=raw[-1]
        entry=dict(timestamp=record['timestamp'],execution_output_line=record['output_line'],
                   PID=33676,raw_process_output=text)
        worker_line=next(line for line in text.splitlines() if line.lstrip().startswith('33676 '))
        if 'UserModeTime' in text:
            match=re.search(r'^\s*33676\s+(\d+)(?:\s|$)',worker_line)
            if not match: match=re.search(r'AM\s+(\d+)\s+\d+\s*$',worker_line)
            assert match,worker_line
            entry['user_cpu_seconds']=int(match[1])/10_000_000
        elif 'ProcessName' in text:
            entry['total_cpu_seconds']=float(worker_line.split()[2])
        else: raise ValueError('Unknown historical CPU column units')
        records.append(entry)
    user=[r['user_cpu_seconds'] for r in records if 'user_cpu_seconds' in r]
    assert len(user)>=2 and user==sorted(user) and user[-1]>user[0]
    save('uniform_cpu_timeline.json',dict(worker_PID=33676,observations=records,
        user_cpu_increased=True,numerical_precision_stage='NOT_RECORDED',memory_peak='NOT_RECORDED',
        limitation='Saved Windows process snapshots prove CPU activity, not completion of a sector or convergence; no full profile exists for this attempt'))
    timings=[]
    for path in (ROOT/'results/uniform_positive_skr_manuscript43_20261023/new_exact_source/source_receipts').glob('*.json'):
        receipt=read(path)
        timings.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
            VA=receipt['VA'],elapsed_seconds=receipt['elapsed_seconds'],backend=receipt['child_backend']))
    worker=ROOT/'scripts/full_support_c4_worker.py'
    tree=ast.parse(worker.read_text(encoding='utf-8'))
    lines={node.name:node.lineno for node in tree.body if isinstance(node,ast.FunctionDef)}
    # A synthetic 3x3 identity check exercises the already validated diagonal solve only.
    path=ROOT/'results/uniform_manuscript_2d_optimization_20261019/diagonal_solve_worker.py'
    spec=importlib.util.spec_from_file_location('_preserved_diagonal_solve',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with mp.workdps(80):
        A=mp.diag([mp.mpf(1),mp.mpf(2),mp.mpf(4)])
        B=mp.matrix([[1,2,3],[4,5,6],[7,8,9]])
        X=module.diagonal_solve(A,B)
        assert A*X==B
        bad=A.copy();bad[0,1]=1
        try: module.diagonal_solve(bad,B)
        except ValueError: pass
        else: raise AssertionError('Non-diagonal input must be rejected')
    result=dict(status='CURRENTLY_VERIFIED_PASS',ensemble_hash=ensemble_hash(ensemble),VA_hex=va.hex(),
        backend=mp.libmp.BACKEND,mpmath_version=mp.__version__,float64_gate=gate,
        mathematical_full_rank_not_inferred_from_float64=True,worker_function_lines=lines,
        worker_sha256=sha(worker),planned_rows=[1050,1250,1450],
        static_eigendecomposition_calls_if_all_rows_completed=12,
        static_complex_exp_calls_if_all_rows_completed=3*4*64*64,
        exact_attempt_profile_available=False,exact_bottleneck_within_worker='UNKNOWN',
        saved_cpu_observations=len(records),last_recorded_user_cpu_seconds=user[-1],
        prior_python_timings=timings,synthetic_diagonal_identity_check='PASS_3_BY_3_80_DIGITS',
        expensive_Cw_calls=0,pilot_executed=False,full_sweep_executed=False)
    save('uniform_diagnostic_checks.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    diagnose()
