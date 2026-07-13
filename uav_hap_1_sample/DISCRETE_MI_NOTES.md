# Discrete-input MI sample

This copy leaves `uav_hap_1` unchanged and switches the protocol-level default
to the differentiable, discrete-input mismatched-decoding estimator.

- `mi_mode="discrete"` is the default.
- `mi_mode="legacy_gaussian"` reproduces the previous `compute_IAB` result.
- `compute_discrete_iab` accepts a vector of instantaneous transmittances and
  returns one MI value per fading realization. Average those returned values for
  ergodic reporting; do not evaluate only at the mean transmittance.
- Training should use 2--8 noise samples per symbol and fresh AWGN draws.
- Evaluation should use 64--256 samples and a fixed `torch.Generator` seed.
  The reporting-oriented `compute_metrics` wrapper defaults to seed 2026 when
  no generator is supplied, while the lower-level differentiable estimator
  uses fresh global RNG draws when its generator is omitted.
- `skr_raw` is never projected to zero. The `skr` field remains the nonnegative
  reporting value used by the existing plots.

The original package has no autoencoder/probabilistic-shaping training model and
no LaTeX source. Therefore, the differentiable estimator is exposed as a PyTorch
function for use by a future model, while `replacement_MI_section.tex` contains
the manuscript replacement requested for the unavailable source document.

Run validation and comparison from the repository root:

```powershell
python -m unittest uav_hap_1_sample.tests.test_discrete_mi -v
python -m uav_hap_1_sample.run_compare_mi_modes --noise-samples 128
```
