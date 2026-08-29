# Evidence register

Status: current through the **prospective numerical-certification-protocol
review**. Results are diagnostics, not publication claims.

## Bound artifacts

| Artifact | SHA-256 | Purpose |
|---|---|---|
| `results/production_gram_certification.json` | `694e5237ccbbf2fe231361dd9ef05303cc72c8b215fa47e6bb40d5bf5c3685ab` | 16-fixture forward, HP stress, and 12-coordinate local-gradient evidence |
| `results/support_threshold_protocol_audit.json` | `673b957234cebaa349340cdadac0ea25f016d01f2189ab5861a137b0bf3cab5b` | Complete 12-disagreement observable/eigenvalue audit |
| `results/direct_support_boundary_sweep.json` | `983e2b4eb7e19bd543ecf17083375762eb3c7e737aa5a90cd51ab32b9d262c73` | Direct PS/GS/VA crossing incidence |
| `results/support_rollback_feasibility.json` | `695f2bc292860457b70a917ce6d42f4094f34bf67b8bcc185caeea4165acccb2` | 960 proposals and objective-free sequential mobility |
| `results/support_boundary_bisection_crn.json` | `2d57ab236541d523dfca484478b86e724e2a7391b1ed2df105ab4e3791908418` | Bisections, cross-run interval, one-sided CRN derivatives, and outward trapping |
| `results/near_coincident_gram_oracle.json` | `2db2388d53052c228fcc0bd96b69d90803d3545da270619f390d03ed5b60b2d1` | Independent 1250/1450-digit full-support stress oracle |

`docs/FINAL_MODEL_SPEC.md` remains unchanged at
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.

## Twelve cross-threshold support disagreements

Ranks are bad/medium/good. Eigenvalues are those in `(1e-14,1e-13]`.
Each delta is the maximum absolute difference over the three states. Full
reference and candidate values, zero-safe relative errors, per-state allowed
errors, and normalized tolerance use are in the bound JSON artifact.

| Fixture | Rank `1e-14` | Rank `1e-13` | Between-threshold eigenvalue(s) | dC | dw | dZ | dl1 | dl2 | dl3 | dchi | dK |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform low | 9/9/9 | 8/8/8 | `3.33933e-14` | `2.514e-12` | `1.149e-10` | `4.482e-11` | `2.651e-12` | `2.651e-12` | `2.778e-12` | `1.474e-11` | `1.474e-11` |
| Uniform high | 18/18/18 | 17/17/17 | `4.47760e-14` | `2.679e-12` | `4.626e-10` | `5.957e-11` | `1.070e-11` | `1.070e-11` | `1.831e-11` | `4.731e-11` | `4.731e-11` |
| Binomial low | 11/11/11 | 10/10/10 | `1.39005e-14` | `7.365e-13` | `2.894e-12` | `1.151e-11` | `7.014e-13` | `7.012e-13` | `7.352e-13` | `3.965e-12` | `3.965e-12` |
| Binomial high | 30/30/30 | 29/29/29 | `3.47091e-14` | `1.963e-12` | `2.457e-12` | `5.004e-12` | `9.299e-13` | `9.304e-13` | `1.581e-12` | `4.974e-12` | `4.974e-12` |
| Fixed MB low | 9/9/9 | 8/8/8 | `4.16837e-14` | `3.076e-12` | `1.215e-10` | `4.942e-11` | `2.927e-12` | `2.927e-12` | `3.068e-12` | `1.630e-11` | `1.630e-11` |
| Fixed MB high | 18/18/18 | 17/17/17 | `7.58444e-14` | `4.447e-12` | `5.468e-10` | `7.452e-11` | `1.341e-11` | `1.341e-11` | `2.294e-11` | `5.972e-11` | `5.972e-11` |
| Optimized MB 0.3 low | 9/9/9 | 8/8/8 | `6.47828e-14` | `4.596e-12` | `1.345e-10` | `5.980e-11` | `3.551e-12` | `3.550e-12` | `3.721e-12` | `1.982e-11` | `1.982e-11` |
| Optimized MB 0.3 high | 19/19/19 | 18/18/18 | `1.87681e-14` | `1.151e-12` | `2.183e-10` | `3.298e-11` | `5.955e-12` | `5.955e-12` | `1.019e-11` | `2.691e-11` | `2.691e-11` |
| Untrained full | 14/14/13 | 13/13/13 | `1.01911e-14,1.06292e-14` | `6.729e-13` | `2.142e-10` | `3.748e-11` | `4.897e-12` | `4.897e-12` | `6.297e-12` | `2.400e-11` | `2.400e-11` |
| Deterministic PS | 18/18/18 | 17/17/17 | `4.23250e-14..4.26333e-14` | `2.559e-12` | `5.249e-10` | `6.709e-11` | `1.205e-11` | `1.205e-11` | `2.062e-11` | `5.327e-11` | `5.327e-11` |
| Deterministic GS | 19/19/19 | 18/18/18 | `7.50936e-14` | `4.506e-12` | `4.062e-9` | `6.769e-10` | `1.226e-10` | `1.226e-10` | `2.097e-10` | `5.607e-10` | `5.607e-10` |
| Deformed full | 15/15/15 | 14/14/14 | `8.07223e-14..9.62772e-14` | `5.564e-12` | `2.854e-10` | `7.006e-11` | `1.002e-11` | `1.002e-11` | `1.354e-11` | `4.964e-11` | `4.964e-11` |

All rows pass. Worst tolerance use is 3.5728%, from deterministic-GS `w`;
its worst relative change is `2.97e-7`.

## Boundary and feasibility evidence

- Direct admissible crossings: PS `5/1512`, GS `6/1512`, VA `44/420`;
  84 additional VA probes leave the frozen box and fail closed. No crossing is
  observed at 10x or smaller family learning-rate scale. Stress remains rank 8.
- Nearest deformed-full bad-state cross-run boundary interval:
  `[0.002889168901951052,0.002889923634]` in direct log-VA.
- At `rho=1e-6`, `|dchi|=1.972e-8`, `|dK|=3.67e-11`; fixed-side
  raw-K AD/FD errors remain within 0.5%. At `rho=1e-7`, support becomes
  execution-sensitive; at `1e-8`, raw-K derivative errors become order 20%.
- Random proposals: `0/960` rejected. Objective-free trajectories:
  `768/768` accepted, no trapped isotropic trajectory, nonzero motion in all
  families.
- Plain persistent outward VA rollback accepts `0/50`, `5/50`, and `50/50`
  in the native artifact from starts `5e-5`, `5e-4`, and `5e-3` below its
  native boundary. An independent execution gives `0/50`, `4/50`, and `49/50`.
  Exact-mask rollback is therefore both trap-prone and execution-sensitive.

## Scope limits

These artifacts certify numerical behavior of the accepted asymptotic
covariance-based functional only. They do not establish an attack theorem,
finite-size/composable security, imperfect-CSI parameter estimation, or a
fading/adaptation security proof.

