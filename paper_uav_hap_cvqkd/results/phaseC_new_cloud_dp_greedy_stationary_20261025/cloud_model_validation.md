# Cloud model validation — DIAGNOSTIC_ONLY

Primary law: conditional N(mu_n,Gamma), Gamma_ij=9*0.9^abs(i-j), J=100. Independent Uniform(-1,1) means and Gaussian residuals resampled every slot. No previous state/rho/AR update. Row-major indexing; index anisotropy retained.

Zero threshold and calibrated p are explicit author-approved simulation conventions. All eight p targets fall within their observed mission-level95% blockage intervals. No per-slot fixed blocked count. Exact thresholds/empirical estimates: empirical_blockage.csv.

The supplied Gamma is CONDITIONAL covariance. Marginalizing random means gives Gamma+I/3; both moments are tested separately, not confused or renormalized. 512 independent mission clusters,30slots each; covariance gate6clusterSE, pooled Pearson and binary correlations reported separately. Uniform KS D=0.0004234397523457112 < DKW bound 0.0021732165924252737.

Four unit-test methods cover exact/symmetric/PD covariance, deterministic slot generation/mean resampling/thresholds/no-state signature, brute-force DP/feasibility/stationary/diagonal moves, and nonanticipating Greedy/ties. All actual MC instances also check shared C/S and DP objective dominance.

Old model is called only in the controlled OLD case, using the untouched src/binary_cloud.py implementation. Same base white normals, sign-adjusted new residuals, same mission IDs, same p0.4 and same geometry/rate map. No historical algorithm outcome is reused as a new-cloud outcome.

See cloud_validation.json, old_new_empirical_correlations.csv, focused_tests.json and verification.json. Source convergence and atmospheric forecast validation are outside these synthetic-cloud checks.
