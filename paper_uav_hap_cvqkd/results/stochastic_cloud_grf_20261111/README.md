# Exponential GRF cloud-generation package

Start with [report_vi.md](report_vi.md) and
[the model/run README](../../docs/STOCHASTIC_CLOUD_GRF_README.md).

Figures, each with a 400-dpi PNG companion:

- [A: target covariance, initial GRF and marginal histograms](figure_A_covariance_initial_GRF.pdf)
- [B: initial relative intensity and presence diagnostic](figure_B_intensity_presence.pdf)
- [C: seven spatial snapshots](figure_C_spatial_snapshots.pdf)
- [D: intensity evolution, morphology and observed segment spans](figure_D_intensity_morphology.pdf)
- [E: mean, variance and cloud fraction](figure_E_time_statistics.pdf)
- [F: spatial covariance versus theory](figure_F_spatial_covariance.pdf)
- [G: material and signed space-time covariance](figure_G_temporal_space_time.pdf)
- [H: paired frozen/evolving behavior](figure_H_frozen_evolving.pdf)
- [Animation, all 1000 slots](cloud_1000_slots.gif)

`cloud_fields.npz`: latent_field, relative_intensity, diagnostic_mask,
coordinates, time and full parameter metadata. `frozen_fields.npz`: paired
frozen sequence from the same initial field. `ensemble_validation.npz` and CSVs
store statistics across eleven independent seeds. `track_segments.csv` records
observed spans and ROI/time/association censoring, not physical cloud lifetimes.

`spectrum_validation.json`, `boundary_validation.json`,
`covariance_support_validation.json` and `frozen_validation.json` document
mathematical/numerical prerequisites. `validation.json` retains every ensemble
check, including failures if present. `references.json` records which primary
sources were actually accessible. `design_receipt.json`, `protected_inputs.json`,
the pre-existing diff/handoff and final hash/verification files retain provenance.

Read-only check from project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/stochastic_cloud_grf_20261111/verify.py
```

Relative intensity is uncalibrated and the presence mask is not optical
blockage. No old Ibrahim experiment or QKD/security/publication setting changed.
