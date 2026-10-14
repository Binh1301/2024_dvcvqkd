# Mobility-aware joint source/UAV optimization: repository audit

The authoritative attached task requests a distance penalty, not the physical
energy model in the selected Overleaf excerpt. Implement synthetic diagnostic
P1 finite MB enumeration, P2 stationary choice, P3 discrete DP. Keep the current
effective Gaussian approximation ignoring fading variance; use direct Z_star,
ideal heterodyne, beta=0.95 and xi_ch=0.0186. No security or publication promotion.

Reused: derive_physical_inputs; LiteralChannel.from_physical;
PhysicalFadingDistribution.moments; authenticate/evaluate_authenticated;
canonical MB construction/normalization; deterministic_mutual_information;
_holevo_from_source_moments and standard_form_covariance. audit.json binds paths
and producer hashes. The authenticated latest source roster supplies 197 MB
ensembles, including the original 182 and 15 later accepted records. No new
source moments, AP/AO, interpolation or new Holevo formula is needed.

The repository supplies h_H=20 km, h_U=1 km, L_ref=21.9393102292 km and zenith
30 degrees but no HAP horizontal coordinates. The configurable demonstration
places the reference at (450,450) m (grid index 44, zero based), with HAP at
(11419.65511459133,450) m. This explicit azimuth/coordinate embedding preserves
the reference slant distance; it is not a measured HAP location. The optional
user clarification was offered before implementation. Clouds are explicitly
synthetic: altitude 5 km, radius 420 m, attenuation 10 dB, initial center
(2093.7168662297537,450) m, velocity (3,0) m/s. No measured-weather claim.

Cloud transmittance multiplies the raw channel exactly once, before the
existing normalization on 0<T<=1 with preserved outage atom. The third moment
is recomputed, not naively multiplied by cloud attenuation. Recompute all
geometry-dependent inputs at each cell. Two time-invariant binary channel
states per position allow 39400 source evaluations instead of 100*30*197.
Full physical state, binary state, exact source hex/ensemble/payload bytes and
scientific-code/config hashes bind each objective journal key. Velocity/penalty
sweeps then use the completed exact state table without fresh SKR interpolation.

Order: small tests including 3-position/4-slot brute force and original geometry
SKR regression; 5-position/3-source smoke; then 100-position/197-source/30-slot
demonstration and configurable velocity/penalty experiments, CSV and six PNG/PDF
figures. Report raw signed K separately from the usable positive part; cumulative
contributions are bits/use-slot when no channel-use rate is specified. Report
average SKR and penalized objective separately. No propulsion energy or bits/J.

All old scientific files/results/cache hashes are protected by startup_manifest.
Frozen actual SHA df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15
still differs from the historical expected hash; preserve it as a pre-existing
publication blocker. NOT_READY_FOR_PUBLICATION_SCALE_RUNS remains. No training,
held-out/final-test/publication evaluation, commit or push. PDF reference bytes
are hash-bound; its full text was not parsed because no PDF parser is installed.
The pasted task and supplied TeX equations define this implementation scope.
