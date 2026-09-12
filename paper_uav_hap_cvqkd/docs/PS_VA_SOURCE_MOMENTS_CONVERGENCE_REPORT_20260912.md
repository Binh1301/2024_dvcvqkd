# 1. Skills / workflow used

Used the repository's evidence-first frozen-gate workflow and the local
Superpowers plans for the corrected AP worker/full-support source-moment path.
Ponytail was applied by reusing the existing worker, checkpoint loader, C4
sector construction, and full-Z implementation; only a minimal diagnostic
wrapper branch and result recorder were added. No retraining, production
equation change, alternate backend, dense global eigensolve, or phase-noise
enablement was performed.

# 2. Frozen PS+VA candidate

The existing repaired-objective checkpoint was used unchanged:

| field | value |
|---|---|
| checkpoint | `results/repaired_full_z_checkpoint_ps_va_20260911_step_50.pt` |
| checkpoint SHA-256 | `1c5d49d1a562c558a18a76994399b09c4bee88ddbebf35370ae9cb690e3ca8d` |
| direct input hash | `4589747c3ae1cf3d8ce996d13f591a0e8f2aae7dd64df402a81507255dd43a99` |
| probability hash (64 q hex values) | `cb54155a394cad8ce7c162fdfd43e620bf89e7da366a241bd2a6aa7574bee47b` |
| orbit constellation hash | `3e56859fb805f8f445c6ec8c465fc435b1b5706a025e67f673c649f30498fcab` |
| full constellation hash | `ee71ed4bbd636ac5418ded90f9762a1ef6f9c0b61a7954f4621ca59332b2ee96` |
| `T` | `0.022181763383054068` (`0x1.6b6d0f130f9b4p-6`) |
| `epsilon_base` | `0.02025322309984713` (`0x1.4bd42cb68e4c4p-6`) |
| `epsilon_total` | `0.02025322309984713` (phase-disabled: `epsilon_base + 0*V_A`) |
| `V_A` | `0.9953704226185827` (`0x1.fda131291ae2cp-1`) |
| q count / full alpha count | `64 / 256` |
| q range / sum | `[0.007898899797162628, 0.026864105952301764]` / `1.0` |
| unique coherent states | `256` |

The complete serialized 64 q values and 256 full amplitudes are frozen in the
machine-readable artifact. Reload verification reproduced the direct-input
hash, C4 probability/amplitude errors were both zero, all q values were
positive, and the corrected worker contains `aa = x2.T` with no legacy
`aa = sr * x2.T` expression.

# 3. 1050-digit diagnostic

All four 64x64 sectors resolved with 64 positive modes, for total support
256. `R_rec` is the captured matrix reconstruction residual; `R_orth`,
`R_sqrt`, `R_inv`, and `R_solve` are respectively orthogonality,
square-root, inverse-square-root, and factorized-solve residuals. The wrapper
did not retain a separately named `G U-U Lambda` residual, so no value is
invented for that distinct diagnostic.

| sector | positive modes | lambda_min | lambda_max | R_rec / R_orth / R_sqrt / R_inv | R_solve | runtime |
|---:|---:|---:|---:|---|---|---|
| 0 | 64 | `1.756e-584` | `6.516e-1` | `1.57e-1050 / 2.60e-1050 / 2.73e-1050 / 9.59e-471` | `0` (2 calls) | row `844.7600824 s` |
| 1 | 64 | `5.518e-598` | `2.286e-2` | `1.23e-1050 / 2.05e-1050 / 2.76e-1050 / 2.10e-464` | `0` (2 calls) | row `844.7600824 s` |
| 2 | 64 | `1.968e-593` | `7.863e-2` | `1.11e-1050 / 2.57e-1050 / 7.96e-1051 / 1.57e-466` | `0` (2 calls) | row `844.7600824 s` |
| 3 | 64 | `6.603e-589` | `2.395e-1` | `8.90e-1051 / 2.49e-1050 / 8.44e-1051 / 3.90e-468` | `0` (2 calls) | row `844.7600824 s` |

Diagnostic C/w were `0.8610813007552428909072445071897962976560950806268` and
`0.0067220381757562110710871873472856506670610666856165`.

# 4. 1250-digit result

All four sectors resolved with 64 positive modes, for total support 256.

| sector | positive modes | lambda_min | lambda_max | R_rec / R_orth / R_sqrt / R_inv | R_solve | runtime |
|---:|---:|---:|---:|---|---|---|
| 0 | 64 | `1.756e-584` | `6.516e-1` | `1.04e-1250 / 1.56e-1250 / 2.48e-1250 / 1.39e-670` | `0` (2 calls) | acceptance pair only; solve-only `152.2347689 s` |
| 1 | 64 | `5.518e-598` | `2.286e-2` | `2.54e-1250 / 1.92e-1250 / 3.89e-1250 / 3.71e-664` | `0` (2 calls) | acceptance pair only; solve-only `152.2347689 s` |
| 2 | 64 | `1.968e-593` | `7.863e-2` | `1.12e-1250 / 1.30e-1250 / 1.23e-1250 / 5.20e-667` | `0` (2 calls) | acceptance pair only; solve-only `152.2347689 s` |
| 3 | 64 | `6.603e-589` | `2.395e-1` | `4.87e-1251 / 1.49e-1250 / 7.46e-1251 / 6.28e-669` | `0` (2 calls) | acceptance pair only; solve-only `152.2347689 s` |

`C_1250 = 0.8610813007552428909072445071897962976560950806268`

`w_1250 = 0.0067220381757562110710871873472856506670610666856165`

# 5. 1450-digit confirmation

All four sectors resolved with 64 positive modes, for total support 256.

| sector | positive modes | lambda_min | lambda_max | R_rec / R_orth / R_sqrt / R_inv | R_solve | runtime |
|---:|---:|---:|---:|---|---|---|
| 0 | 64 | `1.756e-584` | `6.516e-1` | `1.08e-1450 / 2.04e-1450 / 1.14e-1450 / 1.35e-871` | `0` (2 calls) | acceptance pair only; solve-only `217.5061456 s` |
| 1 | 64 | `5.518e-598` | `2.286e-2` | `3.34e-1450 / 2.85e-1450 / 6.36e-1450 / 7.35e-864` | `0` (2 calls) | acceptance pair only; solve-only `217.5061456 s` |
| 2 | 64 | `1.968e-593` | `7.863e-2` | `4.05e-1450 / 2.12e-1450 / 6.69e-1450 / 6.54e-868` | `0` (2 calls) | acceptance pair only; solve-only `217.5061456 s` |
| 3 | 64 | `6.603e-589` | `2.395e-1` | `5.43e-1451 / 1.85e-1450 / 6.37e-1451 / 2.51e-868` | `0` (2 calls) | acceptance pair only; solve-only `217.5061456 s` |

`C_1450 = 0.8610813007552428909072445071897962976560950806268`

`w_1450 = 0.0067220381757562110710871873472856506670610666856165`

# 6. 1250/1450 convergence

The frozen source-moment criterion was

`absolute_delta <= 1e-7 + 1e-6 * max(abs(value_1250), abs(value_1450))`.

| metric | absolute delta | relative delta | frozen tolerance | result |
|---|---:|---:|---:|---|
| C | `0E-49` | `0` | `9.610813007552428909072445071897962976560950806268e-7` | PASS |
| w | `0E-52` | `0` | `1.067220381757562110710871873472856506670610666856165e-7` | PASS |

The serialized 1250/1450 values are equal at the worker's 50-digit output
precision (`stable_digits: serialized_equal`). Both rows are full-rank with
the recorded residuals and no inverse-related numerical failure.

# 7. Authoritative PS+VA source moments

`C_PSVA = 0.8610813007552428909072445071897962976560950806268`

`w_PSVA = 0.0067220381757562110710871873472856506670610666856165`

Classification: `PS_VA_SOURCE_MOMENTS_CONVERGED`.

# 8. Exact-vs-surrogate source moments

| metric | exact | surrogate | absolute error | relative error |
|---|---:|---:|---:|---:|
| C | `0.8610813007552428909...` | `0.8610813078435491` | `7.0883061642490475e-9` | `8.23186632671269e-9` |
| w | `0.006722038175756211071...` | `0.006722081718878012` | `4.354312180092357e-8` | `6.477666544347628e-6` |

This comparison is diagnostic only. The security calculation below uses the
authoritative AP C/w values.

# 9. Median full-Z interval

Using the current 33-grid/12-refinement full-Z implementation:

| quantity | value |
|---|---:|
| `Z_minus` | `0.25403343722167576` |
| `Z_plus` | `0.258948630366243` |
| `Z_phys` | `0.2597704247412494` |
| `Z_L` | `0.25403343722167576` |
| `Z_U` | `0.258948630366243` |
| `Z_star` | `0.25403343722167576` |

The interval check `Z_L <= Z_star <= Z_U` passes; the selected point is the
lower boundary. No phase noise or raw-K clipping was used.

# 10. Exact median security

| quantity | value |
|---|---:|
| `I_AB` | `0.01569902141495305` |
| `beta*I_AB` | `0.014914070344205398` |
| `chi_BE` | `0.014533912528089` |
| raw `K` | `+0.0003801578161163992` |

The run used `beta=0.95`, 512 frozen anchor noise samples, and the phase-
disabled `epsilon_total = epsilon_base` scenario. The security domain was
valid and the current implementation reported no numerical repairs.

# 11. Exact median ranking

`PS_VA_MEDIAN_BEST`

The exact median raw-K values used for the ranking were:

| method | raw K |
|---|---:|
| PS+V_A | `+0.0003801578161163992` |
| Full | `+0.0003328325002894157` |
| MB | `-0.00045919497163375914` |

# 12. Scientific interpretation

At this one median state, exact PS+V_A is above Full, which is above MB. This
is the prescribed preliminary pattern suggesting that adaptive PS+V_A may be
the strongest method and that GS may be unnecessary after the repaired
objective. It is not evidence for a three-state or publication-scale adaptive
claim; poor and good states were deliberately not run.

# 13. Runtime

| computation | measured runtime |
|---|---:|
| 1050 diagnostic row | `844.7600824 s` wall-clock |
| 1250 + 1450 acceptance process | `2009.1630606 s` combined wall-clock |
| 1250 solve calls only | `152.2347689 s` |
| 1450 solve calls only | `217.5061456 s` |

The acceptance wrapper executed 1250 and 1450 in one process and did not
capture a separate wall-clock boundary for each rung. The artifact records
that limitation explicitly; solve-only totals are reported separately and
are not substituted for full-row runtimes.

# 14. Code/artifact changes

Added diagnostic-only instrumentation to
`scripts/replay_instrumented_current_worker.py` and a one-shot recorder at
`scripts/record_ps_va_median_authority.py`. The production worker,
`src/cvqkd/gram_moments.py`, model checkpoint, C/w equations, support
semantics, channel, full-Z implementation, and CI were not changed.

Created:

- `results/ps_va_source_moments_1050_20260912.json`
- `results/ps_va_source_moments_1250_1450_20260912.json`
- `results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json`
- this report

The authoritative artifact SHA-256 is
`9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`.

# 15. Verification

- `py_compile`: PASS for the worker, diagnostic wrapper, and recorder.
- Corrected worker source assertion and cheap C4/global structural tests:
  PASS.
- Explicit corrected C/w fixture regression: the test reached the
  `perturbed_geometry` fixture but the existing complex128 production gate
  returned `None` because its residual was `1.343480882098902e-12`, just
  above `FAST_MAX_RESIDUAL=1e-12`; this is recorded as a harness limitation,
  not silently treated as a pass.
- Three artifact-binding tests also cannot run because their historical
  superseded result files are absent from this checkout.
- Authoritative artifact JSON/schema/hash validation: PASS.
- `git diff --check`: PASS.
- No 1050/1250/1450 target job was added to normal CI.

# 16. Lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

# 17. Remaining blocker

The exact poor/good-state PS+V_A adaptive ranking remains incomplete.

# 18. Recommended next task

Because adaptive PS+V_A beats MB at the median, recommend **exact poor + good
ranking only** under a separately authorized task. Do not execute it here.
