# Strict 26-distance ALT_OPT reproducibility rerun

Scope: diagnostic only, explicitly requested 2026-10-08. Superpowers skill is
not installed; this is a repository execution plan, not a skill invocation.

1. Snapshot current corrected drivers, scientific source/config files, the
   165-row source cache, and historical artifacts. Preserve the already
   documented frozen-spec hash discrepancy; do not edit the specification or
   promote the publication lifecycle.
2. Call the existing distance-sweep main unchanged with a fresh output
   directory, max outer iterations 6, and no --allow-new-source. Use its four
   starts and prior-distance continuation. Do not preload old final solutions.
3. Compare newly executed results against the historical ALT_OPT table. Retain
   actual corrected stopping statuses, missing probes and full coordinate logs.
4. Reuse the existing positive-only base-10 log renderer. Override only the
   MB legend text to ALT_OPT MB-shaped 256-QAM. Keep Uniform/fixed source rows.
5. Validate hashes, baseline, all 26 coordinate-search executions, stopping
   settings, source-generation prohibition and figure data. Save reports,
   input manifest/config and driver snapshots. Run scoped regression tests.
6. Record artifact-first evidence and handoff. Do not claim global optimality
   or continuous convergence while exact-source directions remain unresolved.
