# Lightweight 8 cm UAV receiver — parameter-only diagnostic

Start with `report_vi.md`, `table_1_recommended_parameters.csv`,
`table_2_engineering_comparison.csv` and `detector_scenario_best.csv`.
Signed rates are retained; negative references are not working designs.

Read-only verification from the project directory:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/verify.py
```

This verifier imports no evaluator and runs no search. `--seal` is a one-time
packaging operation. Do not rerun completed scientific stages for stored-data
questions or overwrite sealed artifacts.

The executed stages, in order:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/run_study.py physical
.\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/run_study.py source
.\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/run_study.py finish
.\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/validate_study.py
.\.venv\Scripts\python.exe -X utf8 -B results/lightweight_uav_positive_skr_20261022/build_report.py
```

Each numerical stage refuses to overwrite its completed receipt. Interrupted
stages resume from exact-node JSONL, with model hashes checked. Full fresh
reproduction requires a separately authorized result namespace, a new startup
snapshot, and the same hash-bound inputs; preserve this completed namespace.

`run_study.py` is staging only: it imports the preceding `numeric.py` unchanged.
There is no new mathematical/security implementation, dependency, source-cache
generation or interpolation. `validate_study.py` uses the existing independent
validation helpers. `build_report.py` renders saved data only. All imported
model bytes and original artifacts are protected by `startup_manifest.json`.

Only detector noise .0135/.005 SNU and efficiencies .8/.85/.9/.95 are allowed.
Receiver diameter remains .08m. Residual optical centering is not UAV GPS
precision. HAP20/UAV1km heights are retained because a calibrated vertical
extinction profile was not supplied. No kg/W/flight-time claims are made.
No training, final-test, heldout, publication, AP, model/security change or
production baseline/threshold approval. Existing security/hardware limitations
and NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain in force.
