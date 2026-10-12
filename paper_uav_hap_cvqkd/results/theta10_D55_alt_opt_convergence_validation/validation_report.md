# ALT_OPT convergence validation

Status: VALIDATION_COMPLETE_WITH_UNRESOLVED_EXACT_SOURCE_PROBES

Provenance: PROVENANCE_VERIFICATION_PASS; original cache and artifacts preserved: True.
epsilon_opt=1e-08, parameter tolerance=1e-06, outer max=6. See ao_stopping_criteria_audit.md for original/new conditions and code locations.
Missing requests=836; unique cache keys=50; unique exact ensemble hashes=50.
Representative continuation adds 0 previously unrequested exact keys; total remaining unique keys=50. Historical and current request counts are separate in the priorities ledger.
New exact sources completed=0; pilot compute=860.313000 seconds. Per-probe timeout=90.0; total budget=270.0. All unavailable probes remain listed in missing_source_priorities.csv and source ledgers.
Timing limitation: measured source elapsed exceeded configured total budget=True. Original probe logged 855.172 s inside the fallback and 860.313 s under the controller despite its configured 90 s timeout. Cause is not established by the partial profile. The original ledger/report/script are preserved; supervisor is corrected to absolute-deadline polling and a Windows Job Object CPU/descendant cap. No additional source probe was launched after the elapsed budget was exhausted.
Representative gate passed=False; remaining-distance optimization executed=False. Nonrepresentative rows are explicit LAST_KNOWN data. No global optimum is asserted.
epsilon_opt=1e-8 is the existing optimization stopping threshold, not an independent source-moment/SKR error certificate. The source acceptance tolerance and the inner parameter-resolution tolerance are different conditions. A historical frozen-spec raw hash mismatch remains recorded; the model document is unchanged and publication lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
Max absolute K change on updated/last-known table=0.0. Python tests PASS=True; git diff --check PASS=True.

## Parameters and exact SKR

| L | nu_raw | VA | I_AB | beta I_AB | chi_BE | K | execution | status |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 20 | 0.15 | 6.5 | 0.9922672378103532 | 0.9426538759198355 | 0.8046403446386736 | 0.1380135312811619 | REVALIDATED_REPRESENTATIVE | STAGNATED_IN_EXACT_CATALOG |
| 21 | 0.16 | 6.0 | 0.7994041237646186 | 0.7594339175763876 | 0.6567267537613342 | 0.1027071638150534 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 21.9393102292 | 0.165 | 5.5 | 0.6341892631163653 | 0.602479799960547 | 0.5244988060866094 | 0.07798099387393764 | REVALIDATED_REPRESENTATIVE | STAGNATED_IN_EXACT_CATALOG |
| 22 | 0.165 | 5.5 | 0.6272560789316337 | 0.595893274985052 | 0.5192764189659407 | 0.07661685601911128 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 23 | 0.165 | 5.3 | 0.5044668703810062 | 0.4792435268619559 | 0.421786127447219 | 0.05745739941473693 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 24 | 0.15 | 5.0 | 0.3942801224907866 | 0.37456611636624726 | 0.33119452853845077 | 0.04337158782779649 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 25 | 0.15 | 4.5 | 0.293228779002499 | 0.27856734005237405 | 0.24541160447081678 | 0.033155735581557266 | REVALIDATED_REPRESENTATIVE | UNRESOLVED_BOUNDARY |
| 25.5 | 0.15 | 4.5 | 0.264775835244901 | 0.25153704348265593 | 0.22244252890643645 | 0.029094514576219477 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 26 | 0.15 | 4.5 | 0.23914269755355466 | 0.22718556267587692 | 0.2015867593761862 | 0.02559880329969072 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 26.5 | 0.15 | 4.5 | 0.21611628821602968 | 0.20531047380522818 | 0.18272415201828895 | 0.02258632178693923 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 27 | 0.15 | 4.5 | 0.19547823785273355 | 0.18570432596009687 | 0.16571788437780421 | 0.019986441582292652 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 27.5 | 0.15 | 4.5 | 0.17701217700944571 | 0.16816156815897343 | 0.1504227903586819 | 0.01773877780029154 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 28 | 0.15 | 4.5 | 0.16050910765740234 | 0.15248365227453223 | 0.13669179548292298 | 0.015791856791609243 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 29 | 0.15 | 3.5548673904962893 | 0.10575417742935844 | 0.10046646855789051 | 0.08783271595244191 | 0.012633752605448606 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 30 | 0.15 | 3.5548673904962893 | 0.08788386107132551 | 0.08348966801775923 | 0.07323616401917787 | 0.010253503998581354 | REVALIDATED_REPRESENTATIVE | UNRESOLVED_BOUNDARY |
| 30.5 | 0.15 | 3.5548673904962893 | 0.08036621528300625 | 0.07634790451885594 | 0.06706977612685439 | 0.009278128392001553 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 31 | 0.15 | 3.5548673904962893 | 0.07365069260605406 | 0.06996815797575136 | 0.061548182344572044 | 0.008419975631179313 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 31.5 | 0.15 | 3.5548673904962893 | 0.06764473475002841 | 0.064262498012527 | 0.05659936283473854 | 0.007663135177788452 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 32 | 0.15 | 3.5548673904962893 | 0.06226631123158022 | 0.05915299567000121 | 0.052158974213721176 | 0.006994021456280031 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 32.5 | 0.15 | 3.5548673904962893 | 0.057442922410046116 | 0.05457077628954381 | 0.04816975543839641 | 0.006401020851147396 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 33 | 0.15 | 3.5548673904962893 | 0.05311062447287673 | 0.05045509324923289 | 0.044580900942979174 | 0.005874192306253717 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 34 | 0.15 | 3.5548673904962893 | 0.04570081258740544 | 0.043415771958035164 | 0.038429603594257955 | 0.004986168363777209 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 35 | 0.15 | 3.5548673904962893 | 0.039662921785399874 | 0.03767977569612988 | 0.03340460238907106 | 0.004275173307058823 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 36 | 0.15 | 3.5548673904962893 | 0.034707839732034174 | 0.03297244774543246 | 0.029271893305744534 | 0.0037005544396879267 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 38 | 0.15 | 3.5548673904962893 | 0.027201598959703865 | 0.02584151901171867 | 0.022995174486814207 | 0.0028463445249044643 | NOT_RUN_REPRESENTATIVE_GATE_UNRESOLVED | LAST_KNOWN_EXACT_TESTED_CANDIDATE_ONLY |
| 40 | 0.15 | 3.5548673904962893 | 0.021927193923437116 | 0.020830834227265258 | 0.018571951474997128 | 0.00225888275226813 | REVALIDATED_REPRESENTATIVE | UNRESOLVED_BOUNDARY |

## Exact-source pilot

- nu=0.15, VA=4.027433695248145: TIMEOUT, 860.3129999999983 seconds; FloatingPointError: full-support fallback failed closed: fallback timeout

## Acceleration and precision review

C,w source rows can be shared across distances; exact duplicate probes deduplicated. Cache holds C,w only, no reusable eigensystems. Changing nu/VA changes Gram operators: no cross-ensemble matrix reuse asserted. Original worker uses repeated solves for diagonal systems; a direct diagonal division acceleration would require independent validation and a new execution identity. No source mathematics or precision ladder was changed.

The fixed 1050/1250/1450 precision ladder is retained; it cannot be reduced from these runtime outcomes. Partial live profiles identify where the original worker spent pilot time. Timeouts do not receive SKR values and do not erase successful cache rows. Resume uses --resume, the same verified input manifest and persistent overlay. Timed-out probes are skipped unless --retry-failures is explicitly supplied with a larger budget.

## Numerical verdict

No distance is promoted to convergence solely from an unchanged iterate. A corrected terminal state may be STAGNATED_IN_EXACT_CATALOG or UNRESOLVED_BOUNDARY. All missing coordinate/outer probes and final-pair checks are explicit in the CSVs. Continuous global optimality and publication readiness remain unresolved.
