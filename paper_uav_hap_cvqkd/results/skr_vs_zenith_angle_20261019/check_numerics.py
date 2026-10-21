"""Small independent controls for the new variable-angle runner."""
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_sweep as run
import mpmath as mp
import numpy as np


def main():
    mp.mp.dps=80
    checks=[]

    def check(name,condition):
        assert condition,name
        checks.append(name)

    check('geometry_0',abs(run.channel_at_angle(0)['L_m']-19000)<mp.mpf('1e-65'))
    check('geometry_60',abs(run.channel_at_angle(60)['L_m']-38000)<mp.mpf('1e-65'))
    actual,expected=run.channel_at_angle(30),run.channel()
    check('every_channel_field_at_30',all(abs(actual[k]-expected[k])<mp.mpf('1e-60')*max(1,abs(expected[k])) for k in actual))
    check('atmosphere_at_60',abs(run.channel_at_angle(60)['eta_atm']-mp.mpf('.92')**2)<mp.mpf('1e-65'))
    e=run.make_ensemble(run.unconstrained_config(),'MB',.165,5.475)
    p,a=e.probabilities[0].numpy(),e.amplitudes[0].numpy()
    m=run.security(actual['mean_eta'],actual['mean_sqrt_eta'],run.M(5.475),run.M(3.1986564642787387),run.M(9.973886145561931e-7))
    factored=run.uniform_mi_2d(p,a,float(m['eta_f']),float(m['eta_f_xi_f']),16)
    direct=run.mi_gh(p,a,float(m['eta_f']),float(m['eta_f_xi_f']),16,dimension=2)
    check('product_2D_matches_full_256_mixture',abs(factored-direct)<2e-13)
    check('reference_MB_sign_and_value',abs(.95*factored-float(m['chi_BE'])-9.665799737514629e-5)<2e-13)
    check('vacuum_2D_MI_zero',abs(run.uniform_mi_2d(np.array([1.]),np.array([0j]),.1,.01,16))<1e-14)
    check('zero_transmittance_2D_MI_zero',abs(run.uniform_mi_2d(p,a,0.,.01,16))<1e-14)
    bad=p.copy();bad[0]+=1e-5;bad[-1]-=1e-5
    try:
        run.uniform_mi_2d(bad,a,.001,.01,16)
    except ValueError:
        check('reject_nonproduct_PMF',True)
    else:
        raise AssertionError('Nonproduct PMF accepted')
    run.save('numerical_test_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,
             full_mixture_difference=factored-direct,producer_sha256=run.sha(Path(__file__))))
    print(len(checks),'numerical controls PASS')


if __name__=='__main__':
    main()
