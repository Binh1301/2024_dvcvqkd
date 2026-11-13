# Eq14 cloud attenuation diagnostic

Read report_vi.md and execution_summary.json.
Fixed and reselected finite 212-source catalog only; continuous global reoptimization NOT_RUN.
Uncertified Cw; never an operational/security outage threshold.

Data: critical_thresholds.csv, critical_threshold_map.csv, threshold_maps.npz, geometry-level CSV/JSON and artifact_hashes.json.

Read-only verification:

.venv/Scripts/python.exe -X utf8 -B results/cloud_threshold_eq14_diagnostic_20261112_v4/verify.py

The delivered package retains 72 completed full-sweep checkpoints. A new run without these checkpoints uses fewer full raw curves and more sign-bound grid groups; it evaluates the same root neighborhoods and 0..100 dB coarse sign checks.
