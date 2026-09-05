# Running numerical experiments

Development smoke runs need only a config and write to `results/`:

```powershell
python scripts/run_baselines_cached_source_moments.py --config configs/baseline_smoke.json
```

Completed Uniform, Binomial, and fixed-MB checkpoints are written immediately
as `baseline_cached_<scheme>.json`; the combined summary is
`baseline_cached_source_moments_smoke.json`. Add `--resume` to reuse a
checkpoint whose normalized config matches. Dirty or unavailable Git metadata
is recorded when possible and never blocks development runs. Historical
hash/EVID artifacts are archival only; later paper freezes use Git commit,
config, seeds, and result files.
