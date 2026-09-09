# Next Actions

## Current gate

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

The documentation audit is complete. No training, threshold approval,
baseline selection, final-test access, or publication-scale evaluation is
authorized.

## Priority order

### P0 — resolve target-model blockers

1. Freeze the phase parameters and implement the causal
   \(\epsilon_{\mathrm{base}}\rightarrow\epsilon_{\mathrm{total}}\) chain.
2. Decide and implement the intended scintillation/AoA/raw-\(T\) channel path.
3. Implement and verify the full \(Z\) interval, empty-domain failure, and
   inner \(\chi_{BE}\) maximization.
4. Rebind numerical/provenance evidence after the target path exists.

### P1 — deterministic Friday diagnostics

Use only existing deterministic transmitter modules for regular 256-QAM,
Uniform/Binomial/MB PMFs, C4 orbit expansion, and global-geometry figures.
These do not require training or security evaluation.

### P2 — current-channel diagnostic, if explicitly labeled

A small runner may visualize the current atmospheric/pointing sampler and its
physical \(T\), but it must be labeled as the implemented current sampler, not
as the target scintillation/AoA model.

### P3 — target channel/phase diagnostics

Run only after P0 resolves the required modules and parameters:
\(H_{\mathrm{sc}}\), \(H_{\mathrm p}\), \(B_{\mathrm{AoA}}\), raw/physical \(T\),
\(p_{>1}\), \(\xi_{\mathrm{phase}}(V_A)\), and
\(\epsilon_{\mathrm{total}}(V_A)\).

### P4 — security/SKR and learned output

Run only after P0 plus numerical approval: \(\chi_{BE}(Z)\) over the physical
interval, fixed-baseline K plots, and then learned PS/GS/\(V_A\) diagnostics.

## Stop conditions

- Do not convert current lower-endpoint Holevo values into full-interval claims.
- Do not use epsilon_total as a policy input or sample it independently.
- Do not call current channel artifacts scintillation/AoA evidence.
- Do not run publication training, baseline selection, optimized-MB search,
  final-test access, or long certification.
