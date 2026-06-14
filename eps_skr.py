"""
SKR vs excess noise (eps) sweep for CV-QKD UAV-HAP system.
Compares MB, Binomial, Uniform (QAM-256) as eps varies 0.0001 → 0.1.
Physics ported directly from skr_compare_qam256.html (document 9).

Fixed baseline:
  W0 = 11.00 cm,  a = 20.00 cm,  V = 13.00 km,  C2n = 0.50 e-15
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.special import i0, i1
from pathlib import Path

# ─── QAM precomputed states (VA = 2 SNU) ─────────────────────────────
QAM = {
    "Binomial": dict(va=1.9999999999999998, tr_c=1.414147501311065,
                     w=0.00011333140444522628),
    "Uniform":  dict(va=1.9999999999999993, tr_c=1.4019995788968003,
                     w=0.026543340397914922),
    "MB":       dict(va=1.9980490544457419, tr_c=1.4131628716573499,
                     w=3.536190741123598e-05),
}

COLORS = {"Binomial": "#1D9E75", "Uniform": "#378ADD", "MB": "#D85A30"}
STYLES = {"Binomial": "--",      "Uniform": "-",       "MB": ":"}
LW     = {"Binomial": 2.2,       "Uniform": 2.0,       "MB": 2.2}

# ─── Fixed protocol constants (except eps which is swept) ────────────
ETA     = 0.95
V_EL    = 0.001
BETA    = 0.95
L_KM    = 20.0
LAM     = 1550.0    # nm
SIG_UAV = 10.2      # cm

# ─── Fixed channel parameters ─────────────────────────────────────────
W0_FIX  = 11.00  # cm
A_FIX   = 20.00  # cm
V_FIX   = 13.00  # km
C2N_FIX = 0.50   # ×10^-15

N_MC  = 3000
N_PTS = 1000   # denser grid to resolve the zero-threshold region

# ─── Monte Carlo samples ──────────────────────────────────────────────
def _lcg_samples(n, seed=20240602):
    x = seed & 0xFFFFFFFF
    out = np.empty(n)
    for i in range(n):
        x = (1664525 * x + 1013904223) & 0xFFFFFFFF
        out[i] = (x + 0.5) / 4294967296
    return out

MC = _lcg_samples(N_MC)

# ─── Channel model ────────────────────────────────────────────────────
def kruse_q(V_km):
    if V_km > 50: return 1.6
    if V_km > 6:  return 1.3
    return 0.585 * max(V_km, 1e-9) ** (1/3)


def compute_teff(V_km, W0_cm, a_cm, C2n_15):
    W0  = W0_cm / 100
    a   = a_cm  / 100
    C2n = C2n_15 * 1e-15
    sg  = SIG_UAV / 100
    lam = LAM * 1e-9
    L   = L_KM * 1000

    q       = kruse_q(V_km)
    xi      = (3.912 / V_km) * (LAM / 550) ** (-q)
    eta_atm = np.exp(-xi * L_KM)

    zR  = np.pi * W0**2 / lam
    WL  = W0 * np.sqrt(1 + (L / zR)**2)

    T0sq   = max(0.0, 1 - np.exp(-2 * a**2 / WL**2))
    x      = (2 * a / WL)**2
    ex     = np.exp(-x)
    I0v    = float(i0(x))
    I1v    = float(i1(x))
    denom  = max(1 - ex * I0v, 1e-15)
    ratio  = max(2 * T0sq / denom, 1 + 1e-15)
    Delta  = max(np.log(ratio), 1e-15)
    gammaR = (2 * x * ex * I1v) / max(denom * Delta, 1e-15)
    Gamma  = max(gammaR, 1e-9)
    R      = max(a / Delta ** min(1/Gamma, 1e6), 1e-15)

    sig2_turb = 1.919 * C2n * L**3 * (2 * W0) ** (-1/3)
    sig_r     = np.sqrt(max(sig2_turb + sg**2, 0))
    sig_s     = sig_r / np.sqrt(2)

    u   = np.clip(MC, 1e-15, 1 - 1e-15)
    r   = sig_s * np.sqrt(-2 * np.log(u)) if sig_s > 0 else np.zeros(N_MC)
    ET2 = np.mean(T0sq * np.exp(-(r / R) ** Gamma))
    return eta_atm * ET2


# ─── SKR physics ─────────────────────────────────────────────────────
def _g(x):
    if x <= 1e-15: return 0.0
    return (x + 1) * np.log2(x + 1) - x * np.log2(x)


def compute_skr(T_eff, state, eps):
    """Compute SKR given T_eff, QAM state, and excess noise eps."""
    if T_eff < 1e-10:
        return 0.0, 0.0, 0.0

    VA, tr_c, w = state["va"], state["tr_c"], state["w"]

    # noise model — eps is now variable
    chi_line = (1 - T_eff) / T_eff + eps
    chi_det  = (1 - ETA + V_EL) / ETA
    chi_tot  = chi_line + chi_det / T_eff

    # Z* — eps enters both the noise penalty and the signal term
    zstar = 2 * np.sqrt(T_eff) * tr_c - np.sqrt(2 * T_eff * eps * w)
    a_cv  = VA + 1
    b_cv  = 1 + T_eff * VA + T_eff * eps
    zmax  = np.sqrt(a_cv * b_cv)
    if zstar >= zmax or (a_cv * b_cv - zstar**2) <= 0:
        zstar = min(zstar, zmax * (1 - 1e-9))

    # symplectic eigenvalues
    a, b, c = VA + 1, 1 + T_eff * VA + T_eff * eps, zstar
    Dv   = a**2 + b**2 - 2*c**2
    B    = (a*b - c**2)**2
    disc = max(Dv**2 - 4*B, 0)
    sd   = np.sqrt(disc)
    l1   = np.sqrt(max(0.5*(Dv + sd), 0))
    l2   = np.sqrt(max(0.5*(Dv - sd), 0))
    l3   = max(a - c**2 / (2 + T_eff*VA + T_eff*eps), 1e-15)

    chi_BE = _g((l1-1)/2) + _g((l2-1)/2) - _g((l3-1)/2)
    I_AB   = np.log2(1 + T_eff * VA / (2 + T_eff * chi_tot))
    skr    = max(BETA * I_AB - chi_BE, 0.0)
    return skr, I_AB, chi_BE


# ─── Compute T_eff once (channel does not depend on eps) ─────────────
print("Computing T_eff at fixed channel parameters …")
T_EFF = compute_teff(V_FIX, W0_FIX, A_FIX, C2N_FIX)
print(f"  T_eff = {T_EFF:.6f}  ({10*np.log10(T_EFF):.2f} dB)")

# ─── Sweep excess noise ───────────────────────────────────────────────
EPS_GRID = np.logspace(np.log10(0.0001), np.log10(0.1), N_PTS)  # log scale

print("Sweeping excess noise …")
skr_arr = {name: np.empty(N_PTS) for name in QAM}
skr_log = {name: np.empty(N_PTS) for name in QAM}
iab_arr = {name: np.empty(N_PTS) for name in QAM}
chi_arr = {name: np.empty(N_PTS) for name in QAM}

for i, eps in enumerate(EPS_GRID):
    for name, state in QAM.items():
        skr, iab, chi = compute_skr(T_EFF, state, eps)
        skr_arr[name][i] = skr
        skr_log[name][i] = np.log10(max(skr, 1e-9))
        iab_arr[name][i] = iab
        chi_arr[name][i] = chi

print("  done")

def _last_positive_eps(eps_grid, skr_values):
    idx = np.where(skr_values > 0)[0]
    if len(idx) == 0:
        return None
    return float(eps_grid[idx[-1]])

print("\n── Approx. zero-SKR thresholds ───────────────────────────────")
for name in ["MB", "Binomial", "Uniform"]:
    thr = _last_positive_eps(EPS_GRID, skr_arr[name])
    if thr is None:
        print(f"{name:10s}: not positive in sampled range")
    else:
        print(f"{name:10s}: {thr:.6g}")

# ─── Plot: 3-panel figure ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# ── Panel 1: log10(SKR) vs eps ────────────────────────────────────────
ax = axes[0]
for name in ["MB", "Binomial", "Uniform"]:
    ax.semilogx(EPS_GRID, skr_log[name],
                color=COLORS[name], linestyle=STYLES[name],
                linewidth=LW[name], label=name)
ax.axhline(0,  color="black", linewidth=0.7, alpha=0.35)
ax.axhline(-3, color="gray",  linewidth=0.7, alpha=0.45, linestyle="--")
ax.set_xlabel(r"Excess noise $\varepsilon$  (SNU)", fontsize=11)
ax.set_ylabel(r"$\log_{10}(\mathrm{SKR})$  (bits/pulse)", fontsize=10)
ax.set_title("(a)  SKR vs Excess Noise", fontsize=11)
ax.set_ylim(-9, 0.75)
ax.legend(fontsize=10, framealpha=0.85)

# ── Panel 2: I_AB and chi_BE vs eps ──────────────────────────────────
ax = axes[1]
for name in ["MB", "Binomial", "Uniform"]:
    ax.semilogx(EPS_GRID, iab_arr[name],
                color=COLORS[name], linestyle=STYLES[name],
                linewidth=LW[name], label=f"$I_{{AB}}$ {name}")
    ax.semilogx(EPS_GRID, chi_arr[name],
                color=COLORS[name], linestyle=STYLES[name],
                linewidth=1.0, alpha=0.45,
                label=f"$\\chi_{{BE}}$ {name}")

# annotate which is which
ax.text(0.97, 0.75, "$I_{AB}$ (upper curves)",
        transform=ax.transAxes, ha="right", fontsize=8, color="black")
ax.text(0.97, 0.55, "$\\chi_{BE}$ (lower / faded)",
        transform=ax.transAxes, ha="right", fontsize=8, color="gray")

ax.set_xlabel(r"Excess noise $\varepsilon$  (SNU)", fontsize=11)
ax.set_ylabel("bits/use", fontsize=10)
ax.set_title(r"(b)  $I_{AB}$ and $\chi_{BE}$ vs Excess Noise", fontsize=11)
ax.legend(fontsize=7.5, framealpha=0.85, ncol=2)

# ── Panel 3: SKR gap (MB − Uniform, Binomial − Uniform) ──────────────
ax = axes[2]
gap_bin = skr_log["Binomial"] - skr_log["Uniform"]
gap_mb  = skr_log["MB"]       - skr_log["Uniform"]

# mask out where both are at floor (−9) — gap is meaningless there
mask = (skr_log["Uniform"] > -8.9) | (skr_log["Binomial"] > -8.9)

ax.semilogx(EPS_GRID[mask], gap_bin[mask],
            color=COLORS["Binomial"], linestyle=STYLES["Binomial"],
            linewidth=2.2, label="Binomial − Uniform")
ax.semilogx(EPS_GRID[mask], gap_mb[mask],
            color=COLORS["MB"], linestyle=STYLES["MB"],
            linewidth=2.2, label="MB − Uniform")
ax.axhline(0, color="black", linewidth=0.7, alpha=0.35)
ax.set_xlabel(r"Excess noise $\varepsilon$  (SNU)", fontsize=11)
ax.set_ylabel(r"$\Delta\log_{10}(\mathrm{SKR})$  (decades)", fontsize=10)
ax.set_title("(c)  SKR advantage over Uniform", fontsize=11)
ax.legend(fontsize=10, framealpha=0.85)

# ─── Global title & layout ────────────────────────────────────────────
fig.suptitle(
    "CV-QKD UAV–HAP: SKR vs Excess Noise — Binomial / MB / Uniform (QAM-256)\n"
    f"$L$={L_KM:.0f} km,  $V$={V_FIX:.1f} km,  $W_0$={W0_FIX:.1f} cm,  "
    f"$a$={A_FIX:.1f} cm,  $C_n^2$={C2N_FIX}×10⁻¹⁵,  "
    f"$T_{{eff}}$={T_EFF:.4f},  $\\beta$={BETA}",
    fontsize=10, y=1.02
)

plt.tight_layout()

output_dir = Path(__file__).resolve().parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

panel1 = plt.figure(figsize=(6.2, 4.8))
ax = panel1.add_subplot(111)
for name in ["MB", "Binomial", "Uniform"]:
    ax.semilogx(EPS_GRID, skr_log[name],
                color=COLORS[name], linestyle=STYLES[name],
                linewidth=LW[name], label=name)
ax.axhline(0,  color="black", linewidth=0.7, alpha=0.35)
ax.axhline(-3, color="gray",  linewidth=0.7, alpha=0.45, linestyle="--")
ax.set_xlabel(r"Excess noise $\varepsilon$  (SNU)", fontsize=11)
ax.set_ylabel(r"$\log_{10}(\mathrm{SKR})$  (bits/pulse)", fontsize=10)
ax.set_title("(a)  SKR vs Excess Noise", fontsize=11)
ax.set_ylim(-9, 0.75)
ax.legend(fontsize=10, framealpha=0.85)
panel1.tight_layout()
panel1.savefig(output_dir / "skr_vs_excess_noise_panel1.pdf", format="pdf", bbox_inches="tight")
plt.close(panel1)

panel2 = plt.figure(figsize=(6.2, 4.8))
ax = panel2.add_subplot(111)
for name in ["MB", "Binomial", "Uniform"]:
    ax.semilogx(EPS_GRID, iab_arr[name],
                color=COLORS[name], linestyle=STYLES[name],
                linewidth=LW[name], label=f"$I_{{AB}}$ {name}")
    ax.semilogx(EPS_GRID, chi_arr[name],
                color=COLORS[name], linestyle=STYLES[name],
                linewidth=1.0, alpha=0.45,
                label=f"$\\chi_{{BE}}$ {name}")
ax.text(0.97, 0.75, "$I_{AB}$ (upper curves)",
        transform=ax.transAxes, ha="right", fontsize=8, color="black")
ax.text(0.97, 0.55, "$\\chi_{BE}$ (lower / faded)",
        transform=ax.transAxes, ha="right", fontsize=8, color="gray")
ax.set_xlabel(r"Excess noise $\varepsilon$  (SNU)", fontsize=11)
ax.set_ylabel("bits/use", fontsize=10)
ax.set_title(r"(b)  $I_{AB}$ and $\chi_{BE}$ vs Excess Noise", fontsize=11)
ax.legend(fontsize=7.5, framealpha=0.85, ncol=2)
panel2.tight_layout()
panel2.savefig(output_dir / "skr_vs_excess_noise_panel2.pdf", format="pdf", bbox_inches="tight")
plt.close(panel2)

panel3 = plt.figure(figsize=(6.2, 4.8))
ax = panel3.add_subplot(111)
gap_bin = skr_log["Binomial"] - skr_log["Uniform"]
gap_mb  = skr_log["MB"] - skr_log["Uniform"]
mask = (skr_log["Uniform"] > -8.9) | (skr_log["Binomial"] > -8.9)
ax.semilogx(EPS_GRID[mask], gap_bin[mask],
            color=COLORS["Binomial"], linestyle=STYLES["Binomial"],
            linewidth=2.2, label="Binomial − Uniform")
ax.semilogx(EPS_GRID[mask], gap_mb[mask],
            color=COLORS["MB"], linestyle=STYLES["MB"],
            linewidth=2.2, label="MB − Uniform")
ax.axhline(0, color="black", linewidth=0.7, alpha=0.35)
ax.set_xlabel(r"Excess noise $\varepsilon$  (SNU)", fontsize=11)
ax.set_ylabel(r"$\Delta\log_{10}(\mathrm{SKR})$  (decades)", fontsize=10)
ax.set_title("(c)  SKR advantage over Uniform", fontsize=11)
ax.legend(fontsize=10, framealpha=0.85)
panel3.tight_layout()
panel3.savefig(output_dir / "skr_vs_excess_noise_panel3.pdf", format="pdf", bbox_inches="tight")
plt.close(panel3)

plt.show()
plt.close()

# ─── Quick numerical summary ──────────────────────────────────────────
print("\n── SKR at key eps values ──────────────────────────────────────")
print(f"{'eps':>10s}  {'MB':>10s}  {'Binomial':>10s}  {'Uniform':>10s}")
for eps_check in [0.0001, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1]:
    idx = np.argmin(np.abs(EPS_GRID - eps_check))
    row = [f"{10**skr_log[n][idx]:.2e}" for n in ["MB", "Binomial", "Uniform"]]
    print(f"{eps_check:>10.4f}  {row[0]:>10s}  {row[1]:>10s}  {row[2]:>10s}")
