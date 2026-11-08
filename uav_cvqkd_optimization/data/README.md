# External scientific inputs

No paper-result data are bundled. The demo synthesizes a spatial SKR table using
its explicitly configured analytic fixture and writes the computed values to
skr_input.csv. Every synthetic table and plot carries its data-status label.

SKR input contracts (coordinates in meters, rates in bits/channel use):

- Python array: `SKRLookup.from_array(rows, coordinate_units='m', rate_units='bits/use')`
  with rows `[x_m, y_m, skr_bits_per_use]`.
- `.npy`: the same finite N x 3 numeric matrix (no pickle).
- `.npz`: `points` N x 2 and `rates` N; no object arrays.
- `.csv`: header `x_m,y_m,skr_bits_per_use`. Additional columns are ignored.

Coordinates must span a 2D convex hull. Duplicates, nonfinite inputs and queries
outside the convex hull fail. Rates retain their signed scale; no extrapolation
or implicit unit conversion occurs. Linear triangular interpolation is used.
Paper YAML must explicitly supply `coordinate_units: m`, `rate_units: bits/use`,
the file SHA256 and its scientific provenance. The code cannot establish that
external author-supplied provenance is truthful or that a rate has a security proof.

Clouds: supply `cloud.clusters` in YAML, or `cloud.file` pointing to UTF-8 JSON
`{"clusters": [...]}`. Each entry includes amplitude (mg/m³), center (m), sigma
(m), optionally covariance (m²) and velocity (m/s). Default velocity is the
configured field velocity. No random noise is added to fake Gaussian texture.

File paths are relative to the config file. Record realization identity and
independent calibration/experiment provenance. A 50x50 cloud display samples
cell centers at 40 m spacing for the 2 km square. The analytic Gaussian field
continues outside that square so moving clouds enter/leave without wraparound.
