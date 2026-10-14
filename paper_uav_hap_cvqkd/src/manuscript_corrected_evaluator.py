"""Existing-source-only integration; unsupported receiver security never yields SKR."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from src.manuscript_corrected_3moments import (
    PhysicalFadingDistribution, effective_fading_channel, corrected_z_star,
    corrected_covariance, admissible_correlation_interval, holevo_interval_maximizer,
)
from src.manuscript_corrected_mi import discrete_fading_mutual_information

MODEL = 'manuscript_corrected_3moments'
ROOT = Path(__file__).resolve().parents[1]


def validate_settings(settings):
    required = dict(scientific_model=MODEL,
        physical_probability_law='condition_active_on_0_eta_le_1_preserve_AoA_atom',
        validated_boresight=0., phase_noise='OFF',
        fading_protocol='fixed_C4_source_pooled_iid_phase_tracked_all_uses_including_outage',
        xi_ch=.0186, beta_rec=.95,
        MI_method='actual_discrete_pooled_fading_mixture_sampling_with_likelihood_quadrature',
        output_directory='results/' + MODEL)
    for key, value in required.items():
        if settings.get(key) != value:
            raise ValueError(f'Unsupported corrected-model setting: {key}')
    detector = (settings.get('detector_security_convention'), settings.get('R'), settings.get('xi_det'))
    if detector not in [('trusted', .7, .0135), ('ideal', 1., 0.)]:
        raise ValueError('Unsupported detector convention or receiver parameters')
    if type(settings['MI_samples']) is not int or not 2 <= settings['MI_samples'] <= 4096:
        raise ValueError('Unsupported MI workload; larger runs require separate approval')


def validate_cached_candidate(candidate):
    """Authenticate C,w and the transmitted ensemble without invoking an oracle."""
    from scripts.exact_cache_provenance import source_settings, verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    from src.cvqkd.covariance import quadrature_symmetry_diagnostics
    path = Path(candidate['source_path'])
    if not path.is_absolute():
        path = ROOT / path
    data = path.read_bytes()
    baseline_path = ROOT / 'results/manuscript_corrected_3moments/implementation_validation/baseline_manifest.json'
    config = json.loads((ROOT / 'configs/manuscript_corrected_3moments.json').read_text(encoding='utf-8'))
    if hashlib.sha256(baseline_path.read_bytes()).hexdigest() != config['protected_input_manifest_sha256']:
        raise ValueError('Protected source baseline manifest identity changed')
    baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    relative = str(path.resolve().relative_to(ROOT)).replace('\\', '/')
    if baseline['protected_hashes'].get(relative) != hashlib.sha256(data).hexdigest():
        raise ValueError('Source payload bytes differ from protected existing-source snapshot')
    payload = json.loads(data)
    verified = verify_source_payload(payload, source_settings(unconstrained_config()))
    if (candidate['source_cache_key'] not in (verified['historical_cache_key'], verified['canonical_source_cache_key'])
            or candidate['ensemble_hash'] != payload['ensemble_hash']
            or float(candidate['V_A']).hex() != payload['V_A_hex']
            or float(candidate['nu_raw']).hex() != payload['nu_mb_raw_hex']
            or candidate['C'] != payload['C'] or candidate['w'] != payload['w']):
        raise ValueError('Cached source identity mismatch; no approximate C,w reuse')
    ensemble = candidate['ensemble']
    ensemble.validate(tolerance=1e-12)
    if ensemble_hash(ensemble) != candidate['ensemble_hash']:
        raise ValueError('Transmitted ensemble/cache identity mismatch')
    if not math.isclose(float(ensemble.computed_va()[0]), candidate['V_A'], rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError('VA != 2 average photon number')
    if not quadrature_symmetry_diagnostics(ensemble).standard_form_supported:
        raise ValueError('Centered C4 source required for scalar covariance')
    return ensemble


def scientific_context(candidate, fading, settings, distance_km):
    files = ['src/manuscript_corrected_3moments.py', 'src/manuscript_corrected_mi.py',
             'src/manuscript_corrected_evaluator.py', 'scripts/run_manuscript_corrected_3moments.py',
             'src/manuscript_literal_3moments.py', 'scripts/run_manuscript_literal_3moments.py',
             'scripts/exact_cache_provenance.py', 'scripts/run_exact_mb_test2.py',
             'scripts/run_theta10_D55_unconstrained_three_scheme.py',
             'scripts/calculate_channel_pdf_and_moments.py']
    files += [str(p.relative_to(ROOT)).replace('\\', '/') for folder in ['src/modulation', 'src/channel', 'src/cvqkd']
              for p in sorted((ROOT / folder).glob('*.py'))]
    identity = dict(scientific_model=MODEL, numerical=settings, distance_km=distance_km,
                    raw_channel=fading.raw.__dict__, source_cache_key=candidate['source_cache_key'],
                    ensemble_hash=candidate['ensemble_hash'], C_hex=float(candidate['C']).hex(),
                    w_hex=float(candidate['w']).hex(), nu_raw_hex=float(candidate['nu_raw']).hex(),
                    VA_hex=float(candidate['V_A']).hex(),
                    source_payload_sha256=hashlib.sha256((ROOT / candidate['source_path']).read_bytes()).hexdigest(),
                    implementations={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
                    default_config_sha256=hashlib.sha256((ROOT / 'configs/default.yaml').read_bytes()).hexdigest())
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return identity, digest


def evaluate_candidate(candidate, fading: PhysicalFadingDistribution, settings, *, distance_km):
    validate_settings(settings)
    ensemble = validate_cached_candidate(candidate)
    identity, context_hash = scientific_context(candidate, fading, settings, distance_km)
    moments = fading.moments(R=settings['R'], xi_det=settings['xi_det'], xi_ch=settings['xi_ch'])
    effective = effective_fading_channel(moments, candidate['V_A'])
    z_star = corrected_z_star(effective, candidate['C'], candidate['w'])
    interval = admissible_correlation_interval(effective, candidate['V_A'], candidate['C'], candidate['w'])
    record = dict(scientific_model=MODEL, manuscript_version=settings['manuscript_version'],
                  requested_manuscript_status=settings['requested_manuscript_status'],
                  available_reference_version=settings['available_reference_version'],
                  available_reference_sha256=settings['available_reference_sha256'],
                  authoritative_equation_source=settings['authoritative_equation_source'],
                  distance_km=distance_km, nu_raw=candidate['nu_raw'], VA=candidate['V_A'],
                  C=candidate['C'], w=candidate['w'], source_cache_key=candidate['source_cache_key'],
                  ensemble_hash=candidate['ensemble_hash'], scientific_context_hash=context_hash,
                  detector_efficiency=settings['R'], detector_excess_noise=settings['xi_det'],
                  detector_security_convention=settings['detector_security_convention'],
                  beta_rec=settings['beta_rec'])
    record.update(moments)
    record.update(effective)
    record.update(a=candidate['V_A']+1, Z_star=z_star, correlation_interval=interval, Z_lower=interval.get('Z_lower'),
                  Z_upper=interval.get('Z_upper'), Z_worst=None, lambda_1=None, lambda_2=None,
                  conditional_symplectic_eigenvalues=None, I_AB=None,
                  MI_evaluation_method=settings['MI_method'], chi_BE=None, K_raw=None, K_operational=None,
                  correlation_bound_status=interval.get('correlation_bound_status'), covariance_physicality_status='NOT_EVALUATED',
                  unavailable_fields={})
    try:
        covariance = corrected_covariance(effective, candidate['V_A'], z_star)
        record.update(covariance_at_Z_star=covariance, covariance_physicality_status='CURRENTLY_VERIFIED_PASS')
    except ValueError as error:
        record['covariance_physicality_status'] = 'Z_STAR_OUTSIDE_PHYSICAL_REGION'
        record['covariance_at_Z_star_failure'] = str(error)
    security = holevo_interval_maximizer(effective, candidate['V_A'], candidate['C'], candidate['w'],
               detector_security_convention=settings['detector_security_convention'],
               R=settings['R'], xi_det=settings['xi_det'], grid_size=settings['holevo_grid_size'],
               tolerance=settings['holevo_tolerance'])
    record['holevo_diagnostics'] = security
    if security.get('chi_BE') is None:
        reason = security.get('failure', 'Verified nonideal-detector Holevo model unavailable')
        record.update(status='BLOCKED_BY_SCIENTIFIC_MODEL', security_bound_status=security.get('status'))
        record['unavailable_fields'] = {key: reason for key in ['Z_worst', 'lambda_1', 'lambda_2',
            'conditional_symplectic_eigenvalues', 'chi_BE', 'K_raw', 'K_operational']}
        record['unavailable_fields']['I_AB'] = 'NOT_RUN: receiver security prerequisite unresolved; no reference MI launched'
        return dict(identity=identity, record=record)
    mi = discrete_fading_mutual_information(ensemble.probabilities.detach().cpu().numpy().reshape(-1),
           ensemble.amplitudes.detach().cpu().numpy().reshape(-1), fading, R=settings['R'],
           xi_det=settings['xi_det'], xi_ch=settings['xi_ch'], samples=settings['MI_samples'],
           seed=settings['MI_seed'], quadrature_order=settings['MI_quadrature_order'])
    record['MI_diagnostics'] = mi
    record.update(I_AB=mi.get('I_AB'), MI_evaluation_method=mi.get('MI_evaluation_method'))
    if not mi.get('MI_valid'):
        record.update(status='BLOCKED_BY_SCIENTIFIC_MODEL', failure='MI numerical convergence not established')
        return dict(identity=identity, record=record)
    record.update(chi_BE=security['chi_BE'], Z_worst=security['Z_worst'],
                  lambda_1=security['lambda_1'], lambda_2=security['lambda_2'],
                  conditional_symplectic_eigenvalues=security['conditional_symplectic_eigenvalues'])
    record['K_raw'] = settings['beta_rec'] * record['I_AB'] - record['chi_BE']
    record['K_operational'] = max(0., record['K_raw'])
    record.update(status='ASYMPTOTIC_DIAGNOSTIC_SAMPLING_ESTIMATE', security_bound_status=security.get('status'))
    return dict(identity=identity, record=record)
