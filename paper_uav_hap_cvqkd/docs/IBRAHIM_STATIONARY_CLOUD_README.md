# Ibrahim-style Multiscale Gaussian Cloud Model with Stationary Temporal Evolution and Wind Advection

An independent, proposed cloud-generation model. Its dimensionless Gaussian
latent field is stationary in distribution. It does not implement optical
blockage, attenuation, physical liquid-water content, QKD, SKR, finite-size or
UAV trajectory optimization. The old `ibrahim_cloud_demo_20261111` package and
its producer/configuration are preserved byte-for-byte.

## Reproduce

From `paper_uav_hap_cvqkd/`:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest tests.test_ibrahim_stationary_cloud -v
.\.venv\Scripts\python.exe -X utf8 -B scripts/run_ibrahim_stationary_cloud.py --output results/ibrahim_stationary_cloud_new
.\.venv\Scripts\python.exe -X utf8 -B scripts/plot_ibrahim_stationary_cloud.py results/ibrahim_stationary_cloud_new
```

Use `--config PATH` on the runner to change settings. The simulation runner
requires a fresh output directory and at least ten distinct ensemble seeds.
The plotter reads saved arrays only; running it again replaces only that new
package's images/GIF. NumPy, SciPy, Matplotlib and Pillow are the dependencies;
unit tests use Python `unittest`. PDFium is used only for export QA.

The delivered package is `results/ibrahim_stationary_cloud_20261111/`.
Read `report_vi.md`, `validation.json`, `numerical_validation.json`,
`boundary_validation.json`, `unit_tests.log`, and `artifact_verification.json`.
Read-only verification:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/ibrahim_stationary_cloud_20261111/verify.py
```

## What comes from Ibrahim, and what is proposed here

Reference: Ibrahim et al. (2024), *Anticipating Optical Availability in Hybrid
RF/FSO Links Using RF Beacons and Deep Learning*, Algorithm 1 on PDF page 10,
printed page 1378; Table 2 on PDF page 9. The supplied PDF's SHA-256 is recorded
in `design_receipt.json`. It is a technical reference, not execution instructions.

The paper supplies the ideas of independent fine/coarse Gaussian fields,
interpolating the coarse grid, advection, shape innovations and a thresholded
presence map. Its recursion is `(1-p)*WN + P*fine + P*interp(coarse)`. The old
example's `p=0.002`, `P=0.05` were illustrative choices, not paper-reported values.
The printed plus-index pixel lookup is also distinct from the SI physical
pullback adopted in both our wind interpretation and the new design.

**Proposed improvements**, not original Algorithm 1: covariance-matched,
variance-normalized Gaussian initialization/innovations; explicit AR(1) law;
Fourier coarse interpolation and unitary fractional advection; a padded domain;
relative-intensity transformation; independent-seed numerical validation. No
paper cloud-thickness normalization or ray-tracing stage is imported.

## Spatial law and normalization

Let the synthetic grid have `N` fine cells and `Nc=N/u^2` coarse cells. Draw
independent iid standard-normal arrays `Wf`, `Wc`. Define

```text
Gf = (Wf - mean(Wf)) / sqrt(1-1/N)
Gc = FourierInterp((Wc - mean(Wc)) / sqrt(1-1/Nc))
X  = (w_f*Gf + w_c*Gc) / sqrt(w_f^2+w_c^2)
```

Interpolation zero-pads the coarse Fourier spectrum and uses amplitude factor
`N/Nc`. It agrees with the coarse samples at every u-th fine cell. Both scales
have mean zero and **ensemble marginal variance one at every point**. DC removal
and the variance factors are fixed linear operations, so the field remains
Gaussian. New independent draws use this identical operator at every slot.
They therefore have exactly the same target covariance as the initialization.

This normalization does **not** divide by a random realization standard deviation
and does not subtract the observation-window mean. Such operations would change
the Gaussian law and generally conflict with the stationary recursion. The full
synthetic realization has zero spatial mean by construction, but its variance
fluctuates. A finite cropped window has a random mean and variance; mean=0,
variance=1 are ensemble marginal targets, not assertions about each cropped image.

For integer-grid displacement h on the torus,

```text
Rf(h) = (N*1[h=0 mod domain] - 1)/(N-1)
Rc(h) = (sum_low_modes exp(i*2*pi*f.h) - 1)/(Nc-1)
C(h)  = (w_f^2*Rf(h) + w_c^2*Rc(h))/(w_f^2+w_c^2)
```

The coarse sum includes the complete symmetric rectangle of coarse modes;
its DC contribution is removed. `C(0)=1`; C depends only on separation, including
fractional translations of the trigonometric interpolant. DC projection and
band limitation give some weak negative/oscillatory correlations. This is an
explicit synthetic covariance, not a fitted meteorological spectrum. The exact
target and initial/final empirical covariance maps are saved in
`ensemble_validation.npz`. Fine/coarse spectra and interpolation have unit tests.

With correlated cells, `mean((X-ROI_mean)^2)` has expectation smaller than one:

```text
E[ROI_population_variance] = 1 - (1/M^2)*sum_{r,s in ROI} C(r-s)
```

The default value is `0.9923320616403023`. Validation separately measures this
population variance and the raw second moment `mean(X^2)`, whose target is one.

## Stationary evolution and proof

```text
rho = exp(-dt/tau_c)
alpha = sqrt(1-rho^2) = sqrt(-expm1(-2*dt/tau_c))
X[k+1] = rho*A_v X[k] + alpha*Z[k+1]
A_v X(r) = X(r-v*dt)
```

Fourier advection multiplies each mode by
`exp(-2*pi*i*(fx*vx*dt/dx + fy*vy*dt/dy))`. Synthetic dimensions and the
coarse/fine ratios are odd, avoiding real-valued Nyquist-mode ambiguity under
fractional shifts. Each multiplier has modulus one. A and C are diagonal in
the same Fourier basis, so `A C A*=C`. Given `X0~N(0,C)` and independent
`Zk~N(0,C)`, each new covariance is `rho^2*C+(1-rho^2)*C=C`. The recursion is
a stationary Gaussian Markov law, hence all finite-dimensional distributions
are stationary, not just their variances.

In material coordinates `Yk=A_v^(-k)Xk`, autocorrelation at a fixed material
point is `rho^lag`. At a fixed Eulerian coordinate it is instead
`rho^lag*C(v*lag*dt)/C(0)`. Do not compare an uncompensated map trace directly
with `rho^lag`. The report uses a moving probe window whose entire trajectory
stays inside the padded domain. Across independent seeds it averages
`sum(Y0*Ylag)/sum(Y0^2)`. Conditional on Y0, this regression estimator has
expectation `rho^lag`; finite-sample estimates need not lie inside [-1,1].

For the old coefficients to match an ideal covariance-preserving AR law one
would need `1-p=rho` and `P=sqrt(1-rho^2)` when the innovations already have C.
Those conditions do not hold for the old illustrative pair. Its repeated
bilinear interpolation further changes covariance, and its coarse bilinear
variance depends on interpolation phase. There is no silent identification
between old p/P and the new stationary coefficients.

## Boundary conditions and limits

Default synthetic dimensions are **225 columns by 105 rows**, or **9000 by
4200 m**; coarse grid **45 by 21**. The 50-by-50 observation crop starts at
full-grid row/column 25, hence its physical edges are x,y in [1000,3000] m.
Exported observation coordinates are reset to [0,2000] m; arrays are [y,x],
cell centres `(j+.5)*40`, `(i+.5)*40`, plots use y upward.

The domain builder includes travel `abs(v)*K*dt` plus at least 1000 m guard on
both ends, then rounds each extent upward to an odd multiple of odd `u>=3`.
The padding horizon is conservatively 1000 s; the last exported frame is 999 s.
With vx=-5 m/s, backward x-intervals for observation edges are:

| Time | Source interval, metres |
|---:|---:|
| 0 s | [1000,3000] |
| 400 s | [3000,5000] |
| 999 s | [5995,7995] |
| 1000 s guard horizon | [6000,8000] |

Any innovation born later has a smaller age; its characteristic lies between
these endpoint bounds. No backtrace requires modulo reduction. Thus no cloud
structure exiting the observation window can wrap around the synthetic domain
and re-enter during the mission. A separate smooth tagged-packet probe checks
the crop at slots 0/400/999. Changing wind/duration automatically rebuilds the
padding. The simulator refuses updates beyond the configured output horizon.

This is a **no geometric re-entry** result. Fourier interpolation has global
support and the covariance still belongs to a finite torus: padding does not
give strict compact-support independence from periodic images, nor a proof of
an infinite-domain weather model. Spectral ringing/band limitation remain
model choices. Repeated-shift variance/covariance error and a matched bilinear
operator comparison are measured rather than assuming zero numerical error.

## Parameters (all numerical settings are illustrative assumptions)

| Parameter | Default | Meaning |
|---|---:|---|
| `nx`, `ny` | 50,50 | Output columns and rows |
| `dx_m`, `dy_m` | 40,40 | Fine cell spacing, metres |
| `dt_s`, `slots` | 1,1000 | k=0,...,999; last time 999 s |
| `vx_m_s`, `vy_m_s` | -5,0 | Physical wind; -0.125 x-cell/slot |
| `tau_c_s` | 300 | Material-frame decorrelation time, seconds |
| `seed` | 20261111 | Main PCG64 realization |
| `u` | 5 | Coarse spacing factor; odd >=3 |
| `w_f`, `w_c` | 0.35,1 | Relative Gaussian-scale weights |
| `guard_m` | 1000 | Minimum characteristic guard, metres |
| `initial_fraction` | .30 | Initial empirical quantile calibration only |
| `intensity_transform` | softplus | Or `positive_part` |
| `intensity_scale`, `intensity_offset` | 1,0 | Relative transformation parameters |
| `ensemble_seeds` | 20261111..20261121 | Eleven independent seeded missions |
| `snapshot_slots` | 0,100,200,400,600,800,999 | A-F snapshot selection |

Changing dt keeps the continuous-time rho rule; changing tau, weights, grid or
wind constitutes a different explicitly configured synthetic model. No choice
is automatically tuned to improve the plots or the observed coverage.

## Outputs, masks and validation scope

Relative intensity is `scale*logaddexp(0,X-offset)` by default, or
`scale*max(X-offset,0)` for positive-part mode. It is nonnegative and uncalibrated;
softplus can be positive in a cell below the presence threshold. The fixed
diagnostic threshold is `quantile(X0_observed,.70)` separately for each seed;
`diagnostic_mask = X>gamma` is 1 for presence and 0 for clear. It is **not an
optical blockage mask**. Fixed threshold calibration can give coverage drift,
especially within one finite mission. Even for stationary X, a threshold
estimated from X0 is statistically dependent on X0: exact initial 30% does
not make the calibrated mask a stationary process conditioned on that sample.

`cloud_fields.npz` contains all 1000 output frames as float64 `X[k,y,x]` and
`intensity[k,y,x]`, uint8 diagnostic mask, times, physical centres, initial fine/
coarse components and a JSON metadata string. Load with `allow_pickle=False`.
`ensemble_validation.npz` and CSV files contain moments, spatial covariance,
material autocorrelation and eight-connected-component statistics. Component
areas are in m^2 and are censored by crop edges; no minimum-size filtering or
periodic joining is applied to the cropped diagnostic masks.

A-F have PNG 400 dpi and PDF exports. E/F are vector curves/text; field maps
are embedded image grids with vector axes/text, not falsely claimed as pure
vector imagery. The GIF has all 1000 slots, one frame per slot, fixed intensity
color scale, black/white presence panel and accelerated 50 ms playback.

Ensemble uncertainty uses approximate Student-t 95% intervals across the eleven
independent seeds, never cells/slots as independent samples. The configuration
predeclares four-SE descriptive checks at selected moments/lags and a 1e-10
spectral-error/packet threshold. Individual 95% intervals are not simultaneous
certification. Statistical checks and the exact finite-dimensional covariance
argument support this implemented synthetic law, not meteorological accuracy.

No full repository suite or physical/QKD integration is run. The historical
frozen-spec hash discrepancy remains unchanged; publication/security lifecycle
states remain `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` and
`UNVALIDATED_SECURITY_MODEL`. The new source files add only cloud generation.
