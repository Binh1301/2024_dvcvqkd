# Dynamic Gaussian cloud emulation (isolated diagnostic)

This module implements the multiscale recursion in Ibrahim et al. (2024),
*Anticipating Optical Availability in Hybrid RF/FSO Links Using RF Beacons and
Deep Learning*, Algorithm 1, PDF page 10 (printed page 1378), with Table 2 on
PDF page 9. It produces synthetic cloud fields, not measured weather.
The source PDF is supplied by the user; its SHA-256 is recorded in the example
run receipt. No existing cloud generator or QKD component imports this module.

## Run

From `paper_uav_hap_cvqkd/`, using the existing project environment:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest tests.test_ibrahim_cloud -v
.\.venv\Scripts\python.exe -X utf8 -B scripts\visualize_ibrahim_cloud.py --output results/ibrahim_cloud_example_new --gif
```

The script defaults to `configs/ibrahim_cloud_demo.json`, runs 1000 seconds,
and refuses to overwrite an existing output directory. Add `--config PATH`
to use another JSON configuration. Optional `--reference-pdf PATH` records
the supplied paper's hash. NumPy, SciPy (with `gaussian_filter(radius=...)`),
Matplotlib and Pillow are required; `unittest` is in the standard library.
Pillow is needed for Matplotlib PNG export and the optional GIF. PDFium was
installed only for visual QA and is not a simulation dependency.

## Original algorithm, numerical choices, scenario changes

| Algorithm 1 | Implemented operation | Choice or boundary |
|---|---|---|
| Lines 1-2 | `G0 = fine + interp(coarse)` | Independent standard-normal grids; PCG64 RNG; periodic bilinear interpolation. Paper specifies Gaussian draws and interpolation, but not the interpolation method. |
| Lines 6-11 | Periodic translation of previous **raw** noise | User-requested physical pullback, subpixel displacement and SI units, as detailed below. |
| Lines 12-13 | `(1-p)*G_adv + P*fine + P*interp(coarse)` | Preserve lowercase `p` and uppercase `P` separately. Table 2 describes lowercase `p`; no reproducible numerical pair or relation is supplied. |
| Lines 14-15 | `mask = (G > gamma)` | Integer 1 means cloud; 0 means clear. Strict greater-than, before smoothing. |
| Lines 16-21 | Gaussian convolution of continuous `G` | Separable finite, normalized Gaussian kernel; periodic boundaries. Kernel parameters are explicit numerical choices. |
| Line 22 | Optional normalized display intensity | Fixed-reference min-max scaling is a scenario choice, **not** the paper's meteorological cloud-thickness normalization. |
| Line 23 | No ray tracing in this phase | Masks are exported for later integration only. |

The paper's printed line 9 uses an index lookup with `i+vx`, `j+vy` and
describes pixel-based wrapping. With ascending physical axes that plus-index
lookup moves a pattern opposite to the sign of the index offset. This
implementation deliberately adopts the user's **physical velocity** convention:

```text
G_adv(x,y) = G_previous(x - vx*dt, y - vy*dt)
dx = width_m/nx; dy = height_m/ny
array_shift = (vy*dt/dy, vx*dt/dx)      # [row=y, column=x]
```

Thus `vx=-5 m/s` gives a shift of `-0.125` cells per one-second slot,
moving cloud features left. This explicit sign/unit interpretation is not a
literal substitution of `-5` into the paper's pixel-index expression.
The default 2 km square, 50-by-50 grid, speed, duration, threshold coverage mode
and normalized intensity are HAP-UAV scenario adaptations requested by the user.

Each fine cell spans 40 m; its centre is `(j+0.5)*40, (i+0.5)*40` metres.
Rows increase upward because plots use `origin='lower'`. Coarse Gaussian knots
are placed at fine indices `0,u,2u,...`; interpolation wraps at the domain edge.
The code requires `u` to divide both grid dimensions, rather than silently
rounding the coarse shape. With `u=5`, the coarse random grid is 10-by-10.

## Parameters actually used by the example

| JSON parameter | Example | Meaning |
|---|---:|---|
| `nx`, `ny` | 50, 50 | Columns in x, rows in y |
| `width_m`, `height_m` | 2000, 2000 | Fixed physical domain, metres |
| `u` | 5 | Coarse-grid downsample coefficient |
| `dt_s` | 1 | Time between updates, seconds |
| `vx_m_s`, `vy_m_s` | -5, 0 | Physical velocity, metres per second |
| `duration_s` | 1000 | Last time; includes frames at t=0 through t=1000 (1001 frames) |
| `seed` | 20261111 | PCG64 seed; no global RNG mutation |
| `p` | 0.002 | Per-slot decay of advected Gaussian amplitude |
| `P` | 0.05 | Independent Gaussian injection strength at each scale |
| `threshold_mode` | `coverage` | `coverage` or `fixed` |
| `gamma` | null | Supply a finite scalar in `fixed` mode |
| `target_coverage` | 0.30 | Coverage used to select gamma from the initial raw field |
| `blur_sigma_cells` | 1 | Gaussian standard deviation, cells (40 m here) |
| `blur_radius_cells` | 4 | Finite kernel radius; default 9-by-9 support |
| `normalization` | `reference_minmax` | Or `none` to expose signed BN unchanged |
| `snapshot_times_s` | [0, 40, 80] | Three distinct times on the slot grid within the duration |

`p=0.002` and `P=0.05` are illustrative settings, not values attributed to
Ibrahim et al. No stationary-variance correction or renormalization of the
recursive field is added. Changing `dt_s` changes the number of per-slot
decay/noise updates: `p` and `P` are per-slot, not continuous-time rates.
To compare shape evolution, change `P` explicitly (for example 0, 0.01, 0.1).
The tests verify the corresponding innovation amplitudes on common seeded noise.
To test pure translation, set **both** `p=0` and `P=0`.

## Thresholds, separate arrays and normalization

Default calibration is `gamma = quantile(G0, 1-target_coverage)` with the
linear empirical quantile. A caller may explicitly supply `reference_field`
to `CloudSimulator` instead. The selected gamma stays fixed for the entire
mission. The initial default continuous sample achieves 30% to cell resolution;
ties may prevent exact coverage for another reference. Target 0 uses the
reference maximum; target 1 uses the next representable value below its minimum.
These are reference-time endpoints, not overrides that force future masks.
In fixed mode the supplied gamma is used directly and target coverage is ignored.

Coverage can drift as raw mean and variance evolve; it is never corrected by
per-frame threshold adjustment. The full 1001-slot CSV reports this drift.
Time samples and cells are correlated; temporal standard deviation is descriptive,
not a confidence interval from independent realizations.

`CloudFrame` exposes read-only, independent arrays:

- `raw_noise`: continuous recursive Gaussian field G.
- `mask`: uint8, `(G > gamma)`, values 0 and 1 only.
- `blurred_noise`: continuous BN from normalized Gaussian convolution of G.
- `intensity`: display-only normalization of BN, or a copy of BN in `none` mode.

For `reference_minmax`, freeze `lo=min(blur(G_reference))` and
`hi=max(blur(G_reference))` before the first step. Then compute
`clip((BN-lo)/(hi-lo),0,1)`. Only `intensity` is clipped. Report the clipped
fraction at every slot; a constant blurred reference raises an error because
it supplies no scale. The same reference limits and color scale apply at every
time. Labels use **Normalized Cloud Intensity**. Neither G nor BN nor the mask
is physical CLWC, cloud thickness, extinction, attenuation or an outage rule.
With `normalization='none'`, the label is `Blurred Gaussian field (a.u.)`.

## Numerical and domain limitations

Advection uses first-order `scipy.ndimage.shift(..., mode='grid-wrap')`.
This is genuine subpixel interpolation, not integer rounding. A pulse moves
0.125 cell left per second and its centroid moves 40 m left after eight steps.
Its peak broadens: repeated linear interpolation introduces numerical diffusion.
Do not claim the eight-step array is an exact one-cell roll. The tests separately
verify an exact integer roll, fractional weights, both axes and wrapping.

A 2000 m periodic domain with speed 5 m/s has a **400 s geometric wrap period**.
Structures leaving the left edge re-enter the right edge. Repeated interpolation,
decay and innovation mean the full field does not exactly repeat every 400 s.
This is an artificial torus, particularly relevant for a 1000 s mission.
An enlarged domain/new-inflow extension is not implemented in this phase.

## Outputs and verification

Example: `results/ibrahim_cloud_demo_20261111/`.

- A: fine, upsampled coarse and combined initial field; one common Gaussian scale.
- B: separate continuous-intensity and binary-mask figures, with distinct units.
- C: normalized-intensity snapshots at three requested times, common fixed scale.
- D: corresponding binary snapshots; black clear, white cloud.
- Every figure has a 400-dpi PNG and a PDF with embedded TrueType fonts.
- `cloud_masks.gif`: optional nearest-neighbor mask preview sampled every 5 s;
  playback speed is illustrative. The numerical simulation still uses 1 s slots.
- `cloud_snapshots.npz`: selected raw/mask/BN/intensity arrays, initial components,
  calibration reference, fixed gamma and times; `allow_pickle=False` is sufficient.
- `coverage_timeseries.csv`: all slots, raw moments, coverage and normalization clipping.
- `run_report.json`, `config_used.json`, `protected_input_hashes.json` and
  `artifact_hashes.json`: parameters, results, source/config/PDF hashes,
  environment versions and protected tracked production inputs.
- `unit_tests.log`, `validation.json`: current focused tests and artifact QA.

Tests cover grid shape, binary values, seeded reproducibility, initial multiscale
construction, exact p/P expression, direction, fractional weights, 8-second
centroid displacement, periodic seams, noise-strength evolution, fixed threshold
calibration, unit-sum blur, separate mask, immutable snapshots and invalid inputs.

This is `SYNTHETIC_CLOUD_DIAGNOSTIC_ONLY`. Figure typography does not certify
meteorological accuracy or a physical channel. Future application of
`R_k(q) = [1-b_k(q)] R_clear(q)` needs an explicit coordinate/time sampling
interface; it is not connected here. Existing QKD channel, SKR lookup, finite-size
and UAV optimization remain unchanged. No scientific baseline or QKD threshold
is selected or approved. No training, final-test access, held-out evaluation or
publication-scale experiment is performed.

The historical frozen-spec hash discrepancy remains a blocker for model-sensitive
work: actual `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`
versus historical `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
`UNVALIDATED_SECURITY_MODEL` and `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` remain.
