"""Additional independent trusted limit, matrix ordering, and exact-ensemble hashes."""
import hashlib,json,math,sys,csv
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts import audit_negative_skr_independent as audit
out=Path(__file__).parent;inputs=json.loads((out/'audit_inputs.json').read_text());data=json.loads((out/'independent_audit.json').read_text());probe=json.loads((out/'production_probe.json').read_text())
checks=[]
def check(name,ok,details):checks.append(dict(name=name,status='CURRENTLY_VERIFIED_PASS' if ok else 'FAIL',details=details))
for source in inputs['sources']:
 payload={'schema':'exact-common-ensemble-v1','probabilities':{'dtype':'torch.float64','shape':[1,256],'data':[float(x).hex() for x in source['probabilities']]},'amplitudes':{'dtype':'torch.complex128','shape':[1,256],'data':[[float(z[0]).hex(),float(z[1]).hex()] for z in source['amplitudes']]},'declared_va':{'dtype':'torch.float64','shape':[1],'data':[float(source['V_A']).hex()]}}
 h=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 actual=hashlib.sha256((ROOT/source['source_path']).read_bytes()).hexdigest()
 check('independent_ensemble_and_payload_hash_'+str(source['nu_raw']),h==source['ensemble_hash'] and actual==source['source_payload_sha256'],dict(ensemble=h,payload=actual))
for r in data['results']:
 if r['case']!='reference_fading':continue
 p=next(x['result'] for x in probe['results'] if x['source_id']==r['source_id'] and x['case']==r['case'] and x['detector']==r['detector'])
 ab=float(np.max(np.abs(np.asarray(r['Gamma_AB'])-np.asarray(p['Gamma_AB']))))
 residual=None
 if r['detector']=='trusted_detector':residual=float(np.max(np.abs(np.asarray(r['conditional_covariance'])-np.asarray(p['conditional_covariance_AFG']))))
 check('matrix_ordering_'+str(r['source_id'])+'_'+r['detector'],ab<1e-12 and (residual is None or residual<1e-12),dict(AB_max_difference=ab,AFG_max_difference=residual))
limits=[];source=inputs['sources'][0];m=inputs['reference_state']['moments'];ideal=next(r for r in data['results'] if r['source_id']==0 and r['case']=='reference_fading' and r['detector']=='primary_detector')
for delta in (1e-2,1e-4,1e-6,1e-8):
 r=audit.physical_model(source,m['mean_eta'],m['mean_sqrt_eta'],m['xi_ch'],1-delta,delta*delta)
 limits.append(dict(delta=delta,eta_B=1-delta,nu_B=delta*delta,chi_BE=float(r['chi_BE']),ideal_chi=ideal['chi_BE'],difference=float(r['chi_BE'])-ideal['chi_BE'],conditional_entropy=float(r['conditional_entropy']),chi_upper=float(r['chi_upper']),physical_entropy_bound_pass=bool(r['checks']['holevo_physical_entropy_bound'])))
check('trusted_joint_ideal_limit',all(abs(a['difference'])>abs(b['difference']) for a,b in zip(limits,limits[1:])) and abs(limits[-1]['difference'])<1e-7 and all(x['physical_entropy_bound_pass'] for x in limits),limits)
with (out/'trusted_ideal_limit.csv').open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(limits[0]));writer.writeheader();writer.writerows(limits)
result=dict(status='CURRENTLY_VERIFIED_PASS' if all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in checks) else 'FAILED',checks=checks,source_moment_oracle_runs=0,no_production_numerical_helpers=True)
(out/'supplemental_independent_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2));assert result['status']=='CURRENTLY_VERIFIED_PASS'
