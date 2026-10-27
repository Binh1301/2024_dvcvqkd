# Unresolved spectrum: what can and cannot be certified

The C,w definitions remain

\[
C=\operatorname{Tr}(\sqrt\tau a\sqrt\tau a^\dagger),\quad
B=a_\tau=\sqrt\tau a\tau_{MP}^{-1/2},\quad
w=\sum_kp_k(\|Bv_k\|^2-|\langle v_k,Bv_k\rangle|^2).
\]

For normalized v_k, the last term is also sum p_k||Bv_k-v_k d_k||^2,
where d_k=<v_k,Bv_k>. For a projected vector q_k of norm squared t_k,
the identical expression is

\[
\|u_k\|^2-|d_k|^2
=\|u_k-q_kd_k\|^2+(1-t_k)|d_k|^2.
\]

This is the correction used by both Phase E and E2. It changes neither the
ensemble nor the source definition. It reduces cancellation; it does not fix
an unresolved pseudoinverse or certify spectral truncation.

## A rigorous scalar lower bound, with no new eigensolve

Let z_k be the 64 C4 representatives, p_k their per-symbol probabilities,
e_k=|z_k|^2 and t_k=z_k^4. For photon residue r, the first 64 rows of its
weighted coherent-state map are

\[
(T_r)_{nk}=\frac{2\sqrt{p_k}e^{-e_k/2}z_k^r t_k^n}{\sqrt{(r+4n)!}},
\qquad n,k=0,\ldots,63.
\]

All z_k are nonzero and all t_k are distinct. T_r is invertible. The exact
infinite coherent-state Gram block H_(-r) is T_r^H T_r plus a PSD tail, so

\[
\lambda_{\min}(H_{-r})\ge\lambda_{\min}(T_r^H T_r)
\ge\|T_r^{-1}\|_F^{-2}.
\]

Let b_kn be the coefficients of prod_(j!=k)(x+|t_j|) and
D_k=prod_(j!=k)|t_k-t_j|^2. Lagrange interpolation bounds the absolute
coefficients of the inverse Vandermonde row by b_kn/sqrt(D_k). Consequently

\[
\|T_r^{-1}\|_F^2\le U_r
=\sum_k\frac{e^{e_k}}{4p_k e_k^r D_k}
\sum_{n=0}^{63}b_{kn}^2(r+4n)!.
\]

certify_spectral_floor.py evaluates a conservative upper bound on U_r:

- Original real/imaginary binary64 values are converted exactly to Fraction.
  Nodes t_k, squared distances and energies are exact rationals.
- |t_k|=e_k^2 is rational, so no complex-absolute-value approximation is needed.
- All e_k<23 and e<3 imply exp(e_k)<3^23. This avoids transcendental rounding.
- Positive numerator/coefficient sums are rounded toward +infinity, and positive
  denominators toward -infinity, using standard-library Decimal at 80 digits.
  No default nearest-rounded arithmetic is used to decide a bound.
- The resulting U upper bounds are compared exactly to powers of ten.

| r | Outward upper bound on ||T_r^-1||_F^2 (rounded here for display) | Certified lambda_min lower bound |
|---:|---:|---:|
| 0 | 2.035797e301 | 1e-302 |
| 1 | 3.188397e304 | 1e-305 |
| 2 | 7.022426e307 | 1e-308 |
| 3 | 1.711262e311 | 1e-312 |

Exact decimal upper endpoints and input/producer hashes are in
spectral_lower_bound_certificate.json. Small independent *saved* Fock spectra
provide sanity checks; they are not the proof. The proof is the positive scalar
inequality plus directed arithmetic. This establishes positivity and a finite
conditioning bound, not values of the 25 missing eigenpairs or accurate C,w.
The earlier ordinary-mpf estimates in analytic_bound_feasibility.json are
clearly labeled non-enclosures; they must not be substituted for this certificate.

## Fock tail and why probability mass is insufficient

For e<N+1, the omitted coherent probability obeys

\[
P_{\ge N}(e)\le\frac{\exp(-e)\,e^N/N!}{1-e/(N+1)}.
\]

In the weighted symbol Gram basis, H-H_N is PSD and its spectral norm is at most
the weighted tail trace. Directed scalar arithmetic, using the loose bound
exp(-e)<=1, proves for NF256

\[
\|H-H_{256}\|_2\le1.802212\times10^{-174}.
\]

This is an error bound on the Gram matrix, not on w. The tighter ordinary-mpf
tail expression around 1.999686e-184 is a non-enclosure estimate. Even the
rigorous small matrix-norm bound can exceed the true smallest eigenvalues by
many orders of magnitude. Finite-Fock annihilation-operator truncation must
also be controlled before transferring it to the source functional.

If epsilon=sum_(discarded) lambda and A is annihilation restricted to the exact
finite source support, a conditional C bound follows from Hilbert-Schmidt norms:

\[
|C-C_{PP}|\le\|A\|_2^2(2\sqrt{\operatorname{Tr}(\tau)\epsilon}+\epsilon).
\]

This still requires a certified operator norm, spectral projector and epsilon.
It supplies no corresponding w bound. In B=√tau A tau^-1/2, missing modes can
be amplified by inverse square roots; discarded eigenvalue mass alone is not
an error bound. Off-diagonal operator matrix elements and eigenvector/subspace
errors are essential.

For positive definite matrices with certified floors m_A,m_B and
||A-B||<=delta, the Sylvester-equation and inverse identities give

\[
\|\sqrt A-\sqrt B\|\le\frac{\delta}{\sqrt{m_A}+\sqrt{m_B}},\qquad
\|A^{-1/2}-B^{-1/2}\|\le
\frac{\delta}{\sqrt{m_A m_B}(\sqrt{m_A}+\sqrt{m_B})}.
\]

Such inequalities can propagate certified matrix/eigenvector/rounding errors,
but become very pessimistic at floors near 1e-312. A rank-truncated reference
is singular, so it cannot simply be inserted as B in these inequalities.
No matrix-entry enclosure, tail-operator bound and eigenvector enclosure has
yet been combined into a useful C,w interval here. A rigorous bound is feasible
as a mathematical program; an adequately small **w remainder bound is not
established**. This leaves Route B INCONCLUSIVE.

## Downstream error requirements

Use the single saved primary context, zenith=0.2132318272752531deg,
eta_f=0.22346465369449367, xi_f=0.0816026951989888. Eq. (14) is unchanged:

\[
Z=2\sqrt{\eta_f}C-\sqrt{2\eta_f\xi_f w}.
\]

At the cached C,w, its local derivatives are dZ/dC=0.9454409631372943 and
dZ/dw=-3999.380230094113. These are sensitivity coefficients, not uncertainty
estimates. Historical A/B differences are observed numerical discrepancies,
not rigorous error bars; arbitrary Phase D perturbations are stress tests.

If justified intervals C in [C_l,C_u], w in [w_l,w_u] with w_l>=0 become available,
monotonicity gives the exact enclosure

\[
Z\in[2\sqrt\eta C_l-\sqrt{2\eta\xi w_u},
       2\sqrt\eta C_u-\sqrt{2\eta\xi w_l}].
\]

No defensible source-functional intervals exist yet, so certified C,w,Z and SKR
intervals are null. No alternative Holevo/SKR value, continuous-angle claim or
new channel integration is produced. See downstream_error_requirements.json.
