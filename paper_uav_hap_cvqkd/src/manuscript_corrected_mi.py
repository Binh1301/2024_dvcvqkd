"""Pooled fading, discrete-input MI for the isolated corrected manuscript mode.

Samples come from the physical rho=0 law. Only the likelihood integral uses
positive finite quadrature; its refinement diagnostics are not a bias proof.
The receiver model here is classical and does not establish detector security.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
from scipy.special import logsumexp, roots_legendre

MODEL = 'manuscript_corrected_3moments'
MI_METHOD = 'discrete_pooled_physical_fading_monte_carlo_with_positive_likelihood_quadrature'
MAX_SAMPLES = 4096
MAX_QUADRATURE_ORDER = 256
MAX_REJECTION_DRAWS = 65536


class FadingMIError(ValueError):
    """Invalid inputs or a bounded numerical evaluation could not be completed."""


def _finite(value, name, *, positive=False, nonnegative=False):
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0) or (nonnegative and value < 0):
        raise FadingMIError(f'Invalid {name}: {value!r}')
    return value


def _ensemble(probabilities, amplitudes):
    p = np.asarray(probabilities, dtype=np.float64)
    alpha = np.asarray(amplitudes, dtype=np.complex128)
    if p.ndim != 1 or alpha.shape != p.shape or not 1 <= p.size <= 256:
        raise FadingMIError('MI requires matching one-dimensional p/alpha arrays, at most 256 symbols')
    if not np.isfinite(p).all() or np.any(p < 0) or not np.isfinite(alpha).all():
        raise FadingMIError('PMF/amplitudes must be finite and PMF nonnegative')
    if not math.isclose(float(p.sum()), 1., abs_tol=1e-12, rel_tol=0):
        raise FadingMIError('PMF must sum to one; no PMF repair')
    return p, alpha


def receiver_parameters(amplitudes, eta, *, R=.7, xi_det=.0135, xi_ch=.0186):
    """CN(mean, variance), vacuum SNU=1 before ideal heterodyne.

    Loss inside a coherent-state receiver still has unit complex shot noise.
    xi_det is output-referred quadrature excess noise per detected arm; two
    heterodyne arms give complex variance xi_det, counted exactly once.
    """
    R = _finite(R, 'detector efficiency', positive=True)
    if R > 1:
        raise FadingMIError('Detector efficiency must be in (0,1]')
    xi_det = _finite(xi_det, 'detector excess noise', nonnegative=True)
    xi_ch = _finite(xi_ch, 'channel excess noise', nonnegative=True)
    eta = np.asarray(eta, dtype=np.float64)
    alpha = np.asarray(amplitudes, dtype=np.complex128)
    if eta.ndim != 1 or not np.isfinite(eta).all() or np.any(eta < 0) or np.any(eta > 1):
        raise FadingMIError('Receiver eta nodes must be finite in [0,1]')
    if alpha.ndim != 1 or not np.isfinite(alpha).all():
        raise FadingMIError('Receiver amplitudes must be finite and one-dimensional')
    means = alpha[:, None] * np.sqrt(R * eta[None, :])
    variance = 1 + xi_det + .5 * R * eta * xi_ch
    return means, variance


def _mixture_log_likelihood(y, amplitudes, eta, weights, *, R, xi_det, xi_ch):
    """Integrate the joint complex likelihood; no I/Q factorization."""
    eta, weights = np.asarray(eta), np.asarray(weights)
    if (weights.shape != eta.shape or np.any(weights <= 0)
            or not np.isfinite(weights).all()
            or not math.isclose(float(weights.sum()), 1., abs_tol=1e-12, rel_tol=0)):
        raise FadingMIError('Likelihood quadrature weights must be positive and normalized')
    means, variance = receiver_parameters(amplitudes, eta, R=R, xi_det=xi_det, xi_ch=xi_ch)
    distance = np.asarray(y)[:, None, None] - means[None, :, :]
    log_pdf = -np.log(math.pi * variance)[None, None, :] - np.abs(distance) ** 2 / variance[None, None, :]
    return logsumexp(log_pdf + np.log(weights)[None, None, :], axis=2)


def _quadrature(fading, order, tolerance):
    raw = fading.raw
    if raw.P1 == 0:
        return np.array([0.]), np.array([1.]), dict(order=order, mass_error=0., mean_eta_error=0.,
                    mean_sqrt_eta_error=0., physical_probability_mass_quadrature=1.,
                    active_weight_normalization=1., validation_pass=True)
    d = raw.coefficients()['chi2']
    roots, base_weights = roots_legendre(order)
    u, base_weights = .5 * (roots + 1), .5 * base_weights
    log_eta = np.log(u) / d
    eta = np.exp(log_eta)
    log_density = np.array([fading.log_physical_active_density_in_log_eta(float(y)) for y in log_eta])
    active_weights = base_weights * np.exp(log_density - math.log(d) - np.log(u))
    active_mass = float(active_weights.sum())
    expected_m1 = raw.P1 * raw.active_moment(1.) / fading.active_normalization
    expected_mh = raw.P1 * raw.active_moment(.5) / fading.active_normalization
    diagnostics = dict(order=order, coordinate='u=exp(chi_squared*log_eta)',
                       active_probability_mass_quadrature=active_mass,
                       physical_probability_mass_quadrature=raw.P0 + raw.P1 * active_mass,
                       mass_error=abs(active_mass - 1),
                       mean_eta_error=abs(raw.P1 * float(active_weights @ eta) - expected_m1),
                       mean_sqrt_eta_error=abs(raw.P1 * float(active_weights @ np.sqrt(eta)) - expected_mh),
                       validation_tolerance=tolerance)
    valid = (np.isfinite(active_weights).all() and np.all(active_weights > 0)
             and max(diagnostics[k] for k in ('mass_error', 'mean_eta_error', 'mean_sqrt_eta_error')) <= tolerance)
    diagnostics['validation_pass'] = bool(valid)
    if not valid:
        return None, None, diagnostics
    # Numerical weights are normalized only after checking against the already
    # normalized physical law. This does not renormalize protected Eq. (10).
    diagnostics['active_weight_normalization'] = 1 / active_mass
    weights = raw.P1 * active_weights / active_mass
    if raw.P0 > 0:
        eta, weights = np.r_[0., eta], np.r_[raw.P0, weights]
    return eta, weights, diagnostics


def _physical_fading_samples(fading, samples, rng):
    """Exact rho=0 LN-minus-exponential rejection sampling, conditioned eta<=1."""
    raw = fading.raw
    if raw.rho != 0:
        raise FadingMIError('Unsupported nonzero boresight: rho must be zero')
    eta = np.zeros(samples)
    active_indices = np.flatnonzero(rng.random(samples) >= raw.P0)
    n = len(active_indices)
    if not n:
        return eta, dict(active_samples=0, outage_samples=samples, rejection_draws=0)
    retention = _finite(fading.active_normalization, 'active retention probability', positive=True)
    if retention > 1 + 1e-12:
        raise FadingMIError('Active retention exceeds one')
    budget = max(256, math.ceil(8 * n / retention))
    if budget > MAX_REJECTION_DRAWS:
        raise FadingMIError('Active conditioning needs more than bounded rejection budget; evaluation stopped')
    c = raw.coefficients()
    accepted, used, remaining = [], 0, n
    while remaining and used < budget:
        batch = min(budget - used, max(64, math.ceil(1.2 * remaining / retention)))
        log_eta = (math.log(c['B']) - .5 * raw.sigma_R2
                   + math.sqrt(raw.sigma_R2) * rng.standard_normal(batch)
                   - rng.exponential(1 / c['chi2'], batch))
        retained = np.exp(log_eta[log_eta <= 0])[:remaining]
        accepted.append(retained)
        remaining -= len(retained)
        used += batch
    if remaining:
        raise FadingMIError('Bounded exact physical sampling exhausted its rejection budget')
    eta[active_indices] = np.concatenate(accepted)
    return eta, dict(active_samples=n, outage_samples=samples - n, rejection_draws=used,
                     rejection_budget=budget, method='exact_rho_zero_lognormal_minus_exponential_conditioned_at_one')


def _information_samples(y, symbols, p, alpha, eta_nodes, weights, receiver, batch_size):
    if len(eta_nodes) == 1 and eta_nodes[0] == 0:
        # An all-outage receiver is independent of X: I(X;Y)=0 identically.
        return np.zeros(y.size)
    log_p = np.full_like(p, -math.inf)
    log_p[p > 0] = np.log(p[p > 0])
    information = np.empty(y.size)
    for start in range(0, y.size, batch_size):
        stop = min(start + batch_size, y.size)
        conditional = _mixture_log_likelihood(y[start:stop], alpha, eta_nodes, weights, **receiver)
        marginal = logsumexp(conditional + log_p[None, :], axis=1)
        selected = conditional[np.arange(stop - start), symbols[start:stop]]
        information[start:stop] = (selected - marginal) / math.log(2.)
    return information


def discrete_fading_mutual_information(probabilities, amplitudes, fading, *, R=.7, xi_det=.0135,
        xi_ch=.0186, samples=512, seed=20261013, quadrature_order=32, batch_size=16,
        quadrature_validation_tolerance=1e-6, likelihood_refinement_tolerance=1e-4,
        sampling_stderr_tolerance=.002, max_quadrature_order=256):
    """Numerical discrete/fading MI, never a Gaussian-input or AWGN substitute.

    The reported CI is a normal approximation for iid sampling error only.
    Quadrature refinements/moment checks are not a rigorous total-error bound.
    Nonconverged likelihoods return diagnostic I_AB and an invalid status.
    """
    p, alpha = _ensemble(probabilities, amplitudes)
    if type(samples) is not int or not 2 <= samples <= MAX_SAMPLES:
        raise FadingMIError(f'samples must be an integer in [2,{MAX_SAMPLES}]; larger runs need separate approval')
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise FadingMIError('seed must be a nonnegative integer below 2**64')
    if type(batch_size) is not int or not 1 <= batch_size <= 64:
        raise FadingMIError('batch_size must be an integer in [1,64]')
    if (type(quadrature_order) is not int or type(max_quadrature_order) is not int
            or not 4 <= quadrature_order or not 2 * quadrature_order <= max_quadrature_order <= MAX_QUADRATURE_ORDER):
        raise FadingMIError('Require 4<=quadrature_order and 2*order<=max_order<=256')
    validation_tolerance = _finite(quadrature_validation_tolerance, 'quadrature tolerance', positive=True)
    refinement_tolerance = _finite(likelihood_refinement_tolerance, 'likelihood refinement tolerance', positive=True)
    sampling_tolerance = _finite(sampling_stderr_tolerance, 'sampling stderr tolerance', positive=True)
    if fading.raw.rho != 0:
        raise FadingMIError('Unsupported nonzero boresight: rho must be zero')
    receiver = dict(R=float(R), xi_det=float(xi_det), xi_ch=float(xi_ch))
    receiver_parameters(alpha, np.array([0., 1.]), **receiver)
    identity = dict(scientific_model=MODEL, likelihood=MI_METHOD, receiver=receiver,
                    implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    channel_parameters=asdict(fading.raw), active_normalization=fading.active_normalization,
                    probabilities_hex=[float(v).hex() for v in p],
                    amplitudes_hex=[[float(v.real).hex(), float(v.imag).hex()] for v in alpha],
                    samples=samples, seed=seed, quadrature_order=quadrature_order,
                    max_quadrature_order=max_quadrature_order, batch_size=batch_size,
                    validation_tolerance=validation_tolerance, refinement_tolerance=refinement_tolerance,
                    sampling_stderr_tolerance=sampling_tolerance)
    context_hash = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    base = dict(MI_evaluation_method=MI_METHOD, MI_context_hash=context_hash, sample_count=samples,
                seed=seed, receiver_model='Y=sqrt(R*eta)*alpha+CN(0,1+R*eta*xi_ch/2+xi_det)',
                receiver_noise_reference='xi_det is output-referred; ideal heterodyne complex shot noise is one',
                physical_sampling=True, I_AB=None, stderr=None,
                confidence_interval_95_sampling_only=None,
                confidence_interval_method='normal_approximation_mean_plus_minus_1.96_stderr_sampling_only',
                sampling_stderr_tolerance=sampling_tolerance, sampling_precision_pass=False,
                symbol_entropy_bits=float(-np.sum(p[p > 0] * np.log2(p[p > 0]))),
                sampling_entropy_bounds_pass=False,
                total_error_certified=False, detector_security_verified=False)
    rng = np.random.default_rng(seed)
    symbols = rng.choice(len(p), size=samples, p=p)
    eta, sampling = _physical_fading_samples(fading, samples, rng)
    variance = 1 + receiver['xi_det'] + .5 * receiver['R'] * eta * receiver['xi_ch']
    y = (np.sqrt(receiver['R'] * eta) * alpha[symbols]
         + np.sqrt(variance / 2) * (rng.standard_normal(samples) + 1j * rng.standard_normal(samples)))
    rows, previous, previous_order, final = [], None, None, None
    order = quadrature_order
    converged = False
    while order <= max_quadrature_order:
        nodes, weights, diagnostic = _quadrature(fading, order, validation_tolerance)
        if diagnostic['validation_pass']:
            info = _information_samples(y, symbols, p, alpha, nodes, weights, receiver, batch_size)
            if not np.isfinite(info).all():
                raise FadingMIError('Nonfinite log likelihood/information; no clipping')
            diagnostic['I_AB_estimate'] = float(info.mean())
            if previous is not None:
                delta = info - previous
                difference = abs(float(delta.mean()))
                diagnostic.update(previous_order=previous_order,
                    paired_refinement_mean_difference=difference,
                    paired_refinement_stderr=float(delta.std(ddof=1) / math.sqrt(samples)),
                    likelihood_refinement_tolerance=refinement_tolerance,
                    likelihood_refinement_pass=difference <= refinement_tolerance)
                converged = difference <= refinement_tolerance
            final, previous, previous_order = info, info, order
        rows.append(diagnostic)
        if converged:
            break
        order *= 2
    base.update(sampling_diagnostics=sampling, quadrature_diagnostics=rows,
                quadrature_status='CONVERGED_NUMERICALLY' if converged else 'NOT_CONVERGED',
                status='VALID_NUMERICAL_ESTIMATE' if converged else 'QUADRATURE_NOT_CONVERGED',
                MI_valid=converged)
    if final is not None:
        estimate, stderr = float(final.mean()), float(final.std(ddof=1) / math.sqrt(samples))
        sampling_pass = stderr <= sampling_tolerance
        bounds_pass = -1e-12 <= estimate <= base['symbol_entropy_bits'] + 1e-12
        base.update(I_AB=estimate, stderr=stderr,
                    confidence_interval_95_sampling_only=[estimate - 1.96 * stderr, estimate + 1.96 * stderr],
                    effective_quadrature_order=previous_order, sampling_precision_pass=sampling_pass,
                    sampling_entropy_bounds_pass=bounds_pass,
                    MI_valid=converged and sampling_pass and bounds_pass)
        if converged and not sampling_pass:
            base['status'] = 'SAMPLING_PRECISION_NOT_MET'
        if converged and not bounds_pass:
            base['status'] = 'SAMPLING_BOUND_NOT_ESTABLISHED'
    return base
