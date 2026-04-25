import matplotlib.pyplot as plt

from ..models.iss_model import elevation_model


def plot_fig7():
    """ISS pass elevation vs time."""
    print("▶ Figure 7 (ISS elevation pass)...")
    t, theta = elevation_model()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(t, theta, "b-", lw=2)
    ax.set_xlabel("Duration (s)", fontsize=12)
    ax.set_ylabel("Elevation Angle (°)", fontsize=12)
    ax.set_title(
        "Fig. 7 – ISS Pass Elevation over Mt. John Observatory\n"
        "9 August 2022  |  Max = 87.6°  |  Duration = 663 s",
        fontsize=11,
    )
    ax.set_xlim([0, 700])
    ax.set_ylim([0, 95])
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    print("  ✓ Figure 7 displayed")
