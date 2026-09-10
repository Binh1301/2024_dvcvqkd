# Paper-to-code map

The current manuscript source is not present in the repository. The referenced
2026 PDF path is unavailable; the local 2024 PDF is an unrelated satellite-
to-ground reference. The table therefore maps the current intended quantities
to repository locations without judging alignment.

| Paper quantity | Code file | Function/class |
|---|---|---|
| HAP/UAV geometry and link length | src/channel/geometry.py | LinkGeometry |
| Empirical atmospheric extinction | src/channel/atmospheric_loss.py | atmospheric_transmittance |
| Beam propagation and aperture coupling | src/channel/pointing_error.py | gaussian_beam_radius, pointing_parameters |
| UAV motion and active transverse jitter | src/channel/turbulence.py | UavMotion, uav_translational_variance_m2, pointing_displacement_variance_m2 |
| Legacy constant beam-wander variance | src/channel/turbulence.py | turbulence_beam_wander_variance_m2 (legacy only; not active target) |
| Pointing loss | src/channel/pointing_error.py | pointing_power_transmittance |
| Composite physical FSO sampler | src/channel/fso_channel.py | sample_fso_channel, compose_raw_transmittance, physicalize_raw_transmittance |
| Current joint state sampler | src/channel/state_distribution.py | sample_channel_state_distribution |
| Scintillation profile/Rytov/lognormal H_sc | src/channel/scintillation.py | rytov_variance_from_profile, normalized_lognormal_samples |
| Aperture mapping sigma_R0^2 -> v_sc | src/channel/scintillation.py | resolve_scintillation_variance; unsupported mappings fail closed |
| AoA factor B_AoA and outage | src/channel/aoa.py | aoa_variance_rad2, sample_aoa_gate, aoa_outage_probability |
| Raw-T admission and p_gt_1 | src/channel/fso_channel.py, diagnostics.py | physicalize_raw_transmittance, composite_transmittance_diagnostics |
| Historical intended scintillation factor H_sc row | src/channel/scintillation.py | Architecture implemented; production mapping remains unresolved |
| Historical intended AoA factor B_AoA row | src/channel/aoa.py | Architecture implemented; turbulence mapping may be disabled or externally validated |
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
