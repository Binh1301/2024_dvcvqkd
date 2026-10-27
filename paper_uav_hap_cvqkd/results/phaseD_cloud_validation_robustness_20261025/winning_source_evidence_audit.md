# Winning-source evidence audit — INSUFFICIENT_EVIDENCE

Exact ensemble: `b083ac8400f7e1068ec045f9882bd256cbbfdec50b64d66d8b7f2d84c05eb214`.
Payload: `results/exact_mb_test2/exact_source_cache/dac498f0bd2082d12225b96aa057fb8541f04c48e011f4e6b3795f325f4b62a4.json`.
Payload SHA256: `f835e47731891c935fceab522cddc1e7e9875629fd9166ec0532273e7b694f32`.
Historical cache key: `dac498f0bd2082d12225b96aa057fb8541f04c48e011f4e6b3795f325f4b62a4`.
Canonical source identity: `5692cc57eb1e764c8d4f5ee9645daabc4405ab67c0e974eaf92bfeecfc9f59fd`.

VA=1.358333319784304, VA_hex=0x1.5bbbbb818a6b0p+0; nu_raw=0.30,
nu_repo=42.5*nu_raw=12.75; C=1.067911050328646, w=5.700303183579203e-10.
The physical ensemble was reconstructed with the existing builder; no moments
were generated. PMF, C4 symmetry, p/alpha hashes and256-state normalization
passed the unchanged validators. VA=2*nbar error=4.441e-16;
measured quadrature X=2Re(alpha) variance error=2.22e-16.

## What is verified and what is missing

The payload declares ARBITRARY_PRECISION_FALLBACK, support_size256 and a
1050/1250/1450 decimal-digit ladder, density tolerance1e-12 and physicality
tolerance1e-10. These are settings/claims, not saved convergence observations.
The hash-bound implementation matches the historical implementation under the
existing LF/CRLF provenance policy; no alias policy is changed in this task.

The persistence path in scripts/run_exact_mb_test2.py (the source cache writer)
extracts C,w,route,support from moments.diagnostics[0], then serializes those
summary fields. It does not persist the worker's complete precision-row
diagnostics. The worker can emit digits, rank/resolved, minimum_eigenvalue,
C and w; the winning payload contains none of those per-precision rows.
No bound residual/error estimate for this exact source is saved in the payload.

This task scanned 2722 eligible JSON/JSONL/log/text artifacts;
202 contain the winning ensemble hash or cache key.
The complete matched-path/hash list is winning_source_evidence_matches.csv.
It excludes startup/manifests, held-out/final-test material and this new namespace;
11 files larger than8MB were not read.
Existing Phase B inventory, receipt investigation and Git-evidence scan are
corroboration; copies, cache/ensemble identities and successful later SKR values
do not reconstruct discarded numerical iterations.

No usable identity-bound convergence receipt was recovered from inspected
source/precision artifacts. This is a bounded audit, not a claim that evidence
cannot exist anywhere. Missing receipt does not imply C,w are incorrect.
Classification remains INSUFFICIENT_EVIDENCE. No source job was executed.

## Minimum remaining action

Recover original worker output bound to this exact ensemble/input hashes,
implementation and settings, including the1250/1450 rows, resolved rank,
minimum eigenvalues and C,w differences. If unavailable, independently
authorize the single-source plan in source_recomputation_plan.md. Identity
checks and arbitrary sensitivity perturbations cannot replace that evidence.
