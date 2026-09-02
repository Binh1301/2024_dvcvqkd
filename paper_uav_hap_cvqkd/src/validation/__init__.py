"""Fail-closed numerical validation utilities for the frozen experiment.

The public convergence helpers are loaded lazily so that the standalone Arb
certifier can import ``src.validation.rigorous_flint_support`` in its minimal
environment without importing NumPy or the production numerical stack.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ConvergenceTolerance",
    "fock_convergence_trace",
    "mi_convergence_trace",
    "select_representative_state_indices",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import convergence

        return getattr(convergence, name)
    raise AttributeError(name)
