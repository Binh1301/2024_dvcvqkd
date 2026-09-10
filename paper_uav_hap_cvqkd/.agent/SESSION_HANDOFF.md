# Session Handoff

Date: 2026-09-11

## Authoritative lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Adaptive-training status: `NOT_READY_FOR_ADAPTIVE_TRAINING`.
No training, optimizer step, final-test access, certification, or publication-
scale evaluation occurred.

## Corrected AP worker

The AP worker fix was one line:

    aa = sr * x2.T  ->  aa = x2.T

Algebra: `b=sr*m*sp^(-1)` is the eigenbasis form of
`a_tau=S*a*R`; the second solve yields
`x2.T=sr^2*m*sp^(-2)=G_s*D*G_(s-1)^(-1)`, already equal to the production
`A_s`. The old left `sr` changed w.

Worker SHA-256:
`2cd1feeeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`.

## Corrected evidence

- Three explicit 20-digit fixture equivalence checks passed in 751.396 s.
- Exact Case A hash:
  `c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3`.
- Corrected 800 digits: 256/256, C and w stable, runtime 367.3323453 s.
- Corrected 900 digits: 256/256, C and w stable, runtime 416.6573139 s.
- Corrected C:
  `0.85985110654649868138037962728289179096834048571987`.
- Corrected w:
  `0.018327610474963502048823295065766568532781601388489`.
- Corrected AP artifact:
  `results/ap_worker_corrected_case_A_20260911.json`, SHA-256
  `f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44`.
- Corrected Case A full-Z artifact:
  `results/exploratory_case_A_full_security_corrected_20260911.json`, SHA-256
  `a3b7aaa23635ac5e01e08f3486d4131fe9d17580c51b32ef9b498324fa5723fa`.

Corrected Case A full-Z:

- `[Z_L,Z_U]=[0.2914192733053753, 0.2934784546975139]`;
- `Z_star=0.2914192733053753`;
- `chi_BE_ub=0.01518919002933572`;
- `raw K=0.004757635492383283`.

## Superseded evidence

Old worker-backed Case A, B-D, baseline cached, full-support fallback, and
custom-backward-reference artifacts are retained but marked
`SUPERSEDED_WRONG_AP_W`. Do not use their old w, Z, Holevo, or K values as
current evidence. B-D were not recomputed.

## Custom backward

The experimental AP custom backward remains isolated and
`PENDING_CORRECTED_AP_DIRECTIONAL_VALIDATION`. No Case A directional VJP or
full-Z backward was run after the correction.

## Verification

- `tests.test_ap_worker_equivalence` plus baseline tests: 10 tests pass, 1
  explicit slow test skipped; the slow run separately passed all three
  fixtures in 751.396 s.
- `tests.test_ap_custom_backward`: 2/2 pass; prototype remains isolated.
- `tests.test_full_support_c4_gram_backend`: 6 pass and one pre-existing
  `NameError` in the repeated-spectrum test.
- Corrected AP 800/900 forward smoke completed.
- `py_compile`: pass; `git diff --check`: pass with CRLF warnings only.

## Exact next task

Recompute bounded B-D exploratory subsets with corrected C,w and full-Z path.
Do not execute without separate authorization.
