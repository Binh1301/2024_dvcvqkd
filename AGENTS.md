# Research orchestration for UAV/HAP + 256-QAM + CV-QKD

Use the custom subagents in `.codex/agents/` whenever their specialty materially improves the task. Keep the main thread responsible for requirements, cross-agent decisions, and the final answer.

## Delegation policy

Do not spawn every agent mechanically. Choose the smallest useful subset, normally 2-4 agents. Run read-only independent analysis in parallel when possible. Avoid simultaneous write-heavy work.

Preferred routing:
- End-to-end model, assumptions, variable interfaces, cross-layer consistency -> `system_architect`
- UAV/HAP geometry, FSO/atmospheric turbulence, pointing error, fading -> `atmospheric_channel_expert`
- 256-QAM, adaptive modulation, PS/GS/joint PS+GS, autoencoders, MI/GMI/BER -> `qam256_shaping_expert`
- CV-QKD protocol, covariance/noise/SKR/security/fading treatment -> `cvqkd_security_expert`
- Monte Carlo, optimization code, tests, numerical stability, figures/data -> `numerical_simulation_engineer`
- Papers, prior art, novelty matrix, closest baselines -> `literature_novelty_scout`
- Final technical attack before accepting a result -> `adversarial_reviewer`

## Recommended workflow for a new research idea

1. Spawn `system_architect`, `literature_novelty_scout`, and the most relevant technical specialist(s) in parallel.
2. Wait for their summaries and reconcile conflicting assumptions in the main thread.
3. Give the approved equations/interface contract to `numerical_simulation_engineer` for implementation.
4. After numerical results exist, spawn `adversarial_reviewer` plus one domain specialist to independently audit the claims.
5. Only then produce the paper-ready conclusion.

## Research rules

- Never fabricate citations, numerical results, parameter values, standards, or security proofs.
- Separate facts from hypotheses and simulation expectations.
- Use consistent units and explicitly define normalization conventions.
- Keep training, validation, and test channel realizations separate for learned/adaptive methods.
- Distinguish instantaneous/statistical/estimated CSI and enforce deployment-time availability.
- Classical 256-QAM and CV-QKD are separate subsystems unless an explicit protocol couples them.
- A classical communication improvement does not by itself imply an improvement in CV-QKD secret key rate.
- If discrete 256-point modulation is proposed as the quantum modulation itself, require a security treatment appropriate to discrete-modulated CV-QKD rather than silently reusing Gaussian-modulation formulas.
- Require fair baselines, ablations, limiting-case sanity checks, and reproducible numerical settings.

## Default multi-agent prompt pattern

When the user asks for a full analysis, use language equivalent to:

"Delegate this research task to the smallest relevant set of custom subagents. Run independent read-only analyses in parallel, wait for all of them, reconcile conflicting assumptions, then return one consolidated answer. If implementation is needed, first freeze the mathematical model, then let numerical_simulation_engineer make the change. Before accepting the final claim, ask adversarial_reviewer to attack it."
