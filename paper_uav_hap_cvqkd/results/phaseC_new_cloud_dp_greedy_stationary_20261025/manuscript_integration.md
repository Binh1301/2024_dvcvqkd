# Proposed cloud-subsection integration

The canonical v43 reference is a three-page PDF without an editable cloud
subsection source in this workspace. No frozen manuscript file was modified.
`proposed_manuscript_cloud.patch` is an unapplied add-file patch containing the
isolated replacement. Once the author provides/opens the editable manuscript,
replace only the old cloud-model subsection with:

```latex
\input{manuscript_cloud_model_replacement}
```

Preserve all other expressions, labels and optimization problems. New cloud
labels use a unique phasec prefix. A context-based edit to an unknown .tex file
was not fabricated. The threshold calibration and independent mean resampling
are explicit simulation conventions, not verbatim reference equations.
