"""Same exact source kernel and precision ladder, standard Python MP backend."""
import json
import os
from pathlib import Path
import sys
import time

import source_job as initial
base=initial.base
OUT=initial.OUT


def main():
    va=float(sys.argv[1])
    if not .05<=va<=10:raise ValueError('VA outside authorized range')
    # Do not load, relocate or override the DLL rejected by Application Control.
    os.environ.pop('PYTHONPATH',None)
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    import mpmath
    if mpmath.libmp.BACKEND!='python':raise ValueError('Expected standard Python backend')
    base.torch.set_num_threads(1)
    initial.gram._fallback=initial.diagonal.fallback
    config=base.unconstrained_config()
    ensemble=base.make_ensemble(config,'Uniform',0.,va)
    settings=base.source_settings(config)
    identity=dict(schema='exact-mb-source-cache-v1',ensemble_hash=base.ensemble_hash(ensemble),
        nu_mb_raw_hex=0.0.hex(),nu_mb_repo_hex=0.0.hex(),V_A_hex=va.hex(),
        mb_convention=base.MB_CONVENTION,
        source_implementation={n:base.hashlib.sha256((base.ROOT/n).read_bytes()).hexdigest() for n in base.SOURCE_FILES},
        source_settings=settings)
    target=OUT/'new_exact_source'
    cache=target/'exact_source_cache';receipts=target/'source_receipts'
    cache.mkdir(parents=True,exist_ok=True);receipts.mkdir(exist_ok=True)
    key=base.json_hash(identity);path=cache/(key+'.json')
    attempt=target/('python_attempt_'+va.hex().replace('.','_')+'.json')
    record=dict(VA=va,backend='python',precision_ladder=settings['precision_ladder'],
        worker_timeout_s=3600,status='RUNNING',producer_sha256=initial.hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    def save():attempt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    save();began=time.perf_counter()
    try:
        if path.exists():raise FileExistsError('Do not overwrite completed source')
        moments=base.c4_gram_source_moments(ensemble,
            density_eigenvalue_tolerance=settings['density_eigenvalue_tolerance'],
            physicality_tolerance=settings['physicality_tolerance'])
        if base.ensemble_hash(ensemble)!=identity['ensemble_hash']:raise ValueError('Source ensemble mutated')
        diag=moments.diagnostics[0]
        payload=dict(**identity,cache_key=key,C=float(moments.coherent_correlation[0]),w=float(moments.w[0]),
            support_size=diag['support_size'],source_moment_route=diag['route'],cache_origin='FRESH_EXACT_EVALUATION')
        base.verify_source_payload(payload,settings)
        if min(payload['C'],payload['w'])<0 or payload['support_size']!=256:raise ValueError('Nonphysical source')
        evidence=base.clean(dict(VA=va,VA_hex=va.hex(),elapsed_seconds=time.perf_counter()-began,diagnostic=diag,
            child_backend=dict(backend='python',mpmath=mpmath.__version__),
            precision_ladder=settings['precision_ladder'],isolated_diagonal_solve_equivalence=True,
            additional_producers_sha256={str(p.relative_to(base.ROOT)):initial.hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [Path(__file__),initial.PRIOR/'source_uniform_diagonal.py',initial.PRIOR/'diagonal_solve_worker.py']},
            producer_sha256=record['producer_sha256']))
        path.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
        evidence['payload_file_sha256']=initial.hashlib.sha256(path.read_bytes()).hexdigest()
        (receipts/(identity['ensemble_hash']+'.json')).write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        record.update(status='CURRENTLY_VERIFIED_PASS',source_path=path.relative_to(base.ROOT).as_posix())
    except Exception as error:
        record.update(status='BLOCKED_BY_ENVIRONMENT' if 'timed out' in str(error) else 'FAILED',
            exception_type=type(error).__name__,reason=str(error))
        raise
    finally:
        record['elapsed_seconds']=time.perf_counter()-began;save()
    print(json.dumps(record),flush=True)


if __name__=='__main__':main()
