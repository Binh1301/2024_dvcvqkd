"""Corrected full-fading entry; explicit legacy model retains old CLI semantics."""
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
from scripts.run_manuscript_literal_3moments import verified_candidate
from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
from src.manuscript_literal_3moments import LiteralChannel
from src.manuscript_corrected_3moments import PhysicalFadingDistribution
from src.manuscript_corrected_evaluator import MODEL, evaluate_candidate, validate_settings


def legacy_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scientific-model', choices=[MODEL], required=True)
    parser.add_argument('--source-payload', type=Path, required=True)
    parser.add_argument('--distance-km', type=float, required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/manuscript_corrected_3moments.json')
    args = parser.parse_args()
    settings = json.loads(args.config.read_text(encoding='utf-8'))
    validate_settings(settings)
    if (settings['scientific_model'] != MODEL
            or settings['physical_probability_law'] != 'condition_active_on_0_eta_le_1_preserve_AoA_atom'
            or settings['validated_boresight'] != 0. or settings['phase_noise'] != 'OFF'
            or settings['fading_protocol'] != 'fixed_C4_source_pooled_iid_phase_tracked_all_uses_including_outage'
            or settings['R'] != .7 or settings['xi_det'] != .0135 or settings['xi_ch'] != .0186
            or settings['beta_rec'] != .95 or settings['detector_security_convention'] != 'trusted'
            or settings['output_directory'] != 'results/' + MODEL):
        raise ValueError('Unsupported scientific configuration; explicit model update required')
    config = unconstrained_config()
    candidate = verified_candidate(args.source_payload.resolve(), config)
    vertical = config['channel']['h_hap_m'] - config['channel']['h_uav_m']
    if not math.isfinite(args.distance_km) or args.distance_km * 1000 < vertical:
        raise ValueError('Invalid distance for fixed HAP/UAV geometry')
    physical = derive_physical_inputs(.92,
        zenith_angle_rad_override=math.acos(vertical / (1000 * args.distance_km)),
        aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
    fading = PhysicalFadingDistribution(LiteralChannel.from_physical(physical),
                                        tolerance=settings['normalization_tolerance'])
    result = evaluate_candidate(candidate, fading, settings, distance_km=args.distance_km)
    record = result['record']
    out = ROOT / settings['output_directory'] / (record['scientific_context_hash'] + '.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(out)
    return 2 if record['status'] == 'BLOCKED_BY_SCIENTIFIC_MODEL' else 0


def main():
    # An explicit historical model identifier retains the original CLI semantics.
    # All unqualified corrected runs use the new two-mode full-fading pipeline.
    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument('--scientific-model')
    selected, _ = selector.parse_known_args()
    if selected.scientific_model == MODEL:
        return legacy_main()
    from scripts.run_full_fading_model import main as corrected_main
    return corrected_main()


if __name__ == '__main__':
    raise SystemExit(main())
