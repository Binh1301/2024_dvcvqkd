import numpy as np

# Plot backend
MATPLOTLIB_BACKEND = "TkAgg"

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONSTANTS & PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

LAMBDA = 1550e-9        # Wavelength [m]
RE     = 6_371_000.0    # Earth radius [m]

# Hardware (Table III)
DT = 0.3                # Transmitter aperture diameter [m]
TT = 0.9                # Transmitter optics efficiency
TR = 0.9                # Receiver optics efficiency
LP = 0.1                # Pointing/APT loss

# Excess noise (Table I, all in Shot Noise Units SNU)
EPS_CH  = (0.0060 + 0.0100 + 0.0018 + 0.0005 + 0.0002 + 0.0001)  # ≈ 0.0186
EPS_DET = (0.0130 + 0.0002 + 0.0001 + 0.0001 + 0.0001)            # ≈ 0.0135

# Assumption: eta = 0.6 (InGaAs homodyne/heterodyne at 1550 nm)
ETA     = 0.6
CHI_HOM = (1 - ETA + EPS_DET) / ETA            # homodyne detection noise [SNU]
CHI_HET = (1 + (1 - ETA) + 2 * EPS_DET) / ETA  # heterodyne detection noise [SNU]

# Modulation variances (Table III)
VA_GM  = 5.0    # Gaussian [SNU]
VA_PSK = 0.5    # M-PSK    [SNU]
VA_QAM = 2.0    # M-QAM    [SNU]

# Finite-size parameters (Table III)
F_REP   = 50e6    # Repetition rate [Hz]
N_BLOCK = 1e11    # Total symbols
D_DISC  = 5       # Discretisation parameter
EPS_S   = 2e-10   # Smoothing parameter
EPS_SEC = 1e-9    # Security parameter
P_THR   = 1e-6    # Link outage probability

# FER model (Eq. 26)
M1, M2, M3 = 0.8218, -19.46, -298.1

# Table II coefficients for reconciliation efficiency β
RECON_COEFFS = {
    "MLC-MSD": {"c1": 0.9655, "c2": 0.0001507, "c3": -0.04696, "c4": -0.2238},
    "MD":      {"c1": -0.0825, "c2": 0.1834,   "c3": 0.9821,   "c4": -0.00002815},
}

LATM      = 20_000.0    # Atmosphere thickness [m]
H_OGS_DEF = 0.0         # Default OGS altitude [m]
H_OGS_ISS = 1_029.0     # Mt. John Observatory [m]

# Numerical constants used in Eq. (31)-(32)
DB_PER_NEPER      = 10 * np.log10(np.e)
RYTOV_PREFAC      = 2.25
RYTOV_INT_COEFF   = 6.0 / 11.0
SCINT_T1_COEFF    = 0.20
SCINT_T1_D_COEFF  = 0.18
SCINT_T2_COEFF    = 0.21
SCINT_T2_S_COEFF  = 0.24
SCINT_T2_D_COEFF  = 0.90

# Calculation logging
CALC_LOG_XLSX = "cvqkd_calculation_log.xlsx"

# QAM parameters
N_FOCK = 32
QAM_V_DISC_GAUSS = 0.5

# Plot styling
ELEVS = [90, 60, 30]
LS    = ["-", "--", "-."]
