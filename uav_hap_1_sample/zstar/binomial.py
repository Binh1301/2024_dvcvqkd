import numpy as np

from . import base


def compute_state(alpha0: float, ncut: int) -> dict:
    alpha_list = base.build_constellation(alpha0)
    p = base.build_probs_binomial()
    F = base.build_fock_matrix(alpha_list, ncut)
    tau = base.build_tau(F, p)
    tau_sqrt, tau_invsqrt, eigvals = base.compute_tau_sqrt_invsqrt(tau)
    a_op = base.build_a_operator(ncut)

    nbar = float(np.real(np.trace(tau @ a_op.conj().T @ a_op)))
    va = 2.0 * nbar
    tr_tau = float(np.real(np.trace(tau)))
    tr_c = base.compute_tr_c(tau_sqrt, a_op)
    w, sum_t1, sum_t2 = base.compute_w(tau_sqrt, tau_invsqrt, a_op, F, p)
    rank = int(np.sum(eigvals > 1e-12))

    return {
        "alpha0": float(alpha0),
        "ncut": int(ncut),
        "va": va,
        "tr_tau": tr_tau,
        "tr_c": tr_c,
        "w": w,
        "sum_t1": sum_t1,
        "sum_t2": sum_t2,
        "rank": rank,
    }
