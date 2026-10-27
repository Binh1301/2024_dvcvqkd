# Minimal physical-change diagnostic

Read `report_vi.md` or `executive_conclusion_vi.md` first. The authoritative
three-candidate shortlist is `final_selection.json`, after the local 40 cm
refinement and joint pointing-degradation checks. `selection.json` preserves
the earlier automated shortlist; its 75 cm regression reference is not a final
recommendation.

Tables A/B/C are `table_A_baseline_sensitivity.csv`,
`table_B_positive_candidates.csv`, and `table_C_minimum_improvement.csv`.
Seven vector PDF and 350 dpi PNG figures are in `figures/`. `search_coverage.csv`
records the staged, incomplete Cartesian coverage. A negative sampled region
does not prove infeasibility for all sources or physical designs.

From the project directory, verify saved artifacts without rerunning science:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/minimal_physical_positive_skr_20261022/verify.py
```

`numeric.py` reuses the previous bounded optical/full-Z model and accelerates
the same pooled fading likelihood. `search.py` and `refine.py` log evaluated
nodes; `checks.py` runs independent scoped numerical checks; `finish.py` renders
the saved data. Numerical producers refuse to overwrite completed selections.
Do not rerun them to answer stored-result questions. The one-time `--seal`
option creates `final_receipt.json`; the default verifier is read-only.

All rates are untrusted-detector numerical diagnostics. Hardware calibration,
platform SWaP and operational security remain unvalidated; publication-scale
training, final tests, new AP/source generation and production approval were
not performed. Historical artifacts and source caches are hash-protected.
