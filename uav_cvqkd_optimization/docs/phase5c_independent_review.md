# Phase5C independent review

What this change does: The wrapper performs a bounded, full-catalog reproduction at five distinct geometries, then evaluates the same catalog with channel noise changed from 0.0186 to 0.0136. It uses the unchanged native diagnostic evaluator and keeps the original validated physical-context lineage separate from the active noise protocol.

Review date: 2026-11-07. Expected load: one local, deterministic pilot process. Review scope is the originally executed wrapper, now archived at `docs/phase5c_validation/executed_producer_snapshot.py`, its connected native evaluator/helper flow, tests, and the actual `results/phase5c_skr_noise_pilot_20261107` records. Subsequent implementation fixes are outside this independent review.

## Must fix before reusing the wrapper

1. **A reproduction checkpoint can be accepted as a target checkpoint.** Executed wrapper lines 148-152 validate the point, shared input-manifest digest, and self-seal, but omit the stage and active noise protocol. Copying `reproduction/p0.json` and its seal into an unfinished run's `target/p0.json` and matching seal path satisfies every existing checkpoint acceptance condition; the target stage then uses a historical-noise result without evaluating target noise. This was reproduced by evaluating the guard conditions against the saved reproduction record, without modifying any result. Validate stage, trial configuration, active effective protocol, original physical-protocol digest, exact candidate roster, and scalar/winner consistency on resume. Otherwise a recovered run can falsely report successful target evaluation.

2. **Historical gate inputs lack complete historical binding.** Executed wrapper lines 118-123 trust the current source-pool CSV before binding its current digest, while lines 174-175 read historical candidate CSVs that are neither checked against the original final manifest nor included in the pilot input manifest. The phase5b audit verifies context JSON files, not those candidate CSVs. Altering a candidate CSV within the reproduction tolerance permits the gate to pass against an altered baseline without recording that baseline's identity. Verify the original final-manifest hashes for the pool and all five comparison CSVs, and bind them as execution inputs. Otherwise the reported reproduction comparison lacks a fully identifiable reference.

These findings concern guard completeness. Independent checks below found neither problem in the actual completed fresh pilot. The implementation owner was notified before fixes and reported that all 2,120 candidate calls in this run were fresh.

## Actual saved artifact verification

`CURRENTLY_VERIFIED_PASS` for read-only artifact checks performed during this review:

- All 24 output-manifest entries matched the saved files. All 552 input hashes and all 59 recorded repository producer hashes matched at review time. The normalized configuration digest matched the manifest.
- The historical `source_pool.csv` and all five comparison candidate CSVs matched their original `final_manifest.json` hashes. This independent check closes the factual uncertainty for this completed run; the original wrapper did not enforce it.
- All ten checkpoints identify the correct stage, active effective protocol, trial configuration, and input manifest. Each contains the exact ordered 212-source roster with unique ensemble hashes: 179 MB and 33 Uniform candidates.
- Both family winners in every checkpoint equal the first catalog occurrence of the maximum signed `K_raw`. No clipped-rate selection was observed.
- All 1,060 reproduction rows match historical binary64 values exactly for `eta_f`, `xi_f`, `I_AB`, `chi_BE`, and `K_raw`: maximum absolute deviation is zero for each metric.
- The physical contexts are identical between reproduction and target at each position. Across all 2,120 rows, recomputing `N_effective=(m1-mh**2)*VA+xi_ch*m1+xi_det*M0` gives zero residual; `eta_f=mh**2`, `xi_f=N_effective/eta_f`, and `K_raw=beta*I_AB-chi_BE` also match exactly.
- The largest saved GH64/128 MI difference is `4.440892098500626e-16`, below the native `2e-10` threshold. Native source validation and 80/110-digit Holevo checks remain in the executed evaluator. This review did not independently recompute quantum quantities.
- Every candidate retains `security_valid=false`. The results remain diagnostics, with source evidence and publication/lifecycle status unchanged.

| Position (m) | Reproduction MB K | Target MB K | Target Uniform K |
|---|---:|---:|---:|
| (1000,1000) | 0.0007960878080861267 | 0.00495533778991275 | -0.03000649966888367 |
| (1480,1000) | 0.0007904843942003748 | 0.004948237183717591 | -0.03000484793620073 |
| (0,0) | 0.0007470670338268481 | 0.004893349597699492 | -0.029992343745430194 |
| (1000,960) | 0.000796048935176985 | 0.004955288516825029 | -0.0300064881795543 |
| (40,0) | 0.0007490046937105033 | 0.004895794346111787 | -0.029992890955648756 |

All five MB winner identities are unchanged by the noise adjustment. The supplements are explicitly lookup-ranked high/low positions with distinct radii; they are not an independent validation sample or evidence of a continuous optimum.

## Runtime interpretation

The actual map contains 2,601 rows and **294 distinct squared radii**, confirmed independently from coordinates. A 325-context recipe additionally includes a separate zenith sweep and overcounts map-only regeneration.

The recorded process took 38.0596656 seconds, including 6.6376653 seconds of preparation and both stages. Target context plus evaluator time was 12.6508435 seconds over five geometries. Linear scaling to 294 geometries gives about 743.87 seconds (12.40 minutes), before exports/preparation. Reproduction context plus evaluator time was 18.4568625 seconds, giving 1,085.26 seconds (18.09 minutes) if its colder cost persists. These are local runtime projections, not completed full-map measurements or authorization to run them.

Verdict: The completed pilot artifacts pass independent scalar/provenance checks. Fix findings 1 and 2 before reusing the orchestration wrapper; preserve the completed run and its executed producer bytes.

Not checked: No new quantum evaluations, Z/w mathematical revalidation, held-out data, full-map regeneration, publication certification, or second review of subsequent fixes. Positive diagnostic K does not establish security certification.
