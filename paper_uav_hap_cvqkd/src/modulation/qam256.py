"""Paper Eqs. (65)--(81): square 256-QAM and reference PMFs."""

from __future__ import annotations

import math

import torch


SYMBOL_COUNT = 256
GRID_SIDE = 16


def square_qam256(
    alpha0: float = 1.0,
    *,
    dtype: torch.dtype = torch.complex128,
    device: torch.device | str | None = None,
) -> torch.Tensor:
    """Return Eq. (69) in deterministic ``k*16+l`` order."""

    if not math.isfinite(alpha0) or alpha0 <= 0.0:
        raise ValueError("alpha0 must be finite and positive.")
    real_dtype = torch.float64 if dtype == torch.complex128 else torch.float32
    levels = torch.arange(GRID_SIDE, dtype=real_dtype, device=device) - 7.5
    i_grid, q_grid = torch.meshgrid(levels, levels, indexing="ij")
    points = torch.complex(i_grid.reshape(-1), q_grid.reshape(-1))
    return (float(alpha0) / math.sqrt(30.0) * points).to(dtype=dtype)


def uniform_pmf(
    *, dtype: torch.dtype = torch.float64, device: torch.device | str | None = None
) -> torch.Tensor:
    return torch.full((SYMBOL_COUNT,), 1.0 / SYMBOL_COUNT, dtype=dtype, device=device)


def binomial_pmf(
    *, dtype: torch.dtype = torch.float64, device: torch.device | str | None = None
) -> torch.Tensor:
    one_dimensional = torch.tensor(
        [math.comb(15, k) / 2.0**15 for k in range(GRID_SIDE)],
        dtype=dtype,
        device=device,
    )
    return torch.outer(one_dimensional, one_dimensional).reshape(-1)


def maxwell_boltzmann_pmf(
    nu_mb: float,
    *,
    dtype: torch.dtype = torch.float64,
    device: torch.device | str | None = None,
) -> torch.Tensor:
    if not math.isfinite(nu_mb) or nu_mb < 0.0:
        raise ValueError("nu_mb must be finite and nonnegative.")
    levels = torch.arange(GRID_SIDE, dtype=dtype, device=device) - 7.5
    weights = torch.exp(-float(nu_mb) * levels.square())
    pmf = torch.outer(weights, weights).reshape(-1)
    return pmf / pmf.sum()


def reference_pmf(
    kind: str,
    *,
    nu_mb: float | None = None,
    dtype: torch.dtype = torch.float64,
    device: torch.device | str | None = None,
) -> torch.Tensor:
    if kind == "uniform":
        return uniform_pmf(dtype=dtype, device=device)
    if kind == "binomial":
        return binomial_pmf(dtype=dtype, device=device)
    if kind == "mb":
        if nu_mb is None:
            raise ValueError("nu_mb is required for the Maxwell--Boltzmann PMF.")
        return maxwell_boltzmann_pmf(nu_mb, dtype=dtype, device=device)
    raise ValueError("kind must be one of: uniform, binomial, mb.")

