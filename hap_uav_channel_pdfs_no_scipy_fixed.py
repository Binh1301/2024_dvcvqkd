import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# SciPy-free HAP-UAV channel PDF script
# Requires only: numpy, matplotlib
# Baseline model matches current rho=0 configuration.
# ============================================================

OUT = Path("channel_pdf_figures_no_scipy")
OUT.mkdir(exist_ok=True)

# -----------------------------
# Helpers
# -----------------------------
if hasattr(np, "trapezoid"):
    trapz = np.trapezoid
else:
    trapz = np.trapz

def savefig(name):
    plt.tight_layout()
    plt.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    plt.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close()

def relerr(x, y=1.0):
    return abs(x-y) / max(abs(y), 1e-300)

# ============================================================
# 1. PARAMETERS
# ============================================================
lambda_ = 1.55e-6
H_HAP = 2.0e4
h_UAV = 1.0e3
zeta = 0.0
v_wind = 21.0
Cn2_0 = 5.0e-14

D_r = 0.08
theta_div = 223e-6
omega_0 = 4.425e-3
F_0 = np.inf
eta_atm = 0.9316271221

sigma_h = 1.0
sigma_H_pos = 0.30
theta_jt = 15.61e-6
rho = 0.0

sigma_o = 1.5e-3
theta_FOV = 6.25e-3

epsilon_min = 0.001
epsilon_max = 0.04

# ============================================================
# 2. GEOMETRY
# ============================================================
sec_zeta = 1.0 / np.cos(zeta)
L = (H_HAP - h_UAV) * sec_zeta
k = 2.0 * np.pi / lambda_

omega_0_check = 2.0 * lambda_ / (np.pi * theta_div)
print(f"omega_0(table) = {omega_0:.12e} m")
print(f"omega_0(check) = {omega_0_check:.12e} m")
print(f"relative difference = {abs(omega_0_check-omega_0)/omega_0:.6e}")

# ============================================================
# 3. HUFNAGEL-VALLEY + NUMERICAL INTEGRALS
# ============================================================
def Cn2(h):
    h = np.asarray(h, dtype=float)
    return (
        0.00594 * (v_wind / 27.0) ** 2
        * (1e-5 * h) ** 10 * np.exp(-h / 1000.0)
        + 2.7e-16 * np.exp(-h / 1500.0)
        + Cn2_0 * np.exp(-h / 100.0)
    )

# Dense altitude grid. 200k points is still cheap in NumPy for 19 km.
h_grid = np.linspace(h_UAV, H_HAP, 200_001)
cn = Cn2(h_grid)

I_R = trapz(cn * (h_grid - h_UAV) ** (5.0 / 6.0), h_grid)
sigma_R0_sq = 2.25 * k ** (7.0 / 6.0) * sec_zeta ** (11.0 / 6.0) * I_R

I_phi_num = trapz(cn * h_grid**2, h_grid)
I_phi_den = trapz(cn * h_grid ** (5.0 / 6.0), h_grid)
Phi = (I_phi_num / I_phi_den) ** (6.0 / 7.0)

A_A = (
    1.0
    + 1.11 * (D_r**2 / (lambda_ * Phi * sec_zeta)) ** (7.0 / 6.0)
) ** (-1.0)

sigma_RD_sq = A_A * sigma_R0_sq
v_sc = sigma_RD_sq
mu_ln = -v_sc / 2.0
sigma_ln = np.sqrt(v_sc)

def f_Hsc(x):
    x = np.asarray(x, dtype=float)
    out = np.zeros_like(x)
    m = x > 0
    xx = x[m]
    out[m] = (
        1.0 / (xx * np.sqrt(2.0*np.pi*v_sc))
        * np.exp(-(np.log(xx) + v_sc/2.0)**2 / (2.0*v_sc))
    )
    return out

# ============================================================
# 4. BEAM PROPAGATION + Gd
# ============================================================
curvature_term = 1.0 if np.isinf(F_0) else (1.0 - L/F_0)**2
omega_L = omega_0 * np.sqrt(
    curvature_term + (2.0*L/(k*omega_0**2))**2
)

Lambda = 2.0 * L / (k * omega_L**2)

I_Gd = trapz(
    cn * ((h_grid - h_UAV)/(H_HAP-h_UAV)) ** (5.0/3.0),
    h_grid,
)

G_d = (
    4.35
    * Lambda ** (5.0/6.0)
    * k ** (7.0/6.0)
    * (H_HAP-h_UAV) ** (5.0/6.0)
    * sec_zeta ** (11.0/6.0)
    * I_Gd
)

omega_Le = omega_L * np.sqrt(1.0 + G_d)

nu = np.sqrt(np.pi) * D_r / (2.0*np.sqrt(2.0)*omega_L)
erf_nu = math.erf(float(nu))
A0 = erf_nu**2

omega_Leq_sq = (
    omega_Le**2
    * np.sqrt(np.pi) * erf_nu
    / (2.0*nu*np.exp(-nu**2))
)
omega_Leq = np.sqrt(omega_Leq_sq)

# ============================================================
# 5. MISALIGNMENT
# ============================================================
sigma_jt_sq = sigma_h**2 + sigma_H_pos**2 + (L*theta_jt)**2
sigma_jt = np.sqrt(sigma_jt_sq)
chi = omega_Leq / (2.0*sigma_jt)
chi2 = chi**2

def f_rmis(r):
    r = np.asarray(r, dtype=float)
    out = np.zeros_like(r)
    m = r >= 0
    rr = r[m]
    if rho == 0.0:
        out[m] = rr/sigma_jt_sq * np.exp(-rr**2/(2.0*sigma_jt_sq))
    else:
        arg = rho*rr/sigma_jt_sq
        out[m] = (
            rr/sigma_jt_sq
            * np.exp(-(rr**2+rho**2)/(2.0*sigma_jt_sq))
            * np.i0(arg)
        )
    return out

def f_Hp(u):
    u = np.asarray(u, dtype=float)
    out = np.zeros_like(u)
    m = (u > 0) & (u <= A0)
    uu = u[m]

    if rho == 0.0:
        out[m] = chi2 / (A0**chi2) * uu**(chi2-1.0)
    else:
        logratio = np.log(uu/A0)
        root = np.sqrt(np.maximum(0.0, -0.5*omega_Leq_sq*logratio))
        arg = rho/sigma_jt_sq * root
        out[m] = (
            chi2/(A0**chi2)
            * np.exp(-rho**2/(2.0*sigma_jt_sq))
            * uu**(chi2-1.0)
            * np.i0(arg)
        )
    return out

# ============================================================
# 6. AoA
# ============================================================
def f_theta(theta):
    theta = np.asarray(theta, dtype=float)
    out = np.zeros_like(theta)
    m = theta >= 0
    th = theta[m]
    out[m] = th/sigma_o**2 * np.exp(-th**2/(2.0*sigma_o**2))
    return out

p_out = np.exp(-theta_FOV**2/(2.0*sigma_o**2))
p_in = 1.0 - p_out

# ============================================================
# 7. FIGURES FOR INDIVIDUAL FACTORS
# ============================================================

# 7.1 H_sc
# Lognormal quantile-like plotting window: exp(mu +/- 5 sigma)
hsc_min = np.exp(mu_ln - 5.0*sigma_ln)
hsc_max = np.exp(mu_ln + 5.0*sigma_ln)
x = np.linspace(hsc_min, hsc_max, 2500)
plt.figure(figsize=(6.4, 4.2))
plt.plot(x, f_Hsc(x))
plt.xlabel(r"$H_{\rm sc}$")
plt.ylabel(r"$f_{H_{\rm sc}}(h)$")
plt.title("Scintillation-gain PDF")
plt.grid(alpha=0.25)
savefig("fig_01_scintillation_pdf")

# 7.2 r_mis
rmax = 6.0*sigma_jt + rho
r = np.linspace(0.0, rmax, 2500)
plt.figure(figsize=(6.4, 4.2))
plt.plot(r, f_rmis(r))
plt.xlabel(r"$r_{\rm mis}$ (m)")
plt.ylabel(r"$f_{r_{\rm mis}}(r)$")
plt.title("Radial misalignment PDF")
plt.grid(alpha=0.25)
savefig("fig_02_radial_misalignment_pdf")

# 7.3 H_p
u_min = max(A0*1e-8, np.finfo(float).tiny)
u = np.linspace(u_min, A0, 3000)
plt.figure(figsize=(6.4, 4.2))
plt.plot(u, f_Hp(u))
plt.xlabel(r"$H_p$")
plt.ylabel(r"$f_{H_p}(u)$")
plt.title("Pointing/misalignment coefficient PDF")
plt.grid(alpha=0.25)
savefig("fig_03_pointing_pdf")

# 7.4 theta_a
theta = np.linspace(0.0, max(6.0*sigma_o, 1.25*theta_FOV), 2500)
plt.figure(figsize=(6.4, 4.2))
plt.plot(theta*1e3, f_theta(theta)/1e3)
plt.axvline(theta_FOV*1e3, linestyle="--", label=r"$\theta_{\rm FOV}$")
plt.xlabel(r"$\theta_a$ (mrad)")
plt.ylabel(r"PDF (mrad$^{-1}$)")
plt.title("Angle-of-arrival PDF")
plt.legend()
plt.grid(alpha=0.25)
savefig("fig_04_aoa_pdf")

# 7.5 B_AoA PMF
plt.figure(figsize=(5.6, 4.0))
plt.bar([0, 1], [p_out, p_in])
plt.xticks([0, 1], [r"$B_{\rm AoA}=0$", r"$B_{\rm AoA}=1$"])
plt.ylabel("Probability")
plt.title("AoA acquisition PMF")
plt.grid(axis="y", alpha=0.25)
savefig("fig_05_aoa_pmf")

# 7.6 eta_atm deterministic mass
plt.figure(figsize=(5.6, 4.0))
markerline, stemlines, baseline = plt.stem([eta_atm], [1.0])
plt.xlabel(r"$\eta_{\rm atm}$")
plt.ylabel("Probability mass")
plt.title("Deterministic atmospheric transmittance")
plt.xlim(max(0, eta_atm-0.08), min(1.02, eta_atm+0.08))
plt.ylim(0, 1.1)
plt.grid(alpha=0.25)
savefig("fig_06_atmospheric_mass")

# ============================================================
# 8. COMPOSITE ACTIVE PDF f_X
# ============================================================
# Numerical convolution over u. Use log-spaced u because H_p support starts at 0.
u_conv = np.geomspace(max(A0*1e-10, 1e-300), A0, 5000)
hp_conv = f_Hp(u_conv)

def f_X_vector(tvals):
    tvals = np.asarray(tvals, dtype=float)
    vals = np.empty_like(tvals)

    # Compute in chunks to keep memory bounded.
    chunk = 300
    for i in range(0, len(tvals), chunk):
        tt = tvals[i:i+chunk][:, None]
        uu = u_conv[None, :]
        arg = tt/(eta_atm*uu)
        integrand = (
            (1.0/(eta_atm*uu))
            * f_Hsc(arg)
            * hp_conv[None, :]
        )
        vals[i:i+chunk] = trapz(integrand, u_conv, axis=1)
    return vals

# Main active distribution scale is tiny here, so logarithmic x-grid is useful.
x_lo = max(1e-10, eta_atm*A0*np.exp(mu_ln-6*sigma_ln)*1e-5)
x_hi = min(1.5, eta_atm*A0*np.exp(mu_ln+6*sigma_ln)*1.2)
x_grid = np.geomspace(x_lo, max(x_hi, x_lo*100), 3500)
fx_grid = f_X_vector(x_grid)

# Normalize raw f_X numerically on a wider grid.
x_norm = np.geomspace(1e-12, 2.0, 7000)
fx_norm = f_X_vector(x_norm)
norm_fx = trapz(fx_norm, x_norm)

plt.figure(figsize=(6.4, 4.2))
plt.plot(x_grid, fx_grid)
plt.xlabel(r"$X=\eta_{\rm atm}H_{\rm sc}H_p$")
plt.ylabel(r"$f_X(x)$")
plt.title("Raw active-channel PDF")
plt.grid(alpha=0.25)
savefig("fig_07_raw_active_pdf")

# ============================================================
# 9. PHYSICAL ACTIVE PDF + TOTAL MIXED DISTRIBUTION
# ============================================================
T_grid = np.geomspace(1e-12, 1.0, 5500)
fT_raw = f_X_vector(T_grid)
FX1 = trapz(fT_raw, T_grid)
p_active = fT_raw / FX1
p_cont = p_in * p_active

plt.figure(figsize=(6.4, 4.2))
plt.plot(T_grid, p_cont)
plt.xscale("log")
plt.xlabel(r"$T$")
plt.ylabel("Continuous density")
plt.title("Physical HAP-UAV power-transmittance distribution")
plt.grid(alpha=0.25)
plt.text(
    0.04, 0.93,
    rf"$P(T=0)=p_{{\rm out}}={p_out:.3e}$",
    transform=plt.gca().transAxes,
    va="top"
)
savefig("fig_08_total_channel_continuous_pdf")

plt.figure(figsize=(5.6, 4.0))
plt.bar(["Outage mass\n$T=0$", r"Active mass\n$0<T\leq 1$"], [p_out, p_in])
plt.ylabel("Probability mass")
plt.title("Total channel: outage + active probability")
plt.grid(axis="y", alpha=0.25)
savefig("fig_09_total_channel_outage_mass")

# ============================================================
# 10. MOMENTS
# ============================================================
mean_T = p_in/FX1 * trapz(T_grid*fT_raw, T_grid)
mean_sqrtT = p_in/FX1 * trapz(np.sqrt(T_grid)*fT_raw, T_grid)

epsilon_mean = 0.5*(epsilon_min+epsilon_max)
mean_T_epsilon = mean_T * epsilon_mean

# ============================================================
# 11. NORMALIZATION CHECKS
# ============================================================
hsc_check_grid = np.geomspace(np.exp(mu_ln-10*sigma_ln), np.exp(mu_ln+10*sigma_ln), 100_000)
hsc_norm = trapz(f_Hsc(hsc_check_grid), hsc_check_grid)
hsc_mean = trapz(hsc_check_grid*f_Hsc(hsc_check_grid), hsc_check_grid)

r_check = np.linspace(0, 10*sigma_jt+rho, 100_000)
r_norm = trapz(f_rmis(r_check), r_check)

u_check = np.geomspace(max(A0*1e-12, 1e-300), A0, 100_000)
hp_norm = trapz(f_Hp(u_check), u_check)

pactive_norm = trapz(p_active, T_grid)
total_prob = p_out + p_in*pactive_norm

# ============================================================
# 12. SUMMARY
# ============================================================
print("\n========== DERIVED VALUES ==========")
print(f"L                 = {L:.12e} m")
print(f"k                 = {k:.12e} 1/m")
print(f"sigma_R0^2        = {sigma_R0_sq:.12e}")
print(f"Phi               = {Phi:.12e}")
print(f"A_A               = {A_A:.12e}")
print(f"sigma_RD^2=v_sc   = {v_sc:.12e}")
print(f"omega_L           = {omega_L:.12e} m")
print(f"Lambda            = {Lambda:.12e}")
print(f"G_d               = {G_d:.12e}")
print(f"omega_Le          = {omega_Le:.12e} m")
print(f"nu                = {nu:.12e}")
print(f"A0                = {A0:.12e}")
print(f"omega_Leq         = {omega_Leq:.12e} m")
print(f"L*theta_jt        = {L*theta_jt:.12e} m")
print(f"sigma_jt          = {sigma_jt:.12e} m")
print(f"chi               = {chi:.12e}")
print(f"p_out             = {p_out:.12e}")
print(f"p_in              = {p_in:.12e}")
print(f"raw f_X norm      = {norm_fx:.12e}")
print(f"F_X(1)            = {FX1:.12e}")
print(f"<T>               = {mean_T:.12e}")
print(f"<sqrt(T)>         = {mean_sqrtT:.12e}")
print(f"<T eps_base>      = {mean_T_epsilon:.12e}")

print("\n========== NORMALIZATION CHECKS ==========")
print(f"int f_Hsc         = {hsc_norm:.12e}, rel.err={relerr(hsc_norm):.3e}")
print(f"E[H_sc]           = {hsc_mean:.12e}, rel.err={relerr(hsc_mean):.3e}")
print(f"int f_rmis        = {r_norm:.12e}, rel.err={relerr(r_norm):.3e}")
print(f"int f_Hp          = {hp_norm:.12e}, rel.err={relerr(hp_norm):.3e}")
print(f"int p_active      = {pactive_norm:.12e}, rel.err={relerr(pactive_norm):.3e}")
print(f"total probability = {total_prob:.12e}, rel.err={relerr(total_prob):.3e}")

print(f"\nFigures saved in: {OUT.resolve()}")
