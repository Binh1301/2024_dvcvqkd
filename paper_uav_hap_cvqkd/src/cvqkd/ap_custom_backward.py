"""Experimental arbitrary-precision C4 source-moment reverse VJP.

This module is deliberately not imported by the production Gram/Holevo path.
It keeps the exact full-support formulas while using AP eigensystems and
implicit Sylvester adjoints for ``EXPERIMENTAL_AP_CUSTOM_BACKWARD`` only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import mpmath as mp


@dataclass(frozen=True)
class SourceMomentVJP:
    c: mp.mpf
    w: mp.mpf
    grad_p: tuple[mp.mpf, ...]
    grad_z: tuple[mp.mpc, ...]
    minimum_eigenvalue: mp.mpf


def _sectors(p: Sequence[mp.mpf], z: Sequence[mp.mpc]) -> list[mp.matrix]:
    n = len(p)
    blocks = _raw_blocks(p, z)

    sectors: list[mp.matrix] = []
    for sector in range(4):
        raw = mp.zeros(n)
        for d, block in enumerate(blocks):
            raw += block * (mp.j ** (sector * d))
        sectors.append((raw + raw.H) / 2)
    return sectors


def _spectral_state(matrix: mp.matrix) -> tuple[list[mp.mpf], mp.matrix, mp.matrix, mp.matrix, mp.matrix]:
    values, vectors = mp.eighe(matrix)
    eigenvalues = [mp.re(values[i]) for i in range(values.rows)]
    if any(value <= 0 for value in eigenvalues):
        raise ValueError("AP source-moment VJP requires resolved positive full support")
    square = vectors * mp.diag([mp.sqrt(value) for value in eigenvalues]) * vectors.H
    inverse_square = vectors * mp.diag([1 / mp.sqrt(value) for value in eigenvalues]) * vectors.H
    inverse = vectors * mp.diag([1 / value for value in eigenvalues]) * vectors.H
    return eigenvalues, vectors, square, inverse_square, inverse


def _trace_real(matrix: mp.matrix) -> mp.mpf:
    return mp.fsum(matrix[i, i] for i in range(matrix.rows)).real


def _diag_values(matrix: mp.matrix) -> list[mp.mpc]:
    return [matrix[i, i] for i in range(matrix.rows)]


def _run(
    p: Sequence[mp.mpf],
    z: Sequence[mp.mpc],
    *,
    upstream_c: mp.mpf,
    upstream_w: mp.mpf,
) -> SourceMomentVJP:
    n = len(p)
    sectors = _sectors(p, z)
    states = [_spectral_state(matrix) for matrix in sectors]
    minimum_eigenvalue = min(
        value
        for eigenvalues, _, _, _, _ in states
        for value in eigenvalues
    )
    identity = mp.eye(n)
    g_g = [mp.zeros(n) for _ in range(4)]
    g_s = [mp.zeros(n) for _ in range(4)]
    g_r = [mp.zeros(n) for _ in range(4)]
    g_d = mp.zeros(n)
    g_p = [mp.mpf(0) for _ in range(n)]
    g_z = [mp.mpc(0) for _ in range(n)]

    square = [state[2] for state in states]
    inverse_square = [state[3] for state in states]
    inverse = [state[4] for state in states]
    diagonal_z = mp.diag(z)
    diagonal_weight = mp.diag([1 / (2 * mp.sqrt(value)) for value in p])

    c = mp.mpf(0)
    for sector in range(4):
        previous = (sector - 1) % 4
        b = square[sector] * diagonal_z * inverse_square[previous]
        y1 = square[sector] * b
        y2 = y1 * square[previous]
        y3 = y2 * b.H
        c += _trace_real(y3)

        g_y3 = identity * upstream_c
        g_y2 = g_y3 * b
        g_b = g_y3.H * y2
        g_y1 = g_y2 * square[previous].H
        g_s[sector] += g_y1 * b.H
        g_b += square[sector].H * g_y1
        g_s[previous] += y1.H * g_y2

        g_s[sector] += g_b * (diagonal_z * inverse_square[previous]).H
        g_d += square[sector].H * g_b * inverse_square[previous].H
        g_r[previous] += (square[sector] * diagonal_z).H * g_b

    q_matrices = [square[sector] * diagonal_weight for sector in range(4)]
    a_matrices = [
        sectors[sector]
        * diagonal_z
        * inverse[(sector - 1) % 4]
        for sector in range(4)
    ]
    t_matrices = [
        a_matrices[sector] * q_matrices[(sector - 1) % 4]
        for sector in range(4)
    ]
    inner = [
        mp.fsum(
            mp.conj(q_matrices[sector][i, column])
            * t_matrices[sector][i, column]
            for sector in range(4)
            for i in range(n)
        )
        for column in range(n)
    ]
    residuals = [
        t_matrices[sector]
        - q_matrices[sector] * mp.diag(inner)
        for sector in range(4)
    ]
    w = mp.fsum(
        4
        * p[column]
        * mp.fsum(abs(residuals[sector][i, column]) ** 2 for sector in range(4) for i in range(n))
        for column in range(n)
    )

    g_q = [mp.zeros(n) for _ in range(4)]
    g_t = [mp.zeros(n) for _ in range(4)]
    g_a = [mp.zeros(n) for _ in range(4)]
    g_inner = [mp.mpc(0) for _ in range(n)]
    weight4 = mp.diag([4 * value for value in p])
    inner_diagonal = mp.diag(inner)
    for sector in range(4):
        g_e = residuals[sector] * weight4 * (2 * upstream_w)
        g_t[sector] += g_e
        g_q[sector] -= g_e * inner_diagonal.H
        for column, value in enumerate(_diag_values(-q_matrices[sector].H * g_e)):
            g_inner[column] += value
        for column in range(n):
            g_p[column] += 4 * upstream_w * mp.fsum(
                abs(residuals[sector][i, column]) ** 2 for i in range(n)
            )

    for sector in range(4):
        for column in range(n):
            for i in range(n):
                g_q[sector][i, column] += (
                    t_matrices[sector][i, column] * mp.conj(g_inner[column])
                )
                g_t[sector][i, column] += (
                    q_matrices[sector][i, column] * g_inner[column]
                )

    for sector in range(4):
        previous = (sector - 1) % 4
        g_a[sector] += g_t[sector] * q_matrices[previous].H
        g_q[previous] += a_matrices[sector].H * g_t[sector]

    g_p_matrix = [mp.zeros(n) for _ in range(4)]
    for sector in range(4):
        g_s[sector] += g_q[sector] * diagonal_weight.H
        g_p_matrix[sector] += square[sector].H * g_q[sector]

    for sector in range(4):
        previous = (sector - 1) % 4
        g_g[sector] += g_a[sector] * (
            diagonal_z * inverse[previous]
        ).H
        g_d += sectors[sector].H * g_a[sector] * inverse[previous].H
        g_inverse = (sectors[sector] * diagonal_z).H * g_a[sector]
        g_g[previous] -= inverse[previous].H * g_inverse * inverse[previous].H

    for sector in range(4):
        for column in range(n):
            derivative = -1 / (4 * p[column] ** (mp.mpf(3) / 2))
            g_p[column] += mp.re(g_p_matrix[sector][column, column]) * derivative

    for sector in range(4):
        g_s[sector] -= inverse_square[sector].H * g_r[sector] * inverse_square[sector].H
        hermitian_upstream = (g_s[sector] + g_s[sector].H) / 2
        eigenvalues, vectors, _, _, _ = states[sector]
        local = vectors.H * hermitian_upstream * vectors
        local = mp.matrix(
            [
                [
                    local[i, j]
                    / (mp.sqrt(eigenvalues[i]) + mp.sqrt(eigenvalues[j]))
                    for j in range(n)
                ]
                for i in range(n)
            ]
        )
        g_g[sector] += vectors * local * vectors.H

    blocks = _raw_blocks(p, z)
    for sector in range(4):
        upstream = (g_g[sector] + g_g[sector].H) / 2
        for d, block in enumerate(blocks):
            coefficient = mp.j ** (sector * d)
            g_block = mp.conj(coefficient) * upstream
            rotation = mp.j ** d
            for i in range(n):
                for j in range(n):
                    q = mp.conj(g_block[i, j]) * block[i, j]
                    g_p[i] += mp.re(q / (2 * p[i]))
                    g_p[j] += mp.re(q / (2 * p[j]))
                    row_a = -mp.conj(z[i]) / 2
                    row_b = -z[i] / 2 + rotation * z[j]
                    col_a = -mp.conj(z[j]) / 2 + mp.conj(z[i]) * rotation
                    col_b = -z[j] / 2
                    g_dz_i = mp.conj(q * row_a) + q * row_b
                    g_dz_j = mp.conj(q * col_a) + q * col_b
                    if i == j:
                        g_z_i = g_dz_i + g_dz_j
                        g_z_j = mp.mpc(0)
                    else:
                        g_z_i = g_dz_i
                        g_z_j = g_dz_j
                    g_z[i] += g_z_i
                    if i != j:
                        g_z[j] += g_z_j
    for index in range(n):
        g_z[index] += g_d[index, index]

    return SourceMomentVJP(
        c=c,
        w=w,
        grad_p=tuple(g_p),
        grad_z=tuple(g_z),
        minimum_eigenvalue=minimum_eigenvalue,
    )


def _raw_blocks(p: Sequence[mp.mpf], z: Sequence[mp.mpc]) -> list[mp.matrix]:
    n = len(p)
    blocks: list[mp.matrix] = []
    for d in range(4):
        rotation = mp.j ** d
        blocks.append(
            mp.matrix(
                [
                    [
                        mp.sqrt(p[i] * p[j])
                        * mp.exp(
                            -(
                                abs(z[i]) ** 2
                                + abs(rotation * z[j]) ** 2
                            )
                            / 2
                            + mp.conj(z[i]) * rotation * z[j]
                        )
                        for j in range(n)
                    ]
                    for i in range(n)
                ]
            )
        )
    return blocks


def source_moments_vjp(
    p: Sequence[mp.mpf],
    z: Sequence[mp.mpc],
    *,
    digits: int,
    upstream_c: mp.mpf,
    upstream_w: mp.mpf,
) -> SourceMomentVJP:
    if len(p) != len(z) or not p:
        raise ValueError("p and z must be nonempty and have equal length")
    if digits < 20:
        raise ValueError("digits must be at least 20")
    with mp.workdps(digits):
        probabilities = [mp.mpf(value) for value in p]
        amplitudes = [mp.mpc(value) for value in z]
        if any(not mp.isfinite(value) or value <= 0 for value in probabilities):
            raise ValueError("p must contain finite positive full-support probabilities")
        if any(
            not mp.isfinite(value.real) or not mp.isfinite(value.imag)
            for value in amplitudes
        ):
            raise ValueError("z must contain finite complex amplitudes")
        return _run(
            probabilities,
            amplitudes,
            upstream_c=mp.mpf(upstream_c),
            upstream_w=mp.mpf(upstream_w),
        )
