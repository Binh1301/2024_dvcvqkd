# IEEE manuscript revision for internal review

This isolated revision integrates four unchanged final numerical PDF figures
and the verified saved-data discussion. Build `main.tex` with a standard
IEEEtran-capable LaTeX environment, or the recorded portable Tectonic toolchain:

```powershell
& C:/Users/HP/.codex/tools/manuscript-tex-20261020/tectonic.exe --keep-logs --keep-intermediates main.tex
```

The latest corresponding `.tex` source was not found in the repository,
Documents, Desktop, Downloads, or attached files. `original/manuscript_latest.pdf`
is the authoritative three-page manuscript. Its system/optimization equations,
title, authorship and affiliations are reconstructed here; its placeholder
results are replaced. The preamble and author block are copied verbatim from
the available older `original/HAP_UAV_Availability_Mobility_Overleaf.tex`.
That older file's moving-circle cloud and availability objective are **not**
imported into this revision. No claim of a textual diff against unavailable
latest LaTeX is made. The supplied package list is retained with one necessary
build fix: `fontenc` with T1 encoding makes IEEEtran's Times/Courier families
available under Tectonic/XeTeX. The bibliography basename is `manuscript_refs`
to avoid a Windows/Tectonic collision with the `references/` directory.

Files:

- `main.tex`: original package configuration/authors; provisional abstract,
  review status, conclusion, section includes, bibliography.
- `system_and_method.tex`: P1/P2/P3, Greedy, Bellman recursion and algorithm;
  explicit security-model qualification. The original numbered mathematical
  chain (1)–(15) is retained; the audit formulas are unnumbered.
- `numerical_results.tex`: sections III.A–F and four full-width PDF figures.
- `manuscript_refs.bib`: four primary references, with verified metadata. The latest
  supplied PDF contains no bibliography; no unavailable entries were invented.
- `figures/`: byte-identical copies of the four final PDF figures.
- `validation/`: direct saved-artifact/numerical/LaTeX checks and receipt.
- `references/`: primary-paper PDFs and saved PDF text extraction.

Required author decisions before submission:

1. Choose a physical Bob measurement and approve consistent MI/Holevo/noise
   equations; the current combination is inconsistent. Corrections have not
   been applied or simulated.
2. Approve correlation-domain treatment and effective-fading MI/security
   assumptions, outage conditioning, parameter estimation and key aggregation.
3. Resolve the frozen-model historical hash discrepancy without erasing history.
4. Supply/confirm the latest original LaTeX for an exact-source merge, and fill
   the original `TBD` author names and `XXX` affiliation. These are preserved.
5. Confirm target venue/page limit and formatting. No page limit was supplied.
6. Review finite-catalog boundary, synthetic clouds/geometry, offline future
   information, tracking/reacquisition omissions, and distance-versus-energy
   limitations. Further experiments require separate authorization.

`UNVALIDATED_SECURITY_MODEL`; `NOT_READY_FOR_PUBLICATION_SCALE_RUNS`.
This is a completed numerical manuscript revision for internal review, not a
publication-ready quantum-security claim.
