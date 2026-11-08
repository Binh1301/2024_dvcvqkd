"""Manuscript accumulated-block performance approximation, not a security proof."""
import numpy as np


def finite_key(a: float, u: int, m0: float, epsilon: float) -> dict:
    """a=sum(z*r), u=sum(z); apply the penalty ONCE to the terminal block."""
    if not np.isfinite([a, u, m0, epsilon]).all() or u < 0 or int(u) != u or m0 <= 0 or not 0 < epsilon < 1:
        raise ValueError('Require finite a, integer u>=0, m0>0 and 0<epsilon<1')
    if u == 0 and a != 0:
        raise ValueError('No valid slots must imply zero accumulated contribution')
    n = m0*u
    penalty = 7*np.sqrt(n)*np.sqrt(1-np.log2(epsilon)) if n else 0.
    if not np.isfinite([n, penalty, m0*a]).all():
        raise ValueError('Accumulated signals/contribution exceed finite numerical range')
    return dict(valid_signals=float(n), asymptotic_bits=float(m0*a), penalty_bits=float(penalty),
                penalty_per_signal=float(penalty/n) if n else 0., key_bits=float(max(0., m0*a-penalty)))
