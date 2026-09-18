# Session Handoff

## Latest completed task: EVID-0086 / DEC-0070

The simplified `run_effective_channel_va2.py` runner completed the requested
preliminary effective-channel comparison at `V_A=2.0` for Uniform, Binomial,
and Fixed MB `nu=0.1`.

Effective channel:

```text
T_eff       = 2.990280293659837e-4
epsilon_eff = 0.4690081582855452
beta_rec    = 0.95
```

Final raw SKR values:

```text
Uniform    = -1.402870619160881e-3
Binomial   = -9.203858657136355e-4
Fixed MB   = -9.112353805948547e-4
```

All three source ensembles converged at rank 256 under the 1050/1250/1450 AP
ladder. Full-(Z) Holevo was evaluated for each scheme. No positive-part
clipping was used.

Outputs:

- `results/effective_channel_va2/channel_moments.json`
- `results/effective_channel_va2/effective_channel.json`
- `results/effective_channel_va2/source_moments_va2.json`
- `results/effective_channel_va2/effective_channel_skr_va2.json`
- `results/effective_channel_va2/effective_channel_skr_va2.csv`
- `results/effective_channel_va2/effective_channel_skr_va2.png`

Focused effective-channel/security tests: 44 passed. No training, adaptive
shaping, VA sweep, distance sweep, baseline selection, final-test access, or
publication-scale run was performed.

## Current interpretation

This is a covariance-matched effective-channel diagnostic. It is not equal to
the primary statewise fading average (E[K(T,\epsilon)]), and it must not be
used as the final fading-channel scheme ranking.

## Next action

No further numerical work is required for this diagnostic. The next separate
research task, if desired, is the statewise fading-SKR comparison using the
completed source-moment machinery.
