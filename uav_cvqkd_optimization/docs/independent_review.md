# Independent implementation review

What this change does: The sibling package implements the requested three
baselines and a Pareto-label dynamic program on one waypoint/energy model.
It evaluates P1 and P2 at variable terminal times using the accumulated-block
finite-size performance formula, and exports synthetic demonstration artifacts.

Review scope: the supplied implementation task, implementation plan, package
source, configuration, tests and existing synthetic output structure. This is
a read-only code review except for this report. No production project changes,
external SKR evaluations, publication runs or historical-data reuse were made.
The manuscript was reviewed by the implementer; this independent review used
the supplied task's explicit equations and requirements as its formula oracle.
Expected load: exact mode on small graphs; approximate mode on larger graphs.

## Must fix

1. **An infeasible baseline aborts a feasible experiment (medium).**
   Evidence: `baselines.py:25-27`, `evaluation.py:selected_solutions`,
   `experiments.py:run_methods`.
   - What this is: Stationary is evaluated first and all algorithms are collected
     by a list comprehension. A baseline with no admissible prefix raises.
   - Problem: With the demo rotor parameters, graph points `(0,0),(10,0)`,
     `dt=1`, and `E_max=140 J`, movement costs `126.03368677372114 J` but
     hovering costs `168.49 J`. DP returns `[0,1]`; Stationary throws
     `Problem infeasible: no feasible trajectory reaches a permitted terminal`.
     A configured terminal different from the initial point also makes
     Stationary inherently infeasible even when other methods can reach it.
   - Fix: Preserve method-level infeasibility explicitly and continue feasible
     algorithms. Handle unavailable methods in tables/plots without assigning
     invented zero objective values. Test both the low-budget and terminal cases.
   - If skipped: Valid user configurations fail before producing any comparison.

2. **Authorization validation accepts a quoted false value (medium).**
   Evidence: `config.py:48` tests `not c.get(key)` for the authorization flag.
   - What this is: Paper mode requires an explicit authorization marker in
     addition to input provenance.
   - Problem: YAML `research_use_authorized: "false"` or `"no"` loads as a
     nonempty string and satisfies the check. This does not meet the package's
     stated fail-closed authorization contract.
   - Fix: Require `research_use_authorized is True`; keep provenance validation
     separate. Add a quoted-false regression test.
   - If skipped: A common configuration typing error bypasses the declared gate.

3. **A valid small epsilon produces infinite penalty and wrong key (medium).**
   Evidence: `finite_size.py:14`, corresponding formula in `visualization.py`.
   - What this is: The finite-size evaluator accepts every finite `0<epsilon<1`.
   - Problem: `finite_key(.3,1,1e6,1e-310)` computes `2/epsilon=inf`, returns
     infinite penalty and zero key. The mathematically equivalent stable
     expression gives penalty `224742.26963644163` and key approximately
     `75257.73036355837` bits. JSON export also rejects the infinite output.
   - Fix: Evaluate the logarithm as `1 - log2(epsilon)`, including plotting.
     Add one test for this accepted-domain boundary.
   - If skipped: Some accepted configurations silently produce the wrong
     terminal objective before result serialization fails.

## Findings corrected during review

4. **Approximate experiments launched uncapped exact DP (high, corrected).**
   The original `run_experiment` unconditionally called `solve_dp(scenario)`
   after the four main methods, defeating approximate scalability. The current
   source reuses an existing exact main result only in exact mode and skips
   exact-null pruning sweep entries for approximate main mode. The new
   `test_approximate_run_never_launches_exact_dp` pins this behavior.

5. **Standalone synthetic tables lacked their required warning (medium,
   corrected in source).** Original CSV outputs lacked a `data_status` column,
   even though JSON and figures carried the warning. Current exporters require
   the warning per CSV row and include it in the scenario NPZ. The new
   `test_every_synthetic_table_has_status` pins this behavior. Older generated
   artifacts must be regenerated; source changes do not relabel existing files.

## Scientific and numerical assessment

- The induced-power rationalization matches the supplied rotor equation.
  The sampled lower convex hull includes each queried mean speed; constant
  speed is therefore a feasible candidate, and zero distance retains hover
  power. Graph construction checks edge-cost refinement and stores all costs.
  Refinement agreement is numerical evidence, not a certified uniform error
  bound for the continuous lower envelope. Exact graph claims must retain the
  sampled-energy qualification.
- DP dominance is applied within identical `(k,j,u)` states using exact float
  comparisons. Lower energy and greater accumulated contribution preserve
  future feasibility and reward because the terminal penalty is fixed at a
  given `u`. Parent objects remain alive for trajectory reconstruction.
  No structural exactness defect was found in the inspected recurrence.
- Energy-derived horizons use the minimum feasible edge cost, including hover,
  and intersect the prediction horizon. This supports the stated finite graph
  problem, not unrestricted continuous-space or unlimited-horizon optimality.
- LOS intersects the configured altitude slab before sampling the horizontal
  segment. The code does not silently substitute an endpoint cloud test.
  Fixed spatial sampling can miss narrow opaque regions; the existing explicit
  limitation is appropriate. A coarse/fine agreement check does not certify
  that no smaller interval was missed.
- Lookup loaders disable pickle, demand declared units, reject duplicate or
  invalid coordinates and reject extrapolation. The finite-size penalty is
  applied once to the accumulated block. A source-security proof and physical
  parameter provenance are external scientific requirements, not established
  by these software tests.
- All four methods share the graph, rate array, availability, budget and
  terminal evaluator. Documentation accurately distinguishes future-cloud DP
  information from greedy current-slot decisions and retrospective stopping.

## Verification and deliverables

Executed independently: `python -m pytest -q uav_cvqkd_optimization/tests`
returned **27 passed in 1.15 s** during review. Also executed the low-budget
two-waypoint reproducer and the epsilon-boundary reproducer described above.
The implementer subsequently added regression tests and reported 29 passing;
that later count is not substituted for this reviewer's own observed run.

README, data-input guidance and final reproduction manifests were being authored
by the implementer during review; their absence at the initial snapshot is not
reported as a final missing deliverable. Final acceptance still requires those
files and fresh synthetic artifacts reflecting the corrected exporters.

Verdict at this review checkpoint: fix 1, 2 and 3, then rerun the suite and demo.
Not checked: manuscript PDF independently, real scientific inputs, publication
validity, or every rendered figure. Main residual risk is scientific model and
sampling validity, which software exactness on the discretized graph cannot prove.
