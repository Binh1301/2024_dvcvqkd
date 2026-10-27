# Source-moment sensitivity — DIAGNOSTIC_ONLY

These are user-authorized artificial input perturbations, NOT new or approximate
source-moment calculations and NOT certified solver-error bounds.
The primary evaluator correctly rejects perturbed C,w because its source
identity checks would fail (168 expected rejections,14 stored-value passes).
The original guard probe and producer remain in source_sensitivity_provenance_guard_probe/.
No guard is bypassed in the primary evaluator. This separate diagnostic calls
the EXISTING Eq14/Eq13 mathematical component helper at80/110 digits, keeping
cached MI, VA, eta_f and xi_f fixed. It recomputes Z directly; no free-Z search.
It does not claim the perturbed pairs are realizable source moments for the
unchanged physical ensemble. Historical payloads/catalogs remain unchanged.

13 scenarios at14 saved primary contexts:182 component-level rate evaluations,
expanded to1300 position/scenario rows. There are ZERO new channel integrations,
ZERO C,w calculations, no new ensembles and no mission-policy reruns here.

Ranking changes are assessed ONLY by replacing the winning source's rate,
holding the other211 stored candidates fixed. Correlated errors of other
sources are not covered. The tested box is finite and not a convergence proof.

| Scenario | Valid contexts | Min delta K | Max delta K | Ranks | Positive contexts |
|---|---|---|---|---|---|
| stored | 14 | 0 | 0 | ['1'] | 14 |
| C_delta_-1e-10 | 14 | -1.81383714e-10 | -1.81274024e-10 | ['1'] | 14 |
| C_delta_+1e-10 | 14 | 1.81273996e-10 | 1.81383714e-10 | ['1'] | 14 |
| C_delta_-1e-08 | 14 | -1.81383691e-08 | -1.8127398e-08 | ['1'] | 14 |
| C_delta_+1e-08 | 14 | 1.81273996e-08 | 1.81383707e-08 | ['1'] | 14 |
| C_delta_-1e-06 | 14 | -1.81382907e-06 | -1.81273195e-06 | ['1'] | 14 |
| C_delta_+1e-06 | 14 | 1.81274782e-06 | 1.81384495e-06 | ['1'] | 14 |
| w_relative_-0.01 | 14 | 4.38198703e-08 | 4.38474529e-08 | ['1'] | 14 |
| w_relative_+0.01 | 14 | -4.3628749e-08 | -4.3601304e-08 | ['1'] | 14 |
| w_relative_-0.1 | 14 | 4.48611513e-07 | 4.48893893e-07 | ['1'] | 14 |
| w_relative_+0.1 | 14 | -4.26955489e-07 | -4.26686909e-07 | ['1'] | 14 |
| w_relative_-1 | 14 | 8.74219269e-06 | 8.74769552e-06 | ['1'] | 14 |
| w_relative_+1 | 14 | -3.62330594e-06 | -3.62102668e-06 | ['1'] | 14 |

All tested perturbations retain positive SKR at100/100 primary positions and
rank1 against unchanged competitors. Absolute C shifts up to1e-6 produce
about1.814e-6 bits/use rate shifts. Setting w to0 or twice its stored value
changes K by approximately+8.75e-6 or-3.62e-6 bits/use. These finite stress
observations do not bound the unknown numerical error of historical C,w,
and do not justify upgrading INSUFFICIENT_EVIDENCE.
