import numpy as np
import matplotlib.pyplot as plt

from ..channel.channel_model import total_transmittance
from ..config import EPS_CH, H_OGS_ISS, FiniteSizeParams, NoiseParams, SecurityParams, VA_GM
from ..models.iss_model import elevation_model
from ..protocols.gm import noise, skr_components


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


def plot_fig8():
    """SKR vs elevation for ISS pass – GM-CVQKD, MD vs MLC-MSD."""
    print("▶ Figure 8 (SKR vs elevation angle, ISS pass)...")
    H_iss = 417_500.0
    Dr, V, Cn2, eps = 2.0, 200, 1e-16, EPS_CH
    COLORS = {"MD": "blue", "MLC-MSD": "red"}
    MODE_BETA = {"MD": 0.95, "MLC-MSD": 0.90}
    theta_arr = np.arange(30, 91, 1)
    total_key = {}
    t_pass, theta_pass = elevation_model()
    if t_pass.size > 1:
        sample_dt = np.diff(t_pass, append=t_pass[-1] + (t_pass[-1] - t_pass[-2]))
        dt_nominal = float(np.median(sample_dt))
    else:
        sample_dt = np.array([1.0], dtype=float)
        dt_nominal = 1.0
    theta_bins = np.arange(29.5, 91.5, 1.0)
    pass_mask = theta_pass >= 30.0
    seconds_per_theta, _ = np.histogram(theta_pass[pass_mask], bins=theta_bins, weights=sample_dt[pass_mask])

    fig, ax = plt.subplots(figsize=(8, 5))
    for mode in ["MD", "MLC-MSD"]:
        vals = []
        for th in theta_arr:
            T, _, ok = total_transmittance(float(th), H_iss, Dr, V, Cn2, H_OGS_ISS)
            if not ok:
                vals.append(np.nan)
                continue
            s = _finite_size_skr_from_t(T, VA_GM, eps, MODE_BETA[mode])
            vals.append(_nan(s))
        vals_arr = np.asarray(vals, dtype=float)
        ax.semilogy(theta_arr, vals_arr, color=COLORS[mode], lw=2, label=mode)

        valid = np.isfinite(vals_arr)
        total_key[mode] = float(np.sum(vals_arr[valid] * seconds_per_theta[valid]))

    ax.set_xlabel("Elevation Angle [°]", fontsize=12)
    ax.set_ylabel("SKR [bits/s]", fontsize=12)
    ax.set_title(
        r"Fig. 8 – SKR vs Elevation for ISS Pass  |  $D_r\!=\!2$ m, " r"$H_{ISS}\!=\!417.5$ km, Homodyne",
        fontsize=11,
    )
    ax.set_xlim([30, 90])
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=11)

    txt = (
        f"Pass integration uses 1 deg bins with dt~{dt_nominal:.2f} s/sample\n"
        f"Total key – MD:      {total_key['MD']/1e9:.3f} Gbit  [paper: 1.235 Gbit]\n"
        f"Total key – MLC-MSD: {total_key['MLC-MSD']/1e6:.1f} Mbit  [paper: 385 Mbit]"
    )
    ax.text(0.04, 0.97, txt, transform=ax.transAxes, fontsize=8, va="top", bbox=dict(boxstyle="round", fc="wheat", alpha=0.6))

    print(f"  MD  total key: {total_key['MD']/1e9:.3f} Gbit  (paper: 1.235 Gbit)")
    print(f"  MSD total key: {total_key['MLC-MSD']/1e6:.1f} Mbit  (paper: 385 Mbit)")

    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 8 displayed")
