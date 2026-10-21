"""Numerical-only full-support Gram worker with installed FLINT matrix kernels.

Retains the repository source equations and 1050/1250/1450 ladder. Midpoint
arithmetic is not claimed to be rigorous interval certification. Eigenpairs
must pass independent residual and orthogonality checks before source use.
"""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import full_support_c4_worker as original
import mpmath as mp
sys.path.append(str(ROOT/'.venv-cert/Lib/site-packages'))
from flint import acb,acb_mat,ctx
from diagonal_solve_worker import diagonal_solve

Matrix=type(mp.eye(1))
original_mul=Matrix.__mul__
eigen_checks=[]


def to_flint(matrix):
    digits=mp.mp.dps+8
    return acb_mat([[acb(mp.nstr(mp.re(matrix[i,j]),digits),mp.nstr(mp.im(matrix[i,j]),digits))
                     for j in range(matrix.cols)] for i in range(matrix.rows)])


def from_flint(value):
    return mp.mpc(value.real.mid().str(mp.mp.dps+8,radius=False),
                  value.imag.mid().str(mp.mp.dps+8,radius=False))


def multiply(a,b):
    if not isinstance(b,Matrix) or a.cols!=b.rows or min(a.rows,a.cols,b.cols)<16:
        return original_mul(a,b)
    ctx.dps=mp.mp.dps+30
    value=to_flint(a)*to_flint(b)
    return mp.matrix([[from_flint(value[i,j]) for j in range(value.ncols())]
                      for i in range(value.nrows())])


def eigh(matrix):
    ctx.dps=mp.mp.dps+30
    eigenvalues,vectors=to_flint(matrix).eig(right=True,algorithm='approx')
    values=[from_flint(x) for x in eigenvalues]
    if max(abs(mp.im(x)) for x in values)>mp.mpf('1e-60'):
        raise ValueError('Hermitian eigenvalue has a nonnegligible imaginary part')
    order=sorted(range(len(values)),key=lambda k:mp.re(values[k]))
    U=mp.matrix(matrix.rows,matrix.cols)
    for j,index in enumerate(order):
        col=[from_flint(vectors[i,index]) for i in range(matrix.rows)]
        norm=mp.sqrt(mp.fsum(abs(x)**2 for x in col))
        for i,x in enumerate(col):
            U[i,j]=x/norm
    E=mp.matrix([mp.re(values[k]) for k in order])
    residual=mp.norm(matrix*U-U*mp.diag(E))/mp.norm(matrix)
    orthogonality=mp.norm(U.H*U-mp.eye(matrix.rows))
    if max(residual,orthogonality)>mp.mpf('1e-60'):
        raise ValueError('Eigenpair residual/orthogonality check failed')
    eigen_checks.append(dict(digits=mp.mp.dps,residual=mp.nstr(residual,20),
                             orthogonality=mp.nstr(orthogonality,20)))
    return E,U


if __name__=='__main__':
    Matrix.__mul__=multiply
    original._lu_solve_matrix=diagonal_solve
    mp.eighe=eigh
    original.main()
