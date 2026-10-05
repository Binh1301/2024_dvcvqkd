# Redesigned-baseline MB/V_A continuation final report

The frozen physical model, configuration, model hash, constellation convention,
direct-$Z_-$ Holevo evaluator, and compatible exact cache were unchanged. No
rectangular global restart was used.

## A. Final local optimum

| nu_raw | V_A | I_AB | beta I_AB | chi_BE(Z-) | K |
|---:|---:|---:|---:|---:|---:|
| 0.165 | 5.5 | 0.639529447234013 | 0.6075529748723123 | 0.5285110296626288 | 0.07904194520968355 |

Uniform reference: `nu_raw=0`, `V_A=1.075`, `K=0.008551627907451953`.
The exact MB gain is `0.0704903173022316 bits/use` (`824.2912%`).
The ridge moved toward higher `nu_raw` and lower `V_A` relative to `(0.15,6)`.

## B. Local refinement and top exact candidates

All points used are recorded in `evaluated_points.csv` and the
`continuation_stage_*_new_points.csv` files. The top ten exact rows are:

| rank | nu_raw | V_A | I_AB | beta I_AB | chi_BE(Z-) | K |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | .165 | 5.50 | .6395294472 | .6075529749 | .5285110297 | .0790419452 |
| 2 | .165 | 5.55 | .6442181556 | .6120072479 | .5329656209 | .0790416269 |
| 3 | .165 | 5.60 | .6488916753 | .6164470915 | .5374090573 | .0790380342 |
| 4 | .160 | 5.60 | .6488916723 | .6164470886 | .5374125857 | .0790345030 |
| 5 | .165 | 5.40 | .6301060669 | .5986007635 | .5195681669 | .0790325967 |
| 6 | .160 | 5.50 | .6395294444 | .6075529722 | .5285210729 | .0790318993 |
| 7 | .170 | 5.50 | .6395294490 | .6075529765 | .5285261789 | .0790267976 |
| 8 | .160 | 5.70 | .6581935363 | .6252838595 | .5462589568 | .0790249028 |
| 9 | .165 | 5.70 | .6581935395 | .6252838625 | .5462626820 | .0790211805 |
| 10 | .160 | 5.40 | .6301060642 | .5986007610 | .5195839688 | .0790167922 |

Best-minus-second gap is `3.1826895463e-7 bits/use`. GH-order 8/16/32/64
recomputation over the top ten changed MI by at most `1.498e-10`, so this
ranking is numerically stable under that check.

## C. High-nu closure table

| nu_raw | best tested V_A | max exact SKR on slice | status |
|---:|---:|---:|---|
| .4 | 3.0 | .0700162812 | CLOSED |
| .5 | 3.0 | .0638542433 | CLOSED |
| .6 | 3.0 | .0538106806 | CLOSED |
| .8 | 1.5 | .0465739506 | CLOSED |

Each slice used exact VA probes at low/intermediate/moderate values; all are
below the local best and decrease through the formal `nu_raw=0.8` boundary.

## D. Boundary status

`VA_MIN = CLOSED`

`VA_MAX = CLOSED`

`NU_MAX = CLOSED`

All candidate rows use `epsilon_total=0.0186`, AO OFF, phase noise OFF, no peak
or budget constraint, and direct `$Z_-$`. No interpolation, full-Z rows, Adam,
training, final-test access, or baseline selection was used.

## E. Final lifecycle status

`GLOBAL_OPTIMUM_RESOLVED`
