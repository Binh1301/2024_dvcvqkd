# Winning source: full-support spectral audit

Scope: **DIAGNOSTIC_ONLY**. C,w convergence conclusion: **INCONCLUSIVE**.
The scalar positivity certificate below is not a certificate of the source moments.

The unchanged source is nu_raw=0.30, nu_repo=12.75,
VA=1.358333319784304, VA_hex=0x1.5bbbbb818a6b0p+0, M=256.
Ensemble hash: b083ac8400f7e1068ec045f9882bd256cbbfdec50b64d66d8b7f2d84c05eb214.
Payload hash: f835e47731891c935fceab522cddc1e7e9875629fd9166ec0532273e7b694f32.
See input_provenance.json for exact array hashes and the original cache path.
The binary64 PMF sum is 1.00000000000000005427334506041016108037856461735;
this rounding discrepancy is preserved, with no renormalization. The same p,alpha
are used everywhere. VA=2*nbar, X_A=2Re(alpha) and nu_repo=42.5*nu_raw remain unchanged.

## Mathematical support and complete C4 decomposition

For the weighted coherent-state matrix W, its first 256 Fock rows are

\[
W_{nk}=\sqrt{p_k}\,e^{-|\alpha_k|^2/2}\frac{\alpha_k^n}{\sqrt{n!}},
\qquad n=0,\ldots,255.
\]

All weights are positive and all 256 amplitudes are distinct. Multiplication by
nonzero diagonal factors leaves a Vandermonde determinant proportional to
\(\prod_{i<j}(\alpha_j-\alpha_i)\ne0\). Thus W has rank 256 and all nonzero
eigenvalues of tau, equivalently the 256x256 weighted Gram matrix H=W^H W,
are strictly positive. None of the 25 unresolved modes is mathematically zero.

The exact orbit grouping is checked on the original binary64 arrays, not on
rounded coordinates or an artificially symmetrized ensemble. With
\(F_s[g(k,r),k]=i^{sr}/2\), Q=[F_0,F_1,F_2,F_3] is unitary, and H splits
into four complete 64x64 blocks. This is a change of basis, not rank truncation.
For these conventions **Gram sector s corresponds to Fock photon sector
r=(-s) mod 4**. Matching sector numbers directly would be wrong for s=1,3.

Fresh, inexpensive complex128 checks: unitary error 0; off-block relative error
3.7122e-17; full-vs-sector eigenvalue difference at most 8.8818e-16.
These checks validate the decomposition algebra, not 256 tiny eigenvalues.
See float_sector_checks.json.

## Historical spectra actually available

| Method | Precision | Matrix dimension | Retained rank | Floor |
|---|---:|---:|---:|---:|
| Fock NF64 | 80 | 4x16 | 64 | 1e-60 |
| Fock NF96 | 100 | 4x24 | 96 | 1e-80 |
| Fock NF128 | 140 | 4x32 | 128 | 1e-120 |
| Gram | 80 | 4x64 | 105 | 1e-60 |
| Gram | 180 | 4x64 | 186 | 1e-160 |
| Fock NF256 | 260 | 4x64 | 231 | 1e-240 |

NF64/96/128 cannot represent 256-dimensional support even with perfect arithmetic.
At NF256, the finite Fock projection has rank 256 in exact arithmetic, but only
231 eigenvalues exceed the declared numerical floor. The remaining 25 have
unresolved accuracy; a positive computed sign below the floor is not enough.
The raw NF256 calculation has 251 positive signs and five negative signs, which
does not contradict mathematical positivity. Gram180 has 228 positive signs
but retains only 186 modes. Neither sign count certifies rank.

| Fock photon sector r | Gram s | Fock260 rank | Smallest retained Fock260 | Largest eigenvalue | Retained condition |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 58 | 1.2508124e-234 | 0.59553349 | 4.7611735e233 |
| 1 | 3 | 58 | 1.1137016e-236 | 0.24087341 | 2.1628182e235 |
| 2 | 2 | 58 | 9.2923816e-239 | 0.09742502 | 1.0484397e237 |
| 3 | 1 | 57 | 1.3078290e-232 | 0.03940559 | 3.0130536e230 |

| Fock photon sector r | Gram180 rank | Smallest retained Gram180 | Retained condition |
|---:|---:|---:|---:|
| 0 | 47 | 6.6982024e-158 | 8.8909450e156 |
| 1 | 47 | 1.9525059e-159 | 1.2336629e158 |
| 2 | 46 | 7.3784750e-155 | 1.3203950e153 |
| 3 | 46 | 2.2482972e-156 | 1.7526859e154 |

186 sector-matched eigenvalues agree between Gram180 and Fock256/260; the maximum
relative difference is 2.6966330305187137e-27. This is stronger than agreement of
C,w alone, but it verifies neither the other 70 Gram modes nor historical
eigenvectors, which were not saved. The 231 Fock retained modes include 25
additional modes not independently cross-checked by a completed Gram reference.
The minimum within-sector relative gap among reliable retained eigenvalues is
about 0.9732. Near degeneracy is not seen there. Gaps inside the unresolved tail
remain unknown; cross-sector proximity does not mix the exact C4 blocks.

sector_spectrum_diagnostics.csv has 32 summary rows. Historical residual fields
repeat the saved maximum aggregate residual, explicitly labeled as such; no
per-sector/per-pair historical residual or reconstruction check is fabricated.
historical_spectrum_slices.json retains all completed AP spectrum slices with
their original file hashes. Four Gram260 rows are timeout markers without numbers.

## Magnitudes and precision diagnosis

Extrapolating the last 6/8/10/12 retained log-eigenvalues in the *finite NF256*
sectors suggests 64th eigenvalues around 1e-274 to 1e-284. This is a planning
estimate, not a bound on the actual full Gram minima. The Gram180 extrapolation
is less stable. Precision selection should not rely only on either fit.

A separate rigorous scalar argument in unresolved_spectrum_error_analysis.md
and spectral_lower_bound_certificate.json proves these conservative bounds:

| Fock photon sector r | Gram s | Certified lower bound on full Gram lambda_min |
|---:|---:|---:|
| 0 | 0 | 1e-302 |
| 1 | 3 | 1e-305 |
| 2 | 2 | 1e-308 |
| 3 | 1 | 1e-312 |

These are bounds, not estimated eigenvalues. Since trace(H)<2 for the exact
binary inputs, corresponding full-sector condition bounds are <2e302,
<2e305, <2e308 and <2e312. Actual full condition numbers remain unmeasured.

The leading limitation is conditioning combined with precision/floor selection.
The eigensolver's saved global residuals near 1e-180 or 1e-260 do not establish
relative accuracy for much smaller eigenvalues. Fock truncation is a separate
obstacle: even NF256's tiny tail need not be tiny relative to those eigenvalues.
C4 decomposition itself loses no spectrum. Increasing NF alone, lowering a
float64 threshold, or accepting raw positive signs cannot resolve this problem.

The 260-digit Gram job logged ranks 58,57,58,58 before its 180.125s timeout,
but saved no numerical eigenpair checkpoint. Those eigendecompositions cannot
be resumed from text logs. No 260-digit job was relaunched in E2.

## Formula preservation

The source definitions remain the Phase E definitions, originating from
[Denys, Brown and Leverrier (2021)](https://arxiv.org/abs/2103.13945v3) and
the Sayat journal equations audited in Phase E. The Vandermonde bounds here are
derived separately; they are not attributed to those papers.
Eq. (14), manuscript MI and Holevo are unchanged. No new target C,w, channel,
MI, Holevo, SKR, zenith or mobility calculation was performed.
