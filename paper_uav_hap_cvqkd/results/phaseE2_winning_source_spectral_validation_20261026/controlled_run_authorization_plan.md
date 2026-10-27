# Controlled one-source run: prepared, not authorized or executed

This is a reviewable plan for a separate user-authorized calculation. E2 stops
at preparation. No authorization receipt has been created and no controlled
checkpoint directory exists.

Future output is isolated in results/phaseE2_winning_source_controlled_run_v1/,
not in this sealed preparation package. Its authorization receipt and
controlled_checkpoints/ directory will only be created after separate approval.

Plan: controlled_run_plan.json.
SHA-256: **9e113703b991990d2714983d56f5c326c80c4b51342d56a528bdf482169025b6**.
Any producer/source/plan change requires a fresh hash binding before execution.

Proposed command, from the project directory, **NOT RUN**:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B `
  .\results\phaseE2_winning_source_spectral_validation_20261026\checkpoint_wrapper.py `
  --controlled-run .\results\phaseE2_winning_source_spectral_validation_20261026\controlled_run_plan.json `
  --authorization-file .\results\phaseE2_winning_source_controlled_run_v1\authorization.json
```

authorization.json is deliberately absent. After explicit user approval, a
separate receipt must bind the plan hash and the decision
USER_APPROVED_SINGLE_SOURCE_FULL_SUPPORT_RUN. The current task supplies no such
approval. A missing/incorrect receipt stops execution before launching a worker.

| Item | Proposed setting |
|---|---|
| Source | Original Winner_MB NPZ and payload, exact hashes in plan |
| Precision | Independently constructed 400 and 500 decimal digit runs |
| Matrices | Four 64x64 complex Hermitian C4 weighted-Gram sectors per precision |
| Numerical floor | 1e-380 and 1e-480, respectively; never interpreted as mathematical zero |
| Checkpoints | Future result namespace / controlled_checkpoints/dps_400/sector_0.json ... sector_3.json; similarly dps_500 |
| Moment checkpoint | Each precision's moments.json with sector checkpoint hashes |
| Execution | Sequential actual-base-interpreter workers, one numerical thread |
| Per stage | At most 600s; each sector and final moment stage separately monitored |
| Total | At most 3600s active controller wall; prior recorded worker time deducted on manual resume |
| Memory | Terminate above sampled 1024MiB numerical-worker working set |
| Retry | None automatically; preserve completed sectors and explicit failure receipts |

The watchdog polls every 0.1s; kill/serialization overhead is reported. Memory is
a sampled working-set limit, not an OS hard allocation guarantee. Resume is
compatible only at identical source, code, backend/version, precision and policy.
The two precision levels never reuse one another's eigensystems.

Numerical success requires all 64 modes in every sector at both precisions,
per-pair residuals, reconstruction and orthogonality within 10^(-digits+10),
and lambda_min at least 1e20 times the **nominal**, non-enclosing rounding-plus-
residual allowance. All 256 sector-matched eigenvalues should agree to relative
1e-20. If a tight eigenvalue cluster appears, compare its projectors, not raw
eigenvector components or phases. Independently review source moments under the
unchanged local Phase E targets: |delta C|<=2e-11; |delta w|<=2e-12 **and**
relative |delta w|<=0.001. Direct/residual consistency and finite valid inputs
are required. The local tolerances do not approve a production/security claim.

Automated stop: authorization/identity mismatch, resource limit, worker failure,
consistency failure, unresolved sector rank or inadequate nominal spectral
margin. No higher precision, source substitution or eigenvalue repair follows.

**The runner does not automatically issue FULL_SUPPORT_CERTIFIED.** After any
successful run, assess cross-precision eigenvectors/subspaces, conditioning,
matrix-input roundoff and inverse-square-root amplification. If claiming a
rigorous C,w interval, provide a valid functional enclosure; the scalar
lambda_min certificate alone is insufficient. If adequate accuracy cannot be
justified, report INCONCLUSIVE despite rank256 or matching displayed moments.

The 400/500 recommendation follows the observed finite-spectrum scale and the
certified >=1e-312 global floor. Target runtime is unmeasured. The 60-minute cap
is a budget, not a promise. Existing Phase E logs/checkpoints are analysis inputs;
no usable historical eigenvector checkpoint can be silently reconstructed.

No other source, missing Uniform, catalog, channel, MI, Holevo, SKR or mobility
run is included. Historical caches, manuscripts, frozen specifications,
source classes and all lifecycle/security gates remain protected.
