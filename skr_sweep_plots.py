"""
SKR sweep plots for CV-QKD UAV-HAP system.
4 panels (V, W0, a, C2n) showing only log10(SKR) curves.
Physics ported directly from skr_compare_qam256.html (document 9).

Fixed baseline:
  W0 = 11.00 cm,  a = 20.00 cm,  V = 13.00 km,  C2n = 0.50 e-15
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.special import i0, i1
from pathlib import Path

# ─── QAM precomputed states (from Python code, VA=2 SNU) ──────────────
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

# ─── Protocol constants ───────────────────────────────────────────────
EPS   = 0.001
ETA   = 0.95
V_EL  = 0.001
BETA  = 0.95
L_KM  = 20.0
LAM   = 1550.0   # nm
SIG_UAV = 10.2   # cm

# ─── Fixed sweep baselines ────────────────────────────────────────────
W0_FIX  = 11.00  # cm
A_FIX   = 20.00  # cm
V_FIX   = 13.00  # km
C2N_FIX = 0.50   # ×10^-15

N_MC   = 3000
N_PTS  = 120

# ─── Monte Carlo samples (LCG, same seed as JS) ──────────────────────
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


def compute_channel(V_km, W0_cm, a_cm, C2n_15):
    W0  = W0_cm  / 100
    a   = a_cm   / 100
    C2n = C2n_15 * 1e-15
    sg  = SIG_UAV / 100
    lam = LAM * 1e-9
    L   = L_KM * 1000

    # atmospheric attenuation (Kruse)
    q      = kruse_q(V_km)
    xi     = (3.912 / V_km) * (LAM / 550) ** (-q)
    eta_atm = np.exp(-xi * L_KM)

    # beam propagation
    zR  = np.pi * W0**2 / lam
    WL  = W0 * np.sqrt(1 + (L / zR)**2)

    # aperture truncation
    T0sq = max(0.0, 1 - np.exp(-2 * a**2 / WL**2))
    T0   = np.sqrt(T0sq)

    x   = (2 * a / WL)**2
    ex  = np.exp(-x)
    I0v = float(i0(x))
    I1v = float(i1(x))
    denom  = max(1 - ex * I0v, 1e-15)
    ratio  = max(2 * T0sq / denom, 1 + 1e-15)
    Delta  = max(np.log(ratio), 1e-15)

    # doc-9 Gamma formula: (2*x*ex*I1) / (denom*Delta)
    gammaRaw = (2 * x * ex * I1v) / max(denom * Delta, 1e-15)
    Gamma    = max(gammaRaw, 1e-9)
    R        = max(a / Delta ** min(1/Gamma, 1e6), 1e-15)

    # beam wander
    sig2_turb = 1.919 * C2n * L**3 * (2 * W0) ** (-1/3)
    sig_r     = np.sqrt(max(sig2_turb + sg**2, 0))
    sig_s     = sig_r / np.sqrt(2)

    # Monte Carlo E[T²]
    u  = np.clip(MC, 1e-15, 1 - 1e-15)
    r  = sig_s * np.sqrt(-2 * np.log(u)) if sig_s > 0 else np.zeros(N_MC)
    ET2 = np.mean(T0sq * np.exp(-(r / R) ** Gamma))

    return eta_atm * ET2, eta_atm, ET2


# ─── SKR physics ─────────────────────────────────────────────────────
def _g(x):
    if x <= 1e-15: return 0.0
    return (x + 1) * np.log2(x + 1) - x * np.log2(x)


def compute_skr(T_eff, state):
    if T_eff < 1e-10:
        return 0.0, 0.0, 0.0, 0.0

    VA, tr_c, w = state["va"], state["tr_c"], state["w"]

    chi_line = (1 - T_eff) / T_eff + EPS
    chi_det  = (1 - ETA + V_EL) / ETA
    chi_tot  = chi_line + chi_det / T_eff

    # Z*
    zstar = 2 * np.sqrt(T_eff) * tr_c - np.sqrt(2 * T_eff * EPS * w)
    a_cv  = VA + 1
    b_cv  = 1 + T_eff * VA + T_eff * EPS
    zmax  = np.sqrt(a_cv * b_cv)
    if zstar >= zmax or (a_cv * b_cv - zstar**2) <= 0:
        zstar = min(zstar, zmax * (1 - 1e-9))

    # eigenvalues
    a, b, c = VA + 1, 1 + T_eff * VA + T_eff * EPS, zstar
    Dv    = a**2 + b**2 - 2*c**2
    B     = (a*b - c**2)**2
    disc  = max(Dv**2 - 4*B, 0)
    sd    = np.sqrt(disc)
    l1    = np.sqrt(max(0.5*(Dv + sd), 0))
    l2    = np.sqrt(max(0.5*(Dv - sd), 0))
    l3    = max(a - c**2 / (2 + T_eff*VA + T_eff*EPS), 1e-15)

    chi_BE = _g((l1-1)/2) + _g((l2-1)/2) - _g((l3-1)/2)
    I_AB   = np.log2(1 + T_eff * VA / (2 + T_eff * chi_tot))
    skr    = max(BETA * I_AB - chi_BE, 0.0)
    return skr, I_AB, chi_BE, chi_tot


def log10_skr(T_eff, state):
    skr, *_ = compute_skr(T_eff, state)
    return np.log10(max(skr, 1e-9))


# ─── Sweep helpers ────────────────────────────────────────────────────
def sweep(param, xs, fixed):
    skr_arr  = {k: np.empty(len(xs)) for k in QAM}
    for i, x in enumerate(xs):
        kw = dict(fixed)
        kw[param] = x
        T_eff, *_ = compute_channel(**kw)
        for name, st in QAM.items():
            skr_arr[name][i] = log10_skr(T_eff, st)
    return skr_arr


# ─── Build sweep data ─────────────────────────────────────────────────
print("Computing sweep data …")

sweeps = [
    dict(param="V_km",   xs=np.linspace(1,  50,  N_PTS),
         fixed=dict(W0_cm=W0_FIX, a_cm=A_FIX,   C2n_15=C2N_FIX),
         xlabel="Visibility  $V$  (km)",
         title="(a)  SKR vs Atmospheric Visibility"),

    dict(param="W0_cm",  xs=np.linspace(2,  20,  N_PTS),
         fixed=dict(V_km=V_FIX,   a_cm=A_FIX,   C2n_15=C2N_FIX),
         xlabel="Beam waist  $W_0$  (cm)",
         title="(b)  SKR vs Beam Waist"),

    dict(param="a_cm",   xs=np.linspace(3,  25,  N_PTS),
         fixed=dict(V_km=V_FIX,   W0_cm=W0_FIX, C2n_15=C2N_FIX),
         xlabel="Aperture radius  $a$  (cm)",
         title="(c)  SKR vs Aperture Radius"),

    dict(param="C2n_15", xs=np.linspace(0.01, 10, N_PTS),
         fixed=dict(V_km=V_FIX,   W0_cm=W0_FIX, a_cm=A_FIX),
         xlabel=r"$C_n^2$  ($\times 10^{-15}\ \mathrm{m}^{-2/3}$)",
         title=r"(d)  SKR vs Turbulence Strength  $C_n^2$"),
]

for s in sweeps:
    s["skr"] = sweep(s["param"], s["xs"],  s["fixed"])
    print(f"  {s['param']:8s} done")

# ─── Plot ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
axes = axes.flatten()

for idx, s in enumerate(sweeps):
    ax1 = axes[idx]

    # --- left axis: log10(SKR) ---
    xs = s["xs"]
    for name in ["MB", "Binomial", "Uniform"]:
        ax1.plot(xs, s["skr"][name],
                 color=COLORS[name], linestyle=STYLES[name],
                 linewidth=LW[name], label=name, zorder=3)

    # reference lines
    ax1.axhline(0,  color="black", linewidth=0.7, alpha=0.35, linestyle="-")
    ax1.axhline(-3, color="gray",  linewidth=0.7, alpha=0.45, linestyle="--")

    ax1.set_ylim(-9, 0.75)
    ax1.set_xlabel(s["xlabel"], fontsize=11)
    ax1.set_ylabel("$\\log_{10}(\\mathrm{SKR})$  (bits/pulse)", fontsize=10)
    ax1.set_title(s["title"], fontsize=11, pad=6)
    ax1.grid(True, alpha=0.25)

    ax1.legend(fontsize=9, loc="lower right", framealpha=0.85)

output_dir = Path(__file__).resolve().parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

single_panel_names = {
    "V_km": "skr_sweep_visibility.pdf",
    "W0_cm": "skr_sweep_beam_waist.pdf",
    "a_cm": "skr_sweep_aperture_radius.pdf",
    "C2n_15": "skr_sweep_turbulence.pdf",
}

for s in sweeps:
    panel_fig, panel_ax = plt.subplots(figsize=(6.6, 4.6))
    xs = s["xs"]
    for name in ["MB", "Binomial", "Uniform"]:
        panel_ax.plot(
            xs,
            s["skr"][name],
            color=COLORS[name],
            linestyle=STYLES[name],
            linewidth=LW[name],
            label=name,
            zorder=3,
        )
    panel_ax.axhline(0, color="black", linewidth=0.7, alpha=0.35, linestyle="-")
    panel_ax.axhline(-3, color="gray", linewidth=0.7, alpha=0.45, linestyle="--")
    panel_ax.set_ylim(-9, 0.75)
    panel_ax.set_xlabel(s["xlabel"], fontsize=11)
    panel_ax.set_ylabel("$\\log_{10}(\\mathrm{SKR})$  (bits/pulse)", fontsize=10)
    panel_ax.set_title(s["title"], fontsize=11, pad=6)
    panel_ax.grid(True, alpha=0.25)
    panel_ax.legend(fontsize=9, loc="lower right", framealpha=0.85)
    panel_fig.tight_layout()
    panel_fig.savefig(output_dir / single_panel_names[s["param"]], dpi=220, bbox_inches="tight")
    plt.close(panel_fig)

fig.suptitle(
    "CV-QKD UAV–HAP: SKR Comparison — Binomial / MB / Uniform (QAM-256)\n"
    f"$L$={L_KM} km, $\\lambda$={LAM:.0f} nm, $V_A$=2 SNU, "
    f"$\\beta$={BETA}, $\\sigma_{{UAV}}$={SIG_UAV} cm",
    fontsize=11, y=1.01
)

plt.tight_layout()
plt.show()
plt.close()
