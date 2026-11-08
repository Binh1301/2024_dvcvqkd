# Phase5E independent review

What this change does: The new validator checks the separately approved full clear-sky lookup and then repeats the complete 212-source search at seven original coordinates. It preserves separate MB/Uniform winners and keeps numerical integration readiness separate from source, security, cloud and publication approval.

## Initial review while the full job runs

Status: source-only review; completed full artifacts and direct recomputation are NOT_RUN by this reviewer. No tests, native evaluations or broad hashing were run alongside the main computation.

Scope read: Phase5E plan, preflight, geometry mapping header/sample, explicit approval artifact, validator and its tests, complete lookup executor, pilot checkpoint/comparison helpers, waypoint geometry, tuned physical setup, and the actual native channel/evaluator chain. The expected load is one local 294-context job with two worker processes, followed by seven direct checks with two workers.

### Findings sent before validation

1. **Must fix: Windows checkpoint seal keys do not match slash-built names.** `lookup_benchmark._seal` records native Windows backslashes, while the first validator version searched for `full/<id>.json`. The completed job would be rejected as unsealed. Fix: normalize separators once, reject collisions, retain path containment checks. A `normalized_output_seal` helper and a pure regression test were observed after this finding was sent; execution of the test remains deferred until the measured job finishes.

2. **Must fix before claiming the planned metadata checks: schema metadata is only partly checked.** The first validator version checked NPZ points, rates, three digests and the paper flag, but omitted NPZ units, noise, producer digest, geometry mode and family evidence arrays; it also omitted CSV noise/promotion flags. A resealed wrong-unit export could pass these checks. Fix: compare these stored values with the declared contract, and add a small corruption test. Numeric loader round-trip checks alone are not a substitute for checking stored metadata.

3. **Must fix before claiming five pilot comparisons: the pilot summary is unbound and an empty comparison list passes.** The first validator version reads the Phase5C summary without its output seal and accepts `all([])`. Fix: verify its summary hash against its existing seal and require the five expected distinct positions before comparing values. Test an empty list and a changed summary with an unchanged seal.

### Producer-input equivalence assessment

The actual `_evaluate_job` passes only `point['zenith_deg']` and the same original protocol to the native channel context. The canonical chain reaches `results/skr_vs_zenith_eq14_v43_20261023/model.py:channel_context`, whose optical call fixes the approved 0.30 m aperture, 35 urad full divergence, 0.10 m position standard deviation and 1.561 urad jitter, and uses zero boresight in the raw moment call. Horizontal coordinates, azimuth and cloud state are absent from this input interface. Target 0.0136 channel and 0.005 detector noise enter the unchanged diagnostic evaluator separately. Therefore bit-identical native angles with the identical protocol and source roster justify reuse for this particular clear-sky deterministic producer. This does not establish invariance for another atmospheric or cloud model.

The direct-position function obtains zenith from waypoint geometry and explicit original coordinates, without consulting grouped lookup angles. Its test includes the center and farthest point. Comparing both family winners, their exact source identities and signed scalar metrics is appropriate for the requested spot checks. Accepted source C/w and the Holevo implementation were not rederived.

The original frozen-spec hash discrepancy remains recorded in preflight. The approval is restricted to this numerical diagnostic and does not grant publication or security admissibility. The existing core result seal is intended to remain immutable; any later validation/package seal must be separate.

Initial verdict: fix the listed validator issues before running validation; no source-model change is requested. Final data review will be appended after the coordinator confirms completion of the measured jobs.

Not checked: completed output completeness, final checksums, fresh direct-check results, or tests while the main job runs. No extra native calls were made by this reviewer.
