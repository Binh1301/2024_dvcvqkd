# Phase 5D independent correctness review

What this change does: It measures the existing 212-candidate search on 50 actual grid geometries in serial and with two spawned workers. It also computes finite-size sensitivity from sealed pilot rates and prepares a separately approved full lookup executor.

Review status: initial code review, 2026-11-08. The benchmark was running during this inspection. No tests, quantum evaluations, or large-tree hash checks were run by this reviewer, and no implementation file was changed. Findings were sent to the implementer before benchmark completion. This document does not claim that the running measurement or future full executor has passed final validation.

## Must fix before calling the future executor ready

1. **Interrupted writes can make a valid full run impossible to resume** (`src/uav_qkd/lookup_benchmark.py`, `_write_new`, `_run_stage`, `full_regeneration`).
   - What this is: The driver promises sealed per-point checkpoints and resume for a potentially long full search.
   - Problem: A crash leaving `f0000.json.partial` makes the next exclusive temporary-file creation fail. A crash after the JSON rename but before seal creation causes an unconditional missing-seal read. After all evaluations, an interruption after CSV creation or during NPZ creation similarly fails on the next exclusive export. A summary written before the output manifest permanently trips the completed-output guard even if the final seal was never written.
   - Fix: Recover only owned interrupted files after config/input identity checks; validate or safely recompute unsealed checkpoints. Export atomically and make finalization recoverable, while keeping fully sealed results immutable.
   - If skipped: A routine interruption can strand an expensive run despite all previous scientific checkpoints being intact. Add software-only interruption fixtures at each boundary and verify no unnecessary evaluator calls on recovered sealed points.

2. **The generated CSV is rejected by the package's existing CSV loader** (`lookup_benchmark.py`, full CSV export; `src/uav_qkd/skr_lookup.py:79`).
   - What this is: The executor prepares CSV and NPZ representations of the same lookup.
   - Problem: CSV writes `K_raw_bits_per_use`, while `SKRLookup.load` requires `skr_bits_per_use`. Calling the existing loader on this export raises the missing-header error.
   - Fix: Include the loader's established rate column, with its signed raw-rate meaning made explicit. Exercise CSV and NPZ loading and compare their points and rates in a software fixture.
   - If skipped: Users cannot load the promised CSV through the supported package interface.

## Should fix before author approval of a full run

3. **Checkpoint schema checks accept missing family winners and promoted labels** (`lookup_benchmark.py`, calls to inherited `validate_checkpoint`).
   - What this is: Resume checks checkpoint values against the exact roster and active protocol.
   - Problem: The inherited validator loops over whatever winner keys are supplied, so an empty winner dictionary passes. It also omits candidate `source_evidence_class` versus roster `classification`, and the false security/publication flags. A sealed fixture with a missing Uniform winner can therefore pass validation and produce an incomplete export; a missing MB winner fails late during export.
   - Fix: Add strict checks in the new module for exactly both family winners, unchanged evidence classifications, and false security/publication flags; retain the protected old module unchanged. Test removed-family and promoted-label fixtures.
   - If skipped: The claimed fail-closed boundary does not enforce the output schema and evidence labels it promises.

4. **Detached NPZ output loses the promised provenance identity** (`lookup_benchmark.py`, `np.savez_compressed`).
   - What this is: The saved NPZ contains points, rates, units, noise and one publication flag.
   - Problem: It omits config/input/pool hashes and source evidence labels. Copying only this normal interchange artifact away from its directory loses the binding needed to interpret its rates.
   - Fix: Include the relevant immutable manifest/config/pool identities and evidence labels as non-pickled scalar/array metadata; test round-trip preservation.
   - If skipped: Provenance remains dependent on manually keeping sidecar files with the array.

## Positive findings and review limits

- All 212 candidates are evaluated at every selected geometry, with a separate signed-rate argmax for MB and Uniform; no pruning or fixed-winner shortcut was found.
- Benchmark selection spans the center through the farthest radius deterministically. The actual-grid uniqueness check exists in the focused test.
- The parent retains the initialized engine during the parallel stage. Reported RSS is explicitly a sampled parent-plus-descendant sum, with possible shared-page double counting; CPU sampling limitations are also stated. These measures should be described as this executor's footprint, not an intrinsic worker-only peak.
- Native context creation preserves the original physical protocol; the active effective protocol changes only the accepted noise boundary. This review does not revalidate quantum mathematics or source C/w values.
- The finite-size formula and strict integer threshold follow the stated proxy. The implementation preserves float input values in Decimal threshold arithmetic, calls the existing finite-key helper for the actual penalty, and discloses float cancellation near the strict threshold.
- Valid-signal count already includes clear exposure. Cloud appears once in `n=f_s*eta_valid*c*T`; no second rate erasure was found. `f_s`, `eta_valid`, and mission `m0` remain unassigned.
- Finite-size output refuses an existing nonempty directory. Pilot output and checkpoint seals are checked before borrowing the ten raw rates. Security labels remain diagnostic.
- The full command requires an explicit approval file bound to the exact config and pool; neither the real full path nor publication mode was executed by this reviewer.

Verdict at initial inspection: fix 1 and 2, and cover 3 and 4, before claiming full-executor readiness. The benchmark's measured result and final artifact integrity remain pending completion.

Not checked yet: final sealed benchmark, protected-file inventory, final focused/full test results. No claim of publication readiness or certified extractable key is made.

## Completed-artifact inspection

After the implementer reported the benchmark finished, this reviewer ran bounded, standard-library-only hash and record checks. No native quantum evaluation or full lookup was executed. These checks returned successfully:

- All 204 entries in the benchmark output manifest matched their files; all 100 point checkpoint seals matched their JSON records.
- All 552 benchmark input hashes and all 60 producer hashes matched at inspection time. The archived `executed_producer_snapshot.py` matched the recorded wrapper digest `a5ce3bf8e54f06c077c0fecdba9f87ace59918fed355af788424cda1414e8400`. Subsequent executor fixes must be distinguished from this executed snapshot, preserving the sealed benchmark bytes.
- All 100 point records matched the config's ordered points, stage, config/input hashes, 212-candidate roster, 179 MB/33 Uniform family counts, unchanged classifications, and false security/publication flags.
- Both families' winners matched the signed raw-rate argmax in every record. Serial and parallel candidate and winner dictionaries matched exactly after excluding only the expected `MI_seconds` and `Holevo_seconds` telemetry differences. This checks all 21,200 evaluated candidate records across the two passes.
- All four finite-size output-manifest entries, all 26 recorded inputs, and all four current producer hashes matched. The mission parameters remained null.

Observed resource and timing values from the sealed artifacts:

| Measurement | Serial | Two workers |
|---|---:|---:|
| Stage wall time, seconds | 217.2845631 | 137.3368377 |
| Evaluator calls | 10,600 | 10,600 |
| Calls per second | 48.78395 | 77.18250 |
| Sampled aggregate RSS peak, bytes | 552,968,192 | 1,642,090,496 |
| Sampled process CPU time, seconds | 176.4375 | 188.828125 |
| Point time minimum, seconds | 2.57711 | 4.23831 |
| Point time median, seconds | 3.94175 | 4.67190 |
| Point time maximum, seconds | 9.61891 | 7.82003 |
| Point time mean, seconds | 4.29401 | 4.91038 |
| Point time sample standard deviation, seconds | 0.96875 | 0.72902 |

The measured stage speedup is 1.582128777, not an assumed factor of two. The parent initialization took 22.96615 seconds; worker native initialization times were 12.05210 and 12.14868 seconds and are included in the parallel stage. Process startup and parent preparation are distinct from per-point evaluator timing. Sampling uses a nominal 50 ms wait plus collection overhead; it is not an exact continuous peak measurement.

The full per-point workload is `2601*212=551412` calls. The optional exact radial grouping is `294*212=62328` calls and represents a different, explicitly configured execution mode. Neither full workload was run. The measured run contains 50 distinct spatial geometries and 100 point passes, not 100 distinct geometries.

Artifact verdict: the completed bounded benchmark and finite-size artifacts passed this independent inspection. The initial four findings concern the prepared future executor; the implementer is addressing them separately with software fixtures. Their fixes and final test results are not asserted by this artifact review.

Not checked by this reviewer: real full regeneration, publication mode, final protected-tree inventory, or the final post-fix test suite. Native source/security mathematics were intentionally outside scope; these results remain diagnostic evidence.
