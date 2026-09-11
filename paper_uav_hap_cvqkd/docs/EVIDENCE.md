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

### Current status note (2026-09-10)

EVID-0001 preserves the former implementation-spec hash as historical evidence.
The current edited specification hash and its documentation-only scope are
recorded in EVID-0054; old artifacts must not be reused as evidence for the new
target model.

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

## EVID-0044 - Full-support C4-Gram backend protocol freeze

Date: 2026-09-03

Status: CURRENTLY_VERIFIED_PASS; IMPLEMENTATION NOT RUN

The frozen protocol removes `tau` only from source-moment support selection,
retains all 256 mathematical C4-Gram modes, requires residual-norm `w`, and
freezes deterministic complex128-or-fallback routing. The fallback is exact
binary64 serialization to a 1050/1250/1450-digit arbitrary-precision C4
worker and is evaluation-only until an analytic VJP is independently validated.
All 12 threshold fixtures remain included.

- Freeze artifact: `results/full_support_c4_gram_backend_protocol_freeze_v1.json`.
- Freeze artifact SHA-256:
  `b422f97cad1a4873b6ba07d87098fd72850fb7a7ed0e1e9c23d8fea5e9f8ea4e`.
- Protocol config SHA-256:
  `9955b5d09e6219ba4b19b702bec3747a8d5a3b42de63d1af5d9e23c9575761d2`.

## EVID-0045 - Full-support C4-Gram evaluation backend implemented

Date: 2026-09-03

Status: CURRENTLY_VERIFIED_PASS; VALIDATION NOT RUN

The C4 source path now retains full mathematical support, has deterministic
complex128-or-arbitrary-precision routing, and rejects fallback gradients.
`tau` is diagnostic metadata only at this interface. Focused production tests
pass 5/5 and pinned Arb/FLINT tests pass 13/13. The 12-fixture validation is
frozen but was not invoked.

- Implementation artifact SHA-256:
  `53c8159629e81630b6948225baacbbf4fe1c89c140f01d44d53047495be2503c`.
- Validation manifest SHA-256:
  `194afcaccf0d1eeec250b25faadeb9b923baa19e7d225e536b1ae53268d88537`.

## EVID-0046 - Gradient/VJP validation protocol freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; PROTOCOL NOT EXECUTED

The fast-path-only analytic-VJP protocol is hash-bound to EVID-0029. It reuses
the frozen deterministic Full transmitter, representative states, CRN seed,
coordinates, finite-difference ladder, and derivative tolerance. Any fallback
route is an evaluation-only fail-closed result. No gradient implementation,
protocol execution, training, selection, threshold approval, or test access
occurred.

- Freeze artifact: `results/gradient_vjp_validation_protocol_freeze_v1.json`,
  SHA-256 `e4ce779092d837974a094b109f0de03fec434bd1382662f4df91fcd0ea149721`.

## EVID-0047 - Spectral Fréchet amendment freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; AMENDMENT NOT EXECUTED

EVID-0031 freezes a basis-invariant Fréchet/VJP definition for the positive
definite inverse square root used on the complex128 fast route. It resolves the
pre-certification repeated-eigenvalue definition blocker without changing the
security functional or EVID-0030's non-spectral settings. Synthetic derivative
preflights pass; no analytic VJP implementation or gradient certification ran.

- Freeze artifact: `results/gradient_vjp_spectral_frechet_amendment_freeze_v1.json`,
  SHA-256 `484e18f87ce10d9d0ecea82e829735a4eee65f4e7b69c724c42382823f98fb9d`.

## EVID-0048 - Analytic gradient/VJP implementation freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; CERTIFICATION NOT EXECUTED

The complex128 fast route now uses whole-matrix cluster-safe Loewner Fréchet
boundaries for Hermitian square root and inverse square root. C and residual-w
are expressed in the original sector bases, so native eigenvector backward is
absent from the differentiable graph. The no-override runner loads every probe,
CRN, step, and tolerance from EVID-0030 and fails closed on any non-fast route.
Thirty cheap tests pass. The AP fallback remains non-differentiable.

- Implementation artifact: `results/gradient_vjp_implementation_v1.json`,
  SHA-256 `23ee572c1644ad7dbd765d6cf31e2e599b9be4b8007115456944e5dc865fc84b`.
- Execution manifest SHA-256:
  `455eea2e195ed1509283314d8f7e60e578fc26240961f6c31689bc12019603cf`.

## EVID-0049 - Fast-route gradient/VJP feasibility amendment freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; AMENDMENT NOT EXECUTED

The frozen untrained Full center is a mathematical-full-support AP-only
evaluation fixture, with positive arbitrary-precision modes near `10^-675` but
negative complex128 roundoff-scale eigenvalues. EVID-0033 retains that fixture
without relaxing the fast gate and makes it gradient-ineligible. A separate
algebraic synthetic C4-sector preflight is frozen to validate only the
fast-domain Fréchet/VJP machinery. No gradient certification, training, or AP
differentiation occurred.

- Freeze artifact: `results/fast_route_gradient_vjp_feasibility_amendment_freeze_v1.json`,
  SHA-256 `7117ae0b7235c51df018bddb772bb461a3cb5084ee2dc9cb05555e3548f8354a`.

## EVID-0050 - Synthetic fast-route VJP harness freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; SYNTHETIC VALIDATION NOT EXECUTED

The separate algebraic 4-by-64-sector harness constructs the frozen HPD
synthetic fixture, verifies the existing fast gate, exercises Fréchet matrix
functions plus C/residual-w and bounded downstream preflights, and writes only
the dedicated future result artifact. It never substitutes the frozen Full
center, permits AP differentiation, or claims training validity.

- Harness artifact: `results/synthetic_fast_route_vjp_validation_harness_v1.json`,
  SHA-256 `866c1a76aee6e4dc5d0e09944b31f9f081b232c4660786d8f23b5e4f89bf6b8a`.
- Execution manifest SHA-256:
  `efd92b3f86344695b15cce59a543d30139deeafafb6ce00ebbb4c8dea452884e`.

## EVID-0051 - Synthetic fast-route VJP harness repair freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; V2 EXECUTION NOT RUN

The v1 synthetic validation failed before evaluation because the runner read
nonexistent tolerance keys. The failed v1 result is preserved unchanged. The
repaired runner reads the frozen `absolute_tolerance` and `relative_tolerance`
fields exactly, writes a separate v2 result path, and emits an explicit runtime
attempt fact. Lifecycle guard values remain pre-execution authorization state.

- Repair audit: `results/synthetic_fast_route_vjp_validation_repair_audit_v1.json`,
  SHA-256 `75363a93461f9c4359b3a58890e03427631bf27dad681a1f87ab2e409a97b932`.
- V2 execution manifest SHA-256:
  `a5c677d138de8da98b3e67ce4973044485aaa6ac31f7f2938a25b2df962edc22`.

## EVID-0052 - Manifold-consistent C/w VJP amendment freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; AMENDMENT NOT EXECUTED

The v2 synthetic failure is preserved as an invalid independent-sector
direction. Fixture A remains spectral-only. Fixture B now freezes a uniform
`p_0`, deterministic `z_k=k+1`, and radial `dz=z` prototype direction; all
four sectors are regenerated through the production mapping for every endpoint.
The center and both frozen-step endpoints pass all existing fast gates before
any VJP comparison. No production code or gate changed.

- Freeze artifact: `results/manifold_consistent_cw_vjp_validation_amendment_freeze_v1.json`,
  SHA-256 `77900c988d8898f950e14b17cab5184ed9f5a27b0ffc39a36b78ef684341d4af`.

## EVID-0053 - Manifold-consistent synthetic VJP harness freeze

Date: 2026-09-04

Status: CURRENTLY_VERIFIED_PASS; VALIDATION NOT EXECUTED

The dedicated runner keeps Fixture A spectral-only and regenerates all four
Fixture B sectors from the exact frozen `(p,z)` at center and both endpoints.
It provides detailed gate failures, separate C and residual-w directional rows,
and a bounded downstream raw-K preflight. The runner is frozen but was not
invoked; neither historical synthetic failure was modified.

- Harness artifact: `results/manifold_consistent_synthetic_vjp_harness_v1.json`,
  SHA-256 `e2e8d88916305a90fd49696055bce06ce8b23891fd594a608527053f5b9dbcec`.
- Execution manifest SHA-256:
  `dd81a21bb77acb133278a8c39f342f3c821dca135b5882b9728bb2d5aa9d529a`.
## EVID-0054 - Current model/code documentation alignment audit

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; DOCUMENTATION AUDIT ONLY

### Claim

The documentation audit inspected all 45 Markdown files, the source tree,
tests, configs, numerical entry points, available result metadata, and
manuscript/PDF availability without modifying scientific source or tests and
without running an experiment. The current source implements the C4
PS/GS/adaptive-\(V_A\) transmitter, raw-SKR loss, average-energy dual, and
finite-realization hard peak guard. It does not implement the target
scintillation/AoA/raw-\(T\) path, post-action phase-noise chain, or full
correlation-interval Holevo maximization.

### Evidence

- docs/FINAL_MODEL_SPEC.md
- docs/EQUATIONS.md
- docs/ASSUMPTIONS.md
- docs/CHANNEL_STATE_DISTRIBUTION.md
- docs/SECURITY_SCOPE_FREEZE.md
- docs/PAPER_CODE_ALIGNMENT.md
- src/channel/fso_channel.py
- src/channel/state_distribution.py
- src/modulation/joint_ps_gs.py
- src/cvqkd/mutual_information.py
- src/cvqkd/holevo.py
- src/optimization/trainer.py
- configs/default.yaml
- tests/ and results/current_test_suite.json were inspected read-only

### Provenance

Repository HEAD at audit start: 08cba9e743b249e439bfa8c899e5476e23003e62.
Initial FINAL_MODEL_SPEC SHA-256:
561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1.
Current edited FINAL_MODEL_SPEC SHA-256:
8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843.
No test, training, publication-scale Monte Carlo, certification, or final-test
access was performed by this audit.

### Limitations

This is documentation/source inspection evidence, not a scientific result,
security certification, or authorization to run the target model.

## EVID-0055 - Causal phase/post-action noise implementation

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; TARGET PARAMETER READINESS BLOCKED

### Claim

The implementation now samples and names the exogenous channel quantity as
(\epsilon_{\mathrm{base}}), passes it to the adaptive transmitter, computes
the canonical scenario-level phase coefficient and
(\epsilon_{\mathrm{total}}=\epsilon_{\mathrm{base}}+c_\phi V_A) after the
transmitter action, and passes the same derived tensor to MI and the existing
lower-endpoint Holevo interface. No (C_{n,\phi}^2) production value was
invented; the default target configuration remains null and target entry
points fail closed.

### Verification

- Command: `.\\.venv\\Scripts\\python.exe -m unittest tests.test_phase_noise tests.test_pipeline_consistency tests.test_channel_state_distribution tests.test_baseline_development_workflow tests.test_baseline_cached_source_moments -v`
- Result: 27 tests passed in 2.015 seconds; a supplemental 8-test PS/GS/
  gradient/controller selection also passed in 0.541 seconds.
- Additional static checks: targeted `py_compile` passed and `git diff --check`
  passed.
- The adaptive-(V_A) regression test exercised the SKR gradient through
  (V_A\rightarrow\epsilon_{\mathrm{total}}); the direct algebra test
  verified (d\epsilon_{\mathrm{total}}/dV_A=c_\phi).

### Scope and limitations

The existing Holevo (Z_-)-only algorithm was not modified. Composite
scintillation/AoA/raw-(T), full-(Z) maximization, training, publication-scale
Monte Carlo, certification, and final-test access were not run or implemented.
This entry is implementation evidence, not target-model numerical or
publication evidence.

## EVID-0056 - Full physically admissible Z-interval Holevo implementation

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; TARGET NUMERICAL REBINDING BLOCKED

### Claim

The active Holevo path now computes `Z_minus`, `Z_plus`, `Z_phys`, and their
closed physical intersection using the already-derived post-action
`epsilon_total`. It fails closed with `SecurityDomainError` and structured
interval diagnostics when the intersection is empty or a candidate covariance
fails physicality. For valid intervals it evaluates the existing standard-form
covariance and entropy functional over a deterministic fixed grid plus bounded
golden-section refinement in every grid cell, retains both boundaries, and
returns the selected `Z_star` and `chi_BE_ub`. The covariance cross block uses
the selected Z directly, with no additional `sqrt(T)` factor.

### Verification

- Command: `.\\.venv\\Scripts\\python.exe -m unittest tests.test_holevo_interval -q`
- Result: 11 tests passed.
- Command: `.\\.venv\\Scripts\\python.exe -m unittest tests.test_holevo_interval tests.test_phase_noise tests.test_pipeline_consistency tests.test_channel_state_distribution tests.test_baseline_development_workflow tests.test_baseline_cached_source_moments -q`
- Result: 38 tests passed in 3.969 seconds.
- Selected gradient and C4 backend command: 11 tests passed in 1.949 seconds.
- Selected cached shared-source downstream command: 2 tests passed.
- Targeted `py_compile`, `git diff --check`, and the current
  `FINAL_MODEL_SPEC.md` SHA-256 check passed; the hash remains
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`.

### Known pre-existing test blockers

- A 12-test legacy C4 backend selection ran 11 tests and encountered one
  pre-existing `NameError` because `test_fast_path_vjp_is_finite_at_repeated_sector_spectrum`
  references an undefined local `result`.
- A 25-test legacy gradient/optimizer selection ran 22 tests and encountered
  three pre-existing `FULL_SUPPORT_FALLBACK_EVALUATION_ONLY` errors. The
  arbitrary-precision fallback remains evaluation-only and was not changed.

### Scope and limitations

The fixed grid/refinement maximum is a deterministic numerical implementation;
it is not a new continuous-domain or numerical-certification theorem. Existing
MI/Gram evidence remains bound to the prior scalar-epsilon/lower-endpoint path
and must be rebound before target security/SKR claims. No C_n_phi2 value was
invented, and no training, certification, publication-scale Monte Carlo,
final-test access, or held-out evaluation was performed.

## EVID-0057 - Cn_phi2 scientific and configuration freeze audit

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; AUTHOR FREEZE BLOCKED

### Claim

`channel.cn_phi2_m_minus_two_thirds` is a scenario-level effective phase
turbulence input in `m^(-2/3)`. The repository provides no validated mapping
from the altitude-dependent `C_n^2(h)` scenario to this effective scalar, so
the phase and scintillation quantities remain distinct derived representations
of one physical source. The
production value remains `null`; no author-approved or literature-derived
phase value was found. `c_phi` is derived from the canonical `Cn_phi2`, SI
wavelength, and `LinkGeometry` link distance rather than configured independently.

### Candidate audit

The only `Cn_phi2` numeric values found were explicit test fixtures: `0`,
`1e-16`, and `2e-16 m^(-2/3)`. They are classified `TEST_ONLY` and are not
publication candidates. The active `cn2_m_minus_two_thirds=1e-16` value is a
separate legacy compatibility input and was not promoted to `Cn_phi2`.

### Verification

- Command: `.\\venv\\Scripts\\python.exe -m unittest tests.test_phase_parameter_freeze tests.test_phase_noise tests.test_pipeline_consistency tests.test_holevo_interval tests.test_baseline_development_workflow tests.test_baseline_cached_source_moments -v`
- Result: 42 focused tests passed in 7.517 seconds.
- Command: targeted `py_compile` over all changed Python entry points/modules/tests.
- Result: `CURRENTLY_VERIFIED_PASS`.
- `git diff --check` and the current `FINAL_MODEL_SPEC.md` SHA-256 check were
  run after the audit; the frozen specification remained unchanged.

### Scope and limitations

The freeze template proposes no weak/nominal/strong numeric scenarios because
the repository contains no defensible approved values. Provenance is recorded
alongside existing scalar coefficients and existing resolved-config hashing is
retained. No training, target/publication Monte Carlo, certification,
final-test, held-out evaluation, or numerical approval was performed.

## EVID-0058 - PRE-Numerical composite-channel alignment

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; PRODUCTION MAPPINGS BLOCKED

### Claim

The active channel architecture now composes deterministic Beer--Lambert
atmospheric loss, normalized lognormal scintillation, generalized Rician
pointing, and a hard AoA gate as
T_raw = eta_atm H_sc H_p B_AoA. Active physical admission rejects raw values
above one rather than clipping or flooring them, retains an outage zero, and
records p_out, p_in, p_above_one, raw/physical means, delta_T, and provenance.
The active sampler does not call the legacy constant-C_n^2 beam-wander
variance; sigma_z is excluded from pointing and yaw from AoA variance.

### Scientific blockers

No supported Hufnagel--Valley/profile parameter set, aperture-averaging
mapping from sigma_R0^2 to v_sc, turbulence-induced AoA mapping, or validated
profile-to-effective-C_n,phi^2 mapping was found. Production configuration
therefore remains unresolved/null and fails closed.

### Verification

- tests.test_composite_channel, tests.test_channel_provenance, and
  tests.test_holevo_resolution: CURRENTLY_VERIFIED_PASS.
- Existing channel/state/diagnostic, phase, pipeline, and full-Z focused
  suites: CURRENTLY_VERIFIED_PASS.
- Scoped command covering those modules plus the existing MI, SKR,
  invalid-input, and cached-baseline invariants: CURRENTLY_VERIFIED_PASS;
  90 tests passed in 2.744 seconds.
- Targeted py_compile over changed Python files: CURRENTLY_VERIFIED_PASS.
- git diff --check and frozen FINAL_MODEL_SPEC SHA-256 check:
  CURRENTLY_VERIFIED_PASS; SHA-256 remains
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`.
- The broader legacy gradient/optimizer selection remains separately
  `FAILED` with seven `FULL_SUPPORT_FALLBACK_EVALUATION_ONLY` errors; the
  evaluation-only full-support guard was not weakened.
- Worker-backed pointwise/full-support certification tests: `NOT_RUN` to
  completion under the lifecycle restriction.
- Training, publication-scale Monte Carlo, certification, held-out evaluation,
  and final-test access: NOT_RUN by policy.

### Scope

The 17/33/65/129 full-Z cases are numerical-resolution diagnostics only.
Existing numerical artifacts remain bound to their prior provenance and do not
certify this composite target.

## EVID-0059 - Outage-aware active-state SKR plumbing

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; EXPLORATORY PIPELINE FIX

### Claim

Mixed batches now keep AoA-outage states at exact \(T=0\), skip the policy and
the \(\log_{10}(T)\) feature for those rows, assign outage raw SKR exactly zero,
and preserve gradients through active rows. The composite diagnostics now expose
the signed mean_difference_T alongside the manuscript-relative delta_T.

### Verification

- python -m unittest tests.test_pipeline_consistency tests.test_composite_channel -v
  — 20 tests passed.
- Targeted py_compile for changed source/tests — pass.
- git diff --check — pass.

### Scope

The all-outage training batch fails closed because it has no active gradient
source. No security formula, phase ordering, PS/GS/VA architecture, or lifecycle
gate changed.

## EVID-0060 - Four exploratory composite-channel cases

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; EXPLORATORY_ONLY; NOT_PUBLICATION_APPROVED

### Claim

Cases A--D were sampled with \(N=1000\) each using explicit development
settings. Case A was deterministic atmospheric attenuation; B used
v_sc_override=0.25; C added Rician pointing with
sigma_hap_ang_rad=5e-6; D added an external-validated zero-turbulence AoA
gate with theoretical outage 0.25. Phase was explicitly zero and is not a
publication-approved parameter.

The channel behaved as expected: A had deterministic positive \(T\); B
broaded \(T\) with active mean \(H_{\rm sc}\approx1.029\); C reduced mean
pointing collection; D produced 268/1000 exact outage states versus theoretical
0.25. MI preflight values were finite. The paired manuscript delta_T is zero
for these retained raw/physical pairs; the prior nonzero discrepancy is retained
as proposal_delta_T because proposal and admitted populations differ.

### Evidence

- Artifact: results/exploratory_cases_20260910.json
- Pre-supersession artifact SHA-256:
  355ac90e98cd1c2e723a64e2d7fe8af68b360e5a09a64422bffd1870cc0be212
- Direct one-off Python runner from the project root; no training or
  publication entry point was invoked.

### Security limitation

Full-Z Holevo/K was not completed. The complex128 fast gate failed on the fixed
256-QAM fixture with minimum sector eigenvalue approximately
\(-1.57\times10^{-16}\); the arbitrary-precision fallback is evaluation-only
and was not run for this exploratory batch. Therefore all chi_BE, active-K,
and outage-weighted-K fields are intentionally null, not zero or inferred.

## EVID-0061 - Gram/full-support root-cause audit

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; NUMERICAL EVALUATION BLOCKED

### Claim

The exact exploratory uniform 256-QAM ensemble has 256 strictly positive
probabilities, 256 unique coherent amplitudes, minimum pairwise distance
0.1084652289, maximum amplitude 1.15044748, mean \(|alpha|^2=0.5\), and
\(V_A=1\). The complex128 full Gram and all C4 sectors are Hermitian to the
reported float64 residual, but are severely ill-conditioned: singular minima
are approximately \(10^{-20}\), with condition numbers \(10^{17}\)–\(10^{19}\).

Arbitrary-precision sector eigensolves on the same binary64 ensemble gave
minimum residuals of approximately \(10^{-52}\), \(10^{-103}\), \(10^{-203}\),
\(10^{-403}\), and \(10^{-604}\) at 50, 100, 200, 400, and 600 decimal digits.
The 600-digit resolution count was 254/256. This establishes floating-point
roundoff plus extreme numerical ill-conditioning as the root cause; no
duplicate constellation, zero probability, or sector-indexing bug was found.

### Verification

- Float64 sector/full-Gram diagnostic: 256 positive probabilities and unique
  states; Hermiticity residual 0.0 at reported precision.
- Existing fast gate reproduced a negative eigenvalue at approximately
  \(-1.573e-16\) and infinite condition number.
- Existing AP worker was run only on the one exact state at 400 and 600 digits
  before the bounded diagnostic was stopped; no \(C,w,\chi_{BE}\), or K result
  was promoted from that run.
- No Gram/Holevo production code or numerical gate was changed.

### Limitations

The mathematical full-support conclusion follows from the distinct coherent
states and positive probabilities, but the tiny eigenvalue scale was not fully
resolved to 256/256 within the bounded exploratory budget. This is not
numerical certification and does not authorize training or target SKR claims.

## EVID-0062 - One bounded AP-backed Case A full-Z security evaluation

Date: 2026-09-10

Status: SUPERSEDED_WRONG_AP_W

### Claim

The exact Case A uniform 256-QAM ensemble completed one bounded
arbitrary-precision-backed source-moment evaluation at 800 decimal digits.
Full support resolved at 256/256 with minimum positive eigenvalue approximately
\(3.973e-618\). The resulting \(C,w\) were transferred to the existing float64
covariance/full-Z evaluator without changing its equations or gate.

The physical interval was valid:

\[
[Z_L,Z_U]=[0.2910038617,\;0.2938938663],
\]

and the full-Z maximum occurred at the lower boundary:

\[
Z_\star=0.2910038617,\qquad
\chi_{BE}^{ub}=0.01562624349,
\qquad
K=0.00432058203.
\]

### Evidence

- Artifact: results/exploratory_case_A_full_security_20260910.json
- Pre-supersession artifact SHA-256:
  4e12de13919931a0f54ec9dbc895be5249f1194c408bfe3c322239089031dfad
- AP worker runtime: 290.929 seconds for the one exact state.
- MI used 64 samples per symbol; \(I_{AB}=0.02099665844\).

### Limitations

This entry is retained as historical evidence only. Its AP worker used the
wrong (w) definition and all downstream interval/Holevo/K values are stale.
The corrected Case A result is recorded in EVID-0066.

## EVID-0063 - Exploratory B-D full-Z security subset

Date: 2026-09-10

Status: SUPERSEDED_WRONG_AP_W

### Claim

After exact ensemble identity and C/w stability were established, Cases B-D were
evaluated on deterministic active security subsets of 16 states using the
verified 900-digit Case A source moments. No AP calculation was repeated per
state; no training path was enabled.

Results:

| Case | Mean MI | Mean chi_BE | Mean K active | Mean K all | p_out | Domain failures |
|---|---:|---:|---:|---:|---:|---:|
| B | 0.0291497460 | 0.0204856716 | 0.0072065872 | 0.0072065872 | 0 | 0 |
| C | 0.0267353449 | 0.0188097272 | 0.0065888504 | 0.0065888504 | 0 | 0 |
| D | 0.0236421496 | 0.0167342180 | 0.0057258242 | 0.0041913033 | 0.268 | 0 |

Case D satisfies the sampled outage identity:
\(0.732\times0.0057258242=0.0041913033\).
All 16/16 optima in B-D were at the lower interval boundary; no upper-boundary,
interior, or security-domain failures occurred.

### Evidence

- Artifact: results/exploratory_cases_BD_full_security_20260910.json
- Artifact SHA-256:
  e493bbdeda8ce8913862b8336a859dc2458a16dd444f392882d9b2389e39cc74
- Exact ensemble hash reused for all cases:
  c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3

### Limitations

The security subset is 16 active states per case, not a full-channel estimate.
In addition, the reused AP (w) was superseded by the corrected worker. These
values are historical only and are not current evidence or certification.

## EVID-0064 - Differentiable complex128 source-moment investigation

Date: 2026-09-10

Status: CURRENTLY_VERIFIED_PASS; DIFFERENTIABLE_PATH_BLOCKED

### Claim

The complex128 instability occurs at the C4 eigendecomposition/gate, before
matrix square-root, inverse-square-root, C, or w evaluation. Sector matrices
are finite and Hermitian with zero reported Hermiticity residual, but their
smallest float64 eigenvalues are roundoff-scale negative and their singular
condition numbers are approximately \(10^{17}\)–\(10^{20}\). Both existing
Hermitian square-root functions fail closed on the exact Case A sectors because
they require positive-definite input.

The same fast-gate failure persists for fixed \(V_A=0.5,1,2,4\), a mildly
nonuniform strictly-positive PS fixture, and a perturbed valid GS fixture.
No exact differentiable complex128 C/w formulation was found or implemented.

### Verification

- Exact Case A stage diagnostic: sector construction finite, Hermitian,
  eigensolver finite; sqrt/inverse-sqrt fail at the positive-definite guard.
- Existing gradient selection: four
  FULL_SUPPORT_FALLBACK_EVALUATION_ONLY errors; no AP gradient claim.
- No production Gram/Holevo/security code changed.

### Classification

FLOATING_POINT_ROUNDOFF plus NUMERICAL_ILL_CONDITIONING. This is not classified
as constellation collapse, probability support loss, or implementation indexing
bug. Differentiable training remains blocked.

## EVID-0065 - AP custom-backward feasibility audit

Date: 2026-09-10

Status: SUPERSEDED_BY_EVID-0066; PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION

### Claim

The requested square-root/inverse-square-root implicit adjoint was derived and
implemented as an isolated experimental AP VJP in
`src/cvqkd/ap_custom_backward.py`. On a small positive C4 fixture, the
combined (aC+bw) reverse VJP agrees with an 80-digit central difference to
the recorded test tolerance. The exact Case A ensemble was reconstructed with
row hash
`c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`.

At 800 decimal digits the experimental AP run resolved all 256 modes and
matched the stored (C) value, but its current-formula (w) was
`0.018327610474963502...`, whereas the stored AP worker/reference value is
`0.036100542613870033...`. The discrepancy is 0.017772932138906531... (about
49.23% of the stored reference), so the requested Case A directional VJP
validation was stopped before it could produce a valid claim.

### Evidence

- Artifact: `results/ap_custom_backward_case_A_20260910.json`
- Artifact SHA-256:
  `dc11c998f755d328906558b949444e4bf45a088657938f7b4b1c1a13daaf58d4`
- Experimental derivation/plan:
  `docs/superpowers/plans/2026-09-10-ap-custom-backward.md`
- Focused AP custom tests: `tests/test_ap_custom_backward.py`, 2/2 passed.
- Case A AP custom runtime: 1364.634083500001 seconds at 800 decimal digits.
- Existing AP forward reference runtime: 290.9291875362396 seconds; the
  additional reverse work is estimated at 1073.7048959637614 seconds. Linear
  total-cost estimates are 10917.072668 seconds for batch 8 and
  43668.290672 seconds for batch 32; neither batch was run.
- Resolved minimum positive eigenvalue:
  `3.9730108272405810054e-618`.

### Root cause and limitations

At the time of this audit, `scripts/full_support_c4_worker.py` formed
`aa=sr*x2.T`; the current C4 implementation required
(G_s D G_{s-1}^{-1}=x2.T). EVID-0066 corrected the worker and rebound the
bounded Case A result. The custom-backward directional suite remains pending
against the corrected AP oracle.

No Case A AP central-difference directional validation, torch PS/GS/\(V_A\)
chain, full-Z backward, optimizer step, training, certification, final-test,
or publication-scale evaluation was run.

## EVID-0066 - Corrected AP worker and Case A full-Z rebind

Date: 2026-09-11

Status: CURRENTLY_VERIFIED_PASS; CORRECTED_AP_FORWARD_VALIDATED; EXPLORATORY_ONLY

### Claim

The AP worker now matches the frozen production C4 (A_s=G_sDG_{s-1}^{-1})
definition: `aa=x2.T`. The prior `aa=sr*x2.T` expression multiplied the
production block by an extra (S_s) and produced the wrong (w).

Three explicit 20-digit fixture checks passed for uniform, mildly nonuniform
positive PMF, and perturbed real geometry. The exact Case A ensemble hash is
`c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`.

Corrected AP forward results:

| Digits | Modes | lambda_min | C | w | Runtime (s) |
|---:|---:|---:|---:|---:|---:|
| 800 | 256/256 | 3.973010827240581e-618 | 0.85985110654649868138 | 0.01832761047496350205 | 367.3323453 |
| 900 | 256/256 | 3.973010827240581e-618 | 0.85985110654649868138 | 0.01832761047496350205 | 416.6573139 |

The displayed 50-digit C and w values agree between 800 and 900 digits; the
reported difference is below (10^{-49}).

Using corrected (C,w), the bounded Case A full-Z result is:

\[
[Z_L,Z_U]=[0.2914192733053753,;0.2934784546975139],
\]

with interval width `0.002059181392138565`,
(Z_\star=0.2914192733053753),
(chi_{BE}^{ub}=0.01518919002933572), and raw
(K=0.004757635492383283). The maximizing branch was evaluated by the full
interval solver and occurred at the lower boundary for this state.

### Evidence

- `results/ap_worker_corrected_case_A_20260911.json`, SHA-256
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`
- `results/exploratory_case_A_full_security_corrected_20260911.json`, SHA-256
  `a3b7aaa23635ac5e01e08f3486d4131fe9d17580c51b32ef9b498324fa5723fa`
- Worker SHA-256:
  `2cd1feeeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Corrected Case A full-security artifact records old-vs-corrected values and
  marks the old result `SUPERSEDED_WRONG_AP_W`.
- Superseded artifacts: `exploratory_case_A_full_security_20260910.json`,
  `exploratory_cases_BD_full_security_20260910.json`,
  `baseline_cached_uniform.json`, `baseline_cached_binomial.json`,
  `baseline_cached_mb.json`, `baseline_cached_source_moments_smoke.json`,
  and `full_support_c4_gram_evaluation_validation_v1.json`.

### Limitations

Cases B-D were not recomputed. The corrected Case A result remains bounded,
exploratory, and evaluation-only. Custom backward directional validation is
pending against this corrected AP oracle.

## EVID-0067 - Corrected B-D bounded full-Z security rebind

Date: 2026-09-11

Status: CURRENTLY_VERIFIED_PASS; CORRECTED_A_TO_D_EXPLORATORY_SECURITY_COMPLETED; EXPLORATORY_ONLY

### Claim

Cases B, C, and D were recomputed through the existing physical channel,
statewise MI, corrected source moments, full physical-Z interval Holevo
maximization, and signed raw SKR path. The run used the exact uniform
256-state ensemble row hash
`c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`,
corrected
`C=0.85985110654649868138037962728289179096834048571987`, and corrected
`w=0.018327610474963502048823295065766568532781601388489`.

The bounded security subset contains 16 evenly spaced active rows per case.
The prior ignored B-D artifact and its exact indices were unavailable in this
checkout, so the runner records the deterministic reconstruction rule and new
index/state-pair hashes rather than claiming historical-index reuse.

| Case | mean T | std T | p_out | mean I_AB | mean chi_BE | mean K_active | mean K_all | positive-K fraction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B | 0.029744159058456707 | 0.016634846625299900 | 0 | 0.021431275288813056 | 0.021120154675722480 | -0.000760443151350077 | -0.000760443151350077 | 0.375 |
| C | 0.026411389634989624 | 0.015289139587414003 | 0 | 0.020185924876130967 | 0.019927263946943247 | -0.000750635314618829 | -0.000750635314618829 | 0.375 |
| D | 0.018873208422052853 | 0.016631411472660677 | 0.268 | 0.018074194289578682 | 0.019002584302762596 | -0.001832099727662848 | -0.001341097000649205 | 0.375 |

Case D has active fraction `0.732`, outage fraction `0.268`, and exactly
`268/1000` outage samples. Outage rows were excluded from MI/Holevo and
assigned exact raw `K=0`; the recorded mean-all identity discrepancy is
`0.0`.

For every evaluated case, all 16 full-Z optima were at the lower boundary;
there were zero upper-boundary or interior optima and zero security-domain
failures. Minimum interval widths were B `0.003086232377970677`, C
`0.0029270446367630765`, and D `0.0037002532899432783`; mean widths were B
`0.008015264181052232`, C `0.007714133290954911`, and D
`0.008364188796830796`. The minimum symplectic physicality diagnostics were
B `1.0003897834020814`, C `1.0003379486510962`, and D
`1.000706473068511`.

Negative statewise raw K values were retained; no positive clipping was used.
The corrected-vs-old-w comparisons are stored in the artifact. The corrected
mean chi_BE changes are +`0.000634483075722480`, +`0.001117536746943247`, and
+`0.002268366302762596` for B, C, and D respectively. Corrected mean K_active
changes are -`0.007967030351350077`, -`0.007339485714618829`, and
-`0.007557923927662849` respectively.

### Evidence and provenance

- New artifact: `results/exploratory_cases_BD_full_security_corrected_20260911.json`
- Artifact SHA-256:
  `c7c88940e5219a191277f358318eb756dcdeea61d6a6e546d0286af42a3c2ba0`.
- Producer: `scripts/recompute_corrected_bd_security.py`, SHA-256
  `7ed8327a7389b2ec3f1babba3ef5e4f682f95ca538d4bf4918eb4c79b2a6904c`.
- Corrected worker SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`.
- Corrected AP artifact SHA-256:
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`.
- Corrected Case A artifact SHA-256:
  `a3b7aaa23635ac5e01e08f3486d4131fe9d17580c51b32ef9b498324fa5723fa`.
- Superseded old B-D artifact SHA-256:
  `e493bbdeda8ce8913862b8336a859dc2458a16dd444f392882d9b2389e39cc74`.

The run used `N_channel=1000`, channel seed `20260910`, derived epsilon seed
`4542851964011138592`, AWGN seed `20260911`, 64 noise samples per symbol,
`V_A=1`, beta `0.95`, phase coefficient `0`, and explicit `v_sc=0.25`.
Producer runtimes were B `2.45327990000078 s`, C `2.1217880999902263 s`, and
D `2.2559983000101056 s`, for total `6.839092400012305 s`.
No AP eigendecomposition, training, optimizer step, final-test access, or
publication-scale evaluation was performed. The current FINAL_MODEL_SPEC
hash remains `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`.

### Verification and limitations

- Focused numerical/regression command: 44/44 tests passed.
- `tests.test_ap_worker_equivalence`: `BLOCKED_BY_ENVIRONMENT`; 1 test passed,
  1 slow test was skipped, and 3 tests errored because ignored historical or
  corrected-A JSON fixtures are absent from this checkout.
- Targeted `py_compile` passed.
- The result is a bounded exploratory rebind, not a publication, certification,
  target-model, or adaptive-training result. Corrected AP custom-backward
  directional validation remains pending.

## EVID-0068 - Corrected AP custom-backward cheap validation and bounded PS failure

Date: 2026-09-11

Status: CURRENTLY_VERIFIED_CHEAP_PASS; TARGET_DIRECTIONAL_VALIDATION_FAILED; EXPLORATORY_ONLY

### Claim

The isolated `source_moments_vjp` forward path matches an independent corrected
arbitrary-precision C4 oracle on four well-conditioned four-state fixtures.
Separate C and w directional components, the combined
`J=1.7*C-0.8*w` VJP, and real- and imaginary-alpha convention checks all pass
at 80 digits. The cheap h sweep uses
`1e-3, 3e-4, 1e-4, 3e-5, 1e-5` and reaches a central-difference plateau.

| Fixture | custom/AP C abs. error | custom/AP w abs. error | combined VJP relative error | Status |
|---|---:|---:|---:|---|
| uniform | 1.5431942360347756e-15 | 3.2995049782161180e-17 | 8.40796455182627e-12 | PASS |
| nonuniform positive | 1.3525230168992008e-15 | 5.4567820514094683e-17 | 3.65192560699911e-12 | PASS |
| perturbed real | 1.5657513429009646e-15 | 1.2421912587767274e-17 | 6.73185627518239e-12 | PASS |
| perturbed imaginary | 1.2576776804968873e-15 | 2.3831893654227314e-17 | 1.11326675514486e-11 | PASS |

The exact Case A mapping constructors also pass preflight structure checks
for PS, GS-real, GS-imag, and V_A: positive probabilities, probability sum
`1.0`, 256 unique states, zero-sum probability tangents to floating-point
roundoff, and nonzero geometry/variance tangents.

A single bounded 800-digit PS target attempt then failed the custom reverse
comparison. Corrected AP plus and minus endpoints both resolved `256/256`
with minimum eigenvalues `3.9787561820e-618` and `3.9672737490e-618`.
The corrected AP reference at `h=1e-4` was:

| AP dC | AP dw | AP dJ (`1.7*dC-0.8*dw`) |
|---:|---:|---:|
| 0.0005009242276532432925 | -0.0011532623528549834635 | 0.0017741810692945003680 |

The custom combined result was `3.3995565604790261e+102`, with relative
error `1.9161271751314836e+105`; this is a material failure, not a tolerance
reinterpretation. The custom VJP took `25653.3898618 s`; the two AP endpoints
took `392.6064219 s` and `297.1369369 s`, total target-attempt time
`26348.3480433 s`. GS-real, GS-imag, V_A component tables and full-Z backward
were not started after this fail-closed stop.

The conditioning probe independently shows reverse error increasing as the
smallest Gram eigenvalue approaches the full-support scale, while the forward
remains resolved. This supports a numerical reverse-stability blocker, but
does not validate the 256-state custom gradient.

### Evidence and provenance

- Cheap artifact: `results/ap_custom_backward_corrected_directional_validation_20260911.json`
- Cheap artifact SHA-256:
  `60d6da12dc23bb8d4d086fef6ab3a349201c33745d0a930ba37be8b76203bc14`
- Bounded target-attempt artifact:
  `results/ap_custom_backward_ps_target_attempt_20260911.json`
- Target-attempt artifact SHA-256:
  `3c8b87793b76abc82e0ecc89a5e33fb9c513dec749cdbbd2e4e2f5b4f3856d2a`
- Producer SHA-256:
  `6fa71c0d1d055627a4fa93af79e12617d166712bd0ed14534319d394190e8db9`
- Target-attempt runner SHA-256:
  `3f24854ccf9906a42bde8132f8e6d175ca7a49c928c2caf32027c5914a767244`
- Custom-backward SHA-256:
  `f9b15ae2134fa8aa5137bd9ff298baac98a2a35148431636c644c25c28ae2b92`
- Corrected worker SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Corrected AP source-moment artifact SHA-256:
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`
- Exact ensemble SHA-256:
  `c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`
- Current FINAL_MODEL_SPEC SHA-256:
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`

The prior custom-backward artifact SHA-256
`dc11c998f755d328906558b949444e4bf45a088657938f7b4b1c1a13daaf58d4`
is `SUPERSEDED_WRONG_AP_W`; it is not used as a forward or gradient oracle.
No training, optimizer step, final-test access, channel change, security
equation change, clipping, jitter, support truncation, or full-Z backward was
performed.

### Verification

- `python scripts/validate_corrected_ap_custom_backward.py --phase cheap`:
  `CHEAP_FIXTURE_VALIDATION_PASS`.
- Focused custom/spectral/gradient/protocol suite (including the cheap
  corrected-backward regression): `20/20` passed; the
  parser-negative `--seed` usage line is expected.
- `tests.test_ap_worker_equivalence`: `1` passed, `1` skipped, `3` errored
  because ignored historical/corrected-A artifacts are absent locally;
  classification `BLOCKED_BY_ENVIRONMENT`.
- `py_compile`, JSON parsing/hash checks, and `git diff --check` passed.

### Consequences

Classify the isolated prototype as `AP_CUSTOM_BACKWARD_NOT_VALIDATED`.
Adaptive training remains `NOT_READY_FOR_ADAPTIVE_TRAINING`; the next task is
one root-cause investigation of full-support AP reverse stability/precision.

## EVID-0069 - Full-support differentiable source-moment research audit

Date: 2026-09-11

Status: CURRENTLY_VERIFIED_RESEARCH_ONLY; NO_LIFECYCLE_CHANGE

### Claim

The bounded research audit confirms that the frozen C4 C/w equations are
consistent with the analytical finite-constellation DM-CV-QKD source objects,
and that the proposed forward tangent is the correct diagnostic boundary.
The target custom VJP remains invalid and impractical: corrected AP gives
\(dJ=0.0017741810692945003680\), while the custom reverse gives
\(3.3995565604790261\times10^{102}\) after approximately 7.1 hours.

The target \(\lambda_{\min}\approx3.9730108272405810054\times10^{-618}\)
implies inverse-square-root and Frechet-derivative scales beyond binary64 and
supports a numerical-cancellation hypothesis. This does not, by itself,
exclude a reverse implementation bug.

The primary recommended research path is an exact C4 operator/tangent
reformulation using the solve constraints
\(B_sS_{s-1}=S_sD\) and
\(A_sG_{s-1}=G_sD\), followed by a compiled multiprecision backend only
after the forward tangent and local adjoint identities pass. No security
surrogate, spectral repair, or training was introduced.

### Evidence and provenance

- Research artifact:
  docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md
- Research artifact SHA-256:
  6624e6451c1cec060853d2101e5f3dd247d9ec2c73ae416414d59ed1e29d5ad6
- Bounded workflow plan:
  docs/superpowers/plans/2026-09-11-full-support-differentiable-source-moments-research.md
- The report cites Denys et al. for \(\tau\), \(a_\tau\), \(w\), and QAM
  context; Higham and related matrix-function references for Frechet and
  Sylvester theory; and Arb/FLINT/MPFR references for backend limitations.
- Existing numerical values and hashes are inherited from EVID-0068; no
  target AP job was rerun for this report.

### Verification

- Equation audit covers forward tangents for \(H_d,G_s,S_s,R_s,J_s,A_s,B_s,
  Q_s,T_s,C,w\).
- Reverse audit covers product, inverse, Hermitian projection, ordinary
  transpose, Hermitian transpose, Sylvester, and raw-sector adjoints.
- The report records exact-vs-approximate security error propagation and
  full-Z branch nonsmoothness.
- git diff --check passed after the artifact was created.

### Consequences

Keep the classification
AP_CUSTOM_BACKWARD_NOT_VALIDATED and lifecycle
NOT_READY_FOR_ADAPTIVE_TRAINING. The next permitted numerical task is the
isolated exact forward tangent and three-way PS diagnostic at an adaptive
precision ladder. Do not begin adaptive training, full-Z backward, or
publication-scale evaluation.

## EVID-0070 - Exact C4 constrained-solve forward tangent

Date: 2026-09-11

Status: CURRENTLY_VERIFIED_PASS; DIAGNOSTIC_ONLY

### Claim

An isolated arbitrary-precision C4 forward tangent for the exact full-support
source moments is implemented and validated for the prior Case-A PS direction.
The implementation returns C, w, dC, and dw and differentiates the full
support construction through dH, dG, the square-root Sylvester equation, the
constrained B/A solves, Q/T/u/E, and the C/w product rules. It does not import
or call the old custom reverse and is not connected to autograd or training.

The constrained equations are

    B_s S_(s-1) = S_s D,
    A_s G_(s-1) = G_s D,

with tangents

    dB_s S_(s-1) = dS_s D + S_s dD - B_s dS_(s-1),
    dA_s G_(s-1) = dG_s D + G_s dD - A_s dG_(s-1),

and S_s dS_s + dS_s S_s = dG_s. No clipping, jitter, epsilon identity,
pseudoinverse, rank reduction, or support truncation was used.

### Machine-readable artifact and provenance

- Artifact:
  `results/c4_constrained_forward_tangent_20260911.json`
- Artifact SHA-256:
  `023fb41db59a079314f639ff47513890445c7a7b885c17273a5f3df52b71ddcb`
- Diagnostic module:
  `src/cvqkd/c4_constrained_tangent.py`
- Module SHA-256:
  `a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258`
- Runner:
  `scripts/validate_c4_constrained_tangent.py`
- Runner SHA-256:
  `de7f5e9c6ec9060c5135092aba89864b46bcd019884f10c34514af86405b6c70`
- Focused tests:
  `tests/test_c4_constrained_tangent.py`
- Focused-test SHA-256:
  `6763a7c82c74929a4e4ba3b06df4376fbf027abc417d3dc69a2a4fe711f59c09`
- Prior corrected PS target artifact SHA-256:
  `3c8b87793b76abc82e0ecc89a5e33fb9c513dec749cdbbd2e4e2f5b4f3856d2a`
- Corrected worker SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Exact ensemble SHA-256:
  `c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`
- Recovered prior Case-A PS direction SHA-256:
  `e274073c5038308b521bd1a348c932a4a249cd5fc59a006b7611911e2be6dd87`

### Cheap fixtures

Uniform, nonuniform-positive, perturbed-real, and perturbed-imaginary
four-prototype fixtures all passed. Direct explicit R/J products and the
constrained products agree below 1e-40 relative; solve and Sylvester residuals
are below 1e-45 relative. At h=1e-5, the largest central-difference relative
errors were 6.53e-12 for dC, 6.73e-11 for dw, and 8.95e-12 for combined
dJ. The corrected AP forward C/w values also agree below 2e-50 relative.

### Recovered target direction and precision ladder

The deterministic direction reproduces the prior failed-PS artifact: 64
positive prototype probabilities, sum 1.0, 256 unique states, directional
z-norm 0.15669108927249908, and the direction hash above. The bounded target
ladder recorded the following:

| AP digits | resolved modes | minimum eigenvalue | runtime (s) | result |
|---:|---:|---:|---:|---|
| 200 | 184/256 | -9.3548858387e-203 | 38.5077 | fail closed |
| 400 | 227/256 | -8.0583390027e-403 | 64.8990 | fail closed |
| 600 | 254/256 | -9.1586922129e-604 | 113.5961 | fail closed |
| 800 | 256/256 | 3.9730108272e-618 | 1181.1304 | resolved |

At 800 digits, the constrained tangent produced

    C   = 0.85985110654649868138037962728289179096834048571987
    w   = 0.018327610474963502048823295065766568532781601388489
    dC  = 0.00050092422832962377222627091862944921206718683231693
    dw  = -0.0011532623534953207533476618573511008283277382475422
    dJ  = 0.0017741810709566170444324223035415062817078761571016

Relative to the prior corrected AP central difference at h=1e-4, the errors
are 2.70e-51 for C, 1.88e-51 for w, 1.35e-9 for dC, 5.55e-10 for dw, and
9.37e-10 for dJ. All are below the 1e-8 directional target. The largest
800-digit constrained solve/Sylvester relative residual was below 8e-735;
the B/dB residuals were below 9e-800.

### Conditioning and runtime boundary

The target constrained path's largest materialized A and dA magnitudes were
approximately 9.83e68 and 7.13e68. On the uniform cheap fixture, the old
explicit path materialized R, J, dR, and dJ at approximately 2.27e2,
5.45e4, 4.58e2, and 2.10e5 respectively. The target explicit-intermediate
comparison was attempted but terminated after an approximately 16-minute
runtime window without a completed row. The target constrained-only row took
1181.1304 s, far above the proposed one-minute practicality gate.

### Verification and consequences

- `tests.test_c4_constrained_tangent` and the existing corrected AP regression:
  5/5 passed.
- `py_compile` for module, runner, and tests passed.
- `git diff --check` passed.
- No reverse VJP, GS-real, GS-imaginary, V_A, full-Z backward, optimizer step,
  training, final-test access, publication-scale evaluation, or security-model
  change occurred.

Classify the bounded forward tangent as
`CONSTRAINED_TANGENT_VALIDATED`. This is a local Case-A PS source-moment
diagnostic, not a claim that an adaptive-training gradient is practical or
that the old reverse is repaired. Adaptive readiness remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`. The next permitted derivative task is to
validate the remaining source directions and then separately design a
practical exact reverse boundary; do not start training or full-Z backward.

## EVID-0071 - Bounded full-support forward tangent for remaining source directions

Date: 2026-09-11

Status: CURRENTLY_VERIFIED_PASS; DIAGNOSTIC_ONLY

### Claim

The same isolated arbitrary-precision C4 constrained-solve forward tangent
passed bounded target validation for GS-real, GS-imaginary, and \(V_A\), in
that order, using the existing physical transmitter mapping and the corrected
AP worker for central finite differences. Together with EVID-0070, all four
source directions (PS, GS-real, GS-imaginary, and \(V_A\)) have a validated
forward tangent at the 800-digit target. This does not validate the old
reverse, establish a production gradient, authorize adaptive training, or
change the security model.

No manual 256-alpha perturbation was used. The GS-real path perturbs
`coordinates[0,0]` in the existing 64-prototype representation; GS-imag
perturbs `coordinates[0,1]` through an independent mapping call. Both retain
unit-RMS gauge removal and V_A=1. The V_A path fixes the uniform PMF
and relative constellation and uses (V_A=1+	heta). All target endpoints
use the existing physical normalization

    E_z=sum q|z|^2; s=sqrt(V_A/(2 E_z)); alpha=s*i^r*z,

with phase disabled (`c_phi=0`). The AP finite difference evaluates the
production map at (	heta=-h,+h), rather than linearly perturbing 256
amplitudes.

### Machine-readable artifact and provenance

- Artifact:
  `results/c4_remaining_forward_tangents_20260911.json`
- Artifact SHA-256:
  `471e04862ef5cfaaa3ee65c01d229285ce43f93cb4c08ca8bfc4a198a4414566`
- Runner:
  `scripts/validate_remaining_c4_forward_tangents.py`
- Runner SHA-256:
  `a829e608a73d91a08222753f7660a8303186f9d6b618c26d640331b19641534a`
- Tangent module SHA-256:
  `a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258`
- Focused tests SHA-256:
  `a6b8024aece7257b803c20fdc8ba48cd046d13b012b80f09888ae8c375d08c78`
- Existing production-map source SHA-256:
  `6fa71c0d1d055627a4fa93af79e12617d166712bd0ed14534319d394190e8db9`
- Corrected worker SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Exact ensemble SHA-256:
  `c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`
- FINAL_MODEL_SPEC SHA-256:
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`
- Prior PS tangent artifact SHA-256:
  `023fb41db59a079314f639ff47513890445c7a7b885c17273a5f3df52b71ddcb`

### Cheap directional preflight

All 12 combinations of the three direction families and four small,
well-conditioned fixtures passed at 70 AP digits with h=10^{-5}. The
largest relative errors over the four fixtures were:

| direction | max rel. dC | max rel. dw | max rel. dJ | result |
|---|---:|---:|---:|---|
| GS-real | 7.34e-12 | 1.00e-9 | 2.45e-11 | pass |
| GS-imaginary | 8.66e-12 | 1.24e-10 | 1.46e-11 | pass |
| V_A | 8.88e-12 | 3.39e-10 | 6.29e-12 | pass |

The preflight passed before any 800-digit target computation.

### Target tangent and corrected AP finite difference

Each row used 800 AP digits and one primary h=10^{-4}. The reported
relative target is 10^{-6} for non-near-zero references; all nine target
derivative references were non-near-zero.

| direction | FD dC | tangent dC | rel. dC | FD dw | tangent dw | rel. dw | rel. dJ | tangent s | minus s | plus s | total s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GS-real | -1.23446476359084e-4 | -1.23446476967690e-4 | 4.9301e-9 | 3.47998923826786e-4 | 3.47998925288747e-4 | 4.2010e-9 | 4.5144e-9 | 1406.56 | 297.11 | 297.06 | 2001.04 |
| GS-imaginary | -1.23446476359084e-4 | -1.23446476967690e-4 | 4.9301e-9 | 3.47998923826786e-4 | 3.47998925288747e-4 | 4.2010e-9 | 4.5144e-9 | 1085.59 | 1497.54 | 295.52 | 2878.94 |
| V_A | 5.70250419269228e-1 | 5.70250418939442e-1 | 5.7832e-10 | 1.24889153232869e-2 | 1.24889153193817e-2 | 3.1270e-10 | 5.8108e-10 | 1081.90 | 299.22 | 414.53 | 1795.96 |

All target rows passed. The endpoint-minus and endpoint-plus structures were
positive, normalized, 256-state unique, and full support resolved. The
GS endpoints have physical energy 0.5 for V_A=1; the V_A endpoints
have physical energies 0.49995 and 0.50005 for V_A=0.9999,1.0001.

### Support, residual, and magnitude diagnostics

| direction | central min eigenvalue | minus min eigenvalue | plus min eigenvalue | central/minus/plus rank | max B rel. residual | max dB rel. residual | max A rel. residual | max dA rel. residual | max Sylvester rel. residual |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| GS-real | 3.9730e-618 | 3.9600e-618 | 3.9861e-618 | 256/256/256 | 8.08e-800 | 1.59e-799 | 7.66e-735 | 1.07e-799 | 3.72e-800 |
| GS-imaginary | 3.9730e-618 | 3.9600e-618 | 3.9861e-618 | 256/256/256 | 8.08e-800 | 1.29e-799 | 7.66e-735 | 1.14e-799 | 3.64e-800 |
| V_A | 3.9730e-618 | 3.8730e-618 | 4.0756e-618 | 256/256/256 | 8.08e-800 | 4.64e-800 | 7.66e-735 | 2.11e-798 | 6.14e-800 |

The largest central constrained magnitudes, reported as log_{10} of
the maximum absolute entry, were:

| direction | H | dH | G | dG | S | dS | B | dB | A | dA | Q | dQ | T | dT | u | du | E | dE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GS-real | -2.408 | -2.833 | -1.809 | -2.252 | -1.709 | -1.963 | 1.202 | 1.941 | 68.993 | 70.368 | -0.806 | -1.060 | -0.540 | -0.765 | 0.337 | -0.034 | -1.471 | -1.811 |
| GS-imaginary | -2.408 | -2.833 | -1.809 | -2.252 | -1.709 | -1.963 | 1.202 | 1.941 | 68.993 | 70.368 | -0.806 | -1.060 | -0.540 | -0.765 | 0.337 | -0.034 | -1.471 | -1.811 |
| V_A | -2.408 | -2.637 | -1.809 | -2.201 | -1.709 | -2.008 | 1.202 | -0.740 | 68.993 | 69.057 | -0.806 | -1.105 | -0.540 | -0.674 | 0.337 | -0.320 | -1.471 | -1.394 |

### Verification and consequences

- `.venv\Scripts\python.exe -m unittest tests.test_c4_constrained_tangent tests.test_ap_custom_backward_corrected -v`: 7/7 passed.
- `.venv\Scripts\python.exe -m py_compile scripts\validate_remaining_c4_forward_tangents.py tests\test_c4_constrained_tangent.py`: passed.
- `.venv\Scripts\python.exe scripts\validate_remaining_c4_forward_tangents.py --phase cheap`: 12/12 cheap directional rows passed.
- `git diff --check`: passed after the implementation checks; rerun after this evidence update.

No reverse VJP, full-Z backward, optimizer step, training, B-D/Holevo
backward, final-test access, publication-scale evaluation, or security-model
change occurred. The existing corrected `w` definition and source-moment
functional are unchanged. The target study total was 6677.63 seconds,
including 1.69 seconds of cheap preflight; target-direction totals were
6675.94 seconds.

Classify the combined four-direction diagnostic as
`FULL_SOURCE_FORWARD_TANGENT_VALIDATED`. This remains diagnostic-only and
does not make the path computationally practical for adaptive training.
Adaptive readiness remains `NOT_READY_FOR_ADAPTIVE_TRAINING`. The single
remaining blocker is a validated and computationally practical reverse/adjoint
of the constrained C4 source-moment system. The next permitted task is a
separately scoped practicality study of that boundary; do not execute reverse,
full-Z backward, or training as part of this evidence.

## EVID-0072 - Constrained reverse practicality study

Date: 2026-09-11

Status: CURRENTLY VERIFIED PASS; DESIGN ONLY; NO REVERSE EXECUTED

### Claim

The exact C4 constrained-solve reverse is mathematically sound as a
solve-based adjoint of the validated forward graph. Its minimal expensive
solve count is eight cached primal right solves, eight adjoint right solves,
and four self-adjoint square-root Sylvester solves. It needs no explicit
inverse matrices and has a manageable sub-GB tape estimate, but the target
conditioning and current Python/multiprecision runtime model fail the
practicality gates for an mpmath training backend.

The separately scoped report therefore selects exactly
SKIP_MPMATH_REVERSE_AND_BUILD_COMPILED_MULTIPRECISION_PROTOTYPE.
Adaptive readiness remains NOT_READY_FOR_ADAPTIVE_TRAINING; no reverse VJP,
full-Z backward, optimizer step, training, final-test access, or
publication-scale evaluation occurred.

### Evidence

- docs/CONSTRAINED_REVERSE_PRACTICALITY_STUDY.md
- Report SHA-256:
  5a8bfb0444d1658fed55ad6f1a13cf29c7b4c53bf3614e676db1a97a3a3c0f16
- docs/FULL_SUPPORT_DIFFERENTIABLE_SOURCE_MOMENTS_RESEARCH.md
- src/cvqkd/c4_constrained_tangent.py, SHA-256
  a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258
- results/c4_remaining_forward_tangents_20260911.json, SHA-256
  471e04862ef5cfaaa3ee65c01d229285ce43f93cb4c08bfc4a198a4414566
- FINAL_MODEL_SPEC.md, SHA-256
  8ec01861627c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843

### Boundary

The report is a derivation and planning artifact, not a reverse-validation
result. Primitive adjoint identities, a complete reverse VJP, compiled
multiprecision timing, full-Z backward, and training remain unrun. The next
permitted task is one narrow C++17 64x64 one-sector primitive benchmark at
1250, 1450, and 1650 decimal digits with residual and inner-product gates.

## EVID-0073 - Deep research refinement of the reverse-gradient boundary

Date: 2026-09-11

Status: CURRENTLY VERIFIED PASS; RESEARCH/DESIGN ONLY; NO REVERSE EXECUTED

### Claim

The current full-support reverse-gradient blocker has been expanded into a
37-section literature-backed decision report. The report derives the exact
right-solve and square-root Sylvester adjoints under the real Frobenius
pairing, preserves complex \(u\) and weighted \(w\), compares MPFR/MPC with
Arb/FLINT and Julia/Nemo, gives conservative \(C,w\) error propagation into
the \(Z\) interval, and rejects unannounced spectral truncation. It selects
the compiled C++17 MPFR/MPC constrained reverse as the primary point
prototype, with Arb/acb_mat as a certification/reference mode.

This is a research and engineering recommendation. It does not validate a
reverse VJP, certify an approximate gradient, authorize adaptive training,
or broaden the project's asymptotic security scope.

### Evidence

- docs/DEEP_RESEARCH_SOURCE_MOMENT_REVERSE_GRADIENT.md
- Report SHA-256:
  f6bc18fe28747ee123514d69171f55f49383975e732f51e8dd5a40785bd97996
- docs/CONSTRAINED_REVERSE_PRACTICALITY_STUDY.md, SHA-256:
  5a8bfb0444d1658fed55ad6f1a13cf29c7b4c53bf3614e676db1a97a3a3c0f16
- results/c4_remaining_forward_tangents_20260911.json, SHA-256:
  471e04862ef5cfaaa3ee65c01d229285ce43f93cb4c08bfc4a198a4414566
- src/cvqkd/c4_constrained_tangent.py, SHA-256:
  a42141951a0afec655398868c35f08cad0a6a69cf204f451d6495ebf144c6258
- docs/FINAL_MODEL_SPEC.md, SHA-256:
  8ec01861627c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843
- External theorem, numerical-linear-algebra, arbitrary-precision, and
  DM-CV-QKD references are listed in the report's Sources section.

### Boundary

No primitive adjoint identity, compiled benchmark, full reverse VJP,
full-\(Z\) backward, optimizer step, training run, final-test access,
publication-scale evaluation, or security approval occurred. The next
permitted action remains the one-sector C++17 multiprecision benchmark at
1250, 1450, and 1650 decimal digits, with residual, inner-product, factor
reuse, and timing gates.

## EVID-0074 - Bounded training-surrogate analysis figures and exact anchors

Date: 2026-09-11

Status: CURRENTLY VERIFIED PASS; ANALYSIS ONLY; NEGATIVE FULL-METHOD OUTCOME

### Claim

An isolated `TRAINING_SURROGATE_ONLY` complex128 source-moment path passed the
predeclared Case-A directional calibration and four nearby full-support
ensemble checks. It was used only to search six bounded analysis methods on a
deterministic 16-active-state representative grid with explicit AoA outage
mass. The exact corrected AP worker and existing full-physical-Z Holevo chain
then evaluated MB and seven Full anchors. All eight AP anchor jobs converged;
all 21 exact-vs-surrogate anchor orderings were rank-consistent; the maximum
relative C, w, and K discrepancies were `6.16e-9`, `2.16e-6`, and `2.18e-6`,
respectively.

The figures are analysis-grade and phase-disabled. They do not establish a
positive security result: every active exact raw-K anchor is negative, and the
Full exact-bin estimate (`-0.0015155352`) is worse than the fixed MB baseline
(`-0.0011516261`). The weighted surrogate search-proxy values are marked
`OPTIMIZATION/ANALYSIS ESTIMATE` and are not security certificates.

### Evidence

- `docs/ANALYSIS_FIGURES_REPORT_20260911.md`
- Report SHA-256:
  `b9f0d1f2edb78ec4d9ef02cb4dea063ea175591050c1d7a436f731dfeb1a02c5`
- `src/cvqkd/training_surrogate.py`, SHA-256:
  `266100eb00b8108e7b4738fc6489a697a09c099f76a147895df78579464819be`
- `scripts/run_analysis_figures.py`, SHA-256:
  `9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f`
- `results/training_surrogate_calibration_20260911.json`, SHA-256:
  `7a299f20e7948819ee5f27a737b27669df9f337e7ed9356c288df3bb12b8a8f0`
- `results/training_surrogate_nearby_calibration_20260911.json`, SHA-256:
  `333147ffcccee3adff4ce4da23eb40043ca213b0709edc7d16182149bc0b4a60`
- `results/analysis_channel_grid_20260911.json`, SHA-256:
  `973b282bf62f6b908dd6fabde98947f04e633aca6862870f7e4f54a5bb370c58`
- `results/analysis_training_checkpoints_20260911.json`, SHA-256:
  `c512d37be22890cbbbeef8a6dba0fac38f1bd549a51c7b674956f415c02110eb`
- `results/analysis_candidate_ensembles_20260911.json`, SHA-256:
  `cf46ac546f61cea46bf8b89a12b50045cf90e120faf88a9d087e26347e24c057`
- `results/analysis_exact_ap_security_anchors_20260911.json`, SHA-256:
  `b24d230f5c120fb978636e3f38b244dd48e3f11e9bf911e9777ad6a740aaa637`
- `results/analysis_figure_data_20260911.json`, SHA-256:
  `239d3da2a8cd318d92eab77108f28afd36109cfdd068dc56332d5776b679e699`
- `results/analysis_figures_artifact_20260911.json`, SHA-256:
  `4918fad14ab9a59ede0ac8e4392bc0130df99d1f2fd1a26e6785a59366dc3292`
- Exact corrected worker SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- Grid hash:
  `af2f912e81000a4b09d1942f28ac03078ddc6602774e9b772ba020c4557c5ad2`

### Boundary and verification

The channel grid is a reconstructed exploratory Case-D representative grid,
not a frozen production channel scenario: 1000 sampled realizations, 16
active representatives, active mass `0.732`, and outage mass `0.268`. Phase
was deliberately disabled with `c_phi=0` and
`epsilon_total=epsilon_base`. The active environment had no matplotlib/PIL or
other raster/PDF backend, so six pure-stdlib SVG figures were produced; no
PNG/PDF claim is made.

The smoke and 50-step analysis optimizations passed finite-gradient, PMF,
constellation, V_A-bound, energy, and 256-state uniqueness checks. Uniform and
MB were fixed baselines; `nu=0.1` was not selected as a new formal MB optimum.
The runner took approximately 3654.46 seconds, dominated by the bounded exact
AP anchor rows. A post-write stale print reference was corrected after the
artifact was synthesized; the final artifact provenance is rebound to the
current runner hash above.

No production security implementation, exact C/w definition, full-Z equation,
channel equation, outage rule, phase mapping, final-test data, publication
training, publication-scale evaluation, or lifecycle authorization changed.
The analysis result is `ANALYSIS_FIGURES_READY` but remains
`NOT_PUBLICATION_CERTIFIED`. The scientific classification is
`MIXED_PRELIMINARY_SUPPORT`: the search surrogate is well supported as a
local optimization aid, while the Full method has no meaningful exact
full-Z advantage over the simple baseline in this scenario.

## EVID-0075 - Full-Z objective and aggregation mismatch audit

Date: 2026-09-11

Status: CURRENTLY VERIFIED PASS; DIAGNOSTIC ANALYSIS ONLY; NO SECURITY CLAIM

### Claim

The saved analysis objective audit identifies a decisive mismatch between the
smooth search proxy and the frozen full-Z target. The proxy's `tanh` mapping
places `Z_proxy` below the source-moment lower endpoint `Z_L` in all 16 active
representative states for every tested method mode. The ratio `Z_proxy/Z_L`
is approximately `0.767--0.790`. The proxy is therefore not an
interval-preserving approximation to `max_{Z in [Z_L,Z_U]} chi_BE(Z)` and can
change method rankings.

The fixed-grid aggregation arithmetic passes: active mass is `0.732`, explicit
outage mass is `0.268`, each active representative has unconditional weight
`0.04575`, and all weights sum to one within floating-point roundoff. Active
conditional normalization is a common factor and cannot explain a rank
reversal. The raw negative-rate convention remains intentional under the
frozen specification.

For the fixed baselines, exact full-Z weighted raw K is `-0.0011904563`
(Uniform) and `-0.0009584152` (MB), while the proxy reports
`-0.0273018358` and `-0.0273036361`; exact positive active cells are 5/16
and 7/16 respectively, versus 0/16 for both proxy rows. A first Uniform grid
state has exact interval approximately `[0.1888606775, 0.1919762611]` but
`Z_proxy=0.1449848007`; its exact raw K is `+0.0006380156` and proxy raw K is
`-0.0211091475`.

The saved learned-candidate full-Z recheck is explicitly an analysis estimate
because it uses saved surrogate `C,w`, not corrected AP source moments. It
reverses the proxy ranking: MB is above Uniform, `V_A`, Full, PS+`V_A`, and
PS. Current exact Full anchors also remain worse than MB except at one small
lowest-T difference; the exact-bin Full estimate is `-0.0015155352` versus MB
`-0.0011516261`.

### Evidence and provenance

- `docs/DEEP_RESEARCH_FADING_FULL_Z_BLOCKER_20260911.md`, SHA-256:
  `2cc9f30119903c858304567d8abf962930ce845327db70c35ef9715094d5bc99`
- `scripts/audit_analysis_objective.py`, SHA-256:
  `cabc201737aa3292d528e1cc616a64f3dff1beb25ebf9532fd8f24845f6be80`
- `results/analysis_objective_audit_20260911.json`, SHA-256:
  `bbf6389997941e8447a51261405e45fbfb0b6653a210207f8dda7d070acd6b69`
- Input figure data SHA-256:
  `239d3da2a8cd318d92eab77108f28afd36109cfdd068dc56332d5776b679e699`
- Analysis runner SHA-256:
  `9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f`
- Frozen model specification SHA-256:
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`
- Representative-grid hash:
  `af2f912e81000a4b09d1942f28ac03078ddc6602774e9b772ba020c4557c5ad2`

### Boundary

The producer is read-only analysis code. It did not modify the production
security implementation, frozen model, channel model, final-test data, or
lifecycle authorization. It performed no publication-scale training, final-
test access, reverse VJP, full-Z backward, baseline selection, or security
certification. The 1000-sample/16-representative grid is exploratory, phase is
disabled, and the current fading average remains an oracle-CSI analysis
functional rather than an operational fading security proof.

### Next action supported by this evidence

Repair the search objective with an interval-preserving `Z` parameterization
or the exact bounded full-Z functional, then run only a bounded baseline/rank
audit and short candidate recheck. Defer exact PS+`V_A`, Full-minus-GS causal
controls, and any larger training until the repaired objective agrees with the
exact full-Z reference. Keep `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and
`NOT_READY_FOR_ADAPTIVE_TRAINING`.

## EVID-0076 - Interval-preserving full-Z search objective repair

Date: 2026-09-11

Status: CURRENTLY VERIFIED PASS; ANALYSIS ONLY; EXACT PS+V_A RANKING FAIL-CLOSED

### Claim

The isolated repaired search objective reuses the existing full-physical-Z
Holevo path and its deterministic bounded maximizer with surrogate `C,w`
only during search. The old smooth `tanh` proxy was reproduced first and was
outside the source-moment interval in all `96/96` mode-state rows. The repaired
path had `0/96` interval violations, passed the corrected Case-A reference,
matched the existing Uniform/MB/Full exact AP/full-Z anchor orderings, and
passed finite PS/GS/V_A gradient smoke.

The bounded PS+V_A and Full 50-step analysis checks both passed their 20-step
smoke. On the three selected poor/median/good states, new Full exact AP source
rows converged and Full exceeded MB at all three states; the equal-weight
three-state Full-minus-MB raw-K difference was `+0.0006754022`. The optimized
PS+V_A exact AP rows all failed closed at the full-support worker gate, so no
PS+V_A exact K or complete PS+V_A-versus-Full ranking is claimed.

### Evidence and provenance

- `docs/REPAIRED_FULL_Z_OBJECTIVE_REPORT_20260911.md`, SHA-256:
  `b6077b4942390ea90840b463d495a3199a85fa332f21ede11e604868265b3a5c`
- `scripts/run_repaired_full_z_objective.py`, SHA-256:
  `cd8e4080f5ec859c7466b252a236a88804e01a0c62aa4641e12b1c7a1d6409b3`
- `src/cvqkd/holevo.py`, SHA-256:
  `2380cd196238a06438e86d767f4cb342361ae5054d5154df7f398556e4b0b3c5`
- `tests/test_repaired_full_z_objective.py`, SHA-256:
  `e979927fcfd06e4296d31f8f51b2825b9668ec20615256503a41d497312692da`
- `results/repaired_full_z_objective_analysis_20260911.json`, SHA-256:
  `aa94fc2032ab9d1421c3f4256cf3a7a4be6526c612797f4b162c1c8c85d98f23`
- `results/repaired_full_z_exact_jobs_20260911.json`, SHA-256:
  `52eafe5ee42af34a53b2280ddf10639fe77d50f87702ddc754ababbb06b5ad5c`
- `results/repaired_full_z_ps_va_exact_failure_20260911.json`, SHA-256:
  `27b6474a67b26755f076d3ed7569fe5fe22b3f0758df0242e059ccf4333b997f`
- Existing figure input SHA-256:
  `239d3da2a8cd318d92eab77108f28afd36109cfdd068dc56332d5776b679e699`
- Frozen model specification SHA-256:
  `8ec01861627c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`

### Verification

The corrected Case-A exact raw K was `0.004757635492383283`; the repaired
surrogate/full-Z value was `0.004757636501528051`, with absolute difference
`1.0091e-9`. Existing anchor comparison had maximum absolute K error
`5.2219e-9`, maximum relative error `2.1818e-6`, and consistent ordering on
all seven anchors. Focused `unittest` ran `16` tests with `OK`.

The repaired artifact records the fixed-candidate rank change from
old-proxy order
`PS+V_A > Full > PS > V_A > Uniform > MB` to repaired order
`MB > V_A > Uniform > Full > PS+V_A > PS`. The selected full-Z points are
inside `[Z_L,Z_U]` and the added scalar-evaluator assertion fails closed on
non-finite or out-of-interval candidates.

### Boundary and consequences

This is `ANALYSIS_ESTIMATE` evidence on the existing phase-disabled,
exploratory 16-state grid. It is not a security certification, baseline
selection, adaptive-training authorization, or publication result. No
publication-scale training, final-test access, MPFR/MPC implementation,
corrected AP worker change, C/w definition change, channel/beta/phase/epsilon
change, K clipping, or full-Z equation change occurred.

The exact PS+V_A failure is recorded separately and is not converted to a K:
the 100/150/200-digit diagnostic ranks were below the required 256 full
support in all three states, and the required 800/900-digit attempts returned
`FAIL_CLOSED`. The remaining lifecycle status is
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; novelty remains
`CURRENT_NOVELTY_NOT_SUPPORTED`.
