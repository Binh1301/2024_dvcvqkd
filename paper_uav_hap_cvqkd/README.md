# UAV/HAP FSO 256-point DM-CV-QKD paper code

This folder is a clean, self-contained implementation of the equations explicitly present in `2026__Binh_s_work (8).pdf`. It models a HAP transmitter, UAV receiver, fluctuating FSO channel, 256-point coherent-state modulation, PS, global GS, adaptive modulation variance, discrete-input mutual information, and the paper's asymptotic ideal-heterodyne Holevo/SKR chain.

It does **not** contain reproduced paper results. The draft's Sections V and VI are empty, no paper figures are defined, and essential numerical values—including `V_min`, `V_max`, sample budgets, cutoffs, and training settings—are absent. July legacy checkpoints and plots were intentionally not copied.

## Scientific scope

- Power transmittance is evaluated instantaneously and SKR is averaged after per-state evaluation.
- `V_A = 2 sum_i p_i |alpha_i|^2` is asserted statewise.
- The PS network is exactly `2 -> 128 -> 256` on `[log10(T), epsilon]`.
- The adaptive-variance network is exactly `2 -> 64 -> 1`, followed by the paper's bounded log-domain mapping. Bounds are mandatory.
- GS is one global, channel-independent `256 x 2` tensor.
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
tests/         scientific invariants and limiting cases
docs/          equation, paper, legacy, assumption, and issue maps
results/       empty until a resolved run is executed
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

Tests cover the 16x16 grid, PMFs, weighted centering/energy, Rayleigh moments/support, the `cos^-4(zeta)` factor, PS/GS/`V_A` gradients, MI limits, density orientation, standard-form rejection, covariance physicality, SKR averaging, and invalid inputs.

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
  --epsilon 0.001 --va 2 --beta 0.95 --mb-nu 0.1 `
  --fading-samples 4 --awgn-samples 2 --fock-cutoff 40 `
  --channel-seed 4101 --awgn-seed 4102 `
  --output results\baseline_smoke.json
```

The output includes parameters, channel metadata, and raw metrics.

## Training

Resolve a copy of `configs/default.yaml` first. Train/validation/test seeds and budgets are separate.

```powershell
python scripts\train_ps.py --config configs\resolved.yaml --output-dir experiments\adaptive_ps\run_001
python scripts\train_gs.py --config configs\resolved.yaml --output-dir experiments\adaptive_gs\run_001
python scripts\train_joint.py --mode ps_gs --config configs\resolved.yaml --output-dir experiments\joint_ps_gs\run_001
python scripts\train_joint.py --mode full --config configs\resolved.yaml --output-dir experiments\joint_ps_gs\full_001
```

For adaptive-variance modes, `v_min_snu` and `v_max_snu` must be explicitly resolved. Learned PS/GS can break the symmetry needed by the paper covariance; strict training then stops. `--allow-unproven-standard-form` exists only for explicitly labeled exploratory diagnostics and is not paper-faithful security evidence.

Evaluate a frozen checkpoint on explicitly new random streams:

```powershell
python scripts\evaluate.py --checkpoint experiments\joint_ps_gs\run_001\best.pt `
  --channel-seed 9101 --awgn-seed 9102 --fading-samples 256 `
  --awgn-samples 128 --output results\run_001_independent_test.json
```

The evaluation artifact includes per-state `T`, `I_AB`, `chi_BE`, raw SKR, modulation variance, diagnostics, and the derived namespaced seeds.

## Known limitations

This is an asymptotic covariance-based lower-bound calculation, not a finite-key or composable security proof. Distribution matching, reconciliation feasibility, estimator/feedback overhead, trusted detector imperfections, and arbitrary-asymmetric discrete-modulation security are not supplied by the paper. See [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md).

The original repository remains intact. See [LEGACY_MAPPING.md](docs/LEGACY_MAPPING.md) for the read-only source audit.
