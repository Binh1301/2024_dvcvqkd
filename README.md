# Satellite-to-Ground CV-QKD Simulation

Implementation of "Satellite-to-Ground Continuous Variable Quantum Key Distribution: The Gaussian and Discrete Modulated Protocols in Low Earth Orbit" by Sayat et al., IEEE Transactions on Communications, Vol. 72, No. 6, June 2024.

## Files

- **`cvqkd_simulation.py`** - Complete simulation reproducing Figures 4-8
- **`2024.Satellite-to-Ground_CV-QKD_Gaussian_Discrete_Modulated_LEO (2).pdf`** - Research paper

## Features

### Protocols Implemented
- **GM-CVQKD** (Gaussian Modulated) with homodyne detection
- **M-PSK DM-CVQKD** (Phase Shift Keying) - M ∈ {2, 4, 8}
- **M-QAM DM-CVQKD** (Quadrature Amplitude Modulation) - M ∈ {64, 256}

### Channel Model
- Free-space diffraction loss (Eq. 29)
- Atmospheric scattering - Kruse-Kim model (Eq. 30)
- Turbulence scintillation with aperture averaging (Eq. 31-32)
- Geometric link calculations for LEO satellites (Eq. 28)

### Analysis
- Asymptotic secret key rates (SKR)
- Finite-size corrections (privacy amplification, FER)
- PLOB upper bound comparison
- ISS pass simulation over Mt. John Observatory

## Usage

```bash
python cvqkd_simulation.py
```

This generates all 5 figures:
- **Figure 4**: Asymptotic SKR vs altitude (good atmosphere)
- **Figure 5**: Asymptotic SKR vs altitude (bad atmosphere)
- **Figure 6**: Finite-size SKR comparison (MD vs MLC-MSD)
- **Figure 7**: ISS elevation pass profile
- **Figure 8**: SKR during ISS pass with total key integration

## Requirements

```bash
pip install numpy matplotlib scipy
```

## Key Parameters (from paper)

| Parameter | Value | Description |
|-----------|-------|-------------|
| λ | 1550 nm | Wavelength |
| η | 0.6 | Detector efficiency (InGaAs) |
| D_T | 0.3 m | Transmitter aperture |
| ε_ch | 0.0186 SNU | Channel excess noise |
| ε_det | 0.0135 SNU | Detector excess noise |
| V_A (GM) | 5.0 SNU | Modulation variance (Gaussian) |
| V_A (PSK) | 0.5 SNU | Modulation variance (PSK) |
| V_A (QAM) | 2.0 SNU | Modulation variance (QAM) |
| f_rep | 50 MHz | Repetition rate |
| N_block | 10¹¹ | Block size (finite-size analysis) |

## Expected Results

**Figure 8 - ISS Pass (417.5 km altitude, 663s duration)**:
- MD total key: **~1.235 Gbit**
- MLC-MSD total key: **~385 Mbit**

## Paper Reference

DOI: [10.1109/TCOMM.2024.3359295](https://doi.org/10.1109/TCOMM.2024.3359295)
