import numpy as np

from ..config import CHI_HOM, EPS, EPS_DET, ETA, NoiseParams, SecurityParams


def _as_array(x):
    return np.asarray(x, dtype=float)


def _as_output(x):
    arr = np.asarray(x)
    if arr.ndim == 0:
        return float(arr)
    return arr


def _G(x):
    x_arr = np.maximum(_as_array(x), 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(
            x_arr < 1e-12,
            0.0,
            (x_arr + 1.0) * np.log2(x_arr + 1.0) - x_arr * np.log2(x_arr),
        )
    return _as_output(out)


def detection_noise(noise_params: NoiseParams) -> float:
    eta_d = max(float(noise_params.eta_d), EPS)

    chi_hom = (
        float(noise_params.chi_hom)
        if noise_params.chi_hom is not None
        else (1.0 - eta_d + float(noise_params.epsilon_det)) / eta_d
    )
    chi_het = (
        float(noise_params.chi_het)
        if noise_params.chi_het is not None
        else (2.0 - eta_d + 2.0 * float(noise_params.epsilon_det)) / eta_d
    )

    if noise_params.detection == "hom":
        return float(chi_hom)
    if noise_params.detection == "het":
        return float(chi_het)
    raise ValueError("detection must be 'hom' or 'het'.")


def channel_excess_noise(noise_params: NoiseParams) -> float:
    if noise_params.xi_ch is not None:
        return max(float(noise_params.xi_ch), 0.0)
    eps_ch = float(noise_params.epsilon_bg) + float(noise_params.epsilon_RIN) + float(noise_params.epsilon_mod)
    if noise_params.include_epsilon_toa_as_intensity:
        eps_ch += float(noise_params.epsilon_toa)
    return float(max(eps_ch, 0.0))


def noise(T_samples, noise_params: NoiseParams) -> dict:
    T = np.clip(_as_array(T_samples), EPS, 1.0)
    xi_tot = channel_excess_noise(noise_params)
    X_D = detection_noise(noise_params)
    X_line = (1.0 / T - 1.0) + xi_tot
    X_tot = X_line + X_D / T
    return {
        "xi_tot": xi_tot,
        "X_D": X_D,
        "X_line": X_line,
        "X_tot": X_tot,
        "eta_d": float(noise_params.eta_d),
        "detection": noise_params.detection,
    }


def _I_AB(VA: float, X_tot, detection: str):
    chi_tot = _as_array(X_tot)
    if detection == "hom":
        # Homodyne SNR with power transmittance T and trusted detector noise.
        return _as_output(0.5 * np.log2(1.0 + float(VA) / (1.0 + chi_tot)))
    if detection == "het":
        return _as_output(np.log2(1.0 + float(VA) / (1.0 + chi_tot)))
    raise ValueError("detection must be 'hom' or 'het'.")


def _symp12(VA, T, chi_line, Z=None):
    Ts = np.clip(_as_array(T), EPS, None)
    chi_l = _as_array(chi_line)
    if Z is None:
        Z = np.sqrt(float(VA) ** 2 + 2.0 * float(VA))
    z2 = float(Z) ** 2

    t_v = Ts * (float(VA) + 1.0 + chi_l)
    A = (float(VA) + 1.0) ** 2 + t_v**2 - 2.0 * Ts * z2
    B_inner = Ts * ((float(VA) + 1.0) ** 2 + (float(VA) + 1.0) * chi_l - z2)
    B = B_inner**2
    disc = np.maximum(A**2 - 4.0 * B, 0.0)
    l1 = np.sqrt(np.maximum(0.5 * (A + np.sqrt(disc)), 1e-30))
    l2 = np.sqrt(np.maximum(0.5 * (A - np.sqrt(disc)), 1e-30))
    return l1, l2, B, A


def _holevo_gaussian(VA: float, T, chi_line, X_D: float):
    Ts = np.clip(_as_array(T), EPS, None)
    chi_l = _as_array(chi_line)
    chi_tot = chi_l + float(X_D) / Ts

    l1, l2, B, A = _symp12(VA, Ts, chi_l)
    sqB = np.sqrt(np.maximum(B, 0.0))

    denom = Ts * (1.0 + float(VA) + chi_tot)
    C = (A * float(X_D) + (float(VA) + 1.0) * sqB + Ts * (float(VA) + 1.0 + chi_l)) / denom
    D = (sqB * (float(VA) + 1.0 + sqB * float(X_D))) / denom
    disc = np.maximum(C**2 - 4.0 * D, 0.0)
    l3 = np.sqrt(np.maximum(0.5 * (C + np.sqrt(disc)), 1e-30))
    l4 = np.sqrt(np.maximum(0.5 * (C - np.sqrt(disc)), 1e-30))

    chi_be = _as_array(_G((l1 - 1.0) / 2.0)) + _as_array(_G((l2 - 1.0) / 2.0))
    chi_be -= _as_array(_G((l3 - 1.0) / 2.0)) + _as_array(_G((l4 - 1.0) / 2.0))
    return chi_be


def iab_homodyne(VA: float, T, chi_tot, eta_d: float):
    Ts = np.clip(_as_array(T), EPS, 1.0)
    et = max(float(eta_d), EPS)
    numerator = et * Ts * float(VA)
    denominator = 1.0 + et * Ts * _as_array(chi_tot)
    snr = numerator / np.maximum(denominator, EPS)
    return _as_output(0.5 * np.log2(1.0 + snr))


def skr_components(T_samples, noise_terms: dict, security_params: SecurityParams, detection: str, eta_d: float) -> dict:
    T = np.clip(_as_array(T_samples), EPS, 1.0)
    if detection == "hom":
        I_AB = _as_array(iab_homodyne(security_params.VA, T=T, chi_tot=noise_terms["X_tot"], eta_d=eta_d))
    else:
        I_AB = _as_array(_I_AB(security_params.VA, noise_terms["X_tot"], detection=detection))
    chi_be = _as_array(
        _holevo_gaussian(
            VA=security_params.VA,
            T=T,
            chi_line=noise_terms["X_line"],
            X_D=noise_terms["X_D"],
        )
    )
    skr_arr = float(security_params.beta) * I_AB - chi_be
    return {
        "I_AB": I_AB,
        "chi_BE": chi_be,
        "SKR": skr_arr,
    }


def skr(T_samples, noise_terms: dict, security_params: SecurityParams, detection: str) -> np.ndarray:
    eta_d = float(noise_terms.get("eta_d", 0.5 if detection == "hom" else 1.0))
    out = skr_components(
        T_samples=T_samples,
        noise_terms=noise_terms,
        security_params=security_params,
        detection=detection,
        eta_d=eta_d,
    )
    return out["SKR"]


def _eps_total(T, eps_ch, eps_det=EPS_DET):
    Ts = np.clip(_as_array(T), EPS, None)
    return _as_output(float(eps_ch) + float(eps_det) / Ts)


def _chi_l(T, eps):
    Ts = np.clip(_as_array(T), EPS, None)
    return _as_output((1.0 / Ts - 1.0) + float(eps))


def _chi_t_hom(T, eps):
    Ts = np.clip(_as_array(T), EPS, None)
    return _as_output(_as_array(_chi_l(Ts, eps)) + CHI_HOM / Ts)


def _IAB_hom(VA, chi_t):
    return _as_output(0.5 * np.log2(1.0 + float(VA) / (1.0 + _as_array(chi_t))))


def holevo_gm_homodyne(VA: float, T, chi_line, chi_D: float):
    return _as_output(_holevo_gaussian(VA=VA, T=T, chi_line=chi_line, X_D=chi_D))


def key_rate_gm_homodyne(VA: float, beta: float, T, chi_line, chi_D: float):
    Ts = np.clip(_as_array(T), EPS, None)
    chi_tot = _as_array(chi_line) + float(chi_D) / Ts
    i_ab = _as_array(_IAB_hom(VA, chi_tot))
    chi_be = _as_array(holevo_gm_homodyne(VA=VA, T=Ts, chi_line=chi_line, chi_D=chi_D))
    return _as_output(float(beta) * i_ab - chi_be)


def key_rate_from_noise(VA: float, beta: float, T, xi_tot: float, v_el: float, eta_d: float) -> dict:
    noise_params = NoiseParams(
        xi_ch=xi_tot,
        eta_d=eta_d,
        epsilon_det=float(v_el),
        detection="hom",
    )
    n = noise(T, noise_params)
    K = key_rate_gm_homodyne(VA=VA, beta=beta, T=T, chi_line=n["X_line"], chi_D=n["X_D"])
    return {
        "K": K,
        "chi_line": n["X_line"],
        "chi_D": n["X_D"],
        "chi_tot": n["X_tot"],
    }


def skr_gm(VA, T, eps, beta):
    Ts = np.clip(_as_array(T), EPS, 1.0)
    chi_line = _as_array(_chi_l(Ts, eps))
    chi_tot = chi_line + CHI_HOM / Ts
    i_ab = _as_array(iab_homodyne(VA=VA, T=Ts, chi_tot=chi_tot, eta_d=ETA))
    chi_be = _as_array(holevo_gm_homodyne(VA=float(VA), T=Ts, chi_line=chi_line, chi_D=CHI_HOM))
    return _as_output(float(beta) * i_ab - chi_be)


def optimize_modulation_variance(
    T_eff: float,
    noise_params: NoiseParams,
    beta: float,
    VA_min: float = 0.1,
    VA_max: float = 10.0,
    VA_points: int = 200,
) -> dict:
    T_arr = np.array([max(float(T_eff), EPS)], dtype=float)
    n_terms = noise(T_arr, noise_params)
    va_range = np.linspace(float(VA_min), float(VA_max), int(VA_points))
    skr_list = np.empty_like(va_range)
    iab_list = np.empty_like(va_range)
    chi_list = np.empty_like(va_range)

    for i, va in enumerate(va_range):
        sec = SecurityParams(VA=float(va), beta=float(beta))
        comps = skr_components(
            T_samples=T_arr,
            noise_terms=n_terms,
            security_params=sec,
            detection=noise_params.detection,
            eta_d=noise_params.eta_d,
        )
        iab_list[i] = float(comps["I_AB"][0])
        chi_list[i] = float(comps["chi_BE"][0])
        skr_list[i] = max(float(comps["SKR"][0]), 0.0)

    idx = int(np.argmax(skr_list))
    return {
        "VA_range": va_range,
        "SKR_list": skr_list,
        "I_AB_list": iab_list,
        "chi_BE_list": chi_list,
        "VA_opt": float(va_range[idx]),
        "SKR_opt": float(skr_list[idx]),
    }
