# Paper-to-code map

The manuscript PDF is external to the repository. The attached 2026 PDF is the
source for the channel equations and Table I below; it does not override the
frozen CV-QKD/security specification or authorize publication-scale work.

| Paper quantity | Code file | Function/class |
|---|---|---|
| HAP/UAV geometry and link length | src/channel/geometry.py | LinkGeometry |
| Empirical atmospheric extinction | src/channel/atmospheric_loss.py | atmospheric_transmittance |
| Beam propagation and aperture coupling | src/channel/pointing_error.py | gaussian_beam_radius, pointing_parameters, pointing_power_transmittance |
| UAV motion and active transverse jitter | src/channel/turbulence.py | UavMotion, uav_translational_variance_m2, pointing_displacement_variance_m2 |
| Legacy constant beam-wander variance | src/channel/turbulence.py | turbulence_beam_wander_variance_m2 (legacy only; not active target) |
| Pointing loss and Eq. (37) PDF | src/channel/pointing_error.py | pointing_power_transmittance, pointing_pdf |
| Composite physical FSO sampler | src/channel/fso_channel.py | sample_fso_channel, compose_raw_transmittance, physicalize_raw_transmittance |
| Current joint state sampler | src/channel/state_distribution.py | sample_channel_state_distribution |
| Scintillation profile/Rytov/lognormal H_sc | src/channel/scintillation.py | hufnagel_valley_scintillation, hufnagel_valley_beam_spreading, normalized_lognormal_samples, lognormal_pdf |
| Aperture mapping sigma_R0^2 -> v_sc | src/channel/scintillation.py | resolve_scintillation_variance; unsupported mappings fail closed |
| AoA factor B_AoA and outage | src/channel/aoa.py | aoa_variance_rad2, sample_aoa_gate, aoa_outage_probability |
| Raw-T admission and p_gt_1 | src/channel/fso_channel.py, diagnostics.py | physicalize_raw_transmittance, composite_transmittance_diagnostics |
| Active Eq. (49)/(50) PDF and moments | src/channel/diagnostics.py | active_transmittance_pdf_eq49, active_transmittance_pdf_eq50, active_channel_moments |
| Historical intended scintillation factor H_sc row | src/channel/scintillation.py | Superseded by the Table-I Hufnagel--Valley finite-aperture path for channel-only diagnostics |
| Historical intended AoA factor B_AoA row | src/channel/aoa.py | Explicit Table-I total AoA SD/FOV path; turbulence AoA remains zero/external-only |
| Historical intended raw-T admission row | src/channel/fso_channel.py | Physical admission and diagnostics implemented |
| Effective phase coefficient C_n_phi2 | src/channel/phase_noise.py | Common-turbulence API/provenance implemented; validated profile mapping and author-approved value still required |
| Intended tau_phi2 and c_phi | src/channel/phase_noise.py | Implemented; c_phi is derived from canonical inputs |
| Phase parameter provenance | src/channel/phase_noise.py, scripts/_train.py | Records Cn_phi2, wavelength_m, link_distance_m, tau_phi2, and c_phi |
| Intended post-action epsilon_total | src/channel/phase_noise.py, src/optimization/trainer.py | Implemented; policy remains on epsilon_base |
| Square 256-QAM | src/modulation/qam256.py | square_qam256, canonical_square_qam256 |
| C4 orbit partition and expansion | src/modulation/qam256.py | c4_orbit_indices, expand_c4_orbit_values |
| Uniform, Binomial, MB PMFs | src/modulation/qam256.py | reference_pmf |
| Adaptive PS | src/modulation/probabilistic_shaping.py | ProbabilisticShapingNetwork |
| Global GS | src/modulation/geometric_shaping.py | GlobalGeometricShaping |
| Physical normalization | src/modulation/normalization.py | physical_amplitudes |
| Common ensemble and modes | src/modulation/joint_ps_gs.py | Ensemble, JointTransmitter |
| MI channel | src/cvqkd/mutual_information.py | discrete_mutual_information |
| Source density/Fock diagnostic | src/cvqkd/holevo.py | density_operator |
| C4 Gram source moments | src/cvqkd/gram_moments.py | c4_gram_source_moments |
| Intended full Z interval | src/cvqkd/holevo.py | Implemented with physical intersection and structured empty-domain failure |
| Bounded worst-case Holevo maximization | src/cvqkd/holevo.py | _maximize_bounded_scalar and _holevo_from_source_moments |
| Standard-form covariance | src/cvqkd/covariance.py | standard_form_covariance |
| Bosonic entropy | src/cvqkd/holevo.py | bosonic_entropy |
| Raw statewise SKR | src/cvqkd/secret_key_rate.py | fading_secret_key_rate |
| Energy dual and trainer | src/optimization/trainer.py | EnergyBudgetController, train_step |
| Hard peak guard | src/modulation/joint_ps_gs.py | enforce_peak_photon_constraint |
| Channel diagnostics | src/channel/diagnostics.py | frozen_channel_diagnostics |
| Smoke baseline runner | scripts/run_baselines_cached_source_moments.py | main |
| Training entry points | scripts/train_ps.py, train_gs.py, train_joint.py | main |

Detailed alignment judgments belong only in PAPER_CODE_ALIGNMENT.md.
