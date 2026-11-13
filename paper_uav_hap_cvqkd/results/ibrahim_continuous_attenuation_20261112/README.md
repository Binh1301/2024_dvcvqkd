# Continuous cloud attenuation diagnostic

ILLUSTRATIVE_UNCALIBRATED. Read report_vi.md and ../../docs/IBRAHIM_CONTINUOUS_ATTENUATION_README.md.

Seven PNG400dpi/PDF pairs A-G; 1000-frame GIF; three full reference NPZs.
No Gaussian regeneration, no binary blockage, no QKD integration.

Read-only verification from project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/verify_ibrahim_continuous_attenuation.py results/ibrahim_continuous_attenuation_20261112
```

Files (final complete index also recorded in artifact_hashes.json):

- README.md
- artifact_hashes.json
- artifact_verification.json
- attenuation_histogram.csv
- boundary_validation.json
- cloud_attenuation_db.npz
- cloud_clwc.npz
- cloud_continuous_attenuation.gif
- cloud_transmittance.npz
- configuration.json
- design_receipt.json
- empirical_cdf.csv
- figure_A_gaussian_cloud.pdf
- figure_A_gaussian_cloud.png
- figure_B_illustrative_clwc.pdf
- figure_B_illustrative_clwc.png
- figure_C_continuous_attenuation.pdf
- figure_C_continuous_attenuation.png
- figure_D_cloud_transmittance.pdf
- figure_D_cloud_transmittance.png
- figure_E_attenuation_statistics.pdf
- figure_E_attenuation_statistics.png
- figure_F_physical_scenarios.pdf
- figure_F_physical_scenarios.png
- figure_G_attenuation_time_series.pdf
- figure_G_attenuation_time_series.png
- geometry_examples.json
- metadata.json
- pdf_export_validation.json
- previous_ibrahim_cloud_demo_20261111_verification.log
- previous_ibrahim_stationary_cloud_20261111_verification.log
- previous_packages_validation.json
- previous_session_handoff.md
- previous_stochastic_cloud_grf_20261111_verification.log
- probe_time_series.csv
- protected_inputs.json
- references.json
- regression_tests.log
- render_diff_validation.json
- render_receipt.json
- report_vi.md
- scenario_snapshots.npz
- scenario_summary.csv
- seal_artifacts.py
- spatial_correlation.csv
- startup.json
- temporal_correlation.csv
- time_statistics.csv
- validate_exports.py
- validation.json
- verification_provenance.json
- visual_qa.json
- wind_lag_correlation.csv
