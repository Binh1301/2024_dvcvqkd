"""Small self-checks of the independent audit, with no production imports."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.integrate import quad
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts import audit_negative_skr_independent as audit
out=Path(__file__).parent;inputs=json.loads((out/'audit_inputs.json').read_text())
checks=[]
def check(name,condition,details):
 checks.append(dict(name=name,status='CURRENTLY_VERIFIED_PASS' if condition else 'FAIL',details=details))
check('bosonic_entropy_known_values',audit.g(0)==0 and audit.g(1)==2,'g(0)=0,g(1)=2')
s=audit.spectrum(audit.mp.eye(4));check('vacuum_spectrum',all(abs(x-1)<audit.mp.mpf('1e-55') for x in s),list(map(str,s)))
normal=[]
for variance in (1.,1.1964884143779374,1.1510418900645562):
 norm,err=quad(lambda r:2*r/variance*math.exp(-r*r/variance),0,np.inf,epsabs=1e-13,epsrel=1e-13)
 second,err2=quad(lambda r:2*r**3/variance*math.exp(-r*r/variance),0,np.inf,epsabs=1e-13,epsrel=1e-13)
 normal.append(dict(complex_variance=variance,normalization=norm,second_moment=second,per_real_quadrature=second/2,quadrature_error=err))
check('normalized_complex_likelihood_and_quadratures',all(abs(r['normalization']-1)<1e-12 and abs(r['second_moment']-r['complex_variance'])<1e-12 for r in normal),normal)
# The requested entropy inequality is capable of rejecting a mismatched W.
small_m1=audit.M('2.6407446657e-4');VA=audit.M('5.046875');xi=audit.M('0.0186');W=1+small_m1*(VA+xi);bound=2*audit.g((W-1)/2)
contradiction=dict(status='EXPECTED_REJECTION_IF_INPUTS_ARE_MIXED',not_actual_repository_configuration=True,m1=float(small_m1),W_pre=float(W),chi_upper=float(bound),mismatched_chi=1.1466344829084623,would_fail='HOLEVO_PHYSICAL_ENTROPY_BOUND')
check('entropy_bound_detects_wrong_configuration',contradiction['mismatched_chi']>contradiction['chi_upper'],contradiction)
# Confirm the audit's dependency graph excludes production numerical code.
import ast
script=(ROOT/'scripts/audit_negative_skr_independent.py').read_text(encoding='utf-8');tree=ast.parse(script)
imports=[x.module for x in ast.walk(tree) if isinstance(x,ast.ImportFrom)];imports +=[n.name for x in ast.walk(tree) if isinstance(x,ast.Import) for n in x.names]
check('no_production_numerical_imports',not any(x and (x.startswith('src') or x.startswith('scripts')) for x in imports),imports)
result=dict(status='CURRENTLY_VERIFIED_PASS' if all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in checks) else 'FAILED',checks=checks,independent_audit_script_sha256=hashlib.sha256(script.encode()).hexdigest())
(out/'independent_self_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
assert result['status']=='CURRENTLY_VERIFIED_PASS'
