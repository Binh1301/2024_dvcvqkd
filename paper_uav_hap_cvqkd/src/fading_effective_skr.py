"""Moment-matched Gaussian DM-CV-QKD diagnostic with ideal heterodyne detection.

Keeps the physical law, exact C,w, and existing discrete MI/direct-Z kernels.
This is not the exact pooled fading likelihood or a validated fading-security proof.
"""
from __future__ import annotations
from dataclasses import replace
import math
import numpy as np
import torch
from scripts import run_ao_effective_channel_no_fading_noise_reference as sources
from scripts._common import holevo_numerical_kwargs
from src.manuscript_corrected_3moments import effective_fading_channel
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import deterministic_mutual_information

MODEL='fading_effective_gaussian_heterodyne'
STATUS='PRELIMINARY_MOMENT_MATCHED_GAUSSIAN_FADING_APPROXIMATION'


def effective_channel(moments, VA):
    for name,value in dict(R=1.,xi_det=0.,chi_het=1.).items():
        if moments.get(name)!=value:
            raise ValueError('Only the existing ideal heterodyne security convention is validated: '+name)
    if not math.isclose(moments['physical_probability_mass'],1.,rel_tol=0.,abs_tol=1e-10):
        raise ValueError('Preserve the normalized physical fading law and its AoA atom')
    mapping=effective_fading_channel(moments,VA)
    if moments['mean_sqrt_eta']>0 and mapping['T_eff']==0:
        raise FloatingPointError('Squared amplitude moment underflow; not a zero-channel event')
    noise=mapping['effective_excess_noise_output']
    return dict(mapping,scientific_model=MODEL,scientific_status=STATUS,a=1+VA,N_eff=noise,
        sigma2_complex=1+noise/2,b_pre=mapping['b'],
        m_xi_total=moments['mean_eta_xi_total'],m_excess=mapping['mean_channel_excess_noise_output'],
        fading_variance=mapping['variance_sqrt_eta'],Delta_fad=mapping['fading_noise_output'],
        fading_noise_included=True,vacuum_Bob=1.,heterodyne_added_vacuum=1.,
        trusted_detector_excess_output=0.,trusted_detector_security='IDEAL_ONLY',
        total_noise_subtraction='m_excess=m_xi_total-(1+chi_het-mean_eta)',
        likelihood='CN(sqrt(T_eff)*alpha,1+N_eff/2)',
        exact_pooled_fading_likelihood=False,certified_fading_security_lower_bound=False)


def heterodyne_likelihood(y, alpha, transmission, noise_output):
    if not 0<=transmission<=1 or not math.isfinite(noise_output) or noise_output<0:
        raise ValueError('Invalid heterodyne likelihood parameters')
    variance=1+noise_output/2
    return np.exp(-np.abs(np.asarray(y)-math.sqrt(transmission)*alpha)**2/variance)/(math.pi*variance)


def evaluate_batch(candidate, moment_rows, config, authorized_hashes):
    """One authenticated source, multiple channel states; no C,w recomputation."""
    ensemble=sources.authenticate(candidate,authorized_hashes,config)
    mappings=[effective_channel(m,candidate['V_A']) for m in moment_rows]
    if not mappings:raise ValueError('Empty moment batch')
    active=[i for i,m in enumerate(mappings) if m['T_eff']>0]
    output=[None]*len(mappings)
    for i,m in enumerate(mappings):
        if m['T_eff']==0:
            output[i]=dict(m,nu_raw=candidate['nu_raw'],V_A=candidate['V_A'],C=candidate['C'],w=candidate['w'],
                ensemble_hash=candidate['ensemble_hash'],source_cache_key=candidate['source_cache_key'],
                I_AB=0.,beta_I_AB=0.,chi_BE=0.,SKR=0.,K_raw=0.,K_usable=0.,Z_star=0.,
                QKD_expressions_evaluated=False,status='ZERO_EFFECTIVE_TRANSMISSION',numerical_repairs=[])
    if not active:return output
    batch=replace(ensemble,probabilities=ensemble.probabilities.expand(len(active),-1),
        amplitudes=ensemble.amplitudes.expand(len(active),-1),declared_va=ensemble.declared_va.expand(len(active)))
    transmission=torch.tensor([mappings[i]['T_eff'] for i in active],dtype=torch.float64)
    epsilon=torch.tensor([mappings[i]['xi_eff'] for i in active],dtype=torch.float64)
    numerical=holevo_numerical_kwargs(config)
    with torch.no_grad():
        security=_holevo_from_source_moments(batch,transmission,epsilon,
            coherent_correlation=torch.full_like(transmission,candidate['C']),
            w_raw=torch.full_like(transmission,candidate['w']),tau=None,tau_trace=batch.probabilities.sum(dim=-1),
            require_supported_symmetry=True,symmetry_tolerance=numerical['symmetry_tolerance'],
            physicality_tolerance=numerical['physicality_tolerance'],maximize_full_interval=False,
            diagnostics={'backend':MODEL})
        mi=[deterministic_mutual_information(batch,transmission,epsilon,quadrature_order=order,implementation='product') for order in (8,16,32)]
    if security.diagnostics['mode']!='zstar':raise ValueError('Direct Z-minus target changed')
    entropy=float((-torch.special.xlogy(ensemble.probabilities,ensemble.probabilities).sum()/math.log(2.)))
    for k,i in enumerate(active):
        m=mappings[i];cov=security.covariance
        a=float(cov.matrix[k,0,0]);b=float(cov.matrix[k,2,2]);z=float(security.z[k]);chi=float(security.chi_be[k])
        lambdas=[float(v[k]) for v in (cov.lambda1,cov.lambda2,cov.lambda3)]
        signal=2*math.sqrt(m['T_eff'])*candidate['C'];penalty=math.sqrt(2*m['N_eff']*candidate['w'])
        if max(abs(a-m['a']),abs(b-m['b']),abs(z-(signal-penalty)))>2e-12:
            raise ValueError('Moment/covariance/direct-Z consistency failed')
        if abs(lambdas[2]-(a-z*z/(b+1)))>2e-12:raise ValueError('Heterodyne Schur-complement identity failed')
        if min(lambdas)<1-numerical['physicality_tolerance']:raise ValueError('Nonphysical covariance')
        if abs(float(mi[2][k]-mi[1][k]))>1e-8:raise ValueError('GH16/32 MI precision unresolved')
        value=float(mi[2][k])
        if not 0<=value<=entropy:raise ValueError('Discrete MI outside entropy domain')
        raw=.95*value-chi
        output[i]=dict(m,nu_raw=candidate['nu_raw'],V_A=candidate['V_A'],C=candidate['C'],w=candidate['w'],
            ensemble_hash=candidate['ensemble_hash'],source_cache_key=candidate['source_cache_key'],source_path=candidate['source_path'],
            source_payload_sha256=sources.digest(sources.ROOT/candidate['source_path']),
            Z_star=z,Z_signal=signal,Z_penalty=penalty,Gamma_AB=cov.matrix[k].tolist(),
            lambda_1=lambdas[0],lambda_2=lambdas[1],lambda_3=lambdas[2],
            I_AB=value,beta_rec=.95,beta_I_AB=.95*value,chi_BE=chi,SKR=raw,K_raw=raw,K_usable=max(0.,raw),
            MI_orders=[dict(order=order,I_AB=float(v[k]),SKR=.95*float(v[k])-chi) for order,v in zip((8,16,32),mi)],
            numerical_repairs=list(security.diagnostics['numerical_repairs']),
            Holevo_target='chi_BE_at_direct_Z_star',QKD_expressions_evaluated=True,
            batch_shared_identical_ensemble=True,status='NUMERICALLY_EVALUATED_PRELIMINARY')
    return output


def evaluate_candidate(candidate,moments,config,authorized_hashes):
    return evaluate_batch(candidate,[moments],config,authorized_hashes)[0]
