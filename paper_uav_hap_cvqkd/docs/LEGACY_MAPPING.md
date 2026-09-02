# Legacy mapping and classification

The original repository was audited read-only and remains unchanged.

## Authoritative reusable sources

| Original | Reused behavior | New location | Classification |
|---|---|---|---|
| `uav_hap_1/channel/channel_model.py` | Kruse, Gaussian beam, aperture coupling, turbulence, pointing sampling | `src/channel/` | USEFUL, but Rayleigh scale and zenith factor corrected to frozen paper contract |
| `uav_hap_1/config.py` | Table-I motion values and QAM reference constants | YAML configs / typed dataclasses | USEFUL; unreferenced detector defaults not migrated into active model |
| `uav_hap_1/zstar/base.py` | QAM ordering, fixed PMFs, Fock/Holevo equation trace | `src/modulation/`, `src/cvqkd/` | USEFUL; Gaussian MI path not migrated |
| `uav_hap_1_sample/iab/discrete.py` | Discrete-input MI/log-sum-exp structure | `src/cvqkd/mutual_information.py` | USEFUL |
| `uav_hap_joint_ps_gs.py` | Weighted normalization, differentiable MI/security, seed/checkpoint lessons | modular `src/` | Closest ACTIVE legacy executable, but INCONSISTENT with current paper |
| `test_uav_hap_joint_ps_gs.py` | Normalization/gradient/cutoff test ideas | `tests/` | USEFUL |
| `audit_learned_vs_mb.py` | Validation-only MB optimization and uncertainty cautions | future baselines/ablations | EXPERIMENTAL/USEFUL; not migrated wholesale |

## Explicit conflicts resolved by the frozen contract

- Legacy Rayleigh scale: `sqrt((sigma_turb^2+sigma_uav^2)/2)`. New code follows paper Eqs. (21)--(24): `sqrt(sigma_turb^2+sigma_uav^2)`.
- Legacy constant-`C_n^2` path omitted `cos(zeta)^-4`. New code includes it.
- Legacy PS network: three inputs including derived SNR. Paper network: two inputs only.
- Legacy fixed `V_A`. Paper: optional adaptive `V_A` network with explicit bounds.
- Legacy density contraction used conjugation in the transposed orientation. New Eq. (103) uses `|alpha><alpha|` ket--bra orientation.
- Legacy `Z`/discriminant/eigenvalue caps silently repaired invalid states. New code rejects material invalidity and reports tiny roundoff corrections.

## Not migrated

- `experiments/joint_seed2026/*.pt` and all July checkpoints: architecturally incompatible.
- `ps_gs_results*`, `skr_parameter_sweep_results*`, and generated figures: not paper results.
- `uav_hap/`, most `uav_hap_1/` run/visualization scripts, and `project/`: older or conflicting model generations.
- `cvqkd_simulation.py`, `uav_pcs.py`, `compare_iab_methods.py`: legacy/diagnostic conventions outside the frozen path.
- `search_joint_gain_regions.py`, near-threshold outputs, and quick configs: exploratory evaluation of legacy checkpoints.
- `1.py`, `executor.py`, `execute_test.py`, empty `final_report.py`, generated HTML/PID/log artifacts: UNKNOWN or unrelated; no authoritative dependency trace.

## Duplicate families intentionally left untouched

- `uav_hap_1/` and `uav_hap_1_sample/`
- `ps_gs_results/`, `ps_gs_results_v2/`, `ps_gs_results_fast/`, `ps_gs_full_ncut_check/`
- quick/full/GPU sweep output directories

Nothing in those directories was deleted, moved, renamed, reformatted, or overwritten.

