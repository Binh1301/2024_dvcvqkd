# Near-coincident Gram-oracle diagnosis

Status: **diagnostic evidence only; no active numerical rule changed**. No
training or held-out test realization was accessed.

## Independent construction

The oracle forms the weighted coherent-state Gram matrix

`G_ij = sqrt(p_i p_j) exp(-(|alpha_i|^2+|alpha_j|^2)/2 + conj(alpha_i) alpha_j)`.

The positive cross term is required by `G=V^H V`. A minus cross term would
make a nonzero diagonal overlap smaller than one and is rejected by tests. The
C4 block-circulant matrix is unitarily reduced to four 64-by-64 Hermitian
sectors. `C` and `w` are then evaluated in the spectral support using exact
coherent-state matrix elements; no Fock cutoff is used.

The precision ladder `50,80,120,160` digits and adaptive sequence
`1050,1250,1450` were each frozen before their outcomes. The resolved mode
counts were `16,24,33,44,244,256,256` out of the analytic rank 256. The two
full-support runs took 358.24 s and 390.91 s. Their smallest physical
eigenvalue is about `1.72220511016753e-1099`; this explains why float64 dense
Fock eigendecomposition cannot resolve the mathematical support.

## Full-support result

The 1250-digit result is selected and the 1450-digit result is its successive
confirmation. Absolute differences were `1.29e-1244` for `C`, `4.55e-1013`
for `w`, and at most `1.75e-1014` across downstream security quantities.

| Quantity | Full-support value |
|---|---:|
| `C` | `2.0611991664468614` |
| `w` | `0.25553407612253914` |

For bad/medium/good validation states, respectively:

| State | `Z` | `lambda1` | `lambda2` | `lambda3` | `chi_BE` | raw `K` |
|---|---:|---:|---:|---:|---:|---:|
| bad | 0.55714345357920469 | 4.948501847889319 | 1.0275721582985824 | 4.8506982537761987 | 0.13444206983327636 | -0.082074386116173029 |
| medium | 0.63244356891133158 | 4.9337065049363211 | 1.0335462396890043 | 4.8095164782161755 | 0.16063347000061196 | -0.094611868400453297 |
| good | 0.68012274725131538 | 4.9233614466949058 | 1.0356952392775896 | 4.7810161665959479 | 0.17257990623941402 | -0.097993500656721078 |

Raw `K` uses the convergence-selected `N_MC=2048` MI estimate.

## Float64 diagnosis

The exact complex128 C4-Gram implementation was compared on all 16 canonical
certification fixtures at thresholds `1e-14,1e-13,1e-12`.

- Excluding the stress fixture, Gram versus dense Fock maximum errors at
  `1e-13` were `2.44e-15` (`C`), `1.17e-13` (`w`), `2.00e-14` (`Z`), and
  `1.71e-14` (`chi_BE`). All 15 non-stress fixtures pass every frozen
  tolerance at each of `1e-14`, `1e-13`, and `1e-12`.
- For the stress fixture, complex128 Gram at `1e-13` retains eight modes and
  differs from the full-support high-precision oracle by `2.46e-12` (`C`),
  `2.80e-7` (`w`), `1.08e-8` (`Z`), and `5.08e-9` (`chi_BE`), all within the
  already frozen convergence allowances. Its raw-`K` error is also
  `5.08e-9` because every formulation uses the identical frozen
  `N_MC=2048` MI value. The complex128 results at `1e-14` and `1e-13` have
  identical eight-mode supports and bit-identical `C,w,Z`, symplectic
  eigenvalues, `chi_BE`, and raw `K` in this run.
- The active `1e-12` rule retains only six modes and differs from full support
  by `0.2181586469` in `w` and `0.0033089478` bit in `chi_BE`. It is therefore
  not a full-support approximation for this fixture.

At the active threshold and cutoff 128, the maximum raw-`K` errors relative
to the high-precision full-support oracle are `0.0033089478` for complex128
Gram, `0.0033085559` for dense Fock full-matrix evaluation, and
`0.0033086244` for the algebraically support-restricted residual evaluation.
The corresponding `w` errors are `0.2181586469`, `0.2181284586`, and
`0.2181337344`. Thus all three active-threshold formulations fail the frozen
tolerances; their small mutual differences do not establish correctness.

The declared stress fixture is excluded only from the roster-wide
Gram-versus-dense regression because dense float64 Fock cannot be a reference
for an analytic rank-256 Gram matrix whose smallest eigenvalue is about
`1.72e-1099`. At cutoff 128 its six retained modes have minimum retained
eigenvalue `1.77558e-12` and retained condition number `1.72874e11`. It is
still included in the independent high-precision comparison and in the
fail-closed conclusion.

The unthresholded Gram identities are mathematically exact for C4 ensembles.
The complex128 hard-threshold realization is a regularized numerical
approximation: at `1e-14`/`1e-13` it is observable-level tolerance-equivalent
on this finite roster, but it does not resolve the full 256-mode spectrum. It
is not wired into production and no new threshold is frozen.

## Proposed admissibility rule -- not frozen

A prospective future protocol could require, for every hash-bound realized
ensemble: (1) identical support and frozen-metric agreement at `1e-14` and
`1e-13`; (2) complex128 Gram agreement with an independent high-precision
full-support reference on declared stress fixtures; and (3) complete replay on
the selected validation/realized roster. Current finite evidence supports such
a study, but does not authorize changing the active threshold or publication
execution. Gradients are not certified: a hard eigensupport boundary is not a
smooth training rule, so this diagnostic path must not silently replace the
active differentiable implementation.

Machine-readable evidence:

- `results/near_coincident_gram_oracle.json`
- `results/float64_gram_comparison.json`
- `results/near_coincident_fock_diagnostic.json`
