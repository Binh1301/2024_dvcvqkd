# Phase/Post-Action Excess-Noise Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the active evaluator derive epsilon_total = epsilon_base + c_phi * V_A after the adaptive transmitter action and pass that same tensor to MI and the existing Holevo interface.

**Architecture:** Keep epsilon_base as the only policy feature, expose the phase equations once in src/channel/phase_noise.py, and require an explicit phase scenario value at runtime. A missing production Cn_phi2 fails closed; tests may use explicit zero phase only as a fixture. The existing lower-endpoint Holevo algorithm remains unchanged.

**Tech Stack:** Python 3.12, NumPy, PyTorch float64, unittest, and PyYAML configuration.

---

### Task 1: Add canonical phase equations and failing tests

**Files:**
- Create: src/channel/phase_noise.py
- Modify: src/channel/__init__.py
- Create: tests/test_phase_noise.py

- [x] Write tests first for phase_distortion_variance, phase_noise_coefficient, phase_excess_noise, total_excess_noise, and phase_coefficient_from_parameters.

Required assertions:

~~~python
tau = phase_distortion_variance(2.0e-16, 1.55e-6, 19_000.0)
expected = 2.46 * 2.0e-16 * (2.0 * math.pi / 1.55e-6) ** (7.0 / 6.0) * 19_000.0 ** (11.0 / 6.0)
self.assertAlmostEqual(tau, expected)
self.assertEqual(phase_noise_coefficient(3.0), 3.0 + 0.25 * 3.0**2)
self.assertEqual(phase_distortion_variance(0.0, 1.55e-6, 19_000.0), 0.0)
~~~

Also test batched epsilon_total, zero phase, invalid wavelength/link/Cn_phi2, and autograd d epsilon_total / d V_A = c_phi.

Run from the project directory:

~~~powershell
python -m unittest tests.test_phase_noise -v
~~~

Expected RED result: import failure because phase_noise.py does not exist.

Implement the minimum API. Use math for scalar scenario parameters and Torch-preserving products for V_A. Never use torch.tensor(V_A), never detach it, and never provide a default Cn_phi2. Export the functions from channel/__init__.py.

Run the same command and require all phase tests to pass before continuing.

### Task 2: Rename sampled state semantics and wire the trainer

**Files:**
- Modify: src/channel/state_distribution.py
- Modify: src/channel/diagnostics.py
- Modify: src/optimization/trainer.py
- Modify: tests/test_channel_state_distribution.py
- Modify: tests/test_pipeline_consistency.py
- Modify: tests/test_gradients.py
- Modify: tests/test_energy_budget.py
- Modify: tests/test_physical_peak_domain.py
- Modify: tests/test_pointwise_guard.py

Write a failing pipeline assertion that patches MI and Holevo, calls evaluate_transmitter with phase_coefficient=0.25, and verifies both receive epsilon_base + 0.25 * result.ensemble.declared_va. Verify that policy features remain based on epsilon_base. **Done.**

Run:

~~~powershell
python -m unittest tests.test_pipeline_consistency tests.test_gradients -v
~~~

Expected RED result: the phase argument and derived-epsilon plumbing are absent.

Make ChannelStateSamples store epsilon_base_snu. Keep a documented read-only excess_noise_snu property as a legacy compatibility alias. Update realization hashing and diagnostics to use epsilon_base_snu.

Rename active local variables and trainer parameters to epsilon_base. Add phase_coefficient to evaluate_transmitter and train_step. None must raise an informative error before MI/Holevo; it must not mean zero.

The central evaluation order must be:

~~~python
ensemble = transmitter(transmittance, epsilon_base)
epsilon_total = total_excess_noise(epsilon_base, ensemble.declared_va, phase_coefficient)
mutual_information = discrete_mutual_information(ensemble, transmittance, epsilon_total, ...)
holevo = holevo_information(ensemble, transmittance, epsilon_total, ...)
~~~

Preserve the same Ensemble object invariant and keep pointwise guard construction on epsilon_base. Add epsilon_total to Evaluation only as a defaulted field if needed for state payloads and traceability.

Update unit-test fixtures with explicit phase_coefficient=0.0 only where the zero-phase mathematical limit is intended. Do not add a production default.

Run the focused state, pipeline, gradient, energy, peak, and pointwise tests and require all to pass.

### Task 3: Add explicit runtime configuration and active-entry plumbing

**Files:**
- Modify: configs/default.yaml
- Modify: configs/channel.yaml
- Modify: scripts/_train.py
- Modify: scripts/run_baselines.py
- Modify: scripts/evaluate.py
- Modify: scripts/evaluate_baseline.py
- Modify: scripts/smoke_validate_frozen.py
- Add focused runtime-resolution coverage if needed.

Add only a null phase configuration field; do not invent a physical number. The active default configuration must represent Cn_phi2 as unresolved and fail closed. Add the path to _train.py::TRAIN_REQUIRED. **Done.**

Resolve c_phi from the explicit Cn_phi2, wavelength_m, and LinkGeometry.link_length_m using the canonical phase module. If Cn_phi2 is absent or null, raise an informative error stating that an explicit author-approved scenario-level C_n,phi^2 is required.

Add required --cn-phi2 input to run_baselines.py and pass the computed coefficient. Update held-out and smoke paths to pass the resolved coefficient or fail closed through their existing guards. Do not weaken lifecycle or manifest checks.

Test missing configuration failure, explicit zero Cn_phi2 as a fixture, and active script argument/config plumbing. Do not run the scripts as experiments.

### Task 4: Minimal documentation and final verification

**Files:**
- Modify only as needed: docs/PAPER_CODE_ALIGNMENT.md, docs/KNOWN_ISSUES.md, docs/PROJECT_STATE.md, docs/NEXT_ACTIONS.md, docs/EVIDENCE.md.

Mark only phase/post-action epsilon aligned after fresh focused evidence. Keep composite fading, full-Z security, numerical certification, learned-model validation, and lifecycle state unchanged. **Done.**

Run:

~~~powershell
git diff --check
git diff --stat
python -m unittest tests.test_phase_noise tests.test_channel_state_distribution tests.test_pipeline_consistency tests.test_gradients tests.test_energy_budget tests.test_physical_peak_domain tests.test_pointwise_guard -v
git status --short --branch
~~~

Confirm no Holevo Z-domain code, training authorization, final-test path, Monte Carlo runner, or certification script was broadened. Report exact test counts and environment blockers. Do not claim a full-suite pass unless the full suite is actually run.
