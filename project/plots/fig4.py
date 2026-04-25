import numpy as np
import matplotlib.pyplot as plt

from ..channel.channel_model import total_transmittance
from ..config import ELEVS, EPS_CH, LS, VA_GM, VA_PSK, VA_QAM
from ..protocols.gm import skr_gm
from ..protocols.psk import skr_psk
from ..protocols.qam import _optimize_disc_gaussian_v, skr_qam
from ..reconciliation.finite_size import plob_upper_bound


def _nan(v, floor=1e-12):
    if not np.isfinite(v):
        return np.nan
    return v if v > floor else np.nan


def plot_fig4():
    """Asymptotic SKR vs altitude – good atmosphere – GM / M-PSK / M-QAM."""
    print("▶ Figure 4 (asymptotic, good atmosphere)...")
    V, Cn2, Dr, beta, eps = 200, 1e-16, 1.0, 0.90, EPS_CH
    alt_km = np.arange(160, 1050, 10)
    alt_m = alt_km * 1e3

    panels = [
        (
            "(a) M-PSK",
            [
                ("Gaussian", "goldenrod", "gm", {}),
                ("8-PSK", "blue", "psk", {"M": 8}),
                ("4-PSK", "red", "psk", {"M": 4}),
            ],
            alt_km,
            [160, 1000],
        ),
        (
            "(b) 64-QAM",
            [
                ("Gaussian", "goldenrod", "gm", {}),
                ("Binomial Dist.", "blue", "qam", {"M": 64}),
                ("Disc. Gaussian Dist.", "red", "qam", {"M": 64}),
            ],
            np.arange(160, 5100, 20),
            [160, 5000],
        ),
        (
            "(c) 256-QAM",
            [
                ("Gaussian", "goldenrod", "gm", {}),
                ("Binomial Dist.", "blue", "qam", {"M": 256}),
                ("Disc. Gaussian Dist.", "red", "qam", {"M": 256}),
            ],
            np.arange(160, 6100, 25),
            [160, 6000],
        ),
    ]

    # IEEE-paper-like layout: 3 stacked panels, caption at bottom.
    fig, axes = plt.subplots(3, 1, figsize=(6.5, 11))

    v64 = _optimize_disc_gaussian_v(VA_QAM, 64)
    v256 = _optimize_disc_gaussian_v(VA_QAM, 256)

    for ax, (title, protos, akm, xlim) in zip(axes, panels):
        ax.set_title(title)
        am = akm * 1e3
        # PLOB upper bound at θ=90
        ub = [plob_upper_bound(total_transmittance(90, H, Dr, V, Cn2)[0]) for H in am]
        ax.semilogy(akm, ub, "k-", lw=2.5, label="Upper Bound")

        for lbl, col, ptype, kw in protos:
            for th, ls in zip(ELEVS, LS):
                vals = []
                for H in am:
                    T, _, ff_ok = total_transmittance(th, H, Dr, V, Cn2)
                    if not ff_ok:
                        vals.append(np.nan)
                        continue
                    if ptype == "gm":
                        s = skr_gm(VA_GM, T, eps, beta)
                    elif ptype == "psk":
                        s = skr_psk(VA_PSK, T, eps, kw["M"], beta)
                    else:
                        if lbl == "Disc. Gaussian Dist.":
                            vv = v64 if kw["M"] == 64 else v256
                            s = skr_qam(VA_QAM, T, eps, kw["M"], beta, prob_model="disc_gaussian", v=vv)
                        else:
                            s = skr_qam(VA_QAM, T, eps, kw["M"], beta, prob_model="binomial")
                    vals.append(_nan(s))
                lb = lbl if th == ELEVS[0] else "_"
                ax.semilogy(akm, vals, color=col, ls=ls, lw=1.5, label=lb)

        ax.set_xlabel("Satellite Altitude at Zenith [km]")
        ax.set_ylabel("SKR [bits/pulse]")
        ax.set_ylim([1e-7, 1e0])
        ax.set_xlim(xlim)
        ax.minorticks_on()
        ax.grid(True, which="major", alpha=0.35, linestyle="-")
        ax.grid(True, which="minor", alpha=0.20, linestyle=":")
        ax.legend(fontsize=8, loc="upper right", frameon=True)

    fig.text(
        0.5,
        0.02,
        r"Fig. 4. Asymptotic limit SKRs as a function of satellite altitude for "
        r"(a) M-PSK, (b) 64-QAM, and (c) 256-QAM DM-CVQKD in relation to "
        r"GM-CVQKD in good atmospheric conditions. The solid lines indicate "
        r"$\theta = 90^\circ$, dashed lines indicate $\theta = 60^\circ$, "
        r"dash-dotted lines indicate $\theta = 30^\circ$. $D_r = 1$ m, "
        r"$\beta = 90\%$.",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.show()
    print("  ✓ Figure 4 displayed")
