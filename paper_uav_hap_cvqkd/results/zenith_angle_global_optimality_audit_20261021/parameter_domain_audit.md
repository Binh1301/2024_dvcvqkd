# Audit of the historical optimization domain

Status: **STAGE 1 COMPLETE; NEW-SOURCE PILOT AWAITS EXPLORATORY-DOMAIN APPROVAL**.

## Which experiment governs this audit

The historical `skr_vs_zenith_angle_20261019/protocol.json` governs: 182 MB
and 36 Uniform ensembles; 31 angles 0:2:60 degrees; full divergence 233 urad,
receiver diameter 0.08 m; beta=0.95, xi_ch=0.0186 SNU; ideal detector R=1,
xi_det=0. The rate is normalized two-dimensional I/Q MI minus the recorded
homodyne-conditioned Holevo term. The 233-source mobility roster is excluded.

The frozen specification's dedicated redesigned-baseline experiment uses
w0=0.10 m and Dr=0.55 m and has a separately authorized unbounded MB domain.
It explicitly preserves historical experiment snapshots. That authorization,
its heterodyne convention, and its optical configuration cannot define or
silently replace the present historical experiment.

Current FINAL_MODEL_SPEC raw SHA-256 is
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`, differing
from AGENTS' historical `561fecc9...` hash. This pre-existing authority conflict
is retained as a blocker to model/security promotion, not repaired by this audit.

## Actual finite catalog

| Family | Count | VA range, SNU | Raw nu range | Unique VA | Unique raw nu |
| --- | --- | --- | --- | --- | --- |
| Uniform | 36 | 0.02--12 | 0 | 36 | 1 |
| MB | 182 | 0.025--8 | 0.05--0.8 | 57 | 33 |

The 36 Uniform variances are:

`0.02, 0.025, 0.04, 0.0475, 0.05, 0.0525, 0.06, 0.075, 0.08, 0.1,
0.11, 0.12, 0.13, 0.14, 0.15, 0.18, 0.2, 0.3, 0.5, 0.6, 0.7,
0.75, 0.8, 0.9, 1, 1.075, 1.25, 1.5, 2, 2.05, 3, 3.025, 4, 5, 8, 12`.

MB is an irregular point set, **not** the rectangle implied by independent
nu/VA ranges. It fills 182 of 33*57=1881 distinct-axis combinations (9.676%).
It includes dense samples near nu=0.165, VA=5.475 and many isolated samples;
there is no single nu or VA step. `original_catalog_candidates.csv` preserves
all 218 exact pairs, original hex values, and identities. `parameter_spacing.csv`
contains every unique coordinate and its predecessor spacing. These full
artifacts, rather than the extrema alone, define the finite feasible catalog.

## Raw versus repository MB parameter

Let u_i=i-7.5 and the unscaled square grid q_ij=u_i+i*u_j. The raw MB law is
`p_ij proportional to exp(-nu_raw*(u_i^2+u_j^2))`. Its uniform mean squared
grid radius is 42.5. The repository's unit-energy reference uses q/sqrt(42.5),
so

`nu_repo = 42.5 * nu_raw`.

For example, raw 0.125 corresponds to repository 5.3125; raw 0.165 to 7.0125;
the tested raw range 0.05--0.8 corresponds to 2.125--34. Saved payload hex
fields and the actual PMFs were checked independently for all 218 sources.
This factor is 42.5, not an assumed factor of 85 or a physical VA dependence.

## Normalization and actual constraint switches

All saved sources obey `VA=2*sum(p*abs(alpha)^2)=2*nbar`. Thus VA is in SNU
and mean photons are VA/2. The source construction centers and rescales each
ensemble to this declared variance. Exactly 256 positive probabilities and
distinct complex amplitudes are retained.

The sweep calls `unconstrained_config()` from
`scripts/run_theta10_D55_unconstrained_three_scheme.py:99`, which sets
`v_min_snu`, `v_max_snu`, `v_a_budget_snu`, and `n_peak_photons` to None.
`make_ensemble()` also explicitly supplies no Uniform bounds or peak guard.
Therefore VA=8 and VA=12 are computational catalog endpoints, not active
physical limits of this experiment. The selected MB source (0.125,8) has
4 mean photons and 56.3026183168 peak photons; Uniform VA=12 has 6 mean
and 15.8823529412 peak photons. A historical 30-photon cap would reject the
selected MB source and must not be retroactively imported into this experiment.

The archived manuscript states VA=nbar/2, whereas the archived request and
authenticated sources deliberately use VA=2*nbar. This already disclosed
normalization discrepancy is preserved; no formula is changed in this audit.
The archived manuscript provides no defensible physical upper VA, maximum
transmit energy, calibrated modulation limit, or source-precision operating
domain that could close the continuous optimization problem.

## Mathematical family versus physical domain

The source constructor's formal family is nu_raw>=0, VA>0 with finite
binary64 inputs. Finite nu produces positive mathematical MB weights, but
floating-point underflow and source-moment conditioning can invalidate a
numerical representation. Constructor acceptance alone is not a physical
feasibility theorem or an approved unbounded optimization domain.

Consequently, the physical domains D_U and D_MB are **NOT FULLY SPECIFIED**.
We neither invent an upper energy constraint nor automatically approve
unbounded VA. Per the task's execution rule, the audit stops before source
generation and requests a bounded **numerical** exploratory domain.

## Exact-source numerical feasibility

The cache binds the common binary64 ensemble hash, raw/repository nu and VA
hex, source implementation, solver settings, and C,w. Current worker settings
are precision ladder 1050/1250/1450 digits, density tolerance 1e-12, and
physicality tolerance 1e-10. Fallback execution is evaluation-only, with a
3600-second subprocess timeout. Its last two precision rows must resolve
rank 256 and agree in C,w within `1e-7+1e-6*max(abs(values))`.

These are necessary solver conditions, not physical bounds or a continuous
optimality certificate. No worker was run here; C,w were authenticated from
historical payloads, not independently recomputed. Any future pilot must
fail closed on missing/invalid source moments, altered provenance, underflow,
inconsistent ensembles, nonphysical covariance, or unresolved GH ranking.

## Concrete proposed pilot: NOT APPROVED, NOT EXECUTED

- Uniform numerical interval: VA in [0.02,48] SNU.
- MB numerical rectangle: nu_raw in [0,1.6], VA in [0.025,32] SNU.
- Six representative angles: 24,30,40,48,52,60 degrees.
- Retain the original 218 candidates unchanged for comparisons.
- First batch: at most six source requests, Uniform VA=16,24,48 and MB
  (nu_raw,VA)=(0.08,16),(0.125,16),(0.2,16). Reuse a provenance-matched cache
  first if present; otherwise create exact C,w sequentially.
- At most 36 new rate evaluations for those six sources across six angles.
- At most 3600 worker-seconds per new source, 21600 seconds total source-worker
  allowance (6 hours worst-case), excluding small orchestration overhead.
- Stop after that batch or earlier on a validation/precision failure. No
  automatic domain expansion, second batch, or full 31-angle optimization.

The wider boxes test three/four times the old VA caps and twice the old nu cap.
They are numerical exploration limits, not newly imposed physical constraints.
The first batch prioritizes the observed rising VA tails; it will not exhaust
these boxes, resolve all nu boundaries, or establish global optimality.
Its results will determine whether a further multiregion/refinement batch is
worth proposing. The exact machine-readable proposal is `proposed_pilot.json`.

GLOBAL OPTIMALITY GAP: NOT CERTIFIED

UNVALIDATED_SECURITY_MODEL

NOT_READY_FOR_PUBLICATION_SCALE_RUNS
