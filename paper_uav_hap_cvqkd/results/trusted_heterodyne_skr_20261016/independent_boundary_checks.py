"""Additional independent boundary sweep; no source or model changes."""
import json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.trusted_heterodyne_skr import effective_channel,trusted_holevo
out=Path(__file__).parent
rows=[]
for VA in (1e-2,1e-4,1e-8,1e-12):
 m=effective_channel(dict(mean_eta=.25,mean_sqrt_eta=.5,xi_ch=0.),VA)
 for efficiency in (.3,.7,.95,1-1e-8,1.):
  for electronic in (0.,.0135,.2):
   # Product thermal covariance (z=0) is a physical covariance boundary fixture.
   h=trusted_holevo(m['a'],m['b'],0.,efficiency,electronic)
   assert math.isfinite(h['chi_BE']) and h['chi_BE']>=-1e-12
   rows.append(dict(VA=VA,efficiency=efficiency,electronic=electronic,chi_BE=h['chi_BE'],appendix_status=h['appendix_covariance_status'],residual=h['appendix_purification_spectrum_residual']))
for efficiency in (.3,.7,1.):
 for electronic in (0.,.0135):
  h=trusted_holevo(1.,1.,0.,efficiency,electronic)
  assert h['chi_BE']==0
rng=np.random.default_rng(20261021)
for n in range(100):
 a=1+float(rng.uniform(.01,20));t=float(rng.uniform(.01,.99));noise=float(rng.uniform(0,.2));b=1+t*(a-1+noise);z=float(rng.uniform(.1,1))*math.sqrt(t*(a*a-1))
 h=trusted_holevo(a,b,z,.7,.0135)
 assert h['appendix_purification_spectrum_residual']<1e-10
 rows.append(dict(a=a,b=b,z=z,residual=h['appendix_purification_spectrum_residual'],chi_BE=h['chi_BE']))
result=dict(status='CURRENTLY_VERIFIED_PASS',covariance_checks=len(rows)+6,minimum_VA=1e-12,maximum_Appendix_purification_residual=max(r['residual'] for r in rows),minimum_chi=min(r['chi_BE'] for r in rows),roundoff_allowance=1e-10,no_source_generation=True,scope='Generic physical covariance and vacuum boundaries, not a new modulation ensemble or security proof')
(out/'independent_boundary_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(out/'independent_boundary_cases.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
