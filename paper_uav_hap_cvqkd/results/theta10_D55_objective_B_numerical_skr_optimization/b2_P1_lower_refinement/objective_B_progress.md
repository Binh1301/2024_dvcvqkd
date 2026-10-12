# Objective B lower P1 — preflight complete; fresh execution approval pending

This report distinguishes validated saved results from new calculations.
AP attempts0; new C,w/SKR/full AO0. Budget is proposed, not started or reused.
The required new AP, source CSV, 26-distance CSV and expanded-catalog AO results
will only exist after fresh execution confirmation and a valid source.

## Requested scientific answers

1. Single AP success: NOT_RUN, awaiting fresh execution confirmation.
2. New C,w: unavailable; no approximation/interpolation used.
3. K at `(0.165,5.496875)`: unavailable, not evaluated without source moments.
4. Ordering against VA5.5: unknown. No assumption or error-bound claim.
5. Incumbent change: no new calculation; saved best `(0.165,5.5)` remains
   `K=0.07798099387393764` at L21.9393102292km.
6. P1 bracket: saved/live-confirmed `[5.49375,5.50625]`, not advanced by this task.
7. Width reduction here: zero; current nominal width0.0125.
8. P1 completion: false, `SOURCE_MISSING_REFINEMENT`; zero completed coordinates.
9. Required request now: FIRST `(0.165,5.496875)`. Current paired SECOND
   `(0.165,5.503125)` is not authorized. Post-probe requests remain unknown.
10. AO/catalog agreement: saved original AO independently checked26/26;
    a fresh expanded-catalog AO recheck is NOT_RUN.
11. Improved distances: no new SKR or improvement claim; saved curve unchanged.
12. Blockers: missing exact P1/P2 moments, inner cap4 versus current bracket,
    unresolved outer directions and lack of certified total-K discrimination.
13. Conditional estimate: 13 balanced paired halvings for the actual radius
    criterion,14 loop visits to recognize closure. See P1_bracket_update.md;
    this is not a guarantee or an authorized cap change.
14. Safety: preflight AC/Sleep/restoration PASS; no AP worker was started.
    Actual scientific Job containment/termination/empty-Job verification must
    pass at execution time; historical cleanup is not substituted for it.

## Exact existing reference values

| VA, fixed nu_raw=0.165 | K (bits/use) | Scope |
|---|---|---|
| 5.49375 | 0.07798098033334322 | Saved exact source/objective |
| 5.496875 | NOT_RUN — exact source missing | Target, awaiting approval |
| 5.5 | 0.07798099387393764 | Saved incumbent |
| 5.50625 | 0.07798095622951573 | Completed upper probe |

No certified total-SKR error bound resolves the small saved differences.
All150 sources/3900 metrics/129 actual savedstarts/26 maxima reconciled;
1856 protected hashes unchanged;65 regression tests PASS. See scientific_preflight.md
and machine-readable provenance/checkpoints. Original evaluator/precision/
quadrature/MI/Holevo/AO/settings remain unchanged. NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

After fresh confirmation, requested scope is ONE lower pair only, <=120min total,
<=90min supervisor, unchanged60min internal timeout, >=30min reserve; no retry,
additional pair/P2, observer/profiler or dummy diagnostics. STOP after that attempt.
