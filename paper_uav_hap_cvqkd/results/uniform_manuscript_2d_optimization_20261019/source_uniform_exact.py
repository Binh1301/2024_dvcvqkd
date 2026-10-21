"""One exact Uniform source through the unchanged full-support repository path."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.exact_cache_provenance import MB_CONVENTION, SOURCE_FILES, json_hash, source_settings, verify_source_payload
from scripts.run_exact_mb_test2 import ensemble_hash
from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config
from src.cvqkd.gram_moments import c4_gram_source_moments
import torch


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return value.hex()
    return value


def main():
    va = float(sys.argv[1])
    if not math.isfinite(va) or va <= 0:
        raise ValueError('VA must be positive and finite')
    torch.set_num_threads(1)
    acceleration = Path(r'C:\Users\HP\AppData\Local\Temp\codex-uniform-20261019-gmpy2')
    os.environ['PYTHONPATH'] = str(acceleration)
    backend = subprocess.check_output([sys.executable,'-c',
        'import mpmath,gmpy2,json;print(json.dumps(dict(backend=mpmath.libmp.BACKEND,mpmath=mpmath.__version__,gmpy2=gmpy2.version())))'],text=True).strip()
    config = unconstrained_config()
    ensemble = make_ensemble(config,'Uniform',0.,va)
    settings = source_settings(config)
    identity = dict(schema='exact-mb-source-cache-v1',ensemble_hash=ensemble_hash(ensemble),
                    nu_mb_raw_hex=0.0.hex(),nu_mb_repo_hex=0.0.hex(),V_A_hex=va.hex(),
                    mb_convention=MB_CONVENTION,
                    source_implementation={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCE_FILES},
                    source_settings=settings)
    key = json_hash(identity)
    cache = OUT/'exact_source_cache'
    receipts = OUT/'source_receipts'
    cache.mkdir(exist_ok=True)
    receipts.mkdir(exist_ok=True)
    path, receipt = cache/(key+'.json'), receipts/(identity['ensemble_hash']+'.json')
    if path.exists():
        payload = json.loads(path.read_text(encoding='utf-8'))
        verify_source_payload(payload,settings)
        if not receipt.is_file():
            raise ValueError('Missing source convergence receipt')
    else:
        before = ensemble_hash(ensemble)
        began = time.perf_counter()
        moments = c4_gram_source_moments(ensemble,
                    density_eigenvalue_tolerance=settings['density_eigenvalue_tolerance'],
                    physicality_tolerance=settings['physicality_tolerance'])
        if ensemble_hash(ensemble)!=before:
            raise ValueError('Source evaluator mutated ensemble')
        diag = moments.diagnostics[0]
        payload = dict(**identity,cache_key=key,C=float(moments.coherent_correlation[0]),
                       w=float(moments.w[0]),support_size=diag['support_size'],
                       source_moment_route=diag['route'],cache_origin='FRESH_EXACT_EVALUATION')
        verify_source_payload(payload,settings)
        if payload['C']<0 or payload['w']<0 or payload['support_size']!=256:
            raise ValueError('Nonphysical or incomplete source')
        evidence = clean(dict(VA=va,VA_hex=va.hex(),elapsed_seconds=time.perf_counter()-began,
                             payload_sha256=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),
                             diagnostic=diag,child_backend=json.loads(backend),
                             producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             precision_ladder=settings['precision_ladder']))
        receipt.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        path.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(source_path=str(path.relative_to(ROOT)),receipt_path=str(receipt.relative_to(ROOT)))))


if __name__=='__main__':
    main()
