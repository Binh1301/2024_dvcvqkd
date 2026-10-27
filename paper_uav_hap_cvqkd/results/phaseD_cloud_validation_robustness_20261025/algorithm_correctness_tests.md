# Focused algorithm correctness — CURRENTLY_VERIFIED_PASS

Reused4 Phase C test methods, called as a unittest suite without executing its
stochastic-audit main. All4 passed. They check covariance/threshold validation,
determinism, greedy future-prefix independence, stay/diagonal moves and DP
against256 full-graph trajectories at3 penalties.

Added3 exhaustive checks on a4-node5-slot NONCOMPLETE predecessor graph,
maximal110m step. Enumerate only feasible sequences, test lambda0/ref/.001.
DP U agrees with maximum exhaustive U to<1e-15. The exact recurrence in
src/uav_mobility.py initializes reward S[:,0]/Nt, adds S[:,n]/Nt and subtracts
lambda*d/Dref, then validates backtracking objective and every speed bound.
Free initial position, no deployment/return charge, stay allowed.
Stationary is the offline maximum mission-average fixed position, distance0.
Greedy reads only current S[:,n], uses the same reward/penalty scaling and
deterministic first-index ties. Its prefix remains unchanged if future S is edited.

All7600 saved Phase C DP-vs-baseline inequalities
pass; minimum margin=0.0. New indexing compares also
check per-instance dominance, immutable common S/C hashes and feasible paths.
The saved NEW paths include four new mappings,100 missions and3p values;
their raw outcomes and backtracking are in indexing_realizations.npz.

## Transpose symmetry and tie ordering

Column labels transpose the centered grid. K and distances are exactly
transpose-invariant. DP's objective and Stationary's rate are bit-exact equal
for all300 coupled row/column mission views. Greedy can choose different tied
physical indices, so its original fixed-index tie convention is not equivariant.
A separate300-call Greedy-only test reorders the
transposed problem into the corresponding label order: maximum absolute U
difference=0.0. This isolates the observed
Greedy row/column differences as tie-order effects, not a different cloud law.
The original algorithms and baseline outcomes are untouched.
