# Numerical accuracy audit

ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED

24 originalGH8/directZ-minus evaluations from compatible cached C,w; bit-exact repeats=True.
Independent here means bypassing the objective cache and reconstructing the original inputs; it is NOT an independent arithmetic algorithm.
Maximum delta K=0.0; maximum subtraction input-ULP scale=2.220446049250313e-16.
The input-ULP scale characterizes final subtraction only, NOT errors in computing MI, C,w, eigenvalues or entropies.

## Source checks and retained evidence

All145 source identities,256 support, binary64 parameters, ensemble hashes, source settings and exact implementation/newline aliases verified.
Source precision ladder is1050/1250/1450. Original full_support_c4_worker.py requires final1250/1450 rows resolved with rank256 and C,w agreement within1e-7+1e-6*max(abs(C,w)).
The production cache producer discards per-precision fallback_rows and residual diagnostics when serializing C,w. Current new-probe receipts retain the rejected complex128 fast gate but NOT the AP per-precision observables.
The fast reconstruction residual belongs to the rejected fast route: small residual with nonpositive computed eigenvalues is NOT an AP accuracy bound.
Thus the unchanged worker acceptance rule is provenance-supported, but measured per-precision error at these exact145 sources cannot be reconstructed from the retained payload alone. No new AP is permitted.

## MI/quadrature and Holevo evidence

Existing tests/test_exact_mb_test2a.py provides deterministic full/product GH8 equivalence and bit-exact repeats on its own fixture. Only fixed-order tests are run here; no new quadrature sweep.
Existing results/exact_mb_test2a/gh_convergence.json and joint_mb_va_global/gh_convergence.csv cover other ensembles/channel fixtures; not a bound for the22km ridge.
Existing redesigned_baseline_global_mb_va/continuation_final_summary.json reports top10 GH8-to64 MI delta1.498e-10, but uses w0=.10 and a different channel/K. It does not bind the new5.475/5.425 sources or current22/reference context; no generic error guarantee is imported.
Original evaluate_candidate invokes _holevo_from_source_moments with maximize_full_interval=False and rejects a mode other than zstar. Existing synthetic direct-Z and physicality tests are relevant software evidence, not high-precision entropy/covariance error enclosures.
Original channel replay matches saved reference/22 dictionaries exactly. No precision/order/formula/security variant used.

## Interpretation

Repeated ordering and final subtraction precision do not establish a rigorous total objective error bound. In particular epsilon_opt=1e-8 and physicality tolerances are not total objective accuracy bounds.
The1e-7 gains are reproduced under the frozen evaluator; their distinction from ALL numerical errors and physical significance remain unproven.
Further probes can characterize coverage/sensitivity, not remedy absent total error control by themselves. No continuous fit, extrapolation, predicted gain or convergence claim.
