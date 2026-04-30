import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from ..channel.channel_model import total_transmittance
from ..config import ELEVS, EPS_CH, LS, FiniteSizeParams, NoiseParams, SecurityParams, VA_GM
from ..protocols.gm import noise, skr_components


EL_LEG = [Line2D([0], [0], color="gray", ls=s, lw=1.5, label=f"θ={t}°") for t, s in zip(ELEVS, LS)]


def _nan(v, floor=1e-12):
    if not np.isfinite(v):
        return np.nan
    return v if v > floor else np.nan


def _finite_size_skr_from_t(T, VA, eps, beta):
    t_arr = np.array([max(float(T), 1e-15)], dtype=float)
    n_terms = noise(t_arr, NoiseParams(xi_ch=float(eps), detection="hom"))
    sec = SecurityParams(VA=float(VA), beta=float(beta))
    comps = skr_components(t_arr, n_terms, sec, detection="hom", eta_d=n_terms["eta_d"])
    fs = FiniteSizeParams()
    n_block = int(round(float(fs.n_ratio) * float(fs.N_block)))
    epsilon = float(fs.epsilon_PE + fs.epsilon_EC + fs.epsilon_PA)
    delta = 7.0 * np.log2(2.0 / epsilon) / np.sqrt(float(n_block))
    k = (float(n_block) / float(fs.N_block)) * (float(sec.beta) * float(comps["I_AB"][0]) - float(comps["chi_BE"][0]) - delta)
    return max(float(k), 0.0)


def plot_fig6():
    """Finite-size SKR vs altitude – GM-CVQKD, MD vs MLC-MSD."""
    print("▶ Figure 6 (finite-size)...")
    V, Cn2, eps = 200, 1e-16, EPS_CH
    COLORS = {"MD": "blue", "MLC-MSD": "red"}
    MODE_BETA = {"MD": 0.95, "MLC-MSD": 0.90}

    configs = [("(a) $D_r = 1$ m", 1.0, np.arange(160, 460, 5)), ("(b) $D_r = 2$ m", 2.0, np.arange(160, 1010, 10))]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        r"Fig. 6 – Finite-Size SKRs  |  GM-CVQKD, Homodyne, MD vs MLC-MSD"
        "\n"
        r"Good conditions: $V\!=\!200$ km, $C_n^2\!=\!10^{-16}$",
        fontsize=11,
    )

    for ax, (title, Dr, akm) in zip(axes, configs):
        ax.set_title(title)
        am = akm * 1e3
        for mode in ["MD", "MLC-MSD"]:
            for th, ls in zip(ELEVS, LS):
                vals = []
                for H in am:
                    T, _, ok = total_transmittance(th, H, Dr, V, Cn2)
                    if not ok:
                        vals.append(np.nan)
                        continue
                    s = _finite_size_skr_from_t(T, VA_GM, eps, MODE_BETA[mode])
                    vals.append(_nan(s))
                lb = mode if th == ELEVS[0] else "_"
                ax.semilogy(akm, vals, color=COLORS[mode], ls=ls, lw=1.5, label=lb)

        ax.set_xlabel("Satellite Altitude at Zenith [km]")
        ax.set_ylabel("SKR [bits/s]")
        ax.set_ylim(bottom=1e4)
        ax.set_xlim([akm[0], akm[-1]])
        ax.grid(True, which="both", alpha=0.25)
        h, l = ax.get_legend_handles_labels()
        ax.legend(handles=h + EL_LEG, labels=l + [e.get_label() for e in EL_LEG], fontsize=8, loc="upper right")

    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 6 displayed")
