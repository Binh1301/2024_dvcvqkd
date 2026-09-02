# UAV/HAP FSO 256-point DM-CV-QKD paper code

Current lifecycle/backend state is maintained in `docs/PROJECT_STATE.md`.
Older numerical documents preserve preregistration and diagnostic history and
must not override that snapshot.

This folder implements the frozen model in `docs/FINAL_MODEL_SPEC.md`. It models a HAP transmitter, UAV receiver, fluctuating FSO channel, 256-point coherent-state modulation, C4-symmetric PS, global GS, adaptive modulation variance, discrete-input mutual information, and the accepted asymptotic ideal-heterodyne Holevo/SKR chain.

It does **not** contain publication results. The physical, optimization, and MI
settings are frozen, and `N_MC=2048` is convergence-selected. Exact-dyadic
point-oracle evidence exists, but neither candidate support threshold is
approved and the prospectively frozen V3 whole-segment feasibility gate failed
`0/4` with four resource limits. Incremental hard-support whole-segment
certification is therefore stopped pending the separate method review recorded
in `docs/PROJECT_STATE.md`. No publication training, final-test evaluation, or
baseline ranking has been run. July legacy checkpoints and plots were
intentionally not copied.

## Scientific scope

- Power transmittance is evaluated instantaneously and SKR is averaged after per-state evaluation.
- Production train/validation/test states draw `T` from the frozen FSO model and independently draw a genuinely varying bounded-uniform input-referred `epsilon`; bounds and split seeds are explicit configuration values.
- `V_A = 2 sum_i p_i |alpha_i|^2` is asserted statewise.
- The PS network is `2 -> 128 -> 64` on `[log10(T), epsilon]`; 64 orbit masses expand to a tied 256-symbol PMF.
- The adaptive-variance network is exactly `2 -> 64 -> 1`, followed by the paper's bounded log-domain mapping. Bounds are mandatory.
- GS is one global, channel-independent `64 x 2` prototype tensor expanded by exact 90-degree rotations.
- Physical amplitudes use one statewise scalar `sqrt(V_A/(2 sum_k q_k |z_k|^2))`; no PMF-weighted centering is used.
- Bob uses ideal heterodyne detection and asymptotic reverse reconciliation.
- Exact instantaneous CSI is an oracle assumption. There is no estimator, feedback delay, or CSI-error model.
- The paper's standard-form covariance is rejected by default when the ensemble is quadrature-asymmetric.
- Numerical corrections are reported through diagnostics; materially invalid density/covariance states raise errors.

## Structure

```text
configs/       unresolved paper configuration and explicit conventions
src/channel/   geometry, attenuation, turbulence, pointing, sampling
src/modulation/256-QAM, PMFs, normalization, PS/GS/V_A transmitter
src/cvqkd/     protocol metadata, MI, covariance, Holevo, SKR
src/optimization/constraints, losses, deterministic training kernel
src/utils/     seeds, finite checks, artifact helpers
scripts/       baseline, training, evaluation, reproduction validation
schemas/       future publication-result schema; no claims or values
tests/         scientific invariants and limiting cases
docs/          equation, paper, legacy, assumption, and issue maps
results/       validation diagnostics and fail-closed lifecycle evidence; no publication claims
figures/       empty; figures must derive from saved raw data
```

## Environment

From this folder, create an isolated environment and install the declared minimum interfaces:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The current workspace environment was not modified. A publication lockfile must be created after the authors approve and validate an environment.

## Tests

```powershell
cd paper_uav_hap_cvqkd
python -m unittest discover -s tests -v
```

Tests cover the row-major C4 orbit mapping, PMF expansion, exact energy/zero-mean/isotropy invariants, all ablation owners, PS/GS/`V_A` gradients, common MI/Holevo ensemble identity, channel limits, covariance physicality, SKR averaging, and invalid inputs.

## Paper reproduction status

```powershell
python scripts\reproduce_paper.py --config configs\default.yaml
```

This command intentionally exits with status 2 and lists unresolved paper parameters/results. It must not silently import legacy values.

## Explicit baseline smoke run

The following is an example software smoke configuration, **not a paper result**:

```powershell
python scripts\run_baselines.py `
  --h-hap-m 20000 --h-uav-m 0 `
  --wavelength-m 1.55e-6 --visibility-km 10 `
  --beam-waist-m 0.0626 --aperture-radius-m 0.2 --cn2 1e-15 `
  --epsilon-min 0.0005 --epsilon-max 0.005 --va 2 --v-min 0.5 --v-max 3 `
  --va-budget 2 --beta 0.95 --mb-nu 0.1 `
  --fading-samples 4 --awgn-samples 2 --fock-cutoff 40 `
  --channel-seed 4101 --awgn-seed 4102 `
  --output results\baseline_smoke.json
```

The output includes parameters, channel metadata, and raw metrics.

## Training

Resolve a copy of `configs/default.yaml` first. Training commands are
deliberately limited to train/validation data and cannot generate or evaluate
the held-out test split.

```powershell
python scripts\train_ps.py --config configs\resolved.yaml --initialization-seed 1001 --output-dir experiments\adaptive_ps\run_001
python scripts\train_gs.py --config configs\resolved.yaml --initialization-seed 1001 --output-dir experiments\adaptive_gs\run_001
python scripts\train_joint.py --mode ps_gs --config configs\resolved.yaml --initialization-seed 1001 --output-dir experiments\joint_ps_gs\run_001
python scripts\train_joint.py --mode full --config configs\resolved.yaml --initialization-seed 1001 --output-dir experiments\joint_ps_gs\full_001
```

All modes require a common resolved `v_min_snu`/`v_max_snu` box in the paper training harness; fixed baselines must lie inside it. Adaptive-variance modes additionally require the average-`V_A` dual settings. The frozen PS and GS parameterizations preserve C4 symmetry by construction, and the paper training path fails closed on standard-form symmetry.

Run the deliberately tiny implementation smoke check (not publication training):

```powershell
python scripts\smoke_validate_frozen.py --steps 3 --awgn-samples 2 `
  --fock-cutoff 40 --va-budget 1.5 --dual-learning-rate 0.1 `
  --seed 260826 --output results\frozen_transmitter_smoke.json
```

Held-out evaluation is unavailable until one pre-test selection manifest has
frozen every checkpoint, numerical setting, seed, and analysis rule:

```powershell
python scripts\evaluate.py `
  --selection-manifest experiments\publication_selection_manifest.json `
  --checkpoint-id full-seed-1001 `
  --output results\full_seed_1001_held_out.json
```

The evaluator verifies the manifest, configuration, checkpoint hash, mode, and
initialization seed before it constructs the held-out state realization.
The four selected fixed baselines use the same manifest-controlled test states
and AWGN through `scripts/evaluate_baseline.py --scheme-id <name>`.

Before a publication run, follow [NUMERICAL_PARAMETER_FREEZE.md](docs/NUMERICAL_PARAMETER_FREEZE.md)
and [PUBLICATION_EXPERIMENT_PROTOCOL.md](docs/PUBLICATION_EXPERIMENT_PROTOCOL.md).
Dedicated commands are `scripts/validate_mi_convergence.py`,
`scripts/validate_fock_convergence.py`, and
`scripts/select_validation_baselines.py`. Matched fixed-VA learned runs are
selected by `scripts/select_learned_fixed_va.py`. They fail closed while required
configuration values remain unresolved and never use test data for selection.
After all validation-only selections exist, the roster-only post-selection gate
uses `scripts/validate_selected_roster_convergence.py --selection-roster ...`
followed by `scripts/combine_convergence_evidence.py --selection-roster ...`.
These tools reconstruct all selected ensembles on validation only; they perform
no training and cannot construct the held-out test realization.

## Known limitations

This is an asymptotic covariance-based lower-bound calculation, not a finite-key or composable security proof. Distribution matching, reconciliation feasibility, estimator/feedback overhead, trusted detector imperfections, and arbitrary-asymmetric discrete-modulation security are not supplied by the paper. See [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).

The original repository remains intact. See [LEGACY_MAPPING.md](docs/LEGACY_MAPPING.md) for the read-only source audit.
