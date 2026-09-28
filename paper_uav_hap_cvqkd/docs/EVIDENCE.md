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

## EVID-0077 - PS+V_A full-support blocker root-cause audit

Date: 2026-09-12

Status: CURRENTLY_VERIFIED_PASS; DIAGNOSTIC_ONLY; BLOCKER_UNRESOLVED

### Claim

The focused research audit tests the remaining corrected-AP blocker without
changing the model or opening a lifecycle-gated run. It records PMF, logit,
scale, geometry, serialization, and precision observations for the optimized
PS+V_A checkpoint and matched Full anchors. PS+V_A has positive probabilities
with q_min between 0.00652427 and 0.00912075, p_min between 0.00163107 and
0.00228019, q_max/q_min between 2.66088 and 4.4995, and observed logit ranges
below 1.51. The repository MB reference at nu=0.1 has p_min
0.003306576946... and q_min 0.01322630778....

The weighted-Gram q_min bounds therefore do not support ordinary probability
concentration as the primary explanation for the PS failure. PS and Full also
have nearly equal V_A in the repaired step-50 comparison, and PS has the
larger anchor physical scale and minimum pair separation. A small Full GS
perturbation can still alter an extremely small Gram mode, but its causal
effect is unmeasured.

A read-only 300-digit probe resolved rank 206 for both PS median and Full
median and failed closed at the expected near-zero eigensolver floor. Full
then converged at 800/900 digits, while the PS high-ladder attempts at the same
digits failed closed. This establishes a precision/conditioning contribution
but does not distinguish a PS-specific worker/solver failure from genuinely
worse conditioning. The selected next category is exactly
INVESTIGATE_AP_WORKER_BUG.

### Evidence and provenance

- results/ps_va_full_support_blocker_diagnostic_20260912.json, SHA-256:
  8a44ca9330cca61d8a15d2457b6c1d8445b560b5776935e184de15e550f5255d
- docs/DEEP_RESEARCH_PS_VA_FULL_SUPPORT_BLOCKER_20260912.md, SHA-256:
  c4031394281b6529887f86fa93d7516b6d7ab7c07ce3a5f55c402f3c0a866251
- results/repaired_full_z_ps_va_exact_failure_20260911.json, SHA-256:
  27b6474a67b26755f076d3ed7569fe5fe22b3f0758df0242e059ccf4333b997f
- results/repaired_full_z_exact_jobs_20260911.json, SHA-256:
  52eafe5ee42af34a53b2280ddf10639fe77d50f87702ddc754ababbb06b5ad5c
- scripts/full_support_c4_worker.py, SHA-256:
  2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1
- scripts/run_analysis_figures.py, SHA-256:
  9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f
- src/modulation/probabilistic_shaping.py, SHA-256:
  89e60be5b7ce3de863918f03a6f036287aafc0688a8e24718869784c5b0832b7
- src/modulation/joint_ps_gs.py, SHA-256:
  3760b7c2677c9c88361eb444778f5955beff4529a69472df927647cfac384d8f
- src/modulation/normalization.py, SHA-256:
  88dd777f6ce2f64117dc64cbcebc1335337aaa73f5b597410618d0581fd47ce2
- src/modulation/qam256.py, SHA-256:
  34238f2958943016fac82766e464c3dbacb797a60a2df55566d41afee4a145fa
- src/cvqkd/gram_moments.py, SHA-256:
  bbad4c303a71ae69be99a4fffba90d968de35f34242977bad03dc1b3e6c5c551
- docs/FINAL_MODEL_SPEC.md, SHA-256:
  8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843

### Interpretation

The mathematical support of the current finite positive PS ensemble is not
shown to be lost. The exact PS source moments are still unavailable, so the
worker gate remains correctly fail-closed. The next permitted numerical task is
one median-checkpoint worker decomposition with direct binary64 hex replay,
captured 300/400/600/800/1000/1200-digit rows, and an independently implemented
sector or factorization cross-check using Full median as a positive control.

No training, final-test access, baseline selection, publication-scale evaluation,
C/w equation change, channel change, or support-floor amendment is authorized.
Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive readiness
remains NOT_READY_FOR_ADAPTIVE_TRAINING.

## EVID-0081 - Frozen PS+V_A source moments converged and median full-Z evaluated

Date: 2026-09-12

Status: CURRENTLY_VERIFIED_PASS; RESEARCH-ONLY; MEDIAN-ONLY

### Claim

The authorized `DIRECT_HIGHER_PRECISION_SECTOR_RUN` was completed for exactly
one frozen repaired-objective optimized PS+V_A median candidate. The 1050
decimal-digit diagnostic resolved all four 64x64 C4 sectors with total rank
256 and well-behaved residuals. The 1250 and 1450 acceptance rows both
resolved all 256 modes, passed the frozen C/w convergence criterion, and
produced the authoritative source moments

```text
C_PSVA = 0.8610813007552428909072445071897962976560950806268
w_PSVA = 0.0067220381757562110710871873472856506670610666856165
```

The exact single median full-Z evaluation used the existing 33-grid/12-
refinement implementation, frozen `T`, `epsilon_base`, phase-disabled
`epsilon_total=epsilon_base`, learned `V_A`, `beta=0.95`, and the converged
AP C/w values. It passed `Z_L <= Z_star <= Z_U` and returned

```text
Z_L       = 0.25403343722167576
Z_U       = 0.258948630366243
Z_star    = 0.25403343722167576
I_AB      = 0.01569902141495305
beta I_AB = 0.014914070344205398
chi_BE    = 0.014533912528089
raw K     = 0.0003801578161163992
```

The resulting exact median classification is
`PS_VA_MEDIAN_BEST`, with the existing exact median values ordered
PS+V_A > Full > MB. This is a one-state analysis result, not a three-state
adaptive or publication claim.

### Candidate and numerical provenance

- `results/PS_VA_SOURCE_MOMENTS_CONVERGED_20260912.json`, SHA-256:
  `9b3b269c1c1ae81e027bb8864fb1ccf711551327a2497530602f37bf252f6115`
- `docs/PS_VA_SOURCE_MOMENTS_CONVERGENCE_REPORT_20260912.md`, SHA-256:
  `d1e39435c27063bae978348bedd733a28bc4eb32da86d79e5f1b6b2c3937714a`
- `results/ps_va_source_moments_1050_20260912.json`, SHA-256:
  `dd4d70a0483c8502ffefe1d81a6efa42a6b0adec64619da1d0c532cbc9720f97`
- `results/ps_va_source_moments_1250_1450_20260912.json`, SHA-256:
  `52f446062110e7a21e8138bcf7bfa8c3d11d94904bb80efde17ad43a4c5db474`
- frozen checkpoint SHA-256:
  `1c5d49d1a562c558a18a76994399b09c4bee88ddbebf35370ae9cb690e3ca8d`
- direct input hash:
  `4589747c3ae1cf3d8ce996d13f591a0e8f2aae7dd64df402a81507255dd43a99`
- canonical q probability hash:
  `cb54155a394cad8ce7c162fdfd43e620bf89e7da366a241bd2a6aa7574bee47b`
- orbit constellation hash:
  `3e56859fb805f8f445c6ec8c465fc435b1b5706a025e67f673c649f30498fcab`
- full constellation hash:
  `ee71ed4bbd636ac5418ded90f9762a1ef6f9c0b61a7954f4621ca59332b2ee96`
- `scripts/full_support_c4_worker.py`, SHA-256:
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`
- `scripts/replay_instrumented_current_worker.py`, SHA-256:
  `5dc9832511129dbcdd9a24468fd634924e8e9d6211e6fbe58e1a80a2b5514434`
- `scripts/record_ps_va_median_authority.py`, SHA-256:
  `cb4a387d533ae9b87d3460e3c70479550f66cf356956e37a40c08c7ad1c4ffd8`
- existing exact MB/Full median reference
  `results/repaired_full_z_objective_analysis_20260911.json`, SHA-256:
  `aa94fc2032ab9d1421c3f4256cf3a7a4be6526c612797f4b162c1c8c85d98f23`
- `docs/FINAL_MODEL_SPEC.md`, SHA-256:
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`

### Interpretation

EVID-0081 consumes the DEC-0064 execution authorization and supersedes the
previous `INSUFFICIENT_AP_PRECISION` interpretation for this frozen median
candidate. It does not authorize the unrun poor/good ranking, adaptive
training, baseline selection, final-test access, publication-scale work, or a
novelty claim. The next recommended numerical task is a separately authorized
exact poor+good ranking only because the adaptive method beats MB at this
median state.

The 1050 row took `844.7600824` seconds. The 1250/1450 acceptance process
took `2009.1630606` seconds combined; separate full-row wall times for those
two rungs were not captured, while solve-only totals were `152.2347689` and
`217.5061456` seconds respectively. The explicit corrected C/w fixture
regression remains limited by the existing complex128 production gate on its
perturbed-geometry fixture (`1.343480882098902e-12` versus the `1e-12` gate),
and this is retained as a verification limitation rather than silently
repaired.

Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive readiness
remains NOT_READY_FOR_ADAPTIVE_TRAINING.

## EVID-0078 - Dense-global spectrum necessity decision audit

Date: 2026-09-12

Status: CURRENTLY_VERIFIED_PASS; DIAGNOSTIC_ONLY; RESEARCH-ONLY

### Claim

The research-only numerical-analysis memo determines that a dense
256-by-256 arbitrary-precision eigensolve at the 700--900 digit support
precision is not scientifically necessary for the current PS-versus-Full
worker question. Exact weighted-Gram/source-spectrum equivalence and exact C4
Fourier block diagonalization show that the global spectrum is the union of
the four sector spectra. An independently constructed direct 256-state
weighted Gram at 100 decimal digits has zero reported Hermiticity,
Fourier-off-block, and sector-match residuals for both the median PS+V_A case
and the matched Full control. The global spectrum field in that artifact is
explicitly NOT_RUN.

The unchanged current worker independently reaches rank 256 in every sector
for PS at 800/900 and 1000/1200 digits and for Full at 800/900 digits. The
successive rows have stable C,w and positive minimum resolved modes. This
reclassifies the earlier PS fail-closed attempt as
INSUFFICIENT_AP_PRECISION for the present blocker decision; it does not
support AP_WORKER_PS_SPECIFIC_BUG or AP_FAIL_GATE_BUG. The three-state exact
adaptive ranking remains incomplete.

The dense-check decision is exactly
LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT. A bounded
independent low-precision global spectrum audit remains the next numerical
task, but the expensive dense high-precision target is STOPPED.

### Evidence and provenance

- docs/DEEP_RESEARCH_DENSE_GLOBAL_SPECTRUM_DECISION_20260912.md,
  SHA-256: a6fe26730bfdd874155264d6829674c4004e6007707d8ba0258f0f9e95c47e92
- results/ps_va_ap_worker_localization_20260912.json,
  SHA-256: b068f2fc5a83d9acf269cff532e1f3cf218c640319b3a26bd6c4cea5876e7908
- results/ps_va_worker_instrumented_800_900_20260912.json,
  SHA-256: 3d7dc1024f022a5a4b1121fc6ce98c5c618e6abe46c91b7adcf662c4a75e43a6
- results/ps_va_worker_instrumented_1000_1200_20260912.json,
  SHA-256: 649ff8f2a1a8022d4eef6afa1f6be2b003e34818291a89b1bde01c28a6c927dd
- results/full_worker_instrumented_800_900_20260912.json,
  SHA-256: 08510463a9a57c1e002129805e6f2f25c5dbf216258614623d7467650bb90bde
- scripts/diagnose_ps_va_ap_worker.py,
  SHA-256: dda92c7d9e5070eede104c229b04b1a776445280005d6aea6d9e8f397ac128d7
- scripts/replay_instrumented_current_worker.py,
  SHA-256: 49e78ba130c1ba6aa6de41275a417ed7102d9245a30f5954619cd92d9c39385294
- scripts/full_support_c4_worker.py,
  SHA-256: 2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1
- scripts/run_analysis_figures.py,
  SHA-256: 9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f
- results/repaired_full_z_checkpoint_ps_va_20260911_step_50.pt,
  SHA-256: 1c5d49d1a562c558a18a76994399b09c4bee88ddbebf35370ae9cb690e3ca8d
- results/repaired_full_z_checkpoint_full_20260911_step_50.pt,
  SHA-256: 9e5bf3fb8534cbf2640ca0feb99810518c110c283931d701c44ee52e16622e51
- docs/FINAL_MODEL_SPEC.md,
  SHA-256: 8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843

### Interpretation

No production worker, C/w equation, model family, security definition, or
lifecycle gate was changed. The 100-digit direct matrix audit is structural
evidence only; its approximately 10^-102 negative tail is a numerical
resolution floor. The 800--1200 digit sector rows are diagnostic source
moment evidence only. The next permitted numerical task is
RUN_INDEPENDENT_LOW_PRECISION_GLOBAL_BLOCK_AUDIT on the frozen median PS and
Full inputs at 80/120/200 digits, with a 15-minute total budget. Do not run
the dense high-precision target unless a surviving independent mismatch or
explicit external audit requirement creates a new hypothesis.

Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive readiness
remains NOT_READY_FOR_ADAPTIVE_TRAINING. No security, novelty, publication,
or adaptive-ranking claim follows.

## EVID-0079 - Independent bounded low-precision global block audit

Date: 2026-09-12

Status: CURRENTLY_VERIFIED_PASS; DIAGNOSTIC_ONLY; BOUNDED_PARTIAL

### Claim

The authorized independent global weighted-Gram audit ran under the hard
900-second total budget. It completed the frozen median PS+V_A row at 80
decimal digits, timed out the PS 120-digit child at the remaining budget, and
did not start PS 200 or any Full row. The watchdog finished in
899.0290027 seconds with `budget_compliance=true` and status
`DENSE_LOW_PRECISION_COST_BOUNDED_SKIP`.

The completed PS 80-digit row independently formed the 256-state weighted
Gram from serialized binary64 inputs, checked Hermiticity, trace,
Frobenius, trace-square, Fourier off-block structure, and production-sector
agreement, and then compared the dense eigenvalues with the Fourier-sector
union. It resolved 48 modes above the diagnostic 1e-60 threshold; the
maximum global/sector-union absolute discrepancy was approximately
4.22e-81 and the eigendecomposition residual was approximately 1.89e-80.
The result supports the existing C4 block reduction and provides no evidence
for `AP_WORKER_PS_SPECIFIC_BUG` or `AP_FAIL_GATE_BUG`. It is not a support
certificate and does not complete a PS-versus-Full six-row global audit.

The audit helper's reported Fourier-unitarity field was corrected after the
run: an mpmath callable matrix initializer had produced a zero reporting
matrix, while the explicit W transform was unaffected. The corrected nested-
list construction was checked by the focused Fourier test, and the artifact
records the correction transparently in `posthoc_correction`.

### Evidence and provenance

- docs/INDEPENDENT_GLOBAL_BLOCK_AUDIT_REPORT_20260912.md,
  SHA-256: bf2f0d9b8c2f6b98e50ea0ab90620bb05941475c3b2400be8bc54dda28029b7f
- results/independent_global_block_audit_20260912.json,
  SHA-256: 4adebde66edc194d1097c900f2cffffdb5302278f194c04fd8253fd2fddc292e
- input results/ps_va_ap_worker_localization_20260912.json,
  SHA-256: b068f2fc5a83d9acf269cff532e1f3cf218c640319b3a26bd6c4cea5876e7908
- scripts/diagnose_ps_va_ap_worker.py,
  SHA-256: f771d77ba42282820b2c240637c11563811c1e37b621745264b4d8d4fcb347ba
- scripts/run_independent_global_block_audit.py,
  SHA-256: 2936c65d885a9fce3505ef4235d1f9bbfec6debceecab03087f340fe334d183f
- tests/test_ap_worker_equivalence.py,
  SHA-256: f15d44737e672f4cffe89bd108b037c88b2c21b0dcd2b91a018aceae9fa4568e
- scripts/full_support_c4_worker.py,
  SHA-256: 2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1
- scripts/run_analysis_figures.py,
  SHA-256: 9f9b085c2ddddb9acf484070e5b32eddf2d883d7dcd040416df506b048da549f
- docs/FINAL_MODEL_SPEC.md,
  SHA-256: 8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843

### Interpretation

EVID-0079 accepts the bounded partial audit as structural diagnostic
evidence. It does not reopen the stopped dense high-precision global target,
does not change the model or security definitions, and does not authorize
training, baseline selection, final-test access, or publication-scale work.
The exact dense decision remains
`LOW_PRECISION_GLOBAL_PLUS_HIGH_PRECISION_SECTORS_SUFFICIENT`; the immediate
AP diagnosis remains `INSUFFICIENT_AP_PRECISION`.

The next permitted numerical task is to determine the minimum sector-level AP
precision for frozen PS+V_A, compute exact C,w, and then evaluate only the
median full-Z security point. That task was not executed here.

Lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS and adaptive readiness
remains NOT_READY_FOR_ADAPTIVE_TRAINING.

## EVID-0080 - Deep research decision for minimum PS+V_A sector precision

Date: 2026-09-12

Status: CURRENTLY_VERIFIED_PASS; RESEARCH-ONLY; DECISION-SUPPORT

### Claim

The research-only numerical-analysis investigation selects
`DIRECT_HIGHER_PRECISION_SECTOR_RUN` as the cheapest defensible path for the
remaining frozen optimized PS+V_A source-moment blocker. The next fixed
source-moment ladder should start at 1050 decimal digits, with acceptance at
1250 and confirmation at 1450 digits, followed by only the median full-Z
point. The repository's frozen `1050,1250,1450` ladder and full-support
acceptance rule remain unchanged.

The current PS median has a high-precision diagnostic minimum eigenvalue of
approximately `5.5183e-598` (`-log10` approximately `597.26`). Existing
800/900 and 1000/1200 rows already show stable `C,w` and rank 256, so the
1250/1450 recommendation is a provenance and protocol decision rather than a
claim that 1250 digits are mathematically required for this particular
printed eigenvalue. A mixed outcome-driven sector ladder is not selected
because the frozen protocol forbids outcome-based precision changes and the
cross-sector `w` residual needs a stated error budget.

The investigation proves the weighted-Gram lower bound
`lambda_min(P^(1/2) G P^(1/2)) >= p_min lambda_min(G)`, estimates the PS
probability penalty at about 0.30 decimal orders relative to uniform for the
same geometry, and derives first-order `C,w` to `Z` error propagation. It
finds no evidence that a dense high-precision global eigensolve, an Arb
backend, or a source-moment reformulation is needed for the current blocker.

### Evidence and provenance

- `docs/DEEP_RESEARCH_MINIMUM_PS_VA_SECTOR_PRECISION_20260912.md`,
  SHA-256:
  `5d9a58d8d437fe0f14756316c14a2128ce429c4d2b162204d4f7cfe3d1cc65d4`
- `results/ps_va_worker_instrumented_800_900_20260912.json`,
  SHA-256:
  `3d7dc1024f022a5a4b1121fc6ce98c5c618e6abe46c91b7adcf662c4a75e43a6`
- `results/ps_va_worker_instrumented_1000_1200_20260912.json`,
  SHA-256:
  `649ff8f2a1a8022d4eef6afa1f6be2b003e34818291a89b1bde01c28a6c927dd`
- `results/full_worker_instrumented_800_900_20260912.json`,
  SHA-256:
  `08510463a9a57c1e002129805e6f2f25c5dbf216258614623d7467650bb90bde`
- `results/ps_va_ap_worker_localization_20260912.json`,
  SHA-256:
  `b068f2fc5a83d9acf269cff532e1f3cf218c640319b3a26bd6c4cea5876e7908`
- `docs/FULL_SUPPORT_C4_GRAM_BACKEND_PROTOCOL.md`
- `docs/NUMERICAL_CONVERGENCE_PREREGISTRATION.md`
- `docs/FINAL_MODEL_SPEC.md`, SHA-256:
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`

### Interpretation

EVID-0080 is a decision-support memo, not a numerical result. No AP run,
dense eigensolve, source-moment rebind, full-Z evaluation, training, final
test access, or lifecycle transition occurred. The exact next permitted task
remains the bounded frozen PS+V_A 1050/1250/1450 sector ladder followed by one
median full-Z diagnostic, subject to the existing fail-closed gates. Lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and adaptive readiness remains
`NOT_READY_FOR_ADAPTIVE_TRAINING`.

## EVID-0082 - Manuscript HAP-UAV channel PDF implementation audit

Date: 2026-09-16

Status: CURRENTLY_VERIFIED_PASS; CHANNEL-ONLY DIAGNOSTIC; NOT PUBLICATION CERTIFIED

### Claim

The attached manuscript channel was implemented and audited without changing
the security model or running training. The active default configuration now
derives the scintillation variance from the Hufnagel–Valley profile and the
finite-aperture mapping, uses the generalized pointing law, preserves the
exact AoA outage atom at (T=0), and admits active (T_{raw}\le1) states by
rejection/resampling rather than clipping.

The derived values are
`sigma_R0^2=0.04145444025152738`, `A_A=0.3460413382535926`, and
`v_sc=0.01434494998119213`. The channel PDF diagnostic reports
`<T>=0.019220202427078496`, `<sqrt(T)>=0.1196294585088479`, and
`<T xi>=0.0003940141497551092`, with `P(X>1)=6.269417070431365e-195`.

### Evidence and provenance

- `scripts/calculate_channel_pdf_and_moments.py`, SHA-256:
  `3a448d85147a1f7596d9d2b0e62f405c208432f9244725e72325ca23b5409b03`
- `results/channel_pdf_and_moments.json`, SHA-256:
  `9d791747510e6d2d662492b69d947943a0d096d24d0bc3a0dc1c68dbb5310d76`
- `results/figures_preliminary/channel_transmittance_pdf.png`
- `results/figures_preliminary/channel_transmittance_pdf.pdf`
- `tests/test_channel_pdf_and_moments.py`
- Focused channel/PDF/pipeline/phase suite: 63 tests passed.

### Scope and limitations

The attached PDF is external manuscript input, not a repository security
specification. The Hufnagel–Valley and zero-turbulence AoA values are
scenario-level channel inputs; common-turbulence phase mapping remains null in
the production phase configuration. No training, SKR/security evaluation,
baseline selection, final-test access, or publication-scale run occurred.

Lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`; adaptive training
remains `NOT_READY_FOR_ADAPTIVE_TRAINING`.

## EVID-0083 - Latest manuscript channel consistency correction

Date: 2026-09-25

Status: CURRENTLY_VERIFIED_PASS; CONDITIONAL CHANNEL-ONLY DIAGNOSTIC;
ATMOSPHERIC SCENARIO UNSELECTED

### Claim

The active channel/PDF implementation now uses direct MODTRAN zero-zenith
transmittance `eta_atm=tau_zen**sec(zeta)`, the Table-III Hufnagel--Valley
ground value `C_n^2(0)=1e-14`, the receiver diameter `D_r=0.08 m` derived
once from the configured radius `0.04 m`, the manuscript finite-aperture
factor with `lambda*Phi*sec(zeta)` in its denominator, finite-curvature beam
propagation, and the manuscript `G_d`, `A0`, and equivalent-beam-width
pointing path. Legacy Kruse/visibility and generalized-pointing calls remain
explicit compatibility fixtures only.

The production configuration deliberately leaves `tau_zen: null`; no one of
the manuscript's `0.92`, `0.89`, or `0.75` scenarios was selected. Active
configuration-driven paths fail closed with an atmospheric-scenario decision
error. The explicit conditional diagnostic used `tau_zen=0.92` only as a
reproducible formula/PDF check.

### Evidence and provenance

- `results/channel_pdf_and_moments_20260925.json` (local ignored artifact)
- Artifact SHA-256: `8abeac6c5713a2459b80e279055831d22855db0302be6440383f73828757fa2e`
- `results/channel_pdf_validation_20260925_v2/` (local ignored figures)
- `tests/test_composite_channel.py`
- `tests/test_final_hap_uav_baseline.py`
- `tests/test_channel_pdf_and_moments.py`
- Focused channel/state/PDF/phase/pipeline/numerical-freeze suite: 84 tests
  passed.
- `docs/FINAL_MODEL_SPEC.md` SHA-256 remains
  `8ec018616b27c41104b8bd6d1b5025c2db99d09a14f64409f43dfc60efa01843`.

### Conditional diagnostic values

For explicit `tau_zen=0.92`: `L=21939.310229205777 m`,
`eta_atm=0.9082089654181442`, `sigma_R0^2=0.053962077796191735`,
`Phi=9200.562528132386 m`, `AA=0.7307070923781438`,
`sigma_R,D^2=0.039430472965138456`, `sigma_X^2=0.009857618241284614`,
`G_d=0.0002781635150138471`, `A0=0.0005346028752556014`, and
`omega_L,eq=2.446919845177366 m`. The closed-form and independent integral
PDFs differed by at most about `8.7e-12` on the meaningful density region;
the reported normalizations were `1.000000000000008` for both closed/product
active integrals, and the conditional Monte Carlo comparison passed.

### Limitations

This is channel-only conditional diagnostic evidence. It does not select the
atmospheric baseline, certify the security/SKR path, authorize training,
baseline selection, final-test access, or publication-scale work. Existing
historical Kruse/homogeneous artifacts remain legacy evidence and are not
rebound to this target.

## EVID-0084 - Supplied MB C,w applied to the new conditional channel

Date: 2026-09-25

Status: SUPERSEDED_INVALID_COMMON_ENSEMBLE; DIAGNOSTIC_ONLY

### Claim

The supplied ten historical Maxwell--Boltzmann source-moment pairs were
applied unchanged to the new conditional channel with `tau_zen=0.92`,
`zeta=30 deg`, `V_A=2`, and the legacy AO diagnostic `eta_AO=0.95`.
The current channel moments give
`T_eff=0.0002548668306761576` and
`epsilon_eff=0.13479156643649148`. The existing DM-CV-QKD MI/Holevo/SKR
pipeline was used; no Gaussian security approximation or optimizer was added.

All ten rows passed PMF normalization, `V_A=2`, covariance physicality, and
finite MI/Holevo/SKR checks. All raw SKRs were negative. The numerical maximum
of this supplied grid is at `nu_MB=0.20` with
`K=-0.00018194195597724065` bits/symbol.

### Evidence and provenance

- `results/mb_sweep_fixed_zeta30_VA2.csv`, SHA-256:
  `aadf089c6050c89c0671b7fa7f8e16ad41fa28c8e165ee3a3503f6f07e6e56dd`
- `figures/skr_vs_mb_fixed_zeta30_VA2.pdf`, SHA-256:
  `563119f3560fd5d740362caf2f803c76a2aa82bef3a05f48f0a3c40fce7bb732`
- `figures/skr_vs_mb_fixed_zeta30_VA2.png`, SHA-256:
  `f9a9657a0bd650fe707f12ef5b0a50bbc1701e791437f2aae1fed768f0e7a874`
- Producer: `scripts/run_cached_mb_cw_new_channel.py`, SHA-256:
  `45941de275d26bff57f21968964ffcc471f14dc3eda3b936fbf5bf9d1585e76d`
- Supplied C,w table: `results/mb_nu_threshold_va2/mb_nu_threshold_va2_refined.json`.

### Scope limitations

The supplied C,w rows are historical source-moment evidence under the prior
MB convention and precision policy; they were not recomputed for the new raw
channel realization. This result is therefore a conditional diagnostic, not
a newly certified baseline selection or publication result. The fixed AO phase
fixture uses `C_n,phase^2=1e-16`; production `tau_zen` remains unresolved in
configuration and the lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

## EVID-0085 - MB C,w sweep rebound with reduced phase turbulence strength

Date: 2026-09-25

Status: SUPERSEDED_INVALID_COMMON_ENSEMBLE; DIAGNOSTIC_ONLY

### Claim

EVID-0084 was rebound with the user-selected diagnostic phase turbulence
strength `C_n,phase^2=9.4e-18 m^-2/3`. The channel, supplied ten C,w rows,
`tau_zen=0.92`, `zeta=30 deg`, `V_A=2`, AO `0.95`, and beta `0.95` were held
fixed. All ten rows passed the same PMF, VA, covariance, MI, and Holevo checks.

The resulting `epsilon_eff` is `0.029382316951626387`. All SKRs are positive;
the maximum is at `nu_MB=0.20` with
`K=0.00004194428949251256` bits/symbol.

### Evidence and provenance

- `results/mb_sweep_fixed_zeta30_VA2.csv`, SHA-256:
  `95df645156d14cc3beadd1c63b0b9a6b533fbb3ac1dc05a9819cdbccc0bdfaa1`
- `figures/skr_vs_mb_fixed_zeta30_VA2.pdf`, SHA-256:
  `27a5a574799887adcb1e5942956067f79835d41883688f303d7b2a878870aed5`
- `figures/skr_vs_mb_fixed_zeta30_VA2.png`, SHA-256:
  `fb96d5324633bfa31a4ff3a5d36916cf941dd946c63ba3fee8f49266f559f001`
- Producer SHA-256:
  `4df50ac8a154bc7a8e89753ca9c66c2c606a065e6988c5ca836d2e68e616ca54`

### Limitations

The C,w rows remain supplied historical source moments and were not recomputed
under the new phase value. This remains a conditional diagnostic, not a
production MB baseline selection or publication result. Production phase
configuration remains null/unresolved.

## EVID-0086 - Adam plus central finite-difference diagnostic

Date: 2026-09-26

Status: CURRENTLY_VERIFIED_PASS FOR SYNTHETIC TEST; PHYSICAL TEST NOT RUN

### Claim

A new diagnostic runner exercised the same central finite-difference, sigmoid
chain rule, minimize-`-K` sign, Adam update, and rollback implementation on the
known synthetic objective. From `(nu,V_A)=(0.10,2.0)`, it reached
`(0.1702060383,2.201044144)` after 80 iterations, increasing the objective
from `-0.0249` to `-5.8757e-7`. The `dK/dnu` check at `(0.15,2.0)` was stable
at approximately `0.04` for `h={0.01,0.005,0.001,0.0005}`.

Physical Test 2 was not run: the requested 59-point dense grid and FD stencils
lack exact ensemble-matched C,w at 52 grid points and all requested stencil
neighbors. Interpolation/substitution was deliberately rejected. Therefore
joint physical Test 3 was also not run.

### Evidence and provenance

- `scripts/diagnose_mb_va_adam.py`, SHA-256:
  `4518377caf2ef5d56d93d01f972956752629f1d2a15f40b1bc71150772925788`
- `results/diagnostic_mb_va_adam/synthetic_adam_trace.csv`, SHA-256:
  `1caba1175922d6c7a98c59fa6a5d7e51f61aaadf91379b3e10ef4d780cc4d62b`
- `results/diagnostic_mb_va_adam/diagnostic_report.json`, SHA-256:
  `94977f115c65d4a867d1c397452630b74aceca0c07142511b49fa3fd375fdc3f`
- Focused diagnostic regression: 1 test passed.

### Interpretation

The optimizer machinery appears functional on the synthetic objective. No
claim is made that it optimizes the physical SKR, and no physical optimum,
baseline selection, training authorization, or publication result follows.

## EVID-0087 - Exact common-ensemble MB evaluator and bounded TEST2 readiness

Date: 2026-09-27

Status: CURRENTLY_VERIFIED_PASS FOR EVALUATOR/COARSE LANDSCAPE; FD FAILED; TEST2 NOT RUN

### Claim

`scripts/run_exact_mb_test2.py` now evaluates one physical MB ensemble through
MI, exact C4-Gram source moments, full-interval Holevo, and raw SKR. It enforces
`nu_mb_repo=42.5*nu_mb_raw`, hashes exact binary64 probabilities, amplitudes,
and declared `V_A`, and asserts that the MI, source-moment, and Holevo hashes
are identical. Exact-source cache keys additionally bind the convention,
source implementation hashes, numerical settings, and precision ladder. No
C,w interpolation or nearest-nu lookup is present.

At `V_A=2`, `tau_zen=0.92`, `zeta=30 deg`, `eta_AO=0.95`, and
`C_n,phase^2=9.4e-18 m^-2/3`, the seven-point exact coarse landscape is:

| nu_raw | I_AB | C | w | chi_BE | raw SKR |
|---:|---:|---:|---:|---:|---:|
| 0.10 | 0.00042842019939310917 | 1.4141975446461088 | 3.538218842527366e-05 | 0.0003322232140663406 | 7.477597535711312e-05 |
| 0.13 | 0.00043072331515805475 | 1.4142120065471502 | 3.6250314541869922e-06 | 0.0003291386390917861 | 8.004851030836592e-05 |
| 0.14 | 0.0004309175142386934 | 1.414212851188367 | 1.6856391238553004e-06 | 0.00032868367480354266 | 8.068796372321605e-05 |
| 0.15 | 0.000430916803569481 | 1.414213237782491 | 7.818684597230892e-07 | 0.00032837360185977715 | 8.099736153122978e-05 |
| 0.16 | 0.00043076173163427713 | 1.4142134144018956 | 3.618335204129278e-07 | 0.00032816236469268567 | 8.106128035987757e-05 |
| 0.17 | 0.000430485164097405 | 1.4142134949830283 | 1.6709139201083476e-07 | 0.00032801854487995996 | 8.094236101257479e-05 |
| 0.20 | 0.000429166963560057 | 1.4142135560377151 | 1.62655009052083e-08 | 0.00032780900654927336 | 7.989960883278077e-05 |

The coarse numerical maximum is `nu_raw=0.16`; it is not a continuous optimum
or baseline selection. Known exact rows at 0.10, 0.15, and 0.20 matched. The
prior 0.173421 terminal audit was not imported because it had no hash-bound
cache artifact.

The exact FD check around 0.16 failed readiness. For `h=0.01`,
`dK/dnu=-2.7500259327498024e-06` with paired CRN stderr
`2.3106529029621325e-04`. For `h=0.005`,
`dK/dnu=-3.42140000064565e-06` with stderr
`2.313213344921552e-04`. Both derivatives are unresolved and the two rows do
not meet the frozen local stability tolerance. Adam TEST2 therefore remained
`NOT RUN`; TEST3 remained `NOT RUN`.

### Historical correction

EVID-0084/EVID-0085 used raw-grid C,w rows but passed raw `nu` directly to the
repository canonical PMF. Their MI and source moments came from different
ensembles. Those cached-sweep SKRs are now
`SUPERSEDED_INVALID_COMMON_ENSEMBLE` and cannot support comparison or baseline
selection. The historical artifacts are preserved.

### Evidence and provenance

- `scripts/run_exact_mb_test2.py`, SHA-256:
  `645b2792b0d9eb38609d4e94a165f94b8a927f3d18997671099c4057bc21b2d4`
- `tests/test_exact_mb_test2.py`, SHA-256:
  `6cf5077f53e623f026f7c7fb7f18887c03ade1e63dd418dc66c2df13163fc775`
- `results/exact_mb_test2/run_report.json`, SHA-256:
  `48878f3e9783c465e3001ede06070a7a44e1d8910e06ecbe28434c4e26caadd7`
- `results/exact_mb_test2/coarse_landscape.csv`, SHA-256:
  `07b4c26636344fa5482a6e7dcb41c93ef9f7a89d92c28f2a9a0d70f12f841370`
- `results/exact_mb_test2/finite_difference.json`, SHA-256:
  `e0afe0a3735ce77fc5d440daa6b0b223a3808967871b8e7e0b936128a023dc38`
- Focused verification: 5 tests passed; `py_compile` passed.

### Scope

This is a bounded diagnostic under a conditional channel fixture. It changes
no source-moment mathematics, Adam implementation, security functional,
physical channel model, lifecycle gate, or baseline selection.

## EVID-0095 - Historical exact C,w distance envelope diagnostic

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR HISTORICAL-EXACT DIAGNOSTIC; NOT FINAL FIGURE

Using only current-compatible exact C,w rows from EVID-0094, the distance
diagnostic evaluated 8 Uniform candidates and 30 MB pairs with
`0.05 <= nu_raw <= 0.20`. No new C,w/AP/Fock/Gram calculation was run.

The channel/phase fixture was explicit and recorded in the report:
`tau_zen=0.92`, `C_n,phi^2=9.4e-18`, `eta_AO=0.95`, and
`T_eff=<sqrt(T_raw)>^2`; primary Holevo used `maximize_full_interval=False`.

Results:

```text
Uniform:       no sign change over 19--100 km; SKR remains negative
MB with AO:    bracket [31,33] km; linear estimate 31.409924920888173 km
MB without AO: no sign change over 19--100 km; SKR remains negative
```

The MB AO winner changes V_A with distance (for example, `V_A=2.15` at
19 km, `V_A=1.3833230303` near the zero crossing, and
`V_A=0.7416615151` from 37 km onward), while `nu_raw=0.20` remains the
winning historical MB parameter on the evaluated envelope.

This remains a diagnostic precursor: Uniform V_A coverage is sparse and not
globally optimized, PCS is represented by MB only, and Binomial has no safe
current-compatible exact C,w.

### Evidence and provenance

- `scripts/run_historical_exact_skr_vs_link_distance.py`, SHA-256:
  `aebcf0e39a285dc2c999fdced5fa7eba8028cba0c3611301b5c6b3c511880d94`
- `results/skr_vs_link_distance/historical_exact_distance_plot.png`, SHA-256:
  `0cc2e5b62bd64a7944a28316e1466c0fdf315f44f42dbba27651f2974e5011bf`
- `results/skr_vs_link_distance/historical_exact_distance_plot.pdf`, SHA-256:
  `9b9f05a5bf85613bfcbdeb176f6d603ba53803d6c67b1da11db5d0d17e92ada0`
- `results/skr_vs_link_distance/historical_exact_operation_distance_summary.csv`, SHA-256:
  `1bb3df27ee3f2040dd626180448a2dadba6d4601a249fb8346f3d5837bf51474`
- `results/skr_vs_link_distance/historical_exact_distance_report.json`, SHA-256:
  `0f421a9b75a027c61d2938039f7e2742bf1420fc124a2ae2bd54ab4e6ee1d1e6`

## EVID-0094 - Historical C,w source-moment inventory and reuse audit

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR READ-ONLY AUDIT; NO NEW SOURCE MOMENTS

The repository-wide audit searched structured text artifacts, CSV/JSON/YAML
records, source/cache directories, historical summaries, checkpoints, and
binary metadata without invoking the AP/Fock/Gram evaluator. It found:

```text
C,w records indexed:                 6876
hash-identifiable unique hashes:       77
unhashable C,w records:              6547
duplicate hash groups:                 75
current source-semantics exact rows:   79 (71 MB, 8 Uniform)
known superseded/wrong-AP-w rows:     148
```

The current `run_skr_vs_link_distance.py` roster contains 162 planned
family/parameter/V_A combinations; 146 are feasible ensembles under the
current peak constraint. Seven have safe current hash-bound source matches:
three Uniform rows and four MB rows. There are no safe Binomial matches. Thus
historical recovery covers `7/162 = 4.32098765%` of the planned combinations
(`7/146 = 4.79452055%` of feasible combinations) without new C,w work.

The seven current distance-roster matches are:

```text
Uniform: V_A = 0.1, 0.6, 4.0
MB:      (nu_raw,V_A) = (0.10,0.1), (0.10,4.0), (0.20,0.1), (0.20,2.1)
Binomial: none
```

Seventy-five duplicate groups show repeated source-only C,w copies across
summaries/distance-or-optimization artifacts; every audited duplicate group
has one unique C and one unique w (`max abs delta C = 0`, `max abs delta w = 0`).
This supports treating C,w as ensemble-bound rather than distance-bound, but
does not authorize migration of any historical row with missing or superseded
semantics.

### Reuse boundary

- `SAFE_EXACT_REUSE`: only the seven current hash-bound roster matches.
- `SAFE_AFTER_HASH_RECONSTRUCTION`: none.
- `NEEDS_ONE_POINT_VALIDATION`: historical records with partial metadata; not
  imported into the active cache.
- `UNSAFE_SEMANTICS_MISMATCH`: 148 rows carrying superseded/wrong-AP-w status,
  including the old cached Uniform/Binomial/MB smoke artifacts.
- `NO_MATCH`: the remaining current candidates.

### Evidence and provenance

- `scripts/audit_historical_source_moments.py`, SHA-256:
  `21f7eafbf4603f163773a97b28a4f89c09e4492c292e3a1c68a0893c76f89d82`
- `results/skr_vs_link_distance/historical_source_moment_audit.csv`, SHA-256:
  `a135056fdd33439911a490b617b5f4ba9d70ac423af1bb93e4052a8aa2e04269`
- `results/skr_vs_link_distance/historical_source_moment_matches_current.csv`, SHA-256:
  `17ad3e71d2d70c65e2bea672c29bb5a4cb7aaa7442d033d8ec1a4b9234a3b6a7`
- `results/skr_vs_link_distance/historical_source_moment_duplicates.csv`, SHA-256:
  `079cd22c72794bc402c437c0d6637ba36eaa41328f4448c3123d32a922ef3edd`
- `results/skr_vs_link_distance/historical_source_moment_audit.json`, SHA-256:
  `d2d9bad14f933b15ddbb60d5d9fd6a701c9d2102190f5dfa9e6dbf987aaa7d06`
- `scripts/report_historical_mb_exact_pairs.py`, SHA-256:
  `e06a0647776873fd62ca2b23646bc883ef5caac9f19811e1bda57b02a480ea36`
- `results/skr_vs_link_distance/historical_mb_exact_pairs.csv`, SHA-256:
  `e87e7f5a3c278f2a2a73bddc3c1a3a5e6ccbcb2e856aeb9c3d14d8d9cfd31e7e`
- `results/skr_vs_link_distance/historical_mb_exact_nu_summary.csv`, SHA-256:
  `51a50140da44ac48ceaf29560f6cfc2fad07019ff5da58e5bb0b8e3522b43b55`

No active exact cache was modified. No new C,w, AP/Fock/Gram evaluation,
training, baseline selection, or publication-scale run occurred.

## EVID-0093 - Exact AP coverage batch with fail-closed timeout ledger

Date: 2026-09-28

Status: BLOCKED_BY_ENVIRONMENT; GLOBAL OPTIMUM UNRESOLVED

The authorized exact AP coverage runner processed the high-priority local,
boundary, and uniform rosters using the shared hash-bound source cache. It
preserved the frozen channel, positive-PMF MB convention, V_A-dependent noise,
deterministic GH MI, exact C4/AP source moments, full Holevo, and common
ensemble identity. No interpolation, surrogate, Monte Carlo production MI,
Adam, or model/security change was used.

The completed exact coverage after the batch is:

```text
global grid:   19 / 143 exact
local mesh:    26 / 59 exact
boundary:       9 / 18 exact
uniform:        8 / 43 exact
cache files:   76 exact source JSON files
```

The remaining AP jobs failed closed or remain absent. The source path has a
fixed one-hour subprocess timeout (`timeout=3600` in
`src/cvqkd/gram_moments.py`); completed failures report
`full-support fallback failed closed: fallback timeout`. The runner now emits
per-stage `*_failed_or_incomplete.csv` ledgers and keeps all successful source
files restartable in the shared cache.

The best exact interior point remains:

```text
(nu_raw,V_A) = (0.24,1.95)
SKR          = 2.1544608008872113e-05
P_peak       = 26.325014686064186
```

The best exact boundary point currently available is:

```text
nu_raw       = 0.275
V_A          = 1.939393833980765
SKR          = 2.1507318654867557e-05
P_peak       = 30.0
```

The best exact uniform point currently available remains `V_A=0.1` with
`SKR=-4.485409326324686e-05`; it is not an optimized uniform baseline.
Therefore the classification remains `GLOBAL_OPTIMUM_UNRESOLVED` and no
boundary scalar refinement or baseline gain claim is valid.

### Evidence and provenance

- `scripts/run_joint_mb_va_ap_coverage.py`, SHA-256:
  `bae177f79fdb5790f3cb4b0b354edb53eb74eace10e9086cce7d82e507ff733c`
- `results/joint_mb_va_global/run_report.json`, SHA-256:
  `38c803ce37174de555f604d2eec38b48a4f3cd068f6ae41b3c0023c13e9cf227`
- `results/joint_mb_va_global/global_landscape.csv`, SHA-256:
  `d184d35f96bf3739d9e04b95dedc08d686bf149752d0a55ea2a17efa761767b4`
- `results/joint_mb_va_global/boundary_search.csv`, SHA-256:
  `077e4d79ffc15f2c82a29638678eef43364c580991e6b722430fc697b226ae02`
- `results/joint_mb_va_global/uniform_optimized_baseline.csv`, SHA-256:
  `bf59204a7bbeb4d1e27a3b4d60d868d2e3c511f370413cb78d13b6a2b62bb464`
- `results/joint_mb_va_global/ap_coverage/local_report.json`, SHA-256:
  `bb69aed93bc94f78b7272110de5afd30e132e0ae23764b12f461238d90f5c031`
- `results/joint_mb_va_global/ap_coverage/local.csv`, SHA-256:
  `af291a9f83410d8f0b1dcad834a39a1e3915052a1d1031c4de7f21282f47808c`
- `results/joint_mb_va_global/ap_coverage/local_failed_or_incomplete.csv`, SHA-256:
  `003d75de01f2e21a72fb6f0f5331a98a3768d0f269b70448f2fe6c9b5663144c`
- `results/joint_mb_va_global/ap_coverage/ap_batch_timeout_summary.json`, SHA-256:
  `6b67d48013bbeb36b78316a7e9c9f45e1d60842fc197dc434e41c4b4a8e68d66`
- `results/joint_mb_va_global/ap_coverage_boundary/boundary_report.json`, SHA-256:
  `277b01f6577632d214db7c9f33e4838e374d40721c2200a5f6edd8c4a6b5e50b`
- `results/joint_mb_va_global/ap_coverage_boundary/boundary.csv`, SHA-256:
  `ced0f31666f0f49a443d78f15c4244beca9c569705ad9b6a32ce188f1eb70f9f`
- `results/joint_mb_va_global/ap_coverage_boundary/boundary_failed_or_incomplete.csv`, SHA-256:
  `943080f16165f80a761ad2cdc29d489803e9515682364daa833bfdd71a004733`
- `results/joint_mb_va_global/ap_coverage_uniform/uniform_report.json`, SHA-256:
  `7d92d8bd1d47264e50a2535e8bd8155ee543643206e1b4a7ec7561332022e2b0`
- `results/joint_mb_va_global/ap_coverage_uniform/uniform.csv`, SHA-256:
  `b8ae1a66220747a92b824398ed73d28280fac017a9e54cb84ee7dfe74eeee388`
- `results/joint_mb_va_global/ap_coverage_uniform/uniform_failed_or_incomplete.csv`, SHA-256:
  `04e839f9f0a547ab9748c118b4e6b53c4512dc2db40a46421ec4b15fbf903776`

15 focused tests passed (9 exact-MB/reconciliation and 6 global-joint), and
the AP coverage runner compiled. No physical/security equation, precision
ladder, peak limit, PMF positivity rule, or lifecycle state changed.

## EVID-0092 - Fail-closed global joint MB/V_A coverage diagnostic

Date: 2026-09-27

Status: CURRENTLY_VERIFIED_PASS FOR CACHE-BOUND DIAGNOSTIC; GLOBAL OPTIMUM UNRESOLVED

The authorized follow-up ran a deterministic feasible-domain cache-bound scan
for the exact joint objective. It retained the frozen `nu_repo=42.5*nu_raw`
MB convention, recomputed `epsilon_total=epsilon_base+c_phi*V_A`, used
deterministic GH MI and exact hash-bound C4/AP source moments, and preserved
the common MI/source/Holevo ensemble. No interpolation, surrogate, Gaussian
capacity, or Adam was used.

The runner emitted the required global artifacts, but deliberately stayed
cache-only because an exact source-moment miss is not silently substituted.
Coverage is:

```text
global feasible grid: 143 requested / 15 exact
boundary grid:        18 requested / 5 exact
uniform scan:         43 requested / 5 exact
fresh AP points:       0
classification:        GLOBAL_OPTIMUM_UNRESOLVED
```

The best exact point available across the prior joint landscape/local
refinement and this diagnostic remains:

```text
(nu_raw,V_A) = (0.24,1.95)
SKR          = 2.1544608008872113e-05
I_AB_GH      = 3.5845686947766353e-4
chi_BE       = 3.189894179949082e-4
P_peak       = 26.325014686064186
```

The best exact boundary point currently available is `(0.25,2.133332719960486)`
with `SKR=2.1311057548123425e-05`; the best exact uniform point currently
available is `(nu_raw,V_A)=(0,0.1)` with negative `SKR=-4.485409326324686e-05`.
Neither is a certified global boundary or optimized uniform baseline because
the requested surrounding exact points are missing.

Gauss-Hermite orders 8, 16, 32, and 64 agree at the retained targets to
absolute differences no larger than `1.7763568394002505e-15` in the emitted
convergence artifact. The 6 focused tests pass; compilation and
`git diff --check` pass.

### Evidence and provenance

- `scripts/run_joint_mb_va_global_certification.py`, SHA-256:
  `4d73d6cf62c3a159b9be86193c9f42460fcbb9a71a6a2ff27e8fbb8823111778`
- `scripts/run_joint_mb_va_optimization.py`, SHA-256:
  `50a3e2b2d29c6bffb6b7ca95fd6a06e76e36675a0cfc7a4843ca184b58118f06`
- `tests/test_joint_mb_va_global_certification.py`, SHA-256:
  `707e9ff7d906f6adc5bcb087c72a644fe85fc265293f286e152dcfb196a6e316`
- `results/joint_mb_va_global/run_report.json`, SHA-256:
  `d2b5fb0f1eb7c8ae98b5ca386a883b9c1bff0c7aa8ab070435b9598e7045d7a7`
- `results/joint_mb_va_global/global_landscape.csv`, SHA-256:
  `a31007ffa9dd16c86f4a8434513dcc8470495abec3583a50abc4da2a243bc7b3`
- `results/joint_mb_va_global/feasible_boundary.csv`, SHA-256:
  `e755f0ce697e496daa65c943a73949007db568dad4581de2dee0ad228c7fe96c`
- `results/joint_mb_va_global/boundary_search.csv`, SHA-256:
  `0f30db2964fec0eed13e36e8430b6a78d7932607ab4162001ba2eea416bed75c`
- `results/joint_mb_va_global/interior_search_log.csv`, SHA-256:
  `fea7714606a7011436dd44fd00d567f48a43e63cbc22b6400661a856febd3001`
- `results/joint_mb_va_global/uniform_optimized_baseline.csv`, SHA-256:
  `a9c7a93c6c45518e90034d1094a37577c1238edfd7a8da1d85c8d1b935bf210`
- `results/joint_mb_va_global/local_refinement.csv`, SHA-256:
  `65474704c8f529801669cc7697d84297fb1858b7420c0383cd20937369e1edc8`
- `results/joint_mb_va_global/optimum_certification.csv`, SHA-256:
  `b3e0945c012b366775bd7f0845a214ed760fa5bf71ade1c4118f306891ffa35`
- `results/joint_mb_va_global/objective_decomposition.csv`, SHA-256:
  `ce5dbac070860cea2298b910a58d18d68d72e915a9aa6c2ca33095d06bb937fa`
- `results/joint_mb_va_global/gh_convergence.csv`, SHA-256:
  `054d224259ae0493498dfca5cee2ac37521665f5d06b4216595a3bd38142c0a6`

No physical/security equation, peak limit, PMF positivity rule, lifecycle
state, or baseline-selection claim changed.

## EVID-0091 - Authorized exact joint MB/V_A landscape and local refinement

Date: 2026-09-27

Status: CURRENTLY_VERIFIED_PASS FOR JOINT LANDSCAPE; GLOBAL OPTIMUM UNRESOLVED

The authorized joint stage evaluated the curved feasible region
`V_A,max(nu)=min(V_A_config_max, 2*n_peak*m2(nu)/|x_max|^2)` with deterministic
GH MI, V_A-dependent post-action noise, exact hash-bound C4/AP source moments,
and full-Z Holevo. No interpolation, surrogate, or Adam was used.

The sparse 25-point grid's best row was near `(nu_raw,V_A)=(.20,2.025)` with
`SKR=2.14336794e-05`. Exact local refinement found

```text
(nu_raw,V_A) = (0.24,1.95)
SKR          = 2.1544608008872113e-05
I_AB_GH      = 3.5845686947766353e-4
C            = 1.3876689082607805
w            = 1.0292981533840356e-9
Z_star       = 0.04430689348631826
chi_BE      = 0.0003189894179949082
epsilon_total=0.02911275902783573
peak_photon  = 26.325014686064186
```

The local stencil has lower SKR at `nu=.23,.25` with `V_A=1.95` and at
`V_A=1.925,1.975` with `nu=.24`. This supports a local interior candidate,
not a global optimum. The sparse global domain and uniform optimized baseline
are not fully certified.

The fixed-V_A=2 MB sweep is only a diagnostic slice: changing V_A materially
changes MI, phase noise, peak feasibility, C,w, and Holevo.

The author authorization is recorded in
`results/exact_mb_asymptotic/author_authorization.json`; global publication
lifecycle remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence and provenance

- `scripts/run_joint_mb_va_optimization.py`, SHA-256:
  `7589d10311f62e10d2065f00f0a9643860c4b021dde162cdc50748c4708a100f`
- `scripts/run_joint_mb_va_local_refinement.py`, SHA-256:
  `8f01b4362f688d7c170dd4c6110824dfcb1829a48ae308b9d396aba894fea997`
- `results/joint_mb_va/run_report.json`, SHA-256:
  `d1bb963343216014a47fb3c949ae0228815668c885a2875941a6d5bfebfa7cad`
- `results/joint_mb_va/feasible_boundary.csv`, SHA-256:
  `47b88082288f58a6fdd4f23b7b3189b2c55b0582f49b98b56e82442689c1c67b`
- `results/joint_mb_va/joint_landscape.csv`, SHA-256:
  `4998143831eb0a10625c41dd619c7e4ead6c3aace6e875e4219e7905a3c7365a`
- `results/joint_mb_va/local_refinement.json`, SHA-256:
  `d3742a4bf340d52899139acc9e107c6920c155214ca2eaaa96c4a3882a0f7d65`
- Focused joint verification passed; no physical/security equations changed.

## EVID-0090 - Authorized exact-MB boundary/asymptotic landscape

Date: 2026-09-27

Status: CURRENTLY_VERIFIED_PASS FOR AUTHORIZED SUB-STAGE; FINITE OPTIMUM UNRESOLVED

### Authorization

The author explicitly authorized `EXACT MB OPTIMIZATION AND ASYMPTOTIC
CERTIFICATION` only. Publication-scale runs, physical/security model changes,
Adam, interpolation, surrogates, and broader optimization remain excluded.
The authorization is recorded in
`results/exact_mb_asymptotic/author_authorization.json`; the global lifecycle
remains `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Extended finite-positive-PMF landscape

Exact hash-matched source moments and deterministic GH MI were evaluated at
`nu_raw={0.20,0.22,0.25}`. SKR continued increasing:

| nu_raw | C | w | Z_star | chi_BE | SKR | H_X | N_eff |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.20 | 1.4142135560 | 1.62655e-08 | 0.0451540702 | 3.278090e-04 | 2.145554e-05 | 5.4161 | 42.70 |
| 0.22 | 1.4142135610 | 3.46869e-09 | 0.0451543360 | 3.277579e-04 | 2.150663e-05 | 5.2786 | 38.82 |
| 0.25 | 1.4142135618 | 1.60865e-09 | 0.0451544087 | 3.277439e-04 | 2.152061e-05 | 5.0942 | 34.16 |

At `nu_raw=0.30`, the unchanged hard peak constraint rejects the normalized
ensemble because `max|alpha|^2=33.75000034 > n_peak=30`. The same fail-closed
physical boundary rejects `.35`, `.40`, and `.50`; the raw-to-repo helper was
expanded to accept those finite nonnegative parameters so this is not an
artificial parameter-range stop.

No turnover was found before the physical boundary. A finite interior bracket
was not established; no bounded scalar optimizer was run.

### Asymptotic reduced-support diagnostic

The actual minimum-energy shell contains four points with raw coordinates
`(+-0.5,+-0.5)`. Under fixed `V_A=2`, the reduced-support diagnostic becomes
the QPSK-like physical geometry `(+-1/sqrt(2),+-1/sqrt(2))` with scale
`sqrt(85)`. A separate dense-Fock cutoff-64 diagnostic returned
`C=1.25985255`, `w=0.11873224`, `Z_star=0.03889244`,
`chi_BE=0.00124983`, and `SKR=-9.00561e-4`.

This is explicitly an `ASYMPTOTIC_DIAGNOSTIC_NOT_PRODUCTION_FINITE_NU` result.
It is not substituted for the strictly positive-PMF production C4/AP path.
The discrepancy from the finite-positive-PMF trend is retained as a support-
boundary discontinuity question; no asymptotic K-infinity claim is made.

### Evidence and provenance

- `scripts/run_exact_mb_asymptotic.py`, SHA-256:
  `d7993edb8f91db94ebe3222e76cb026ee85e9d954f5f153850e10d35713dae1c`
- `results/exact_mb_asymptotic/author_authorization.json`, SHA-256:
  `6a69ed33ec08fb02ac4dea99f25c9ddbd067bf886dac0e5ca30bdebca69b5be6`
- `results/exact_mb_asymptotic/extended_landscape.json`, SHA-256:
  `9f04348f55b3b7752f03da3c586a34baa89c65d76afba5ab3782ce4e71911442`
- `results/exact_mb_asymptotic/extended_landscape.csv`, SHA-256:
  `2302ae130efcd1ab2fb37947168b045c164671335531f7891c7c93e546d3d3c6`
- `results/exact_mb_asymptotic/asymptotic_four_state_diagnostic.json`, SHA-256:
  `d8e18dd368b9b597866805453599eedbd067bf886dac0e5ca30bdebca69b5be6`

## EVID-0089 - Same-point MI reconciliation and deterministic-SKR coarse correction

Date: 2026-09-27

Status: CURRENTLY_VERIFIED_PASS; RECONCILIATION_DIAGNOSTIC_ONLY

### MI reconciliation

The old seven-point coarse MI values were recomputed using the same physical
ensemble hashes, PMF, amplitudes, `T`, `epsilon_total`, `sigma_c2`, and
heterodyne convention as the deterministic GH evaluator. The old 2048-sample
means reproduced to floating-point precision. The old coarse MI variation was
not statistically resolvable: the maximum reconstructed deviation was
`2.742` standard errors, so the historical MI column is classified
`STOCHASTIC_COARSE_ONLY`.

The independent 65536-sample MC cross-check agrees with GH; the maximum
`(I_MC-I_GH)/stderr` magnitude is `0.3857`. The fixed-V_A low-SNR leading
term is nearly invariant across MB shaping: `I_AB_GH` stays approximately
`0.0003676468876` while entropy, fourth moment, C,w, and Holevo vary.

### Corrected deterministic-SKR coarse values

Replacing old stochastic MI with deterministic GH MI while retaining only
hash-matched C,w/Holevo rows gives:

| nu_raw | old SKR | deterministic SKR |
|---:|---:|---:|
| 0.10 | 7.4775975e-05 | 1.7041329e-05 |
| 0.13 | 8.0048510e-05 | 2.0125904e-05 |
| 0.14 | 8.0687964e-05 | 2.0580868e-05 |
| 0.15 | 8.0997362e-05 | 2.0890941e-05 |
| 0.16 | 8.1061280e-05 | 2.1102179e-05 |
| 0.17 | 8.0942361e-05 | 2.1245998e-05 |
| 0.20 | 7.9899609e-05 | 2.1455537e-05 |

The deterministic coarse maximum moves to `nu_raw=0.20`; this remains a grid
diagnostic, not a continuous optimum.

### Point-evaluator readiness and lifecycle boundary

The existing common evaluator can create arbitrary exact MB ensembles and
compute C,w,Z*,chi_BE through the exact cache/AP path, so
`FULL EXACT SKR POINT EVALUATION: READY`. A Holevo derivative is not required
for a derivative-free bounded scalar search. That search was nevertheless not
run because optimized-MB search/baseline selection is not authorized by the
current lifecycle state `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.

### Evidence and provenance

- `scripts/run_exact_mb_reconciliation.py`, SHA-256:
  `cfde6563ba9aeb61a2d445e13a368ce87982697ca5c74dabc5213e6f3952365a`
- `tests/test_exact_mb_reconciliation.py`, SHA-256:
  `3eaa8e2601fb52be127b87cf71147298179ba4a4a313ead0ff26fe98d3bac1be`
- `results/exact_mb_reconciliation/run_report.json`, SHA-256:
  `834a100f547e091800b96763fb97a236a67dc1ff6e719ac639ff511a32bd6e2f`
- `results/exact_mb_reconciliation/same_point_reconciliation.csv`, SHA-256:
  `74d9837cfae3c3ac1a13d635fd39a9045b179d512d8b08a3222e76ce6f31388b`
- `results/exact_mb_reconciliation/low_snr_diagnostics.json`, SHA-256:
  `5374c34a88b0842b1432ac8e995cca84656fa8b50bb8e369b239d2dc4d6a9376`
- `results/exact_mb_reconciliation/wide_gradient.json`, SHA-256:
  `94187fa17cef4c53727f73b6be286ca06ed5bbf4889bce6d39452148801a8cad`
- Focused verification: 15 tests passed; `py_compile` passed.

## EVID-0088 - Deterministic Gauss-Hermite MI and raw-nu autodiff certification

Date: 2026-09-27

Status: CURRENTLY_VERIFIED_PASS; DETERMINISTIC_MI_CERTIFIED; DIAGNOSTIC_ONLY

### Claim

The repository now has a deterministic float64 mutual-information evaluator in
`src/cvqkd/mutual_information.py`. It uses the existing conditional complex
Gaussian likelihood and Gauss-Hermite quadrature, with no random channel-noise
samples. The existing Monte-Carlo evaluator remains unchanged for independent
cross-checking.

The certified chain is

```text
nu_raw -> nu_repo=42.5*nu_raw -> canonical MB PMF
-> probability-dependent physical amplitude normalization
-> deterministic I_AB -> dI_AB/dnu_raw
```

The actual 256-state ensemble is exactly Cartesian 16-PAM x 16-PAM and its MB
PMF factorizes. Full 2-D deterministic MI and the exact 2x1-D product path
agreed at all tested `nu_raw={0.10,0.15,0.16,0.17,0.20}`; the largest absolute
difference was `2.702211284594247e-15`. The selected smallest converged
quadrature order was `N_GH=8` over tested orders `8,16,24,32,48,64`.

Autodiff derivatives at `nu_raw={0.15,0.16,0.17}` agreed with central
differences through `h=1e-4` under absolute tolerance `1e-9`; the derivative
is numerically near zero in this very-low-transmittance fixture, so relative
error is not used at the near-zero rows. The analytical PMF derivative and the
raw-to-repo factor `42.5` also passed.

The independent MC cross-check used the existing evaluator, the same five CRN
seeds, and `65536` samples per symbol only for validation. The largest
absolute GH/MC difference in standard-error units was `0.3857`.

### Required boundary

No C,w interpolation was added. No Holevo/security equation, phase model,
channel model, Adam implementation, or common-ensemble contract was changed.
The full-SKR bounded search and Adam remain `NOT RUN`; optimized-MB search is
still lifecycle-gated and this result does not select a baseline or continuous
optimum.

### Evidence and provenance

- `src/cvqkd/mutual_information.py`, SHA-256:
  `4c7d38d7f796dde0e24155117d17ca5758e9561527f4acb29fc24d9bb7e947b4`
- `scripts/run_exact_mb_test2a.py`, SHA-256:
  `946311e82e79a08803307b270b4de2df83ef026f4d27a713e96e6da868cbafd2`
- `tests/test_exact_mb_test2a.py`, SHA-256:
  `5049a2c2ec5f5a9b423e2ab41cc395cefb6a86765f6d929530714da5fcdc1c57`
- `results/exact_mb_test2a/run_report.json`, SHA-256:
  `abebb82fcf3090d8cac32f7d2fed13d370465972a4e4250238b728f12e2fba3a`
- `results/exact_mb_test2a/gh_convergence.csv`, SHA-256:
  `f96e8da220e5486b6e1f0f9763919aec0f4ae38cfc0d5e4d495d36c55ae18997`
- `results/exact_mb_test2a/autodiff_vs_fd.csv`, SHA-256:
  `63bcf5a42a2ff99b7b60352acf8f81a7e9de40c94b82f7d8f26cc233bde5c7e7`
- `results/exact_mb_test2a/mc_vs_gh.csv`, SHA-256:
  `4ebda74fb20b3386d26142dfa303aee6691f272eafb0ff0f197aa4ee4c7f98a4`
- Focused verification: 13 deterministic-MI/mutual-information tests passed;
  `py_compile` passed.
## EVID-0096 - Historical exact receiver-aperture sensitivity stop diagnostic

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR APERTURE STOP DIAGNOSTIC; FULL SWEEP NOT RUN

Using only the audit-approved historical exact source moments, the diagnostic
tested receiver diameters `0.08, 0.10, 0.12, 0.14, 0.16 m` at the minimum
physical distance `L=19 km`. It evaluated 8 Uniform candidates and 30 MB
candidates with `0.05 <= nu_raw <= 0.20`; no new C,w/AP/Fock/Gram calculation
was run and no candidate evaluation failed.

The active fixture remained `tau_zen=0.92`,
`C_n,phi^2=9.4e-18`, `eta_AO=0.95`, `beta=0.95`,
`epsilon_ch=0.0186`, `T_eff=<sqrt(T_raw)>^2`, and
`maximize_full_interval=False`. The repository convention was preserved:
`aperture_radius_m` is the receiver radius and finite-aperture scintillation
receives diameter `D_r=2r`.

At `L=19 km`, no tested diameter made all three envelope SKRs positive:

```text
D_r (m)   Uniform SKR       MB with AO SKR       MB without AO SKR
0.08     -5.08556989e-05    3.26201781e-05      -6.03780295e-05
0.10     -7.60479161e-05    5.51461198e-05      -9.04189521e-05
0.12     -1.05488559e-04    8.43472085e-05      -1.25585354e-04
0.14     -1.38940590e-04    1.20500632e-04      -1.65604585e-04
0.16     -1.76201031e-04    1.63837593e-04      -2.10242997e-04
```

Consequently the requested full distance sweep was not launched, and no
selected aperture or operation-distance estimate was produced. The raw-tail
audit returned `P(T_raw>1)=0` for all five tested apertures at this distance.

### Evidence and provenance

- `scripts/run_historical_exact_aperture_diagnostic.py`, SHA-256:
  `cf1d5899436b9abd64f8b2926525cca7ebca7fc82ad4057767198935241b1423`
- `results/skr_vs_link_distance/aperture_all_positive_diagnostic/aperture_sensitivity.csv`, SHA-256:
  `0d4415e394c266badf6738b8a434e68dec1f7092a718b519a4555ce9be064bb4`
- `results/skr_vs_link_distance/aperture_all_positive_diagnostic/selected_aperture_metadata.json`, SHA-256:
  `7d17e443222385e1a32f859ac872de5f5f9a975224322a2e9a687ca3fb06c699`
- Verification: runner exit code 0; `py_compile` and `git diff --check` passed.
## EVID-0097 - Historical exact phase-noise sensitivity and stop diagnostic

Date: 2026-09-29

Status: CURRENTLY_VERIFIED_PASS FOR PHASE SENSITIVITY; ALL-POSITIVE THRESHOLD NOT FOUND

The receiver aperture was returned to the original baseline
`r_ap=0.04 m`, `D_r=0.08 m`. Using the same 8 historical exact Uniform and
30 historical exact MB candidates, the diagnostic changed only
`C_n,phi^2` and evaluated the 19-km point. No new C,w/AP/Fock/Gram source
moment was computed.

The fixed fixture was `tau_zen=0.92`, `epsilon_ch=0.0186`, `beta=0.95`,
`eta_AO=0.95`, `T_eff=<sqrt(T_raw)>^2`, and direct-Z
`maximize_full_interval=False`. The channel value was
`T_eff=2.9529598841299403e-4` and `P(T_raw>1)=0` at 19 km for every phase
value because the current channel path does not make attenuation depend on
`C_n,phi^2`.

At the current `C_n,phi^2=9.4e-18`, the winning rows were:

```text
Uniform      AO on   nu=0,   V_A=0.10  beta I_AB=2.02358416e-05  chi_BE=7.10915405e-05  K=-5.08556989e-05
MB with AO   AO on   nu=.20, V_A=2.15  beta I_AB=4.35004220e-04  chi_BE=4.02384041e-04  K= 3.26201781e-05
MB no AO     AO off  nu=.20, V_A=.10  beta I_AB=2.02358176e-05  chi_BE=8.06138471e-05  K=-6.03780295e-05
```

The phase-only sweep was:

```text
C_n,phi^2       Uniform K       MB+AO K        MB-noAO K
9.4e-18        -5.08557e-05    3.26202e-05   -6.03780e-05
7.0e-18        -5.05413e-05    3.88918e-05   -5.45644e-05
5.0e-18        -5.02793e-05    4.51464e-05   -4.97341e-05
3.0e-18        -5.00172e-05    5.16788e-05   -3.33088e-05
2.0e-18        -4.98862e-05    5.53004e-05   -1.61936e-05
1.0e-18        -4.97551e-05    5.89395e-05    1.03169e-05
```

Thus `C_nphi2_all_positive_threshold` was not found. At `1e-18`, Uniform
remains negative with `beta I_AB=2.0235842663529624e-05`,
`chi_BE=6.99909819751876e-05`, and
`K=-4.975513931165798e-05`; MB-with-AO and MB-without-AO are positive. The
requested full distance sweep was not run.

### Evidence and provenance

- `scripts/run_historical_exact_phase_sensitivity.py`, SHA-256:
  `84cbaa5a254cfecd79750b982491766d73673429c1c6411ee2a1c92c1cc6c4f2`
- `results/skr_vs_link_distance/phase_noise_sensitivity/phase_sensitivity.csv`, SHA-256:
  `0094339caa4a8f9ae0c21dfab2526207a2940ab705f8923c4a774cd6a6da5715`
- `results/skr_vs_link_distance/phase_noise_sensitivity/phase_sensitivity_report.json`, SHA-256:
  `c2348287a820005670da79fee4e4451f158c649bb358120665c29ee830898481`
- Verification: phase runner exit code 0; artifact assertions and `py_compile` passed.
