# Independent Fock / Gram / repository source moments

Scope: selected-source numerical diagnostics, not security certification.
The source moments contain no channel transmittance, excess noise or zenith angle.

## Canonical definitions and checked references

For the identical ordered input arrays `(p,alpha)`, define

\[
\tau=\sum_kp_k|\alpha_k\rangle\langle\alpha_k|,\quad
a_\tau=\tau^{1/2}a\tau^{-1/2}_{\rm MP},
\]
\[
C=\operatorname{Tr}(\tau^{1/2}a\tau^{1/2}a^\dagger),\qquad
w=\sum_kp_k\{\|a_\tau|\alpha_k\rangle\|^2
-|\langle\alpha_k|a_\tau|\alpha_k\rangle|^2\}.
\]

The local publisher PDF of [Sayat et al.](https://doi.org/10.1109/TCOMM.2024.3359295),
IEEE TCOM 72(6), pp.3244–3255, was inspected, including the rendered page3247:
Eq.(20) gives the lower correlation formula, Eq.(21) the coherent-state mixture,
and Eq.(22) the weighted variance. It is the actual 12-page journal version,
not the differently paginated 29-page preprint. The definition and support
convention are cross-checked against [Denys–Brown–Leverrier v3](https://arxiv.org/abs/2103.13945v3),
Eq.(12), Sec.5.1 and the covariance derivation. The MP inverse is zero off support.
The modulation convention used here is the approved VA=2*nbar, not the v43
printed nbar/2 convention; the manuscript is not edited. PDF hashes/pages
are in reference_audit.json; the actual inspected copies are under inputs/.

All moment expressions above are also supplied explicitly by the user. The
derivations below are linear algebra for those definitions, not new source laws.

## A. Direct truncated Fock operator

Let F[n,k]=exp(-|alpha_k|²/2)*alpha_k^n/sqrt(n!), n=0,...,NF-1.
Construct tau_F=F diag(p) F† and a[n-1,n]=sqrt(n), without normalizing
individual columns of F or changing p. In finite arithmetic, diagonalize the
Hermitian tau_F. The declared retained set is I_delta={lambda>delta}; both
the square root and inverse square root are formed on this set. Thus a
positive delta is an explicit regularization, not the exact MP inverse of
the full mathematical source if any genuine positive modes are omitted.

The float64 implementation constructs the NF-by-NF density and operators
directly. The arbitrary-precision implementation constructs the same density
in photon-number-mod4 blocks. For exactly C4-symmetric inputs, off-sector
density entries vanish algebraically; within each block,
tau_F[n,m]=4*sum_over_orbit_representatives p[k] F[n,k] conj(F[m,k]).
This is still a Fock density calculation and never calls an overlap/Gram builder.
The annihilation map is built from physical photon indices, including wrap
between mod4 sectors. No source-moment routine from the repository is imported.

If NF<M, rank(tau_F)<=NF, even when the exact coherent-state ensemble has
rank M=256. A small trace tail alone cannot certify the inverse-square-root
functional. NF, physical tail, retained rank and precision must be reported
separately. The independent Poisson-tail checks use
sum_{n>=NF} exp(-|alpha|²)|alpha|^(2n)/n!, without subtracting a CDF from one.

## B. Independent weighted-overlap representation

Let W map the k-th coordinate to sqrt(p_k)|alpha_k>. Then

\[
H=W^\dagger W,\quad H_{ij}=\sqrt{p_ip_j}
\exp[-(|\alpha_i|^2+|\alpha_j|^2)/2+\bar\alpha_i\alpha_j],
\]
\[
L=W^\dagger aW=H\operatorname{diag}(\alpha).
\]

If H=V Lambda V† on positive support, Q=W V Lambda^{-1/2} has orthonormal
columns and tau=Q Lambda Q†. Consequently

\[
A=Q^\dagger aQ=\Lambda^{-1/2}V^\dagger L V\Lambda^{-1/2},\quad
T=\Lambda^{1/2}A\Lambda^{-1/2},
\]
\[
c_k=Q^\dagger|\alpha_k\rangle
=\Lambda^{1/2}V^\dagger e_k/\sqrt{p_k},
\]
\[
C_B=\sum_{r,s}\sqrt{\lambda_r\lambda_s}|A_{rs}|^2,
\quad w_B=\sum_kp_k(\|Tc_k\|^2-|c_k^\dagger Tc_k|^2).
\]

These equations prove mathematical equivalence to the canonical definitions
when all nonzero modes are included. They do not make a low-precision
thresholded eigensystem numerically equivalent to the exact MP operator.

Method B builds the full weighted overlap matrix and weighted annihilation
entries from the actual frozen arrays. At arbitrary precision it applies a
unitary C4 discrete Fourier transform to that full matrix. In orbit notation,
F_s[orbit(k,r),k]=i^(s*r)/2. It computes F_s† H F_s and
F_s†(H diag(alpha))F_(s-1) directly, then the support formulas above.
No Fock density is built in Method B. Exact rotations and equal orbit weights
are checked before using this reduction; amplitudes or weights are not replaced
by averaged/symmetrized inputs. Methods A and B share numerical libraries and
source arrays, but not a C,w kernel, density construction or overlap evaluator.

## Stable residual and normalization

For a normalized physical coherent state v, u=a_tau v and d=<v,u>,
||u-v*d||²=||u||²-|d|². This is the nonnegative orthogonal-residual identity.

A truncated vector v_F has squared norm t<1. Applying the unit-norm expression
to v_F alone would introduce an error. With u represented in its finite
subspace, the omitted component of the original normalized coherent state
gives the exact correction

\[
\|u-v_Fd\|^2+(1-t)|d|^2=\|u\|^2-|d|^2.
\]

Equivalently, an explicitly orthogonal finite-vector residual is
||u-v_F*d/t||²+(1/t-1)|d|². Normalizing v_F changes the finite problem unless
all factors are carried through. Method A preserves the original coefficients
and records normalized-column results only as a separate diagnostic. Method B
similarly includes the coherent-state component outside retained spectral
support: replace t by ||c_k||². Arbitrary-precision Method A uses this support
identity as well, accounting for both Fock and spectral omissions.
No negative w or correction term is clipped or replaced by an absolute value.

## Numerical controls and meaning of agreement

Complex128 runs use declared thresholds1e-10,1e-12,1e-14,1e-16.
Arbitrary precision uses the prospectively recorded guard floor10^(-digits+20),
with digits80,100,140,180,260 as scheduled. This guard is not a mathematical
rank decision; unresolved positive eigenvalues remain an explicit limitation.
Negative eigenvalues, eigensolver residuals, retained conditions and all raw
w values are saved. Full coherent support requires256 positive modes here.
Agreement of C,w under different NF/digits is an observable diagnostic, not
an error enclosure for omitted modes of an unboundedly conditioned inverse.
Small-constellation full-rank checks validate implementation algebra, not the
missing256-state support or a security theorem.

## Repository equivalence and separate observations

The active repository path is a full-support C4 Gram reformulation, not the
legacy finite Fock backend. In sector eigen-coordinates, its annihilation
matrix is sqrt(Lambda_s) U_s†diag(z)U_(s-1) invsqrt(Lambda_(s-1)); its a_tau
matrix adds the same outer square-root factors as T above. The residual is
weighted by4p because one representative describes four original symbols.
Its channel-independent C,w definitions are therefore the same for this exact
C4 ensemble when the full support and precision assumptions hold.

The repository also contains thresholded dense/support-restricted Fock
diagnostics. They are not the producer of the selected cache entries.
Convergence labels/settings in a cache do not reconstruct lost precision rows.

Denys discusses general correlation-interval maximization in the footnotes
on p.12. This is a separate security-scope observation, not a change to the
source definitions; no Z interval, endpoint substitution, MI/Holevo change or
manuscript edit is implemented. The approved downstream formula remains
Z=2*sqrt(eta_f)*C-sqrt(2*eta_f*xi_f*w), exactly.
