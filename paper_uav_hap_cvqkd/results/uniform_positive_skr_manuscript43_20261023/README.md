# Reproduction and read-only verification

Run from paper_uav_hap_cvqkd with .venv/Scripts/python.exe -X utf8 -B.
Read-only check: results/uniform_positive_skr_manuscript43_20261023/verify.py

Producer sequence (use a new isolated output namespace for reproduction):
source_job.py VA: historical GMP launcher, recorded OS policy failure.
source_python_job.py VA: unchanged full-support kernel/precision, standard MP Python backend.
search.py screen: prospective protocol Stage A/B/C and separate secondary screen.
complete_search.py extend: extra divergence60/raw normalization and selected checks.
complete_search.py finish: fresh available sources, comparisons and matched curves.
check_guards.py / independent_bounded.py: isolated boundary/independent moment checks.
write_outputs.py: saved data only; writes CSV source labels, report and three PNG/PDF pairs.

Do not rerun completed numerical phases or overwrite old caches/receipts.
No new package or production change. New exact sources are versioned under new_exact_source.
All maxima are best exact-tested; security remains provisional.
