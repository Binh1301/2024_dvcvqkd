"""Interface tests only; exact analytic fixtures are not paper simulation data."""
from pathlib import Path
import numpy as np
import pytest
from uav_qkd.config import load_config
from uav_qkd.hap_uav_channel import (
    load_channel_reference, reference_geometry, waypoint_geometry, FadingMoments,
    effective_channel, bind_existing_mb_backend, make_skr_request,
    ExistingMomentProvider,
)
from uav_qkd.finite_size_reference import (
    load_finite_reference, delta_per_signal, valid_signals_per_clear_slot,
    finite_size_aware_key_yield_proxy,
)
from uav_qkd.cloud_channel import CloudPolicy, evaluate_link_slot, cloud_blockage_effect
from uav_qkd.cloud_model import CloudField, GaussianCluster
from uav_qkd.blockage import BlockageModel

ROOT=Path(__file__).parents[1]


def channel():
    return load_channel_reference(ROOT/'configs/channel/hap_uav_mb_reference.yaml')


def test_source_a_config_si_units_and_no_implicit_mission_inputs():
    c=channel()
    assert c['hap_altitude_m']==20000 and c['uav_altitude_m']==1000
    assert c['beam_full_divergence_rad']==pytest.approx(233e-6)
    assert c['receiver_aperture_diameter_m']==.08
    assert c['transmitter_jitter_angle_rad']==pytest.approx(15.61e-6)
    assert c['uav_position_sd_m']==1.
    assert c['uav_angular_fluctuation_sd_rad']==pytest.approx(1.5e-3)
    assert c['receiver_fov_half_angle_rad']==pytest.approx(6.25e-3)
    assert c['hap_horizontal_m'] is None
    assert c['channel_excess_noise_snu'] is None and c['detector_excess_noise_snu'] is None
    assert c['reconciliation_efficiency']==.95


def test_general_geometry_varies_by_waypoint_and_reference_is_separate():
    c=channel()
    a=waypoint_geometry([0.,0.,20000.],[0.,0.],1000.,c['zenith_atmospheric_transmittance'])
    b=waypoint_geometry([0.,0.,20000.],[19000.,0.],1000.,c['zenith_atmospheric_transmittance'])
    assert a.slant_distance_m==19000 and a.zenith_angle_rad==0
    assert b.slant_distance_m==pytest.approx(19000*np.sqrt(2))
    assert b.zenith_angle_rad==pytest.approx(np.pi/4)
    assert b.atmospheric_transmittance==pytest.approx(.92**np.sqrt(2))
    reference=reference_geometry(c)
    assert reference.zenith_angle_rad==pytest.approx(np.pi/6)
    assert reference.slant_distance_m==pytest.approx(19000/np.cos(np.pi/6))
    with pytest.raises(ValueError,match='HAP'):
        waypoint_geometry(None,[0,0],1000.,.92)


def test_finite_size_reference_is_separate_from_signal_rate_and_m0():
    r=load_finite_reference(ROOT/'configs/finite_size/ieee_2025_reference.yaml')
    assert r['derived']['n_block_reference']==80000000
    assert r['derived']['epsilon_reference']==pytest.approx(3e-8)
    delta=delta_per_signal(80000000,3e-8)
    assert delta==pytest.approx(7*np.sqrt(np.log2(2/3e-8)/80000000))
    assert valid_signals_per_clear_slot(1000.,1.,.25)==250.
    with pytest.raises(ValueError,match='f_s|signal'):
        valid_signals_per_clear_slot(None,1.,.8)
    paper=load_config(ROOT/'configs/paper.yaml')
    assert paper['m0'] is None and paper['epsilon'] is None
    assert paper['verified_context']['eta_valid'] is None


def test_effective_channel_preserves_amplitude_moment_square_and_noise():
    # Exact two-atom unit distribution: eta=0 or1 with equal weights.
    m=FadingMoments(mean_eta=.5,mean_sqrt_eta=.5,mean_eta_xi=0.,provenance='exact analytic unit fixture')
    e=effective_channel(m,2.)
    assert e.power_transmittance==.25 and e.amplitude_gain==.5
    assert e.output_excess_noise==.5 and e.input_excess_noise==2.
    assert e.power_transmittance!=m.mean_eta
    with pytest.raises(ValueError):
        effective_channel(FadingMoments(.1,.8,0.,'invalid fixture'),2.)


def test_existing_mb_boundary_forwards_data_without_touching_core():
    m=FadingMoments(.25,.5,0.,'deterministic pure-loss analytic unit case')
    e=effective_channel(m,2.)
    source={'VA':2.,'C':object(),'w':object()}
    context={'moments':{'m1':.25,'mh':.5,'M0':1.},'source_id':'unit interface only'}
    protocol={'beta':.95,'xi_ch':0.,'xi_det':0.,'source_normalization':'VA=Vmod=2*nbar; X_A=2Re(alpha)'}
    class Recorded(Exception):pass
    def untouched_backend(src,ctx,p):
        assert src is source and ctx is context and p is protocol
        assert src['C'] is source['C'] and src['w'] is source['w']
        raise Recorded('I/O reached existing backend; no SKR fabricated')
    bound=bind_existing_mb_backend(untouched_backend,source,context,protocol)
    request=make_skr_request(e,.95)
    with pytest.raises(Recorded):bound(request)


def test_binary_cloud_is_deterministic_path_erasure_not_endpoint_attenuation():
    field=CloudField([GaussianCluster(10.,(50.,0.),(2.,2.))],(0.,0.))
    model=BlockageModel(field,5.,[0,0,100],0.,mode='layer',sample_spacing_m=.1,
                        layer_bottom_m=49.,layer_top_m=51.)
    policy=CloudPolicy(mode='binary_erasure',author_approved=True,provenance='existing idealized binary model; unit fixture')
    effect=cloud_blockage_effect(model,[100,0],0.,policy)
    assert effect.blocked is True and field.evaluate([[100,0]],0.)[0]<5
    def forbidden(*args):raise AssertionError('Blocked link must not call channel/SKR backend')
    slot=evaluate_link_slot(None,2.,1000.,.95,forbidden,forbidden,effect)
    assert slot.valid_signals==0 and slot.skr_bits_per_use==0
    assert slot.power_transmittance==0 and slot.cloud_mode=='binary_erasure'


def test_attenuation_and_erasure_are_not_applied_twice():
    from uav_qkd.cloud_channel import CloudEffect
    unapproved=CloudPolicy('optical_attenuation',False,'unapproved unit fixture')
    with pytest.raises(ValueError,match='approv'):
        CloudEffect(unapproved,attenuation_factor=.5)
    policy=CloudPolicy('optical_attenuation',True,'sourced factor for unit interface only')
    effect=CloudEffect(policy,attenuation_factor=.5)
    with pytest.raises(ValueError,match='moment|noise'):
        evaluate_link_slot(None,2.,1000.,.95,lambda g:None,lambda r:None,effect)
    with pytest.raises(ValueError,match='erasure|exclusive'):
        CloudEffect(policy,blocked=True,attenuation_factor=.5)


def test_approved_attenuation_requires_explicit_postloss_moments_keeps_signal_count():
    from uav_qkd.cloud_channel import CloudEffect
    policy=CloudPolicy('optical_attenuation',True,'explicit exact unit-case power factor')
    effect=CloudEffect(policy,attenuation_factor=.5)
    calls=[]
    def postloss(geometry,factor):
        calls.append(factor)
        # Noiseless deterministic eta=.5, exactly known algebraically.
        return FadingMoments(.5,np.sqrt(.5),0.,'post-loss analytic unit fixture')
    class Reached(Exception):pass
    def recorder(request):
        assert request.power_transmittance==pytest.approx(.5)
        raise Reached('No fabricated clear-sky SKR value')
    with pytest.raises(Reached):
        evaluate_link_slot(None,2.,1000.,.95,lambda g:None,recorder,effect,attenuated_moment_provider=postloss)
    assert calls==[.5]


def test_accumulated_proxy_reuses_existing_terminal_formula():
    r=finite_size_aware_key_yield_proxy([.001,.001,.001],[1,0,1],1e6,3e-8,1.)
    assert r['valid_signals']==2e6 and r['asymptotic_bits']==2000.
    expected=7*np.sqrt(2e6*np.log2(2/3e-8))
    assert r['penalty_bits']==pytest.approx(expected)
    assert r['objective_name']=='finite_size_aware_key_yield_proxy'
    assert r['average_skr_bits_s']==r['key_bits']/3


def test_geometry_is_forwarded_to_existing_physical_and_moment_providers():
    # Exact pure-loss unit case; zero noises are explicit fixture values only.
    c=channel();c['channel_excess_noise_snu']=0.;c['detector_excess_noise_snu']=0.
    g=waypoint_geometry([0,0,20000],[19000,0],1000,.92)
    native={'native_physical_object':'unit callback identity'}
    def physical(request):
        assert request['slant_distance_m']==g.slant_distance_m
        assert request['zenith_angle_rad']==pytest.approx(np.pi/4)
        assert request['beam_full_divergence_rad']==pytest.approx(233e-6)
        assert request['receiver_aperture_diameter_m']==.08
        assert request['hap_horizontal_m']==[0.,0.]
        assert request['uav_horizontal_m']==[19000.,0.]
        assert 'reference_zenith_angle_deg' not in request
        return native
    def moments(obj):
        assert obj is native
        return {'m1':.25,'mh':.5,'M0':1.}
    provider=ExistingMomentProvider(c,physical,moments,'exact analytic fixture; no paper evaluation')
    out=provider(g)
    assert out.mean_eta==.25 and out.mean_sqrt_eta==.5 and out.mean_eta_xi==0.
    c['channel_excess_noise_snu']=None
    with pytest.raises(ValueError,match='noise|xi_ch'):
        provider(g)


def test_existing_computed_skr_response_replay_is_unchanged():
    # Replay stored receiver30 I/O ONLY, never reuse it as the new reference model.
    import csv,hashlib,json
    base=ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106'
    with (base/'skr_map.csv').open(encoding='utf-8-sig',newline='') as f:row=next(csv.DictReader(f))
    tag=hashlib.sha256(row['context_angle_hex'].encode()).hexdigest()[:18]
    native=json.loads((base/'contexts'/f'{tag}.json').read_text())
    protocol=json.loads((base/'execution_physical_protocol.json').read_text())
    saved=native['winners']['MB']
    source={'VA':float(row['MB_VA']),'C':object(),'w':object()}
    moments=FadingMoments.from_existing_v43(native['moments'],xi_ch=protocol['xi_ch'],
                                           xi_det=protocol['xi_det'],provenance='stored receiver30 context, I/O replay')
    backend=bind_existing_mb_backend(lambda s,c,p:saved,source,native,protocol)
    from uav_qkd.cloud_channel import CloudEffect
    effect=CloudEffect(CloudPolicy('binary_erasure',True,'unit interface clear flag'),blocked=False)
    slot=evaluate_link_slot(None,source['VA'],1000.,.95,lambda g:moments,backend,effect)
    assert slot.skr_bits_per_use==float(row['MB_K_raw'])
    assert slot.valid_signals==1000 and slot.backend_metadata is saved
    assert slot.power_transmittance==pytest.approx(float(row['eta_f']))


def test_attenuation_does_not_erase_slots_in_zero_base_transmission_limit():
    from uav_qkd.cloud_channel import CloudEffect
    effect=CloudEffect(CloudPolicy('optical_attenuation',True,'unit factor, exact zero base-channel limit'),attenuation_factor=.5)
    def forbidden(*args):raise AssertionError('Zero transmission has no SKR backend evaluation')
    slot=evaluate_link_slot(None,2.,1000.,.95,forbidden,forbidden,effect,
                            attenuated_moment_provider=lambda g,a:FadingMoments(0.,0.,0.,'exact zero base-channel fixture'))
    assert slot.valid_signals==1000 and slot.retained_slot is True
    assert slot.skr_bits_per_use==0


def test_provider_rejects_geometry_from_different_altitudes_or_tau():
    c=channel();c['channel_excess_noise_snu']=0.;c['detector_excess_noise_snu']=0.
    def forbidden(*args):raise AssertionError('Mismatched geometry must be rejected before physical evaluation')
    provider=ExistingMomentProvider(c,forbidden,forbidden,'unit boundary mismatch')
    for g in [waypoint_geometry([0,0,20000],[0,0],2000,.92),
              waypoint_geometry([0,0,20000],[0,0],1000,.9)]:
        with pytest.raises(ValueError,match='geometry|altitude|tau'):
            provider(g)


@pytest.mark.parametrize('args', [(.5,0.,0.,'invalid',None),(.5,.6,0.,'invalid',2.),
                                  (.1,.3,0.,'invalid',.2)])
def test_impossible_scalar_moments_are_rejected(args):
    with pytest.raises(ValueError,match='Moment|mass|moment'):
        FadingMoments(*args)


def test_physical_subset_is_not_full_lookup_compatibility():
    import copy,json
    from uav_qkd.phase4_audit import compare_lookup_reference
    c=channel()
    protocol=json.loads((ROOT.parent/'paper_uav_hap_cvqkd/results/skr_zenith_heatmap_20261106/execution_physical_protocol.json').read_text())
    matched=copy.deepcopy(protocol)
    matched['physical'].update(Dr_m=.08,divergence_full_urad=233.,jitter_urad=15.61,sigma_h_m=1.)
    matched['beta']=.5;matched['source_normalization']='different_source_convention'
    result=compare_lookup_reference(c,matched)
    assert not result.get('configuration_compatible',False)
    assert result['physical_subset_matches'] is True
    assert result['full_configuration_compatibility']=='NOT_ESTABLISHED'
    assert result['beta_matches'] is False and result['normalization_matches'] is False


def test_read_only_reference_audit_and_no_historical_overwrite(tmp_path):
    from uav_qkd.phase4_audit import audit_references
    report=audit_references(tmp_path)
    assert report['paper_mode']=='NOT_RUN' and report['core_evaluations']==0
    assert report['lookup_compatibility']['physical_subset_matches'] is False
    assert len(report['lookup_compatibility']['physical_mismatches'])==4
    assert report['finite_reference']['n_block_reference']==8e7
    with pytest.raises(FileExistsError):audit_references(tmp_path)


def test_effective_scalar_overflow_is_rejected_before_backend():
    m=FadingMoments(.5,.5,1.7e308,'numerical-range boundary unit fixture')
    with pytest.raises(ValueError,match='effective|noise'):
        effective_channel(m,1e308)


def test_variance_mapping_is_exact_not_a_shared_text_prefix():
    bad={'beta':.95,'source_normalization':'VA=Vmod=2*nbar + 1'}
    with pytest.raises(ValueError,match='normalization'):
        bind_existing_mb_backend(lambda *args:None,{'VA':2.},{},bad)
