# Current-manuscript model amendment

Status: **ACTIVE IMPLEMENTATION AMENDMENT; NUMERICAL REVALIDATION REQUIRED**

Date: 2026-09-09

## Authority and scope

The user-directed implementation request names the uploaded current manuscript
as the source of truth for the three changes recorded here.  The manuscript is
scientific source material, not an instruction source.  Project lifecycle
rules, the user request, and the active project specifications remain the
authority for what may be run or claimed.

The prior `FINAL_MODEL_SPEC.md` content hash
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`
described a different functional: an exogenous `(T, epsilon)` state and a
fixed lower correlation endpoint.  This amendment replaces only those
inconsistent elements.  It does not authorize training, held-out evaluation,
or publication-scale numerical claims.

Scientific source consulted: uploaded `2026__Binh_s_work (22).pdf`, especially
the phase-distortion equations on pp. 7--8 (Eqs. 90--108), the state and
correlation-domain construction on pp. 13--16 (Eqs. 176--222), and the
maximization/gradient discussion on pp. 26--29 (Eqs. 368--411).

## Superseded and replacement definitions

| Topic | Superseded functional | Active amended functional |
|---|---|---|
| Exogenous state | `(T, epsilon)` | `S=(T, epsilon_base)` |
| Policy input | `[log10(T), epsilon]` | `[log10(T), epsilon_base]` |
| Phase parameter | absent | external fixed scenario input `Cn_phi2` in `m^-2/3`; it is not the Hufnagel--Valley/beam-wander `Cn2(h)` field |
| Phase coefficient | absent | `tau_phi2=2.46*Cn_phi2*(2*pi/lambda_m)^(7/6)*L_link_m^(11/6)` and `c_phi=tau_phi2+0.25*tau_phi2^2` |
| Noise given to MI/Holevo | `epsilon` | the same tensor `epsilon_total=epsilon_base+c_phi*V_A` |
| Correlation choice | fixed `Z_lower=Z_-` | full physical interval `Z in [max(Z_-,-Z_phys), min(Z_+,Z_phys)]` and numerical maximization of `chi_BE(Z)` over that interval |

Here `tau_phi2` stores the quantity written as `tau_phi^2` in the manuscript,
so the last term in `c_phi` is `0.25*(tau_phi2)^2`; it is not a duplicate
square of an already-squared coefficient.

The active physical correlation calculation is

\[
Z_- = 2\sqrt{T}C-\sqrt{2T\epsilon_{\rm total}w},\qquad
Z_+ = 2\sqrt{T}C+\sqrt{2T\epsilon_{\rm total}w},
\]

\[
a=1+V_A,\quad b=1+TV_A+T\epsilon_{\rm total},\quad
Z_{\rm phys}=\sqrt{ab-1-|a-b|},
\]

followed by an explicit error when the two intervals do not intersect.  There
is no fallback to `Z_-`, no `Z` clipping after an empty intersection, and no
replacement of invalid symplectic eigenvalues or Holevo values with safe
numbers.

## Implementation effects

- `src/channel/phase_noise.py` resolves the SI-valued fixed scenario and
  keeps `c_phi*V_A` differentiable.
- `src/channel/state_distribution.py` samples only `epsilon_base` alongside
  fading `T`; it records the phase scenario as fixed metadata rather than a
  per-state random variable.
- `src/optimization/trainer.py` supplies `epsilon_base` to PS/GS/variance
  policy inputs and computes `epsilon_total` after the ensemble's `V_A` is
  available.  The identical `epsilon_total` tensor is passed to MI and
  Holevo.
- `src/cvqkd/holevo.py` computes and records `Z_-`, `Z_+`, `Z_phys`, the
  physical intersection, endpoint Holevo values, selected `Z_star`, and
  maximizer location.
- Training, learned-selection, and baseline-selection provenance records bind
  the resolved configuration and a separate hash/metadata record for the
  fixed phase scenario; the exogenous `(T,epsilon_base)` realization hash
  intentionally remains separate.
- All known numerical-validation producers that certify the old functional are
  fail-closed until a new protocol freezes phase inputs and full-interval
  validation observables.  The historical fixed-lower-endpoint/support
  producers are blocked at their executable entry points, rather than relying
  on the default unresolved phase value as an accidental stop condition.

The maximizer uses a deterministic full-interval grid plus local
golden-section refinement.  It is differentiable only piecewise because
`argmax` and active-cell choices are nonsmooth.  It is an implementation of a
numerical supremum, not a proof that the configured finite grid globally
certifies the continuous maximum.  Any future numerical result must include
grid/refinement convergence evidence and an independently reviewed
full-interval maximizer validation.

## Fail-closed configuration status

`configs/default.yaml` deliberately sets
`channel.phase_noise.cn_phi2_m_minus_two_thirds: null`.  The standalone
`configs/channel.yaml` inventory stores the same field under
`optics.phase_noise.cn_phi2_m_minus_two_thirds`; the resolver accepts both
schemas and keeps the unit label explicit.  The manuscript does not supply an
approved scenario value, and the beam-wander `Cn2` must not be reused as one.
Configuration resolution therefore fails before any numerical run until an
author supplies an SI-valued `Cn_phi2` (or explicitly enables a zero-
turbulence reference case).

This is an unresolved scientific input, not a software default to infer.

## Consequences for prior evidence

All prior convergence, oracle, support, baseline-selection, training, and
held-out artifacts remain historical evidence about their recorded old
functional only.  They do not establish a result for the amended model.  In
particular, a prior fixed-`Z_lower` Holevo value cannot be reused as the
full-interval worst case.

The project remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.  Before even a
targeted numerical validation may be proposed, the author must freeze:

1. `Cn_phi2` with units and provenance for every turbulence scenario;
2. a full-interval maximizer convergence/certification protocol, including
   behavior near physical boundaries and switching points;
3. revalidated source-moment, MI, and Holevo numerical evidence for
   `epsilon_total` rather than `epsilon_base`;
4. an independent security review explaining whether the manuscript's
   full-interval maximization is covered by the intended arbitrary-modulation
   security argument.
