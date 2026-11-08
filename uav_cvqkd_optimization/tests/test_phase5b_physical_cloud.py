"""Author-input checks and arithmetic/LOS fixtures; no new research SKR data."""
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from uav_qkd.config import load_config
from uav_qkd.cloud_model import CloudField, GaussianCluster

ROOT = Path(__file__).parents[1]
LOOKUP = ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106'


def test_author_tuned_setup_separate_from_original_and_provenance_bound():
    from uav_qkd.hap_uav_channel import load_channel_reference
    old = load_channel_reference(ROOT/'configs/channel/hap_uav_mb_reference.yaml')
    tuned = load_channel_reference(ROOT/'configs/channel/optimized_physical_setup.yaml')
    assert [old[k] for k in ('receiver_aperture_diameter_m', 'beam_full_divergence_rad',
                             'transmitter_jitter_angle_rad', 'uav_position_sd_m')] == [.08,233e-6,15.61e-6,1.]
    fields = dict(receiver_aperture_diameter_m=.30, beam_full_divergence_rad=35e-6,
                  transmitter_jitter_angle_rad=1.561e-6, uav_position_sd_m=.10,
                  detector_excess_noise_snu=.005, channel_excess_noise_snu=.0136)
    assert {k:tuned[k] for k in fields} == fields
    provenance = tuned['author_supplied_provenance']
    assert provenance['status'] == 'AUTHOR_SUPPLIED'
    assert set(provenance['confirmed_fields']) == set(fields)
    assert hashlib.sha256(Path(provenance['attachment_path']).read_bytes()).hexdigest() == provenance['attachment_sha256']
    assert tuned['historical_noise_conflict_requires_confirmation'] is True
    assert tuned['paper_mode'] == 'NOT_RUN' and tuned['cloud_coupling']['author_approved'] is False
    assert old['channel_excess_noise_snu'] is None


def test_beam_waist_and_receiver_footprint_are_distinct_full_angle_SI():
    from uav_qkd.physical_setup import beam_sanity
    c = load_config(ROOT/'configs/channel/optimized_physical_setup.yaml')
    result = beam_sanity(c)
    w0 = 2*1550e-9/(math.pi*35e-6)
    assert result['transmitter_waist_radius_m'] == pytest.approx(w0)
    assert .028 < w0 < .029
    assert [r['distance_m'] for r in result['receivers']] == [19000.,21940.]
    for row in result['receivers']:
        expected = math.sqrt(w0*w0+(row['distance_m']*35e-6/2)**2)
        assert row['beam_radius_m'] == pytest.approx(expected)
        assert row['beam_diameter_m'] == 2*row['beam_radius_m']
        assert row['beam_radius_m'] > 10*w0
        capture = -math.expm1(-2*.15**2/expected**2)
        assert row['ideal_centered_circular_capture'] == pytest.approx(capture)
        assert 0 < row['diffraction_only_manuscript_erf_approx'] < 1
    assert result['receivers'][0]['ideal_centered_circular_capture'] > result['receivers'][1]['ideal_centered_circular_capture']
    assert result['turbulence_broadening_applied'] is False


@pytest.mark.parametrize('field,value', [('beam_full_divergence_rad',0.), ('beam_full_divergence_rad',float('nan')), ('wavelength_m',None)])
def test_beam_missing_or_invalid_values_fail(field,value):
    from uav_qkd.physical_setup import beam_sanity
    c = load_config(ROOT/'configs/channel/optimized_physical_setup.yaml');c[field]=value
    with pytest.raises(ValueError):beam_sanity(c)


def test_exact_reference_windows_and_binary_mask_share_one_field():
    from uav_qkd.cloud_candidate import cloud_reference_windows
    # Synthetic Gaussian fixture only; threshold is not a paper choice.
    field = CloudField([GaussianCluster(10., (1510.,1000.), (100.,400.))], (-5.,0.))
    windows = cloud_reference_windows(field,threshold=5.)
    assert [w['bounds_m'] for w in windows] == [[0.,2000.,0.,2000.], [1500.,3500.,0.,2000.], [5000.,7000.,0.,2000.]]
    for w in windows:
        assert w['clwc_mg_m3'].shape == (50,50)
        assert w['cell_m'] == [40.,40.]
        assert w['reference_points_m'][0,0,0] == w['bounds_m'][0]+20.
        physical = w['reference_points_m']+np.array([-5.,0.])*w['time_s']
        np.testing.assert_allclose(field.evaluate(physical,w['time_s']),w['clwc_mg_m3'],rtol=1e-14,atol=1e-14)
        np.testing.assert_array_equal(w['blocked'],w['clwc_mg_m3']>=5.)
    assert windows[1]['bounds_m'][0]/40 == 37.5
    assert cloud_reference_windows(field)[0]['blocked'] is None
    # The historical saved figure geometry is checked without importing its writer.
    with np.load(ROOT.parent/'dynamic_gaussian_cloud_figure/cloud_field_data.npz') as saved:
        np.testing.assert_array_equal(saved['starts'],[0,1500,5000])
        for mask,t in zip(saved['masks'],saved['thresholds']):
            np.testing.assert_array_equal(mask,saved['field']>=t)


def test_reference_windows_reject_nonrigid_drift_and_invalid_times():
    from uav_qkd.cloud_candidate import cloud_reference_windows
    field = CloudField([GaussianCluster(10., (0.,0.), (1.,1.), velocity=(1.,0.))],(-5.,0.))
    with pytest.raises(ValueError,match='rigid'):cloud_reference_windows(field)
    field = CloudField([],(-5.,0.))
    with pytest.raises(ValueError):cloud_reference_windows(field,times=(-1.,))


def approved_fixture():
    """Explicit approval for SOFTWARE TEST only, never edits candidate config."""
    c = load_config(ROOT/'configs/cloud/binary_los_blockage_candidate.yaml')
    c.update(author_approved=True,threshold_approved=True,approval_provenance='SOFTWARE FIXTURE ONLY',
             realization_provenance='EXPLICIT SOFTWARE FIXTURE COEFFICIENTS',
             threshold_mg_m3=5.,layer_bottom_m=50.,layer_top_m=60.,sample_spacing_m=.5)
    return c


def test_candidate_cannot_enable_itself_without_both_approvals_and_inputs():
    from uav_qkd.cloud_candidate import build_binary_los_blockage
    c=load_config(ROOT/'configs/cloud/binary_los_blockage_candidate.yaml')
    field=CloudField([],(-5.,0.))
    with pytest.raises(ValueError,match='approved'):build_binary_los_blockage(c,field,[0.,0.,100.],0.)
    for key in ('author_approved','threshold_approved','threshold_mg_m3','layer_bottom_m','sample_spacing_m','realization_provenance'):
        c=approved_fixture();c[key]=None
        with pytest.raises(ValueError):build_binary_los_blockage(c,field,[0.,0.,100.],0.)


def test_candidate_declared_drift_cannot_differ_from_supplied_realization():
    from uav_qkd.cloud_candidate import build_binary_los_blockage
    c=approved_fixture()
    with pytest.raises(ValueError,match='velocity'):
        build_binary_los_blockage(c,CloudField([], (5.,0.)),[0.,0.,100.],0.)


def test_candidate_LOS_blockage_skips_skr_and_clear_replays_native_rate_once():
    from uav_qkd.cloud_candidate import build_binary_los_blockage
    from uav_qkd.cloud_channel import cloud_blockage_effect,evaluate_link_slot
    from uav_qkd.hap_uav_channel import FadingMoments,bind_existing_mb_backend
    from uav_qkd.finite_size_reference import finite_size_aware_key_yield_proxy
    field=CloudField([GaussianCluster(10.,(50.,0.),(4.,4.))],(-5.,0.))
    model,policy=build_binary_los_blockage(approved_fixture(),field,[0.,0.,100.],0.)
    assert not field.evaluate([[100.,0.]],0.)[0]>=5.
    assert model.blocked([100.,0.],0.)  # Interior path; UAV endpoint is clear.
    stored=json.loads(next((LOOKUP/'contexts').glob('*.json')).read_text(encoding='utf-8'))
    native=json.loads((LOOKUP/'execution_physical_protocol.json').read_text(encoding='utf-8'))
    source=stored['winners']['MB'];calls=[]
    def evaluator(s,context,protocol):
        calls.append(s)
        return source  # Actual saved native response in its own original context.
    backend=bind_existing_mb_backend(evaluator,source,stored,native)
    moments=FadingMoments.from_existing_v43(stored['moments'],xi_ch=native['xi_ch'],xi_det=native['xi_det'],provenance='saved receiver30 fixture')
    def moment_provider(geometry):return moments
    args=(None,source['VA'],1e6,.95,moment_provider,backend)
    blocked=evaluate_link_slot(*args,cloud_blockage_effect(model,[100.,0.],0.,policy))
    assert blocked.valid_signals==blocked.skr_bits_per_use==blocked.power_transmittance==0.
    assert calls==[]
    clear=evaluate_link_slot(*args,cloud_blockage_effect(model,[0.,100.],0.,policy))
    assert clear.valid_signals==1e6 and clear.skr_bits_per_use==source['K_raw']
    assert len(calls)==1
    finite=finite_size_aware_key_yield_proxy([blocked.skr_bits_per_use,clear.skr_bits_per_use],[0,1],1e6,1e-6,1.)
    assert finite['valid_signals']==1e6
    assert finite['asymptotic_bits']==1e6*source['K_raw']
    assert finite['penalty_bits']==pytest.approx(7*np.sqrt(1e6*np.log2(2/1e-6)))


def test_old_noise_inferred_from_actual_saved_scalar_outputs_and_recipe_not_authorized():
    from uav_qkd.phase5b_audit import audit_lookup_noise
    audit=audit_lookup_noise(LOOKUP)
    assert audit['actual_channel_excess_noise_snu']==.0186
    assert audit['actual_detector_excess_noise_snu']==.005
    assert audit['stored_winner_checks']==650
    assert audit['max_effective_noise_residual_old']<1e-14
    assert audit['min_effective_noise_residual_requested']>0
    assert audit['channel_noise_inferred_range'][0]==pytest.approx(.0186)
    assert audit==audit_lookup_noise(LOOKUP)
    recipe=load_config(ROOT/'configs/lookup/optimized_physical_setup_regeneration.yaml')
    assert recipe['execution_authorized'] is False and recipe['status']=='PREPARED_NOT_RUN'
    assert recipe['target_native_protocol']['xi_ch']==.0136
    assert recipe['target_native_protocol']['xi_det']==.005
    assert recipe['geometry']['shape']==[51,51] and recipe['geometry']['hap_projection_m']==[1000.,1000.]
    assert recipe['geometry']['role']=='historical_lookup_replay_not_mission_coordinate_approval'


def test_tuned_lookup_refusal_names_channel_noise_despite_optical_match():
    from uav_qkd.skr_lookup import compare_lookup_setup,SKRLookup
    from uav_qkd.hap_uav_channel import load_channel_reference
    tuned=load_channel_reference(ROOT/'configs/channel/optimized_physical_setup.yaml')
    protocol=json.loads((LOOKUP/'execution_physical_protocol.json').read_text(encoding='utf-8'))
    report=compare_lookup_setup(tuned,protocol)
    assert report['physical_mismatches']==[]
    assert report['noise_mismatches']==['channel_excess_noise_snu']
    assert report['noise_comparison'][1]['matches'] is True
    with pytest.raises(ValueError,match='incompatible.*channel_excess_noise_snu'):
        SKRLookup.load('MUST_NOT_READ.csv',reference=tuned,protocol=protocol,coordinate_units='m',rate_units='bits/use')


@pytest.mark.parametrize('invalid', [float('inf'),float('nan'),-1.])
def test_noise_comparison_cannot_report_invalid_noise_as_matching(invalid):
    from uav_qkd.skr_lookup import compare_lookup_setup
    c=load_config(ROOT/'configs/channel/optimized_physical_setup.yaml')
    protocol=json.loads((LOOKUP/'execution_physical_protocol.json').read_text(encoding='utf-8'))
    c['channel_excess_noise_snu']=invalid;protocol['xi_ch']=invalid
    with pytest.raises(ValueError,match='noise'):
        compare_lookup_setup(c,protocol)
