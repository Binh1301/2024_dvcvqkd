import numpy as np

from ..config import CHI_HOM, EPS, NoiseParams, SecurityParams


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
        else (1.0 - eta_d + float(noise_params.v_el)) / eta_d
    )
    chi_het = (
        float(noise_params.chi_het)
        if noise_params.chi_het is not None
        else (2.0 - eta_d + 2.0 * float(noise_params.v_el)) / eta_d
    )

    if noise_params.detection == "hom":
        return float(chi_hom)
    if noise_params.detection == "het":
        return float(chi_het)
    raise ValueError("detection must be 'hom' or 'het'.")


def noise(T_samples, noise_params: NoiseParams) -> dict:
    T = np.clip(_as_array(T_samples), EPS, 1.0)
    xi_tot = float(noise_params.xi_ch) + float(noise_params.xi_det) + float(noise_params.xi_phase)
    X_D = detection_noise(noise_params)
    X_line = (1.0 / T - 1.0) + xi_tot
    X_tot = X_line + X_D / T
    return {
        "xi_tot": xi_tot,
        "X_D": X_D,
        "X_line": X_line,
        "X_tot": X_tot,
    }


def _I_AB(VA: float, X_tot, detection: str):
    if detection == "hom":
        return 0.5 * np.log2(1.0 + float(VA) / (1.0 + _as_array(X_tot)))
    if detection == "het":
        return np.log2(1.0 + float(VA) / (1.0 + _as_array(X_tot)))
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


def skr(T_samples, noise_terms: dict, security_params: SecurityParams, detection: str) -> np.ndarray:
    I_AB = _I_AB(security_params.VA, noise_terms["X_tot"], detection=detection)
    chi_be = _holevo_gaussian(
        VA=security_params.VA,
        T=T_samples,
        chi_line=noise_terms["X_line"],
        X_D=noise_terms["X_D"],
    )
    return security_params.beta * I_AB - chi_be


def _eps_total(T, eps_ch, eps_det=0.0135):
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
    noise_params = NoiseParams(xi_ch=xi_tot, xi_det=0.0, xi_phase=0.0, eta_d=eta_d, v_el=v_el, detection="hom")
    n = noise(T, noise_params)
    K = key_rate_gm_homodyne(VA=VA, beta=beta, T=T, chi_line=n["X_line"], chi_D=n["X_D"])
    return {
        "K": K,
        "chi_line": n["X_line"],
        "chi_D": n["X_D"],
        "chi_tot": n["X_tot"],
    }


def skr_gm(VA, T, eps, beta):
    chi_line = _chi_l(T, eps)
    return key_rate_gm_homodyne(VA=VA, beta=beta, T=T, chi_line=chi_line, chi_D=CHI_HOM)
