"""Explicit single-point, existing-exact-source-only manuscript backend entry.

No sweep, optimization or new source-moment computation is available here.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
from scripts.exact_cache_provenance import json_hash, source_settings, verify_source_payload
from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload, unconstrained_config
from src.manuscript_literal_3moments import MODEL, MANUSCRIPT_VERSION, MANUSCRIPT_SHA256, LiteralChannel, ManuscriptModelError, evaluate_candidate


def verified_candidate(source_path, config):
    payload = json.loads(source_path.read_text(encoding='utf-8'))
    payload['_provenance'] = verify_source_payload(payload, source_settings(config))
    payload['_path'] = str(source_path.resolve())
    return candidate_from_payload(config, {payload['ensemble_hash']: payload}, 'MB',
                                  float.fromhex(payload['nu_mb_raw_hex']), float.fromhex(payload['V_A_hex']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scientific-model', choices=[MODEL], required=True)
    parser.add_argument('--source-payload', type=Path, required=True)
    parser.add_argument('--manuscript', type=Path, required=True)
    parser.add_argument('--distance-km', type=float, required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/manuscript_literal_3moments.json')
    args = parser.parse_args()
    if hashlib.sha256(args.manuscript.read_bytes()).hexdigest() != MANUSCRIPT_SHA256:
        raise ValueError('Manuscript version/hash mismatch')
    settings = json.loads(args.config.read_text(encoding='utf-8'))
    if settings['scientific_model'] != MODEL or settings['manuscript_sha256'] != MANUSCRIPT_SHA256:
        raise ValueError('Wrong model configuration')
    if (settings['manuscript_version'] != MANUSCRIPT_VERSION
            or settings['equation_11_to_20_mapping'] != 'T=eta_f; xi=xi_f'
            or settings['MI_mapping'] != 'existing_discrete_GH8_product_with_T_eta_f_and_epsilon_xi_f'
            or settings['output_directory'] != 'results/' + MODEL):
        raise ValueError('Unsupported version/mapping/output configuration')
    if settings['beta_rec'] != .95 or settings['quadrature_order'] != 8 or settings['renormalize'] or settings['integration_interval'] != [0, 1]:
        raise ValueError('Unsupported scientific configuration; no silent overrides')
    config = unconstrained_config()
    candidate = verified_candidate(args.source_payload, config)
    vertical = config['channel']['h_hap_m'] - config['channel']['h_uav_m']
    if not math.isfinite(args.distance_km) or args.distance_km * 1000 < vertical:
        raise ValueError('Invalid distance for fixed HAP/UAV geometry')
    physical = derive_physical_inputs(.92, zenith_angle_rad_override=math.acos(vertical / (1000 * args.distance_km)),
                                     aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
    channel = LiteralChannel.from_physical(physical)
    moments = channel.moments(R=settings['R'], xi_det=settings['xi_det'], xi_ch=settings['xi_ch'],
                              normalization_tolerance=settings['normalization_tolerance'])
    physical_identity = dict(channel=channel.__dict__, distance_km=args.distance_km,
                             receiver_diameter_m=.55, w0_m=.0986760647169751, tau_zen=.92,
                             physics_mapping='PDF Eq6 effective aperture; Eq5 raw Rytov; existing geometry/HV/G_d')
    producer_files = ['src/manuscript_literal_3moments.py', 'scripts/run_manuscript_literal_3moments.py',
                      'scripts/calculate_channel_pdf_and_moments.py', 'scripts/exact_cache_provenance.py',
                      'scripts/run_exact_mb_test2.py', 'scripts/run_theta10_D55_unconstrained_three_scheme.py',
                      'src/modulation/normalization.py', 'src/modulation/qam256.py', 'src/modulation/joint_ps_gs.py',
                      'src/cvqkd/mutual_information.py', 'src/cvqkd/covariance.py']
    producer_files += [str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT / 'src/channel').glob('*.py')]
    identity = dict(scientific_model=MODEL, manuscript_sha256=MANUSCRIPT_SHA256, numerical=settings,
                    physical=physical_identity, source_identity=candidate['canonical_source_cache_key'],
                    source_C_hex=candidate['C'].hex(), source_w_hex=candidate['w'].hex(),
                    implementations={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in producer_files},
                    config_input_sha256=hashlib.sha256((ROOT / 'configs/default.yaml').read_bytes()).hexdigest())
    cache_id = json_hash(identity)
    output_dir = ROOT / 'results' / MODEL
    output = output_dir / (cache_id + '.json')
    if output.exists():
        raise FileExistsError('Preserve existing records; this model-specific identifier already exists')
    try:
        record = evaluate_candidate(candidate, moments, distance_km=args.distance_km,
                                    physical_config_hash=json_hash(physical_identity), numerical_config_hash=json_hash(settings))
    except ManuscriptModelError as error:
        record = dict(scientific_model=MODEL, manuscript_version=MANUSCRIPT_VERSION, manuscript_sha256=MANUSCRIPT_SHA256, status='MODEL_OR_NUMERICAL_FAILURE',
                      failure=str(error), SKR=None, nu_raw=candidate['nu_raw'], VA=candidate['V_A'],
                      C=candidate['C'], w=candidate['w'], physical_config_hash=json_hash(physical_identity),
                      numerical_config_hash=json_hash(settings), distance_km=args.distance_km,
                      source_cache_key=candidate['source_cache_key'], **moments)
        for key in ('eta_f', 'xi_f', 'eta_f_xi_f', 'a', 'b', 'Z_star', 'lambda_1', 'lambda_2', 'lambda_3', 'I_AB', 'chi_BE'):
            record.setdefault(key, None)
    output_dir.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(identity=identity, cache_identifier=cache_id, record=record), indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(output)
    return 0 if record['status'].startswith('PASS') else 2


if __name__ == '__main__':
    raise SystemExit(main())
