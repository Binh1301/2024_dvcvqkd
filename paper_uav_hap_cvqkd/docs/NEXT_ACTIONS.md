# Next actions

1. Author reviews and either approves, revises, or rejects
   `PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL.md`.
2. If approved, prospectively freeze before fresh outcomes:
   - candidate/reference thresholds;
   - backend/thread provenance;
   - spectral guard calibration procedure;
   - whole-segment checker;
   - backtracking and optimizer-momentum rollback behavior;
   - rejection/progress criteria and fresh seeds.
3. Implement the enhanced update checker and tests. Do not activate `1e-13`
   before formal recertification passes.
4. Rerun the complete canonical, stress, gradient, boundary, and feasibility
   protocol with the newly frozen rules.
5. Later replay every hash-bound selected training/validation ensemble.
6. Only after numerical certification passes may the 31x15 optimized-MB
   validation grid and validation-only baseline selection run.
7. Keep the final test set inaccessible until all numerical, training, and
   selection choices are frozen.

Publication-scale training remains prohibited.

