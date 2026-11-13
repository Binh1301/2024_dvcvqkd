"""Independent adaptive-MI and covariance checks on saved root endpoints."""
from pathlib import Path
import csv
import json
import math
import sys
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1];sys.path.insert(0,str(ROOT))
from src.eq14_cloud_diagnostic import Eq14Diagnostic

model=Eq14Diagnostic();by_hash={s['ensemble_hash']:s for s in model.sources}
verified=[]
for name in ['vertical','grid_000','grid_125','grid_250','domain_corner','extended_19.5km']:
    summary=json.loads((OUT/(name+'_summary.json')).read_text())
    context=model.context(summary['zenith_deg'])
    with (OUT/(name+'_evaluations.csv')).open() as f:records=list(csv.DictReader(f))
    seen=set()
    for mode,s in summary['searches'].items():
        bracket=s['diagnostic_crossing_interval_db']
        if bracket is None:continue
        for A in bracket:
            row=next(r for r in records if r['mode']==mode and float(r['A_db'])==A)
            key=(row['ensemble_hash'],A)
            if key in seen:continue
            seen.add(key);source=by_hash[key[0]]
            actual=model.evaluate(source,context,A)
            independent,error=model.h['independent_mi'](source['p'],source['alpha'],actual['t'],1+actual['N_effective'])
            comp=model.model['components'](source['VA'],actual['t'],actual['N_effective']/actual['t'],source['C'],source['w'],digits=110)
            v,w,z=[comp[k] for k in ['V','W','Z_manuscript_eq14']]
            gamma=np.array([[v,0,z,0],[0,v,0,-z],[z,0,w,0],[0,-z,0,w]])
            omega=np.kron(np.eye(2),np.array([[0.,1.],[-1.,0.]]))
            spectrum=np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
            delta=max(abs(spectrum-np.sort([comp['nu_1'],comp['nu_2']])))
            conditional=math.sqrt(v*(v-z*z/w))
            assert abs(independent-actual['I_AB'])<2e-10 and delta<2e-11
            assert abs(conditional-comp['nu_3'])<2e-11
            assert abs(actual['K_raw']-float(row['K_raw']))<2e-12
            verified.append(dict(geometry=name,A_db=A,ensemble_hash=key[0],
                adaptive_MI_difference=abs(independent-actual['I_AB']),adaptive_integral_error_estimate=error,
                matrix_spectrum_difference=float(delta),conditional_eigenvalue_difference=abs(conditional-comp['nu_3']),
                raw_rate_replay_difference=abs(actual['K_raw']-float(row['K_raw']))))
result=dict(status='CURRENTLY_VERIFIED_PASS',scope='selected numerical checkpoints only; not source or security certification',checks=verified)
(OUT/'selected_root_validation.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print('Independent root-endpoint checks PASS:',len(verified))
