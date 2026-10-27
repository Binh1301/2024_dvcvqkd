"""Method A: Fock coefficients/density only. No repository or Gram moment imports."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import scipy.linalg as la


def float64(p,alpha,cutoff,thresholds):
    start=time.perf_counter();M=len(p)
    states=np.empty((cutoff,M),complex);states[0]=np.exp(-abs(alpha)**2/2)
    for n in range(1,cutoff):states[n]=states[n-1]*alpha/np.sqrt(n)
    tau=(states*p)@states.conj().T
    herm=float(la.norm(tau-tau.conj().T));tau=(tau+tau.conj().T)/2
    values,U=la.eigh(tau,driver='evd')
    eig_res=float(la.norm(tau@U-U*values)/la.norm(tau))
    ann=np.diag(np.sqrt(np.arange(1,cutoff)),1)
    norms=np.sum(abs(states)**2,axis=0);output=[]
    for threshold in thresholds:
        keep=values>threshold;v=values[keep];Q=U[:,keep]
        square=(Q*np.sqrt(v))@Q.conj().T
        inverse=(Q/np.sqrt(v))@Q.conj().T
        a_tau=square@ann@inverse
        u=a_tau@states;d=np.sum(states.conj()*u,axis=0)
        first=np.sum(abs(u)**2,axis=0)
        direct=float(p@(first-abs(d)**2))
        # The original infinite coherent state has norm1. Its omitted Fock part
        # contributes (1-norm_F^2)|d|^2 to the full orthogonal residual.
        residual=float(p@(np.sum(abs(u-states*d)**2,axis=0)+(1-norms)*abs(d)**2))
        normalized=states/np.sqrt(norms)
        un=a_tau@normalized;dn=np.sum(normalized.conj()*un,axis=0)
        normalized_res=float(p@np.sum(abs(un-normalized*dn)**2,axis=0))
        C=np.trace(square@ann@square@ann.conj().T)
        output.append(dict(method='A_Fock',backend='scipy_complex128',digits=16,NF=cutoff,
            eigenvalue_threshold=threshold,numerical_rank=int(keep.sum()),source_size=M,
            minimum_eigenvalue=float(values.min()),minimum_retained_eigenvalue=float(v.min()),
            retained_condition=float(v.max()/v.min()),negative_eigenvalues=int((values<0).sum()),
            material_negative=bool(values.min() < -threshold),tau_trace=float(np.trace(tau).real),
            coherent_norm_min=float(norms.min()),coherent_norm_max=float(norms.max()),
            weighted_coherent_norm=float(p@norms),hermitian_error=herm,eigensolver_relative_residual=eig_res,
            C=float(C.real),C_imaginary_residual=float(C.imag),w_direct=direct,w_residual=residual,
            w_normalized_truncated_states=normalized_res,direct_residual_difference=direct-residual,
            state_normalization='Original truncated coefficients unchanged; full-state residual correction explicit',
            full_source_rank_resolved=int(keep.sum())==M,elapsed_seconds=time.perf_counter()-start))
    return output,values.tolist()


def exact_orbits(p,alpha):
    lookup={complex(z):j for j,z in enumerate(alpha)};seen=set();groups=[]
    for j,z in enumerate(alpha):
        if j in seen:continue
        orbit=[lookup[complex(z*r)] for r in [1,1j,-1,-1j]]
        assert len(set(orbit))==4 and all(p[k]==p[j] for k in orbit)
        seen.update(orbit);groups.append(orbit)
    assert len(seen)==len(p)
    return groups


def arbitrary(p,alpha,cutoff,digits):
    """Direct Fock density, reduced by exact photon-number-mod4 symmetry."""
    import mpmath as mp
    start=time.perf_counter()
    groups=exact_orbits(p,alpha);M=len(p);K=len(groups)
    with mp.workdps(digits):
        weights=[mp.mpf(float(p[g[0]])) for g in groups]
        z=[mp.mpc(float(alpha[g[0]].real),float(alpha[g[0]].imag)) for g in groups]
        F=mp.matrix(cutoff,K)
        for k,a in enumerate(z):
            F[0,k]=mp.exp(-abs(a)**2/2)
            for n in range(1,cutoff):F[n,k]=F[n-1,k]*a/mp.sqrt(n)
        indices=[list(range(r,cutoff,4)) for r in range(4)]
        blocks=[];values=[];vectors=[];raw=[];residuals=[]
        floor=mp.power(10,-digits+20)
        for r,index in enumerate(indices):
            V=mp.matrix([[F[n,k] for k in range(K)] for n in index]);blocks.append(V)
            tau=4*V*mp.diag(weights)*V.H
            eig,U=mp.eighe(tau);raw.extend([eig[i] for i in range(len(eig))])
            keep=[i for i in range(len(eig)) if eig[i]>floor]
            val=[eig[i] for i in keep];Q=mp.matrix([[U[n,i] for i in keep] for n in range(U.rows)])
            values.append(val);vectors.append(Q)
            residuals.append(mp.norm(tau*U-U*mp.diag(eig))/mp.norm(tau))
            print(f'Fock NF{cutoff} dps{digits} sector{r} retained{len(val)}',flush=True)
        q=[vectors[r].H*blocks[r] for r in range(4)]
        transformed=[];C=mp.mpf(0)
        for out in range(4):
            inp=(out+1)%4
            A=mp.matrix(len(indices[out]),len(indices[inp]))
            out_lookup={n:i for i,n in enumerate(indices[out])}
            for j,n in enumerate(indices[inp]):
                if n-1 in out_lookup:A[out_lookup[n-1],j]=mp.sqrt(n)
            local=vectors[out].H*A*vectors[inp]
            sout=mp.diag([mp.sqrt(x) for x in values[out]])
            sinv=mp.diag([1/mp.sqrt(x) for x in values[inp]])
            transformed.append((sout*local*sinv)*q[inp])
            C+=mp.fsum(mp.sqrt(values[out][i]*values[inp][j])*abs(local[i,j])**2
                       for i in range(local.rows) for j in range(local.cols))
        direct=mp.mpf(0);stable=mp.mpf(0)
        for k in range(K):
            d=mp.fsum(mp.conj(q[r][i,k])*transformed[r][i,k] for r in range(4) for i in range(q[r].rows))
            first=mp.fsum(abs(transformed[r][i,k])**2 for r in range(4) for i in range(q[r].rows))
            qnorm=mp.fsum(abs(q[r][i,k])**2 for r in range(4) for i in range(q[r].rows))
            direct+=4*weights[k]*(first-abs(d)**2)
            stable+=4*weights[k]*(mp.fsum(abs(transformed[r][i,k]-q[r][i,k]*d)**2
                for r in range(4) for i in range(q[r].rows))+(1-qnorm)*abs(d)**2)
        norms=[mp.fsum(abs(F[n,k])**2 for n in range(cutoff)) for k in range(K)]
        retained=[v for sector in values for v in sector]
        st=lambda x:mp.nstr(x,50)
        row=dict(method='A_Fock',backend='mpmath_eighe_C4_Fock',digits=digits,NF=cutoff,
            eigenvalue_threshold=st(floor),numerical_rank=len(retained),source_size=M,
            minimum_eigenvalue=st(min(raw)),minimum_retained_eigenvalue=st(min(retained)),
            retained_condition=st(max(retained)/min(retained)),negative_eigenvalues=sum(x<0 for x in raw),
            material_negative=bool(min(raw)<-floor),tau_trace=st(4*mp.fsum(weights[k]*norms[k] for k in range(K))),
            coherent_norm_min=st(min(norms)),coherent_norm_max=st(max(norms)),
            maximum_coherent_tail=st(max(1-x for x in norms)),
            eigensolver_relative_residual=st(max(residuals)),C=st(C),w_direct=st(direct),w_residual=st(stable),
            direct_residual_difference=st(direct-stable),state_normalization='No state/PMF renormalization; known full coherent norm1 used for residual',
            full_source_rank_resolved=len(retained)==M,elapsed_seconds=time.perf_counter()-start)
        return [row],[st(v) for v in raw]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('output')
    parser.add_argument('--cutoff',type=int,required=True);parser.add_argument('--digits',type=int,default=16)
    args=parser.parse_args();data=np.load(args.input);p,a=data['p'],data['alpha']
    assert np.isfinite(p).all() and np.isfinite(a).all() and np.all(p>0)
    if args.digits==16:result,spectrum=float64(p,a,args.cutoff,[1e-10,1e-12,1e-14,1e-16])
    else:result,spectrum=arbitrary(p,a,args.cutoff,args.digits)
    Path(args.output).write_text(json.dumps(dict(rows=result,spectrum=spectrum),indent=2,allow_nan=False),encoding='utf-8')


if __name__=='__main__':main()
