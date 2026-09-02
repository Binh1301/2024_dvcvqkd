"""Paper Eqs. (65)--(81): square 256-QAM and reference PMFs."""

from __future__ import annotations

import math

import torch


SYMBOL_COUNT = 256
GRID_SIDE = 16
C4_ORDER = 4
C4_ORBIT_COUNT = SYMBOL_COUNT // C4_ORDER


def c4_orbit_indices(*, device: torch.device | str | None = None) -> torch.Tensor:
    """Return the deterministic ``[64,4]`` C4 partition of row-major QAM labels.

    Column ``r`` contains the original 16-by-16 row-major label reached after
    multiplying the first-quadrant representative in column zero by ``1j**r``.
    First-quadrant representatives retain row-major order, while scatter
    expansion leaves all 256 public symbol labels unchanged.
    """

    rows: list[list[int]] = []
    visited: set[int] = set()
    for real_index in range(GRID_SIDE // 2, GRID_SIDE):
        for imag_index in range(GRID_SIDE // 2, GRID_SIDE):
            a, b = real_index, imag_index
            orbit = [
                a * GRID_SIDE + b,
                (GRID_SIDE - 1 - b) * GRID_SIDE + a,
                (GRID_SIDE - 1 - a) * GRID_SIDE + (GRID_SIDE - 1 - b),
                b * GRID_SIDE + (GRID_SIDE - 1 - a),
            ]
            if len(set(orbit)) != C4_ORDER:
                raise RuntimeError("Square 256-QAM unexpectedly contains a short C4 orbit.")
            rows.append(orbit)
            visited.update(orbit)
    if len(rows) != C4_ORBIT_COUNT or len(visited) != SYMBOL_COUNT:
        raise RuntimeError("Failed to partition square 256-QAM into 64 C4 orbits.")
    return torch.tensor(rows, dtype=torch.long, device=device)


def expand_c4_orbit_values(orbit_values: torch.Tensor) -> torch.Tensor:
    """Expand ``[...,64]`` complex prototypes into row-major ``[...,256]`` points."""

    if orbit_values.shape[-1] != C4_ORBIT_COUNT or not orbit_values.is_complex():
        raise ValueError("orbit_values must be complex with final dimension 64.")
    rotations = torch.tensor((1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j),
                             dtype=orbit_values.dtype, device=orbit_values.device)
    values = orbit_values.unsqueeze(-1) * rotations
    indices = c4_orbit_indices(device=orbit_values.device).reshape(-1)
    output = torch.empty((*orbit_values.shape[:-1], SYMBOL_COUNT),
                         dtype=orbit_values.dtype, device=orbit_values.device)
    return output.scatter(-1, indices.expand(*orbit_values.shape[:-1], -1), values.reshape(*orbit_values.shape[:-1], -1))


def expand_c4_orbit_masses(orbit_masses: torch.Tensor) -> torch.Tensor:
    """Expand normalized ``[...,64]`` orbit masses to tied row-major symbol PMFs."""

    if orbit_masses.shape[-1] != C4_ORBIT_COUNT or orbit_masses.is_complex():
        raise ValueError("orbit_masses must be real with final dimension 64.")
    indices = c4_orbit_indices(device=orbit_masses.device).reshape(-1)
    values = orbit_masses.unsqueeze(-1).expand(*orbit_masses.shape, C4_ORDER) / C4_ORDER
    output = torch.empty((*orbit_masses.shape[:-1], SYMBOL_COUNT),
                         dtype=orbit_masses.dtype, device=orbit_masses.device)
    return output.scatter(-1, indices.expand(*orbit_masses.shape[:-1], -1), values.reshape(*orbit_masses.shape[:-1], -1))


def c4_orbit_masses(probabilities: torch.Tensor, tolerance: float = 1e-10) -> torch.Tensor:
    """Collapse a row-major C4-symmetric PMF to its 64 orbit masses."""

    if probabilities.shape[-1] != SYMBOL_COUNT or probabilities.is_complex():
        raise ValueError("probabilities must be real with final dimension 256.")
    grouped = probabilities[..., c4_orbit_indices(device=probabilities.device)]
    within_orbit_error = (grouped - grouped[..., :1]).abs().amax()
    checked_error = within_orbit_error.detach()
    if not bool(torch.isfinite(checked_error)) or float(checked_error) > tolerance:
        raise ValueError("probabilities are not tied within each C4 orbit.")
    return grouped.sum(dim=-1)


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


def canonical_square_qam256(
    *,
    dtype: torch.dtype = torch.complex128,
    device: torch.device | str | None = None,
) -> torch.Tensor:
    """Return square QAM after the frozen global unit-RMS gauge removal."""

    points = square_qam256(dtype=dtype, device=device)
    return points / torch.sqrt(points.abs().square().mean())


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
    points = canonical_square_qam256(dtype=torch.complex128, device=device)
    energy = points.abs().square().to(dtype=dtype)
    pmf = torch.exp(-float(nu_mb) * energy)
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
