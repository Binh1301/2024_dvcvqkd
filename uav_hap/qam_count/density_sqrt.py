import numpy as np
from math import factorial, comb, sqrt
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy.linalg import eigh

# =====================================================
# STEP 1: PARAMETERS
# =====================================================
Ncut   = 25
alpha0 = 2 * sqrt(2)   # base amplitude

# =====================================================
# STEP 2: DENSITY MATRIX rho (25x25)
# rho = sum_{k,l} p_{k,l} |alpha_{k,l}><alpha_{k,l}|
# =====================================================
print("=" * 55)
print("256-QAM Binomial — rho and rho^(1/2)")
print("=" * 55)
print(f"Ncut   = {Ncut}")
print(f"alpha0 = 2*sqrt(2) = {alpha0:.6f}")
print()
print("Step 1: Computing density matrix rho (25x25)...")

rho = np.zeros((Ncut, Ncut), dtype=complex)

for k in range(16):
    for l in range(16):
        # Complex amplitude of symbol (k, l)
        # alpha_{k,l} = alpha0/sqrt(30) * [(k-7.5) + i*(l-7.5)]
        alpha = alpha0 / sqrt(30) * ((k - 7.5) + 1j * (l - 7.5))

        # Binomial probability
        p = comb(15, k) * comb(15, l) / 2**30

        # Coherent state |alpha> in Fock basis
        # <n|alpha> = exp(-|alpha|^2/2) * alpha^n / sqrt(n!)
        v = np.zeros(Ncut, dtype=complex)
        for n in range(Ncut):
            v[n] = np.exp(-abs(alpha)**2 / 2) * (alpha**n) / sqrt(factorial(n))

        # Accumulate: rho += p * |alpha><alpha|
        rho += p * np.outer(v, np.conj(v))

rho_real = np.real(rho)
tr_rho   = np.trace(rho).real
print(f"  Tr(rho)         = {tr_rho:.15f}")
print(f"  rho Hermitian?    max|rho - rho†| = {np.max(np.abs(rho - rho.conj().T)):.2e}")

# =====================================================
# STEP 3: EIGENDECOMPOSITION
# rho = V D V†
# D   = diag(lambda_0, ..., lambda_{N-1})
# =====================================================
print()
print("Step 2: Eigendecomposition  rho = V D V†...")

eigvals, V = eigh(rho)          # eigh: for Hermitian matrix, eigvals real & sorted ascending
eigvals    = np.maximum(eigvals, 0.0)   # clip tiny negatives from floating point
D          = np.diag(eigvals)

print(f"  Eigenvalues (all {Ncut}):")
for i, ev in enumerate(eigvals):
    if ev > 1e-10:
        print(f"    lambda[{i:2d}] = {ev:.12f}")
print(f"  Sum of eigenvalues = {eigvals.sum():.15f}")

# =====================================================
# STEP 4: sqrt(D)
# sqrt_D = diag(sqrt(lambda_0), ..., sqrt(lambda_{N-1}))
# =====================================================
print()
print("Step 3: Computing sqrt(D)...")

sqrt_eigvals = np.sqrt(eigvals)
sqrt_D       = np.diag(sqrt_eigvals)

print(f"  sqrt(lambda) values (nonzero):")
for i, sv in enumerate(sqrt_eigvals):
    if sv > 1e-5:
        print(f"    sqrt(lambda[{i:2d}]) = {sv:.12f}")

# =====================================================
# STEP 5: rho^{1/2} = V sqrt(D) V†
# =====================================================
print()
print("Step 4: Computing rho^(1/2) = V sqrt(D) V†...")

rho_sqrt      = (V * sqrt_eigvals[None, :]) @ V.conj().T
rho_sqrt_real = np.real(rho_sqrt)

# Verification
err_sq  = np.max(np.abs(rho_sqrt @ rho_sqrt - rho))
tr_sqrt = np.real(np.trace(rho_sqrt))
print(f"  Verify rho^½ @ rho^½ = rho:  max error = {err_sq:.2e}")
print(f"  Tr(rho^½) = sum(sqrt(lambda)) = {tr_sqrt:.12f}")
print(f"  rho^½ Hermitian? max|rho^½ - (rho^½)†| = {np.max(np.abs(rho_sqrt - rho_sqrt.conj().T)):.2e}")

# =====================================================
# STEP 6: ANNIHILATION OPERATOR a (for reference)
# a[j-1, j] = sqrt(j),  i.e. <j-1|a|j> = sqrt(j)
# =====================================================
a_op  = np.zeros((Ncut, Ncut), dtype=complex)
for j in range(1, Ncut):
    a_op[j-1, j] = sqrt(j)
adag = a_op.conj().T

VA     = np.real(np.trace(rho @ adag @ a_op))
Tr_C   = np.real(np.trace(rho_sqrt @ a_op @ rho_sqrt @ adag))
print()
print("Step 5: Key quantities for Z*")
print(f"  V_A = Tr(rho a†a)                  = {VA:.12f}")
print(f"  Tr(rho^½ a rho^½ a†)               = {Tr_C:.12f}")
print(f"  Ratio Tr_C / V_A                   = {Tr_C/VA:.8f}")

# =====================================================
# STEP 7: VISUALIZATION
# 4-panel figure:
#   [0,0] rho heatmap        [0,1] rho^½ heatmap
#   [1,0] eigenvalues bar    [1,1] sqrt eigenvalues bar
# =====================================================
print()
print("Step 6: Rendering visualization...")

fig = plt.figure(figsize=(36, 32))
fig.patch.set_facecolor('#F8F7F4')

gs = gridspec.GridSpec(
    2, 2, figure=fig,
    hspace=0.35, wspace=0.25,
    left=0.06, right=0.97,
    top=0.93,  bottom=0.06
)

# ── helper: annotated heatmap ────────────────────────
def draw_heatmap(ax, data, title, cmap, annot_size=6.0):
    vmax = np.max(np.abs(data))
    sns.heatmap(
        data,
        ax=ax,
        annot=True,
        fmt=".4f",
        cmap=cmap,
        vmin=0.0,
        vmax=vmax,
        cbar=True,
        square=True,
        linewidths=0.4,
        linecolor='#CCCCCC',
        annot_kws={"size": annot_size, "color": "black"},
        cbar_kws={"shrink": 0.75, "pad": 0.02}
    )
    ax.set_title(title, fontsize=17, fontweight='bold', pad=12, color='#1a1a1a')
    ax.set_xlabel("Fock state $|n\\rangle$", fontsize=12, labelpad=8)
    ax.set_ylabel("Fock state $\\langle m|$", fontsize=12, labelpad=8)
    ax.tick_params(axis='both', labelsize=9)
    ticks = list(range(0, Ncut, 2))
    ax.set_xticks([t + 0.5 for t in ticks])
    ax.set_xticklabels(ticks)
    ax.set_yticks([t + 0.5 for t in ticks])
    ax.set_yticklabels(ticks)

# ── [0,0] rho ────────────────────────────────────────
ax0 = fig.add_subplot(gs[0, 0])
draw_heatmap(
    ax0, rho_real,
    r"Density Matrix $\rho$ — Real Part   ($N_{\rm cut}=25$)",
    cmap='Blues'
)

# ── [0,1] rho^{1/2} ──────────────────────────────────
ax1 = fig.add_subplot(gs[0, 1])
draw_heatmap(
    ax1, rho_sqrt_real,
    r"$\rho^{1/2} = V\sqrt{D}\,V^\dagger$ — Real Part   ($N_{\rm cut}=25$)",
    cmap='Greens'
)

# ── [1,0] eigenvalues of rho ─────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
ax2.set_facecolor('#F0F4FA')
idx  = np.arange(Ncut)
bars = ax2.bar(idx, eigvals, color='#3B7DC8', edgecolor='white',
               linewidth=0.6, width=0.75, zorder=3)

for b, v in zip(bars, eigvals):
    if v > 1e-5:
        ax2.text(
            b.get_x() + b.get_width() / 2, v + 0.003,
            f"{v:.5f}", ha='center', va='bottom',
            fontsize=6.0, color='#1a3a6b', rotation=90
        )

ax2.set_xlabel("Eigenvalue index $i$", fontsize=12, labelpad=8)
ax2.set_ylabel("$\\lambda_i$", fontsize=13)
ax2.set_title(r"Eigenvalues $\lambda_i$ of $\rho$",
              fontsize=17, fontweight='bold', pad=12, color='#1a1a1a')
ax2.set_xticks(idx[::2])
ax2.set_xticklabels(idx[::2], fontsize=9)
ax2.tick_params(axis='y', labelsize=9)
ax2.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
ax2.set_xlim(-0.5, Ncut - 0.5)
ax2.text(
    0.03, 0.97,
    f"$\\sum\\lambda_i = {eigvals.sum():.10f}$\n"
    f"$\\mathrm{{Tr}}(\\rho) = {tr_rho:.10f}$",
    transform=ax2.transAxes, ha='left', va='top', fontsize=10,
    bbox=dict(fc='white', ec='#3B7DC8', lw=1, pad=5)
)

# ── [1,1] sqrt eigenvalues ────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
ax3.set_facecolor('#F0FAF0')
bars2 = ax3.bar(idx, sqrt_eigvals, color='#2E8B57', edgecolor='white',
                linewidth=0.6, width=0.75, zorder=3)

for b, v in zip(bars2, sqrt_eigvals):
    if v > 1e-3:
        ax3.text(
            b.get_x() + b.get_width() / 2, v + 0.003,
            f"{v:.5f}", ha='center', va='bottom',
            fontsize=6.0, color='#1a5e2e', rotation=90
        )

ax3.set_xlabel("Eigenvalue index $i$", fontsize=12, labelpad=8)
ax3.set_ylabel("$\\sqrt{\\lambda_i}$", fontsize=13)
ax3.set_title(r"$\sqrt{\lambda_i}$ — Eigenvalues of $\rho^{1/2}$",
              fontsize=17, fontweight='bold', pad=12, color='#1a1a1a')
ax3.set_xticks(idx[::2])
ax3.set_xticklabels(idx[::2], fontsize=9)
ax3.tick_params(axis='y', labelsize=9)
ax3.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
ax3.set_xlim(-0.5, Ncut - 0.5)
ax3.text(
    0.03, 0.97,
    f"$\\mathrm{{Tr}}(\\rho^{{1/2}}) = \\sum\\sqrt{{\\lambda_i}} = {tr_sqrt:.8f}$",
    transform=ax3.transAxes, ha='left', va='top', fontsize=10,
    bbox=dict(fc='white', ec='#2E8B57', lw=1, pad=5)
)

# ── super title ───────────────────────────────────────
fig.suptitle(
    "256-QAM Binomial  |  Density Matrix $\\rho$  and  $\\rho^{1/2}$\n"
    r"$\alpha_0 = 2\sqrt{2}$,   $N_{\rm cut} = 25$,   "
    r"$p_{k,l} = \binom{15}{k}\binom{15}{l}\,/\,2^{30}$",
    fontsize=20, fontweight='bold', color='#0C1F3D', y=0.976
)

out = "rho_and_sqrt_rho_qam256.png"
plt.savefig(out, dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f"  Saved: {out}")
print()
print("Done.")