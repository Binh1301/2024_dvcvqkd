# Independent review disposition

Review source: independent_review.md, retained as the reviewer's original
checkpoint report. All five actionable findings were reproduced with failing
tests before correction. Final full suite: 34 passed (JUnit evidence in
../results/tests_20261107.xml). No unresolved critical/important findings or
deferred minor findings were reported.

1. Infeasible Stationary no longer aborts feasible methods. A distinct
   InfeasibleProblem exception is recorded at method level; tables/plots leave
   unavailable objective values absent, never invent zero. Regression tests:
   test_infeasible_stationary_does_not_abort_other_methods and
   test_optional_terminal_reports_stationary_infeasible.
2. Paper research-use authorization requires the literal boolean True.
   Regression: test_quoted_false_does_not_authorize_paper.
3. Finite penalty uses 1-log2(epsilon), avoiding 2/epsilon overflow, and
   factors the square roots. Regression: test_extreme_valid_epsilon_is_finite.
4. Approximate mode no longer launches uncapped exact reference solves.
   Regression: test_approximate_run_never_launches_exact_dp. A separate
   approximate smoke run also completes with no exact comparison.
5. CSV rows and NPZ data carry the explicit synthetic/research status.
   Regression: test_every_synthetic_table_has_status. Final artifacts were
   regenerated after correction; earlier development outputs are superseded.

Extra verification checks saved-output corruption detection, parent pointer
backtracking, five random exhaustive tiny graphs, all-blocked trajectories,
velocity-grid refinement and LOS sample-spacing refinement on the demo only.
These are software checks, not physical or composable-security certification.
