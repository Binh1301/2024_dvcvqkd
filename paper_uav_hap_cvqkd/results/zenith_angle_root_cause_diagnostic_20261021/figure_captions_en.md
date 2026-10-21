# English figure captions

All rate figures use the unchanged historical conditional manuscript model. **UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.** Markers denote evaluated points; connecting lines provide visual guidance only.

## fig_01_original_semilog

Stored raw-rate comparison for optimized Uniform, fixed MB, and catalog-optimized MB 256-QAM. The logarithmic ordinate displays only strictly positive values; omitted nonpositive points remain in the numerical tables. Maxima are evaluated on the original 2-degree grid.

[Vector PDF](figures/fig_01_original_semilog.pdf) · [350-dpi PNG](figures/fig_01_original_semilog.png)

## fig_02_raw_signed

Signed raw rates for all three source choices on the complete original zenith grid. The zero line separates positive and nonpositive model outputs; no negative values are clipped or replaced.

[Vector PDF](figures/fig_02_raw_signed.pdf) · [350-dpi PNG](figures/fig_02_raw_signed.png)

## fig_A_geometry_atmosphere

Historical geometry and atmospheric attenuation: (a) propagation distance L=19 sec(zeta) km; (b) atmospheric power transmittance 0.92 raised to sec(zeta). Longer slant paths reduce transmittance throughout the evaluated domain.

[Vector PDF](figures/fig_A_geometry_atmosphere.pdf) · [350-dpi PNG](figures/fig_A_geometry_atmosphere.png)

## fig_B_beam_pointing

Beam and pointing quantities reconstructed from the recorded historical parameters: (a) free-space, turbulence-broadened, and equivalent beam radii; (b) total, positional, and angular-jitter displacement variances; (c) peak collection fraction; (d) normalized pointing shape d. The three beam-radius curves nearly coincide at this scale; their separate numerical values are retained.

[Vector PDF](figures/fig_B_beam_pointing.pdf) · [350-dpi PNG](figures/fig_B_beam_pointing.png)

## fig_C_scintillation_outage

Scintillation and angle-of-arrival quantities in the historical literal channel: (a) Rytov variance, used directly as the lognormal log variance; (b) corresponding scintillation index; (c) prescribed AoA outage probability. In-FOV probability is one minus the constant outage probability. No alternative aperture-averaging closure is substituted.

[Vector PDF](figures/fig_C_scintillation_outage.pdf) · [350-dpi PNG](figures/fig_C_scintillation_outage.png)

## fig_D_channel_moments

Saved fading-channel moments and algebraic penalties: (a) mean power transmittance and effective transmittance; (b) square-root-transmittance variance; (c) normalized fading penalty Rf. Both transmittances decrease monotonically, whereas Rf reaches its discrete minimum at 56 degrees, beyond the MB rate maximum at 48 degrees.

[Vector PDF](figures/fig_D_channel_moments.pdf) · [350-dpi PNG](figures/fig_D_channel_moments.png)

## fig_E_noise_decomposition

Effective excess-noise decomposition for the fixed exact MB source (nu_raw,VA)=(0.165,5.475): (a) input-referred fading and total excess noise; (b) effective input-referred physical noise; (c) output-referred total, fading, and physical excess noise. Input- and output-referred quantities are kept on separate panels.

[Vector PDF](figures/fig_E_noise_decomposition.pdf) · [350-dpi PNG](figures/fig_E_noise_decomposition.png)

## fig_F_MI_Holevo_SKR

Fixed-source decomposition of the recorded numerical rate: (a) reconciled two-dimensional mutual information; (b) homodyne-conditioned Holevo expression; (c) their signed difference. Both information terms decrease, but the Holevo reduction dominates before 48 degrees and the mutual-information loss dominates afterward. This mixed measurement convention is not a validated secret-key-rate model.

[Vector PDF](figures/fig_F_MI_Holevo_SKR.pdf) · [350-dpi PNG](figures/fig_F_MI_Holevo_SKR.png)

## fig_G_source_optimization

Effect of finite-catalog MB source selection: (a) fixed-source and catalog-optimized signed rates; (b) their absolute difference. Both curves attain their evaluated maximum at 48 degrees. The gain includes changes of modulation variance and is not an equal-energy shaping comparison.

[Vector PDF](figures/fig_G_source_optimization.pdf) · [350-dpi PNG](figures/fig_G_source_optimization.png)

## fig_H_selected_source_parameters

Recorded source parameters versus zenith angle: (a) modulation variance; (b) raw MB parameter. Straight segments connect the actual sampled points and do not imply interpolation of the source catalog. No source switches occur near either reported positive-rate maximum.

[Vector PDF](figures/fig_H_selected_source_parameters.pdf) · [350-dpi PNG](figures/fig_H_selected_source_parameters.png)

## fig_I_controlled_diagnostics

Fixed-source numerical counterfactuals: (a) the original fading result and a control fixing normalized fading statistics at 30 degrees while varying the historical deterministic factor A0 times atmospheric transmittance; (b) a nonfading channel matched to the saved mean power transmittance. Both controls decrease at all 30 adjacent intervals. These artificial controls are diagnostic interventions, not physical flight trajectories or replacement security models.

[Vector PDF](figures/fig_I_controlled_diagnostics.pdf) · [350-dpi PNG](figures/fig_I_controlled_diagnostics.png)

## fig_J_relative_fading_factors

Additive logarithmic decomposition of one plus the normalized fading penalty into pointing, scintillation, and AoA factors for zero boresight. The negligible discarded upper-tail moment is explicitly bounded in the diagnostic tables. Pointing improves while scintillation worsens; the ordinate is logarithmic to resolve their different positive magnitudes.

[Vector PDF](figures/fig_J_relative_fading_factors.pdf) · [350-dpi PNG](figures/fig_J_relative_fading_factors.png)

