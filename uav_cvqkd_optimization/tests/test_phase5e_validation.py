"""Geometry and provenance validation without fresh scientific evaluations."""
import pytest


def test_direct_coordinates_do_not_consume_lookup_group_or_angle():
    from uav_qkd.phase5e_validation import direct_positions
    from uav_qkd.config import load_config
    from uav_qkd.skr_pilot import ROOT
    config=load_config(ROOT/'configs/channel/optimized_physical_setup.yaml')
    points=direct_positions(config)
    assert len(points)==7
    assert (points[0]['x_m'],points[0]['y_m'],points[0]['zenith_deg'])==(1000.,1000.,0.)
    assert any(p['x_m']==2000. and p['y_m']==2000. for p in points)
    assert all('group_id' not in p for p in points)
    assert all(p['geometry_origin']=='independent_coordinate_geometry_not_lookup_mapping' for p in points)


def test_full_result_validation_refuses_unsealed_data_before_any_computation(tmp_path):
    from uav_qkd.phase5e_validation import validate_full_data
    with pytest.raises(ValueError,match='sealed'):
        validate_full_data(tmp_path)
    assert list(tmp_path.iterdir())==[]


def test_direct_comparison_does_not_clip_signed_skr_or_ignore_winner():
    from uav_qkd.phase5e_validation import compare_winner
    a=dict(eta_f=.2,xi_f=.1,I_AB=.1,chi_BE=.2,K_raw=-.105,VA=1.,nu_raw=.3,ensemble_hash='same')
    assert compare_winner(a,a)['passed']
    assert not compare_winner(dict(a,K_raw=.105),a)['passed']
    assert not compare_winner(dict(a,ensemble_hash='other'),a)['passed']


def test_windows_output_manifest_paths_are_normalized_without_collisions():
    from uav_qkd.phase5e_validation import normalized_output_seal
    assert normalized_output_seal({'full\\f0000.json':'hash'})=={'full/f0000.json':'hash'}
    with pytest.raises(ValueError,match='collision'):
        normalized_output_seal({'full\\f0000.json':'hash','full/f0000.json':'hash'})


@pytest.mark.parametrize('field,value',[('rate_units','bits/s'),('xi_ch',.0186),('producer_sha256','other'),('paper_admissible',True)])
def test_detached_npz_wrong_metadata_is_refused(field,value):
    import numpy as np
    from uav_qkd.phase5e_validation import check_npz_metadata
    m=dict(config_sha256='config',candidate_pool_sha256='pool')
    rows=[dict(MB_source_evidence_class='INSUFFICIENT_EVIDENCE',Uniform_source_evidence_class='INSUFFICIENT_EVIDENCE')]
    d={k:np.array(v) for k,v in dict(config_sha256='config',input_manifest_sha256='input',candidate_pool_sha256='pool',
       producer_sha256='producer',geometry_mode='radial_exact',coordinate_units='m',rate_units='bits/use',xi_ch=.0136,xi_det=.005,paper_admissible=False).items()}
    d.update({f+'_source_evidence_class':np.array(['INSUFFICIENT_EVIDENCE']) for f in ('MB','Uniform')})
    check_npz_metadata(d,m,'input','producer',rows)
    d[field]=np.array(value)
    with pytest.raises(ValueError,match='metadata'):check_npz_metadata(d,m,'input','producer',rows)


def test_empty_pilot_data_cannot_pass_by_vacuous_truth():
    from uav_qkd.phase5e_validation import require_pilot_positions
    with pytest.raises(ValueError,match='five'):
        require_pilot_positions({'comparisons':[],'reproduction_checks':[]},{'points':[]})


def test_pilot_summary_requires_original_output_seal(tmp_path):
    from uav_qkd.phase5e_validation import load_verified_pilot
    with pytest.raises(ValueError,match='seal'):load_verified_pilot(tmp_path)
