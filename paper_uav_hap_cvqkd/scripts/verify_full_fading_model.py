"""Independent spectrum/entropy checks and stricter fixed-configuration replay."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from scripts.run_manuscript_literal_3moments import verified_candidate
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    from src.full_fading_channel import OpticalConfig,FullFadingLaw
    from src.full_fading_evaluator import (authenticate_source,effective_channel,
        evaluate_ideal_security,mixture_mi,reduced_likelihood_nodes)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((args.input/'receipt.json').read_text())
    for name,digest in receipt['outputs'].items():
        if hashlib.sha256((args.input/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Input result hash mismatch')
    settings=receipt['settings']
    candidate=verified_candidate(ROOT/settings['source_payload'],unconstrained_config())
    ensemble=authenticate_source(candidate,settings['source_payload_sha256'])
    p=ensemble.probabilities.detach().numpy().reshape(-1)
    alpha=ensemble.amplitudes.detach().numpy().reshape(-1)
    checks=[]
    def check(name,residual,tolerance):
        checks.append(dict(name=name,residual=float(residual),tolerance=tolerance,
                           status='CURRENTLY_VERIFIED_PASS' if abs(residual)<=tolerance else 'FAILED'))
    for path in sorted(args.input.glob('*_D*.json')):
        record=json.loads(path.read_text())
        old=record['effective']; tag=record['baseline']+'_'+old['optical_mode']
        law=FullFadingLaw(OpticalConfig(**old['configuration']),old['optical_mode'],tolerance=2e-13)
        effective=effective_channel(law.moments(),record['VA'])
        for key in ('mean_eta','mean_sqrt_eta','N_eff','b'):
            check(tag+'_'+key,effective[key]-old[key],2e-11)
        eta,weights,diagnostics=law.quadrature(64)
        nodes,ww,compression=reduced_likelihood_nodes(eta,weights,72)
        mi=mixture_mi(p,alpha,nodes,ww,output_order=80,reference_variance=1.5)
        check(tag+'_mixture_MI_stricter',mi-record['actual_fading_mixture']['I_AB'],1e-8)
        security=evaluate_ideal_security(effective,record['VA'],record['C'],record['w'],grid_size=513,tolerance=1e-11)
        check(tag+'_Holevo_stricter',security['chi_BE']-record['security']['chi_BE'],1e-10)
        covariance=security['covariance']; matrix=np.array(covariance['Gamma_AB'])
        omega=np.kron(np.eye(2),np.array([[0,1],[-1,0]]))
        eig=np.sort(np.abs(np.linalg.eigvals(1j*omega@matrix)))[::2]
        check(tag+'_direct_matrix_symplectic',np.max(np.abs(eig-np.sort([covariance['lambda_1'],covariance['lambda_2']]))),2e-12)
        minimum=float(np.linalg.eigvalsh(matrix+1j*omega).min())
        check(tag+'_uncertainty_matrix_violation',min(0.,minimum),1e-12)
        a,b,z=covariance['a'],covariance['b'],covariance['Z']
        delta=a*a+b*b-2*z*z; determinant=(a*b-z*z)**2
        root=math.sqrt(delta*delta-4*determinant)
        ll=[math.sqrt((delta+root)/2),math.sqrt((delta-root)/2),a-z*z/(b+1)]
        def g(n): return 0. if n==0 else (n+1)*math.log2(n+1)-n*math.log2(n)
        independent_chi=g((ll[0]-1)/2)+g((ll[1]-1)/2)-g((ll[2]-1)/2)
        check(tag+'_direct_invariants_entropy',independent_chi-security['chi_BE'],2e-11)
        check(tag+'_K_mixture_replay',.95*mi-security['chi_BE']-record['actual_fading_mixture']['K_raw'],1e-8)
        (args.output/(tag+'.json')).write_text(json.dumps(dict(MI=mi,security=security,physical_quadrature=diagnostics,
                       compression=compression,min_uncertainty_eigenvalue=minimum),indent=2)+'\n')
        print(tag+' verification complete',flush=True)
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromNames([
        'tests.test_full_fading_pipeline','tests.test_manuscript_corrected_3moments',
        'tests.test_manuscript_corrected_ideal_reference'])
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (args.output/'unit_tests.txt').write_text(stream.getvalue())
    result=dict(checks=checks,tests_run=tests.testsRun,unit_test_failures=len(tests.failures),unit_test_errors=len(tests.errors),
                numerical_pass=all(c['status']=='CURRENTLY_VERIFIED_PASS' for c in checks),
                unit_tests_pass=tests.wasSuccessful(),requested_reference_version_verified=False,
                task_status='IMPLEMENTED_NUMERICALLY_VALIDATED_REFERENCE_VERSION_PENDING')
    (args.output/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
    return 0 if result['numerical_pass'] and result['unit_tests_pass'] else 2


if __name__=='__main__':raise SystemExit(main())
