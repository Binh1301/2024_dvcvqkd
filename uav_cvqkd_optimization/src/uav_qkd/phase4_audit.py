"""Audit the new reference configurations/interfaces; never run a paper mission.

python -m uav_qkd.phase4_audit --output docs/phase4_validation/reference_audit
"""
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
from .hap_uav_channel import load_channel_reference,reference_geometry
from .finite_size_reference import load_finite_reference

ROOT=Path(__file__).resolve().parents[2]


def compare_lookup_reference(reference,protocol):
    physical=protocol['physical']
    fields={
        'hap_altitude_m':('h_hap_km',1000.),'uav_altitude_m':('h_uav_km',1000.),
        'receiver_aperture_diameter_m':('Dr_m',1.),'beam_full_divergence_rad':('divergence_full_urad',1e-6),
        'transmitter_jitter_angle_rad':('jitter_urad',1e-6),'uav_position_sd_m':('sigma_h_m',1.),
        'wavelength_m':('wavelength_m',1.),'zenith_atmospheric_transmittance':('tau_zen',1.),
        'ground_turbulence_cn2_m_minus_2_3':('Cn2_ground',1.),'rms_wind_speed_m_s':('wind_m_s',1.),
        'receiver_fov_half_angle_rad':('FOV_half_rad',1.),'uav_angular_fluctuation_sd_rad':('sigma_AoA_rad',1.),
    }
    comparison=[]
    for new,(old,scale) in fields.items():
        ref=float(reference[new]);prior=float(physical[old])*scale
        comparison.append(dict(parameter=new,reference=ref,lookup=prior,
                               matches=bool(np.isclose(ref,prior,rtol=1e-12,atol=0))))
    mismatches=[row['parameter'] for row in comparison if not row['matches']]
    beta_matches=bool(np.isclose(reference['reconciliation_efficiency'],protocol['beta'],rtol=1e-12,atol=0))
    normalization_matches=str(protocol.get('source_normalization','')).split(';',1)[0].strip()==reference['existing_module_normalization']
    return dict(physical_subset_matches=not mismatches,full_configuration_compatibility='NOT_ESTABLISHED',
                beta_matches=beta_matches,normalization_matches=normalization_matches,
                physical_mismatches=mismatches,comparison=comparison,
                source_evidence_promoted=False,paper_admissible=False,
                unresolved_reference_noise=[name for name in ('channel_excess_noise_snu','detector_excess_noise_snu') if reference.get(name) is None],
                conclusion='Different physical profiles: receiver30 values cannot represent the new Section-IV experiment' if mismatches
                           else 'Physical subset comparison alone does not establish full protocol/geometry/noise compatibility or admissibility')


def audit_references(output,channel_path=None,finite_path=None,lookup_protocol_path=None):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise FileExistsError('Choose a new empty audit directory; historical artifacts are preserved')
    cp=Path(channel_path or ROOT/'configs/channel/hap_uav_mb_reference.yaml')
    fp=Path(finite_path or ROOT/'configs/finite_size/ieee_2025_reference.yaml')
    lp=Path(lookup_protocol_path or ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json')
    channel=load_channel_reference(cp);finite=load_finite_reference(fp)
    geometry=reference_geometry(channel)
    protocol=json.loads(lp.read_text(encoding='utf-8'))
    compatibility=compare_lookup_reference(channel,protocol)
    report=dict(status='CURRENTLY_VERIFIED_PASS',scope='reference-config/interface audit only',
                paper_mode='NOT_RUN',Z_w_core='AUTHOR_CONFIRMED_CORRECT_UNCHANGED_NOT_REVALIDATED',
                core_evaluations=0,closed_form_channel_evaluations=0,reference_geometry=asdict(geometry),
                finite_reference=finite['derived'],lookup_compatibility=compatibility,
                missing_mission_inputs=['HAP horizontal coordinates','q0','E_max','graph','prediction horizon','f_s','eta_valid or m0',
                                        'cloud mode approval and sourced attenuation or layer/threshold/LOS settings','lambda','security claim scope'])
    output.mkdir(parents=True,exist_ok=True)
    inputs={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (cp,fp,lp)}
    producers={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in
               [ROOT/'src/uav_qkd'/name for name in ('hap_uav_channel.py','finite_size_reference.py','cloud_channel.py','phase4_audit.py')]}
    report['input_sha256']=inputs;report['producer_sha256']=producers
    (output/'reference_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='docs/phase4_validation/reference_audit')
    args=parser.parse_args(argv)
    report=audit_references(args.output)
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
