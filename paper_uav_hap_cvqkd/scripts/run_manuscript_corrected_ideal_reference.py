"""One authorized ideal-heterodyne reference; preserve all earlier modes/results."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
from scripts.run_manuscript_literal_3moments import verified_candidate
from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
from src.manuscript_literal_3moments import LiteralChannel
from src.manuscript_corrected_3moments import (
    PhysicalFadingDistribution, effective_fading_channel, corrected_z_star,
    corrected_covariance, admissible_correlation_interval, holevo_interval_maximizer, _ideal_holevo,
)
from src.manuscript_corrected_evaluator import validate_settings, validate_cached_candidate, scientific_context
from src.manuscript_corrected_mi import discrete_fading_mutual_information

SOURCE = 'results/exact_mb_test2/exact_source_cache/77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c.json'
OUTPUT = 'results/manuscript_corrected_3moments/ideal_heterodyne_reference_20261013'


def _effective_gaussian_mi(ensemble, effective, orders):
    """Discrete input, AWGN surrogate; distinct from the actual pooled mixture."""
    import torch
    from src.cvqkd.mutual_information import deterministic_mutual_information
    rows = []
    for order in orders:
        value = float(deterministic_mutual_information(ensemble,
            torch.tensor([effective['T_eff']], dtype=torch.float64),
            torch.tensor([effective['xi_eff']], dtype=torch.float64),
            quadrature_order=order, implementation='product')[0])
        rows.append(dict(order=order, I_AB=value))
    difference = abs(rows[-1]['I_AB'] - rows[-2]['I_AB'])
    return dict(I_AB=rows[-1]['I_AB'], MI_method='discrete_QAM_effective_Gaussian_AWGN_approximation',
                quadrature_rows=rows, last_refinement_difference=difference,
                refinement_tolerance=1e-8, numerical_refinement_pass=difference <= 1e-8,
                sigma2_complex=1+effective['effective_excess_noise_output']/2,
                actual_fading_mixture=False, approximation_error_bound='NOT_ESTABLISHED')


def evaluate_reference(settings):
    validate_settings(settings)
    required = dict(R=1., xi_det=0., detector_security_convention='ideal',
                    detector_model='ideal_heterodyne', AO='OFF',
                    reference_distance_km=21.9393102292, reference_nu_raw=.165, reference_VA=5.5,
                    run_output_directory=OUTPUT, effective_gaussian_GH_orders=[8,16,32],
                    sampling_stderr_tolerance=.002, MI_samples=4096)
    for key, value in required.items():
        if settings.get(key) != value:
            raise ValueError(f'Unsupported one-reference setting: {key}')
    config = unconstrained_config()
    candidate = verified_candidate(ROOT/SOURCE, config)
    if (candidate['nu_raw'].hex() != float(.165).hex()
            or candidate['V_A'].hex() != float(5.5).hex()):
        raise ValueError('Only the authorized exact source pair is permitted')
    ensemble = validate_cached_candidate(candidate)
    distance = settings['reference_distance_km']
    vertical = config['channel']['h_hap_m'] - config['channel']['h_uav_m']
    physical = derive_physical_inputs(.92,
        zenith_angle_rad_override=math.acos(vertical/(1000*distance)),
        aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
    fading = PhysicalFadingDistribution(LiteralChannel.from_physical(physical),
                                        tolerance=settings['normalization_tolerance'])
    moments = fading.moments(R=1.,xi_det=0.,xi_ch=settings['xi_ch'])
    effective = effective_fading_channel(moments,candidate['V_A'])
    z = corrected_z_star(effective,candidate['C'],candidate['w'])
    cov = corrected_covariance(effective,candidate['V_A'],z)
    chi_star = _ideal_holevo(cov)
    interval = admissible_correlation_interval(effective,candidate['V_A'],candidate['C'],candidate['w'])
    maximum = holevo_interval_maximizer(effective,candidate['V_A'],candidate['C'],candidate['w'],
        detector_security_convention='ideal',R=1.,xi_det=0.,grid_size=settings['holevo_grid_size'],
        tolerance=settings['holevo_tolerance'])
    approximation = _effective_gaussian_mi(ensemble,effective,settings['effective_gaussian_GH_orders'])
    mixture = discrete_fading_mutual_information(
        ensemble.probabilities.detach().cpu().numpy().reshape(-1),
        ensemble.amplitudes.detach().cpu().numpy().reshape(-1),fading,
        R=1.,xi_det=0.,xi_ch=settings['xi_ch'],samples=settings['MI_samples'],
        seed=settings['MI_seed'],quadrature_order=settings['MI_quadrature_order'],
        sampling_stderr_tolerance=settings['sampling_stderr_tolerance'])
    identity,_ = scientific_context(candidate,fading,settings,distance)
    identity['ideal_reference_runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    digest=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    record={**moments,**effective, 'scientific_model':'manuscript_corrected_3moments',
        'detector_model':'ideal_heterodyne','detector_security_convention':'ideal',
        'distance_km':distance,'nu_raw':candidate['nu_raw'],'VA':candidate['V_A'],
        'C':candidate['C'],'w':candidate['w'],'source_cache_key':candidate['source_cache_key'],
        'ensemble_hash':candidate['ensemble_hash'],'scientific_context_hash':digest,
        'raw_pdf_mass':moments['raw_probability_mass'],'physical_pdf_mass':moments['physical_probability_mass'],
        'channel_excess_noise_output':effective['mean_channel_excess_noise_output'],
        'N_eff':effective['effective_excess_noise_output'],
        'a':cov['a'],'b':cov['b'],'Z_star':z,'covariance_at_Z_star':cov,
        'lambda_1':cov['lambda_1'],'lambda_2':cov['lambda_2'],'lambda_3':cov['lambda_3'],
        'chi_BE_at_Z_star':chi_star,'Z_admissible_interval':[interval['lower'],interval['upper']],
        'correlation_interval':interval,'Z_worst_case':maximum['Z_worst'],
        'chi_BE_worst_case':maximum['chi_BE'],'holevo_interval_diagnostics':maximum,
        'I_AB':mixture['I_AB'],'MI_method':mixture['MI_evaluation_method'],'MI_diagnostics':mixture,
        'beta_I_AB':None,'K_at_Z_star':None,'K_conservative':None,
        'validated_security_lower_bound':'NOT_ESTABLISHED',
        'effective_Gaussian_approximation':approximation,
        'phase_noise':'OFF','AO':'OFF','reference_candidates_evaluated':1,
        'scientific_validation_status':'NUMERICAL_DIAGNOSTIC_ONLY'}
    if mixture['I_AB'] is not None:
        record['beta_I_AB']=settings['beta_rec']*mixture['I_AB']
        record['K_at_Z_star']=record['beta_I_AB']-chi_star
        if maximum['chi_BE'] is not None:
            record['K_conservative']=record['beta_I_AB']-maximum['chi_BE']
    record['K_interpretation']='signed Monte Carlo point estimates; numeric interval maximum; no certified lower bound'
    approximation['beta_I_AB']=settings['beta_rec']*approximation['I_AB']
    approximation['K_at_Z_star']=approximation['beta_I_AB']-chi_star
    approximation['K_conservative']=(approximation['beta_I_AB']-maximum['chi_BE']
                                   if maximum['chi_BE'] is not None else None)
    approximation['K_interpretation']='effective Gaussian channel approximation, not actual pooled-fading SKR'
    if maximum['chi_BE'] is None:
        record['scientific_validation_status']='NOT_ESTABLISHED_HOLEVO_INTERVAL_NUMERICS'
    elif not mixture['MI_valid']:
        record['scientific_validation_status']='NOT_ESTABLISHED_MI_PRECISION'
    return dict(identity=identity,record=record)


GROUPS={
    'PHYSICAL CHANNEL':['raw_pdf_mass','physical_pdf_mass','mean_eta','mean_sqrt_eta','mean_eta_xi_total'],
    'EFFECTIVE CHANNEL':['T_eff','fading_noise_output','channel_excess_noise_output','N_eff','xi_eff'],
    'SOURCE':['nu_raw','VA','C','w'], 'COVARIANCE':['a','b','Z_star'],
    'HOLEVO':['lambda_1','lambda_2','lambda_3','chi_BE_at_Z_star','Z_admissible_interval','Z_worst_case','chi_BE_worst_case'],
    'MUTUAL INFORMATION':['I_AB','MI_method'],
    'SECRET KEY RATE':['beta_I_AB','K_at_Z_star','K_conservative','scientific_validation_status']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/manuscript_corrected_3moments_ideal_reference.json')
    args=parser.parse_args()
    out=ROOT/OUTPUT
    out.mkdir(parents=True,exist_ok=True)
    # Exclusive marker prevents accidentally launching this authorized point twice.
    with (out/'execution_started.json').open('x',encoding='utf-8') as stream:
        json.dump(dict(scope='ONE_REFERENCE_ONLY',config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest()),stream)
    start=time.monotonic()
    result=evaluate_reference(json.loads(args.config.read_text(encoding='utf-8')))
    result['elapsed_seconds']=time.monotonic()-start
    with (out/'reference_result.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    record=result['record']
    for title,keys in GROUPS.items():
        print(title)
        for key in keys:
            value=record.get(key)
            print(f'{key} = {value if value is not None else "NOT_ESTABLISHED"}')
    print('MI_sampling_stderr =',record['MI_diagnostics']['stderr'])
    print('MI_precision_status =',record['MI_diagnostics']['status'])
    print('EFFECTIVE GAUSSIAN APPROXIMATION =',json.dumps(record['effective_Gaussian_approximation']))
    print(out/'reference_result.json')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
