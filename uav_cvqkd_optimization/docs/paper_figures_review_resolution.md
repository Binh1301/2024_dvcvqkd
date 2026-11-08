# Figure review resolution

The independent checkpoint report is retained in paper_figures_independent_review.md.
Four findings were reproduced with failing tests and fixed in the new plotting
module, without changing historical producers or results:

1. Empty/incomplete saved-output seals: require the consumed file hashes,
   required model/evaluation producer bindings, and original configuration input
   binding before the existing verifier runs. Regression:
   test_empty_or_incomplete_saved_seal_cannot_authenticate_measurements.
2. Missing audit inputs: write BLOCKED manifests and no fake images rather than
   crashing before status generation. Regression:
   test_missing_audit_inputs_produce_blocked_manifests.
3. Invisible short trajectories: use a captioned trajectory-extent view with
   equal physical scales and unchanged path coordinates. Regression:
   test_short_paths_remain_visible_without_changing_coordinates.
4. Missing source/version qualifications: retain the exact rotor URL/version in
   captions/manifests and the recorded DP classification on result-based figures.
   Regression: test_captions_include_rotor_version_and_dp_classification.

All 59 tests pass after the fixes, including the original 42 tests. No unresolved
important review finding or deferred minor was reported. Review is a software
and rendering check, not a scientific/security or source-evidence promotion.
