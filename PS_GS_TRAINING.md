# Reproducible PS and PS+GS training

The executed pipeline is implemented in `uav_hap_joint_ps_gs.py`. It uses the
existing UAV-HAP channel and QAM definitions while keeping the differentiable
MI and Holevo calculations in float64/complex128 PyTorch.

## Important conventions

- Every shaped constellation is centered with its active probabilities.
- The unit geometry satisfies `sum_i p_i |x_i|^2 = 1`.
- The channel constellation is `alpha_i = sqrt(V_A/2) x_i`.
- Checkpoint selection uses fixed-validation `K_raw = beta I_AB - chi_BE`.
- Joint epoch zero is saved before any optimizer update.
- Test channel/AWGN seeds are independent of training and validation seeds.
- Rayleigh samples describe channel fading, never symbol probabilities.

## Configurations

- `ps_gs_fast_config.json`: development/debugging only. It does not establish a
  converged physical conclusion.
- `ps_gs_full_config.json`: staged schedule with final `ncut=150`, larger
  validation/test budgets, and repeated Monte Carlo evaluation.

## Training commands

PS-only:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --mode ps --output-dir experiments\ps_seed2026
```

GS-only:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --mode gs --output-dir experiments\gs_seed2026
```

Staged PS plus GS plus PS+GS:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --mode joint --output-dir experiments\joint_seed2026
```

Exact resume from the last valid optimizer state:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --output-dir experiments\joint_seed2026 --resume experiments\joint_seed2026\checkpoints\last_valid_joint.pt --resume-additional-epochs 100
```

Final evaluation without retraining:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --output-dir experiments\joint_seed2026 --evaluation-only
```

## Reading the console output

- `val_K=skipped` means that epoch is between validation checks. With the full
  configuration, validation runs every five epochs and at the end of a phase.
  It does not indicate a non-finite model value.
- Full evaluation intentionally takes longer than a training epoch because it
  uses 256 fading states, 128 AWGN samples per symbol, `ncut=150`, and five
  independent uncertainty runs. Scheme-level progress is printed while it runs.
- If final evaluation is interrupted after training, the best and final
  checkpoints remain valid. Run the evaluation-only command above in the same
  output directory; retraining is not required.

## Required ablations

PS-preserving joint initialization:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --joint-initialization ps_preserving --output-dir experiments\joint_ps_init
```

Independent PS plus GS initialization:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --joint-initialization combined --output-dir experiments\joint_combined_init
```

No geometric regularization:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --disable-geometry-regularization --output-dir experiments\joint_no_reg
```

Regularization warm-up uses the default zero start factor. A nonzero start can
be tested with:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --geometry-regularization-start-factor 0.1 --output-dir experiments\joint_reg_start_01
```

Simultaneous and alternating updates:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --update-strategy simultaneous --output-dir experiments\joint_simultaneous
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --update-strategy alternating --alternating-ps-steps 3 --output-dir experiments\joint_alternating
```

Reduced versus full cutoff:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_fast_config.json --output-dir experiments\joint_reduced_ncut
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --output-dir experiments\joint_full_ncut
```

Small versus large Monte Carlo budgets:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_fast_config.json --output-dir experiments\joint_small_mc
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --output-dir experiments\joint_large_mc
```

Independent training seeds:

```powershell
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --seed 2026 --output-dir experiments\joint_seed2026
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --seed 2027 --output-dir experiments\joint_seed2027
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --seed 2028 --output-dir experiments\joint_seed2028
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --seed 2029 --output-dir experiments\joint_seed2029
python uav_hap_joint_ps_gs.py --config ps_gs_full_config.json --seed 2030 --output-dir experiments\joint_seed2030
```

## Tests

```powershell
python -m unittest test_uav_hap_joint_ps_gs uav_hap_1_sample.tests.test_discrete_mi
```

The test suite covers weighted normalization and gradient flow, PS-preserving
joint equivalence, epoch-zero ranking, checkpoint/RNG restoration, Holevo
gradients, discrete-MI regressions, and a real `ncut=150` security evaluation.

## Interpretation

Fast or failed PS+GS optimization is not evidence that PS is fundamentally
better. Separate optimization failure, initialization compatibility,
regularization conflict, Monte Carlo uncertainty, and cutoff convergence before
making a physical-layer conclusion. A PS+GS gain should be claimed only when
repeated full training seeds and independent test confidence intervals support
it.
