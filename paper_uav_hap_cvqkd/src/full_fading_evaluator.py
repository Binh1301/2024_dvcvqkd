"""Full-noise, ideal-heterodyne DM diagnostics with separated MI methods.

No source oracle, source interpolation, parameter optimization or security
certification. The exact ensemble and source payload are authenticated together.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.special import logsumexp, roots_hermite

from src.manuscript_corrected_3moments import (admissible_correlation_interval,
    corrected_covariance, holevo_interval_maximizer)

MODEL='corrected_full_fading_v1'


def effective_channel(moments,VA):
    m1,mh=map(float,(moments['mean_eta'],moments['mean_sqrt_eta']))
    xi=float(moments.get('xi_ch',.0186))
    if (not all(math.isfinite(v) for v in (m1,mh,VA,xi)) or VA<=0 or xi<0
            or moments.get('R',1.)!=1 or moments.get('xi_det',0.)!=0):
        raise ValueError('Finite full-noise inputs and ideal receiver required')
    if not math.isclose(moments['physical_probability_mass'],1.,abs_tol=1e-10,rel_tol=0):
        raise ValueError('Normalized physical distribution required')
    deterministic=moments.get('moment_law')=='deterministic_delta'
    t=float(moments['deterministic_transmissivity']) if deterministic else mh*mh
    if deterministic and (m1!=t or mh!=math.sqrt(t)):
        raise ValueError('Invalid deterministic moment tag')
    if not 0<=t<=m1<=1:
        raise ValueError('Invalid fading moments; no clipping')
    variance=0. if deterministic else m1-t
    noise=variance*VA+m1*xi
    b=1+m1*(VA+xi)
    if not math.isclose(b,1+t*VA+noise,rel_tol=1e-13,abs_tol=1e-13):
        raise ValueError('Full-noise covariance identity failed')
    return dict(moments,VA=VA,T_eff=t,eta_f=t,variance_sqrt_eta=variance,
                N_eff=noise,output_excess_noise=noise,output_excess_noise_from_third=noise,
                xi_eff=noise/t if t else None,R_f=m1/t if t else None,
                a=VA+1,b=b,fading_noise_output=variance*VA,channel_noise_output=m1*xi,
                sigma2_complex=1+noise/2,fading_noise_included=True)


def evaluate_ideal_security(effective,VA,C,w,grid_size=257,tolerance=1e-9):
    interval=admissible_correlation_interval(effective,VA,C,w)
    result=holevo_interval_maximizer(effective,VA,C,w,grid_size=grid_size,tolerance=tolerance)
    if result['chi_BE'] is None:
        raise ValueError(f'Holevo interval convergence failed: {result}')
    covariance=corrected_covariance(effective,VA,result['Z_worst'])
    return dict(result,covariance=covariance,Z_minus=interval['theoretical_lower'],
                Z_plus=interval['theoretical_upper'],lambda_3=covariance['lambda_3'])


def authenticate_source(candidate,expected_sha256):
    from scripts.exact_cache_provenance import source_settings, verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    from src.cvqkd.covariance import quadrature_symmetry_diagnostics
    raw=Path(candidate['source_path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError('Exact source payload hash mismatch')
    payload=json.loads(raw)
    verify_source_payload(payload,source_settings(unconstrained_config()))
    ensemble=candidate['ensemble']
    ensemble.validate(tolerance=1e-12)
    if ensemble_hash(ensemble)!=payload['ensemble_hash'] or candidate['ensemble_hash']!=payload['ensemble_hash']:
        raise ValueError('MI and exact C,w ensemble identity mismatch')
    if (float(candidate['V_A']).hex()!=payload['V_A_hex']
            or float(candidate['nu_raw']).hex()!=payload['nu_mb_raw_hex']
            or candidate['C']!=payload['C'] or candidate['w']!=payload['w']):
        raise ValueError('Source parameter or moment mismatch')
    if not math.isclose(float(ensemble.computed_va()[0]),candidate['V_A'],rel_tol=1e-12,abs_tol=1e-12):
        raise ValueError('VA != 2 mean photons')
    if not quadrature_symmetry_diagnostics(ensemble).standard_form_supported:
        raise ValueError('Centered C4 source required')
    return ensemble


def reduced_likelihood_nodes(eta,weights,order):
    """Gaussian quadrature of sqrt(eta) using a reorthogonalized Lanczos basis.

    The AoA atom is kept separately. This compresses numerical integration
    nodes, never the source's 256-state support or its quantum density matrix.
    """
    eta,weights=np.asarray(eta),np.asarray(weights)
    zero=(eta==0); zero_weight=float(weights[zero].sum())
    x=np.sqrt(eta[~zero]); w=weights[~zero]; active=float(w.sum()); w=w/active
    q=np.sqrt(w); previous=np.zeros_like(q); beta=0.; basis=[]; aa=[]; bb=[]
    for i in range(order):
        basis.append(q.copy())
        z=x*q-beta*previous
        a=float(q@z); z-=a*q
        for vector in basis:
            z-=float(vector@z)*vector
        b=float(np.linalg.norm(z)); aa.append(a)
        if i==order-1 or b<1e-15: break
        bb.append(b); previous,q=q,z/b; beta=b
    nodes,vectors=eigh_tridiagonal(aa,bb,lapack_driver='stev')
    if np.any(nodes<0) or np.any(nodes>1):
        raise ValueError('Compressed physical quadrature outside [0,1]')
    new_weights=active*vectors[0]**2
    keep=new_weights>0
    nodes=np.r_[0.,nodes[keep]**2]; new_weights=np.r_[zero_weight,new_weights[keep]]
    diagnostics=dict(order=order,nodes=len(nodes),m1_error=abs(float(new_weights@nodes)-float(weights@eta)),
                     mhalf_error=abs(float(new_weights@np.sqrt(nodes))-float(weights@np.sqrt(eta))),
                     source_support_reduced=False,zero_weight=zero_weight)
    if max(diagnostics['m1_error'],diagnostics['mhalf_error'])>1e-11:
        raise ValueError('Likelihood compression moment check failed')
    return nodes,new_weights,diagnostics


def mixture_mi(p,alpha,eta,weights,*,output_order=40,reference_variance=None,batch_size=24):
    """Deterministic full-complex-output integral, including the zero atom.

    Integrate under an auxiliary CN(0,s_ref) using a 2D Hermite rule. The joint
    mixture never factorizes into I and Q marginals under shared fading.
    """
    p=np.asarray(p,dtype=float); alpha=np.asarray(alpha,dtype=complex)
    eta=np.asarray(eta,dtype=float); weights=np.asarray(weights,dtype=float)
    if (p.ndim!=1 or alpha.shape!=p.shape or not np.isfinite(p).all() or np.any(p<=0)
            or not np.isfinite(alpha).all() or not math.isclose(float(p.sum()),1.,abs_tol=1e-12,rel_tol=0)
            or eta.shape!=weights.shape or eta.ndim!=1 or np.any(eta<0) or np.any(eta>1)
            or not np.isfinite(eta).all() or not np.isfinite(weights).all() or np.any(weights<0)
            or not math.isclose(float(weights.sum()),1.,abs_tol=1e-12,rel_tol=0)):
        raise ValueError('Invalid exact ensemble or fading quadrature')
    keep=weights>0; eta,weights=eta[keep],weights[keep]
    if len(eta)==1 and eta[0]==0: return 0.
    if reference_variance is None:
        reference_variance=1+float(weights@eta)*float(p@np.abs(alpha)**2)
    if not math.isfinite(reference_variance) or reference_variance<=0 or output_order<4:
        raise ValueError('Invalid output quadrature')
    roots,hw=roots_hermite(output_order)
    x,y=np.meshgrid(roots,roots,indexing='ij')
    points=math.sqrt(reference_variance)*(x+1j*y).ravel()
    output_weights=np.outer(hw,hw).ravel()/math.pi
    means=alpha[:,None]*np.sqrt(eta)[None,:]
    variance=1+.0186*eta/2
    log_weights=np.log(weights)
    result=0.
    for start in range(0,len(points),batch_size):
        yy=points[start:start+batch_size]
        # Squared distances avoid taking a complex absolute square in a 3D temporary.
        dist=(yy.real[:,None,None]-means.real[None,:,:])**2+(yy.imag[:,None,None]-means.imag[None,:,:])**2
        conditional=logsumexp(-dist/variance-np.log(math.pi*variance)+log_weights,axis=2)
        marginal=logsumexp(conditional+np.log(p),axis=1)
        logq=-np.log(math.pi*reference_variance)-np.abs(yy)**2/reference_variance
        integrand=np.sum(p[None,:]*np.exp(conditional-logq[:,None])*(conditional-marginal[:,None]),axis=1)/math.log(2)
        result+=float(output_weights[start:start+len(yy)]@integrand)
    if not math.isfinite(result): raise ValueError('Nonfinite fading mixture MI')
    return result


def evaluate_candidate(candidate,law,config):
    """One fixed-source configuration; separate results for both MI methods."""
    import torch
    from src.cvqkd.mutual_information import deterministic_mutual_information
    expected=dict(scientific_model=MODEL,xi_ch=.0186,beta=.95,detector='ideal_heterodyne',
                  R=1.,xi_det=0.,phase_noise='OFF',AO='OFF')
    if any(config.get(k)!=v for k,v in expected.items()):
        raise ValueError('Unsupported primary scientific configuration')
    ensemble=authenticate_source(candidate,config['source_payload_sha256'])
    moments=law.moments()
    effective=effective_channel(moments,candidate['V_A'])
    security=evaluate_ideal_security(effective,candidate['V_A'],candidate['C'],candidate['w'],
                                    config.get('holevo_grid_size',257),config.get('holevo_tolerance',1e-9))
    t=torch.tensor([effective['T_eff']],dtype=torch.float64)
    eps=torch.tensor([effective['xi_eff']],dtype=torch.float64)
    gaussian_rows=[dict(order=n,I_AB=float(deterministic_mutual_information(ensemble,t,eps,
                          quadrature_order=n,implementation='product')[0])) for n in config['gaussian_orders']]
    if abs(gaussian_rows[-1]['I_AB']-gaussian_rows[-2]['I_AB'])>config['mi_tolerance']:
        raise ValueError('Gaussian-effective MI did not converge')
    p=ensemble.probabilities.detach().numpy().reshape(-1)
    alpha=ensemble.amplitudes.detach().numpy().reshape(-1)
    eta,weights,quad_diagnostics=law.quadrature(config['physical_quadrature_order'])
    mixture_rows=[]
    for n in config['mixture_orders']:
        nodes,ww,compression=reduced_likelihood_nodes(eta,weights,n)
        value=mixture_mi(p,alpha,nodes,ww,output_order=n)
        mixture_rows.append(dict(order=n,I_AB=value,compression=compression))
    difference=abs(mixture_rows[-1]['I_AB']-mixture_rows[-2]['I_AB'])
    entropy=float(-p@np.log2(p))
    mixture_pass=(difference<=config['mi_tolerance']
                  and 0<=mixture_rows[-1]['I_AB']<=entropy)
    chi=security['chi_BE']
    def decomposition(value,method,status):
        return dict(MI_method=method,I_AB=value,beta_I_AB=.95*value,chi_BE=chi,K_raw=.95*value-chi,
                    numerical_status=status,security_classification='ASYMPTOTIC_DIAGNOSTIC_NOT_COMPOSABLE_CERTIFICATE')
    return dict(scientific_model=MODEL,nu_raw=candidate['nu_raw'],VA=candidate['V_A'],C=candidate['C'],w=candidate['w'],
                ensemble_hash=candidate['ensemble_hash'],source_path=str(candidate['source_path']),
                source_payload_sha256=config['source_payload_sha256'],effective=effective,security=security,
                gaussian_effective=decomposition(gaussian_rows[-1]['I_AB'],'DISCRETE_256_GAUSSIAN_EFFECTIVE', 'CURRENTLY_VERIFIED_PASS'),
                actual_fading_mixture=decomposition(mixture_rows[-1]['I_AB'],'DISCRETE_256_ACTUAL_POOLED_FADING_MIXTURE',
                                    'CURRENTLY_VERIFIED_PASS' if mixture_pass else 'FAILED'),
                gaussian_refinement=gaussian_rows,mixture_refinement=mixture_rows,mixture_last_difference=difference,
                physical_quadrature=quad_diagnostics,mixture_convergence_pass=mixture_pass,
                security_limitations=['fixed centered C4 source independent of fading; phase tracked',
                    'pooled stationary iid channel uses including AoA outage; Eve may purify fading label',
                    'no temporal-correlation, finite-size, composable, calibration or reconciliation-code proof',
                    'numerical interval maximization is not a rigorous continuous supremum enclosure',
                    'active conditioning is an explicit optical surrogate assumption'])
