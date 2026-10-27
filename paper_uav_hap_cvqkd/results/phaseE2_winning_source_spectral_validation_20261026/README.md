# Phase E2: winning-source spectrum

Read validation_report_vi.md first. Source-moment convergence is INCONCLUSIVE;
source evidence remains INSUFFICIENT_EVIDENCE and strict Phase B remains false.

- full_support_spectral_audit.md and sector_spectrum_diagnostics.csv: source
  spectrum, correct C4/Fock mapping and historical retained ranks.
- unresolved_spectrum_error_analysis.md and spectral_lower_bound_certificate.json:
  a rigorous scalar positivity/tail bound, not a C,w error certificate.
- checkpoint_stub_tests.md and checkpoint_test_results.json: 14 current focused
  checks, M<=16 only; original development evidence retained separately.
- precision_feasibility.md and controlled_run_authorization_plan.md: a bounded
  400/500-digit one-source plan, not executed. authorization.json is absent.
- source_convergence_status.json: machine-readable scientific conclusion.
- artifact_integrity_report.md, artifact_manifest.json and verification.json:
  preservation and saved-data verification.

Read-only check from project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B .\results\phaseE2_winning_source_spectral_validation_20261026\verification.py
```

Do not rerun the test/diagnostic producers in this sealed namespace; stub
directories deliberately fail closed on overwrite. The prepared controlled-run
command reads this sealed implementation/plan and writes only the separately
named future run namespace, after explicit approval. E2 preparation remains intact.
