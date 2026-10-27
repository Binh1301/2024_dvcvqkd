"""Compare the isolated diagonal solve with the original arbitrary-precision LU."""
import hashlib
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'results/uniform_manuscript_2d_optimization_20261019'))
import diagonal_solve_worker as d
mp=d.mp


def main():
    records=[]
    for digits in [1050,1250,1450]:
        with mp.workdps(digits):
            A=mp.diag([mp.mpf(1),mp.mpf('1e-50'),mp.mpf('1e-250'),mp.mpf('1e-500')])
            B=mp.matrix([[mp.mpc(mp.mpf(i+1)/(j+3),mp.mpf(j+1)/(i+7)) for j in range(4)] for i in range(4)])
            fast=d.diagonal_solve(A,B);reference=d.original._lu_solve_matrix(A,B)
            error=max(abs(fast[i,j]-reference[i,j])/max(mp.mpf(1),abs(reference[i,j])) for i in range(4) for j in range(4))
            assert error<mp.power(10,-digits+20)
            records.append(dict(digits=digits,maximum_relative_error=mp.nstr(error,25)))
    for A in [mp.matrix([[1,1],[0,2]]),mp.diag([1,0])]:
        try:d.diagonal_solve(A,mp.eye(2))
        except ValueError:pass
        else:raise AssertionError('Invalid diagonal operand accepted')
    result=dict(status='CURRENTLY_VERIFIED_PASS',
        comparison='Original LU vs exact diagonal division, complex RHS and positive spectrum spanning 500 decades',
        records=records,invalid_operands_rejected=True,
        worker_sha256=hashlib.sha256(Path(d.__file__).read_bytes()).hexdigest(),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),source_convergence_not_implied=True)
    (OUT/'source_diagonal_equivalence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('CURRENTLY_VERIFIED_PASS: 3 precisions and invalid diagonal guards')


if __name__=='__main__':main()
