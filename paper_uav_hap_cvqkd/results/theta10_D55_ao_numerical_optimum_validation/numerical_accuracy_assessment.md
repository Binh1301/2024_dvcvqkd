# Numerical accuracy assessment

ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED. No new evaluation or quadrature/precision sweep.

146 source identities/full support256 are verified against original construction,
settings and code.1050/1250/1450 is unchanged; full_support_c4_worker.py accepts
final1250/1450 resolved rank256 and per-C/w agreement1e-7+1e-6*max(abs(reference)).
Production caches retain binary64 C,w but discard fallback per-precision rows.
The new5.4875 receipt retains the rejected complex128 gate, not the AP observable
residuals. A small rejected-fast-route residual is not a full-support AP bound.
No current candidate-specific AP error enclosure can be recovered from these files.

Batch3 new_source_objective_reproducibility.csv records6 original GH8/direct-Z
metric repeats with bit-exact differences0. Earlier145 preparation records24
repeats. These are historical measured repeatability, not fresh results here,
and not independent arithmetic or truncation-error validation. File hashes protected.

MI is deterministic discrete-input heterodyne product GH8, not Gaussian-input MI.
The existing fixed-GH8 full/product test is rerun without changing quadrature.
exact_mb_test2a/gh_convergence.json and joint_mb_va_global/gh_convergence.csv
cover different ensembles/channel fixtures. The redesigned baseline continuation
reports top10 GH8->64 difference1.498e-10 under w0=.10, not the current .098676...
reference/22 ridge. None is a validated quadrature bound for every current best.

Direct-Z Holevo uses the same source/ensemble/excess noise and rejects wrong
mode/nonphysical inputs. Existing software tests validate conventions and guards;
they do not enclose errors in eigenvalues, square roots or entropy cancellation.
No independent high-precision whole-objective bound is retained at these winners.

At reference betaI=.602479799960547,chi=.5244988060866094, so K=.07798099387393764.
Neighbor gaps are7.834476867252249e-8(reference runner-up) and
1.733217454003011e-7(22km runner-up). Final subtraction input-ULPs are of order1e-16;
this scale does NOT bound source, quadrature, channel, covariance or entropy error.
epsilon_opt=1e-8,parameter_tolerance=1e-6 and physicality tolerances are different
quantities, not total-K accuracy bounds. Reproduced tiny gains cannot be called
error-resolved or physically significant. Current ordering is reproducible only.

Future reliable approximate numerical optimality needs candidate-specific retained
source convergence/residual records, compatible existing MI convergence evidence
or separately authorized diagnostics, stable physicality/Holevo checks, and an
explicit total-objective accuracy assessment relative to relevant gaps. Do not
silently change the evaluator or claim this proposed work is already done.
