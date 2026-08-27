# Assumptions

1. The HAP is Alice/transmitter and the UAV is Bob/receiver.
2. The paper default is vertical. Nonvertical support exists only to implement the explicit zenith factor and is not claimed as a completed paper experiment.
3. Atmospheric loss is spatially homogeneous Kruse/Beer--Lambert loss.
4. Turbulence uses the constant-`C_n^2` closed form in the draft.
5. Boresight offset is zero; displacement components are independent zero-mean Gaussian variables.
6. `sigma_axis` follows explicit Eqs. (21)--(24), not the legacy `sqrt(total/2)` convention.
7. Excess noise is input-referred SNU. Publication experiments draw it from an explicitly bounded uniform sensitivity domain independently of `T`; this is not asserted to be an empirical atmospheric law. The independence is required because the frozen model supplies no measured or mechanistic `T`--`epsilon` coupling.
8. Exact instantaneous `(T,epsilon)` is available to the transmitter as an oracle. No estimator, feedback delay, quantization, authentication cost, or CSI error is implemented.
9. Bob performs ideal heterodyne detection. Detector efficiency/electronic noise have no separate term in the paper equations implemented here.
10. Reconciliation is asymptotic reverse reconciliation with explicit `beta`.
11. No finite-size or composable-security claim is made.
12. The same physical `Ensemble` is passed to MI and Holevo.
13. Global GS does not depend on channel state; PS and optional `V_A` do.
14. Direct symbol probabilities are used; no Gumbel sampling, bit labeling, neural receiver, distribution matcher, GMI, BER, or coded-throughput model is present.
15. Channel-state samples are iid Monte Carlo realizations, not a temporally correlated UAV trajectory.
