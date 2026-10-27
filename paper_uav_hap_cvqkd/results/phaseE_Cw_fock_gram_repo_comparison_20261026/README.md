# Phase E independent source comparison

Read [Vietnamese report](validation_report_vi.md), [derivation](mathematical_derivation.md),
[repository audit](repository_Cw_audit.md), [stability analysis](Cw_numerical_stability.md),
[six-row comparison](Cw_comparison.csv), [all diagnostics](convergence_diagnostics.csv),
[A-minus-B differences](pairwise_method_differences.csv), [one-context Eq14 check](Z_SKR_sensitivity.csv).

Independent implementations: [Fock](independent_fock_Cw.py), [Gram](independent_gram_Cw.py).
[Bounded controller](run_comparison.py) refuses a completed batch; do not rerun it
in this historical namespace. [Analysis](analyse_comparison.py) uses saved jobs only.
Raw spectra, values and limit outcomes are under jobs/. Input arrays/hashes and
primary source PDFs are under inputs/ and reference_audit.json.

Overall INCONCLUSIVE for full256-mode convergence, despite tested observable
agreement. No historical source evidence classification is promoted. Strict
Phase B remains false; no source catalog or physical/security equation is edited.
