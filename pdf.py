import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

RESULTS_DIR = Path(__file__).resolve().parent / "paper_uav_hap_cvqkd" / "results"
json_path = RESULTS_DIR / "channel_pdf_and_moments.json"

if json_path.is_file():
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    diagnostic_fallback = False
else:
    fallback_path = RESULTS_DIR / "frozen_channel_diagnostics.json"
    if not fallback_path.is_file():
        raise FileNotFoundError(
            f"Missing channel PDF data: {json_path}\n"
            f"Fallback diagnostic is also missing: {fallback_path}"
        )

    with fallback_path.open("r", encoding="utf-8") as f:
        diagnostic = json.load(f)
    derived = diagnostic["derived"]
    upper_eta = float(derived["transmittance_support"]["upper"])
    sigma = float(derived["sigma_r_rayleigh_scale_m"])
    scale = float(derived["pointing_scale_radius_m"])
    gamma = float(derived["pointing_shape_gamma"])
    eta = np.geomspace(upper_eta * 1.0e-8, upper_eta * (1.0 - 1.0e-10), 1000)
    log_ratio = np.log(upper_eta / eta)
    p_active = (
        scale**2
        / (gamma * sigma**2 * eta)
        * log_ratio ** (2.0 / gamma - 1.0)
        * np.exp(-(scale**2 / (2.0 * sigma**2)) * log_ratio ** (2.0 / gamma))
    )
    data = {
        "eta_grid": eta.tolist(),
        "p_active": p_active.tolist(),
        "p_continuous": p_active.tolist(),
        "p_out": 0.0,
        "p_in": 1.0,
        "mean_eta": derived["analytic_mean_transmittance"],
    }
    diagnostic_fallback = True

eta = np.asarray(data["eta_grid"], dtype=float)
p_active = np.asarray(data["p_active"], dtype=float)
p_cont = np.asarray(data["p_continuous"], dtype=float)

p_out = float(data["p_out"])
p_in = float(data["p_in"])
mean_eta = float(data["mean_eta"])

fig, ax = plt.subplots(figsize=(7.2, 4.8))

# Full-channel continuous component
ax.plot(
    eta,
    p_cont,
    linewidth=2.0,
    label=r"$p_{\mathrm{in}}p_{\mathrm{active}}(\eta)$"
)

# Conditional active-link PDF
ax.plot(
    eta,
    p_active,
    linestyle="--",
    linewidth=1.6,
    label=r"$p_{\mathrm{active}}(\eta)$"
)

# Mean physical transmittance
ax.axvline(
    mean_eta,
    linestyle=":",
    linewidth=1.5,
    label=rf"$\langle\eta\rangle={mean_eta:.4f}$"
)

# AoA outage is a discrete probability mass, not a PDF height
ax.annotate(
    rf"AoA outage: $P(T=0)={p_out:.2f}$",
    xy=(0, 0),
    xytext=(0.04, 0.90),
    textcoords="axes fraction",
    arrowprops=dict(arrowstyle="->")
)

ax.set_xlabel(r"Channel transmittance $\eta=T$")
ax.set_ylabel("Probability density")
title = "HAP--UAV Channel Transmittance Distribution"
if diagnostic_fallback:
    title += "\n(nominal no-outage pointing diagnostic)"
ax.set_title(title)

ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

FIGURES_DIR = RESULTS_DIR / "figures_preliminary"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

fig.savefig(
    FIGURES_DIR / "channel_transmittance_pdf_clean.png",
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    FIGURES_DIR / "channel_transmittance_pdf_clean.pdf",
    bbox_inches="tight"
)

plt.show()
