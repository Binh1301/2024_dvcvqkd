# UAV receiver / detector / payload trade-off diagnostic

Start with `report_vi.md`, `selected_designs.csv`, TablesA–D and
`UAV_mass_power_evidence.csv`. All rates are signed model diagnostics, not
hardware/security-certified operating rates.

Read-only verification from the project directory:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/verify.py
```

The verifier imports no evaluator. Its `--seal` switch is a one-time packaging
operation, never a scientific rerun. Do not overwrite sealed artifacts.

Executed producer order:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/run_study.py physical
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/run_study.py source
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/complete_source_coverage.py
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/refine.py
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/refine_minimum.py
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/validate_study.py
.\.venv\Scripts\python.exe -X utf8 -B results/uav_skwap_aware_positive_skr_20261022/build_report.py
```

Numerical phases refuse to overwrite completed phase receipts. The exact-node
JSONL permits interrupted work to resume under the same parameter/model hashes.
For a fresh reproduction, use a new authorized namespace and startup snapshot;
preserve this experiment, all historical outputs and exact source caches.

`parameter_adapter.py` exposes receiver diameter to the existing circular
collector. Propagation, moments, untrusted covariance, full-Z Holevo and source
normalization remain imported unchanged. Actual MI reuses identical historical
bytecode with aperture-aware quadrature input. Matching regressions and direct
likelihood/collector checks establish numerical consistency, not security.

`complete_source_coverage.py` includes cached Stage-A points when selecting the
physical/source coordinate set; stage metadata is not mathematical membership.
Its original optimization snapshot is preserved. Critical roots use one fixed
common exact source, optics, geometry and pointing scenario; they are not a
global minimum. Rounded receiver points are evaluated directly and refined.

Hardware evidence is primary-source manufacturer/prototype data for separate
reference components. It is not a validated BOM for the three designs. Unknown
total mass, electrical operating power, compatible repetition rate, external
availability and energy/duty/flight duration remain explicitly unknown. No
fabricated bit/s, J/bit or sortie yield; no double-counting integrated terminals.

No below-.005 detector noise, trusted detector, new model/equation/distribution,
AO, source moments/AP, production baseline/threshold approval, training,
final-test/heldout/publication or lifecycle promotion.

`refine_minimum.py` preserves the completed initial shortlist in `selection_phase1/`,
then checks at most three local diameter/source coordinates using the selected
exact MB source. Its separate roots do not replace the common-source detector
comparison or establish a global minimum.
