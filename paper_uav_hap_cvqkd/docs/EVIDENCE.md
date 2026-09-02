# Evidence Register

This register is mostly append-only. Evidence status describes the evidence,
not lifecycle authorization. `QUARANTINED` evidence must not support approval.
Machine-readable JSON artifacts currently exist locally under `results/` but
are ignored by `.gitignore`; see EVID-0013.

## EVID-0001 — Frozen model identity and security scope

Date: 2026-08-30

Status: ACTIVE

Scope: Scientific model and permitted security claims.

### Claim

`FINAL_MODEL_SPEC.md` is the authoritative frozen model and has SHA-256
`561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
The implemented claim is an asymptotic oracle-CSI covariance-based DM-CV-QKD
rate functional; no attack class is assigned to the adaptive fading average.

### Evidence

- `docs/FINAL_MODEL_SPEC.md`
- `docs/SECURITY_SCOPE_FREEZE.md`
- `src/cvqkd/protocol.py`
- `src/cvqkd/secret_key_rate.py`

### Provenance

Producer hash: not applicable; frozen Markdown specification.

Config hash: not applicable.

Input/roster hash: not applicable.

Repository commit: `0ced45a6ed0004267f34e66e7638d7e7d28bc93d`.

Schema version: not applicable.

### Reproduction / verification

Run `Get-FileHash docs/FINAL_MODEL_SPEC.md -Algorithm SHA256` from the project
root and compare the lowercase digest above.

### Limitations

This identity does not certify numerical convergence or a complete security
proof.

### Supersedes / Superseded by

Supersedes pre-freeze unrestricted-PMF/weighted-centering descriptions.

## EVID-0002 — Frozen C4 transmitter implementation

Date: 2026-08-30

Status: ACTIVE

Scope: Physical transmitter architecture and normalization.

### Claim

The source implements 64 C4 orbit masses expanded to 256 tied probabilities,
one global unit-RMS GS prototype set, an independent adaptive-VA branch, and
the statewise scalar normalization
`alpha = sqrt(V_A/(2 sum_k q_k |z_k|^2)) x`. The same ensemble object is
passed to MI and Holevo paths.

### Evidence

- `src/modulation/probabilistic_shaping.py`
- `src/modulation/geometric_shaping.py`
- `src/modulation/joint_ps_gs.py`
- `src/modulation/normalization.py`
- `tests/test_frozen_transmitter.py`
- `tests/test_normalization.py`
- `tests/test_pipeline_consistency.py`
- `docs/FINAL_MODEL_SPEC.md`

### Provenance

Producer hash: current source tree; inspect Git diff before use.

Config hash: `dc2a9a5af8028c0f22cb6e8600a12a60f023ccc7d274f95c7557c134802ab015`
for `configs/default.yaml` at reconstruction.

Input/roster hash: not applicable to architecture.

Repository commit: `0ced45a6ed0004267f34e66e7638d7e7d28bc93d`, dirty worktree.

Schema version: not applicable.

### Reproduction / verification

Inspect the cited source and run the cited tests in the locked environment.

### Limitations

The tests are present, but the current environment cannot execute them because
PyTorch is unavailable. Architecture does not imply numerical certification.

### Supersedes / Superseded by

Supersedes the legacy unrestricted 256-logit and weighted-centering path.

## EVID-0003 — Mutual-information sample count selected at 2048

Date: 2026-08-27

Status: ACTIVE

Scope: Finite preregistered MI certification roster only.

### Claim

The sequential MI artifact has status `CONVERGENCE_SELECTED` and selects
`N_MC=2048` after the preregistered global refinement and replication rules.
The roster hash is
`e91c2f9ded0c665e781a450286ffc01633e310a95d77e923efb3b9516791b531`;
the validation-state realization hash is
`247b428bb5dcbaf5e532ecd15a3b46efdf07bdcc47759348a8625576c2c4c500`.

### Evidence

- `results/mi_convergence.json`
- `docs/MI_CERTIFICATION_ROSTER.md`
- `docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`
- `src/cvqkd/mutual_information.py`
- Artifact SHA-256:
  `6fb7134690ecfc5c17f427ea348f0b951ea0df0cbe19b1d9d6db2279c19b10a4`

### Provenance

Producer hash: recorded inside the artifact's generation chain.

Config hash: artifact records resolved-config hash
`92ec2f2f3630ee65dff0a2b4d2d7eb6f13c884685f36552ba066692b5ef7994c`;
the current raw config hash is different and is recorded in PROJECT_STATE.

Input/roster hash:
`e91c2f9ded0c665e781a450286ffc01633e310a95d77e923efb3b9516791b531`.

Repository commit: not embedded as a complete Git provenance record.

Schema version: `mi-sequential-convergence-v2`.

### Reproduction / verification

Verify the artifact hash, status, `minimum_common_sample_count`,
`convergence_selected_sample_count`, roster hash, and all per-stage rules.

### Limitations

Finite fixtures do not certify future learned checkpoints, the continuous
policy domain, Holevo support, or publication performance. The JSON is locally
ignored by Git.

### Supersedes / Superseded by

Supersedes earlier runtime-only MI estimates. Not superseded.

## EVID-0004 — Fock/support convergence gate failed

Date: 2026-08-28

Status: ACTIVE

Scope: Preregistered finite numerical fixture suite.

### Claim

`results/fock_convergence.json` has status `FAILED_FROZEN_TOLERANCE` and no
selectable cutoff because `near_coincident_pseudoinverse_stress` fails. The
stress-only extension through nonselectable cutoff 256 also has no stable
suffix. The failure is support/pseudoinverse conditioning, not density-trace
tail loss.

### Evidence

- `results/fock_convergence.json`, SHA-256
  `1ed980bf1bb033147f245c9a04dd0e3d0de55bf39260bb32563714dd4bfcd8dd`
- `results/near_coincident_fock_diagnostic.json`, SHA-256
  `b70f480475ea5bbe354354e346044286aef47da5417445ab40f3b1f785854287`
- `docs/NUMERICAL_DOMAIN_SCOPE.md`
- `docs/GRAM_ORACLE_DIAGNOSIS.md`

### Provenance

Producer hash: recorded in each artifact.

Config hash: Fock artifact records resolved-config hash
`92ec2f2f3630ee65dff0a2b4d2d7eb6f13c884685f36552ba066692b5ef7994c`
as written in its provenance; verify the artifact directly before reuse.

Input/roster hash: same finite fixture roster described by EVID-0003.

Repository commit: not fully embedded.

Schema version: `fock-convergence-evidence-v2` and
`near-coincident-fock-diagnostic-v1`.

### Reproduction / verification

Verify `status`, `failed_fixtures`, null common cutoff, and the fixed
tolerances in the artifacts and preregistration.

### Limitations

This failure does not prove all physically realized ensembles fail. The active
production backend is now cutoff-independent C4 Gram, but its support rule is
still blocked by the same stress evidence.

### Supersedes / Superseded by

`results/fock_cutoff_certification.json` is deprecated and noncertifying.

## EVID-0005 — Full-support arbitrary-precision stress oracle

Date: 2026-08-28

Status: ACTIVE

Scope: One named near-coincident stress fixture on three validation states.

### Claim

The independent coherent-state Gram oracle resolves all 256 mathematical
modes at 1250 digits and confirms them at 1450 digits. The smallest positive
eigenvalue is approximately `1.722e-1099`. The selected full-support values are
`C=2.0611991664468614` and `w=0.25553407612253914`; successive full-support
differences are far below the frozen tolerances.

### Evidence

- `results/near_coincident_gram_oracle.json`, SHA-256
  `2db2388d53052c228fcc0bd96b69d90803d3545da270619f390d03ed5b60b2d1`
- `docs/GRAM_ORACLE_DIAGNOSIS.md`
- `scripts/oracle_near_coincident_gram.py`

### Provenance

Producer hash:
`a0237188cd5a4d771820e44fa51490f160bec9cebe313400eeac9d265cb3cb4b`.

Config hash:
`cc2a9e401e2cabe3303b2bb31f50741cc257b8f99c40f9b3e61dfcd215a5868e`
as embedded by the oracle artifact.

Input/roster hash: the artifact names the fixture but does not bind a current
semantic ensemble hash; this is a provenance limitation.

Repository commit: not embedded.

Schema version: `near-coincident-gram-oracle-v1`.

### Reproduction / verification

Verify the artifact digest, `full_mathematical_support_oracle_obtained`,
support sizes `[64,64,64,64]`, selected/confirmation precision, and successive
differences.

### Limitations

Only one stress fixture is covered. It does not establish full-support error
control for the other pilot fixtures or continuous PS/GS policies. Its config
hash predates the current raw config, and its semantic fixture binding is
incomplete.

### Supersedes / Superseded by

Supersedes cutoff-256 float64 as a stress-fixture ground truth.

## EVID-0006 — Production C4-Gram backend integration

Date: 2026-08-29

Status: ACTIVE

Scope: Implemented backend and prospective finite diagnostic replay.

### Claim

The public production Holevo path uses cutoff-independent C4 Gram source
moments; dense Fock is explicit diagnostic-only. The production diagnostic
binds current config, MI, oracle, Gram source, and Holevo source hashes. It
reports 16 canonical fixtures, all observable plateaus passing, and 12 local
gradient coordinates passing, but its formal support-identity gate fails and
`all_required_gates_pass=false`.

### Evidence

- `src/cvqkd/gram_moments.py`, SHA-256
  `f13e256887476eb67762be410ed77219b837c7b07367622899260115ce7358a3`
- `src/cvqkd/holevo.py`, SHA-256
  `06c38b43d6ee30d39857b57868adcfcf15a90188e60cd2ef24af38d9e4fa7679`
- `results/production_gram_certification.json`, SHA-256
  `694e5237ccbbf2fe231361dd9ef05303cc72c8b215fa47e6bb40d5bf5c3685ab`
- `tests/test_gram_moments.py`
- `tests/test_holevo.py`

### Provenance

Producer hash:
`3d4d2e5bae4496ee4d75c157d51a453fd38cf6295cac1024080e07e91527a8b6`.

Config hash:
`dc2a9a5af8028c0f22cb6e8600a12a60f023ccc7d274f95c7557c134802ab015`.

Input/roster hash:
`e91c2f9ded0c665e781a450286ffc01633e310a95d77e923efb3b9516791b531`.

Repository commit: source hashes match the current files; artifact does not
embed a complete Git revision.

Schema version: `production-c4-gram-certification-v1`.

### Reproduction / verification

Verify every embedded source/input digest and inspect
`formal_threshold_certification`, `formal_support_identity_gate_passes`, and
`all_required_gates_pass`.

### Limitations

Artifact status is `PROSPECTIVE_DIAGNOSTIC_NOT_READY`, not certification. No
selected checkpoint roster exists. Current dynamic tests are environment-
blocked.

### Supersedes / Superseded by

Supersedes the dense-Fock production wiring. Dense Fock remains historical
diagnostic evidence.

## EVID-0007 — Candidate 1e-13 forward and gradient diagnostics

Date: 2026-08-29

Status: ACTIVE

Scope: Outcome-informed pilot diagnostics only.

### Claim

At candidate `1e-13` versus float64 `1e-14`, all declared observables pass on
the 16-fixture pilot roster, and 12/12 local fixed-support PS/GS/VA coordinates
pass the preregistered finite-difference rule. The near-coincident stress `w`
error versus the full-support oracle is `2.79635e-7`, consuming 78.652% of its
allowance. Formal support identity fails.

### Evidence

- `results/production_gram_certification.json`
- `results/float64_gram_comparison.json`, SHA-256
  `e63abd39e944f4362df36620f4d74ce03afab121337f8d66cdf40981f898cdf6`
- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`

### Provenance

Producer/config/input hashes: see EVID-0006 and the artifacts.

Repository commit: source hashes match the current Gram/Holevo files.

Schema versions: `production-c4-gram-certification-v1` and
`float64-c4-gram-comparison-v1`.

### Reproduction / verification

Verify `all_observable_plateaus_pass`, `all_coordinates_pass`, and the false
formal support gate in the production artifact.

### Limitations

Local fixed-support differentiability is not continuous-segment stability.
Candidate `1e-13` was selected after pilot outcomes and is not approved.

### Supersedes / Superseded by

The proposed protocol was rejected by DEC-0006; diagnostics remain pilot
evidence.

## EVID-0008 — Cross-threshold support audit

Date: 2026-08-29

Status: ACTIVE

Scope: Pilot comparison of `1e-13` against truncated float64 `1e-14`.

### Claim

Twelve fixtures change retained support. All declared observable differences
pass relative to the truncated `1e-14` pilot calculation; the worst normalized
tolerance use is 3.5728% from deterministic-GS `w`. This does not establish
agreement with the physical full-support functional.

| Fixture | Rank at `1e-14` | Rank at `1e-13` | Between-threshold eigenvalue(s) |
|---|---:|---:|---:|
| Uniform low | 9/9/9 | 8/8/8 | `3.33933e-14` |
| Uniform high | 18/18/18 | 17/17/17 | `4.47760e-14` |
| Binomial low | 11/11/11 | 10/10/10 | `1.39005e-14` |
| Binomial high | 30/30/30 | 29/29/29 | `3.47091e-14` |
| Fixed MB low | 9/9/9 | 8/8/8 | `4.16837e-14` |
| Fixed MB high | 18/18/18 | 17/17/17 | `7.58444e-14` |
| Optimized MB 0.3 low | 9/9/9 | 8/8/8 | `6.47828e-14` |
| Optimized MB 0.3 high | 19/19/19 | 18/18/18 | `1.87681e-14` |
| Untrained full | 14/14/13 | 13/13/13 | `1.01911e-14,1.06292e-14` |
| Deterministic PS | 18/18/18 | 17/17/17 | `4.23250e-14..4.26333e-14` |
| Deterministic GS | 19/19/19 | 18/18/18 | `7.50936e-14` |
| Deformed full | 15/15/15 | 14/14/14 | `8.07223e-14..9.62772e-14` |

### Evidence

- `results/support_threshold_protocol_audit.json`, SHA-256
  `673b957234cebaa349340cdadac0ea25f016d01f2189ab5861a137b0bf3cab5b`
- `docs/PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`

### Provenance

Producer hash:
`d08be1bb0389bd2d3ed1778bee53fd304e38f56ea3bfaf506b0b690817996a6f`.

Config hash:
`dc2a9a5af8028c0f22cb6e8600a12a60f023ccc7d274f95c7557c134802ab015`.

Input/roster hash:
`e91c2f9ded0c665e781a450286ffc01633e310a95d77e923efb3b9516791b531`.

Repository commit: artifact binds current Gram/Holevo sources by hash.

Schema version: `support-threshold-protocol-audit-v1`.

### Reproduction / verification

Verify all 12 rows, per-state tolerances, and
`candidate_threshold_assessment.status=PROPOSED_NOT_APPROVED`.

### Limitations

The `1e-14` reference retains only 8–30 modes, not mathematical rank 256.

### Supersedes / Superseded by

Not superseded; restricted to pilot evidence.

## EVID-0009 — Energy and peak-domain evidence

Date: 2026-08-27

Status: ACTIVE

Scope: Author-approved finite physical domain and fixed-baseline checks.

### Claim

Current config freezes `V_A in [0.1,4.0] SNU`, average `V_A<=1.5 SNU`, and
hard `max_i|alpha_i|^2<=30` photons over complete preregistered realizations.
The amplitude artifact passes fixed-baseline checks and leaves learned selected-
roster replay pending.

### Evidence

- `configs/default.yaml`
- `docs/AMPLITUDE_DOMAIN_DECISION.md`
- `results/amplitude_domain_certification.json`, SHA-256
  `6a73374ffd41fc87f490bdb12071cacf3799898c9ada80b5c9935238fdfe16a5`
- `tests/test_physical_peak_domain.py`
- `tests/test_energy_budget.py`

### Provenance

Producer: `scripts/certify_amplitude_domain.py`.

Config hash: artifact records
`48019b65376607341fd2f3c90c64f1c63bec96ad56125d3a54968f882d35bc1f`;
current raw config is `dc2a...`, so the artifact is not by itself current-
config lifecycle proof.

Input/roster hash: fixed analytic families plus declared finite scope.

Repository commit: not embedded.

Schema version: `amplitude-domain-certification-v1`.

### Reproduction / verification

Compare approved values in current config and document, then verify the
artifact status and analytic fixed-family rows.

### Limitations

No continuous-domain bound or learned selected-roster certificate is claimed.

### Supersedes / Superseded by

Supersedes the earlier unbounded/soft-penalty-only domain.

## EVID-0010 — Boundary and rollback diagnostics

Date: 2026-08-29

Status: ACTIVE

Scope: Pilot PS/GS/VA boundary incidence and mobility diagnostics.

The bisection aggregate within this evidence group is `QUARANTINED`.

### Claim

Direct sweeps observe PS `5/1512`, GS `6/1512`, and VA `44/420` admissible
crossings; 84 extra VA probes leave the box. Random proposals reject `0/960`,
and objective-free trajectories accept `768/768`. Native persistent outward
VA rollback accepts `0/50`, `5/50`, and `50/50` from three starting offsets,
showing possible trapping. Cross-runtime boundary values are not certified.

### Evidence

- `results/direct_support_boundary_sweep.json`, SHA-256
  `983e2b4eb7e19bd543ecf17083375762eb3c7e737aa5a90cd51ab32b9d262c73`
- `results/support_rollback_feasibility.json`, SHA-256
  `dceba618fe4ad76a24cfb47d849d1d8c20c836e754a9d5048114ea3c589b3460`
- `results/support_boundary_bisection_crn.json`, SHA-256
  `2d57ab236541d523dfca484478b86e724e2a7391b1ed2df105ab4e3791908418`
  — **QUARANTINED**

### Provenance

Corrected boundary producer hash:
`e3e0dbb80993e7e0dd24c0a8c141015cf8bedaf325943b5448db20a9e3ec0f09`.

Quarantined artifact embeds old producer hash:
`ea6d112dd7762364c105938bf0dcc8f8c7b0b8553525db49b1ee65f3a1c8159f`.

Config/input hashes: recorded in each artifact; verify before reuse.

Repository commit: corrected producer is an uncommitted worktree edit.

Schema versions: `direct-support-boundary-sweep-v1`,
`support-rollback-feasibility-v1`, and
`support-boundary-bisection-crn-v1`.

### Reproduction / verification

Verify direct/rollback artifact hashes and lifecycle guards. Do not use the
quarantined bisection artifact for approval. Regeneration requires a matching
environment, raw per-environment artifacts, and fresh provenance.

### Limitations

Finite probes do not prove continuous-segment stability or nontrapping.
Independently reported boundary span `7.54732e-7` and rollback differences are
unbound pilot observations.

### Supersedes / Superseded by

The corrected producer supersedes the old producer; no replacement artifact
exists yet.

## EVID-0011 — Baseline, training, and final evaluation not run

Date: 2026-08-30

Status: ACTIVE

Scope: Lifecycle dependencies.

### Claim

The 31-by-15 optimized-MB grid, validation baseline selection, publication
training, learned checkpoint selection, final-test access, and held-out
publication evaluation have not occurred. No checkpoint files are present.

### Evidence

- `results/mb_grid_numerical_precertification.json`, status
  `NOT_RUN_FOCK_DEPENDENCY`, SHA-256
  `04bb848f25758b66ac8300ca00d7100e50d78d02c1ef9459e458869058cbd6fd`
- `results/validation_baseline_selection.json`, status
  `NOT_RUN_NUMERICAL_DEPENDENCY`, SHA-256
  `842b5b38b9cfd7b75140c552fbb6dd25d2412ca4b1eff785e876c689f4b56800`
- Empty run directories under `experiments/`; no `*.pt`, `*.pth`, `*.ckpt`, or
  `*.safetensors` files found at reconstruction.
- `configs/default.yaml` records baseline selections as blocked.

### Provenance

Producer/config/input hashes: dependency-blocker artifacts reference upstream
evidence; no selection outcomes exist.

Repository commit: `0ced45a6ed0004267f34e66e7638d7e7d28bc93d`, dirty worktree.

Schema versions: `mb-grid-numerical-precertification-dependency-blocker-v1`
and `validation-baseline-selection-dependency-blocker-v1`.

### Reproduction / verification

Inspect both artifacts and search experiment/checkpoint paths without opening
or generating test data.

### Limitations

Absence of local checkpoints is a current workspace observation; it is not a
claim about external storage.

### Supersedes / Superseded by

Not superseded.

## EVID-0012 — Current verification environment

Date: 2026-08-30

Status: ACTIVE

Scope: Current worktree verification only.

### Claim

Current dynamic test status is `BLOCKED_BY_ENVIRONMENT`: CPython 3.12.10 is
available, but `import torch` fails with `ModuleNotFoundError`. No current
full-suite PASS or exact historical full-suite count is repository-supported.

### Evidence

- `requirements-publication.lock`, SHA-256
  `47d7a39962914a2ad0d22e44cfb4f9dced6684e56ab35a9d0b4d8efd53b29e62`
- Current command: `python -c "import torch"`.
- Individual smoke artifacts under `results/`; none is a complete-suite test
  manifest.

### Provenance

Producer hash: not applicable to local environment probe.

Config hash: not applicable.

Input/roster hash: not applicable.

Repository commit: `0ced45a6ed0004267f34e66e7638d7e7d28bc93d`, dirty worktree.

Schema version: not applicable.

### Reproduction / verification

Run the import command. Do not install dependencies as part of documentation
reconstruction.

### Limitations

This is machine-local and may change in another environment. Historical smoke
artifacts are not a current-worktree dynamic pass.

### Supersedes / Superseded by

Replace with a hash-bound full-suite result when one is actually generated in
the locked environment.

## EVID-0013 — Result-artifact portability limitation

Date: 2026-08-30

Status: ACTIVE

Scope: Repository persistence and handoff reliability.

### Claim

Scientific JSON artifacts are locally present under `results/` but
`.gitignore` excludes `results/*` except `.gitkeep`. Therefore their hashes and
summaries are persistent in this Markdown register, but a clean Git clone does
not contain the JSON payloads.

### Evidence

- `.gitignore`
- `git check-ignore -v results/mi_convergence.json`
- `git check-ignore -v results/production_gram_certification.json`
- Artifact hashes in EVID-0003 through EVID-0011.

### Provenance

Producer/config/input hashes: see individual evidence entries.

Repository commit: `0ced45a6ed0004267f34e66e7638d7e7d28bc93d`.

Schema version: not applicable.

### Reproduction / verification

Run `git status --ignored --short results` and confirm the local files/hashes.

### Limitations

Markdown summaries cannot replace full machine-readable evidence for future
approval. Artifact retention/versioning policy remains unresolved and must be
decided without altering scientific outcomes.

### Supersedes / Superseded by

Superseded by EVID-0014 once the staged allowlist is committed.

## EVID-0014 - Minimal portable certification artifact set

Date: 2026-08-30

Status: SUPERSEDED REPOSITORY STATE

Scope: Evidence persistence and clean-clone reconstruction.

### Claim

The repository now has a narrow `.gitignore` allowlist and a machine-readable
manifest for 19 non-quarantined payloads totaling 16,984,424 bytes. The files
are staged in the current dirty worktree, but are not portable from commit
`0ced45a6...` until these changes are committed.

### Evidence

- `docs/CERTIFICATION_ARTIFACT_MANIFEST.json`
- `.gitignore`
- `git ls-files --stage results`

### Provenance

Each payload's SHA-256 and byte count are embedded in the manifest.

### Reproduction / verification

Recompute every listed file hash and size, then verify each listed result is
not ignored and is present in the Git index.

### Limitations

This does not promote quarantined, deprecated, benchmark, smoke, or unlisted
payloads. A staged-but-uncommitted set is not yet available to a clean clone.

### Supersedes / Superseded by

Superseded by EVID-0020. Commit `8daba301...` contains this original
19-payload foundation; the current worktree manifest extends it to 22.

## EVID-0015 - Outcome-uninspected independent confirmation roster

Date: 2026-08-30

Status: ACTIVE FOUNDATION

Scope: Prospective numerical confirmation only; not final held-out data.

### Claim

Before evaluating candidate outcomes, a disjoint certification channel and
18-fixture roster were frozen with `OUTCOME_INSPECTION_STATUS=NOT_INSPECTED`.
The high-precision oracle subset contains four predeclared fixtures.

### Evidence

- `results/independent_confirmation_roster.json`, SHA-256
  `a9362ee752be5e9eeb5c0152574d0909a95bf7927e48be727ad9a9534600c1de`
- Roster payload SHA-256
  `b5c25689c3634c5bf9f525bc7366b8661174f628077d92f128b3feaa5ae09762`
- `configs/independent_confirmation_roster.yaml`, SHA-256
  `b8205459bf186ce662a649fb819c5d80f8c75c5eba443a12db94d2dc138e70eb`

### Provenance

Producer SHA-256:
`fb2dcb8c19ee45b28e5d5c192db0d982cbc861e3c24afe1c49d5f04e4c62ecb4`.
Schema SHA-256:
`04dc4a082d7171edfb85eb0b8d7f9460d638955696a2e8b3b044cb1f1d0836ee`.
Repository commit: `0ced45a6...`, dirty worktree.

### Reproduction / verification

Run `scripts/freeze_independent_confirmation_roster.py` only under its
fail-closed no-overwrite semantics and validate against the declared schema.

### Limitations

This freezes membership; it does not approve a support threshold. The
certification channel seed is 202701 and fixture seed is 27083001. Its 384
samples are disjoint from train, validation, test, and pilot.

### Supersedes / Superseded by

Supersedes the missing-roster blocker in the prior project snapshot.

## EVID-0016 - Restored locked environment and current dynamic suite

Date: 2026-08-30

Status: ACTIVE

Scope: Current worktree verification.

### Claim

The exact publication lock was installed into the ignored project `.venv`.
The repository-native `unittest` discovery command ran 124 tests with exit
code 0 in 5.932 seconds under CPython 3.12.10 and torch 2.13.0+cpu.

### Evidence

- `results/current_environment_manifest.json`, SHA-256
  `78c35983aaf7fe9fbc636c80d39b9271ea7930c588b28c4d02703c2e2bce5ff9`
- `results/current_test_suite.json`, SHA-256
  `6709db5bcaec5345281832201075ca9b34a26611c5bb22cf8ed6954d7bb324fe`
- Command: `python -m unittest discover -s tests -v`

### Provenance

Test producer SHA-256:
`2b76ea628ef6cd06d0f9804c6f5a904e1ac8c7e24a11daac473bd27334599fb5`.
Test schema SHA-256:
`f7175cbb21b7dd9d213f8cbdc09da40acf46c8ad67787c69f1c926fd1492b35e`.
Requirements lock SHA-256:
`47d7a39962914a2ad0d22e44cfb4f9dced6684e56ab35a9d0b4d8efd53b29e62`.

### Reproduction / verification

Use `.venv/Scripts/python.exe scripts/run_current_test_suite.py`.

### Limitations

This is a current code-test pass, not threshold certification or publication
authorization. The environment is machine-local; its manifest is portable.

### Supersedes / Superseded by

Supersedes EVID-0012's environment-blocked observation.

## EVID-0017 - Experimental whole-segment support enclosure

Date: 2026-08-30

Status: HISTORICAL EXPERIMENTAL FOUNDATION, SUPERSEDED NUMERICAL BACKEND

Scope: Foundation for prospective C4-Gram segment certification.

### Claim

Outward-expanded value intervals and derivative bounds now propagate through
affine/ReLU, softmax, sigmoid/log-VA, GS unit-RMS gauge, physical energy
normalization, and analytic coherent overlaps. Synthetic no-crossing and
known-crossing cases behave correctly, and all 12 realized endpoint changes
are enclosed. However, 0/12 realized paths has a support certificate because
a validated initial Gram/Hermitian eigensystem enclosure `eta_num` is absent.

### Evidence

- `results/whole_segment_support_enclosure_validation.json`, SHA-256
  `6e26ce424d96eb0fa1d99d6749d7e743dc27b69e8cabb13a71a9b8de840879ec`
- Bound/observed endpoint ratios: 7.97955 to 52.60276.
- Finite-node threshold gaps, diagnostic only: `8.0414e-14` to
  `8.2549e-14`.
- Known crossing rejected with 768 unresolved subintervals; obvious
  no-crossing synthetic case certified.

### Provenance

Producer SHA-256:
`cee8b09d474aabf2597d4f7d99854eefde70d4f7b4d059be4125301cefecf936`.
Module SHA-256:
`045b3220292bde6c5f44faea02339bac216cd645e10ae8e23e956e0076e5fd39`.
Config SHA-256:
`9fab65a89e9083196c9505fbc24b8489c043bfbb3c09bf0fdb3cd67593401237`.

### Reproduction / verification

Run `scripts/validate_whole_segment_support_enclosure.py` in the locked
environment and validate the artifact against its schema.

### Limitations

`numpy.nextafter` expansion is not a formally validated directed-rounding
eigensolver. No verified Gram assembly/inertia bound exists, and the logic is
not integrated into transactional Adam acceptance with optimizer/RNG rollback.
Finite-node ranks are diagnostics, not proofs.

### Supersedes / Superseded by

Superseded for validated-arithmetic status by EVID-0021 and for current
realized-path outcome by EVID-0022. Its derivative-bound diagnostic remains
historical evidence only.

## EVID-0018 - Regenerated boundary diagnostic with complete provenance

Date: 2026-08-30

Status: ACTIVE DIAGNOSTIC, NOT FROZEN

Scope: Proposed-threshold boundary characterization only.

### Claim

The corrected producer regenerated the boundary/CRN diagnostic with complete
source, config, roster, environment, schema, precision, and lifecycle
provenance. The old artifact remains quarantined. The bad-state boundary is
centered at `0.002889168901951052` with final width
`6.984920454533583e-13`, separating retained ranks 14 and 15. Rollback accepts
0/50, 5/50, and 50/50 proposals at the three predeclared starting offsets.

### Evidence

- `results/support_boundary_bisection_crn_regenerated.json`, SHA-256
  `a1d780dc76e251662cadbe99e6f8277e7b59a75d13590b85527beda83fc0af67`
- Runtime: 209.567 seconds.
- Candidate threshold under evaluation: `1e-13`.

### Provenance

Producer SHA-256:
`c1042faccf809b665e1fd2ba1b02e33a5c638f2520bf70aa290248e1a180977c`.
Schema SHA-256:
`f85990620cdc5a50ff5469dd7426ee9c8b4357179e47eb1bc0159461d0e02f06`.
Roster and environment hashes match EVID-0015 and EVID-0016.

### Reproduction / verification

Run the corrected producer in the locked environment and validate all embedded
dependency hashes against current files.

### Limitations

Bisection and finite-node CRN evidence do not prove continuous-segment support
stability and do not approve the candidate threshold.

### Supersedes / Superseded by

Supersedes only the provenance defect of the quarantined boundary payload.

## EVID-0019 - Four-fixture independent full-support Gram oracle

Date: 2026-08-30

Status: ACTIVE NUMERICAL ORACLE, NOT THRESHOLD APPROVAL

Scope: Predeclared independent high-precision subset.

### Claim

All four predeclared oracle fixtures resolve mathematical rank 256 at two
successive precisions and converge below `1e-10`. Uniform and Binomial require
600/800 digits; the two near-coincident fixtures require 1250/1450 digits.
Maximum successive full-support differences range from about `3.12e-361` to
the largest value, `2.39e-256`.

### Evidence

- Final artifact `results/independent_confirmation_gram_oracles.json`,
  SHA-256
  `b566049ec70588e6112c4d3d327b8af6e60d81c4a04f47f41444ac54490c61b6`
- Frozen incomplete precursor, SHA-256
  `26442175e622d304b35b4ff9cef077310eca67d614fa550f469199d5ae7d5b8d`
- Final smallest positive eigenvalues: uniform `3.17025e-573`, Binomial
  `3.76132e-380`, phase-step `5e-8` `2.02444e-1137`, and phase-step
  `2e-7` `1.46509e-1061`.

### Provenance

Producer SHA-256:
`287da3958450fb411be7280a34fbe94231c4e7c623abce24f217fb843d8b2d8f`.
Config SHA-256:
`1afa75778205bb624b628fc74f51d354d9426931b006162e1e119ac086d6e9c2`.
Schema SHA-256:
`f9c04f8c16a712ea1dd23ae43622771b3e446db1a2c3cc5ca8d10b070123b123`.

### Reproduction / verification

Run `scripts/oracle_independent_confirmation_gram.py` with the frozen roster
and precision schedule. The analytic weighted coherent-state Gram/operator
chain is independent of Fock cutoff and float64 threshold selection.

### Limitations

The regular-fixture precision extension was frozen for rank resolution only;
it did not inspect candidate-threshold observables. Included raw K uses the
certified `N_MC=2048` estimator on certification-only states, not final test.
This oracle does not supply a verified float64 whole-segment enclosure or
approve any support threshold.

### Supersedes / Superseded by

Extends EVID-0005 from one stress fixture to four prospectively selected
fixtures.

## EVID-0020 - Repository checkpoint reconstruction

Date: 2026-08-31

Status: ACTIVE REPOSITORY-STATE EVIDENCE

Scope: Phase-0 portability/checkpoint audit only.

### Claim

At task start, branch `feat/pre-scale-run` was clean at commit
`8daba301cdcb7cc3737323454e6507094848f788`. That commit already tracks the
19-payload independent-confirmation foundation declared by the then-current
manifest. There was no staged 44-path foundation set to commit, so no second
or misleading checkpoint commit was created.

### Evidence

- `git status --short --branch`: clean at task start.
- `git diff --cached --stat` and `git diff --cached`: empty at task start.
- Commit `8daba301...`, message `feat: pre scale + history implement`.
- All 19 former manifest payloads are tracked at that commit.

### Limitations

The commit is broader than a certification-foundation-only commit. The frozen
roster and completed oracle first enter Git history together, so Git history
alone cannot prove prospective ordering. New Arb artifacts added by this task
are present in the worktree portability manifest but are not claimed to be in
the pre-task commit.

### Subsequent checkpoint verification (2026-08-31)

Commit `34c5eaa632cf7425fb844f82a4d02d3f29d4e6a3` subsequently committed exactly
the 22-path failed Arb-cycle/state set from the clean parent. Its message is
`feat: get the real difference to 0 so dont update more`, not the suggested
historical-checkpoint message, but the tree content preserves the prior 0/12
artifact and portable inputs. The threshold-shifted-inertia task started from
a clean index and worktree at this commit; no redundant checkpoint or history
rewrite was performed.

## EVID-0021 - Isolated Arb certification backend and exact path fixtures

Date: 2026-08-31

Status: ACTIVE EXPERIMENTAL NUMERICAL FOUNDATION, NOT THRESHOLD APPROVAL

Scope: Certification-only validated arithmetic and regression evidence.

### Claim

An isolated python-flint backend now propagates Arb/acb balls through the exact
binary64 PS, bounded log-VA, GS unit-RMS gauge, energy normalization, and C4
weighted coherent-state Gram path. The certification environment contains
python-flint 0.9.0 / FLINT 3.6.0 and uses a separate hash-pinned lock. Eleven
requested certification regression classes pass in that environment.

### Evidence

- `results/certification_flint_environment.json`, SHA-256
  `47f6c51f9c76be1ec7cd7411bb3c638dd6d117c4d592ec25de1c988b60db745b`.
- `results/rigorous_segment_fixture_bundle.json`, SHA-256
  `1a29b45266c4fa3f0dd8a3773c31665dd49679c64466835a9a92a8b767dd2149`.
- `requirements-certification-flint.lock`.
- `src/validation/rigorous_flint_support.py`.
- `docs/RIGOROUS_ARB_CERTIFICATION.md`.
- Isolated command `python -m unittest -v tests.test_rigorous_flint_support`:
  `CURRENTLY_VERIFIED_PASS`, 11/11, 0 failures, runtime 0.935 seconds.
- Production command `python -m unittest discover -s tests -v`:
  `CURRENTLY_VERIFIED_PASS`, 135 discovered: 124 passed and 11
  certification-only skips, runtime 8.761 seconds.

### Method and limitations

Every float endpoint is reconstructed as its exact IEEE-754 dyadic. Ambiguous
ReLU states use the full interval hull. Sector perturbation radii use rigorous
Frobenius upper bounds, and `algorithm=approx` is forbidden. This establishes
an inclusion-producing arithmetic path, not an approved threshold, a uniform
continuous-domain theorem, or optimizer integration.

## EVID-0022 - Realized Arb whole-segment attempt fails closed at endpoint spectra

Date: 2026-08-31

Status: ACTIVE EXPERIMENTAL FAIL-CLOSED RESULT

Scope: Three certification-only channel states times PS/GS/VA/mixed paths.

### Claim

The standalone certifier evaluated all 12 preregistered realized paths under
the prospectively fixed 160/256/384-bit schedule and work limits. It certified
0/12, proved 0 crossings, and left 12/12 unresolved. Each path stopped before
subdivision because the validated FLINT eigensolver could not isolate the
start or end C4-sector spectra at any scheduled precision, despite
`multiple=True`. No unresolved result was promoted to pass.

### Evidence

- `results/rigorous_whole_segment_certification.json`, SHA-256
  `0b09b2d11c1c645fce882cb5d7403161d98973043bb6dce6a9257c3aa0360cd6`.
- Aggregate: 12 segments; 0 certified; 0 rigorous crossings; 12 unresolved;
  maximum subdivision depth 0; runtime 1061.9827932000626 seconds.
- Each endpoint records failed validated isolation at 160, 256, and 384 bits.
- Synthetic regressions: obvious no crossing passes, known crossing is
  rigorously identified, near-boundary non-crossing passes.

### Limitations

The result does not establish a threshold-relative endpoint rank or a
whole-segment support certificate. Because endpoint isolation failed, realized
Weyl leaves, certified spectral margins, and interval-depth statistics beyond
depth zero do not exist. No realized interval was entered, so realized
perturbation-radius/observed-endpoint-change ratios are unavailable rather
than inferred. The next proof method must count eigenvalues relative to the
threshold without requiring isolation of every extremely clustered
eigenvalue, for example validated Hermitian inertia. Candidate `1e-13`
remains proposed/unapproved and configured `1e-12` remains invalid/unapproved.

## EVID-0023 - Threshold-shifted block-LDL* certifies all realized endpoints

Date: 2026-08-31

Status: ACTIVE EXPERIMENTAL POINT CERTIFICATION, NOT THRESHOLD APPROVAL

For Hermitian `G`, numerical support above proposed `tau` equals the positive
inertia of `G - tau I`. A validated Arb/acb 1x1/2x2 block-LDL* recursion
certified 24/24 endpoint rows (15 unique points), with zero unresolved endpoint
dimensions and support count 13 at both ends of every realized path. All used
160 bits; the minimum signed pivot/block margin was
`8.628156120464208e-14`; runtime was `63.32869829982519` seconds.

Evidence: `results/shifted_inertia_environment_v1.json` SHA-256
`053e6bf516729f44a960ae8e5c433d9531690257ebd878945d51c21ac49d6b61`
and `results/shifted_inertia_endpoint_certification_v1.json` SHA-256
`45b509a94ac94ae92f7c9c03d67465d068d426dcb4da10777e613ab3f0152b5d`.
The isolated certification suite passed 32/32; the production suite discovered
156 tests, with 124 passes and 32 certification-only skips.

Strictly signed scalar pivots and determinant/trace-certified Hermitian 2x2
blocks are eliminated by validated Schur complements; Sylvester inertia
additivity supplies the proof. Floating-point pivot quality selects only among
already certified candidates. Endpoint equality is not a whole-segment proof.
The config/result chronology is hash-bound and supported by file creation
order, but was not committed before execution, so Git history alone does not
prove preregistration.

## EVID-0024 - Direct interval guard-band inertia remains unresolved on 12/12 paths

Date: 2026-08-31

Status: ACTIVE EXPERIMENTAL FAIL-CLOSED RESULT; V1 NOT ACCEPTABLE FOR A PASS

The endpoint gate permitted a deterministic whole-segment attempt, but direct
Arb interval propagation, midpoint Frobenius guard bands, and dyadic
subdivision certified 0/12 paths, proved 0/12 crossings, and left 12/12
fail-closed. No zero-containing enclosure or guard-count disagreement was
promoted to a crossing.

Evidence: `results/shifted_inertia_whole_segment_certification_v1.json`,
SHA-256 `07d61fe810691f7276fc61005224d405a5ab794f380353e0d9386cc8912a6635`.
Median/max depth was 13/20 and median/max precision was 512/512 bits. There
were 299 attempted nodes, 260 resource-limit leaves, and zero accepted leaves.
Final available lower/upper guard counts differed by 61--63 modes (median 62),
with observed interval Frobenius radii about `1.668e-10` to `1.352e-2`.
Runtime was `12302.942093300167` seconds (`3.4175` hours), `11.5849x` the
previous `1061.9827932000626`-second 0/12 cycle. Good/VA alone recorded
`7425.47932009981` seconds because work-limit checks are cooperative;
good/mixed was not started after the total limit.

Adversarial review found that V1 records but does not enforce the frozen
fixture-bundle and environment hashes, so a hypothetical V1 pass could not be
accepted automatically. Its generic endpoint-rank-difference crossing branch
also lacks a prior whole-path domain/continuity proof; that branch was dormant
because current endpoints all had equal counts. Unresolved dimensions must be
reported by guard-count gaps and unattempted sectors, not only by
`n_zero_or_unresolved`, which can be zero when two certified guard counts
differ. These defects do not create a false pass in this 0/12 artifact, but a
new producer version is mandatory before future acceptance.

## EVID-0025 - Oracle fixtures confirm point machinery and rank/support distinction

Date: 2026-08-31

Status: ACTIVE DIAGNOSTIC CROSS-CHECK, NOT INDEPENDENT THRESHOLD-SUPPORT ORACLE

The validated point routine certified proposed-threshold supports 17, 29, 7,
and 8 for the four frozen oracle fixtures, all at 160 bits and matching
complex128 diagnostics. All four fixtures independently have mathematical
rank 256 at two high-precision settings. This confirms that mathematical rank
and threshold-dependent numerical support are distinct.

Evidence: `results/shifted_inertia_oracle_crosscheck_v1.json`, SHA-256
`d03ee8b33f7ad308a2f8e05aa22058341f7abb5adb4a58775c8eafcb0d9c24e5`;
4/4 point certificates and rank-256 fixtures; runtime
`14.061144800158218` seconds.

The high-precision artifact stores rank/extreme-eigenvalue evidence, not full
eigenvalue lists or independent counts above exact binary64 `tau`. Therefore
17/29/7/8 are validated Arb point results corroborated by complex128, not an
independent high-precision threshold-support confirmation. The two
near-coincident fixtures lack prior candidate-count rows. Such a claim would
require high-precision counts above exact `tau` or validated threshold-gap
isolation.

## EVID-0026 - Exact-dyadic oracle independently certifies support and nearest gaps

Date: 2026-09-01

Status: ACTIVE VALIDATED POINT EVIDENCE, NOT THRESHOLD APPROVAL

The hash-frozen V2.2 oracle reconstructed the four roster fixtures from exact
binary64 dyadics. Arbitrary-precision mpmath spectra proposed dyadic brackets
only. Arb/acb shifted block-LDL* inertia independently proved support counts
above exact `0x1.c25c268497682p-44`, the counts below it, and one-eigenvalue
brackets immediately on both sides.

The certified above/below/unresolved counts are respectively:

- Uniform high-VA: `17 / 239 / 0`;
- Binomial high-VA: `29 / 227 / 0`;
- near-coincident `5e-8`: `7 / 249 / 0`;
- near-coincident `2e-7`: `8 / 248 / 0`.

All exact-threshold inertias passed at 160 bits. Certified lower bounds on the
distance from `tau` to the closest eigenvalues below/above are approximately
`5.5224e-14 / 4.5299e-13`, `6.5291e-14 / 3.1807e-14`,
`5.3588e-14 / 5.9219e-14`, and `9.9999999968e-14 / 6.4259e-13`.
The scientific runtime was `694.6966014998034` seconds; the outer worker
completed before its 3600-second hard deadline.

Evidence:

- `results/exact_tau_oracle_v2_2.json`, SHA-256
  `57da0dfc9bb040774f053498935b692f99360c254cd7c700619a707be17e1bda`;
- `results/exact_tau_oracle_v2_2_watchdog.json`, SHA-256
  `1b7279a1f5c102a9bd99216af3fc6acabd8d0cb6f10b95783f9cda0f923af259`;
- V2.2 freeze manifest SHA-256
  `2bd9f865ebe0f191ec5b5e1e5df8b4e628c24afb0e13d1fd3d050600d8fdd08e`.

The initial V2 producer failure and V2.1 partial result are preserved. V2
failed before scientific output because it called nonexistent
`mpmath.eigvalsh`. V2.1 rigorously certified the same four counts but failed
nearest-gap brackets because bracket-center arithmetic fell back to 15-digit
mpmath precision. Both defects received new code/config/manifest revisions
and regression tests before re-execution; neither `tau` nor numerical limits
changed.

## EVID-0027 - Taylor/eigencluster feasibility gate fails closed under hard budgets

Date: 2026-09-01

Status: ACTIVE EXPERIMENTAL FAIL-CLOSED RESULT; FULL 12-PATH RUN PROHIBITED

The prospectively selected SHA-ranked subset was `medium/ps`, `good/gs`,
`medium/va`, and `medium/mixed`. The V2.3 parent verified the frozen bindings,
the live FLINT environment, and the certified exact-tau oracle before starting
segment work. The frozen gate failed:

- whole segments certified: `0/4`;
- proven crossings: `0/4`;
- resource-limit rows: `4/4`;
- provenance failures: `0/4`;
- accepted segment artifacts/path-domain rows: `0/4`;
- total parent runtime: `1800.0382972999942` seconds.

Three workers wrote durable checkpoints before termination. Medium/PS and
good/GS completed four nodes and reached depth 3; medium/VA completed three
nodes and reached depth 2. Their last node used 512 bits, exhausted the fixed
cluster cap 24, and failed to certify the combined far block. Last-node Taylor
Frobenius radii were `4.1878038679e-5`, `1.6073560576e-6`, and
`2.0905619381e-5`, with about 89--92 seconds per completed node. No mixed-path
worker was started after the total budget was exhausted.

The checkpoints can exist only after the worker's path-domain routine returned
`PATH_DOMAIN_CERTIFIED`, but the worker did not durably journal that result
before node evaluation. Because killed workers produced no final segment row,
the aggregate correctly reports zero accepted machine-readable path-domain
certificates. This control-flow implication is diagnostic, not a substitute
for the required persistent Phase-3 artifact.

The hard-timeout implementation also failed its strict acceptance contract:
medium/PS recorded `1004.2271167999133` seconds against a 450-second segment
limit. On Windows, terminating the immediate Python process did not bound the
post-termination wait; the exact process-tree/pipe cause was not independently
traced. Good/GS recorded 450.012 seconds and medium/VA received only 345.791
seconds from the remaining total budget.

Evidence:

- `results/taylor_eigencluster_feasibility_v2_3.json`, SHA-256
  `b7430af4831d96a7b94d88383aab3a64190aecf4ad50099bc3e6a8901921fd1d`;
- versioned checkpoint/watchdog files under
  `results/taylor_eigencluster_feasibility_v2_3_work/`;
- config SHA-256
  `a3ee9c1afcfb35b4422265057ef2635fd61479317af9b47bae725c7df9b68406`;
- V2.3 freeze-manifest SHA-256
  `57e3f7692fcd86c8f31ce70daf7b82a2a8dfa757064a3c44a3be6e6eb426fb1b`.

V2 validates common scalar-path Taylor propagation through the actual
transmitter and C4 Gram construction, but then collapses cross-entry Taylor
correlation to independent matrix balls before fixed-basis congruence/Schur
work. The observed radii remain many orders of magnitude larger than `tau`.
Rounded-Q nonsingularity did certify, with Frobenius defects about
`9.48e-15`--`1.13e-14`, but each last far block certified only 2 positive
modes and left 38/40 dimensions unresolved; no Schur solve was reached. The
quantitative gate failed every acceptance check, so no all-12 V2 cycle ran.

## EVID-0028 - V3 coefficient-congruence feasibility fails the decisive gate

Date: 2026-09-01

Status: ACTIVE EXPERIMENTAL FAIL-CLOSED RESULT; CURRENT HARD-SUPPORT METHOD STOPPED

V3 was frozen in two prospective phases. Source, numerical rules, the new
selection namespace, schemas, and tests were committed at
`b0ff03b963a50219bcee3439fd9175a9891e39a3`. The preselection manifest was
then committed before fixture IDs were resolved. Its SHA-256 is
`660ea716bc05b933d5b4b342c0fd8b1a5aa9584f3bdc41a93c77577664c210b5`.
Only afterward did the outcome-blind resolver select `bad/ps`, `bad/gs`,
`bad/va`, and `bad/mixed` under namespace
`whole-segment-v3-feasibility`; the selection artifact SHA-256 is
`1ea89229c267c395842757bdee2793d4acfd44946266d9b1b41162c347bdf8ba`.
The final execution manifest SHA-256 is
`5057cbd443c1d5aa37206fd282a8de949559b03ed39ba41e88c3cb5c898b202b`.

The complete repository suite passed 259 tests before execution. The frozen
20-case synthetic preflight passed 20/20; its real Windows descendant-tree
timeout had 0.0012818-second overshoot. The preflight artifact SHA-256 is
`81fe173259071b3124d13da13cd7618564e566e32c7cba7a4a9ea300acb87b50`.

The realized feasibility result failed closed:

- complete fixed-inertia segments: `0/4`;
- proven crossings: `0/4`;
- resource-limit rows: `4/4`;
- path-domain certificates persisted: `4/4`;
- attempted/completed nodes reconstructed from journals: `7/3`;
- successful Schur eliminations durably recorded: `52`;
- total runtime: `2438.1743897000006 s` against the frozen `1800 s` limit.

| Segment | Limit (s) | Return (s) | Overshoot (s) | Nodes attempted/completed | Schur events |
|---|---:|---:|---:|---:|---:|
| bad/ps | 420.000 | 420.002312 | 0.002312 | 2/1 | 14 |
| bad/gs | 420.000 | 420.001134 | 0.001134 | 2/1 | 24 |
| bad/va | 420.000 | 751.528187 | 331.528187 | 2/1 | 14 |
| bad/mixed | 207.136480 | 844.915756 | 637.779276 | 1/0 | 0 |

All four Job records eventually report zero active processes and complete tree
termination. The first two met the frozen two-second return bound. The latter
two are `WATCHDOG_CONTRACT_BREACH`: Job termination did not bound parent
return. The implementation calls `TerminateJobObject` synchronously; the
artifact does not independently locate where the long return was spent, so a
blocking termination call under active native computation is a source-
supported hypothesis, not a proven operating-system cause.

The three completed root nodes all stopped in C4 sector 0 at 512 bits with
`RESIDUAL_INERTIA_UNCERTIFIED`. Their true-near cluster stayed exactly eight.
Coefficient-level congruence reduced the paired root enclosure radius to
`0.0265262`, `0.0264878`, and `0.0231441` of the entrywise-then-congruence
radius. Sequential Schur reduction executed 2, 3, and 2 successful
eliminations in those completed nodes. Nevertheless, terminal unresolved far
counts were `53,52,53` (median 53 versus V2.3's representative 38), and final
reduced dimensions were `61,60,61` (median 61 versus V2.3's approximately
62). Dependency tightening worked, but did not make the proof practical.

All path artifacts were committed before spectral work. Their critical lower
bounds include orbit mass at least `0.0155679464`, positive VA-to-bound
margins at least `0.521169873` and `3.378347420`, raw GS gauge energy at least
`1.4166666559`, physical normalization energy at least `0.996348573`, and
physical scale at least `0.557314046`; every coherent amplitude was finite.

Evidence:

- `results/taylor_eigencluster_feasibility_v3.json`, SHA-256
  `5427c6828254f79deb954f096122a26dc8ae2038c686adca42513378ed567483`;
- hash-chained journals, path-domain artifacts, and watchdog records under
  `results/taylor_eigencluster_feasibility_v3_work/`;
- config SHA-256
  `878a17f51734e2c1565276b5ee13d8a0cf2b7bfedfab5f6a7749409b0ee57a20`;
- V3 environment artifact SHA-256
  `75ecb123dff9b9df94c7cb0b2a2f9f4a258007e637b8e35417756933704ca6a1`.

The full 12-segment run is prohibited. Candidate `1e-13` remains proposed and
unapproved. No V4 is authorized automatically.

## EVID-0029 - Provenance reconciliation and method-review authorization

Date: 2026-09-01

Status: ACTIVE REPOSITORY-STATE EVIDENCE; POINTWISE DESIGN ONLY

### Claim

The frozen-model and reported certification provenance mismatches were audited
at the byte level. Every mismatch was CRLF/LF normalization only; canonical
UTF-8 LF bytes matched the historical recorded digests and semantic payloads
were unchanged. Explicit `eol=lf` attributes now cover the frozen model,
current hash-bound source/config/schema files, the MB dependency-blocker
payload, and the V3 text chain. The historical portability manifest remains
unchanged and a new current V3 manifest is authoritative for EVID-0026--0028.

The read-only numerical/security review concluded that whole-segment support
invariance is an additional condition for differentiability through the hard
support operation, not a prerequisite for the adopted statewise security
functional at a validated realized point. Existing pointwise support/gap and
local-gradient evidence is finite and diagnostic. A prospective transactional
pointwise guard may therefore be designed without changing the physical model,
MI functional, Holevo functional, or SKR evaluator. It may only restrict the
optimization domain and remains subject to a future threshold/protocol freeze.

### Evidence

- `results/provenance_reconciliation_v1.json`, SHA-256
  `5e50caf7171e88d2455eeaf10847804bb1b211cbeb679c65536633dad8c6e70f`
- `docs/CERTIFICATION_ARTIFACT_MANIFEST_CURRENT.json`, SHA-256
  `4de0b1cddbb3533b93c3e8b80b88667b921a37ff2852a0cc34a6eb36b01493b3`
- `.gitattributes`
- `tests/test_independent_confirmation_roster.py` (2/2 pass after policy fix)
- EVID-0026, EVID-0027, EVID-0028
- DEC-0018

### Provenance

Producer: repository byte-policy audit and deterministic hash checks.

Repository commit at audit: `e29d55850e7a6cf5c49f0917eb7ea96e167989ba`.

Current dynamic full-suite status: `BLOCKED_BY_ENVIRONMENT`; the locked
CPython 3.12.10 / torch 2.13.0+cpu environment is not installed locally.

### Limitations

This evidence authorizes implementation of the frozen design as the next task.
It does not approve `1e-13`, reactivate `1e-12`, certify whole segments,
authorize training/evaluation, or authorize publication-scale execution. The
security claim remains oracle-CSI, asymptotic, covariance-based DM-CV-QKD with
no attack class assigned to the fading average.

## EVID-0030 - Pointwise guard protocol design freeze

Date: 2026-09-01

Status: ACTIVE PROPOSED PROTOCOL; IMPLEMENTATION RECORDED IN EVID-0031

### Claim

The pointwise spectral guard protocol is prospectively frozen as a design
contract. Its certification unit is one unique realized statewise physical
ensemble, deduplicated by exact canonical hash; Monte Carlo noise samples and
intermediate optimizer interpolation points are excluded. The threshold is
parametric and remains unapproved. Validated shifted-Hermitian block-LDL*
inertia with nearest-eigenvalue brackets is required; raw complex128 distance
is not certification.

The guard accepts only when the certified lower distance
`min(tau-upper_below, lower_above-tau)` strictly exceeds twice the maximum
validated bracket half-width. Equality or insufficient margin rejects. The
four statuses are exactly `POINTWISE_ADMISSIBLE`,
`POINTWISE_GUARD_BAND_REJECT`, `POINTWISE_CERTIFICATION_FAILED`, and
`PROVENANCE_FAILURE`. Local gradients are permitted only after
`POINTWISE_ADMISSIBLE`. The transaction requires complete rollback equivalence
for model/optimizer/dual/RNG/generator state and does not prove any segment.

### Evidence

- `configs/pointwise_guard_protocol_v1.yaml`, SHA-256
  `54a0c46bfb1eab9e00c3e5320489f2c0de8a9fd7541363fed440c21d3d90c979`
- `schemas/pointwise_guard_protocol_v1.schema.json`, SHA-256
  `5950ee485526b69a1656402d8cb88f38408a63e20568f6673d7661446471bca2`
- `docs/POINTWISE_GUARD_PROTOCOL.md`, SHA-256
  `96fc8c251db8cb0967cf7c0d1cbd67d61f07633814db279a4fd3c261534d3cb8`
- `tests/test_pointwise_guard_protocol_design.py`, SHA-256
  `491fa2f1504c71ca68d5f95cb08f6ce3b30587aeae87a9a0aae55e121f040297`
- Design regression suite: `7/7` pass (`CURRENTLY_VERIFIED_PASS`).
- DEC-0019.

### Provenance

The protocol binds repository commit, canonical frozen-model hash, protocol
config/schema, point-certification producer, environment, confirmation roster,
trainer, and eventual rollback implementation. All lifecycle guards are false;
the prospective smoke test is `PROPOSED_NOT_RUN`.

### Limitations

This design does not approve `1e-13`, reactivate `1e-12`, change the security
functional, establish continuous-domain support, or authorize training,
baseline selection, final-test access, or smoke execution. Its implementation
is recorded separately in EVID-0031.

## EVID-0031 - Pointwise guard implementation scoped pass

Date: 2026-09-01

Status: ACTIVE IMPLEMENTATION EVIDENCE; SMOKE NEXT

### Claim

The frozen pointwise protocol is implemented in a small guard module and
integrated into the existing trainer. It performs exact final-ensemble hash
deduplication, injected validated-certifier/provenance checks, pre-update
rejection before backward, endpoint validation, deferred dual updates, and
complete rollback. No raw complex128 support fallback or interpolation proof
was added. The implementation matrix passed in the current environment; the
broader suite remains environment-blocked by missing pytest/locked runtime.

### Evidence

- `results/pointwise_guard_implementation_v1.json`, SHA-256
  `0c73104e4c5625b402f004aa5a8215093066756a13a631a12a4e217fbe27e144`
- `src/optimization/pointwise_guard.py`, SHA-256
  `12c887e6b1896d62b2aac28990463e650ac990c24df9469f74e13423e71971c8`
- `src/optimization/trainer.py`, SHA-256
  `42a2ca2e61fc3a0b1f54a759bd522603f92985af864fc792142f5eba9b5cfa37`
- `tests/test_pointwise_guard.py`: `8/8` pass (`CURRENTLY_VERIFIED_PASS`).
- Related scoped suite: `64/64` pass (`CURRENTLY_VERIFIED_PASS`).
- Full discovery: `BLOCKED_BY_ENVIRONMENT`.
- DEC-0020.

### Limitations

The production validated point-certifier adapter is injected and the threshold
remains unapproved. The six-step smoke test is frozen but was not run in this
task. No publication training, baseline selection, or test access is allowed.

## EVID-0032 - Pointwise smoke blocked by certification environment

Date: 2026-09-01

Status: BLOCKED_BY_ENVIRONMENT; NO SMOKE OUTCOME

### Claim

The frozen six-step pointwise-guard smoke test was not executed. The current
environment has Torch `2.8.0+cu128` and CUDA available but cannot import the
required validated Arb/python-flint backend. No repository smoke runner or
repository-backed `certify_point` adapter exists; the injected certifier used
by unit tests is not a scientific smoke substitute. Therefore no optimizer
update, certification check, rollback, or determinism metric was attempted.

### Evidence

- `results/pointwise_guard_smoke_v1.json`, SHA-256
  `4149cc220e41428382f5432255da09414e5de5e7d1eddce6ca2cd9e3ae78e825`
- `schemas/pointwise_guard_smoke_v1.schema.json`, SHA-256
  `62d18591ec493d99b894a81121b6775fdf391979b736e212a6c5fb3ab49395ea`
- `configs/pointwise_guard_protocol_v1.yaml`
- `src/optimization/pointwise_guard.py`
- `DEC-0021`

### Limitations

This is an execution blocker, not a usability result. No threshold was
approved and no scientific/security functional changed. The next action is to
restore the hash-pinned certification environment and provide a validated
repository-backed point adapter before rerunning the same frozen smoke.

## EVID-0033 - Certification environment restore blocked

Date: 2026-09-01

Status: BLOCKED_BY_ENVIRONMENT; ADAPTER NOT STARTED

### Claim

The required certification environment could not be restored on this machine.
The repository lock requires CPython 3.12.10, python-flint 0.9.0/FLINT 3.6.0,
PyYAML 6.0.3, and Windows x86-64. Only CPython 3.13.7 is installed; the
Python 3.12 launcher/interpreter, repository-local certification virtual
environments, and `python-flint` import are absent. Dependency pins were not
changed. The validated adapter and smoke runner were therefore not attempted.

### Evidence

- `results/certification_environment_restore_v1.json`, SHA-256
  `1fd40556a71790d06e087126b3802143d657bb6aca19431776e50ce293dc1557`
- `schemas/certification_environment_restore_v1.schema.json`, SHA-256
  `555b87ef24c4d9781b8956bc9a8ffa06d7ec25fc2860b76a81916a7609abcae0`
- `requirements-certification-inertia.lock`, SHA-256
  `dd03ee6c033b268c6aba1d2e589a5f408e7f872bbd8d8a33d3bec9f77ec4b607`
- `requirements-certification-flint.lock`, SHA-256
  `cfc1bab0f88ec71776fd4430be0f81d0aae3acf5b7fe9f143b796c5853080450`
- EVID-0032
- DEC-0021

### Limitations

No smoke outcome, adapter result, or optimization-usability decision exists.
The exact frozen smoke remains unrun and the original blocked smoke artifact
is preserved.

## EVID-0034 - Hash-pinned certification environment restored

Date: 2026-09-01

Status: CURRENTLY_VERIFIED_PASS; ADAPTER NOT STARTED

### Claim

The exact repository certification environment was restored in `.venv-cert`
using CPython 3.12.10 and only the hash-pinned certification dependencies.
Verified versions are python-flint 0.9.0, bundled FLINT 3.6.0, PyYAML 6.0.3,
and NumPy 2.5.2 on Windows x86-64. The environment identity matches the
repository lock and frozen model hash. The real Arb/acb point-certification
regressions and shifted-inertia point/segment unit tests pass 32/32.

### Evidence

- `results/certification_environment_restore_v2.json`, SHA-256
  `0a3849805e5795547aa65302794404f128df712de9fee4bac29de7aaa2ec01cd`
- `requirements-certification-inertia.lock`, SHA-256
  `dd03ee6c033b268c6aba1d2e589a5f408e7f872bbd8d8a33d3bec9f77ec4b607`
- `scripts/capture_taylor_eigencluster_environment_v3.py`
- `.venv-cert\\Scripts\\python.exe -m unittest -v tests.test_rigorous_flint_support`:
  `CURRENTLY_VERIFIED_PASS`, 11/11.
- `.venv-cert\\Scripts\\python.exe -m unittest -v tests.test_rigorous_shifted_inertia tests.test_rigorous_shifted_inertia_segment`:
  `CURRENTLY_VERIFIED_PASS`, 21/21.

### Limitations

This verifies only the certification environment and existing numerical
preflight. No pointwise adapter or smoke runner was implemented, and the
frozen smoke remains unrun.

## EVID-0035 - Real point-certifier adapter verified

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; REAL BACKEND

### Claim

The production final physical ensemble now crosses an explicit subprocess
boundary into the restored `.venv-cert` Arb/FLINT runtime. All 256
probabilities and complex amplitudes are serialized as exact binary64
`float.hex` values in canonical JSON. The worker reconstructs C4 sectors
without centering, clipping, reordering, or renormalization and uses validated
Arb eigenvalue balls or shifted-Hermitian inertia for proof decisions. NumPy
complex128 values may seed bracket candidates only and never establish support
or admissibility.

Uniform and Binomial historical fixtures reproduce support counts 17 and 29;
a near-coincident fixture executes the real backend and returns only certified
or explicit fail-closed output. Exact production probability/amplitude
round-trip tests pass.

### Evidence

- `results/pointwise_certifier_adapter_v1.json`, SHA-256
  `03cf353c27bdd10e572ec52a727c16f7596a8f152962b63670859a190c304ed5`
- adapter commit `1f172be1bbfa3189d5e4e39e6330e38daf397a2e`
- pointwise runtime/adapter tests: `12/12` (`CURRENTLY_VERIFIED_PASS`)
- real Arb/shifted-inertia suite: `32/32` (`CURRENTLY_VERIFIED_PASS`)

### Limitations

No smoke outcome was consumed. The threshold remains proposed/unapproved and
the adapter does not change the production security functional.

## EVID-0036 - Frozen pointwise smoke runner and execution manifest

Date: 2026-09-02

Status: PROSPECTIVE_FROZEN_BEFORE_SMOKE_OUTCOMES; EXECUTION NOT RUN

### Claim

The minimal no-override runner reads the committed pointwise protocol and
representative-state roster, uses the production transactional trainer plus
the real subprocess adapter, and writes the required two-repetition trace. A
prospective execution manifest binds the stable adapter commit, runner,
worker, certifier, trainer, schemas, protocol, restored environment, lock,
roster, default config, and frozen model before execution. The runner was not
invoked.

### Evidence

- `configs/pointwise_guard_execution_manifest_v1.json`, SHA-256
  `03273a5dc6b58669853d7d7bac2078312e0276b78924ca502273e8a643723006`
- initial runner freeze commit `dfc655b7313c6e1dcd860bd3f82c4f0b64b0cb10`; final runner source hash is bound in the manifest
- runner freeze tests: `2/2` (`CURRENTLY_VERIFIED_PASS`)
- DEC-0023

### Limitations

The execution manifest authorizes only the already frozen six-step
certification-only smoke. It does not approve a threshold or publication-scale
execution.

## EVID-0037 - Completed V1 pointwise smoke is optimization-effectively-frozen

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; V1 OUTCOME PRESERVED

### Claim

The prospectively frozen V1 guard smoke completed under the real restored
Arb/FLINT adapter and the hash-bound execution manifest. Both six-step
repetitions are byte-identical after excluding only repetition and runtime.
All 12 steps rejected at the pre-update V1 guard, so no backward pass,
proposal, rollback, or commit occurred. All three unique realized ensembles
returned `CERTIFIED_POINT` support count 13; the batch status was always
`POINTWISE_GUARD_BAND_REJECT` because the V1 certified margins did not exceed
the frozen `2 * uncertainty_upper` buffer.

Under the prospectively frozen V1 outcome rule, zero committed updates with
every rejection explained by a frozen guard status is
`OPTIMIZATION_EFFECTIVELY_FROZEN`. This is an outcome of V1, not permission to
retune or rerun it.

### Evidence

- `results/pointwise_guard_smoke_v2.json`, SHA-256
  `4a914944aecb09204187040e461e84cd67e34f4c254647eea8ece2e625854360`
- execution manifest SHA-256
  `03273a5dc6b58669853d7d7bac2078312e0276b78924ca502273e8a643723006`
- manifest file-binding mismatches: `0`
- trace hashes: two identical
  `a7daf2245e7624f63e487d5f32835bf28e04b05405f84c56296aaf55f0bdcebb`

### Limitations

The result tests only the fixed three-state, six-step, two-repetition smoke.
It does not approve `1e-13`, establish a continuous-domain theorem, or
authorize publication training. The earlier blocked
`results/pointwise_guard_smoke_v1.json` is also preserved.

## EVID-0038 - Prospective pointwise guard V2 methodology review

Date: 2026-09-02

Status: PROPOSED V2 FROZEN BEFORE IMPLEMENTATION; IMPLEMENTATION ONLY

### Claim

Arb eigenvalue balls rigorously enclose eigenvalues, and validated
inertia-count changes rigorously bracket the adjacent eigenvalue. However, the
current direct-eigenball path selects its alleged nearest balls by binary64
midpoint without proving interval order. Its selected ball is rigorous for an
eigenvalue, but the exported `nearest` label is not uniformly proved. Ordinary
float conversion also does not preserve a directed-outward endpoint contract.

When the inward-facing endpoints are rigorous, the quantity

`min(tau - max_i(U_i below tau), min_j(L_j above tau) - tau)`

already includes interval uncertainty and is a rigorous distance lower bound.
Strict positivity proves separation. The V1 `2 * uncertainty_upper` condition
therefore adds a second buffer; it is not required for support or distance
certification. The repository's 12/12 finite-difference evidence requires
fixed plus/minus support masks and three adjacent stable step pairs, but it
does not justify any Arb-width multiplier.

The proposed V2 rule is consequently:

`support_is_rigorously_certified AND certified_margin > 0`.

Any engineering margin is fixed at zero. V2 implementation must use global
inward-facing Arb endpoints or certified adjacent inertia brackets, decide
strict positivity before non-directed serialization, and fail closed.

### Evidence

- `results/pointwise_guard_v2_methodology_review.json`, SHA-256
  `dbf1b4dc369195f8ee94bd8870f3a6142a69bba7e3130f2a2d8822e699d5ad77`
- `configs/pointwise_guard_protocol_v2.yaml`, SHA-256
  `6eb21147336e4ca4c305abdf2532fe03eaa8e4bb570a4c8918bdb91638727845`
- `schemas/pointwise_guard_protocol_v2.schema.json`, SHA-256
  `2ec0b6e24929d4c0275e88da79b4a46e15a2787059d0c31d44efaa06ecf84f44`
- `docs/POINTWISE_GUARD_PROTOCOL_V2.md`, SHA-256
  `1bc1959b80b592227eaa671a4204a6dc3eec5110fe1064c03ecc88865c918a35`
- fixed-support gradient evidence:
  `results/production_gram_certification.json`, SHA-256
  `694e5237ccbbf2fe231361dd9ef05303cc72c8b215fa47e6bb40d5bf5c3685ab`

### Limitations

V2 is proposed and inactive. No V2 runtime, adapter, smoke execution,
threshold approval, security-functional change, or frozen-model change
occurred.

## EVID-0039 - V2 implementation and smoke manifest freeze

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; V2 SMOKE AUTHORIZED NOT RUN

### Claim

The V2 Arb-side strict-separation certificate, V2 guard mode, real worker
protocol, and no-override smoke runner pass the scoped implementation tests.
The V2 execution manifest is hash-bound to the tested source, protocol,
schemas, restored certification environment, roster, trainer, and frozen model.
The manifest authorizes only the later six-step, two-repetition smoke; that
smoke was not run in this task.

### Evidence

- `results/pointwise_guard_implementation_v2.json`, SHA-256
  `7c6c64ae34e7acdd3e7af5a586fd808e70c2476b4755e82b177d51128913dc01`
- `configs/pointwise_guard_execution_manifest_v2.json`, SHA-256
  `d27d7fd6be10121b4217e8cc72af88481e994acb89d30787cfa7c8c9b5e4f568`
- `scripts/run_pointwise_guard_smoke_v2.py`
- production scoped tests: `31/31` pass
- pinned Arb/FLINT tests: `34/34` pass
- V2 manifest binding mismatches: `0`

### Limitations

At the time of this pre-execution freeze, no V2 smoke outcome existed;
subsequent EVID-0040 records the completed outcome. Candidate `1e-13` remains
unapproved; publication training, baseline selection, optimized-MB search, and
final-test access remain unauthorized.

## EVID-0040 - Completed V2 pointwise guard smoke is optimization-usable

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; REAL BACKEND; V2 OUTCOME PRESERVED

### Claim

The authorized V2 smoke completed once under the frozen V2 execution manifest.
Both six-step repetitions are byte-identical after excluding only repetition
and runtime. All 12 steps attempted and committed an optimizer update. Every
pre-update and post-update pointwise check was `POINTWISE_ADMISSIBLE`; all 12
gradient-finite checks passed; there were zero rollbacks, rollback-equivalence
failures, certification failures, or provenance failures. The three unique
realized ensembles carried support count 13 and strictly positive Arb-certified
spectral margins.

The preregistered V2 usability criterion therefore passes:
`OPTIMIZATION_USABLE`.

### Evidence

- `results/pointwise_guard_smoke_v3.json`, SHA-256
  `321b6dc4fd28168878d84e511478c209379b6c0aa36da5d9e794092317ca36f6`
- `configs/pointwise_guard_execution_manifest_v2.json`, SHA-256
  `d27d7fd6be10121b4217e8cc72af88481e994acb89d30787cfa7c8c9b5e4f568`
- protocol config SHA-256
  `6eb21147336e4ca4c305abdf2532fe03eaa8e4bb570a4c8918bdb91638727845`
- trace hash, repeated twice:
  `63d8a4a860f62f4ab2e768fc88e1c97c256052acc528608d485cf829c613020f`
- attempts/commits/rollbacks: `12/12/0`
- pre/post admissibility: `12/12` and `12/12`
- finite gradients: `12/12`
- rollback-equivalence failures: `0`
- certification/provenance failures: `0/0`
- lifecycle guards: all `false`

### Limitations

This is a finite, three-state, six-step, two-repetition smoke result. It does
not approve `1e-13`, establish continuous-domain support stability, or
authorize publication-scale training. All V1 negative evidence remains
preserved, including the V1 guard-band rejection artifact.

## EVID-0041 - Threshold and numerical approval gate review

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; THRESHOLD APPROVAL BLOCKED

### Claim

The active production Holevo implementation is cutoff-independent C4 Gram, so
the `fock_cutoff` configuration label is stale as a production backend
dependency. The dense-Fock stress study did fail its frozen suffix and remains
preserved diagnostic evidence; it is not silently upgraded or deleted.

The active numerical blocker is the threshold-dependent C4-Gram support rule:
the `1e-14` versus `1e-13` support masks change on 12 fixtures, the production
formal support-identity gate is false, and the existing comparison was
outcome-informed. The `BLOCKED_NUMERICAL_DEPENDENCY` baseline-selection label
is downstream of this unresolved numerical decision.

Existing evidence satisfies the exact tau binding, environment/backend,
active C4-Gram implementation, high-precision stress oracle, finite
complex128/high-precision observable comparison, fixed-support gradient audit,
and V2 optimizer-usability gate. It is not sufficient to approve `1e-13` for
publication-scale experiments.

### Minimum required prospective validation

Authorize design only for a new outcome-independent finite validation protocol:
independent full-support arbitrary-precision Gram oracles for every declared
ill-conditioned production fixture, comparison of `C,w,Z`, symplectic
eigenvalues, `chi_BE`, and raw `K` against those oracles under the existing
frozen tolerances, and explicit author approval before changing threshold
status. No smoke, training, baseline selection, optimized-MB search, or test
access is authorized.

### Evidence

- `results/threshold_numerical_gate_review_v1.json`, SHA-256
  `3f75ddb9325ee8a15af2b05039232aec0d76088fff2b1e86a3ab3137b1d008de`
- `results/fock_convergence.json`, SHA-256
  `1ed980bf1bb033147f245c9a04dd0e3d0de55bf39260bb32563714dd4bfcd8dd`
- `results/near_coincident_gram_oracle.json`, SHA-256
  `2db2388d53052c228fcc0bd96b69d90803d3545da270619f390d03ed5b60b2d1`
- `results/production_gram_certification.json`, SHA-256
  `694e5237ccbbf2fe231361dd9ef05303cc72c8b215fa47e6bb40d5bf5c3685ab`
- `results/float64_gram_comparison.json`, SHA-256
  `e63abd39e944f4362df36620f4d74ce03afab121337f8d66cdf40981f898cdf6`
- `results/exact_tau_oracle_v2_2.json`, SHA-256
  `57da0dfc9bb040774f053498935b692f99360c254cd7c700619a707be17e1bda`
- `results/pointwise_guard_smoke_v3.json`, SHA-256
  `321b6dc4fd28168878d84e511478c209379b6c0aa36da5d9e794092317ca36f6`

### Limitations

`1e-13` remains `PROPOSED_UNAPPROVED`; `1e-12` remains
`INVALID_UNAPPROVED`. The active security claims and frozen model are
unchanged.

## EVID-0042 - Frozen 12-fixture prospective threshold validation

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; EXECUTION NOT RUN

The manifest binds the 12 production fixtures with observed support-mask
differences, their ensemble hashes, a full-support arbitrary-precision C4-Gram
oracle at 600/800 digits, production `tau=1e-13`, required observables, and
the existing moment/information tolerances. The oracle determines support from
full mathematical support and convergence only; it does not apply production
tau. The runner requires its explicit execution flag and was not invoked.

- Manifest: `configs/threshold_validation_execution_manifest_v1.json`, SHA-256
  `20002a34598afd2b0a9673bb73318601ec53bc89f4315503d9c7b74151b917b7`.
- Config SHA-256: `bb6425290286f02a849149eac5cc234babefd0fdcdd5c6cf17d7110beb8b95c7`.
- Frozen model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.

## EVID-0043 - Threshold fixture hash mismatch is a harness failure

Date: 2026-09-02

Status: CURRENTLY_VERIFIED_PASS; VALIDATION NOT RERUN

`untrained_full_initialization` deterministically reconstructs to frozen hash
`f7128dc210719de3942c4af8e2a47811d6994b746b06c1001dea542b39fbe8c4`
from the frozen production seed and three validation states. The failed harness
instead checked independent-roster hash
`55126c105b839e4ec6a13737abdc1886b128ba7d56958bbcd32cb6dbf984ce88`.
The correction passes the already-frozen production hash through the reusable
oracle harness. No threshold evaluation or scientific fixture change occurred.
Diagnosis artifact SHA-256:
`8e0c89a5e219d4df44295db7975e996a3c465d8f7561c6b7284513d5c18ab528`.
