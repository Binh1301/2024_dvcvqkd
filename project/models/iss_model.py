import numpy as np


def elevation_model(duration=663, max_elev=87.6, dt=1.0):
    """
    ISS pass elevation angle vs time over Mt. John Observatory (9 Aug 2022).
    # Assumption: Gaussian proxy in absence of measured ephemeris track.
    Returns (t_arr [s], theta_arr [°]).
    """
    t = np.arange(0, duration + dt, dt)
    theta = max_elev * np.exp(-0.5 * ((t - 350) / 115) ** 2)
    return t, np.maximum(theta, 0.0)
