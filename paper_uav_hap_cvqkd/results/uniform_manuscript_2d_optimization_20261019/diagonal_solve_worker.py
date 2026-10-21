"""Same source worker and precision ladder, with an exact diagonal-system solve.

The original worker's two solve operands are diagonal square-root eigenvalue
matrices. No source equation, eigensolver, support or precision is changed.
"""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts import full_support_c4_worker as original
import mpmath as mp


def diagonal_solve(A,B):
    if A.rows!=A.cols or B.rows!=A.rows:
        raise ValueError('Incompatible diagonal solve dimensions')
    if any(A[i,j]!=0 for i in range(A.rows) for j in range(A.cols) if i!=j):
        raise ValueError('Diagonal shortcut requires exact off-diagonal zeros')
    if any(A[i,i]==0 for i in range(A.rows)):
        raise ValueError('Singular diagonal system')
    return mp.matrix([[B[i,j]/A[i,i] for j in range(B.cols)] for i in range(A.rows)])


if __name__=='__main__':
    original._lu_solve_matrix=diagonal_solve
    original.main()
