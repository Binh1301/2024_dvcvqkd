# Saved-evidence verification

From repository root, run:

```powershell
paper_uav_hap_cvqkd/.venv/Scripts/python.exe -X utf8 -B paper_uav_hap_cvqkd/results/skr_vs_zenith_angle_20261019/verify_results.py
```

This verifies saved tables, source/input/output hashes, figures and preservation
of prior files. It does not reevaluate a source, channel, MI or SKR. The completed
producer refuses to overwrite `summary.json`.

The scientific producer is `run_sweep.py`; its small controls are in
`check_numerics.py`. A deliberate scientific replay must use a new sibling
directory under `results/`, a fresh startup manifest, the same hash-bound
request/manuscript and verified inputs, and the recorded project interpreter.
No new source moments or external dependencies are required. Do not run the
producer inside this completed namespace.

`build_report.py` renders the report from saved results. `run.log` records the
reference gate before the first sweep angle. `protocol.json` declares the finite
catalog objective and tolerances. The original immutable channel and homodyne
Holevo helpers are imported; only the channel's zenith angle is generalized in
this isolated producer. All plotted data come from the new angle evaluations.
`render_figures.py` makes the final layout from the saved CSV, with headroom
under the upper-right legend. Its receipt binds the unchanged numerical input.

Scope: manuscript-style normalized 2D MI plus homodyne Holevo, not validated
homodyne security. Catalog maxima are not continuous global optima. Frozen-hash
and lifecycle blockers remain unchanged; no publication or test-data access,
production baseline/threshold certification, Objective C restart, commit or push.
