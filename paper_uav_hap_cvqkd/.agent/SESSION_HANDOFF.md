# Session Handoff

Date: 2026-09-11

## Authoritative lifecycle

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

Adaptive-training status: `NOT_READY_FOR_ADAPTIVE_TRAINING`.
No training, optimizer step, final-test access, certification, or
publication-scale evaluation occurred.

## Completed this session

- Read the full-support differentiable source-moments research report and
  bounded Superpowers plan before implementation.
- Added the isolated `EXPERIMENTAL_DIAGNOSTIC_ONLY` arbitrary-precision C4
  forward tangent in `src/cvqkd/c4_constrained_tangent.py`.
- Implemented exact full-support raw/sector tangents, Sylvester square-root
  tangents, constrained right solves for B/A and dB/dA, and C/w propagation.
  The module does not import or call the old custom reverse.
- Added fast focused tests in `tests/test_c4_constrained_tangent.py` and the
  manual runner `scripts/validate_c4_constrained_tangent.py`.
- Cheap uniform, nonuniform-positive, perturbed-real, and
  perturbed-imaginary fixtures passed direct/constrained, residual, forward,
  and central-difference checks.
- Recovered the exact prior Case-A PS direction by hash and ran the bounded
  200/400/600/800 AP ladder. The 800-digit constrained row resolved 256/256
  modes and passed the 1e-8 dC/dw/dJ comparison to the prior corrected AP
  finite difference.

## Target result boundary

Artifact:
`results/c4_constrained_forward_tangent_20260911.json`

The target 800-digit row reports:

- `C=0.85985110654649868138037962728289179096834048571987`;
- `w=0.018327610474963502048823295065766568532781601388489`;
- `dC=0.00050092422832962377222627091862944921206718683231693`;
- `dw=-0.0011532623534953207533476618573511008283277382475422`;
- `dJ=0.0017741810709566170444324223035415062817078761571016`;
- relative errors to prior AP: `1.35e-9` for dC, `5.55e-10` for dw,
  `9.37e-10` for dJ;
- runtime: `1181.1304 s`.

Classification: `CONSTRAINED_TANGENT_VALIDATED`, diagnostic-only. The lower
precision rows fail closed before resolving all modes. The target explicit
R/J comparison was attempted but not completed within an approximately
16-minute window; cheap-fixture explicit/constrained evidence passed.

## Verification

- `tests.test_c4_constrained_tangent` plus the existing corrected AP
  regression: 5/5 passed.
- `py_compile` for module, runner, and tests passed.
- `git diff --check` passed after the implementation checks; rerun after any
  subsequent evidence edit.

## Open blockers and next action

1. The exact tangent is too slow for the proposed adaptive runtime gate and
   does not repair the custom reverse.
2. Validate remaining GS-real, GS-imaginary, and V_A forward directions only
   as bounded diagnostics if continuing this line.
3. Keep reverse repair, full-Z backward, adaptive training, final-test access,
   baseline selection, threshold approval, and publication-scale work closed.
4. Preserve the frozen full-support C4 model: no clipping, jitter, epsilon
   identity, pseudoinverse rank reduction, support truncation, or model change.
