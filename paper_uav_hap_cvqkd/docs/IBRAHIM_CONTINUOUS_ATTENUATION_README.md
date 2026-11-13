# Independent 2D Spatiotemporal Continuous Cloud Attenuation Model

Status: **ILLUSTRATIVE_UNCALIBRATED**. This standalone diagnostic reads the
existing Ibrahim Stationary Gaussian data; it never regenerates that field,
imports the QKD channel, computes SKR, or changes security/publication settings.

The delivered package is `results/ibrahim_continuous_attenuation_20261112/`.
Read its `report_vi.md` for parameter tables, provenance, numerical results,
empirical correlations, geometry, scientific limitations and all figure captions.

## Equations and attribution

The saved latent field follows the previously proposed stationary multiscale
Gaussian construction, spectral wind advection and AR(1) evolution. Those
improvements are not the original Ibrahim Algorithm 1. The existing field and
all old producer/config/result files remain unchanged.

Assumed CLWC surrogate (not supplied or calibrated by Ibrahim):

```text
L[k,y,x] = L0 * max(G[k,y,x] - gamma0, 0)    [g/m^3]
gamma0 = 0.6946257315928469 (reuse saved initial quantile, never re-estimate)
```

This positive-part map is continuous and has a zero atom. It does not produce
binary optical blockage, and no attenuation cutoff is applied. It is not a
moisture-conservation or droplet-microphysics model. No per-frame normalization.

Ibrahim et al. (2024), [DOI:10.1109/TMLCN.2024.3457490](https://doi.org/10.1109/TMLCN.2024.3457490),
Section II-A, Eqs. (5)-(7), printed page 1373:

```text
V = 1.002 / (L * N)^0.6473                        [km]
omega = (3.91/V) * (lambda_nm/550)^(-x(V))         [dB/km, paper convention]
x = .585*cbrt(V)  for 0<V<6
    1.3          for 6<V<=50
    1.6          for V>50
```

The printed equation leaves **V=6 undefined**. This implementation explicitly
assigns `x(6)=1.3`, completing that one point with the upper branch. It retains
all printed branches and their jumps at 6 and 50 km. It does not silently use
the common five-branch Kim expression. Thus *continuous* means continuous-valued
attenuation, not a globally continuous mathematical function. The paper's
coefficient and dB/km convention are followed literally, without adding a Np/dB
factor. Measurement/extinction conventions need review before physical adoption.

`L` is in g/m^3, `N` in cm^-3, wavelength in nm. `L=0` gives visibility +inf as
an explicit limiting sentinel, `omega=A=0,T=1`; +inf is not saved in NPZ/JSON.
Positive-CLWC visibility and all saved physical arrays must be finite.

Reference maps assume a full slab and vertical incidence:

```text
A_cloud = omega * H_km / cos(zenith)      [dB]
T_cloud = 10^(-A_cloud/10)               [power ratio]
```

The reference is not a claim that the actual HAP-UAV segment intersects a cloud.
`layer_intersection` checks the finite segment against cloud base/top, measures
the actual in-cloud path (including partial penetration) and returns the cloud
midpoint `q_c`. It does not identify cloud coordinates with UAV coordinates.
`representative_link_attenuation` bilinearly samples CLWC at `q_c` and applies
the measured path length. It returns zero cloud loss if there is no intersection;
an intersecting coordinate outside the saved map fails rather than wrapping.
This is a midpoint approximation, not an integral through horizontal variation.
`combine_clear_cloud` is a pure optional multiplication interface, unused by QKD.

## Parameters and illustrative scenarios

Input: 2 km square, 50x50 cells, 40 m spacing, 1000 slots at 1 s (0..999 s),
wind (-5,0) m/s, source seed 20261111, tau=300 s. Lambda=1550 nm.

Every physical scenario below is **uncalibrated**, not a measured cloud case.

| Name | L0 (g/m^3) | N (cm^-3) | H (km) |
|---|---:|---:|---:|
| reference | 0.1 | 100 | 0.5 |
| L0_low | 0.05 | 100 | 0.5 |
| L0_high | 0.3 | 100 | 0.5 |
| H_thin | 0.1 | 100 | 0.1 |
| H_thick | 0.1 | 100 | 1 |
| N_low | 0.1 | 50 | 0.5 |
| N_high | 0.1 | 300 | 0.5 |

The Gaussian-to-CLWC mapping, N and H require meteorological calibration.
For fixed gamma, the optical law depends on L0 and N only through L0*N.
Consequently L0_low/N_low and L0_high/N_high give equal attenuation (up to
roundoff) although CLWC differs. Optical loss alone cannot identify L0 and N
separately; these are parameter sensitivity cases, not independent validation.
OPAC water-cloud model values provide an order-of-magnitude comparison only;
they do not calibrate these scenarios. Rectified Gaussian tails are unbounded;
no arbitrary saturation is applied. At extreme loss, float64 transmittance
underflow raises an error; retain dB/logT rather than inventing a nonzero floor.

## Reproduce and verify

From `paper_uav_hap_cvqkd/`, using the existing NumPy, SciPy, Matplotlib, Pillow
environment. PDFium is needed only for visual export QA. No new dependencies.

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m unittest tests.test_ibrahim_continuous_attenuation -v
.\.venv\Scripts\python.exe -X utf8 -B scripts/run_ibrahim_continuous_attenuation.py --config configs/ibrahim_continuous_attenuation.json --output results/ibrahim_continuous_attenuation_new
.\.venv\Scripts\python.exe -X utf8 -B scripts/plot_ibrahim_continuous_attenuation.py results/ibrahim_continuous_attenuation_new
.\.venv\Scripts\python.exe -X utf8 -B scripts/report_ibrahim_continuous_attenuation.py results/ibrahim_continuous_attenuation_new
```

The runner requires a new output directory and checks the original NPZ/metadata
against its old manifest before transforming. It records producer, config and
input hashes before calculation. Seed reproducibility is inherited through
the saved source hash; the new transformation is fully deterministic, without
any RNG. Rendering/reporting reads saved arrays only. Keep the sealed delivered
namespace immutable; use a new output directory for parameter experiments.

Read-only verification of the delivered package:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/verify_ibrahim_continuous_attenuation.py results/ibrahim_continuous_attenuation_20261112
```

The delivered verifier also checks the saved regression log, sealed artifacts,
1003 old file hashes and export evidence. A fresh numerical-only run is not a
sealed delivery until tests, export QA and sealing are performed.

## Outputs and interpretation

- `cloud_clwc.npz`: full reference `clwc_g_m3[k,y,x]`, float64, units/coordinates.
- `cloud_attenuation_db.npz`: full reference loss and specific loss, float64.
- `cloud_transmittance.npz`: full reference power ratios, float64, 0<T<=1.
- `scenario_snapshots.npz`: seven times for every scenario; full 1000-slot
  means/maxima/quantiles in CSV. Main NPZs contain the reference scenario only.
- `time_statistics.csv`, `scenario_summary.csv`, `probe_time_series.csv`,
  `attenuation_histogram.csv`, `empirical_cdf.csv` (exact CDF at saved nodes).
- `spatial_correlation.csv`, `temporal_correlation.csv`,
  `wind_lag_correlation.csv`: empirical pooled Pearson coefficients for G/L/A/T.
- Figures A-G: PNG400dpi and PDF; 1000-frame continuous-loss GIF, physical y up.
- Config, design receipt, metadata, validation, boundary/geometry examples,
  regression/protected/manifest/visual-export evidence and Vietnamese report.

Nonlinear transforms change covariance. Correlations use valid nonwrapped pairs
with separate sample means per pair set; no iid confidence claims from cells or
slots. Eulerian temporal correlation includes wind and is not `exp(-lag/300)`.
Reusing all frames in their original order preserves the latent process; the
pointwise transform adds neither resampling nor geometric re-entry. The source
padding only proves no characteristic wrap during the configured horizon;
global Fourier support and finite-torus covariance remain limitations.

This package is suitable for isolated software diagnostics and future scoped
integration design. It is not a validated physical cloud model, a QKD security
result or authorization to change lifecycle/publication state.
