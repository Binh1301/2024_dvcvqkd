# Session Handoff

## Latest completed task: EVID-0083 / DEC-0067

The attached PDF5 Table-I HAP--UAV FSO channel is implemented as the active
channel-only path. The Hufnagel--Valley profile and finite-aperture equations
derive `v_sc=0.02886934966162772`. Exact PDF Gaussian-beam pointing derives
`omega_L=2.118504621202276 m`, `G_d=0.00024089665983497693`,
`A0=0.0007127365410377602`, and `omega_L_eq=2.1191553233134117 m`.
The active sampler uses Rician displacement, Eq. (36) `H_p`, Eq. (1)
composition, exact AoA outage `T=0`, and rejection-based active-domain
admission without clipping or a positive floor.

Analytical utilities implement Eqs. (12), (37), (49), and (50). The bounded
diagnostic `scripts/run_hap_uav_fso_pdf_diagnostic.py` ran with `N=10000`,
seed `42`; the artifact is
`results/hap_uav_fso_pdf_diagnostic/diagnostic_results.json` and includes four
Monte Carlo/analytical-PDF figures plus saved arrays.

Focused channel/PDF/state/outage/pipeline/phase tests: 56 passed. The broader
energy/physical-peak test selection still has three pre-existing
`FULL_SUPPORT_FALLBACK_EVALUATION_ONLY` errors; no security or trainer code
was changed to bypass them.

## Changed project surface

- `src/channel/pointing_error.py`, `src/channel/scintillation.py`,
  `src/channel/fso_channel.py`, `src/channel/state_distribution.py`, and
  `src/channel/diagnostics.py`: exact PDF5 primitives, active PDFs, moments,
  configuration overrides, provenance, and compatibility aliases.
- `configs/default.yaml` and `configs/channel.yaml`: PDF5 Table-I baseline
  inputs; phase `C_n,phi^2` remains null.
- `scripts/_train.py`, `_common.py`, `_numerical_validation.py`, baseline
  selectors, freeze wrapper, and the channel diagnostic: central wiring and
  explicit provenance.
- `tests/test_pdf_channel_model.py` plus focused expectation updates.
- `docs/` current alignment/evidence/decision/state/next-action records.

The old EVID-0082 generalized-pointing/old-aperture artifact is retained as
historical superseded evidence. The frozen model specification, CV-QKD,
Holevo, optimizer, PS/GS/V_A, training, final-test, and publication lifecycle
were not changed or authorized.

Branch: `feat/step-one`
HEAD: `62f8d390095e4e6ef3721789e9658b4015090ea9`
Lifecycle: `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`
Adaptive training: `NOT_READY_FOR_ADAPTIVE_TRAINING`

## Exactly one next action

Do not run training or security evaluation. If separately authorized, rebind
the target numerical/security evidence to this new channel configuration before
any learned or publication claim.
