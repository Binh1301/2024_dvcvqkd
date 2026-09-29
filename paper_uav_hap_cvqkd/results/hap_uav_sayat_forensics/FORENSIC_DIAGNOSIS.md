# HAP-UAV versus Sayat 2024 forensic diagnosis

Status: **diagnostic complete with exact-C,w coverage limitation**  
Primary fixture: phase noise OFF, AO OFF, `tau_zen=0.92`, `epsilon=0.0186`,
`beta=0.95`, ideal heterodyne, `T_eff=<sqrt(T_raw)>^2`.

No new C,w source moment was computed. All security rows use existing
hash-matched historical source moments at their actual `(nu_raw,V_A)`.

## Bottom line

The short physical distance is not the controlling variable. At the 30-degree
baseline the current optical model produces

```text
T_eff = 2.548668306761574e-4
loss  = 35.936866815634886 dB
```

The main loss is `A0=5.346028752556014e-4`, equivalent to 32.7197 dB,
because a 0.08 m receiver observes a beam of radius about 2.446 m. Pointing
jitter adds 2.7548 dB. Atmosphere, scintillation, and AoA/FOV together add
only about 0.4624 dB.

At this `T_eff`, all eight currently available exact Uniform points are
negative even with phase noise disabled. The best tested point is

```text
V_A       = 0.1 SNU
I_AB      = 1.8384594915765717e-5
beta I_AB = 1.746536516997743e-5
chi_BE    = 6.0919614311594206e-5
K         = -4.3454249141616776e-5 bits/use
```

Thus the immediate failure is `chi_BE > beta I_AB`, not MI alone. Direct
`Z_minus` and frozen-target full-interval maximization select the same point
and give identical SKR for all eight tested Uniform ensembles, so that
authority mismatch does not explain this numerical result.

## Ranked root causes

| Rank | Parameter / choice | Current value | Sayat 2024 | Quantified effect | Importance |
|---:|---|---:|---:|---|---|
| 1 | Receiver/beam coupling | `D_r=0.08 m`, beam radius `2.446 m` | `D_r=1 or 2 m` | Current `A0` loss `32.72 dB`; small-aperture area gain is `21.94 dB` for 1 m and `27.96 dB` for 2 m | Critical |
| 2 | Beam divergence / transmitter optics | `223 urad`, waist `4.425 mm` | `D_t=0.3 m`, diffraction-limited | `223 urad/(lambda/D_t)=43.16`, a `32.70 dB` scale difference; not additive to A0 because both describe optical coupling | Critical |
| 3 | Excess noise for Uniform at current T | `0.0186 SNU` | channel sum `0.0186 SNU`, but shaped QAM | Sparse-exact Uniform threshold is about `0.0054067 SNU`; current value is 3.44 times larger | Critical |
| 4 | Probability distribution/security moment | Uniform | binomial or optimized discrete Gaussian | Best tested MB is positive; Uniform is negative. MB's much smaller `w` tightens `Z_star` and lowers the Holevo penalty | High |
| 5 | Pointing jitter | factor `0.530304` | fixed APT efficiency `0.9` inside geometric model | Current loss `2.7548 dB`; Sayat pointing term alone is `0.4576 dB` | Medium |
| 6 | Fading scalar | `<sqrt(T)>^2` | deterministic dB transmittance | Replacing by `<T>` changes only `0.377 dB`, far below the missing 25.47 dB | Low |
| 7 | Reconciliation | `beta=0.95` | `beta=0.90` asymptotic | Current model is more favorable | Not a cause |
| 8 | Detector | ideal heterodyne; no detector efficiency/noise | nonideal detector equations and `epsilon_det=0.0135` | Current model is more optimistic. Adding detector loss cannot rescue SKR | Not a cause |

## Current HAP-UAV dB budget

| Component | Loss (dB) |
|---|---:|
| Atmospheric transmittance | 0.418142 |
| Finite-aperture / beam coupling A0 | 32.719687 |
| Pointing-jitter moment | 2.754751 |
| Scintillation square-root moment | 0.042811 |
| AoA/FOV active-probability moment | 0.001475 |
| **Total T_eff** | **35.936867** |

## Sayat 2024 good-channel reproduction

Equations 29--33 of
<https://arxiv.org/html/2211.16862v3> were evaluated at zenith with
`V=200 km`, constant `Cn2=1e-16`, `D_t=0.3 m`, optics efficiencies 0.9,
pointing factor 0.9, and `p_thr=1e-6`. The positive magnitude of the
scintillation fading margin was used.

| Distance | D_r | Geometric | Scattering | Scintillation | Total loss | T |
|---:|---:|---:|---:|---:|---:|---:|
| 200 km | 1 m | 1.658 dB | 0.324 dB | 1.893 dB | 3.874 dB | 0.4098 |
| 300 km | 1 m | 5.179 dB | 0.324 dB | 1.893 dB | 7.396 dB | 0.1821 |
| 500 km | 1 m | 9.616 dB | 0.324 dB | 1.893 dB | 11.833 dB | 0.06556 |
| 1000 km | 1 m | 15.637 dB | 0.324 dB | 1.893 dB | 17.854 dB | 0.01639 |
| 500 km | 2 m | 3.596 dB | 0.324 dB | 0.896 dB | 4.816 dB | 0.3299 |
| 1000 km | 2 m | 9.616 dB | 0.324 dB | 0.896 dB | 10.836 dB | 0.08248 |

The paper's far-field condition invalidates its 2 m formula at 200 and
300 km. Even its 1 m, 1000 km channel is about 18.08 dB better than the
current 22 km HAP-UAV `T_eff`; at 500 km it is about 24.10 dB better.

The paper also does not compare against Uniform 256-QAM: its QAM PMFs are
binomial or discrete Gaussian, and the discrete-Gaussian parameter is optimized.

## Uniform V_A result and exact-coverage boundary

Exact historical C,w exists only at

```text
V_A = 0.1, 0.6, 0.7, 0.8, 1.075, 2.05, 3.025, 4.0 SNU.
```

All eight are negative. The best tested point is `V_A=0.1`; there is no
positive tested range. This is **not** a proof that no `V_A` in `[0.01,5]`
works because:

1. exact C,w is absent at the other requested values;
2. the frozen repository domain is `[0.1,4.0]`, not `[0.01,5]`;
3. lifecycle state prohibits baseline selection and a new high-resolution AP
   source-moment campaign.

Therefore the definitive continuous Uniform optimum remains unresolved. No
interpolation of C,w was used.

## Controlled counterfactual thresholds

These thresholds maximize only over the eight available exact Uniform
candidates.

```text
Minimum T_eff for K>0:       0.0898274552
Maximum loss for K>0:        10.465909 dB
Current T_eff:               0.0002548668
Missing link margin:         25.470958 dB
Winning tested V_A at T*:    0.8 SNU

Maximum epsilon at current T: 0.0054066652 SNU
Current epsilon:              0.0186 SNU
Winning tested V_A at eps*:   0.6 SNU

Required receiver diameter in the current channel model:
D_r approximately 1.52931 m, with other parameters fixed.
```

At `epsilon=0`, Uniform becomes positive at tested `V_A=0.7` with
`K=3.99909e-5`. This demonstrates that both link loss and excess noise matter.

## Uniform versus shaped QAM

At identical `T_eff`, epsilon, beta, and security evaluator:

| Scheme | Best tested parameters | beta I_AB | chi_BE | SKR |
|---|---|---:|---:|---:|
| Uniform | `V_A=0.1` | 1.74654e-5 | 6.09196e-5 | -4.34542e-5 |
| MB historical exact, unconstrained diagnostic | `nu_raw=0.15`, `V_A=3.554867` | 6.20734e-4 | 5.66844e-4 | 5.38903e-5 |
| MB historical exact, current `V_A<=1.5` budget | `nu_raw=0.20`, `V_A=1.383323` | 2.41583e-4 | 2.05060e-4 | 3.65227e-5 |

The unconstrained shaped point has `w=1.27416e-6`; the Uniform points near comparable
high variance have `w` around `2.7e-2` to `3.0e-2`. Shaping concentrates
probability on central symbols, changes the physical normalization, increases
the usable source correlation, and greatly reduces the non-Gaussian penalty
entering

```text
Z_star = 2 sqrt(T) C - sqrt(2 T epsilon w).
```

This is why shaping changes both MI and Eve's Holevo bound; it is not merely
an SNR gain.

The unconstrained MB winner is not a valid production baseline under the
current fading-averaged `V_A<=1.5` budget; the budget-feasible MB row is
reported separately above.

## Distance diagnostic

The fixed geometry has a minimum physical link distance of 19 km, so the
requested 5--18 km segment is impossible without changing the HAP/UAV
altitudes. Over 19--50 km:

- Uniform remains negative; there is no operation distance because it never
  enters the positive region.
- the sparse historical MB envelope remains positive through 50 km, so its
  operation distance is only bounded below by 50 km in this run.
- Uniform has `chi_BE > beta I_AB` throughout; for MB the inequality is
  reversed throughout.

## Convention audit

- `T` is power transmittance; amplitudes are multiplied by `sqrt(T)`.
- The scalar fading experiment uses `<sqrt(T_raw)>^2`. `<T_raw>` is not passed
  to MI/Holevo.
- MI uses complex ideal-heterodyne noise `CN(0, 1 + T epsilon/2)`.
- `V_A=2 sum_i p_i |alpha_i|^2` is validated by the common Ensemble object.
- The same reconstructed ensemble hash binds MI, C,w, Z, and Holevo.
- `beta` multiplies only `I_AB`.
- no detector efficiency or detector electronic noise is implemented. The
  requested `eta_det=0.7`, `epsilon_det=0.0135` therefore cannot be described
  as active parameters.
- no vacuum, heterodyne, channel-noise, or phase-noise double counting was
  found inside the current ideal-detector/phase-off path.
- target documentation requests full-Z maximization while the distance runner
  uses direct `Z_minus`; at all eight tested Uniform points the numerical
  maximizer is the same lower endpoint, so the discrepancy has zero observed
  effect here.

## Artifacts

- `forensic_report.json`
- `current_hap_link_budget.csv`
- `sayat_good_channel_budget.csv`
- `uniform_existing_exact_phase_off.csv`
- `mb_existing_exact_phase_off.csv`
- `uniform_aperture_counterfactual.csv`
- `detector_convention_audit.csv`
- `distance_phase_off_existing_exact.csv`
- `distance_operation_summary.csv`
- `uniform_skr_vs_va_existing_exact.png/.pdf`
- `distance_skr_and_security_terms.png/.pdf`
