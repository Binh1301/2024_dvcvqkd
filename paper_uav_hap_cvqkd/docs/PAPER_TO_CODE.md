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
| UAV motion and constant beam-wander variance | src/channel/turbulence.py | UavMotion, turbulence_beam_wander_variance_m2 |
| Pointing loss | src/channel/pointing_error.py | pointing_power_transmittance |
| Composite current FSO sampler | src/channel/fso_channel.py | sample_fso_channel |
| Current joint state sampler | src/channel/state_distribution.py | sample_channel_state_distribution |
| Intended scintillation factor H_sc | — | NOT IMPLEMENTED |
| Intended AoA factor B_AoA and outage | — | NOT IMPLEMENTED |
| Intended raw-T admission and p_gt_1 | — | NOT IMPLEMENTED |
| Intended phase coefficient C_n_phi2 | — | NOT IMPLEMENTED |
| Intended tau_phi2 and c_phi | — | NOT IMPLEMENTED |
| Intended post-action epsilon_total | — | NOT IMPLEMENTED |
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
| Intended full Z interval | — | NOT IMPLEMENTED |
| Current lower-endpoint Holevo path | src/cvqkd/holevo.py | _holevo_from_source_moments |
| Standard-form covariance | src/cvqkd/covariance.py | standard_form_covariance |
| Bosonic entropy | src/cvqkd/holevo.py | bosonic_entropy |
| Raw statewise SKR | src/cvqkd/secret_key_rate.py | fading_secret_key_rate |
| Energy dual and trainer | src/optimization/trainer.py | EnergyBudgetController, train_step |
| Hard peak guard | src/modulation/joint_ps_gs.py | enforce_peak_photon_constraint |
| Channel diagnostics | src/channel/diagnostics.py | frozen_channel_diagnostics |
| Smoke baseline runner | scripts/run_baselines_cached_source_moments.py | main |
| Training entry points | scripts/train_ps.py, train_gs.py, train_joint.py | main |

Detailed alignment judgments belong only in PAPER_CODE_ALIGNMENT.md.
