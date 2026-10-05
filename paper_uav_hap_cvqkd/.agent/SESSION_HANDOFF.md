# Session Handoff

## Latest completed task: theta10/D55 three-scheme comparison

Date: 2026-10-02

EVID-0119 / DEC-0103 completed the exact D55 three-curve diagnostic. Uniform
was independently VA-optimized, fixed MB used `(nu=.2,VA=1.3833230303)`, and
optimized MB used the exact 145-point bank.

- Uniform VA sequence moves from `1.5` at 20 km to `.5` at 35--40 km.
- Uniform exact sign bracket: 25 km positive, 25.5 km non-positive.
- Fixed and optimized MB remain positive through 40 km.
- Optimized MB is beta-I_AB dominated in the gain decomposition except fixed
  MB at 20 km, where lower chi_BE dominates.
- Experiment hash: `eb9ac8410ce48a982b6c06ac2534b6f3e69818bf9a61aec57a73532250efdc89`.

Artifacts: `results/skr_vs_distance_theta10urad_D55cm_three_scheme/`.

## Current gate

Preserve the diagnostic figure/table. Do not select D55 as a publication
baseline, infer 40 km as a maximum distance, train, or access final-test data.
Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Previous handoff

## Latest completed task: transition theta/D_r Uniform frontier

Date: 2026-10-02

EVID-0118 / DEC-0102 searched only theta15--50 urad and D_r=.30--.80 m.
Positive branches require very-large apertures:

- theta15: Dcrit20≈.553045 m, Dcrit25≈.642847 m.
- theta20: Dcrit20≈.654944 m, Dcrit25≈.766989 m.
- theta25: Dcrit20≈.756441 m; no positive 25-km point below .80 m.
- theta30--50: no positive 20-km point below .80 m.

Exact boundary `T_eff≈.089827455` persists. Four refined candidates are
positive only through 20 or 25 km and fail at 30 km. No 30--40-km Uniform
candidate exists; MB was not run.

Artifacts: `results/transition_theta_dr_frontier/`.

## Current gate

Do not extend optical ranges, run MB, select a baseline, generate a publication
figure, train, or access final-test data. Publication lifecycle remains
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Previous handoff

## Latest completed task: joint theta/D_r optical search

Date: 2026-10-02

EVID-0117 / DEC-0101 completed the primary full-angle divergence/receiver
coarse search: 9 theta values × 10 diameters × 5 distances = 90 exact
Uniform optical pairs. Every pair is `NONPOSITIVE_AT_20`; no 30--40-km
Uniform crossing exists in the declared domain.

- Best K(20): `-3.3000236312e-5` at `theta=50 urad,D_r=.10 m`.
- Best K(30)/K(40): `theta=250 urad,D_r=.10 m`, still negative.
- Exact source moments `.14,.18,.20` were generated with support 256.
- MB, local refinement, and full-distance refinement were not run because no
  Uniform crossing candidate exists; this is fail-closed by protocol.
- Classification: no solution in primary joint optical domain.

Artifacts: `results/joint_theta_dr_optical_search/`.

## Current gate

Do not extend the optical domain, alter security/noise/pointing, select a
baseline, generate a publication figure, train, or access final-test data.
Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Previous handoff

## Latest completed task: theta10 receiver-aperture Uniform diagnostic

Date: 2026-10-02

EVID-0116 / DEC-0100 completed the exact-cache receiver-diameter sweep for
the current theta10 baseline with all other physical/security parameters
frozen. The available Uniform VA bank contains 11 exact rows; 10 requested
VA source moments in `0<V_A<=1.5` remain missing.

- Exact threshold bracket at 20 km: `D_r≈0.491811 m`, `V_A*=.8`.
- Exact threshold bracket at 22 km: `D_r≈0.512472 m`, `V_A*=.8`.
- Exact threshold bracket at 25 km: `D_r≈0.544644 m`, `V_A*=.8`.
- First tested positive diameters: `.50 m` at 20 km; `.55 m` at 22/25 km.
- `D_r=.55 m` matches the old positive-Uniform sign pattern.
- Classification is cache-bound; no continuous-VA threshold is claimed.

Artifacts: `results/theta10_receiver_aperture_uniform_diagnostic/`.

## Current gate

No model/security change, divergence/noise/AO/phase change, publication figure,
baseline selection, training, or final-test access. Publication lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Previous handoff

## Latest completed task: positive-Uniform provenance audit

Date: 2026-10-02

EVID-0115 / DEC-0099 traced the historical symlog figure to the exact
common-feasible table under the old physical baseline `w0=.10 m`,
`D_r=.55 m`, `tau_zen=.92`, epsilon `.0186`, beta `.95`, AO/phase OFF, and
direct `Z_minus`. The old distance sweep recomputed channel quantities at all
83 distances; no interpolation or new source moments occurred.

- Uniform exact envelope: positive through 25 km, negative at 26 km.
- MB exact envelope: positive at 800 km, negative at 810 km (O(1e-11)
  diagnostic bracket).
- Ten original short-distance rows reproduced with max `abs(diff K)=0.0`.
- Old physical VA `.08,.10,.12,.13,.15` is negative at 20/22/25/30 km.
- Classification: `POSITIVE_UNIFORM_FROM_OLD_PHYSICAL_BASELINE`.

Artifacts: `results/positive_uniform_provenance_audit/`.

## Current gate

No replacement figure, new parameter search, source-moment generation, MB
rerun, baseline selection, training, or final-test access. Publication
lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## Previous handoff

## Latest completed task: Uniform VA verification at theta10urad/D10cm

Date: 2026-10-02

EVID-0114 / DEC-0098 completed the Uniform-only exact diagnostic without
changing the frozen physical/security configuration. The implementation-derived
peak domain is `0 < V_A <= 22.666666666666668`.

- Exact coverage: 322 rows, 14 VA values × 23 distances.
- Exact tested envelope: `V_A=0.12` through 31 km and `V_A=0.13` from
  31.5--40 km.
- Every selected Uniform SKR is negative; no exact positive point or sign
  crossing exists.
- `V_A=1.075` is a fixed reference-bank row, not a per-distance optimum.
- `V_A=0.1` is strictly below the exact-tested envelope but within the frozen
  `1e-6` absolute SKR tolerance: classify
  `VA=0.1 NEAR-OPTIMAL WITHIN NUMERICAL TOLERANCE`.
- 13 requested VA source moments remain missing; no continuous optimum is
  claimed and no interpolation was used.

Artifacts: `results/uniform_va_optimization_theta10_D10cm/`.

## Current gate

Publication lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`. Do not
rerun MB, redraw the final figure, select a baseline, train, access final-test
data, or promote the Uniform envelope to a continuous/global optimum. Any
follow-up must use the same exact cache and an explicit source-point budget.
