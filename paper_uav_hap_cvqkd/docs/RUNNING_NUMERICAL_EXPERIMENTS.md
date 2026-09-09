# Running numerical experiments

This file documents existing entry points only. No command below was run by the
2026-09-10 documentation audit.

## Smoke

Seconds to a few minutes, development-only, not a paper result:

~~~powershell
python scripts\smoke_validate_frozen.py --steps 3 --awgn-samples 2 --fock-cutoff 40 --va-budget 1.5 --dual-learning-rate 0.1 --seed 260826 --output results\frozen_transmitter_smoke.json
~~~

The fixed-baseline smoke entry point is:

~~~powershell
python scripts\run_baselines_cached_source_moments.py --config configs\baseline_smoke.json
~~~

It evaluates the current C4 Gram/lower-endpoint path and must not be used as a
target full-interval security or publication result.

## Preliminary diagnostic

Seconds to a few minutes after a resolved diagnostic configuration exists:

~~~powershell
python scripts\freeze_channel_diagnostics.py --config configs\default.yaml --output results\frozen_channel_diagnostics.json
~~~

This existing command uses the current atmospheric/pointing sampler. It does
not generate plots, scintillation, AoA outages, raw-T/p_gt_1, phase noise, or
epsilon_total. The plotting module only requires a saved raw-data path; no
plotting entry point currently exists.

## Certification

Potentially expensive and lifecycle-gated. Do not run while preparing Friday
figures:

- run_full_support_c4_gram_evaluation_validation.py
- validate_mi_convergence.py
- validate_fock_convergence.py
- validate_selected_roster_convergence.py
- combine_convergence_evidence.py
- certify_rigorous_whole_segment_support.py
- run_gradient_vjp_validation.py
- run_manifold_consistent_synthetic_vjp_validation_v3.py

These commands do not resolve the missing target phase chain or full-interval
security solver.

## Publication-scale

Do not run without explicit lifecycle approval:

- train_ps.py
- train_gs.py
- train_joint.py
- evaluate.py
- evaluate_baseline.py
- optimized-MB or baseline-selection scripts

No command may be added to this document unless the script exists in scripts/.
Do not pass a current lower-endpoint smoke result off as target-model evidence.
