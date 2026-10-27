# Numerical validation — DIAGNOSTIC_ONLY

- Original grid provenance: `results/skr_vs_zenith_eq14_v43_20261023/protocol.json` SHA256 `55c36205c19ada6f4fd2d5211e8733248399e0fe2eee5944a7e9d3ac24bca964`, `/angles_deg`.
- Saved pairs: 12932; duplicate pairs: 0; reused rows identical: 1908.
- Evaluator SHA256: `c7d4f0429fca5636d5e4354a23ba69d124c889801d01138734452216714c94e3`; physical protocol SHA256: `bac73f66e6d803bc8cb27454f69caa515d79eaa440cd751af2967497dde41632`.
- Source reconstruction verifies all 212 PMF/amplitude digests, payload SHA256, binary64 VA/nu, C/w hex, 256 symbols and X variance. No source moment kernel executed.
- Every primary pair: unchanged GH64/128 MI tolerance 2e-10; direct Eq14/Eq13 80/110 digits tolerance 2e-11. Failures remain rows with blank rates.
- Independent selected checks: 235 (35 reused, 200 new); all PASS. New checks add GH256, adaptive MI, independent symplectic matrix spectrum, conditional covariance and 160-digit components. These are supplemental checks, not additional catalog evaluations or C,w calculations.
- Max independent MI difference 1.366962099069724e-15; max covariance difference 6.2172489379008766e-15; conditional difference 4.4408920985006262e-16.
- Max saved raw-rate residual 0; direct Eq14 float residual 8.8817841970012523e-16.
- Max closed/direct channel moment residual 4.8849813083506888e-15; 80/110-digit moment residual 4.9984845456054304e-71.
- Near-tie supplemental selected rows: 0; all selected schemes checked at all angles, including crossings and source switches.
- Three focused tests PASS. No failed candidate excluded. Source classifications unchanged; successful rate computation is not source convergence evidence.
- Truncated PDF is not mathematically normalized. Deficit recorded; no clipping, renormalization or PDF replacement. No Z interval/optimization.
- Strict Phase B remains BLOCKED; UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
