import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from ..channel.channel_model import total_transmittance
from ..config import ELEVS, EPS_CH, LS, VA_GM, VA_QAM
from ..protocols.gm import skr_gm
from ..protocols.qam import _optimize_disc_gaussian_v, skr_qam
from ..reconciliation.finite_size import plob_upper_bound


EL_LEG = [Line2D([0], [0], color="gray", ls=s, lw=1.5, label=f"θ={t}°") for t, s in zip(ELEVS, LS)]


def _nan(v, floor=1e-12):
    if not np.isfinite(v):
        return np.nan
    return v if v > floor else np.nan


def plot_fig5():
    """Asymptotic SKR vs altitude – bad atmosphere – GM / M-QAM only."""
    print("▶ Figure 5 (asymptotic, bad atmosphere)...")
    V, Cn2, Dr, beta, eps = 20, 1e-13, 1.0, 0.90, EPS_CH
    alt_km = np.arange(160, 6100, 25)
    alt_m = alt_km * 1e3

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        r"Fig. 5 – Asymptotic SKRs  |  Bad: $V\!=\!20$ km, "
        r"$C_n^2\!=\!10^{-13}$, $D_r\!=\!1$ m, $\beta\!=\!90\%$  "
        "(M-PSK omitted: no positive SKR)",
        fontsize=11,
    )

    v64 = _optimize_disc_gaussian_v(VA_QAM, 64)
    v256 = _optimize_disc_gaussian_v(VA_QAM, 256)
    for ax, M_qam in zip(axes, [64, 256]):
        ax.set_title(f"({chr(96 + list(axes).index(ax) + 1)}) {M_qam}-QAM")
        ub = [plob_upper_bound(total_transmittance(90, H, Dr, V, Cn2)[0]) for H in alt_m]
        ax.semilogy(alt_km, ub, "k-", lw=2.5, label="Upper Bound")

        for lbl, col, ptype, VA in [
            ("Gaussian", "goldenrod", "gm", VA_GM),
            ("Binomial Dist.", "blue", "qam", VA_QAM),
            ("Disc. Gaussian Dist.", "red", "qam", VA_QAM),
        ]:
            for th, ls in zip(ELEVS, LS):
                vals = []
                for H in alt_m:
                    T, _, ff_ok = total_transmittance(th, H, Dr, V, Cn2)
                    if not ff_ok:
                        vals.append(np.nan)
                        continue
                    if ptype == "gm":
                        s = skr_gm(VA, T, eps, beta)
                    elif lbl == "Disc. Gaussian Dist.":
                        vv = v64 if M_qam == 64 else v256
                        s = skr_qam(VA, T, eps, M_qam, beta, prob_model="disc_gaussian", v=vv)
                    else:
                        s = skr_qam(VA, T, eps, M_qam, beta, prob_model="binomial")
                    vals.append(_nan(s))
                lb = lbl if th == ELEVS[0] else "_"
                ax.semilogy(alt_km, vals, color=col, ls=ls, lw=1.5, label=lb)

        ax.set_xlabel("Satellite Altitude at Zenith [km]")
        ax.set_ylabel("SKR [bits/pulse]")
        # FIX: lower y-min to display low-SKR curves (θ=60°, θ=30°).
        ax.set_ylim([1e-12, 1e0])
        ax.set_xlim([alt_km[0], alt_km[-1]])
        ax.grid(True, which="both", alpha=0.25)
        h, l = ax.get_legend_handles_labels()
        ax.legend(handles=h + EL_LEG, labels=l + [e.get_label() for e in EL_LEG], fontsize=7, loc="upper right")

    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 5 displayed")
