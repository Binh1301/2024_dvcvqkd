# Figure captions

All curves are numerical diagnostics for the explicitly introduced passive
random-Gaussian-width channel, homodyne 1D, untrusted detection, beta=0.95,
epsilon_ch=0.0186 SNU. No curve establishes hardware or operational security.
Lines connect evaluated nodes; no smoothing, source-moment interpolation or
inferred intermediate evaluations are used. Negative raw rates are retained.

1. **fig_aperture:** Aperture sensitivity at zenith30deg, full divergence10urad,
   exact MB(VA=8,nu_raw=.125), eta_det=.8, epsilon_det=.0135 SNU. Original
   position/angular jitter (1m,15.61urad) versus both reduced by factor.1.
   Parameters apart from aperture and the labeled pointing change are identical.
2. **fig_divergence:** Full-angle divergence sensitivity at receiver diameter.75m,
   zenith30deg and the same source/detector/pointing comparison as Figure1.
   Beam waist is recomputed as w0=2lambda/(pi*theta_full) at each node.
3. **fig_detector_noise:** Detector output excess-noise sensitivity at eta_det=.8.
   Original8cm/233urad/30deg link versus.75m/10urad/0deg with pointing reduced
   by factor.1. Each point is the best authenticated existing-catalog candidate;
   the source can change between nodes. All detector noise remains untrusted.
4. **fig_detector_efficiency:** Efficiency sensitivity at epsilon_det=.0135 SNU,
   using the same two optical scenarios and catalog-ranking rule as Figure3.
   Efficiency is applied once in the composed channel, never again in Holevo.
5. **fig_distance:** Signed distance dependence at fixed source per curve.
   Original8cm/233urad/original-pointing MB(.3,.5194444399281013) versus
   .75m/10urad/pointing-factor.1 MB(.125,8), same detector(.8,.0135).
   Altitudes20/1km remain fixed; zenith, atmospheric loss, beam propagation,
   turbulence and total transverse jitter are recomputed at every distance.
   The tested domain ends at38km/60deg; no maximum-range certificate is implied.
