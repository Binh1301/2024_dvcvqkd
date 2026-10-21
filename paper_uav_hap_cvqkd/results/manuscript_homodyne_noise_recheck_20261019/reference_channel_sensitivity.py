"""Separately identified A0/w_eq convention diagnostic, never a model correction."""
import csv
import json
import math
from pathlib import Path
import sys

import mpmath as mp
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.recheck_manuscript_homodyne_noise import M, channel, mi_gh, security

OUT = Path(__file__).resolve().parent
mp.mp.dps = 80
g = channel()
source = json.loads((OUT/'result.json').read_text())['model']
with np.load(OUT/'verified_ensemble.npz', allow_pickle=False) as ensemble:
    p, alpha = ensemble['probabilities'], ensemble['amplitudes']
levels, inv = np.unique(alpha.real, return_inverse=True)
marginal = np.bincount(inv, weights=p)
v_old = mp.sqrt(mp.pi)*M('.08')/(2*mp.sqrt(2)*g['wL_m'])
a_old = mp.erf(v_old)**2
w_old = mp.sqrt(g['w_eff_m']**2*mp.sqrt(mp.pi)*mp.erf(v_old)/(2*v_old*mp.exp(-v_old*v_old)))
rows = []
for label, a0, weq in [('PDF_Eq6_effective_width_PRIMARY',g['A0'],g['w_eq_m']),
                        ('DIAGNOSTIC_ONLY_unbroadened_aperture_metadata',a_old,w_old)]:
    d = (weq/(2*g['sigma_s_m']))**2
    B = a0*g['eta_atm']
    s, c3 = g['sigma_R2'], g['C3']
    c1, mu = mp.exp(s*d*(1+d)/2), s*(1+2*d)/2
    x1 = -mp.log(B)+mu
    def moment(q):
        a = d+q
        Q = (mp.exp(a*x1-a*mu)*mp.erfc(c3*x1)
             + mp.exp(a*a/(4*c3*c3)-a*mu)*mp.erfc(a/(2*c3)-c3*x1))/2
        return g['P1']*B**q*d*c1/(d+q)*Q
    model = security(moment(1), moment(M('.5')),M('5.475'),M(source['C']),M(source['w']))
    i2 = 2*mi_gh(marginal,levels.astype(complex),float(model['eta_f']),float(model['eta_f_xi_f']),32,dimension=1)
    assert model['physical'] and math.isfinite(i2)
    rows.append(dict(convention=label,A0=float(a0),w_eq_m=float(weq),mean_eta=float(model['mean_eta']),
                     mean_sqrt_eta=float(model['mean_sqrt_eta']),I_AB_2D=i2,
                     chi_BE=float(model['chi_BE']),K=.95*i2-float(model['chi_BE'])))
with (OUT/'reference_channel_sensitivity.csv').open('w',encoding='utf-8',newline='') as stream:
    writer = csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps(rows,indent=2))
