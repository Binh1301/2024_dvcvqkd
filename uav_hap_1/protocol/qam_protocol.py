from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..zstar import base as zbase
from ..zstar import binomial as zbin
from ..zstar import mb as zmb
from ..zstar import uniform as zuni


@dataclass(frozen=True)
class QAMState:
    label: str
    alpha0: float
    ncut: int
    va: float
    tr_tau: float
    tr_c: float
    w: float
    rank: int
    nu_tilde: Optional[float] = None
    convergence_ok: Optional[bool] = None


@dataclass(frozen=True)
class QAMMetrics:
    z_star_raw: float
    z_star: float
    z_star_max: float
    z_star_clipped: bool
    chi_be: float
    i_ab: float
    skr_raw: float
    skr: float
    chi_tot: float
    chi_line: float
    chi_det: float
    lambda1: float
    lambda2: float
    lambda3: float
    # Diagnostic fields
    term_signal: float
    term_noise: float
    z_raw_over_zmax: float
    z_raw_margin: float


def build_state_binomial(alpha0: float, ncut: int) -> QAMState:
    state = zbin.compute_state(alpha0=alpha0, ncut=ncut)
    return QAMState(
        label="binomial",
        alpha0=state["alpha0"],
        ncut=state["ncut"],
        va=state["va"],
        tr_tau=state["tr_tau"],
        tr_c=state["tr_c"],
        w=state["w"],
        rank=state["rank"],
    )


def build_state_uniform(alpha0: float, ncut: int) -> QAMState:
    state = zuni.compute_state(alpha0=alpha0, ncut=ncut)
    return QAMState(
        label="uniform",
        alpha0=state["alpha0"],
        ncut=state["ncut"],
        va=state["va"],
        tr_tau=state["tr_tau"],
        tr_c=state["tr_c"],
        w=state["w"],
        rank=state["rank"],
    )


def build_state_mb(alpha0: float, ncut: int, nu_tilde: float) -> QAMState:
    state = zmb.compute_state(alpha0=alpha0, ncut=ncut, nu_tilde=nu_tilde)
    return QAMState(
        label="mb",
        alpha0=state["alpha0"],
        ncut=state["ncut"],
        va=state["va"],
        tr_tau=state["tr_tau"],
        tr_c=state["tr_c"],
        w=state["w"],
        rank=state["rank"],
        nu_tilde=state["nu_tilde"],
    )


def compute_metrics(
    state: QAMState,
    T: float,
    eps: float,
    beta: float,
    eta: float,
    v_el: float,
    clip_zstar: bool = True,
) -> QAMMetrics:
    # Diagnostic terms
    term_signal = 2 * np.sqrt(T) * state.tr_c
    term_noise = np.sqrt(2 * T * eps * state.w)
    z_star_raw = zbase.compute_zstar(state.tr_c, state.w, T, eps)
    
    a_cv = state.va + 1.0
    b_cv = 1.0 + T * state.va + T * eps
    z_star_max = float((a_cv * b_cv) ** 0.5)
    z_star_used = z_star_raw
    clipped = False
    if clip_zstar and (z_star_raw >= z_star_max or (a_cv * b_cv - z_star_raw**2) <= 0.0):
        z_star_used = min(z_star_raw, z_star_max * (1.0 - 1e-9))
        clipped = True

    l1, l2, l3, _, _, _ = zbase.compute_eigenvalues(state.va, z_star_used, T, eps)
    chi_be = zbase.compute_chi_BE(l1, l2, l3)
    chi_tot, chi_line, chi_det = zbase.compute_chi_tot(T, eps, eta, v_el)
    i_ab = zbase.compute_IAB(state.va, T, chi_tot)
    skr_raw = zbase.compute_SKR(beta, i_ab, chi_be)
    skr = max(skr_raw, 0.0)
    
    # Diagnostic metrics
    z_ratio = z_star_raw / z_star_max if z_star_max > 0 else np.inf
    z_margin = z_star_max - z_star_raw
    
    return QAMMetrics(
        z_star_raw=z_star_raw,
        z_star=z_star_used,
        z_star_max=z_star_max,
        z_star_clipped=clipped,
        chi_be=chi_be,
        i_ab=i_ab,
        skr_raw=skr_raw,
        skr=skr,
        chi_tot=chi_tot,
        chi_line=chi_line,
        chi_det=chi_det,
        lambda1=l1,
        lambda2=l2,
        lambda3=l3,
        term_signal=term_signal,
        term_noise=term_noise,
        z_raw_over_zmax=z_ratio,
        z_raw_margin=z_margin,
    )
