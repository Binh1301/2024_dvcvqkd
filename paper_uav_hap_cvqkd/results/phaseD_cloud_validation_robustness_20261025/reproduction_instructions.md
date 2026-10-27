# Reproduction and scope

From paper_uav_hap_cvqkd, use:

```
.venv/Scripts/python.exe -X utf8 -B results/phaseD_cloud_validation_robustness_20261025/reproduce_phaseD.py --phase verify
```

This reads saved records, reconstructs all new cloud masks by their exact
permutations, checks every new stored trajectory/reward/constraint/objective,
checks all protected hashes and the sealed artifact manifest. It never calls a
source solver, channel integration, training or held-out evaluation.

The analysis functions explicitly reproduce baseline summaries, covariance,
threshold/correlation diagnostics, paired bootstrap, indexing policies and
component-level sensitivity. The analysis CLI refuses to overwrite a completed
run. For numerical regeneration, copy the code and startup/config inputs into
a separate sibling result namespace; keep the Phase C baseline binding fixed.
In that new namespace run --phase analysis (including the transpose tie check),
then --phase reports and --phase figures.
This regenerates diagnostics only, with no exact-source calculation.
Do not run producer commands against the delivered sealed namespace.
PDF export QA uses check_pdf_exports.py with the bundled PDF Python runtime.
The four manuscript files are isolated fragments; no frozen manuscript edit is
applied. Compilation was NOT_RUN because no TeX engine was found in PATH.

Seeds: base Gaussian/Uniform streams are the exact Phase C archived arrays
(seed20261015,mission0..99). Random index assignments use20261026 and20261027.
Paired bootstrap uses seed20261026 and10000 draws of100 whole missions.
All indexing configurations share the same base fields. New configurations
are coupled Monte Carlo views, not additional independent cloud samples.

Initial analysis code is preserved under source_sensitivity_provenance_guard_probe/.
Its provenance-guard probe is retained; final sensitivity uses the existing
mathematical components with fixed cached MI and effective channel. The primary
source-validation checks are never relaxed. Arbitrary perturbations are not
certified source errors or newly computed moments.
