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

Status: ACTIVE, PENDING COMMIT

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

Supersedes EVID-0013 after commit.

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

Status: EXPERIMENTAL / PROPOSED, FAIL-CLOSED

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

Not superseded.

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
