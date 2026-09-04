# Next Actions

## Current Gate

`NOT_READY_FOR_PUBLICATION_SCALE_RUNS`

The completed V1 smoke outcome is `OPTIMIZATION_EFFECTIVELY_FROZEN` and must
not be rerun or retuned. V2 is implemented, frozen, and
`OPTIMIZATION_USABLE`; neither smoke may be rerun. Publication lifecycle
remains closed pending threshold/numerical approval.

## Exact Next Permitted Action

`FULL-SUPPORT C4 GRAM EVALUATION BACKEND: PASS / FROZEN`.

The arbitrary-precision fallback remains evaluation-only. No hard support
threshold is approved; publication training is unauthorized; baseline
selection and optimized-MB grid selection remain unperformed; final-test data
remain untouched.

Design and freeze an independent gradient/VJP validation protocol before any
publication-scale training.

## Stop Conditions

- Do not rerun or retune the completed V1 smoke.
- Do not rerun or retune V2 after observing its outcome.
- Do not treat `OPTIMIZATION_USABLE` as threshold approval or publication
  authorization.
- Do not add a positive engineering margin without a new prospective protocol
  and independent evidence.
- Do not approve candidate `1e-13` or reactivate historical `1e-12` in this
  validation-design task.
- Do not change the physical model, `tau`, MI, Holevo, SKR, security
  functional, optimizer settings, seeds, states, precision, or smoke settings.
- Do not perform publication training, optimized-MB search, baseline
  selection, final-test access, or held-out evaluation.

## Preserved Facts

- Frozen model SHA-256:
  `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`.
- V1 smoke artifact SHA-256:
  `4a914944aecb09204187040e461e84cd67e34f4c254647eea8ece2e625854360`.
- Proposed V2 config SHA-256:
  `6eb21147336e4ca4c305abdf2532fe03eaa8e4bb570a4c8918bdb91638727845`.
- V2 execution manifest SHA-256:
  `d27d7fd6be10121b4217e8cc72af88481e994acb89d30787cfa7c8c9b5e4f568`.
- V2 smoke artifact SHA-256:
  `321b6dc4fd28168878d84e511478c209379b6c0aa36da5d9e794092317ca36f6`.
- V2 methodology artifact SHA-256:
  `dbf1b4dc369195f8ee94bd8870f3a6142a69bba7e3130f2a2d8822e699d5ad77`.
- Threshold gate review artifact SHA-256:
  `3f75ddb9325ee8a15af2b05039232aec0d76088fff2b1e86a3ab3137b1d008de`.
- Final test remains inaccessible and untouched.
