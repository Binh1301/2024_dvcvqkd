# Publication experiment protocol

Status: preregistered workflow and output contract only. Publication-scale
training must not begin until every unresolved entry in
`AUTHOR_NUMERICAL_DECISIONS.md` is author-approved and the preregistered finite
fixture diagnostics have selected defensible numerical settings. Those finite
diagnostics do not certify a learned domain. After training and validation
selection, final held-out evaluation remains blocked until convergence passes
for the exact enumerated, hash-bound selected ensembles/checkpoints.

## Dataset generation and split separation

Generate `T` only through the frozen HAP--UAV FSO channel and generate
`epsilon` independently from the declared bounded-uniform sensitivity law.
The independence assumption is explicit because no measured or mechanistic
coupling is available. Use the frozen train/validation/test base seeds and
namespaced streams. Save exact state arrays, metadata, seeds, and SHA-256
hashes. The split validator must reject equal base seeds, realization hashes,
or exact state-pair overlap.

Training uses iid train streams only. Validation and test realizations are
fixed. Test channel states and test AWGN must not be loaded by baseline search,
hyperparameter selection, stopping, checkpoint selection, convergence-setting
selection, or failed-run triage.

## Numerical settings and baseline selection

1. On validation states, run the dedicated nested-sample MI convergence grid
   with all preregistered replication seeds. Reuse each nested noise stream
   across transmitter configurations and require the largest-count reference
   estimates to agree across replications within the declared tolerance.
2. On preregistered validation bad/medium/good states and transmitter cases,
   run Fock convergence for `C,w,Z,chi_BE` and trace error, including the
   synthetic C4 boundary fixture at the author-approved
   `|alpha|=sqrt(n_peak)` physical limit.
   This finite fixture suite is a precheck only and must not claim learned-domain
   coverage. After selection, rerun/certify every baseline ensemble and learned
   checkpoint for MI and Fock convergence with
   `validate_selected_roster_convergence.py`. First write a
   `selected-convergence-roster-v1` artifact conforming to
   `schemas/selected_convergence_roster.schema.json`; it contains only the
   already frozen config, validation-state, selections, and checkpoint roster
   and therefore does not need a not-yet-created convergence hash. Hash-bind
   that exact roster into
   all MI/Fock/threshold artifacts and combined evidence. The canonical roster
   hash excludes only the not-yet-created convergence artifact binding, avoiding
   a hash dependency cycle while retaining config/state/selection/checkpoints.
3. Run the dedicated density-eigenvalue/pseudoinverse threshold sensitivity
   audit for `C,w,Z,chi_BE`; bind its evidence to the same selected roster.
4. Freeze the common MI sample counts and Fock cutoff before any final test.
5. Search Uniform and Binomial over the same feasible fixed-`V_A` grid.
6. Search fixed MB over that same `V_A` grid using the preregistered reference
   `nu_MB`.
7. Search optimized MB over the Cartesian product of the preregistered `nu`
   and feasible `V_A` grids.

All candidate scores are validation raw average SKR, evaluated with common
random numbers. Fixed policies require `V_A<=V_A_budget`; all candidates also
obey the common `[V_min,V_max]` box and identical hard
`max_i|alpha_i|^2<=n_peak` rule. Peak-infeasible candidates are recorded as
ineligible, not clipped or scored. If any mandatory benchmark has no feasible
candidate, the comparison remains blocked. Ties prefer lower `V_A`, then lower `nu`.
The selection artifact records `test_set_used:false` and the validation state
hash.

The fixed-variance learned modes (PS, GS, and PS+GS) use
`scripts/select_learned_fixed_va.py` for a separate validation-only selection
over the identical feasible `V_A` grid after matched training runs. The
selector requires the complete preregistered seed set for every candidate,
one common training-protocol hash, validation-budget feasibility, and records
with no test fields. The training runs themselves are publication-scale work
and are not executed by this parameter-freeze task.

## Learned-model training and checkpoint selection

Run every learned ablation for every preregistered initialization seed using
the identical train channel/AWGN stream schedule. Use raw expected SKR, never
statewise positive clipping. Adaptive-VA modes use the projected energy dual;
the objective and energy constraint use the same state weights. The primary
run has all geometry-regularizer coefficients zero.

Validate once per epoch. Preserve the exact highest raw-SKR checkpoint among
checkpoints satisfying the complete-validation average `V_A` budget and hard
peak domain. Adaptive policies use the preregistered test-blind rule
`mean_validation(V_A)+margin<=V_A_budget`; fixed policies use their exact VA.
Each proposed optimizer update is accepted only if its final
physical ensemble remains peak-feasible on the training batch; otherwise both
model and Adam state are rolled back. Stop only
by the frozen maximum epoch or validation-patience/minimum-delta rule. Account
for every attempted seed and retain failed-run diagnostics rather than silently
discarding failures.

## Final held-out evaluation

Training commands cannot construct test states. After code, data hashes,
baselines, hyperparameters, checkpoints, numerical settings, and analysis
rules are frozen, create a `publication-selection-manifest-v1` artifact conforming
to `schemas/publication_selection_manifest.schema.json`. Only the manifest-gated
`scripts/evaluate.py` may then construct the held-out realization. It accepts
no free seeds, counts, checkpoint path, or analysis choices. Evaluate each
selected learned scheme once. Evaluate Uniform, Binomial, fixed MB, and
optimized MB through `scripts/evaluate_baseline.py`, which reads the selected
`(V_A,nu)` directly from the hash-bound baseline artifact. Both evaluators use
the identical manifest-controlled test state and AWGN streams.
Before any held-out invocation, run `scripts/validate_publication_manifest.py`;
it verifies the resolved configuration, baseline and learned-selection
artifacts, convergence evidence, environment lock, attempted-seed accounting,
the exact seven-mode-by-seed checkpoint roster, and every checkpoint against
their preregistered hashes, complete-validation maximum symbol energy, and
common peak-feasibility attestation.
Before binding the combined evidence into that final manifest, run
`scripts/combine_convergence_evidence.py --selection-roster ...`. The combiner
regenerates the validation realization, reloads and hashes all selections and
checkpoints, reconstructs all eleven selected physical ensembles, and rejects
any missing, extra, duplicate, source-hash, ensemble-hash, config, setting, or
tolerance mismatch in each of the three evidence files.
Accumulate per-state raw SKR across batches and divide once by the total state
count. Save `I_AB`, `chi_BE`, raw SKR, positive-part diagnostic, `V_A`, PMF,
orbit masses, geometry, and constraint/amplitude diagnostics per state.
Record `n_peak`, maximum physical photon number, slack, and feasibility in
every selection and evaluation artifact.
If a held-out adaptive policy has negative realized budget slack, preserve the
artifact with `comparison_valid:false` and exclude it from publishable fair
comparisons. Held-out failure must never trigger retraining, checkpoint
reselection, margin changes, or another test realization.

## Multi-seed aggregation and uncertainty

The independent training seed is the primary replication unit. Report all
seed-level held-out means, their arithmetic mean and standard deviation, and a
two-sided 95% Student-t confidence interval. For learned-versus-baseline and
ablation contrasts, use paired seed-level differences with the same held-out
states and AWGN streams. Baselines are deterministic conditional on validation
selection and are paired with each learned seed's test evaluation randomness.
State-bootstrap intervals may be secondary, clearly labeled conditional on the
trained seeds; they must not replace seed-level uncertainty.

## Provenance and environment

Every run directory must include the resolved YAML and its SHA-256, Git commit,
dirty diff or explicit clean status, `python --version`, `pip freeze`, PyTorch
version, device/dtype, all seeds and namespace rules, split hashes, script
command, start/end timestamps, checkpoint SHA-256, convergence artifacts, raw
metrics, and failure logs. Figure/table generation consumes only archived raw
artifacts and never reruns or retunes models implicitly.

## Future result schema

No field below is a result or claim yet. Future artifacts conform to
`schemas/publication_results.schema.json` (`publication-results-v2`) and contain:

- average raw SKR, aggregate-clipped SKR, `I_AB`, and `chi_BE` for all four
  fixed baselines and all seven learned ablations;
- per-state and binned SKR versus `(T,epsilon)`;
- the `V_A(T,epsilon)` heatmap grid and values;
- orbit entropy `H(Q)`, full entropy `H(P)=H(Q)+2`, orbit masses, and full PMFs;
- preregistered bad/medium/good states with representative PMFs;
- canonical square and learned global GS coordinates with explicit gauge;
- positive-SKR probability and raw-SKR outage thresholds/statistics;
- achieved mean photon number, budget slack, common `n_peak`, peak slack and
  feasibility, maximum energy, PAPR, energy quantiles, minimum distances,
  covariance, trace, and numerical-repair flags;
- seed-level estimates, paired contrasts, intervals, and provenance links.

SKR fields must distinguish the primary raw fading average from
`[mean(K_raw)]_+` and the state-selective oracle diagnostic
`mean([K_raw]_+)`.
