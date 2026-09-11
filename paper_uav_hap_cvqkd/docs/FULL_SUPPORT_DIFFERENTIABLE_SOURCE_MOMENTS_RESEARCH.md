# Full-Support Differentiable 256-State DM-CV-QKD Source Moments

## Executive conclusion

The current C4 source-moment target is mathematically consistent with the
finite-constellation DM-CV-QKD bound being used by the repository. In
particular, the security literature defines the weighted state
\(\tau=\sum_k p_k|\alpha_k\rangle\langle\alpha_k|\), the transformed
annihilation operator \(a_\tau=\tau^{1/2}a\tau^{-1/2}\) on the support, and a
non-Gaussianity term \(w\) that is a sum of squared projection residuals. These
are the same objects represented by the repository's C4 factors \(B_s,A_s,Q_s\)
and residual \(E_s\), up to the repository's fixed sector convention.

The proposed forward-mode diagnostic is mathematically the right next
diagnostic. It should compare three independently accumulated quantities:

1. a corrected arbitrary-precision central finite difference;
2. an arbitrary-precision forward tangent propagated through the exact
   differential equations; and
3. the current custom reverse VJP.

The existing evidence already separates ordinary algebra from target
conditioning. Four small fixtures pass the corrected forward and VJP checks,
including real and imaginary complex-alpha directions. On the actual 256-state
ensemble, however, the corrected AP finite difference is
\(dJ=1.7741810692945004\times10^{-3}\), while the custom reverse returns
\(3.3995565604790261\times10^{102}\). The reverse pass takes about 7.1 hours
for one direction. This is an invalid gradient and an impractical training
path.

The most likely explanation is a combination of severe numerical
ill-conditioning and cancellation through explicit inverse-spectrum
intermediates. It is not possible to exonerate the reverse implementation
until the forward tangent oracle and local adjoint identities pass at the
target spectrum. A simple replacement of ordinary transpose by conjugate
transpose would be incorrect in the corrected AP worker: the worker's
transpose is part of a solve-orientation construction. Any explicit transpose
in a differentiated graph does, however, require the ordinary-transpose
adjoint, not the Hermitian-transpose adjoint.

The primary recommendation is therefore:

> Build an exact C4 operator/tangent boundary that evaluates the same C and w
> through right-side solve constraints, never materializes inverse square-root
> or inverse Gram matrices unless a diagnostic requires them, and validate its
> forward tangent before repairing or trusting a reverse VJP. Once the tangent
> oracle is correct, move the same equations to a compiled arbitrary-precision
> backend with certified precision escalation. Keep adaptive training closed
> until all four physical directions pass and the measured per-gradient cost
> is acceptable.

This is an exact-arithmetic reformulation and numerical implementation plan,
not a security surrogate. Spectral clipping, jitter, support truncation,
pseudoinverse rank reduction, and a changed security bound remain out of
scope.

## 1. Scope, evidence, and status

### Repository facts

The following are repository evidence, not literature claims:

| Item | Current evidence |
|---|---|
| Ensemble | Full-support uniform 256-QAM, represented by 64 C4 prototypes |
| Support | 256 positive probabilities, 256 distinct coherent states, 256/256 resolved in corrected AP target endpoints |
| Smallest target Gram-sector eigenvalue | Approximately \(3.9730108272405810054\times10^{-618}\) |
| Corrected C | \(0.85985110654649868138037962728289179096834048571987\) |
| Corrected w | \(0.018327610474963502048823295065766568532781601388489\) |
| Corrected AP source artifact | results/ap_worker_corrected_case_A_20260911.json |
| Corrected AP artifact SHA-256 | f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44 |
| Exact ensemble SHA-256 | c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3 |
| Corrected worker SHA-256 | 2cd1feeeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1 |
| Current custom-backward SHA-256 | f9b15ae2134fa8aa5137bd9ff298baac98a2a35148431636c644c25c28ae2b92 |
| Target directional result | Corrected AP \(dJ=0.0017741810692945003680\); custom \(dJ=3.3995565604790261\times10^{102}\) |
| Custom reverse runtime | 25653.3898618 seconds, approximately 7.1 hours |
| Lifecycle | NOT_READY_FOR_PUBLICATION_SCALE_RUNS |
| Adaptive status | NOT_READY_FOR_ADAPTIVE_TRAINING |

The old arbitrary-precision artifact with the incorrect w construction is
superseded and is not an oracle. The corrected worker uses aa = x2.T, not
aa = sr * x2.T.

### Evidence labels used below

- **Repository evidence** means a stored result, source inspection, hash, or
  bounded test already present in this checkout.
- **Literature fact** means a claim supported by a cited paper or numerical
  linear-algebra reference.
- **Derivation** means algebra shown here from the frozen repository
  equations.
- **Numerical inference** means an inference from the measured spectrum,
  precision, or runtime; it is not a proof of the implementation's root cause.
- **Speculation** means a live hypothesis that must be falsified by the
  proposed tests.

No publication-scale training, optimizer step, final-test access, channel
change, security-equation change, clipping, jitter, or support truncation was
performed for this investigation.

## 2. Source-theory audit

### What the security literature actually defines

Denys, Brown, and Leverrier derive an analytical lower bound for discrete
modulation and explicitly define

$$
\tau=\sum_k p_k|\alpha_k\rangle\langle\alpha_k|,
\qquad
a_\tau=\tau^{1/2}a\tau^{-1/2},
$$

where the inverse is taken on the support. Their expression for the
non-Gaussianity term is

$$
w=\sum_k p_k\left(
\langle\alpha_k|a_\tau^\dagger a_\tau|\alpha_k\rangle
-|\langle\alpha_k|a_\tau|\alpha_k\rangle|^2
\right).
$$

They also give the equivalent projection-residual interpretation

$$
w=\sum_k p_k\left\|
\Pi_k^\perp a_\tau|\alpha_k\rangle
\right\|^2.
$$

These definitions are stated in the paper, not inferred from this
repository. See Denys et al., especially the definitions of \(\tau\),
\(a_\tau\), \(w\), and the residual interpretation
[1](https://arxiv.org/html/2103.13945).

The same paper uses the source term in the correlation interval in the form

$$
Z_\pm=2\sqrt{T}\,
\operatorname{tr}\!\left(\tau^{1/2}a\tau^{1/2}a^\dagger\right)
\pm\sqrt{2T\xi w}.
$$

The repository's C/w convention is therefore not an arbitrary numerical
surrogate. The repository still has to preserve its own exact sector
normalization and full physical \(Z\)-interval semantics. The original paper
also discusses maximizing the Holevo quantity over the allowed interval; it
does not justify hard-coding the lower endpoint as a universal maximizer.

### What is not supplied by the literature

The surveyed source papers do not provide a differentiable, full-support,
256-state C4 implementation with reverse-mode derivatives at a smallest
Gram eigenvalue near \(10^{-618}\). Denys et al. provide ancillary Python
scripts for evaluating analytical QAM quantities, but not a full-support
automatic-differentiation or custom-VJP protocol at this conditioning scale.
This is an audit result, not proof that no unpublished implementation exists.

The other relevant security approaches use different numerical objects:

- Ghorai et al. and Lin et al. use numerical SDP approaches for discrete
  modulation, with finite-dimensional numerical representations rather than
  the current exact C4 C/w VJP
  [2](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.9.021059),
  [3](https://journals.aps.org/prx/abstract/10.1103/PhysRevX.9.041064).
- Kaur, Guha, and Wilde use a Gauss-Hermite/continuity route to establish a
  Gaussian-comparison result; this is not the current source-moment
  differentiation problem
  [4](https://link.aps.org/accepted/10.1103/PhysRevA.103.012412).
- Upadhyaya et al. develop a finite-dimensional reduction with an analytical
  correction, and Kanitschar et al. and Bäuml et al. address other finite-size
  or coherent-attack settings. None supplies the missing target VJP
  [5](https://journals.aps.org/prxquantum/abstract/10.1103/PRXQuantum.2.020325),
  [6](https://doi.org/10.1103/PRXQuantum.4.040306),
  [7](https://quantum-journal.org/papers/q-2024-07-18-1418/).
- The recent free-space DM-CV-QKD paper surveyed here uses numerical SDP
  security calculations and does not provide this differentiable C4
  full-support route
  [8](https://journals.aps.org/prapplied/abstract/v7d9-ylyl).

High-order QAM experiments demonstrate that 64- and 256-state modulation is
experimentally relevant, but they report key-rate experiments or analytical
security evaluations rather than the conditioning or derivative behavior of
the present Gram representation
[9](https://arxiv.org/abs/2203.08470),
[10](https://arxiv.org/abs/2111.12356).

## 3. Frozen C4 finite-dimensional representation

Let \(s\in\mathbb Z_4\), \(r=s-1\pmod 4\), and \(n=64\). Let \(p_i>0\),
\(\sum_i p_i=1\), \(z_i\in\mathbb C\), \(D=\operatorname{diag}(z)\), and

$$
P=\operatorname{diag}\left(\frac{1}{2\sqrt{p_i}}\right).
$$

For \(\rho_d=i^d\), define the raw block

$$
H_d[i,j]=\sqrt{p_i p_j}\,
\exp\left[
-\frac{|z_i|^2+|\rho_dz_j|^2}{2}
+\overline{z_i}\rho_dz_j
\right].
$$

The sector matrices are

$$
X_s=\sum_{d=0}^3 i^{sd}H_d,
\qquad
G_s=\frac{X_s+X_s^\dagger}{2}.
$$

This is the repository's fixed C4 convention. The Hermitian projection is
important: the raw finite-precision sum is not assumed to be exactly
Hermitian after evaluation.

For a positive PMF and a distinct finite coherent-state set, the full Gram
matrix is positive definite. A finite set of distinct coherent states is
linearly independent, a fact used in the analytical treatment of finite
constellations by Denys et al. [1]. C4 block diagonalization is a unitary
change of basis, so it preserves positive definiteness in exact arithmetic.
The tiny target eigenvalue is therefore a conditioning issue, not evidence
of a physical rank deficiency.

For each sector define

$$
S_s=G_s^{1/2},\qquad
R_s=S_s^{-1},\qquad
J_s=G_s^{-1}.
$$

The frozen products are

$$
B_s=S_sDR_r,\qquad
A_s=G_sDJ_r,\qquad
Q_s=S_sP,\qquad
T_s=A_sQ_r.
$$

The statewise projection coefficient and residual are

$$
u_k=\sum_s(Q_s^\dagger T_s)_{kk},
\qquad
E_s=T_s-Q_s\operatorname{diag}(u).
$$

The source moments are

$$
C=\sum_s\operatorname{Re}\operatorname{Tr}
\left(S_sB_sS_rB_s^\dagger\right),
$$

and

$$
w=\sum_{s,k}4p_k\|E_s[:,k]\|_2^2.
$$

### Why A and B have these forms

This is a derivation from the finite-dimensional weighted-state
factorization. Let \(V_s\) be the coefficient matrix of the weighted
coherent states in sector \(s\), so \(G_s=V_s^\dagger V_s\), and let

$$
U_s=V_sG_s^{-1/2}=V_sR_s.
$$

Then \(U_s^\dagger U_s=I\). The annihilation map between neighboring C4
sectors has coefficient action \(aV_r=V_sD\), in the repository's sector
orientation. Consequently,

$$
U_s^\dagger aU_r
=R_sG_sDR_r
=S_sDR_r
=B_s.
$$

On the support, \(\tau^{1/2}\) has matrix representation \(S_s\) in this
orthonormalized sector basis. Therefore

$$
U_s^\dagger a_\tau U_r
=S_sB_sR_r
=S_s^2DR_r^2
=G_sDG_r^{-1}
=A_s.
$$

This proves that the corrected worker's aa = x2.T result is the desired
\(A_s\). The old aa = sr * x2.T result inserts an additional \(S_s\) and
therefore differentiates a different quantity if carried into the reverse
path.

The \(Q_s=S_sP\) columns are the repository's sector components of the
normalized orbit states. The factor \(1/2\) is the C4 orbit normalization
under the current convention. This factor is not a new security assumption;
it is part of the frozen C4 coordinate representation.

## 4. Forward differential audit

### Is the proposed diagnostic correct?

Yes, subject to three conditions:

1. the perturbed \(p,z\) path is the same physical path used by the
   finite-difference oracle, including softmax, GS normalization, and
   \(V_A\) scaling;
2. every perturbed point remains positive, distinct, and full support; and
3. all matrix solves and square-root tangents are performed at a precision
   that resolves the perturbed spectrum.

A forward tangent and a central finite difference are independent enough to
locate an error before reverse-mode code is considered. They are not
independent if they share the same cached \(S,R,J\) values or the same
incorrect forward worker. The tangent runner should therefore construct its
own \(dG\) and compare its base forward \(C,w\) against the corrected worker
before comparing derivatives.

### Raw blocks and sector tangents

Write the exponent in \(H_d[i,j]\) as \(\kappa_{d,ij}\). For a real
parameter path, \(d\overline z=\overline{dz}\), and

$$
dH_d[i,j]
=H_d[i,j]\left[
\frac{dp_i}{2p_i}
+\frac{dp_j}{2p_j}
+d\kappa_{d,ij}
\right].
$$

The exponent differential is

$$
\begin{aligned}
d\kappa_{d,ij}
={}&-\frac12\left(
\overline z_i\,dz_i+z_i\,d\overline z_i
+\overline z_j\,dz_j+z_j\,d\overline z_j
\right)\\
&+d\overline z_i\,\rho_dz_j
+\overline z_i\,\rho_d\,dz_j.
\end{aligned}
$$

The coefficients of \(dz_i,d\overline z_i,dz_j,d\overline z_j\) are,
respectively,

$$
-\frac{\overline z_i}{2},\qquad
-\frac{z_i}{2}+\rho_dz_j,\qquad
-\frac{\overline z_j}{2}+\overline z_i\rho_d,\qquad
-\frac{z_j}{2}.
$$

The sector tangent is

$$
dG_s=\frac12\left[
\sum_d i^{sd}dH_d+
\left(\sum_d i^{sd}dH_d\right)^\dagger
\right].
$$

### Matrix-function tangents

The square-root tangent is the unique solution of the Sylvester equation

$$
S_s\,dS_s+dS_s\,S_s=dG_s.
$$

Because \(S_s\) is positive definite, the Sylvester operator is invertible:
in an eigenbasis of \(G_s\), its denominators are
\(\sqrt{\lambda_i}+\sqrt{\lambda_j}>0\).

The inverse tangents are

$$
dR_s=-R_s(dS_s)R_s,
\qquad
dJ_s=-J_s(dG_s)J_s.
$$

The diagonal tangents are

$$
dD=\operatorname{diag}(dz_i),
\qquad
dP=\operatorname{diag}\left(-\frac{dp_i}{4p_i^{3/2}}\right).
$$

### Product tangents

The frozen products differentiate as

$$
dB_s=dS_sDR_r+S_sdDR_r+S_sDdR_r,
$$

$$
dA_s=dG_sDJ_r+G_sdDJ_r+G_sDdJ_r,
$$

$$
dQ_s=dS_sP+S_sdP,
\qquad
dT_s=dA_sQ_r+A_sdQ_r.
$$

The expression for \(dA_s\) is equivalent to

$$
dA_s=dG_sDG_r^{-1}
+G_sdDG_r^{-1}
-A_sdG_rG_r^{-1}.
$$

The second form is useful for checking signs and the location of the
previous-sector inverse.

### Tangents of u, E, C, and w

For each state column,

$$
du_k=\sum_{s,i}\left[
\overline{dQ_s[i,k]}\,T_s[i,k]
+\overline{Q_s[i,k]}\,dT_s[i,k]
\right].
$$

Then

$$
dE_s=dT_s-dQ_s\operatorname{diag}(u)
-Q_s\operatorname{diag}(du).
$$

The C tangent is

$$
\begin{aligned}
dC=\sum_s\operatorname{Re}\operatorname{Tr}\big(&
dS_sB_sS_rB_s^\dagger
+S_sdB_sS_rB_s^\dagger\\
&+S_sB_sdS_rB_s^\dagger
+S_sB_sS_rdB_s^\dagger
\big).
\end{aligned}
$$

The w tangent is

$$
dw=\sum_{s,k}\left[
4\,dp_k\|E_s[:,k]\|_2^2
+8p_k\operatorname{Re}\left(
E_s[:,k]^\dagger dE_s[:,k]\right)
\right].
$$

These equations are the exact forward differential of the frozen C/w
representation. They are not an approximation and do not require
differentiating eigenvectors.

### Required three-way test

For a physical scalar parameter \(\theta\), use the same direction \(d\) in
all three calculations:

$$
\frac{dC}{d\theta}\approx
\frac{C(\theta+h)-C(\theta-h)}{2h},
\qquad
\frac{dw}{d\theta}\approx
\frac{w(\theta+h)-w(\theta-h)}{2h}.
$$

Use a bounded \(h\) sweep such as
\(10^{-3},3\cdot10^{-4},10^{-4},3\cdot10^{-5},10^{-5}\). The selected
finite-difference result must be on a plateau, and the AP precision must be
increased if the plateau moves with precision. For non-near-zero
directions, retain the existing exploratory relative target \(10^{-6}\);
for near-zero directions report an absolute error with a stated scale.

The order of interpretation is:

| Observation | Interpretation |
|---|---|
| Tangent matches AP finite difference; reverse fails | Strong evidence for a reverse/adjoint or gradient-assembly bug |
| Tangent and reverse both match finite difference | Derivative path is algebraically and numerically supported at that point |
| Tangent fails at low precision but converges with precision | Representation is numerically ill-conditioned, not necessarily algebraically wrong |
| Tangent fails after a precision plateau while forward values agree | Differential formula, parameter path, or matrix solve orientation is wrong |
| No precision resolves the AP reference | Backend/algorithm is insufficient for the requested exact validation |

## 5. Reverse-mode audit

Use the real Frobenius pairing

$$
dL=\operatorname{Re}\operatorname{Tr}(\overline X^\dagger dX).
$$

### Primitive adjoints

For \(Y=AXB\),

$$
\overline X=A^\dagger\overline YB^\dagger,
\qquad
\overline A=\overline YB^\dagger X^\dagger,
\qquad
\overline B=X^\dagger A^\dagger\overline Y.
$$

For the two different transpose operations,

$$
Y=X^\dagger\quad\Longrightarrow\quad \overline X=\overline Y^\dagger,
$$

whereas

$$
Y=X^T\quad\Longrightarrow\quad \overline X=\overline Y^T.
$$

The second rule is ordinary transpose, not Hermitian transpose. This is the
most important complex-convention warning for the AP solve construction.
The corrected worker uses x2.T because its multi-right-hand-side solve
produces a transposed representation of the desired matrix. Changing it to
x2.H would conjugate the mathematical object and would not repair the
conditioning problem.

For \(Y=X^{-1}\),

$$
\overline X=-X^{-\dagger}\overline YX^{-\dagger}.
$$

For Hermitian projection
\(\mathcal H(X)=(X+X^\dagger)/2\),

$$
\overline X=\mathcal H(\overline Y).
$$

The symmetrization is not optional when the primal input is constrained to
the Hermitian subspace.

### Square-root adjoint

The primal equation is

$$
S\,dS+dS\,S=dG.
$$

Let the accumulated upstream at S, including all direct S uses, be
\(\overline S\). First pass the inverse relation \(R=S^{-1}\):

$$
\overline S\leftarrow
\overline S-R^\dagger\overline R R^\dagger.
$$

The Sylvester operator

$$
\mathcal L_S(X)=SX+XS
$$

is self-adjoint under the real Frobenius pairing when \(S=S^\dagger\).
Therefore \(\overline G\) is obtained by solving

$$
S\overline G+\overline G S
=\mathcal H(\overline S).
$$

If \(G=U\operatorname{diag}(\lambda_i)U^\dagger\), then

$$
\overline G
=U\left[
\frac{(U^\dagger\mathcal H(\overline S)U)_{ij}}
{\sqrt{\lambda_i}+\sqrt{\lambda_j}}
\right]_{ij}U^\dagger.
$$

There is no extra factor of two. The factor one half belongs to the
Hermitian projection of the raw sector, not to the Sylvester adjoint.

### Reverse of C

For

$$
Y_s=S_sB_sS_rB_s^\dagger
$$

and scalar upstream \(g_C\), initialize
\(\overline Y_s=g_CI\). Reverse the product in the order

$$
Y_3=Y_2B_s^\dagger,\quad
Y_2=Y_1S_r,\quad
Y_1=S_sB_s.
$$

The accumulated rules are

$$
\begin{aligned}
\overline Y_2&\mathrel{+}=\overline Y_3B_s,
&
\overline B_s&\mathrel{+}=\overline Y_3^\dagger Y_2,\\
\overline Y_1&\mathrel{+}=\overline Y_2S_r^\dagger,
&
\overline S_r&\mathrel{+}=Y_1^\dagger\overline Y_2,\\
\overline S_s&\mathrel{+}=\overline Y_1B_s^\dagger,
&
\overline B_s&\mathrel{+}=S_s^\dagger\overline Y_1.
\end{aligned}
$$

For \(B_s=S_sDR_r\),

$$
\begin{aligned}
\overline S_s&\mathrel{+}=\overline B_s(DR_r)^\dagger,\\
\overline D&\mathrel{+}=S_s^\dagger\overline B_sR_r^\dagger,\\
\overline R_r&\mathrel{+}=(S_sD)^\dagger\overline B_s.
\end{aligned}
$$

### Reverse of w

Let \(P_4=\operatorname{diag}(4p)\). For
\(w=\sum_s\|E_sP_4^{1/2}\|_F^2\), the residual upstream is

$$
\overline E_s=2g_wE_sP_4.
$$

For \(E_s=T_s-Q_s\operatorname{diag}(u)\),

$$
\overline T_s\mathrel{+}=\overline E_s,
\qquad
\overline Q_s\mathrel{-}=\overline E_s\operatorname{diag}(u)^\dagger,
\qquad
\overline u\mathrel{-}=\operatorname{diag}(Q_s^\dagger\overline E_s).
$$

For
\(u_k=\sum_{s,i}\overline{Q_s[i,k]}T_s[i,k]\),

$$
\overline Q_s[:,k]\mathrel{+}=T_s[:,k]\overline{\overline u_k},
\qquad
\overline T_s[:,k]\mathrel{+}=Q_s[:,k]\overline u_k.
$$

The remaining product and inverse rules are

$$
\begin{aligned}
\overline A_s&\mathrel{+}=\overline T_sQ_r^\dagger,
&
\overline Q_r&\mathrel{+}=A_s^\dagger\overline T_s,\\
\overline S_s&\mathrel{+}=\overline Q_sP^\dagger,
&
\overline P&\mathrel{+}=S_s^\dagger\overline Q_s,\\
\overline G_s&\mathrel{+}=\overline A_s(DJ_r)^\dagger,
&
\overline D&\mathrel{+}=G_s^\dagger\overline A_sJ_r^\dagger,\\
\overline J_r&\mathrel{+}=(G_sD)^\dagger\overline A_s,
&
\overline G_r&\mathrel{-}=J_r^\dagger\overline J_rJ_r^\dagger.
\end{aligned}
$$

The explicit p contribution from \(4p_k\) is

$$
\frac{\partial L}{\partial p_k}\mathrel{+}=
4g_w\sum_s\|E_s[:,k]\|^2,
$$

and the P contribution uses

$$
\frac{d}{dp_k}\frac{1}{2\sqrt{p_k}}
=-\frac{1}{4p_k^{3/2}}.
$$

### Reverse of the raw C4 sector construction

Let \(\overline G_s\) be the symmetrized upstream after all source-moment
uses. The sector DFT sends it to the raw block as

$$
\overline H_d=\sum_s\overline{i^{sd}}\,\mathcal H(\overline G_s).
$$

Let \(g_{d,ij}\) denote the scalar entry of the raw-block adjoint
\(\overline H_d\). For one raw entry define

$$
q_{d,ij}=\overline{g_{d,ij}}\,H_d[i,j].
$$

With

$$
a=-\frac{\overline z_i}{2},\quad
b=-\frac{z_i}{2}+\rho_dz_j,\quad
c=-\frac{\overline z_j}{2}+\overline z_i\rho_d,\quad
d=-\frac{z_j}{2},
$$

the real-pairing gradients contributed by this entry are

$$
\begin{aligned}
\overline p_i&\mathrel{+}=\operatorname{Re}\frac{q_{d,ij}}{2p_i},
&\overline p_j&\mathrel{+}=\operatorname{Re}\frac{q_{d,ij}}{2p_j},\\
\overline z_i&\mathrel{+}=\overline{q_{d,ij}a}+q_{d,ij}b,
&\overline z_j&\mathrel{+}=\overline{q_{d,ij}c}+q_{d,ij}d.
\end{aligned}
$$

For \(i=j\), the two amplitude contributions are added to the same
prototype. The loop over both \((i,j)\) and \((j,i)\) supplies the reverse
entry contributions when \(i\ne j\). This explicitly distinguishes
\(dz\) from \(d\overline z\); replacing the conjugates by Hermitian matrix
operations without this scalar derivation changes the complex gradient.

Finally, symmetrize each accumulated \(\overline G_s\), apply the
Sylvester adjoint, and reverse the sector DFT. The raw-block probability
and complex-amplitude rules must use the real pairing above; a complex
gradient should not be compared to a real finite difference without
explicitly enforcing \(d\overline z=\overline{dz}\).

### Audit of the current prototype

Source inspection shows that the prototype:

- uses the corrected \(A_s=G_sDG_r^{-1}\) forward expression;
- uses the corrected residual form of w;
- applies the inverse and Sylvester adjoints in the expected order;
- symmetrizes the square-root upstream;
- uses ordinary transpose only in the corrected worker, not as an
  accidentally conjugated VJP primitive;
- passes the cheap real/imaginary convention checks.

That is positive evidence, not a target validation. The target failure can
still arise from a subtle raw-sector conjugation error, a solve-orientation
error, loss of Hermiticity at insufficient precision, or an upstream term
that is algebraically correct but numerically destroyed. The forward tangent
is the shortest way to distinguish those cases.

## 6. Conditioning at the target spectrum

### Frechet formula

For a Hermitian positive matrix
\(G=U\operatorname{diag}(\lambda_i)U^\dagger\), the Frechet derivative of a
spectral function is

$$
L_f(G,E)
=U\left(F\circ(U^\dagger EU)\right)U^\dagger,
$$

where

$$
F_{ij}=
\begin{cases}
\dfrac{f(\lambda_i)-f(\lambda_j)}{\lambda_i-\lambda_j},
&\lambda_i\ne\lambda_j,\\[1.2ex]
f'(\lambda_i),&\lambda_i=\lambda_j.
\end{cases}
$$

This is standard matrix-function theory; see Higham's treatment of
Frechet derivatives and matrix-function conditioning
[11](https://doi.org/10.1137/1.9780898717778),
[12](https://doi.org/10.1137/130945259).

For \(f(x)=\sqrt{x}\), the diagonal coefficient is
\(1/(2\sqrt{\lambda})\). For \(f(x)=x^{-1/2}\), it is
\(-1/(2\lambda^{3/2})\). The square-root Frechet derivative can equivalently
be computed by a Sylvester equation
\(S X+X S=E\), as described in the matrix-function literature
[13](https://doi.org/10.1016/j.jmaa.2018.05.005).

### Numerical scale

Using the repository's target scale
\(\lambda=3.9730108272405810054\times10^{-618}\), the scalar/eigenbasis
scales are approximately:

| Quantity | Scale |
|---|---:|
| \(\sqrt{\lambda}\) | \(1.9932412867589767\times10^{-309}\) |
| \(\lambda^{-1/2}\) | \(5.016954076974828\times10^{308}\) |
| \(\lambda^{-1}\) | \(2.516982821047435\times10^{617}\) |
| diagonal sqrt Frechet coefficient \(1/(2\sqrt{\lambda})\) | \(2.508477038487414\times10^{308}\) |
| diagonal inverse-sqrt Frechet magnitude \(1/(2\lambda^{3/2})\) | \(6.313793612864766\times10^{925}\) |
| inverse Frechet magnitude \(\lambda^{-2}\) | \(6.335202521447903\times10^{1234}\) |

The inverse-square-root value itself and the square-root derivative
coefficient exceed the largest finite binary64 magnitude
\(\left(\approx1.7977\times10^{308}\right)\). This is before considering
matrix multiplication, solve growth, or cancellation.

The relevant warning is about significant digits, not only exponent range.
Arbitrary-precision libraries can represent exponents much larger than
\(10^{308}\), but an 800-decimal-digit calculation cannot reliably subtract
terms of size \(10^{925}\) to obtain a result of size \(10^{-3}\). Such a
subtraction would require at least roughly 929 significant decimal digits
before guard digits. If terms of size \(10^{1234}\) participate, the
corresponding lower bound is roughly 1238 digits before guard digits.

This makes 800 digits plausibly insufficient for a reverse chain that
actually exposes the worst inverse-spectrum derivative. It does not prove
that the current code reaches those worst terms, and it does not prove that
the target VJP failure is free of an algebraic bug. The observed
\(10^{102}\) result is not a physical derivative; its scale is compatible
with failed cancellation or unstable reverse accumulation.

The target behavior is therefore best classified as:

- **Established:** the target representation is extremely ill-conditioned;
- **Established:** the current custom target VJP is invalid;
- **Strong numerical inference:** direct reverse differentiation of explicit
  inverse-spectrum intermediates is unstable at the tested precision;
- **Unresolved:** whether a reverse algebraic bug also contributes.

## 7. Exact C4 reformulations

### Eliminating explicit inverse matrices from products

The exact products can be evaluated as right-side constrained solves:

$$
B_sS_r=S_sD,
\qquad
A_sG_r=G_sD.
$$

These equations are algebraically identical to
\(B_s=S_sDR_r\) and \(A_s=G_sDG_r^{-1}\), but they do not require storing
\(R_r\) or \(J_r\) as explicit dense matrices. Their tangents can be
computed from

$$
dB_sS_r+B_sdS_r=dS_sD+S_sdD,
$$

and

$$
dA_sG_r+A_sdG_r=dG_sD+G_sdD.
$$

Thus the recommended tangent implementation can avoid forming \(dR\) and
\(dJ\) altogether. This is an exact reformulation. It does not make the
linear systems well-conditioned automatically; it makes the cancellation
visible at solve residuals and avoids multiplying several explicit inverse
matrices.

The C term has the exact reordered form

$$
C_s=\operatorname{Re}\operatorname{Tr}
\left(G_sD R_rD^\dagger S_s\right),
$$

obtained by substituting \(B_s=S_sDR_r\), using
\(S_s^2=G_s\), \(R_rS_r=I\), and cyclicity of trace. It has one fewer
explicit inverse-square-root factor, but it still needs an action of
\(R_r\) or an equivalent solve. It is useful as a cross-check, not a proof
of a root-free formula.

For w, the direct residual expression

$$
w=\sum_{s,k}4p_k\|T_s[:,k]-Q_s[:,k]u_k\|^2
$$

is preferable to evaluating a large norm minus a large projection term.
The repository fast path already computes the residual and uses the
subtraction identity as a diagnostic. The residual should remain the
primary quantity in any high-precision implementation.

### Nonorthogonal-basis and QR/Cholesky options

Working directly with the weighted coherent-state matrix, a Cholesky,
QR, or generalized-eigen representation can avoid explicitly constructing
\(G^{-1/2}\). This is a numerical representation choice, not a change to
the exact source moment. It can reduce memory traffic and improve residual
monitoring.

It cannot remove the underlying near-dependence of the 256 coherent
states. A factorization must still resolve pivots/eigenvalues at the
\(10^{-618}\) scale if the exact full-support inverse on the support is
needed. A binary64 Cholesky that silently treats a tiny pivot as zero would
be support truncation by another name.

A Cholesky-based matrix-function action is especially attractive for
compiled multiprecision, but it must be compared against the spectral
oracle and accompanied by solve residuals, positive-pivot certificates, and
precision escalation. Higham notes that suitable reformulations can avoid
unnecessary explicit square-root/inverse-square-root constructions and
that factorization-based reductions are useful for positive matrices
[11]. The same source cautions that the representation still has to respect
the problem's conditioning.

### Additional C4 simplification

For generic adaptive \(p,z\) subject only to C4 orbit symmetry, the four
64-by-64 sectors are generally different. C4 block diagonalization is
therefore the robust exact reduction already available.

Further sector equality would require additional invariance, such as a
reflection/D4 symmetry or a separable PMF/geometry that is preserved by the
adaptive parameterization. Generic GS real and imaginary directions need not
preserve those symmetries. Assuming equal sectors would silently remove
allowed adaptive directions and change the target.

A tensor/Kronecker reduction is likewise special-case only. The square QAM
grid may suggest tensor structure, but arbitrary learned PMFs and
geometry-normalization maps need not factor into independent quadratures.
No general root-free closed form for both C and w follows from C4 alone.

### Matrix-function actions

Matrix-function actions, constrained solves, and a stacked residual
projection are exact ways to organize the calculation. They are not
conditioning cures. The problem is not that the exact C/w values are
undefined; it is that a nonorthogonal coherent-state representation contains
modes that are almost linearly dependent. Any exact orthogonalizing map must
pay for that information somewhere, either through tiny factorization pivots
or large inverse-like coefficients.

## 8. Literature and implementation survey

| Work or route | Numerical object | Relevance to this blocker | What it does not establish |
|---|---|---|---|
| Denys et al. 2021 | Analytical C/w-style bound for discrete modulation; QAM examples through 1024 states | Confirms the source-moment security objects and shows large QAM is a meaningful use case [1] | No target-scale differentiable VJP or conditioning study |
| Ghorai et al. 2019 | Numerical SDP for discrete modulation | Established DM-CV-QKD security numerics for smaller modulation families [2] | Not the frozen full-support C4 C/w route |
| Lin et al. 2019 | Numerical SDP for quaternary modulation | Useful comparison for finite-dimensional security numerics [3] | No 256-state full-support source-moment gradient |
| Kaur et al. 2021 | Gauss-Hermite/continuity argument | Shows a different way to connect discrete modulation to Gaussian security [4] | Not an exact differentiable C4 implementation |
| Upadhyaya et al. 2021 | Finite-dimensional reduction with analytical correction | Shows that finite-dimensional reductions can be security-relevant [5] | Does not solve this source VJP |
| Kanitschar et al. 2023 | Finite-size proof and numerical examples | Relevant finite-size methodology [6] | Not a full-support 256-state differentiable source calculation |
| Bäuml et al. 2024 | Finite-size coherent-attack SDP for four states | Illustrates cutoff-based numerical security analysis [7] | Cutoff/SDP numerics do not validate the current exact C4 gradient |
| Li et al. 2026 | Free-space DM-CV-QKD with numerical SDP | Relevant application context [8] | No source-moment gradient or \(10^{-618}\) conditioning result |
| 64/256-QAM experiments | Experimental/analytical high-order modulation | Confirms practical interest in high-order QAM [9,10] | No evidence about internal Gram derivative conditioning |
| Higham matrix-function theory | Frechet derivatives and conditioning | Supplies the correct sensitivity framework [11,12] | General theory does not make this particular implementation stable |
| Arb/FLINT/MPFR | Ball or arbitrary-precision matrix arithmetic | Candidate engineering backend for guard digits and error tracking [14-17] | Backend choice alone does not prove a security or gradient result |

Arb uses ball arithmetic and can track rigorous enclosures, but its
documentation explicitly warns about dependency overestimation and the need
for guard bits and precision escalation
[14](https://arblib.org/using.html). FLINT supplies arbitrary-precision
complex matrix operations, solves, and eigen-related routines, while also
documenting that some eigen routines are experimental and may require care
[15](https://flintlib.org/doc/acb_mat.html). MPFR provides correctly rounded
arbitrary-precision floating-point arithmetic, and MPFR-based BLAS/LAPACK
implementations provide a route to compiled multiprecision linear algebra
[16](https://www.mpfr.org/),
[17](https://arxiv.org/abs/2109.13406).

The practical implication is that a compiled multiprecision backend is an
implementation enabler, not the primary mathematical fix. The equations
must first be validated by a forward tangent and local adjoint identities.

## 9. Approximation and security-error propagation

### What ordinary approximations would change

Clipping small eigenvalues, adding \(\delta I\), dropping modes, using a
thresholded pseudoinverse, or replacing \(G^{-1/2}\) by a lower-rank
orthogonalization changes the support representation. Unless accompanied by
a new security theorem, those operations are not exact evaluation of the
frozen C/w bound.

In particular, support truncation is not justified merely because its
contribution to C appears small. The w term contains an inverse-support
operator, and small Gram modes can have a disproportionately large effect
on intermediate or derivative quantities.

### A rigorous error budget, if approximation is later considered

Suppose a future certified method returns

$$
|C-\widehat C|\le\delta_C,\qquad
0\le w\le \widehat w+\delta_w.
$$

Then a conservative source interval containing the exact \(Z_-\) and \(Z_+\)
is

$$
\begin{aligned}
Z_{\mathrm{src},L}
&=2\sqrt{T}(\widehat C-\delta_C)
-\sqrt{2T\epsilon(\widehat w+\delta_w)},\\
Z_{\mathrm{src},U}
&=2\sqrt{T}(\widehat C+\delta_C)
+\sqrt{2T\epsilon(\widehat w+\delta_w)}.
\end{aligned}
$$

The physical covariance interval must then be intersected with this
expanded source interval, and the Holevo maximum must be recomputed over
that conservative interval. If a tighter lower w enclosure is certified,
the \(Z_+\) lower endpoint can be sharpened, but no monotonicity shortcut
should be assumed without proving it for the active Holevo branch.

If \(w\) is close to zero, the square-root dependence makes a derivative
bound singular unless the error is handled as an interval rather than by
linearization. The current reference w is approximately \(0.0183\), but
adaptive geometry could move closer to zero.

An AP-calibrated differentiable approximation can be acceptable as a
training heuristic only if final candidate evaluation is exact or
conservatively certified. It cannot be advertised as an exact security
gradient merely because it is calibrated at a few AP points.

### Full-Z nonsmoothness

Even after C/w gradients are correct, the statewise objective includes a
maximum of \(\chi_{BE}(Z)\) over an interval. The selected maximizer gives a
local derivative only when the active branch is isolated. A branch switch
can make the objective nonsmooth. The one-state test must record \(Z_\star\),
the competing-candidate gap, and the branch under both finite-difference
signs. Source-moment differentiability does not imply global differentiability
of the full \(K_n\).

## 10. Ranked options

The ranking separates mathematical fidelity from runtime. Runtime entries
are expectations from the current measurements, not benchmark results for a
new backend.

| Rank | Option | Exact C/w fidelity | Security defensibility | Engineering cost | Expected runtime | Decision |
|---:|---|---|---|---|---|---|
| 1 | Exact C4 operator/tangent reformulation plus compiled multiprecision | Exact in arithmetic; certified only after precision/error checks | Highest; preserves M=256, C, w, and full-Z | High | Current Python is minutes for forward and hours for reverse; compiled target is unknown and must be benchmarked | Primary path |
| 2 | Corrected AP forward plus repaired implicit adjoint | Exact in arithmetic | High if all target directions pass | Medium to high | Current AP reverse already measured at about 7.1 hours per direction | Diagnostic only; do not train |
| 3 | Implicit differentiation of solve/Sylvester constraints | Exact derivative of the chosen representation | High when paired with an exact stable forward | Medium | Potentially lower memory and fewer catastrophic products; speed unmeasured | Use inside option 1 |
| 4 | Nonorthogonal-basis, QR, Cholesky, or generalized-eigen representation | Algebraically exact if full support is retained | High if tiny pivots are resolved and residuals certified | Medium to high | Could reduce overhead; conditioning may remain comparable | Use as implementation variant, not standalone cure |
| 5 | AP-calibrated fast differentiable approximation | Not exact | Conditional; final exact/certified evaluation required | Medium | Likely seconds to minutes, but no security-gradient claim without bounds | Fallback study only |
| 6 | Rigorous spectral truncation with a new conservative theorem | Not the frozen exact C/w functional | Potentially defensible only after a new proof and adjusted bound | Very high | Potentially fast | Out of current scope |
| 7 | Gradient-free optimization with exact forward evaluations | No gradient needed; exact objective evaluations remain possible | High for each evaluated candidate | Medium | At roughly 5-7 minutes per source evaluation, hundreds or thousands of evaluations imply days to weeks | Last-resort research fallback |
| 8 | Current custom AP reverse as-is | Intended exact formula, but target-invalid | None for training because it is unvalidated | Already implemented | About 7.1 hours per direction | Reject |

The options are not independent. The stable route combines ranks 1, 3, and
4: use C4, formulate B/A as constrained solves, differentiate those
constraints implicitly, and run the result in a compiled multiprecision
backend. Rank 2 remains the simplest diagnostic oracle before that
engineering investment.

## 11. Primary recommendation

### Recommended algorithm

Implement one isolated exact C4 tangent boundary in this order:

1. Form \(H_d\), \(G_s\), and support diagnostics at arbitrary precision.
2. Compute \(S_s=G_s^{1/2}\) with a full-support matrix-function method and
   retain positive-pivot/eigenvalue evidence.
3. Compute B and A from the exact right-side constraints
   \(B_sS_r=S_sD\) and \(A_sG_r=G_sD\), using solves rather than explicit
   \(R_r\) and \(J_r\).
4. Compute \(Q_s=S_sP\), \(T_s=A_sQ_r\), \(u\), and the direct residual
   \(E_s\). Evaluate w from the residual norm.
5. Compute \(dG_s\), solve the square-root Sylvester equation for \(dS_s\),
   and differentiate the B/A constraints:

   $$
   dB_sS_r=dS_sD+S_sdD-B_sdS_r,
   $$

   $$
   dA_sG_r=dG_sD+G_sdD-A_sdG_r.
   $$

6. Propagate \(dQ,dT,du,dE,dC,dw\) using the equations in Section 4.
7. Only after the tangent passes, derive the reverse from the same
   constrained equations or repair the current reverse code. Do not
   duplicate inverse matrices in the tangent and reverse implementations.
8. Move the validated path to compiled MPFR/Arb/FLINT-style arithmetic, with
   precision escalation until interval or high-precision differences stabilize.

This is still the exact C/w functional. The constrained equations are just
the identities obtained by multiplying the frozen definitions on the right.

### Validation and falsification

The route is falsified, or the task is blocked, by any of the following:

- a small fixture violates the direct-versus-constrained solve identity;
- \(dC,dw\) from the tangent fail an AP finite-difference plateau after
  precision is increased and all support checks pass;
- the tangent passes but local adjoint identities fail;
- the target AP reference cannot resolve 256/256 positive modes at the
  precision ladder;
- ball enclosures remain wider than the required derivative tolerance;
- a target direction changes rank or loses positive probabilities;
- all derivative checks pass but one gradient remains too slow for the
  planned adaptive workload.

The minimum test matrix is:

| Stage | Required check |
|---|---|
| Algebra | Direct explicit R/J products equal constrained-solve products on small positive fixtures |
| Tangent | AP finite difference, forward tangent, and direct component checks for C and w |
| Conditioning | Precision ladder; minimum eigenvalue, solve residual, Sylvester residual, and cancellation diagnostics |
| Reverse primitives | Matrix-product, inverse, Hermitian projection, ordinary transpose, and Sylvester adjoint inner-product identities |
| Target source moments | PS-logit, GS-real, GS-imaginary, and \(V_A\) directions |
| Complex convention | Separate real-alpha and imaginary-alpha paths under the PyTorch real-scalar convention |
| Full-Z | Only after all source directions pass; record branch location and nonsmoothness margin |
| Lifecycle | No optimizer step, no training, no final-test access, no publication-scale run |

For a primitive \(Y=F(X)\), the local adjoint identity should be tested as

$$
\operatorname{Re}\operatorname{Tr}(\overline Y^\dagger dY)
\approx
\operatorname{Re}\operatorname{Tr}(\overline X^\dagger dX)
$$

for independent AP perturbations. This catches transpose/conjugation errors
without requiring the complete C/w graph to be stable.

### Runtime gate

The current 7.1-hour per-direction reverse is already a practical failure
for ordinary adaptive training, regardless of eventual correctness. A
reasonable proposed engineering gate for reopening a one-step adaptive
smoke is a measured, stable 256-state gradient in under roughly one minute
on the development machine, with documented batch scaling and no hidden
precision downgrade. This is a proposed practicality gate, not a security
theorem and not a replacement for the repository lifecycle gate.

If the exact tangent/reverse path passes mathematically but misses that
runtime gate, classify it as correct-but-impractical and study one
AP-calibrated differentiable strategy separately. Do not silently substitute
that strategy into the security calculation.

## 12. Final disposition

### Current classification

AP_CUSTOM_BACKWARD_NOT_VALIDATED

This is required by the bounded target failure. The small-fixture passes do
not override the target result, and GS-real, GS-imaginary, \(V_A\), and
full-Z backward validation were correctly not started after the fail-closed
stop.

### Adaptive-training readiness

NOT_READY_FOR_ADAPTIVE_TRAINING

### Security invariants preserved

- Exact \(M=256\) full support remains the target.
- The corrected C and w are retained.
- No eigenvalue clipping, jitter, epsilon identity, pseudoinverse rank
  reduction, or support truncation is proposed as a silent repair.
- The full physical \(Z\)-interval and worst-case Holevo semantics remain
  unchanged.
- No K positive-part clipping is introduced.

### One remaining blocker

The single blocker is: **a validated and computationally practical
full-support source-moment derivative at the \(10^{-618}\) Gram-eigenvalue
scale is still missing.**

### Recommended next task

Implement the isolated exact forward tangent using the C4 constrained-solve
formulation, then run the three-way PS directional diagnostic at an adaptive
precision ladder before touching the reverse VJP. Do not execute adaptive
training as part of that task.

## Sources

1. A. Denys, P. Brown, and A. Leverrier, “Explicit asymptotic secret key rate
   of continuous-variable quantum key distribution with an arbitrary
   modulation,” Quantum 5, 540 (2021), arXiv HTML:
   https://arxiv.org/html/2103.13945
2. S. Ghorai et al., “Practical security of discrete-modulation continuous-
   variable quantum key distribution,” Physical Review X 9, 021059 (2019):
   https://journals.aps.org/prx/abstract/10.1103/PhysRevX.9.021059
3. J. Lin, T. Upadhyaya, and N. Lütkenhaus, “Security analysis of practical
   discrete-modulated continuous-variable quantum key distribution,”
   Physical Review X 9, 041064 (2019):
   https://journals.aps.org/prx/abstract/10.1103/PhysRevX.9.041064
4. E. Kaur, S. Guha, and M. M. Wilde, “Asymptotic security of discrete-
   modulation protocols for continuous-variable quantum key distribution,”
   Physical Review A 103, 012412 (2021), accepted manuscript:
   https://link.aps.org/accepted/10.1103/PhysRevA.103.012412
5. T. Upadhyaya et al., finite-dimensional reduction for discrete-modulated
   CV-QKD, PRX Quantum 2, 020325 (2021):
   https://journals.aps.org/prxquantum/abstract/10.1103/PRXQuantum.2.020325
6. M. Kanitschar et al., finite-size discrete-modulation CV-QKD, PRX Quantum
   4, 040306 (2023):
   https://doi.org/10.1103/PRXQuantum.4.040306
7. S. Bäuml et al., finite-size coherent-attack security for four coherent
   states, Quantum 8, 1418 (2024):
   https://quantum-journal.org/papers/q-2024-07-18-1418/
8. Li et al., free-space discrete-modulated CV-QKD, Physical Review Applied
   25, 024013 (2026):
   https://journals.aps.org/prapplied/abstract/v7d9-ylyl
9. “High-dimensional discrete-modulated CV-QKD with 64- and 256-QAM,”
   arXiv:2203.08470:
   https://arxiv.org/abs/2203.08470
10. “Experimental demonstration of probabilistically shaped 64- and 256-QAM
    discrete-modulated CV-QKD,” arXiv:2111.12356:
    https://arxiv.org/abs/2111.12356
11. N. J. Higham, Functions of Matrices: Theory and Computation, SIAM:
    https://doi.org/10.1137/1.9780898717778
12. N. J. Higham and M. Relton, “Higher order Frechet derivatives of matrix
    functions and the level-2 condition number,” SIAM J. Matrix Anal. Appl.:
    https://doi.org/10.1137/130945259
13. P. Del Moral and A. Niclas, Frechet derivatives of matrix functions:
    https://doi.org/10.1016/j.jmaa.2018.05.005
14. Arb documentation, including ball arithmetic and precision guidance:
    https://arblib.org/using.html
15. FLINT arbitrary-precision complex matrix documentation:
    https://flintlib.org/doc/acb_mat.html
16. MPFR arbitrary-precision arithmetic:
    https://www.mpfr.org/
17. MPLAPACK/MPBLAS arbitrary-precision linear algebra:
    https://arxiv.org/abs/2109.13406
