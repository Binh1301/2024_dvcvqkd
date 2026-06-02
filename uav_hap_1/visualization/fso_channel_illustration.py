from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError("matplotlib is required for plotting.") from exc

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from uav_hap_1.channel.channel_model import link_distance_m
    from uav_hap_1.config import ChannelParams, GeometryParams
else:
    from ..channel.channel_model import link_distance_m
    from ..config import ChannelParams, GeometryParams


@dataclass(frozen=True)
class IllustrationParams:
    nx: int = 900
    ny: int = 320
    y_extent: float = 0.25
    fog_alpha_min: float = 0.06
    fog_alpha_max: float = 0.32
    eddy_count: int = 60
    seed: int = 7


def _beam_radius(W0_m: float, wavelength_m: float, L_m: float, x_m: np.ndarray) -> np.ndarray:
    z_r = math.pi * float(W0_m) ** 2 / max(float(wavelength_m), 1e-15)
    return float(W0_m) * np.sqrt(1.0 + (x_m / max(z_r, 1e-15)) ** 2)


def _smooth_series(series: np.ndarray, window: int = 31) -> np.ndarray:
    window = max(int(window), 3)
    kernel = np.ones(window, dtype=float) / float(window)
    padded = np.pad(series, (window // 2, window // 2), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def generate_fso_channel_figure(
    out_dir: Path,
    channel_params: ChannelParams | None = None,
    geometry: GeometryParams | None = None,
    illustration: IllustrationParams | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    params = channel_params or ChannelParams()
    geom = geometry or GeometryParams()
    style = illustration or IllustrationParams()

    rng = np.random.default_rng(style.seed)

    L_m = link_distance_m(geom)
    x_m = np.linspace(0.0, L_m, style.nx)

    w_x = _beam_radius(params.W0_m, params.wavelength_m, L_m, x_m)
    w_L = float(w_x[-1])

    scale = style.y_extent / max(2.4 * w_L, 1e-9)
    w_norm = w_x * scale

    x = np.linspace(0.0, 1.0, style.nx)
    y = np.linspace(-style.y_extent, style.y_extent, style.ny)
    X, Y = np.meshgrid(x, y)

    sigma_ln = float(np.clip(0.25 + 0.12 * np.log10(params.Cn2 / 1e-15 + 1.0), 0.18, 0.55))
    ln_i = rng.normal(0.0, sigma_ln, size=style.nx)
    ln_i = _smooth_series(ln_i, window=41)
    scint = np.exp(ln_i)

    w_grid = np.maximum(w_norm, 1e-5)
    I = np.exp(-2.0 * (Y**2) / (w_grid**2)) * scint
    I = I / np.max(I)

    I_db = 10.0 * np.log10(np.maximum(I, 1e-6))

    fig, ax = plt.subplots(figsize=(11.5, 4.6))

    fog = np.linspace(style.fog_alpha_min, style.fog_alpha_max, style.nx)
    fog_img = np.tile(fog, (style.ny, 1))
    ax.imshow(
        fog_img,
        extent=[0.0, 1.0, y.min(), y.max()],
        cmap="Greys",
        alpha=0.28,
        origin="lower",
        aspect="auto",
    )

    im = ax.imshow(
        I_db,
        extent=[0.0, 1.0, y.min(), y.max()],
        cmap="viridis",
        alpha=0.85,
        origin="lower",
        aspect="auto",
    )

    ax.plot(x, w_norm, color="deepskyblue", lw=1.8, alpha=0.9)
    ax.plot(x, -w_norm, color="deepskyblue", lw=1.8, alpha=0.9)
    ax.plot([0.0, 1.0], [0.0, 0.0], color="cyan", lw=1.2, alpha=0.6)

    for _ in range(style.eddy_count):
        cx = float(rng.uniform(0.1, 0.95))
        cy = float(rng.uniform(-0.19, 0.19))
        r = float(rng.uniform(0.008, 0.030))
        ax.add_patch(Circle((cx, cy), r, edgecolor="white", facecolor="none", lw=0.9, alpha=0.18))

    ax.add_patch(Circle((0.0, 0.0), 0.012, color="black", alpha=0.8))
    a_norm = float(params.a_m) * scale
    ax.add_patch(Circle((1.0, 0.0), a_norm, edgecolor="black", facecolor="none", lw=2.0))

    arrow = FancyArrowPatch((0.035, w_norm[0]), (0.035, -w_norm[0]),
                            arrowstyle="<->", mutation_scale=12, color="white", lw=1.2)
    ax.add_patch(arrow)

    ax.text(0.045, 0.0, r"$w_0$", color="white", va="center", fontsize=10)
    ax.text(0.02, style.y_extent * 0.86, f"Visibility V = {params.visibility_km:.0f} km",
            color="white", fontsize=10)
    ax.text(0.60, -style.y_extent * 0.88, r"$C_n^2$ turbulence", color="white", fontsize=10)
    ax.text(0.96, a_norm + 0.02, r"$a$", ha="right", fontsize=10, color="black")

    ax.text(
        0.02,
        -style.y_extent * 0.86,
        f"Beam waist w0 = {params.W0_m * 100:.2f} cm",
        color="white",
        fontsize=9,
    )

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(y.min(), y.max())
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("FSO Channel under Atmospheric Turbulence (Log-Normal Fading)", fontsize=12)

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Received intensity (dB, log scale)")

    fig.tight_layout()
    out_path = out_dir / "fso_channel_visualization.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path

