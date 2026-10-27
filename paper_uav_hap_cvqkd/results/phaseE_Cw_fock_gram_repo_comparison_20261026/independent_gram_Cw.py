"""Method B: weighted coherent overlaps and support eigenstates; no Fock density."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import scipy.linalg as la


def float64(p,alpha,thresholds):
    start=time.perf_counter();M=len(p)
    overlap=np.exp(-.5*(abs(alpha[:,None])**2+abs(alpha[None,:])**2)+alpha[:,None].conj()*alpha[None,:])
    H=np.sqrt(p[:,None]*p[None,:])*overlap
    L=H*alpha[None,:]
    eigen,U=la.eigh(H,driver='evd')
    eig_res=float(la.norm(H@U-U*eigen)/la.norm(H));output=[]
    for threshold in thresholds:
        keep=eigen>threshold;values=eigen[keep];V=U[:,keep];s=np.sqrt(values)
        annihilation=(V.conj().T@L@V)/(s[:,None]*s[None,:])
        C=float(np.sum((s[:,None]*s[None,:])*abs(annihilation)**2))
        q=(s[:,None]*V.conj().T)/np.sqrt(p)[None,:]
        T=(s[:,None]*annihilation)/s[None,:]
        u=T@q;d=np.sum(q.conj()*u,axis=0);qnorm=np.sum(abs(q)**2,axis=0)
        first=np.sum(abs(u)**2,axis=0)
        direct=float(p@(first-abs(d)**2))
        # Include the coherent state's component outside the retained support.
        residual=float(p@(np.sum(abs(u-q*d)**2,axis=0)+(1-qnorm)*abs(d)**2))
        output.append(dict(method='B_Gram',backend='scipy_complex128_full_Gram',digits=16,NF='',source_size=M,
            eigenvalue_threshold=threshold,numerical_rank=int(keep.sum()),minimum_eigenvalue=float(eigen.min()),
            minimum_retained_eigenvalue=float(values.min()),retained_condition=float(values.max()/values.min()),
            negative_eigenvalues=int((eigen<0).sum()),material_negative=bool(eigen.min() < -threshold),
            tau_trace=float(np.trace(H).real),hermitian_error=float(la.norm(H-H.conj().T)),
            eigensolver_relative_residual=eig_res,projected_coherent_norm_min=float(qnorm.min()),
            projected_coherent_norm_max=float(qnorm.max()),C=C,w_direct=direct,w_residual=residual,
            direct_residual_difference=direct-residual,full_source_rank_resolved=int(keep.sum())==M,
            elapsed_seconds=time.perf_counter()-start))
    return output,eigen.tolist()


def orbits_from_arrays(probabilities,amplitudes):
    groups=[];unused=set(range(len(probabilities)))
    by_amplitude={complex(a):j for j,a in enumerate(amplitudes)}
    while unused:
        k=min(unused);z=complex(amplitudes[k])
        g=[by_amplitude[complex(z*rotation)] for rotation in [1,1j,-1,-1j]]
        assert all(probabilities[j]==probabilities[k] for j in g)
        assert all(j in unused for j in g)
        unused.difference_update(g);groups.append(g)
    return groups


def arbitrary(p,alpha,digits):
    import mpmath as mp
    start=time.perf_counter();M=len(p);groups=orbits_from_arrays(p,alpha);K=len(groups)
    with mp.workdps(digits):
        weights=[mp.mpf(float(x)) for x in p]
        amplitudes=[mp.mpc(float(x.real),float(x.imag)) for x in alpha]
        H=mp.matrix(M)
        for i in range(M):
            for j in range(i,M):
                overlap=mp.exp(-(abs(amplitudes[i])**2+abs(amplitudes[j])**2)/2+mp.conj(amplitudes[i])*amplitudes[j])
                H[i,j]=mp.sqrt(weights[i]*weights[j])*overlap
                H[j,i]=mp.conj(H[i,j])
        print(f'Gram H{M} dps{digits} overlaps built',flush=True)
        # F_s[orbit(k,r),k] = i^(s*r)/2 is a unitary symmetry transform.
        # Build F_s^dag H F_s and F_s^dag (H diag(alpha)) F_(s-1)
        # directly from the full H, rather than the repository sector formula.
        blocks=[];L_blocks=[]
        for s in range(4):
            previous=(s-1)%4;B=mp.matrix(K);L=mp.matrix(K)
            for i,g in enumerate(groups):
                for j,h in enumerate(groups):
                    B[i,j]=mp.fsum(mp.j**(-s*r+s*t)*H[g[r],h[t]]/4 for r in range(4) for t in range(4))
                    L[i,j]=mp.fsum(mp.j**(-s*r+previous*t)*H[g[r],h[t]]*amplitudes[h[t]]/4
                                    for r in range(4) for t in range(4))
            blocks.append((B+B.H)/2);L_blocks.append(L)
        floor=mp.power(10,-digits+20);values=[];vectors=[];raw=[];residuals=[]
        for s,B in enumerate(blocks):
            lam,V=mp.eighe(B);raw.extend([lam[j] for j in range(K)])
            residuals.append(mp.norm(B*V-V*mp.diag(lam))/mp.norm(B))
            indices=[j for j in range(K) if lam[j]>floor]
            values.append([lam[j] for j in indices])
            vectors.append(mp.matrix([[V[i,j] for j in indices] for i in range(K)]))
            print(f'Gram dps{digits} sector{s} retained{len(indices)}',flush=True)
        q=[]
        prototype_weights=[weights[g[0]] for g in groups]
        for s in range(4):
            q.append(mp.diag([mp.sqrt(v) for v in values[s]])*vectors[s].H*
                     mp.diag([1/(2*mp.sqrt(v)) for v in prototype_weights]))
        C=mp.mpf(0);u=[]
        for out in range(4):
            inp=(out-1)%4
            sr=mp.diag([mp.sqrt(v) for v in values[out]])
            ir=mp.diag([1/mp.sqrt(v) for v in values[out]])
            ic=mp.diag([1/mp.sqrt(v) for v in values[inp]])
            A=ir*(vectors[out].H*L_blocks[out]*vectors[inp])*ic
            C+=mp.fsum(mp.sqrt(values[out][i]*values[inp][j])*abs(A[i,j])**2
                       for i in range(A.rows) for j in range(A.cols))
            u.append((sr*A*ic)*q[inp])
        direct=mp.mpf(0);stable=mp.mpf(0);norms=[]
        for k in range(K):
            mean=mp.fsum(mp.conj(q[s][r,k])*u[s][r,k] for s in range(4) for r in range(q[s].rows))
            first=mp.fsum(abs(u[s][r,k])**2 for s in range(4) for r in range(q[s].rows))
            norm=mp.fsum(abs(q[s][r,k])**2 for s in range(4) for r in range(q[s].rows));norms.append(norm)
            direct+=4*prototype_weights[k]*(first-abs(mean)**2)
            stable+=4*prototype_weights[k]*(mp.fsum(abs(u[s][r,k]-q[s][r,k]*mean)**2
                for s in range(4) for r in range(q[s].rows))+(1-norm)*abs(mean)**2)
        retained=[v for block in values for v in block];st=lambda x:mp.nstr(x,50)
        row=dict(method='B_Gram',backend='mpmath_full_overlap_Gram_C4_unitary',digits=digits,NF='',
            source_size=M,eigenvalue_threshold=st(floor),numerical_rank=len(retained),
            minimum_eigenvalue=st(min(raw)),minimum_retained_eigenvalue=st(min(retained)),
            retained_condition=st(max(retained)/min(retained)),negative_eigenvalues=sum(v<0 for v in raw),
            material_negative=bool(min(raw)<-floor),tau_trace=st(mp.fsum(H[i,i] for i in range(M)).real),
            eigensolver_relative_residual=st(max(residuals)),projected_coherent_norm_min=st(min(norms)),
            projected_coherent_norm_max=st(max(norms)),C=st(C),w_direct=st(direct),w_residual=st(stable),
            direct_residual_difference=st(direct-stable),full_source_rank_resolved=len(retained)==M,
            elapsed_seconds=time.perf_counter()-start)
        return [row],[st(v) for v in raw]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('output')
    parser.add_argument('--digits',type=int,default=16);args=parser.parse_args()
    data=np.load(args.input);p,a=data['p'],data['alpha']
    assert np.isfinite(p).all() and np.isfinite(a).all() and np.all(p>0)
    if args.digits==16:result,spectrum=float64(p,a,[1e-10,1e-12,1e-14,1e-16])
    else:result,spectrum=arbitrary(p,a,args.digits)
    Path(args.output).write_text(json.dumps(dict(rows=result,spectrum=spectrum),indent=2,allow_nan=False),encoding='utf-8')


if __name__=='__main__':main()
