# Cloud mathematical validation — DIAGNOSTIC_ONLY

The simulation adopts G_n=mu_n+epsilon_n, with independent slot innovations
epsilon_n~N(0,Gamma) and iid per-cell/per-slot mu_jn~Uniform(-1,1).
Gamma_ij=9(0.9)^|i-j| is the conditional covariance, in deterministic row-major
label order. No physical cloud centre, wind velocity or temporal AR is modeled.

## Conditional and unconditional covariance

E[G|mu]=mu and Cov(G|mu)=Gamma. The law of total covariance gives
Cov(G)=E[Cov(G|mu)]+Cov(E[G|mu])=Gamma+I/3, because independent Uniform means
have variance1/3. Hence Var(G_j)=28/3; off-diagonal covariance stays9*.9^lag.
The unconditional G is a Gaussian/Uniform mixture, not a multivariate Gaussian.
Its off-diagonal correlation is (27/28)*.9^lag. Residual epsilon=G-mu is used
to test Gamma, with no re-scaling of the covariance.

The original100 independent Phase C missions are reused, 30 slots each.
For each matrix entry, use the mean known-zero-mean cross product within each
mission, then its between-mission standard error. The <=6SE gate is a finite
diagnostic, not a formally calibrated simultaneous covariance certificate.
The previous512-mission audit remains preserved; it is not rerun.

Minimum eigenvalue: 0.473800660116; Cholesky max error: 1.776e-15.

conditional: maximum standardized entry error 3.40728SE; diagonal target 9.

unconditional: maximum standardized entry error 3.58246SE; diagonal target 9.33333333333.

## Temporal independence and uncertainty

Code inspection confirms separate PCG64 streams for innovations and means,
both sampled as entire slot-by-cell arrays; there is no prior-field argument
or persistent shared mean. Nonzero-lag covariance is theoretically zero under
these independent-slot assumptions. Known-marginal normalized cross moments
are measured at lags1,2,5,10 for G, epsilon, mu and binary C.
Pointwise95% and Bonferroni95% intervals across these16 temporal comparisons
are both saved. The G lag1 estimate is about-0.01129: its pointwise95%CI
slightly excludes0, while its Bonferroni interval includes0. Do not hide this
pointwise fluctuation or describe it as evidence of a temporal mechanism.
All16 family-adjusted intervals include0. Independence is a property of the
specified generator, not something a correlation test can prove in general.

## Binary thresholds

By symmetry G and-G have the same marginal law, which is continuous, so
P(G>0)=1/2. For calibrated p, integrate the Uniform-mixture survival probability.
An independent80-digit antiderivative of Phi checks the stored thresholds:
P(G>t)=3/2[H((1-t)/3)-H((-1-t)/3)], H(x)=x Phi(x)+phi(x).
No exact per-slot blocked count is imposed. Pointwise sampling intervals use
independent mission means, not300000 supposedly independent cells/slots.
These thresholds and independently resampled means are explicit simulation
conventions; no attribution to Gong/Sanchez Net for these details is made.

| p | Threshold | Calibration error | Empirical p [mission95%CI] |
|---|---|---|---|
| 0.1 | 3.9155457 | -2.77555756e-17 | 0.0996 [0.0968945094,0.102305491] |
| 0.2 | 2.57158067 | 2.77555756e-17 | 0.199096667 [0.195077875,0.203115459] |
| 0.3 | 1.60235723 | 0 | 0.29898 [0.293716311,0.304243689] |
| 0.4 | 0.774138063 | 0 | 0.399706667 [0.393829007,0.405584326] |
| 0.5 | 0 | 0 | 0.500366667 [0.49398595,0.506747383] |
| 0.6 | -0.774138063 | 0 | 0.601206667 [0.594924289,0.607489045] |
| 0.7 | -1.60235723 | 1.11022302e-16 | 0.701096667 [0.695320587,0.706872746] |
| 0.8 | -2.57158067 | -1.11022302e-16 | 0.80083 [0.796038228,0.805621772] |

## Binary spatial correlations

For pair latent residual correlation rho, the joint threshold exceedance
minus p^2 equals the integral from0 to rho of the bivariate normal density,
averaged over the two independent Uniform means. Divide this integral by
p(1-p) to obtain the binary correlation. This Plackett-identity integral is
computed with20/40-point Gauss-Legendre mean quadrature and independent
adaptive integration over rho; agreement is below1e-10. This is a validation
derivation for the supplied cloud law, not a replacement law.
Binary correlations need not equal residual or unconditional G correlations.
At zero threshold, the Gaussian arcsine formula alone is inappropriate after
marginalizing the independent Uniform means. Known-marginal covariance and
pooled Pearson estimates are both saved and explicitly distinguished.

| Cells (zero-based) | Distance m | Residual rho | Mixture G rho | Predicted binary rho | Empirical binary [95%CI] |
|---|---|---|---|---|---|
| 0,1 | 100 | 0.9 | 0.867857143 | 0.668078222 | 0.682666667 [0.658071731,0.707261602] |
| 0,2 | 200 | 0.81 | 0.781071429 | 0.570162959 | 0.555333333 [0.525071775,0.585594892] |
| 0,10 | 100 | 0.34867844 | 0.336225639 | 0.218207002 | 0.208 [0.172114999,0.243885001] |
| 9,10 | 905.538514 | 0.9 | 0.867857143 | 0.668078222 | 0.664666667 [0.633575413,0.69575792] |
| 0,11 | 141.421356 | 0.313810596 | 0.302603075 | 0.19562849 | 0.197333333 [0.162313831,0.232352835] |
| 0,99 | 1272.79221 | 2.95126654e-05 | 2.84586417e-05 | 1.81101606e-05 | -0.0313333333 [-0.0638147323,0.00114806568] |
