# ALT_OPT exact diagnostic report

- Status: `ALT_OPT_DIAGNOSTIC_COMPLETE_WITH_UNRESOLVED_INNER_SEARCH`
- Scope: `DIAGNOSTIC_ONLY`
- Distance: `21.9393102292 km`
- Claim: `BEST_AO_EXACT_TESTED_CANDIDATE_ONLY_NOT_GLOBAL`

## Best exact-tested AO candidate

- Start: `0.1`
- nu_raw: `0.16500000000000001`
- V_A: `5.5`
- I_AB: `0.63418926311636525`
- beta I_AB: `0.60247979996054701`
- chi_BE: `0.52449880608660937`
- K: `0.077980993873937643`
- Run status: `INNER_SEARCH_FAILURE`

## Multi-start final rows

| Initial nu | Final nu | Final V_A | K | Iterations | Exact evaluations | Status |
|---:|---:|---:|---:|---:|---:|---|
| 0.10000000000000001 | 0.16500000000000001 | 5.5 | 0.077980993873937643 | 3 | 53 | `INNER_SEARCH_FAILURE` |
| 0.14999999999999999 | 0.16500000000000001 | 5.5 | 0.077980993873937643 | 2 | 6 | `INNER_SEARCH_FAILURE` |
| 0.29999999999999999 | 0.16500000000000001 | 5.5 | 0.077980993873937643 | 2 | 6 | `INNER_SEARCH_FAILURE` |
| 0.80000000000000004 | 0.40000000000000002 | 3 | 0.069125858219845626 | 3 | 9 | `INNER_SEARCH_FAILURE` |

## Accounting and limitations

- Requested objective calls: `232`
- Unique exact SKR evaluations: `74`
- Cache hits: `124`
- Missing exact source probes: `34`
- Numerical failures: `0`
- Source cache changed: `False`
- No interpolation of source moments or SKR was used.
- Physical AO and phase noise remained OFF; optimization AO is named ALT_OPT.
- The result is not a global-optimality proof.
