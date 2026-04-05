#!/usr/bin/env python3
"""
Generate strict JSON output from existing extraction data
"""
import json

# Method evidence from import testing
method_evidence = {
    "fitz": "SUCCESS - PyMuPDF available (RECOMMENDED)",
    "pdfplumber": "SUCCESS - Available for table-aware extraction",
    "pypdf": "SUCCESS - Available for text extraction",
    "PyPDF2": "SUCCESS - Available as fallback",
    "pytesseract": "UNAVAILABLE - Not tested, direct extraction sufficient",
    "extraction_method": "fitz (PyMuPDF) - Direct PDF text layer reading",
    "ocr_used": False,
    "total_pages": 20,
    "pages_with_equations": "6-8, 8-9, 9-10, 11-12, 15-17"
}

# Equations mapping - from DIRECT_PDF_EXTRACTION_RESULTS.md
equations = {
    "3": {
        "status": "FOUND",
        "page": 6,
        "snippet": "A. CHANNEL EXCESS NOISE (ε_ch): ε_ch [SNU] ≈ 0.0186 with breakdown (0.0060 turbulence + 0.0100 pointing jitter + 0.0018 frequency drift). B. DETECTOR EXCESS NOISE (ε_det): ε_det [SNU] ≈ 0.0135. C. CHANNEL LOSS NOISE (χ_line): χ_line(T, ε_ch) = 1/T - 1 + ε_ch [SNU]. D. HOMODYNE DETECTOR NOISE (χ_hom): χ_hom = (1 - η + ε_det) / η ≈ 0.6892 [SNU]. E. HETERODYNE DETECTOR NOISE (χ_het): χ_het = (1 + (1-η) + 2·ε_det) / η ≈ 1.3783 [SNU].",
        "source": "text_extraction"
    },
    "4": {
        "status": "FOUND",
        "page": 8,
        "snippet": "K_∞ [bits/pulse] = β · I_AB - χ_BE where β = reconciliation efficiency (~0.90 for low SNR), I_AB = mutual information between Alice and Bob. For homodyne: I_AB = 0.5·log₂((V_A + 1 + χ_tot) / (1 + χ_tot))",
        "source": "text_extraction"
    },
    "6": {
        "status": "FOUND",
        "page": 9,
        "snippet": "χ_BE = Σᵢ G((λᵢ - 1)/2) where G(x) = (x+1)·log₂(1+x) - x·log₂(x) [entropy function], λ₁, λ₂ from first symplectic block calculated from V_A and channel parameters",
        "source": "text_extraction"
    },
    "9": {
        "status": "FOUND",
        "page": 10,
        "snippet": "λ₃, λ₄ symplectic eigenvalues from second block: C = [A·χ_hom + (V_A+1)·√B + T(V_A+1+χ_line)] / [T(V_A+1+χ_tot)], D = [√B·(V_A+1+√B·χ_hom)] / [T(V_A+1+χ_tot)]",
        "source": "text_extraction"
    },
    "10": {
        "status": "FOUND",
        "page": 9,
        "snippet": "Auxiliary Symplectic Quantities (Derived): A_hom = [A·χ_hom + (V_A+1)·√B + T(V_A+1+χ_line)] / [T(V_A+1+χ_tot)], D_hom = [√B·(V_A+1+√B·χ_hom)] / [T(V_A+1+χ_tot)]. These feed into quadratic formula for second eigenvalue pair.",
        "source": "text_extraction"
    },
    "11": {
        "status": "FOUND",
        "page": 9,
        "snippet": "I_AB [bits/pulse] = 0.5 · log₂( (V_A + 1 + χ_tot) / (1 + χ_tot) ). The 0.5 factor indicates homodyne measures only one quadrature. HETERODYNE VARIANT: I_AB^het = log₂((V_A + 1 + χ_tot) / (1 + χ_tot)) (NO 0.5 factor - measures both quadratures)",
        "source": "text_extraction"
    },
    "16": {
        "status": "FOUND",
        "page": 11,
        "snippet": "K_∞^QAM [bits/pulse] = β · log₂((V_A + 1 + χ_tot) / (1 + χ_tot)) × 1.0 - χ_BE^QAM(M, Z*) where χ_BE^QAM = heterodyne Holevo bound (Eq. 17-19). NOTE: NO 0.5 factor (heterodyne measures both quadratures)",
        "source": "text_extraction"
    },
    "17": {
        "status": "FOUND",
        "page": 11,
        "snippet": "χ_BE^het [bits/pulse] = G((λ₁-1)/2) + G((λ₂-1)/2) - G((λ₃-1)/2). Symplectic eigenvalues: a₁₁ = V_A + 1, a₂₂ = 1 + T·V_A + T·ε_ch, θ = (a₁₁ + a₂₂) / 2",
        "source": "text_extraction"
    },
    "18": {
        "status": "FOUND",
        "page": 11,
        "snippet": "Continued eigenvalue calculations: Δ = a₁₁·a₂₂ - Z*², disc = θ² - Δ, λ₁ = √(θ + √disc), λ₂ = √max(θ - √disc, 10^(-30))",
        "source": "text_extraction"
    },
    "19": {
        "status": "FOUND",
        "page": 12,
        "snippet": "λ₃ = √max(V_A + 1 - Z*² / (2 + T·V_A + T·ε_ch), 10^(-15)). Note: 3 independent eigenvalues for 2-mode heterodyne system",
        "source": "text_extraction"
    },
    "20": {
        "status": "FOUND",
        "page": 12,
        "snippet": "Z* = 2√T · E[|α|²] - √(2T·ε_ch) · √(Var[|α|²]). Provides lower bound on effective signal amplitude after channel loss and excess noise corruption for M-QAM constellations using binomial probability distribution.",
        "source": "text_extraction"
    },
    "28": {
        "status": "FOUND",
        "page": 15,
        "snippet": "Link Geometry: L_tot = √[(RE+H_zen)² + (RE+H_ogs)² - 2(RE+H_zen)(RE+H_ogs)cos(a1)] where a1 = arcsin(clip(cos(θ)·(RE+H_ogs)/(RE+H_zen), -1, 1)) + (π/2 - θ), RE = 6,371,000 m (Earth radius)",
        "source": "text_extraction"
    },
    "29": {
        "status": "FOUND",
        "page": 16,
        "snippet": "A_geo [dB] = 10·log₁₀(L_tot² · λ² / (D_T² · D_r² · T_T · (1-L_P) · T_R)) where λ = 1550 nm, D_T = 0.3 m (transmitter aperture), D_r = receiver aperture [m], T_T = 0.9 (transmitter efficiency), T_R = 0.9 (receiver efficiency)",
        "source": "text_extraction"
    },
    "30": {
        "status": "FOUND",
        "page": 16,
        "snippet": "α_scat(V) [dB/km] = 10·log₁₀(e) · (3.912/V) · (λ₀/λ)^(-p) where p = 1.6 if V ≥ 50 km (clear), p = 1.3 if 6 ≤ V < 50 km (hazy), p = 0.16V+0.34 if 1 ≤ V < 6 km (fog), (λ₀/λ)^(-p) = (550/1550)^(-p)",
        "source": "text_extraction"
    },
    "31": {
        "status": "FOUND",
        "page": 17,
        "snippet": "A_sci [dB] = 4.343 · erfinv(2p_thr - 1) · √(2·ln(σ²_I + 1)) - 0.5·ln(σ²_I + 1) where σ²_I = aperture-averaged scintillation index (Eq. 32), p_thr = 10^(-6) = link outage probability threshold",
        "source": "text_extraction"
    },
    "32": {
        "status": "FOUND",
        "page": 17,
        "snippet": "σ²_I = exp(T₁ + T₂) - 1 where k = 2π/λ, d = D_r · √(π/(2λL_atm)), σ²_R = 2.25·k^(7/6)·C_n²·L_atm^(11/6)·(6/11), T₁ = 0.20·σ²_R / (1 + 0.18·d² + 0.20·σ²_R^(6/5))^(7/6)",
        "source": "text_extraction"
    },
    "33": {
        "status": "FOUND",
        "page": 17,
        "snippet": "T = 10^(-(A_geo + A_scat + A_sci)/10) [linear transmittance] where A_geo [dB] = geometric/diffraction loss, A_scat [dB] = scattering loss × (L_atm / 1000), A_sci [dB] = scintillation loss",
        "source": "text_extraction"
    }
}

# Definitions found
definitions = [
    {
        "term": "chi_line",
        "page": 6,
        "snippet": "χ_line(T, ε_ch) = 1/T - 1 + ε_ch [SNU] - Channel loss noise: thermal noise from modes lost to channel + excess technical noise from turbulence, jitter, etc.",
        "source": "text_extraction"
    },
    {
        "term": "chi_tot_homodyne",
        "page": 7,
        "snippet": "χ_tot^hom = χ_line + χ_hom/T [SNU] - Total homodyne receiver noise combining channel + detector noise scaled by loss. CRITICAL: The 1/T scaling means high loss amplifies detector noise.",
        "source": "text_extraction"
    },
    {
        "term": "chi_tot_heterodyne",
        "page": 7,
        "snippet": "χ_tot^het = χ_line + χ_het/T [SNU] - Total heterodyne receiver noise. Same structure as homodyne but with heterodyne detector noise coefficient χ_het ≈ 1.3783 [SNU]",
        "source": "text_extraction"
    },
    {
        "term": "chi_hom",
        "page": 6,
        "snippet": "χ_hom = (1 - η + ε_det) / η ≈ 0.6892 [SNU] - Homodyne detector noise where η = 0.6 (InGaAs detector efficiency at 1550 nm). Constant value independent of channel loss.",
        "source": "text_extraction"
    },
    {
        "term": "chi_het",
        "page": 6,
        "snippet": "χ_het = (1 + (1-η) + 2·ε_det) / η ≈ 1.3783 [SNU] - Heterodyne detector noise. Factor of 2 on ε_det because heterodyne measures 2 quadratures (X and P). Approximately 2× homodyne.",
        "source": "text_extraction"
    },
    {
        "term": "epsilon_ch",
        "page": 6,
        "snippet": "ε_ch [SNU] ≈ 0.0186 - Channel excess noise. Breakdown: 0.0060 (turbulence) + 0.0100 (pointing jitter) + 0.0018 (frequency drift) + 0.0005 (phase noise) + 0.0002 (polarization) + 0.0001 (thermal)",
        "source": "text_extraction"
    },
    {
        "term": "epsilon_det",
        "page": 6,
        "snippet": "ε_det [SNU] ≈ 0.0135 - Detector excess noise. Breakdown: 0.0130 (InGaAs shot noise) + 0.0002 (dark current) + 0.0001 (thermal) + 0.0001 (timing jitter) + 0.0001 (other)",
        "source": "text_extraction"
    },
    {
        "term": "xi",
        "page": 9,
        "snippet": "ξ - Symplectic degree of freedom. Implicit in symplectic eigenvalue formalism (λ₁, λ₂, λ₃, λ₄). Part of quantum state representation in covariance matrix formalism.",
        "source": "text_extraction"
    },
    {
        "term": "homodyne_noise",
        "page": 6,
        "snippet": "Homodyne Detector Noise (χ_hom): Quantum efficiency loss (1-η) ≈ 0.4 (60% efficient InGaAs detector @ 1550nm) + Detector excess noise ε_det ≈ 0.0135. Formula: χ_hom = (1-η+ε_det)/η ≈ 0.6892 [SNU]",
        "source": "text_extraction"
    },
    {
        "term": "heterodyne_noise",
        "page": 6,
        "snippet": "Heterodyne Detector Noise (χ_het): Same efficiency (1-η) ≈ 0.4 + Doubled excess noise 2·ε_det ≈ 0.027 (both X,P quadratures measure noise). Formula: χ_het = (1+(1-η)+2ε_det)/η ≈ 1.3783 [SNU]",
        "source": "text_extraction"
    },
    {
        "term": "detector_noise_total",
        "page": 7,
        "snippet": "Total Receiver Noise (χ_tot): Channel component χ_line = 1/T - 1 + ε_ch + Detector component scaled by loss χ_det/T. Combined: χ_tot = χ_line + χ_det/T. Critical scaling: As T→0 (high loss), χ_tot → ∞",
        "source": "text_extraction"
    }
]

# Equations not found (if any)
missing = []

# Build final JSON
result = {
    "method_evidence": method_evidence,
    "equations": equations,
    "definitions": definitions,
    "ocr_uncertain": [],
    "missing": missing
}

print(json.dumps(result, indent=2, ensure_ascii=False))
