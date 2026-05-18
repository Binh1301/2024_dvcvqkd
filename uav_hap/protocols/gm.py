import numpy as np

from ..config import CHI_HOM, EPS, EPS_DET, NoiseParams, SecurityParams


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


def _g_lambda(x):
    x_arr = _as_array(x)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(
            x_arr <= 1.0 + 1e-10,
            0.0,
            ((x_arr + 1.0) / 2.0) * np.log2((x_arr + 1.0) / 2.0)
            - ((x_arr - 1.0) / 2.0) * np.log2((x_arr - 1.0) / 2.0),
        )
    return _as_output(out)


def detection_noise(noise_params: NoiseParams) -> float:
    eta_d = max(float(noise_params.eta_d), EPS)
    chi_hom = (
        float(noise_params.chi_hom)
        if noise_params.chi_hom is not None
        else ((1.0 - eta_d) / eta_d + float(noise_params.v_el) / eta_d)
    )
    chi_het = (
        float(noise_params.chi_het)
        if noise_params.chi_het is not None
        else ((2.0 - eta_d) / eta_d + 2.0 * float(noise_params.v_el) / eta_d)
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
    V = float(VA) + 1.0
    if detection == "hom":
        return _as_output(0.5 * np.log2((V + chi_tot) / np.maximum(1.0 + chi_tot, EPS)))
    if detection == "het":
        return _as_output(np.log2((V + chi_tot) / np.maximum(1.0 + chi_tot, EPS)))
    raise ValueError("detection must be 'hom' or 'het'.")


def _chi_l(T, eps):
    Ts = np.clip(_as_array(T), EPS, None)
    return _as_output((1.0 / Ts - 1.0) + float(eps))


def _chi_t_hom(T, eps):
    Ts = np.clip(_as_array(T), EPS, None)
    return _as_output(_as_array(_chi_l(Ts, eps)) + CHI_HOM / Ts)


def _IAB_hom(VA, chi_t):
    V = float(VA) + 1.0
    chi_t_arr = _as_array(chi_t)
    return _as_output(0.5 * np.log2((V + chi_t_arr) / np.maximum(1.0 + chi_t_arr, EPS)))


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


def _holevo_gaussian_3_eigs(VA: float, T_eff, chi_line, chi_hom: float) -> dict:
    Ts = np.clip(_as_array(T_eff), EPS, None)
    chi_l = _as_array(chi_line)
    V = float(VA) + 1.0
    chi_h = float(chi_hom)

    A = V**2 * (1.0 - 2.0 * Ts) + 2.0 * Ts + Ts**2 * (V + chi_l) ** 2
    B = Ts**2 * (V * chi_l + 1.0) ** 2
    disc = np.maximum(A**2 - 4.0 * B, 0.0)
    lambda1 = np.sqrt(np.maximum(0.5 * (A + np.sqrt(disc)), EPS))
    lambda2 = np.sqrt(np.maximum(0.5 * (A - np.sqrt(disc)), EPS))

    lambda3_num = (V + chi_h) * (V * chi_l + 1.0)
    lambda3_den = np.maximum((V + chi_l) * (1.0 + chi_h), EPS)
    lambda3 = np.sqrt(np.maximum(lambda3_num / lambda3_den, EPS))

    chi_be = _as_array(_g_lambda(lambda1)) + _as_array(_g_lambda(lambda2)) - _as_array(_g_lambda(lambda3))
    return {
        "lambda1": lambda1,
        "lambda2": lambda2,
        "lambda3": lambda3,
        "chi_BE": chi_be,
    }


def _holevo_gaussian(VA: float, T, chi_line, X_D: float):
    out = _holevo_gaussian_3_eigs(VA=VA, T_eff=T, chi_line=chi_line, chi_hom=float(X_D))
    return out["chi_BE"]


def iab_homodyne(VA: float, T, chi_tot, eta_d: float):
    del T, eta_d
    return _IAB_hom(VA, chi_tot)


def skr_components(T_samples, noise_terms: dict, security_params: SecurityParams, detection: str, eta_d: float) -> dict:
    del eta_d
    T = np.clip(_as_array(T_samples), EPS, 1.0)
    if detection == "hom":
        I_AB = _as_array(_IAB_hom(security_params.VA, noise_terms["X_tot"]))
        holevo_terms = _holevo_gaussian_3_eigs(
            VA=security_params.VA,
            T_eff=T,
            chi_line=noise_terms["X_line"],
            chi_hom=float(noise_terms["X_D"]),
        )
        chi_be = _as_array(holevo_terms["chi_BE"])
    else:
        I_AB = _as_array(_I_AB(security_params.VA, noise_terms["X_tot"], detection=detection))
        holevo_terms = _holevo_gaussian_3_eigs(
            VA=security_params.VA,
            T_eff=T,
            chi_line=noise_terms["X_line"],
            chi_hom=float(noise_terms["X_D"]),
        )
        chi_be = _as_array(holevo_terms["chi_BE"])
    skr_arr = float(security_params.beta) * I_AB - chi_be
    return {
        "I_AB": I_AB,
        "chi_BE": chi_be,
        "SKR": skr_arr,
        "lambda1": holevo_terms["lambda1"],
        "lambda2": holevo_terms["lambda2"],
        "lambda3": holevo_terms["lambda3"],
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
        v_el=float(v_el),
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
    i_ab = _as_array(_IAB_hom(VA, chi_tot))
    holevo_terms = _holevo_gaussian_3_eigs(VA=float(VA), T_eff=Ts, chi_line=chi_line, chi_hom=CHI_HOM)
    chi_be = _as_array(holevo_terms["chi_BE"])
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
