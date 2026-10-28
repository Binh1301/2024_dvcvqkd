# LaTeX revision: optimization through conclusions

Upload `overleaf_III_B_revision.zip` into a new Overleaf project. The package
contains a self-contained `main.tex` with an inline bibliography and two vector
PDF figure assets. PNG previews at 350 dpi are available in `figures/`.

The user explicitly chose **LaTeX and figures only, without compilation** on
2026-10-21. No revised `main.pdf` is supplied. LaTeX overflow, float placement,
rendered equation widths, and occupied page length remain unverified.

Before that choice, automatic approval review rejected downloading the official
portable Tectonic executable, citing the earlier read-only request. The download
was not performed, and no external compiler was executed.

The reference PDF was located locally and matched its recorded SHA-256. Its
pages 4--6 informed the optimization flow, single-column algorithm/table/figure,
wide two-panel comparison, and short conclusion. No equations or numerical
results were imported from that paper.

Scientific paragraphs and equations before optimization are unchanged. The
source snapshot lacks a separate Introduction. Necessary heading changes create
Sections II and III.A, after which LaTeX automatically produces III.B, IV, and V.
The two requested figure numbers are retained as 2 and 3 using a figure-counter
offset: there is no authenticated preceding system illustration in this source.
This numbering reservation is explicit, not a fabricated Fig. 1.

See `revision_report_vi.md`, `validation_report.md`, `figure_manifest.csv`, and
`validation/static_checks.json` for provenance and limitations. Static recheck:

```powershell
python -X utf8 -B results/manuscript_globecom_III_B_revision_20261021/verify_revision.py
```

No SKR/channel/source calculation, source optimization, Greedy/DP execution,
cloud generation, or new statistical resampling was performed. Production and
historical results were preserved. No commit or push was made.

UNVALIDATED_SECURITY_MODEL

NOT_READY_FOR_PUBLICATION_SCALE_RUNS
