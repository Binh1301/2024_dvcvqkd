# 145 MB exact catalog: cache-only validation and Batch3 plan

CURRENTLY_VERIFIED_PASS_CACHE_ONLY_DIAGNOSTIC

Verified145 pairs and3770 objectives, AO/catalog matches=26/26 (existing AO, freshly verified catalog).
Original evaluator repeats=24, missing objective completions=0, new AP=0.
Full26-distance maxima/runner-up/gaps in catalog_145_verification.csv; exact identities in source_145_provenance.csv.

## Answers to the10 requested questions

1. Existing ALT_OPT attains the current145-catalog maximum at26/26 distances; no new full multistart AO execution.
2.22km best currently exact-tested pair=(0.165,5.475), K=0.07661740491526092.
3. Nearest evaluated VA neighbors: [{"side": "lower", "nu_raw": 0.165, "V_A": 5.45, "K": 0.07661714229913241, "source_cache_key": "5764a134490ed68f96ff10357aa67c1f4f57b88f2bd1ca6a4a9a8498859f6644"}, {"side": "upper", "nu_raw": 0.165, "V_A": 5.5, "K": 0.07661685601911128, "source_cache_key": "77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c"}].
4. Both immediate VA neighbors and further available shoulders are lower: sampled local maximum. Not a continuous maximum certificate.
5. Reference best=(0.165,5.5), K=0.07798099387393764. Original channel replay matches saved inputs exactly: T_eff=0.2011265222214531 at reference versus0.19841067967448092 at22km. K(5.475)-K(5.5)=-3.620594889452988e-7 at reference, versus+5.488961496435962e-7 at22km. Both distance-dependent inputs and exact ordering consistently select the different points; no evidence of a coding error. No assertion that numerical error is impossible.
6. ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED: all24 reevaluations reproduce stored metrics, but no compatible rigorous total-objective bound exists; gains are numeric ordering only.
7.54 unique missing pairs, independently recovered from618 calls;312 boundary/306 bracket-source-missing invocations are different units.
8. Exactly3 missing original midpoint ensembles: ((0.165, 5.4625), (0.165, 5.4875), (0.16531250000000003, 5.5)); binary64 hashes in batch_3_selected_probes.csv. NOT_RUN.
9. TwoVA shoulders refine the22km peak (upper shared with reference); one nu midpoint on5.5 reference ridge gives complementary shaping coverage. No guaranteed improvement or closure.
10. Conditionally justified for targeted coverage/sensitivity, not another expensive run merely to reproduce the finite maximum. Total-error evidence is still insufficient to certify tiny physical gains. Stop: no new AP authorized.

## Both directions and alternative distances

AtVA5.475 the only evaluated nu=[0.165]; bracket=[None, None]. Original lower outer request(.0825,5.475) is missing. Opposite(.33,5.475) is not yet requested because the original search stops on the missing lower side; it remains unchecked, not closed.
Selected third nu midpoint(.16531250000000003,5.5) closes neither side atVA5.475. It is selected because a true two-sided local bracket already exists onVA5.5 with fine neighboring nu values;(.16375,5.5) is deferred for prior3600s timeout.
20/21 alternative(.15,6.375) ranks next, between measured6.25/6.5 (20km currentrunner-up/best); broader sampling and no cross-reference shaping information.23km(.165,5.35) and24km(.15,5.25) remain ranked alternatives with measured neighbors; unknownK is never predicted.
Missing_source_ranking.csv provides all54 keys/hex representations, unique affected-call counts, original events, distances, measured neighborK, timeout history and qualitative runtime risk.

##139 ->142 ->145 at22km

| Catalog | best nu | best VA | K | runner-up gap | increment | cumulative |
|---|---|---|---|---|---|---|
|139|0.165|5.5|0.07661685601911128|1.3629724421315714e-06|0.0|0.0|
|142|0.165|5.45|0.07661714229913241|2.8628002113340045e-07|2.8628002113340045e-07|2.8628002113340045e-07|
|145|0.165|5.475|0.07661740491526092|2.626161285101958e-07|2.626161285101958e-07|5.488961496435962e-07|

Second measured increment is smaller than the first, but two increments do not establish an asymptotic diminishing-gain law or predict Batch3.
No source/scientific/optimization/settings changes or interpolation.145 catalog unchanged. Existing source moments reused only for24 diagnostic reevaluations and any missing valid objectives; all prior artifacts hash-protected.
35 current scoped tests and git diff --check PASS;856 protected files unchanged. Diagnostic wall=42.92200000000594s, main-process CPU=24.28125s (test subprocess CPU excluded). Final read-only scientific artifact verification PASS; see final_preparation_verification.json. Missing_source_ranking.csv and batch_3_selected_probes.csv additionally contain exact parameter differences from every affected distance's selected optimum, without inferring unknownK.
Frozen-spec historical hash discrepancy remains PREEXISTING_UNCHANGED; no publication/training/test/baseline/threshold approval. Stop after planning.
