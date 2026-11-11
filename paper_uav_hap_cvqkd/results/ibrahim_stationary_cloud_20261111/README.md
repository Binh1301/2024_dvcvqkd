# Stationary multiscale Gaussian cloud diagnostic

Read [the Vietnamese report](report_vi.md) first. Formula derivation,
parameters, assumptions and run commands are in
[the model README](../../docs/IBRAHIM_STATIONARY_CLOUD_README.md).

The six figures each have a 400-dpi PNG companion:

- [A: independent Gaussian scales and combined latent field](figure_A_multiscale.pdf)
- [B: relative intensity and cloud-presence diagnostic](figure_B_intensity_presence.pdf)
- [C: seven latent snapshots](figure_C_latent_snapshots.pdf)
- [D: seven diagnostic-mask snapshots](figure_D_presence_snapshots.pdf)
- [E: coverage, mean and variance with seed-level uncertainty](figure_E_time_statistics.pdf)
- [F: spatial covariance and motion-compensated temporal correlation](figure_F_correlations.pdf)
- [All 1000 slots, accelerated animation](cloud_1000_slots.gif)

`cloud_fields.npz`: all main-seed cropped arrays, not just snapshots.
`ensemble_validation.npz`: eleven seeds, target/empirical covariance and metrics.
`time_statistics.csv`, `temporal_correlation.csv` and
`connected_components_main.csv`: human-readable numeric exports.
`design_receipt.json`: settings/criteria, source/config hashes, environment.
`validation.json`: 67 predeclared descriptive ensemble checks and old-baseline
comparison from saved artifacts only. `boundary_validation.json` and
`numerical_validation.json`: no-reentry geometry, tagged-packet and diffusion probes.

Verify without simulation:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/ibrahim_stationary_cloud_20261111/verify.py
```

No calibrated CLWC, optical blockage/attenuation or QKD interpretation is attached
to the relative intensity or diagnostic masks. Existing baseline, QKD code,
security/publication state and frozen specifications remain unchanged.
