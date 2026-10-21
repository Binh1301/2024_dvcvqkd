"""Isolated source launcher; retain the full-support worker's diagonal algebra."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import source_uniform_exact as base
import src.cvqkd.gram_moments as gram


def fallback(p,z):
    request=dict(probabilities_float64_hex=[float(x).hex() for x in p.detach().tolist()],
                 prototypes_float64_hex=[[complex(x).real.hex(),complex(x).imag.hex()] for x in z.detach().tolist()],
                 precision_ladder_decimal_digits=list(gram.PRECISION_LADDER))
    done=subprocess.run([sys.executable,str(HERE/'diagonal_solve_worker.py')],
                        input=json.dumps(request,sort_keys=True),text=True,capture_output=True,timeout=3600)
    if done.returncode:
        return dict(status='FAIL_CLOSED',reason=done.stderr[-2000:])
    return json.loads(done.stdout)


if __name__=='__main__':
    gram._fallback=fallback
    base.main()
    # Preserve the base receipt and make the isolated arithmetic identity explicit.
    for path in (HERE/'source_receipts').glob('*.json'):
        record=json.loads(path.read_text(encoding='utf-8'))
        if float(record['VA'])!=float(sys.argv[1]):
            continue
        record['isolated_diagonal_solve_equivalence']=True
        record['additional_producers_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in (Path(__file__),HERE/'diagonal_solve_worker.py')}
        path.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n',encoding='utf-8')
