"""Small, bounded implementation/repeatability checks; no256-source computation."""
import ast
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
import independent_fock_Cw as A
import independent_gram_Cw as B
from run_comparison import working_set

OUT=Path(__file__).resolve().parent


def main():
    begin=time.perf_counter();checks=[]
    for module in [A,B]:
        tree=ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append(node.module or '')
        assert not any(x.startswith(('src.','scripts.','inventory','physical_map')) for x in imports)
        checks.append(dict(check=module.__name__+'_no_repository_moment_import',status='CURRENTLY_VERIFIED_PASS'))
    for name in ['Uniform_4','MB_16']:
        path=OUT/'inputs'/f'{name}.npz';before=hashlib.sha256(path.read_bytes()).hexdigest()
        data=np.load(path);p,a=data['p'],data['alpha'];p0=p.copy();a0=a.copy()
        for method,call in [('A',lambda:A.float64(p,a,48,[1e-12])),('B',lambda:B.float64(p,a,[1e-12]))]:
            first,_=call();second,_=call()
            assert all(first[0][k]==second[0][k] for k in ['C','w_direct','w_residual','numerical_rank'])
            checks.append(dict(check=f'{name}_{method}_repeatability',status='CURRENTLY_VERIFIED_PASS'))
        np.testing.assert_array_equal(p,p0);np.testing.assert_array_equal(a,a0)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    data=np.load(OUT/'inputs/Uniform_4.npz');p,a=data['p'],data['alpha']
    x,_=A.float64(p,a,8,[1e-14]);y,_=B.float64(p,a,[1e-14])
    perm=np.array([2,0,3,1]);phase=np.exp(.37j)
    for method,ref,computed in [
        ('A_permutation',A.float64(p,a,48,[1e-12])[0][0],A.float64(p[perm],a[perm],48,[1e-12])[0][0]),
        ('B_permutation',y[0],B.float64(p[perm],a[perm],[1e-14])[0][0]),
        ('A_phase',A.float64(p,a,48,[1e-12])[0][0],A.float64(p,a*phase,48,[1e-12])[0][0]),
        ('B_phase',y[0],B.float64(p,a*phase,[1e-14])[0][0])]:
        error=max(abs(ref[k]-computed[k]) for k in ['C','w_residual'])
        assert error<2e-12
        checks.append(dict(check=method,status='CURRENTLY_VERIFIED_PASS',max_Cw_difference=error))
    assert abs(x[0]['w_direct']-x[0]['w_residual'])<2e-14
    checks.append(dict(check='nonunit_Fock_norm_explicit_residual_correction',status='CURRENTLY_VERIFIED_PASS',
        coherent_norm=x[0]['coherent_norm_min'],w_direct=x[0]['w_direct'],w_corrected_residual=x[0]['w_residual'],
        w_if_normalized_truncated_states=x[0]['w_normalized_truncated_states']))
    elapsed=time.perf_counter()-begin;memory=working_set(os.getpid())/1024**2
    assert elapsed<5 and memory<1024
    result=dict(status='CURRENTLY_VERIFIED_PASS',checks=checks,elapsed_seconds=elapsed,
        low_cost_check_time_limit_seconds=5,observed_working_set_MiB=memory,working_set_limit_MiB=1024,
        maximum_source_symbols=16,maximum_Fock_dimension=48,new256_source_jobs=0,source_catalog_modified=0)
    (OUT/'focused_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=result['status'],checks=len(checks),elapsed_seconds=elapsed)))


if __name__=='__main__':main()
