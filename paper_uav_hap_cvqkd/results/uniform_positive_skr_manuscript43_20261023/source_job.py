"""Versioned Uniform source job through the preserved full-support/diagonal path."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import FunctionType

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
PRIOR=ROOT/'results/uniform_manuscript_2d_optimization_20261019'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(PRIOR))
import source_uniform_exact as base
import source_uniform_diagonal as diagonal
import src.cvqkd.gram_moments as gram


def main():
    va=float(sys.argv[1])
    if not .05<=va<=10:raise ValueError('Uniform source VA outside authorized range')
    target=OUT/'new_exact_source';target.mkdir(exist_ok=True)
    gram._fallback=diagonal.fallback
    task=FunctionType(base.main.__code__,{**base.main.__globals__,'OUT':target,'__file__':str(Path(__file__))},
        base.main.__name__,base.main.__defaults__)
    original_out=base.OUT
    task()
    assert base.OUT==original_out
    for path in (target/'source_receipts').glob('*.json'):
        record=json.loads(path.read_text(encoding='utf-8'))
        if float(record['VA'])!=va:continue
        record['isolated_diagonal_solve_equivalence']=True
        record['historical_files_modified']=False
        record['additional_producers_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__),PRIOR/'source_uniform_exact.py',PRIOR/'source_uniform_diagonal.py',PRIOR/'diagonal_solve_worker.py']}
        path.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n',encoding='utf-8')


if __name__=='__main__':main()
