# Original P1 update — exact lower dependency resolved, search not complete

At L=21.9393102292km, fixednu0.165, original P1 retains bestVA5.5,
K0.07798099387393764. New lowerVA5.496875 givesK0.07798099350667076,
delta-3.6726688357191506e-10; total-SKR discrimination is NOT_ESTABLISHED.

Actual bracket: `[5.49375,5.50625]` -> `[5.496875,5.50625]`.
Binary64 widths0.01249999999999929 ->0.009374999999999467, nominal25% narrower.
New width/tolerance~9375, actual maximum-neighbor radius/tolerance~6250.
Radius remains0.006249999999999645: progress on the lower side has not moved
the upper neighbor. This update comes from original exact catalog/search logic,
not a forced shrink or a fit.

Status `BRACKETED_EXACT_CATALOG_SOURCE_MISSING`, reason
`SOURCE_MISSING_REFINEMENT`, completion false. One exact dependency resolved;
zero additional completed paired-refinement levels, zero closed coordinates.
The next original paired requests are FIRST(.165,5.4984375),
SECOND(.165,5.503125), both missing and NOT executed.

Actual criterion is `max(best-lower,upper-best)<=1e-6`, not full width.
IDEALIZED fixed-best both-sides midpoint halving:13 additional paired levels
for the radius criterion,14 loop visits including its pre-evaluation closure
check. Full-width <=1e-6 would need14 halvings. These are estimates, not guarantees.
After four idealized paired levels radius would remain~0.000390625,~390.625
tolerances; current inner cap4 cannot close this starting bracket in one such
call. Missing sources block it sooner. Cap/tolerances/algorithm unchanged.
P2, outer closure and total-K numerical discrimination remain unresolved.

Exact traces: reference_P1_refinement.csv, cache_only_searches.json,
coordinate_search_status.csv and final_verification.json. No convergence/global
certificate; STOP, no automatic follow-up AP.
