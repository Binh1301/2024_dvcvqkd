"""Small numerical checks; no new source computation or optimization."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
from scripts.optimize_uniform_manuscript_2d import uniform_mi_2d
from scripts.recheck_manuscript_homodyne_noise import mi_gh
from diagonal_solve_worker import diagonal_solve
from scripts.full_support_c4_worker import _lu_solve_matrix
import mpmath as mp
import numpy as np

checks=[]
for digits in (50,1050):
    with mp.workdps(digits):
        A=mp.diag([mp.mpf('1e-20'),mp.mpf('1.23456789'),mp.mpf('8e10')])
        B=mp.matrix([[mp.mpf(i+j+1)/7 for j in range(3)] for i in range(3)])
        residual=mp.norm(diagonal_solve(A,B)-_lu_solve_matrix(A,B))/mp.norm(_lu_solve_matrix(A,B))
        assert residual<mp.mpf(10)**(-digits+5)
        assert mp.norm(A*diagonal_solve(A,B)-B)<mp.mpf(10)**(-digits+5)
        checks.append(dict(check='diagonal_solve_'+str(digits),residual=mp.nstr(residual,12)))
try:
    diagonal_solve(mp.matrix([[1,1],[0,1]]),mp.eye(2))
    raise AssertionError('Nondiagonal matrix was accepted')
except ValueError:
    checks.append(dict(check='reject_nondiagonal',residual=0))
for va in (.02,.05,12.):
    q=np.arange(16)-7.5
    alpha=(np.sqrt(va/85)*(q[:,None]+1j*q[None,:])).ravel()
    p=np.full(256,1/256)
    t=.0002435454887726596
    noise=.0000204884482551047*va+.0186*.0002640339370277643
    actual=uniform_mi_2d(p,alpha,t,noise,16)
    expected=mi_gh(p,alpha,t,noise,16,dimension=2)
    assert abs(actual-expected)<2e-13
    checks.append(dict(check='same_2D_MI_'+str(va),residual=actual-expected))
(HERE/'numerical_test_receipt.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',checks=checks),indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,indent=2))
