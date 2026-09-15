import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


RESULTS_DIR = (
    Path(__file__).resolve().parent
    / "paper_uav_hap_cvqkd"
    / "results"
)

json_path = RESULTS_DIR / "channel_pdf_and_moments.json"

if not json_path.is_file():
    raise FileNotFoundError(
        "Missing final HAP--UAV channel PDF data:\n"
        f"{json_path}\n"
        "Generate channel_pdf_and_moments.json first. "
        "Do not substitute a pointing-only diagnostic "
        "for the final transmittance distribution."
    )

with json_path.open("r", encoding="utf-8") as f:
    data = json.load(f)


# ============================================================
# Load final mixed-distribution data
# ============================================================

eta = np.asarray(data["eta_grid"], dtype=float)

p_active = np.asarray(
    data["p_active"],
    dtype=float,
)

p_cont = np.asarray(
    data["p_continuous"],
    dtype=float,
)

p_out = float(data["p_out"])
p_in = float(data["p_in"])
mean_eta = float(data["mean_eta"])


# ============================================================
# Basic validity checks
# ============================================================

if not (
    eta.ndim
    == p_active.ndim
    == p_cont.ndim
    == 1
):
    raise ValueError(
        "eta_grid, p_active, and p_continuous "
        "must all be one-dimensional."
    )

if not (
    len(eta)
    == len(p_active)
    == len(p_cont)
):
    raise ValueError(
        "eta_grid, p_active, and p_continuous "
        "must have identical lengths."
    )

if np.any(~np.isfinite(eta)):
    raise ValueError("eta_grid contains non-finite values.")

if np.any(~np.isfinite(p_active)):
    raise ValueError("p_active contains non-finite values.")

if np.any(~np.isfinite(p_cont)):
    raise ValueError(
        "p_continuous contains non-finite values."
    )

if np.any(eta <= 0.0) or np.any(eta > 1.0):
    raise ValueError(
        "Active transmittance grid must satisfy "
        "0 < eta <= 1."
    )

if np.any(np.diff(eta) <= 0.0):
    raise ValueError(
        "eta_grid must be strictly increasing."
    )

if np.any(p_active < 0.0):
    raise ValueError("p_active contains negative density.")

if np.any(p_cont < 0.0):
    raise ValueError(
        "p_continuous contains negative density."
    )

if not np.isclose(
    p_out + p_in,
    1.0,
    rtol=1e-10,
    atol=1e-12,
):
    raise ValueError(
        f"p_out + p_in != 1: "
        f"{p_out} + {p_in}"
    )


# ============================================================
# Mixed-law consistency
#
# P_T(deta)
# =
# p_out delta_0(deta)
# +
# p_in p_active(eta) deta
# ============================================================

if not np.allclose(
    p_cont,
    p_in * p_active,
    rtol=1e-6,
    atol=1e-12,
):
    raise ValueError(
        "p_continuous is inconsistent with "
        "p_in * p_active."
    )


# ============================================================
# Numerical normalization checks
# ============================================================

active_mass = np.trapezoid(
    p_active,
    eta,
)

continuous_mass = np.trapezoid(
    p_cont,
    eta,
)

total_mass = p_out + continuous_mass

mean_eta_from_pdf = np.trapezoid(
    eta * p_cont,
    eta,
)

print(
    f"active PDF mass      = "
    f"{active_mass:.12f}"
)
print(
    f"continuous mass      = "
    f"{continuous_mass:.12f}"
)
print(
    f"outage mass          = "
    f"{p_out:.12f}"
)
print(
    f"total probability    = "
    f"{total_mass:.12f}"
)
print(
    f"mean eta from PDF    = "
    f"{mean_eta_from_pdf:.12f}"
)
print(
    f"stored mean eta      = "
    f"{mean_eta:.12f}"
)

# Numerical quadrature tolerance depends on eta-grid resolution.
if not np.isclose(
    active_mass,
    1.0,
    rtol=2e-3,
    atol=2e-4,
):
    raise ValueError(
        "Conditional active PDF is not normalized: "
        f"{active_mass}"
    )

if not np.isclose(
    continuous_mass,
    p_in,
    rtol=2e-3,
    atol=2e-4,
):
    raise ValueError(
        "Continuous probability mass does not equal "
        f"p_in: {continuous_mass} vs {p_in}"
    )

if not np.isclose(
    total_mass,
    1.0,
    rtol=2e-3,
    atol=2e-4,
):
    raise ValueError(
        "Final mixed distribution is not normalized: "
        f"{total_mass}"
    )

if not np.isclose(
    mean_eta_from_pdf,
    mean_eta,
    rtol=2e-3,
    atol=1e-6,
):
    raise ValueError(
        "Stored mean_eta disagrees with PDF quadrature: "
        f"{mean_eta} vs {mean_eta_from_pdf}"
    )


# ============================================================
# Plot
# ============================================================

fig, ax = plt.subplots(
    figsize=(7.2, 4.8)
)

# Full-channel continuous component:
#
# p_cont(eta)
# =
# p_in p_active(eta)
#
ax.plot(
    eta,
    p_cont,
    linewidth=2.0,
    label=(
        r"$p_{\rm in}"
        r"p_{\rm active}(\eta)$"
    ),
)

# Outage-inclusive mean physical transmittance
ax.axvline(
    mean_eta,
    linestyle=":",
    linewidth=1.5,
    label=(
        rf"Outage-inclusive mean "
        rf"$\langle\eta\rangle="
        rf"{mean_eta:.4f}$"
    ),
)

ax.set_xlabel(
    r"Channel transmittance $\eta=T$"
)

# Show the full physically admissible transmittance domain.
ax.set_xlim(0.0, 1.0)
ax.set_xticks(np.linspace(0.0, 1.0, 11))

ax.set_ylabel(
    "Probability density"
)

# The AoA outage is a probability mass at eta = 0.
# It must NOT be plotted as an ordinary PDF height.
ax.text(
    0.04,
    0.94,
    (
        rf"Mixed law: $p_T=p_{{out}}\delta_0"
        rf"+p_{{in}}p_{{active}}$"
        "\n"
        rf"$P(T=0)={p_out:.2f}$: Dirac mass"
        "\n"
        rf"continuous mass $p_{{in}}={p_in:.2f}$"
    ),
    transform=ax.transAxes,
    va="top",
    bbox=dict(
        boxstyle="round",
        alpha=0.15,
    ),
)

# Visual marker for the discrete outage mass at T=0.
# Use p_out = 1 - p_in; the blue PDF peak is not a probability mass.
ax_mass = ax.twinx()
ax_mass.vlines(
    0.0,
    0.0,
    p_out,
    color="tab:red",
    linewidth=3.0,
    label=rf"$P(T=0)={p_out:.2f}$",
)
ax_mass.scatter([0.0], [p_out], color="tab:red", s=45)
ax_mass.set_ylim(0.0, 1.0)
ax_mass.set_ylabel("Discrete probability mass")

ax.set_title(
    "HAP--UAV Channel Transmittance Distribution"
)

ax.grid(alpha=0.25)

lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax_mass.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2)

fig.tight_layout()


# ============================================================
# Save
# ============================================================

FIGURES_DIR = (
    RESULTS_DIR
    / "figures_preliminary"
)

FIGURES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

fig.savefig(
    FIGURES_DIR
    / "channel_transmittance_pdf_clean.png",
    dpi=300,
    bbox_inches="tight",
)

fig.savefig(
    FIGURES_DIR
    / "channel_transmittance_pdf_clean.pdf",
    bbox_inches="tight",
)

plt.show()
